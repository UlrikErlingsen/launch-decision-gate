"""Signal Hub contract: importable UI entry point, Streamlit only under ui/, slug-namespaced state, packaged installs."""

import ast
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest
from streamlit.testing.v1 import AppTest

from gatesignal import __version__


ROOT = Path(__file__).parents[1]
PACKAGE = ROOT / "src" / "gatesignal"
UI = PACKAGE / "ui"
UI_ONLY_LIBRARIES = {"streamlit", "plotly"}
PAGES = [
    "Welcome",
    "1 · Evidence & criteria",
    "2 · Economics & scenarios",
    "3 · Risks & contingencies",
    "4 · Decision & export",
    "Methods & limits",
]
RENDER_SCRIPT = """
from gatesignal.ui import render

render()
"""


def _imported_roots(path: Path) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


def test_ui_entry_point_matches_the_hub_contract() -> None:
    from gatesignal.ui import APP_INFO, render

    assert callable(render)
    assert APP_INFO == {"product": "Gate Signal", "version": __version__, "repo": "launch-decision-gate", "slug": "gate"}


def test_only_the_ui_package_imports_streamlit_or_plotly() -> None:
    offenders = {
        str(path.relative_to(PACKAGE)): sorted(_imported_roots(path) & UI_ONLY_LIBRARIES)
        for path in PACKAGE.rglob("*.py")
        if UI not in path.parents and _imported_roots(path) & UI_ONLY_LIBRARIES
    }
    assert not offenders, offenders


