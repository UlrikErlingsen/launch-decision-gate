"""Signal brand: shared theme shell, README information architecture, and runtime scaffolding."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from gatesignal import __version__


ROOT = Path(__file__).parents[1]
APP = str(ROOT / "app.py")
UI = ROOT / "src" / "gatesignal" / "ui"


def test_shared_signal_shell_renders() -> None:
    app = AppTest.from_file(APP, default_timeout=120)
    app.run()

    assert not app.exception, [error.value for error in app.exception]
    body = "\n".join(str(item.value) for item in app.markdown)
    sidebar = "\n".join(str(item.value) for item in app.sidebar.markdown)
    assert "OPEN PRODUCT DECISION SUPPORT" in body
    assert "NEW-PRODUCT GATE DECISIONS" in body
    assert f"Gate Signal v{__version__}" in body
    assert "structured evidence, not automated approval" in body
    assert "Part of the Signal suite" in body
    assert "AGPL-3.0-or-later" in body
    assert "sg-mast" in body  # the shared Signal masthead
    assert "sg-foot" in body  # the shared Signal footer
    assert "Know when the evidence deserves the next investment" in sidebar
    assert "sg-side" in sidebar  # the shared Signal sidebar lockup


def test_app_uses_shared_signal_theme_instead_of_pasted_styles() -> None:
    standalone = (ROOT / "app.py").read_text(encoding="utf-8")
    ui_source = (UI / "app.py").read_text(encoding="utf-8")
    theme = (UI / "signal_theme.py").read_text(encoding="utf-8")
    assert 'st.set_page_config(**sig.page_config("gate"))' in standalone
    assert "sig.apply(NS)" in ui_source
    assert "st.plotly_chart(" not in ui_source  # charts go through sig.chart (template + theme=None)
    assert ui_source.count("template=sig.template(NS)") == 4  # every figure carries the per-app template
    assert "<style>" not in standalone + ui_source
    assert "unsafe_allow_html" not in ui_source
    for old_colour in ("#173c3a", "#d95b40", "#83d2b4", "#f2c66d", "#17322e", "#102c2a", "#f8f5ed", "#59716c", "#e88954"):
        assert old_colour not in (standalone + ui_source).lower()
    assert "GateSignal" not in ui_source
    assert (UI / "assets" / "marks" / "gatesignal-mark-64.png").exists()
    assert ":focus-visible" in theme
    assert "@media (prefers-reduced-motion:reduce)" in theme
    assert "friendly_message" in ui_source


def test_readme_matches_suite_information_architecture() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    # Signal README template order: readers find the same section in the same place in every repo.
    sections = [
        "## Read this first",
        "## Scope",
        "## Try the demo in three minutes",
        "## Data contract",
        "## Methods",
        "## Decision statuses",
        "## Exports",
        "## Run locally",
        "## Privacy",
        "## No install? Give this file to an AI",
        "## Development",
        "## Where this fits in Signal",
        "## References",
        "## Originality and license",
    ]
    positions = [readme.find(f"\n{heading}\n") for heading in sections]
    assert all(position >= 0 for position in positions), dict(zip(sections, positions, strict=True))
    assert positions == sorted(positions)
    assert readme.startswith('<p align="center">\n  <img src="assets/gatesignal-banner.png"')
    assert "gatesignal-banner.svg" not in readme
    assert "Signal-Decide-4f80a2" in readme  # family badge in the Decide 600 colour
    assert "github.com/UlrikErlingsen/launch-decision-gate/actions" in readme  # tests badge
    assert "**Gate Signal**" in readme
    assert "GateSignal" not in readme
    assert "Creator Signal" not in readme
    assert '<img src="assets/gatesignal-mark-64.png"' in readme  # suite footer
    # Honesty statements survive the restructure.
    assert "it does not manufacture evidence or delegate approval" in readme
    assert "does **not** calculate a probability of product success" in readme
    assert "never an authorization" in readme
    for path in ("assets/gatesignal-banner.png", "assets/gatesignal-mark-64.png", "assets/gatesignal-social.png"):
        assert (ROOT / path).exists()
    assert not (ROOT / "assets" / "gatesignal-banner.svg").exists()


def test_runtime_scaffolding_is_private_and_health_checked() -> None:
    config = (ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    launcher = (ROOT / "run_app.command").read_text(encoding="utf-8")

    assert "gatherUsageStats = false" in config
    assert 'base = "light"' in config
    assert 'primaryColor = "#4f80a2"' in config  # Signal Decide family, 600 step
    assert "USER gatesignal" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "8597" in dockerfile
    assert "--browser.gatherUsageStats=false" in launcher
    assert "GATESIGNAL_PORT" in launcher
    assert "Gate Signal" in launcher


def test_launchers_docker_and_config_share_the_50_mb_small_input_tier() -> None:
    from gatesignal.io import TIER_MAX_UPLOAD_MB

    config = (ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    macos = (ROOT / "run_app.command").read_text(encoding="utf-8")
    windows = (ROOT / "run_app.bat").read_text(encoding="utf-8")
    assert TIER_MAX_UPLOAD_MB == 50
    assert f"maxUploadSize = {TIER_MAX_UPLOAD_MB}" in config
    assert f'MAX_UPLOAD_MB="${{GATESIGNAL_MAX_UPLOAD_MB:-{TIER_MAX_UPLOAD_MB}}}"' in macos
    assert f"set GATESIGNAL_MAX_UPLOAD_MB={TIER_MAX_UPLOAD_MB}" in windows
    assert "--server.maxUploadSize=%GATESIGNAL_MAX_UPLOAD_MB%" in windows
    assert f"STREAMLIT_SERVER_MAX_UPLOAD_SIZE={TIER_MAX_UPLOAD_MB}" in dockerfile
    assert "--server.maxUploadSize" not in dockerfile
