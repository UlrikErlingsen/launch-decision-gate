"""GateSignal's transparent decision-support engine."""

__version__ = "1.0.0"

from .decision import DecisionBrief, build_decision_brief
from .finance import FinanceSummary, analyze_cash_flows, analyze_volume_bridge
from .risk import RiskSummary, analyze_risks, challenge_completion
from .scoring import GateSummary, score_gate

__all__ = [
    "DecisionBrief",
    "FinanceSummary",
    "GateSummary",
    "RiskSummary",
    "analyze_cash_flows",
    "analyze_risks",
    "analyze_volume_bridge",
    "build_decision_brief",
    "challenge_completion",
    "score_gate",
]
