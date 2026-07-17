"""Import summary evidence from sibling Signal apps without duplicating their engines."""

from __future__ import annotations

import json

from .errors import DataProblem

TRIAL_INTENTION_SCHEMA = "signal.trial-intention.v1"
PRICE_EVIDENCE_SCHEMA = "signal.price-evidence.v1"
MAX_INTEROP_BYTES = 5 * 1024 * 1024


def read_trial_intention(raw: bytes) -> dict[str, object]:
    """Read a ChoiceSignal trial-intention export (schema ``signal.trial-intention.v1``).

    Returns the concept name, sample size, and two candidate trial rates as
    decimals: the weighted stated-trial estimate and its unadjusted
    top-two-box ceiling. The file's own caveats travel along.
    """
    if not raw:
        raise DataProblem("This file is empty.")
    if len(raw) > MAX_INTEROP_BYTES:
        raise DataProblem("A trial-intention export should be a small JSON file; this one exceeds 5 MB.")
    try:
        payload = json.loads(raw.decode("utf-8-sig"))
    except Exception as exc:
        raise DataProblem("This file is not readable JSON. Export it from ChoiceSignal's concept-test page.") from exc
    if not isinstance(payload, dict) or payload.get("schema") != TRIAL_INTENTION_SCHEMA:
        raise DataProblem(
            "This is not a ChoiceSignal trial-intention export "
            f"(expected schema ‘{TRIAL_INTENTION_SCHEMA}’). Use the ‘Download trial intention JSON’ "
            "button on ChoiceSignal's concept-test page."
        )
    trial = payload.get("trial_assumption")
    if not isinstance(trial, dict):
        raise DataProblem("The export is missing its trial_assumption block; re-export it from ChoiceSignal.")
    try:
        weighted = float(trial["weighted_trial_%"])
        ceiling = float(trial["ceiling_top_two_box_%"])
        respondents = int(payload["respondents"])
    except (KeyError, TypeError, ValueError) as exc:
        raise DataProblem("The export is missing its trial numbers; re-export it from ChoiceSignal.") from exc
    if not (0 <= weighted <= 100 and 0 <= ceiling <= 100):
        raise DataProblem("Trial percentages in the export must lie between 0 and 100.")
    if respondents <= 0:
        raise DataProblem("The export reports no respondents.")
    generated_by = payload.get("generated_by") if isinstance(payload.get("generated_by"), dict) else {}
    return {
        "concept": str(payload.get("concept", "Unnamed concept")),
        "respondents": respondents,
        "weighted_trial_rate": weighted / 100.0,
        "ceiling_trial_rate": ceiling / 100.0,
        "source_product": str(generated_by.get("product", "ChoiceSignal")),
        "source_version": str(generated_by.get("version", "")),
        "note": str(trial.get("note", "")),
    }


def read_price_evidence(raw: bytes) -> dict[str, object]:
    """Read a TagSignal price-evidence export (schema ``signal.price-evidence.v1``).

    Returns the candidate and reference prices, the declared unit cost and the
    derived unit margin (candidate price minus declared unit cost), the projected
    volume, and the incremental contribution with its interval. The evidence
    tier, decision status, interpretation, and warning travel along.
    """
    if not raw:
        raise DataProblem("This file is empty.")
    if len(raw) > MAX_INTEROP_BYTES:
        raise DataProblem("A price-evidence export should be a small JSON file; this one exceeds 5 MB.")
    try:
        payload = json.loads(raw.decode("utf-8-sig"))
    except Exception as exc:
        raise DataProblem("This file is not readable JSON. Export it from TagSignal's evidence page.") from exc
    if not isinstance(payload, dict) or payload.get("schema") != PRICE_EVIDENCE_SCHEMA:
        raise DataProblem(
            "This is not a TagSignal price-evidence export "
            f"(expected schema ‘{PRICE_EVIDENCE_SCHEMA}’). Use the GateSignal bridge export "
            "on TagSignal's evidence page."
        )
    try:
        candidate_price = float(payload["candidate_price"])
        reference_price = float(payload["reference_price"])
        unit_cost = float(payload["declared_unit_cost"])
        volume = float(payload["candidate_projected_volume"])
        candidate_contribution = float(payload["candidate_contribution"])
        incremental = float(payload["incremental_contribution"])
    except (KeyError, TypeError, ValueError) as exc:
        raise DataProblem(
            "The export is missing its price or contribution numbers; re-export it from TagSignal."
        ) from exc
    interval = payload.get("incremental_contribution_interval")
    if (
        not isinstance(interval, (list, tuple))
        or len(interval) != 2
        or not all(isinstance(edge, (int, float)) and not isinstance(edge, bool) for edge in interval)
    ):
        raise DataProblem(
            "The incremental-contribution interval must be a two-number [low, high] list; "
            "re-export it from TagSignal."
        )
    low, high = float(interval[0]), float(interval[1])
    if low > high:
        raise DataProblem(
            "The incremental-contribution interval is reversed (low exceeds high); re-export it from TagSignal."
        )
    if candidate_price <= 0:
        raise DataProblem("The candidate price in the export must be greater than zero.")
    if unit_cost < 0:
        raise DataProblem("The declared unit cost in the export cannot be negative.")
    if volume < 0:
        raise DataProblem("The projected volume in the export cannot be negative.")
    producer = payload.get("producer") if isinstance(payload.get("producer"), dict) else {}
    return {
        "candidate_price": candidate_price,
        "reference_price": reference_price,
        "declared_unit_cost": unit_cost,
        "unit_margin": candidate_price - unit_cost,
        "candidate_projected_volume": volume,
        "candidate_contribution": candidate_contribution,
        "incremental_contribution": incremental,
        "incremental_contribution_interval": [low, high],
        "within_observed_support": bool(payload.get("within_observed_support", False)),
        "evidence_tier": str(payload.get("evidence_tier", "")),
        "decision_status": str(payload.get("decision_status", "")),
        "interpretation": str(payload.get("interpretation", "")),
        "warning": str(payload.get("warning", "")),
        "source_product": str(producer.get("product", "TagSignal")),
        "source_version": str(producer.get("version", "")),
    }
