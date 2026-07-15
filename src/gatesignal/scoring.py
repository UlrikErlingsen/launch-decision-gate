"""Transparent multi-criteria scoring with non-compensatory must-pass checks."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .errors import DataProblem


CRITERIA_COLUMNS = [
    "category",
    "criterion",
    "weight",
    "score",
    "evidence_strength",
    "must_pass",
    "threshold",
    "evidence_note",
]


@dataclass(frozen=True)
class GateSummary:
    """A scored gate with evidence quality kept separate from preference scores."""

    weighted_score: float
    evidence_coverage: float
    must_pass_failures: tuple[str, ...]
    criteria: pd.DataFrame
    evidence_gaps: pd.DataFrame
    score_range_if_one_point_wrong: tuple[float, float]


def _as_bool(value: object) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    normalized = str(value).strip().lower()
    if normalized in {"true", "yes", "1", "y"}:
        return True
    if normalized in {"false", "no", "0", "n", "", "nan", "none"}:
        return False
    raise DataProblem(f"Could not read must_pass value ‘{value}’ as yes or no.")


def prepare_criteria(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize one row per decision criterion."""
    missing = [column for column in CRITERIA_COLUMNS if column not in frame.columns]
    if missing:
        raise DataProblem("The criteria table is missing: " + ", ".join(missing) + ".")
    if frame.empty:
        raise DataProblem("Add at least one criterion before scoring the gate.")

    prepared = frame.loc[:, CRITERIA_COLUMNS].copy()
    for column in ["category", "criterion", "evidence_note"]:
        prepared[column] = prepared[column].fillna("").astype(str).str.strip()
    if prepared["criterion"].eq("").any():
        raise DataProblem("Every criterion needs a short, specific name.")
    if prepared["criterion"].duplicated().any():
        duplicates = prepared.loc[prepared["criterion"].duplicated(), "criterion"].tolist()
        raise DataProblem("Criterion names must be unique. Repeated: " + ", ".join(duplicates[:5]) + ".")

    for column in ["weight", "score", "evidence_strength", "threshold"]:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
        if prepared[column].isna().any():
            raise DataProblem(f"Every {column.replace('_', ' ')} must be numeric.")
    if (prepared["weight"] <= 0).any():
        raise DataProblem("Criterion weights must be greater than zero.")
    if not prepared["score"].between(0, 10).all():
        raise DataProblem("Criterion scores must be between 0 and 10.")
    if not prepared["threshold"].between(0, 10).all():
        raise DataProblem("Must-pass thresholds must be between 0 and 10.")
    if not prepared["evidence_strength"].between(0, 3).all():
        raise DataProblem("Evidence strength must be between 0 (none) and 3 (strong).")

    prepared["must_pass"] = prepared["must_pass"].map(_as_bool)
    weight_total = float(prepared["weight"].sum())
    prepared["normalized_weight"] = prepared["weight"] / weight_total
    prepared["weighted_contribution"] = prepared["normalized_weight"] * prepared["score"]
    prepared["evidence_coverage_contribution"] = (
        prepared["normalized_weight"] * prepared["evidence_strength"] / 3.0
    )
    prepared["must_pass_status"] = np.where(
        ~prepared["must_pass"],
        "Not a hard gate",
        np.where(prepared["score"] >= prepared["threshold"], "Pass", "Fail"),
    )
    return prepared


def score_gate(frame: pd.DataFrame) -> GateSummary:
    """Score criteria while preserving hard failures and evidence gaps."""
    criteria = prepare_criteria(frame)
    weighted_score = float(criteria["weighted_contribution"].sum())
    evidence_coverage = float(criteria["evidence_coverage_contribution"].sum())
    failures = tuple(
        criteria.loc[criteria["must_pass_status"].eq("Fail"), "criterion"].astype(str).tolist()
    )
    gaps = criteria.loc[
        criteria["evidence_strength"].le(1),
        ["category", "criterion", "normalized_weight", "score", "evidence_strength", "must_pass", "evidence_note"],
    ].sort_values(["must_pass", "normalized_weight"], ascending=[False, False])

    uncertainty = float(criteria["normalized_weight"].sum())
    score_range = (max(0.0, weighted_score - uncertainty), min(10.0, weighted_score + uncertainty))
    return GateSummary(
        weighted_score=weighted_score,
        evidence_coverage=evidence_coverage,
        must_pass_failures=failures,
        criteria=criteria,
        evidence_gaps=gaps.reset_index(drop=True),
        score_range_if_one_point_wrong=score_range,
    )
