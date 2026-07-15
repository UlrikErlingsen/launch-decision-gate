"""Import summary evidence from sibling Signal apps without duplicating their engines."""

from __future__ import annotations

import json

from .errors import DataProblem

TRIAL_INTENTION_SCHEMA = "signal.trial-intention.v1"
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
