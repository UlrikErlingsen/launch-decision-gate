"""Scenario cash-flow and volume-bridge calculations."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .errors import DataProblem


CASH_FLOW_COLUMNS = ["scenario", "probability", "period", "cash_flow"]
VOLUME_COLUMNS = [
    "scenario",
    "market_size",
    "awareness_rate",
    "availability_rate",
    "trial_rate",
    "repeat_rate",
    "additional_units_per_repeater",
    "unit_contribution",
]


@dataclass(frozen=True)
class FinanceSummary:
    """Scenario economics with NPV as the primary decision measure."""

    discount_rate: float
    expected_npv: float
    probability_negative_npv: float
    reference_scenario: str
    reference_npv: float
    scenarios: pd.DataFrame
    cash_flows: pd.DataFrame


def _cash_flow_vector(group: pd.DataFrame) -> np.ndarray:
    maximum = int(group["period"].max())
    vector = np.zeros(maximum + 1, dtype=float)
    vector[group["period"].astype(int).to_numpy()] = group["cash_flow"].to_numpy(dtype=float)
    return vector


def npv(cash_flows: np.ndarray, discount_rate: float) -> float:
    """Discount period-indexed cash flows, including period zero."""
    periods = np.arange(len(cash_flows), dtype=float)
    return float(np.sum(cash_flows / np.power(1.0 + discount_rate, periods)))


def unique_irr(cash_flows: np.ndarray) -> float | None:
    """Return IRR only when the cash-flow pattern has one sign change and one valid real root."""
    nonzero = cash_flows[np.abs(cash_flows) > 1e-12]
    if len(nonzero) < 2:
        return None
    sign_changes = int(np.sum(np.sign(nonzero[1:]) != np.sign(nonzero[:-1])))
    if sign_changes != 1:
        return None
    roots = np.roots(cash_flows[::-1])
    candidates: list[float] = []
    for root in roots:
        if abs(root.imag) > 1e-8 or root.real <= 0:
            continue
        rate = 1.0 / root.real - 1.0
        if rate > -1.0 and np.isfinite(rate):
            candidates.append(float(rate))
    unique = sorted({round(value, 10) for value in candidates})
    return unique[0] if len(unique) == 1 else None


def discounted_payback(cash_flows: np.ndarray, discount_rate: float) -> float | None:
    """Return the first discounted payback period, with linear interpolation."""
    discounted = cash_flows / np.power(1.0 + discount_rate, np.arange(len(cash_flows), dtype=float))
    cumulative = np.cumsum(discounted)
    if cumulative[0] >= 0:
        return 0.0
    hits = np.flatnonzero(cumulative >= 0)
    if len(hits) == 0:
        return None
    period = int(hits[0])
    previous = float(cumulative[period - 1])
    current_flow = float(discounted[period])
    if current_flow <= 0:
        return float(period)
    return float((period - 1) + (-previous / current_flow))


def prepare_cash_flows(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate a long table with one row per scenario and period."""
    missing = [column for column in CASH_FLOW_COLUMNS if column not in frame.columns]
    if missing:
        raise DataProblem("The cash-flow table is missing: " + ", ".join(missing) + ".")
    if frame.empty:
        raise DataProblem("Add at least one cash-flow scenario.")
    prepared = frame.loc[:, CASH_FLOW_COLUMNS].copy()
    prepared["scenario"] = prepared["scenario"].fillna("").astype(str).str.strip()
    if prepared["scenario"].eq("").any():
        raise DataProblem("Every cash-flow row needs a scenario name.")
    for column in ["probability", "period", "cash_flow"]:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
        if prepared[column].isna().any():
            raise DataProblem(f"Every cash-flow {column} must be numeric.")
    if not prepared["probability"].between(0, 1).all():
        raise DataProblem("Scenario probabilities must be decimals between 0 and 1.")
    if (prepared["period"] < 0).any() or not np.allclose(prepared["period"], np.round(prepared["period"])):
        raise DataProblem("Cash-flow periods must be whole numbers starting at zero.")
    prepared["period"] = prepared["period"].astype(int)
    if prepared.duplicated(["scenario", "period"]).any():
        raise DataProblem("Each scenario-period pair must appear only once.")
    probabilities = prepared.groupby("scenario", sort=False)["probability"].agg(["min", "max"])
    if not np.allclose(probabilities["min"], probabilities["max"]):
        raise DataProblem("Use one consistent probability on every row of the same scenario.")
    total_probability = float(probabilities["max"].sum())
    if not np.isclose(total_probability, 1.0, atol=1e-6):
        raise DataProblem(f"Scenario probabilities must sum to 1.00; they currently sum to {total_probability:.3f}.")
    return prepared.sort_values(["scenario", "period"], kind="stable").reset_index(drop=True)


