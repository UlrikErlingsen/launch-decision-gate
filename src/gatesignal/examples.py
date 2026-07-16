"""Original blank and fictional project bundles used by the app and tests."""

from __future__ import annotations

import pandas as pd

from .brand import BRAND_EVIDENCE_COLUMNS
from .finance import CASH_FLOW_COLUMNS, VOLUME_COLUMNS
from .risk import CHALLENGE_COLUMNS, RISK_COLUMNS
from .scoring import CRITERIA_COLUMNS


def default_challenge() -> pd.DataFrame:
    """Return an independently worded challenge checklist."""
    return pd.DataFrame(
        [
            ["A relevant outside-view base rate has been documented", False, ""],
            ["Evidence that could disconfirm the case has been recorded", False, ""],
            ["Past spending has been excluded from the forward decision", False, ""],
            ["A reviewer without delivery ownership has challenged the case", False, ""],
            ["Every material forecast has a named assumption owner", False, ""],
            ["The next commitment is bounded by a measurable learning milestone", False, ""],
        ],
        columns=CHALLENGE_COLUMNS,
    )


def blank_brand_evidence() -> pd.DataFrame:
    """Return independent prompts spanning extension, alliance, disclosure, and reputation risk."""
    rows = [
        ["Category fit", "The proposed category use is credible for the focal brand", "Not assessed", 0, 5, False, "", "", ""],
        ["Image and value fit", "Brand meanings and customer expectations fit the offer or partner", "Not assessed", 0, 4, False, "", "", ""],
        ["Transfer asymmetry", "Positive associations transfer in both directions without one party carrying most downside", "Not assessed", 0, 4, False, "", "", ""],
        ["Dilution and confusion", "The extension or alliance will not blur, weaken, or contradict core brand meaning", "Not assessed", 0, 5, False, "", "", ""],
        ["Control and governance", "Rights, quality control, exit, data use, and incident authority are explicit", "Not assessed", 0, 5, False, "", "", ""],
        ["Disclosure", "Customers can recognize the commercial relationship and material claims", "Not assessed", 0, 4, False, "", "", ""],
        ["Activism", "Public positions are congruent with behavior, stakeholder expectations, and partner conduct", "Not assessed", 0, 4, False, "", "", ""],
        ["Reputation spillover", "Partner, category, and controversy spillovers have an owned response and exit path", "Not assessed", 0, 5, False, "", "", ""],
    ]
    return pd.DataFrame(rows, columns=BRAND_EVIDENCE_COLUMNS)


def blank_project() -> dict[str, object]:
    """Return a small editable project bundle without hidden defaults."""
    return {
        "metadata": {
            "project_name": "Untitled concept",
            "decision_question": "Should this concept receive the next bounded investment?",
            "decision_owner": "",
            "review_stage": "Concept review",
            "currency": "NOK",
            "discount_rate": 0.12,
        },
        "criteria": pd.DataFrame(
            [
                ["Customer", "The problem is material for the target user", 1.0, 5.0, 0.0, True, 6.0, ""],
                ["Feasibility", "A credible delivery path exists", 1.0, 5.0, 0.0, True, 6.0, ""],
                ["Economics", "Forward economics clear the declared hurdle", 1.0, 5.0, 0.0, True, 5.0, ""],
            ],
            columns=CRITERIA_COLUMNS,
        ),
        "cash_flows": pd.DataFrame(
            [
                ["Base", 1.0, 0, -100_000.0],
                ["Base", 1.0, 1, 60_000.0],
                ["Base", 1.0, 2, 70_000.0],
            ],
            columns=CASH_FLOW_COLUMNS,
        ),
        "volume_bridge": pd.DataFrame(
            [["Base", 10_000.0, 0.40, 0.70, 0.20, 0.35, 1.0, 100.0]],
            columns=VOLUME_COLUMNS,
        ),
        "risks": pd.DataFrame(
            [["Describe the most material uncertainty", "", 3, 3, 0, "", "", ""]],
            columns=RISK_COLUMNS,
        ),
        "brand_evidence": blank_brand_evidence(),
        "challenge": default_challenge(),
    }


