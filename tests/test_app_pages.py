from __future__ import annotations

from streamlit.testing.v1 import AppTest


def app() -> AppTest:
    return AppTest.from_file("app.py", default_timeout=20).run()


def test_welcome_page_and_brand_are_rendered() -> None:
    at = app()

    assert not at.exception
    assert any("GateSignal" in markdown.value for markdown in at.markdown)
    assert any("does not approve a project" in warning.value for warning in at.warning)


def test_every_page_renders_with_fictional_demo() -> None:
    at = app()
    at.button(key="load_demo").click().run()

    for page in [
        "1 · Evidence & criteria",
        "2 · Economics & scenarios",
        "3 · Risks & contingencies",
        "4 · Decision & export",
        "Methods & limits",
    ]:
        at.radio[0].set_value(page).run()
        assert not at.exception, page


def test_analysis_flow_produces_conservative_decision() -> None:
    at = app()
    at.button(key="load_demo").click().run()

    at.radio[0].set_value("1 · Evidence & criteria").run()
    at.button(key="score_gate").click().run()
    assert "gate_summary" in at.session_state

    at.radio[0].set_value("2 · Economics & scenarios").run()
    at.button(key="analyze_finance").click().run()
    assert "finance_summary" in at.session_state

    at.radio[0].set_value("3 · Risks & contingencies").run()
    at.button(key="analyze_risk").click().run()
    assert "risk_summary" in at.session_state
    assert "brand_summary" in at.session_state
    assert at.session_state["brand_summary"].status == "CONDITIONAL BRAND SUPPORT"

    at.radio[0].set_value("4 · Decision & export").run()
    at.button(key="build_decision").click().run()

    assert at.session_state["decision_brief"].disposition == "HOLD FOR RISK RESPONSE"
    assert len(at.download_button) >= 3
