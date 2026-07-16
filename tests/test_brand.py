from gatesignal.brand import analyze_brand_evidence
from gatesignal.decision import build_decision_brief
from gatesignal.examples import demo_project
from gatesignal.finance import analyze_cash_flows
from gatesignal.risk import analyze_risks, challenge_completion
from gatesignal.scoring import score_gate


def test_demo_covers_extension_alliance_and_reputation_domains() -> None:
    project = demo_project()
    summary = analyze_brand_evidence(project["brand_evidence"])

    assert summary.status == "CONDITIONAL BRAND SUPPORT"
    assert summary.material_concerns == 1
    assert not summary.blocking_items
    domains = set(summary.evidence["domain"])
    assert {"Category fit", "Transfer asymmetry", "Dilution and confusion", "Control and governance"} <= domains
    assert {"Disclosure", "Activism", "Reputation spillover"} <= domains


def test_must_resolve_brand_concern_holds_decision() -> None:
    project = demo_project()
    evidence = project["brand_evidence"].copy()
    evidence.loc[0, ["evidence_direction", "evidence_strength", "must_resolve"]] = ["Raises concern", 1, True]
    brand = analyze_brand_evidence(evidence)
    brief = build_decision_brief(
        score_gate(project["criteria"]),
        analyze_cash_flows(project["cash_flows"], project["metadata"]["discount_rate"]),
        analyze_risks(project["risks"]),
        challenge_completion(project["challenge"]),
        brand=brand,
    )

    assert brand.status == "BRAND RISK UNRESOLVED"
    assert brief.disposition == "HOLD FOR BRAND EVIDENCE"
    assert "brand evidence blocker" in brief.required_actions[0]