def demo_project() -> dict[str, object]:
    """Return a fully fictional concept case created for GateSignal."""
    criteria = pd.DataFrame(
        [
            ["Strategy", "Fits the sponsor's refill and reuse direction", 12, 8, 2, False, 6, "Strategy memo and capability interview"],
            ["Customer", "Target households experience the stated storage problem", 16, 7, 2, True, 6, "Twelve interviews plus a small concept survey"],
            ["Value", "The concept is meaningfully different from current refills", 12, 7, 2, False, 6, "Competitor teardown and concept comparison"],
            ["Feasibility", "The metered cap performs consistently across concentrates", 15, 6, 1, True, 6, "Bench prototype; extended-use test pending"],
            ["Safety", "Materials and instructions support safe intended use", 10, 6, 1, True, 6, "Supplier declarations; compatibility test pending"],
            ["Economics", "Forward unit and project economics clear the hurdle", 15, 7, 2, True, 5, "Supplier quotes and three demand cases"],
            ["Delivery", "The team can source, fill, and support the launch", 10, 6, 1, False, 5, "One supplier qualified; backup not qualified"],
            ["Learning", "The next spend buys evidence on the largest uncertainties", 10, 8, 3, False, 6, "Bounded pilot plan with stop conditions"],
        ],
        columns=CRITERIA_COLUMNS,
    )

    cash_rows: list[list[object]] = []
    cash_cases = {
        "Downside": (0.25, [-720_000, 80_000, 170_000, 210_000, 190_000]),
        "Base": (0.50, [-720_000, 170_000, 320_000, 410_000, 350_000]),
        "Upside": (0.25, [-720_000, 260_000, 470_000, 620_000, 500_000]),
    }
    for scenario, (probability, values) in cash_cases.items():
        cash_rows.extend([scenario, probability, period, value] for period, value in enumerate(values))

    volume = pd.DataFrame(
        [
            ["Downside", 180_000, 0.28, 0.45, 0.10, 0.30, 1.2, 54.0],
            ["Base", 180_000, 0.42, 0.60, 0.16, 0.42, 1.5, 58.0],
            ["Upside", 180_000, 0.55, 0.72, 0.22, 0.52, 1.8, 61.0],
        ],
        columns=VOLUME_COLUMNS,
    )

    risks = pd.DataFrame(
        [
            [
                "Concentrate damages a surface when instructions are ignored",
                "Product lead",
                2,
                5,
                1,
                "Compatibility tests, clear exclusions, and packaging review",
                "Any severe pilot incident or repeated minor pattern",
                "Pause affected use case, investigate, and revise formula or instructions",
            ],
            [
                "Single cap supplier cannot hold metering tolerance",
                "Operations lead",
                3,
                4,
                2,
                "Tighten acceptance specification and qualify a second supplier",
                "",
                "Move volume to backup tooling and narrow supported concentrates",
            ],
            [
                "Retail placement produces less availability than planned",
                "Commercial lead",
                3,
                3,
                1,
                "Run a limited channel pilot before national commitments",
                "Four-week weighted availability remains below 45%",
                "Shift launch volume to direct and specialist channels",
            ],
            [
                "Repeat use is weaker than stated concept interest",
                "Insights lead",
                3,
                4,
                1,
                "Measure observed reuse and refill orders in the pilot",
                "Eight-week repeat rate remains below 28%",
                "Stop expansion and diagnose product experience before redesign",
            ],
        ],
        columns=RISK_COLUMNS,
    )

    challenge = default_challenge()
    challenge.loc[:, "completed"] = [True, True, True, False, True, True]
    challenge.loc[:, "note"] = [
        "Compared with three recent refill launches available to the team",
        "Key counter-case: customers may prefer ready-to-use formats",
        "All values use future cash flows only",
        "Independent operations reviewer is scheduled",
        "Owners named in the assumptions file",
        "Pilot budget and stop conditions drafted",
    ]

    brand_evidence = pd.DataFrame(
        [
            ["Category fit", "The home-care category use is credible for the focal brand", "Supports", 2, 5, False, "Brand lead", "Fictional concept interviews and portfolio review", "Confirm fit in a pre-specified concept comparison"],
            ["Image and value fit", "Refill behavior fits the brand's convenience and waste-reduction meanings", "Supports", 2, 4, False, "Insights lead", "Fictional qualitative pattern; no market claim", "Quantify fit and relevance in the pilot sample"],
            ["Transfer asymmetry", "The cap supplier gains visibility while the focal brand carries most customer downside", "Raises concern", 2, 4, False, "Partnership lead", "Responsibility mapping identifies asymmetric customer exposure", "Negotiate reciprocal warranties and incident obligations"],
            ["Dilution and confusion", "The system will not weaken the brand through complexity or unsafe-use confusion", "Neutral / mixed", 2, 5, False, "Brand lead", "Instructions tested only in a small fictional prototype review", "Run comprehension and brand-feedback checks after extended use"],
            ["Control and governance", "Quality control, incident authority, data use, and exit rights are explicit", "Supports", 2, 5, False, "Legal lead", "Draft supplier quality agreement and escalation map", "Close remaining exit and recall clauses before pilot"],
            ["Disclosure", "Customers can identify the system relationship and material environmental claims", "Supports", 3, 4, False, "Compliance lead", "Draft packaging disclosure and claim substantiation file", "Verify recognition and comprehension in label testing"],
            ["Activism", "Waste-reduction communication is congruent with operating behavior and partner conduct", "Neutral / mixed", 2, 4, False, "Sustainability lead", "Claim inventory linked to fictional operating assumptions", "Independent review of claims and supplier conduct"],
            ["Reputation spillover", "Supplier or product incidents have an owned communication and exit path", "Supports", 2, 5, False, "Communications lead", "Draft incident roles and holding statements", "Tabletop test the escalation and exit process"],
        ],
        columns=BRAND_EVIDENCE_COLUMNS,
    )

    return {
        "metadata": {
            "project_name": "LoopDose cleaning concentrate system",
            "decision_question": "Should the fictional LoopDose concept receive funding for a bounded market pilot?",
            "decision_owner": "HomeCare investment committee (fictional)",
            "review_stage": "Concept evidence",
            "currency": "NOK",
            "discount_rate": 0.12,
        },
        "criteria": criteria,
        "cash_flows": pd.DataFrame(cash_rows, columns=CASH_FLOW_COLUMNS),
        "volume_bridge": volume,
        "risks": risks,
        "brand_evidence": brand_evidence,
        "challenge": challenge,
    }
