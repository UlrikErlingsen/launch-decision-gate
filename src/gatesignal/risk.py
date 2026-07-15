"""Risk-register triage and challenge-process checks."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .errors import DataProblem


RISK_COLUMNS = [
    "risk",
    "owner",
    "probability",
    "impact",
    "evidence_strength",
    "mitigation",
    "trigger",
    "response",
]
CHALLENGE_COLUMNS = ["check", "completed", "note"]


@dataclass(frozen=True)
class RiskSummary:
    """Risk triage with contingency preparedness kept visible."""

    risks: pd.DataFrame
    high_or_critical: int
    untreated_high_or_critical: int
    contingency_coverage: float


def _as_bool(value: object) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    normalized = str(value).strip().lower()
    if normalized in {"true", "yes", "1", "y"}:
        return True
    if normalized in {"false", "no", "0", "n", "", "nan", "none"}:
        return False
    raise DataProblem(f"Could not read completed value ‘{value}’ as yes or no.")


def analyze_risks(frame: pd.DataFrame) -> RiskSummary:
    """Validate an ordinal 5×5 register and assess response preparedness."""
    missing = [column for column in RISK_COLUMNS if column not in frame.columns]
    if missing:
        raise DataProblem("The risk register is missing: " + ", ".join(missing) + ".")
    if frame.empty:
        raise DataProblem("Add at least one material project risk.")
    prepared = frame.loc[:, RISK_COLUMNS].copy()
    for column in ["risk", "owner", "mitigation", "trigger", "response"]:
        prepared[column] = prepared[column].fillna("").astype(str).str.strip()
    if prepared["risk"].eq("").any() or prepared["risk"].duplicated().any():
        raise DataProblem("Risk names must be unique and non-blank.")
    for column in ["probability", "impact", "evidence_strength"]:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
        if prepared[column].isna().any():
            raise DataProblem(f"Every risk {column.replace('_', ' ')} must be numeric.")
    if not prepared["probability"].between(1, 5).all() or not prepared["impact"].between(1, 5).all():
        raise DataProblem("Risk probability and impact ratings must be between 1 and 5.")
    if not prepared["evidence_strength"].between(0, 3).all():
        raise DataProblem("Risk evidence strength must be between 0 and 3.")
    prepared["risk_score"] = prepared["probability"] * prepared["impact"]
    prepared["risk_band"] = pd.cut(
        prepared["risk_score"],
        bins=[0, 4, 9, 15, 25],
        labels=["Low", "Medium", "High", "Critical"],
        include_lowest=True,
    ).astype(str)
    prepared["response_ready"] = (
        prepared["owner"].ne("") & prepared["mitigation"].ne("") & prepared["trigger"].ne("") & prepared["response"].ne("")
    )
    high = prepared["risk_band"].isin(["High", "Critical"])
    high_count = int(high.sum())
    untreated = int((high & ~prepared["response_ready"]).sum())
    coverage = float(prepared.loc[high, "response_ready"].mean()) if high_count else 1.0
    prepared = prepared.sort_values(["risk_score", "evidence_strength"], ascending=[False, True]).reset_index(drop=True)
    return RiskSummary(
        risks=prepared,
        high_or_critical=high_count,
        untreated_high_or_critical=untreated,
        contingency_coverage=coverage,
    )


def prepare_challenge(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate the documented challenge process."""
    missing = [column for column in CHALLENGE_COLUMNS if column not in frame.columns]
    if missing:
        raise DataProblem("The challenge checklist is missing: " + ", ".join(missing) + ".")
    if frame.empty:
        raise DataProblem("Add at least one independent challenge check.")
    prepared = frame.loc[:, CHALLENGE_COLUMNS].copy()
    prepared["check"] = prepared["check"].fillna("").astype(str).str.strip()
    prepared["note"] = prepared["note"].fillna("").astype(str).str.strip()
    if prepared["check"].eq("").any() or prepared["check"].duplicated().any():
        raise DataProblem("Challenge checks must be unique and non-blank.")
    prepared["completed"] = prepared["completed"].map(_as_bool)
    return prepared


def challenge_completion(frame: pd.DataFrame) -> float:
    """Return the share of documented challenge checks completed."""
    prepared = prepare_challenge(frame)
    return float(prepared["completed"].mean())
