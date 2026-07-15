"""Traceable gate recommendation rules."""

from __future__ import annotations

from dataclasses import dataclass

from .finance import FinanceSummary
from .risk import RiskSummary
from .scoring import GateSummary


@dataclass(frozen=True)
class DecisionBrief:
    """A model-generated disposition for discussion, never an automatic approval."""

    disposition: str
    headline: str
    reasons: tuple[str, ...]
    required_actions: tuple[str, ...]


def build_decision_brief(
    gate: GateSummary,
    finance: FinanceSummary,
    risk: RiskSummary,
    challenge_completion: float,
) -> DecisionBrief:
    """Apply explicit, conservative rules in priority order."""
    reasons = [
        f"Weighted criterion score: {gate.weighted_score:.2f}/10.",
        f"Evidence coverage: {gate.evidence_coverage:.0%}.",
        f"Probability-weighted NPV: {finance.expected_npv:,.0f}.",
        f"Untreated high or critical risks: {risk.untreated_high_or_critical}.",
        f"Independent challenge checks completed: {challenge_completion:.0%}.",
    ]
    actions: list[str] = []

    if gate.must_pass_failures:
        actions.extend(f"Resolve the must-pass failure: {criterion}." for criterion in gate.must_pass_failures)
        return DecisionBrief(
            disposition="REWORK OR STOP",
            headline="A non-compensatory gate has failed; the weighted average cannot override it.",
            reasons=tuple(reasons),
            required_actions=tuple(actions),
        )
    if gate.weighted_score < 5:
        actions.append("Redesign the concept or document why scarce resources should remain committed.")
        return DecisionBrief(
            disposition="STOP OR REDESIGN",
            headline="The current concept scores weakly across the declared decision criteria.",
            reasons=tuple(reasons),
            required_actions=tuple(actions),
        )
    if finance.expected_npv < 0 and finance.reference_npv < 0:
        actions.append("Change price, cost, volume, timing, or scope assumptions and rebuild the cash-flow cases.")
        return DecisionBrief(
            disposition="REWORK ECONOMICS",
            headline="Both the reference case and probability-weighted economics are negative.",
            reasons=tuple(reasons),
            required_actions=tuple(actions),
        )
    if risk.untreated_high_or_critical:
        actions.append("Assign an owner, observable trigger, and executable response to every high or critical risk.")
        return DecisionBrief(
            disposition="HOLD FOR RISK RESPONSE",
            headline="Material risks do not yet have complete contingency responses.",
            reasons=tuple(reasons),
            required_actions=tuple(actions),
        )
    if gate.evidence_coverage < 0.60:
        actions.append("Strengthen the highest-weight evidence gaps before committing the next irreversible spend.")
        return DecisionBrief(
            disposition="HOLD FOR EVIDENCE",
            headline="The preference score is more confident than the supporting evidence warrants.",
            reasons=tuple(reasons),
            required_actions=tuple(actions),
        )
    if challenge_completion < 2 / 3:
        actions.append("Complete the independent challenge checks and record disconfirming evidence.")
        return DecisionBrief(
            disposition="HOLD FOR CHALLENGE",
            headline="The case has not yet received enough documented independent challenge.",
            reasons=tuple(reasons),
            required_actions=tuple(actions),
        )

    actions.append("Record the accountable decision owner, funding limit, learning milestone, and next review date.")
    return DecisionBrief(
        disposition="CONSIDER GO",
        headline="No declared hard gate is failing, economics are positive, and the case is ready for accountable review.",
        reasons=tuple(reasons),
        required_actions=tuple(actions),
    )
