"""Brand-extension and alliance evidence audit for GateSignal."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .errors import DataProblem


BRAND_EVIDENCE_COLUMNS = [
    "domain",
    "claim_or_risk",
    "evidence_direction",
    "evidence_strength",
    "materiality",
    "must_resolve",
    "owner",
    "evidence_note",
    "next_test",
]
BRAND_EVIDENCE_DIRECTIONS = ["Supports", "Neutral / mixed", "Raises concern", "Not assessed"]


@dataclass(frozen=True)
class BrandEvidenceSummary:
    evidence: pd.DataFrame
    evidence_gaps: pd.DataFrame
    blocking_items: tuple[str, ...]
    material_concerns: int
    evidence_coverage: float
    status: str


def _as_bool(value: object) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    normalized = str(value).strip().lower()
    if normalized in {"true", "yes", "1", "y"}:
        return True
    if normalized in {"false", "no", "0", "n", "", "nan", "none"}:
        return False
    raise DataProblem(f"Could not read must_resolve value ‘{value}’ as yes or no.")


def analyze_brand_evidence(frame: pd.DataFrame) -> BrandEvidenceSummary:
    """Audit brand-extension/alliance claims without converting them into a success probability."""
    missing = [column for column in BRAND_EVIDENCE_COLUMNS if column not in frame.columns]
    if missing:
        raise DataProblem("The brand evidence section is missing: " + ", ".join(missing) + ".")
    if frame.empty:
        raise DataProblem("Add at least one brand-extension or alliance evidence question.")
    prepared = frame.loc[:, BRAND_EVIDENCE_COLUMNS].copy()
    for column in ["domain", "claim_or_risk", "evidence_direction", "owner", "evidence_note", "next_test"]:
        prepared[column] = prepared[column].fillna("").astype(str).str.strip()
    if prepared["domain"].eq("").any() or prepared["claim_or_risk"].eq("").any():
        raise DataProblem("Every brand evidence row needs a domain and a specific claim or risk.")
    if prepared["claim_or_risk"].duplicated().any():
        raise DataProblem("Brand evidence claims or risks must be unique.")
    if not prepared["evidence_direction"].isin(BRAND_EVIDENCE_DIRECTIONS).all():
        raise DataProblem("Brand evidence direction must use the available support, mixed, concern, or not-assessed labels.")
    for column in ["evidence_strength", "materiality"]:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
        if prepared[column].isna().any():
            raise DataProblem(f"Every brand {column.replace('_', ' ')} must be numeric.")
    if not prepared["evidence_strength"].between(0, 3).all():
        raise DataProblem("Brand evidence strength must be between 0 (none) and 3 (strong).")
    if not prepared["materiality"].between(1, 5).all():
        raise DataProblem("Brand materiality must be between 1 and 5.")
    prepared["must_resolve"] = prepared["must_resolve"].map(_as_bool)
    prepared["evidence_gap"] = prepared["evidence_strength"].le(1) | prepared["evidence_direction"].eq("Not assessed")
    prepared["material_concern"] = prepared["evidence_direction"].eq("Raises concern") & prepared["materiality"].ge(4)
    prepared["response_documented"] = prepared["owner"].ne("") & prepared["next_test"].ne("")
    prepared["blocking"] = (
        prepared["must_resolve"]
        & (
            prepared["evidence_gap"]
            | prepared["evidence_direction"].isin(["Raises concern", "Not assessed"])
        )
    ) | (prepared["material_concern"] & ~prepared["response_documented"])
    prepared["coverage_contribution"] = prepared["materiality"] * prepared["evidence_strength"] / 3.0
    evidence_coverage = float(prepared["coverage_contribution"].sum() / prepared["materiality"].sum())
    blocking_items = tuple(prepared.loc[prepared["blocking"], "claim_or_risk"].astype(str).tolist())
    material_concerns = int(prepared["material_concern"].sum())
    gaps = prepared.loc[
        prepared["evidence_gap"] | prepared["blocking"],
        [
            "domain", "claim_or_risk", "evidence_direction", "evidence_strength", "materiality",
            "must_resolve", "owner", "evidence_note", "next_test", "blocking",
        ],
    ].sort_values(["blocking", "materiality", "evidence_strength"], ascending=[False, False, True])
    if blocking_items:
        status = "BRAND RISK UNRESOLVED"
    elif evidence_coverage < 0.60 or prepared["evidence_direction"].eq("Not assessed").any():
        status = "BRAND EVIDENCE INCOMPLETE"
    elif material_concerns:
        status = "CONDITIONAL BRAND SUPPORT"
    else:
        status = "NO AUTOMATIC BRAND CLEARANCE"
    prepared = prepared.drop(columns="coverage_contribution")
    return BrandEvidenceSummary(
        evidence=prepared,
        evidence_gaps=gaps.reset_index(drop=True),
        blocking_items=blocking_items,
        material_concerns=material_concerns,
        evidence_coverage=evidence_coverage,
        status=status,
    )