def analyze_cash_flows(frame: pd.DataFrame, discount_rate: float) -> FinanceSummary:
    """Calculate scenario NPV, constrained IRR, and discounted payback."""
    if not 0 <= discount_rate <= 1:
        raise DataProblem("The discount rate must be between 0% and 100%.")
    prepared = prepare_cash_flows(frame)
    rows: list[dict[str, object]] = []
    for scenario, group in prepared.groupby("scenario", sort=False):
        vector = _cash_flow_vector(group)
        probability = float(group["probability"].iloc[0])
        scenario_npv = npv(vector, discount_rate)
        irr = unique_irr(vector)
        payback = discounted_payback(vector, discount_rate)
        rows.append(
            {
                "scenario": scenario,
                "probability": probability,
                "npv": scenario_npv,
                "irr": irr,
                "discounted_payback": payback,
                "initial_cash_flow": float(vector[0]),
                "undiscounted_total": float(vector.sum()),
            }
        )
    scenarios = pd.DataFrame(rows)
    expected_npv = float((scenarios["probability"] * scenarios["npv"]).sum())
    probability_negative = float(scenarios.loc[scenarios["npv"] < 0, "probability"].sum())
    base_matches = scenarios["scenario"].str.casefold().eq("base")
    reference = scenarios.loc[base_matches].iloc[0] if base_matches.any() else scenarios.iloc[scenarios["probability"].argmax()]
    return FinanceSummary(
        discount_rate=float(discount_rate),
        expected_npv=expected_npv,
        probability_negative_npv=probability_negative,
        reference_scenario=str(reference["scenario"]),
        reference_npv=float(reference["npv"]),
        scenarios=scenarios,
        cash_flows=prepared,
    )


def analyze_volume_bridge(frame: pd.DataFrame) -> pd.DataFrame:
    """Turn explicit reach, trial, and repeat assumptions into scenario volume."""
    missing = [column for column in VOLUME_COLUMNS if column not in frame.columns]
    if missing:
        raise DataProblem("The volume bridge is missing: " + ", ".join(missing) + ".")
    if frame.empty:
        raise DataProblem("Add at least one volume scenario.")
    prepared = frame.loc[:, VOLUME_COLUMNS].copy()
    prepared["scenario"] = prepared["scenario"].fillna("").astype(str).str.strip()
    if prepared["scenario"].eq("").any() or prepared["scenario"].duplicated().any():
        raise DataProblem("Volume scenarios need unique, non-blank names.")
    for column in VOLUME_COLUMNS[1:]:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
        if prepared[column].isna().any():
            raise DataProblem(f"Every {column.replace('_', ' ')} must be numeric.")
    for column in ["awareness_rate", "availability_rate", "trial_rate", "repeat_rate"]:
        if not prepared[column].between(0, 1).all():
            raise DataProblem(f"{column.replace('_', ' ').title()} must be between 0 and 1.")
    if (prepared[["market_size", "additional_units_per_repeater", "unit_contribution"]] < 0).any().any():
        raise DataProblem("Market size, additional units, and unit contribution cannot be negative.")
    prepared["first_time_trials"] = (
        prepared["market_size"]
        * prepared["awareness_rate"]
        * prepared["availability_rate"]
        * prepared["trial_rate"]
    )
    prepared["repeat_units"] = (
        prepared["first_time_trials"] * prepared["repeat_rate"] * prepared["additional_units_per_repeater"]
    )
    prepared["total_units"] = prepared["first_time_trials"] + prepared["repeat_units"]
    prepared["modeled_contribution"] = prepared["total_units"] * prepared["unit_contribution"]
    return prepared
