from __future__ import annotations

from dataclasses import replace

from gatesignal.decision import build_decision_brief
from gatesignal.examples import demo_project
from gatesignal.finance import analyze_cash_flows
from gatesignal.risk import analyze_risks, challenge_completion
from gatesignal.scoring import score_gate


def _demo_summaries():
    project = demo_project()
    return (
        score_gate(project["criteria"]),
        analyze_cash_flows(project["cash_flows"], project["metadata"]["discount_rate"]),
        analyze_risks(project["risks"]),
        challenge_completion(project["challenge"]),
    )


def test_demo_risk_is_not_ready_without_observable_trigger() -> None:
    _, _, risk, challenge = _demo_summaries()

    assert risk.high_or_critical == 3
    assert risk.untreated_high_or_critical == 1
    assert risk.contingency_coverage == 2 / 3
    assert challenge == 5 / 6


def test_decision_holds_demo_for_incomplete_high_risk_response() -> None:
    brief = build_decision_brief(*_demo_summaries())

    assert brief.disposition == "HOLD FOR RISK RESPONSE"
    assert "owner, observable trigger" in brief.required_actions[0]


def test_failed_hard_gate_has_priority_over_attractive_economics() -> None:
    gate, finance, risk, challenge = _demo_summaries()
    failing_gate = replace(gate, must_pass_failures=("Required safety evidence",))

    brief = build_decision_brief(failing_gate, finance, risk, challenge)

    assert brief.disposition == "REWORK OR STOP"
    assert "Required safety evidence" in brief.required_actions[0]

