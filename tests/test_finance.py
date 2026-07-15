from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from gatesignal.errors import DataProblem
from gatesignal.examples import demo_project
from gatesignal.finance import analyze_cash_flows, analyze_volume_bridge, npv, unique_irr


def test_npv_and_unique_irr_for_conventional_cash_flow() -> None:
    cash_flows = np.array([-100.0, 110.0])

    assert npv(cash_flows, 0.10) == pytest.approx(0.0)
    assert unique_irr(cash_flows) == pytest.approx(0.10)


def test_irr_is_suppressed_for_multiple_sign_changes() -> None:
    assert unique_irr(np.array([-100.0, 230.0, -132.0])) is None


def test_demo_finance_uses_probability_weighted_scenarios() -> None:
    project = demo_project()
    summary = analyze_cash_flows(project["cash_flows"], project["metadata"]["discount_rate"])

    manual = float((summary.scenarios["probability"] * summary.scenarios["npv"]).sum())
    assert summary.expected_npv == pytest.approx(manual)
    assert summary.reference_scenario == "Base"
    assert summary.reference_npv > 0
    assert summary.probability_negative_npv == pytest.approx(0.25)


def test_scenario_probabilities_must_sum_to_one() -> None:
    cash_flows = pd.DataFrame(
        [["Down", 0.4, 0, -100], ["Down", 0.4, 1, 80], ["Up", 0.4, 0, -100], ["Up", 0.4, 1, 130]],
        columns=["scenario", "probability", "period", "cash_flow"],
    )

    with pytest.raises(DataProblem, match="sum to 1.00"):
        analyze_cash_flows(cash_flows, 0.10)


def test_volume_bridge_exposes_reach_trial_and_repeat_arithmetic() -> None:
    row = analyze_volume_bridge(demo_project()["volume_bridge"]).query("scenario == 'Base'").iloc[0]
    trials = 180_000 * 0.42 * 0.60 * 0.16
    repeat_units = trials * 0.42 * 1.5

    assert row["first_time_trials"] == pytest.approx(trials)
    assert row["repeat_units"] == pytest.approx(repeat_units)
    assert row["modeled_contribution"] == pytest.approx((trials + repeat_units) * 58)