def test_core_package_imports_without_streamlit_or_plotly() -> None:
    # A fresh interpreter, so modules already imported by other tests cannot hide a stray import.
    code = (
        f"import sys\nsys.path.insert(0, {str(ROOT / 'src')!r})\n"
        "import gatesignal, gatesignal.brand, gatesignal.decision, gatesignal.errors, gatesignal.examples, "
        "gatesignal.finance, gatesignal.interop, gatesignal.io, gatesignal.risk, gatesignal.scoring\n"
        "loaded = sorted(name for name in ('streamlit', 'plotly') if name in sys.modules)\n"
        "assert not loaded, loaded\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr


def test_render_never_sets_page_config_or_navigation() -> None:
    for path in UI.glob("*.py"):
        if path.name == "signal_theme.py":
            continue
        source = path.read_text(encoding="utf-8")
        for call in ("st.set_page_config(", "st.navigation(", "st.Page("):
            assert call not in source, (path.name, call)


def test_render_runs_from_a_script_without_set_page_config() -> None:
    app = AppTest.from_string(RENDER_SCRIPT, default_timeout=120)
    app.run()

    assert not app.exception, [error.value for error in app.exception]
    assert app.sidebar.radio[0].key == "gate:page"
    assert "gate:project" in app.session_state
    assert "project" not in app.session_state
    body = "\n".join(str(item.value) for item in app.markdown)
    assert "NEW-PRODUCT GATE DECISIONS" in body
    assert f"Gate Signal v{__version__}" in body

    app.button(key="gate:load_demo").click().run()
    assert not app.exception, [error.value for error in app.exception]
    assert str(app.session_state["gate:project"]["metadata"]["project_name"]).startswith("LoopDose")


@pytest.mark.parametrize("page", PAGES)
def test_every_widget_key_is_namespaced(page: str) -> None:
    app = AppTest.from_string(RENDER_SCRIPT, default_timeout=120)
    app.run()
    app.button(key="gate:load_demo").click().run()
    app.sidebar.radio[0].set_value(page).run()

    assert not app.exception, [error.value for error in app.exception]
    widgets = [
        *app.radio,
        *app.selectbox,
        *app.checkbox,
        *app.button,
        *app.text_input,
        *app.text_area,
        *app.number_input,
    ]
    assert widgets
    unkeyed = [(type(widget).__name__, widget.label) for widget in widgets if widget.key is None]
    assert not unkeyed, unkeyed
    assert all(widget.key.startswith("gate:") for widget in widgets)


def test_session_state_and_widget_keys_go_through_the_namespace_helper() -> None:
    source = (UI / "app.py").read_text(encoding="utf-8")
    state_keys = re.findall(r"session_state(?:\[|\.get\(|\.pop\(|\.setdefault\()\s*([^,\])]+)", source)
    widget_keys = re.findall(r"\bkey=([^,)\n]+)", source)
    assert state_keys and widget_keys
    assert all(key.startswith("k(") for key in state_keys), state_keys
    assert all(key.startswith("k(") for key in widget_keys), widget_keys
    assert 'NS = "gate"' in source


def test_ui_reads_no_repository_files() -> None:
    # The Hub installs the release as a normal package: only src/gatesignal/ (and declared package data) exists there.
    for path in [*UI.glob("*.py"), *(path for path in PACKAGE.glob("*.py"))]:
        source = path.read_text(encoding="utf-8")
        for marker in ("parents[", ".parent.parent", "examples/", "docs/", "assets/gatesignal", '"assets"'):
            if path.name == "signal_theme.py" and marker == '"assets"':
                continue  # the theme reads its marks next to itself: src/gatesignal/ui/assets/marks/
            assert marker not in source, (path.name, marker)
    from gatesignal.ui import signal_theme as sig

    assert PACKAGE in sig.ASSETS.resolve().parents
    for suffix in ("-mark.svg", "-mark-64.png"):
        assert (sig.ASSETS / "marks" / f"gatesignal{suffix}").is_file()
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert '"gatesignal.ui" = ["assets/marks/*"]' in pyproject


def _copy_as_installed(target: Path) -> Path:
    """Copy what a non-editable install ships: the package modules plus the declared package data."""
    site = target / "site"
    shutil.copytree(
        PACKAGE,
        site / "gatesignal",
        ignore=lambda folder, names: [
            name
            for name in names
            if (Path(folder) / name).is_file()
            and not name.endswith(".py")
            and Path(folder).resolve() != (UI / "assets" / "marks").resolve()
        ]
        + [name for name in names if name == "__pycache__"],
    )
    return site


PACKAGED_CHECK = '''
import os
import sys

site = os.environ["GATESIGNAL_TEST_SITE"]
repo_src = os.path.normcase(os.path.realpath(os.environ["GATESIGNAL_REPO_SRC"]))
sys.path[:] = [p for p in sys.path if not p or os.path.normcase(os.path.realpath(p)) != repo_src]
sys.path.insert(0, site)

from streamlit.testing.v1 import AppTest

SCRIPT = """
import os
import sys
sys.path.insert(0, os.environ["GATESIGNAL_TEST_SITE"])
import gatesignal
assert os.path.realpath(gatesignal.__file__).startswith(os.path.realpath(os.environ["GATESIGNAL_TEST_SITE"]))
from gatesignal.ui import render
render()
"""

app = AppTest.from_string(SCRIPT, default_timeout=120).run()
assert not app.exception, [e.value for e in app.exception]
app.button(key="gate:load_demo").click().run()
for page in sys.argv[1:]:
    app.sidebar.radio[0].set_value(page).run()
    assert not app.exception, (page, [e.value for e in app.exception])
app.sidebar.radio[0].set_value("4 · Decision & export").run()
app.button(key="gate:build_decision").click().run()
assert not app.exception, [e.value for e in app.exception]
assert app.session_state["gate:decision_brief"].disposition
print("ok")
'''


def test_render_works_from_a_packaged_install_without_repository_files(tmp_path: Path) -> None:
    site = _copy_as_installed(tmp_path)
    workdir = tmp_path / "elsewhere"
    workdir.mkdir()
    env = {**os.environ, "GATESIGNAL_TEST_SITE": str(site), "GATESIGNAL_REPO_SRC": str(ROOT / "src")}
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-c", PACKAGED_CHECK, *PAGES],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=300,
        cwd=workdir,
        env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ok" in result.stdout
