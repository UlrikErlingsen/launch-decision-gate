from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

from gatesignal import __version__

APP = str(Path(__file__).parents[1] / "app.py")
PAGES = [
    "1 · Evidence & criteria",
    "2 · Economics & scenarios",
    "3 · Risks & contingencies",
    "4 · Decision & export",
    "Methods & limits",
]


def app() -> AppTest:
    return AppTest.from_file(APP, default_timeout=60).run()


def test_welcome_page_and_brand_are_rendered() -> None:
    at = app()

    assert not at.exception
    body = "\n".join(str(markdown.value) for markdown in at.markdown)
    assert f"Gate Signal v{__version__}" in body
    assert "NEW-PRODUCT GATE DECISIONS" in body
    assert "structured evidence, not automated approval" in body
    assert any("does not approve a project" in warning.value for warning in at.warning)


def test_every_page_renders_with_fictional_demo() -> None:
    at = app()
    at.button(key="gate:load_demo").click().run()
    assert at.sidebar.radio[0].value == "1 · Evidence & criteria"

    for page in PAGES:
        at.radio[0].set_value(page).run()
        assert not at.exception, page


def test_welcome_button_opens_the_review() -> None:
    at = app()
    at.button(key="gate:open_review").click().run()

    assert not at.exception
    assert at.sidebar.radio[0].value == "1 · Evidence & criteria"


def test_analysis_flow_produces_conservative_decision() -> None:
    at = app()
    at.button(key="gate:load_demo").click().run()

    at.radio[0].set_value("1 · Evidence & criteria").run()
    at.button(key="gate:score_gate").click().run()
    assert "gate:gate_summary" in at.session_state

    at.radio[0].set_value("2 · Economics & scenarios").run()
    at.button(key="gate:analyze_finance").click().run()
    assert "gate:finance_summary" in at.session_state

    at.radio[0].set_value("3 · Risks & contingencies").run()
    at.button(key="gate:analyze_risk").click().run()
    assert "gate:risk_summary" in at.session_state
    assert "gate:brand_summary" in at.session_state
    assert at.session_state["gate:brand_summary"].status == "CONDITIONAL BRAND SUPPORT"

    at.radio[0].set_value("4 · Decision & export").run()
    at.button(key="gate:build_decision").click().run()

    assert not at.exception
    assert at.session_state["gate:decision_brief"].disposition == "HOLD FOR RISK RESPONSE"
    body = "\n".join(str(markdown.value) for markdown in at.markdown)
    assert "MODEL DISPOSITION" in body
    assert "HOLD FOR RISK RESPONSE" in body
    assert len(at.download_button) >= 3
