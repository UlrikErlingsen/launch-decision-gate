from __future__ import annotations

import pytest

from gatesignal.examples import demo_project
from gatesignal.scoring import score_gate


def test_demo_scoring_separates_preferences_evidence_and_hard_gates() -> None:
    summary = score_gate(demo_project()["criteria"])

    assert summary.weighted_score == pytest.approx(6.87)
    assert summary.evidence_coverage == pytest.approx(0.5833333333)
    assert summary.must_pass_failures == ()
    assert set(summary.evidence_gaps["criterion"]) == {
        "The metered cap performs consistently across concentrates",
        "Materials and instructions support safe intended use",
        "The team can source, fill, and support the launch",
    }
    assert summary.score_range_if_one_point_wrong == pytest.approx((5.87, 7.87))


def test_hard_gate_failure_is_not_offset_by_high_average() -> None:
    criteria = demo_project()["criteria"].copy()
    criteria.loc[:, "score"] = 10
    safety = criteria["category"].eq("Safety")
    criteria.loc[safety, "score"] = 5
    criteria.loc[safety, "threshold"] = 6

    summary = score_gate(criteria)

    assert summary.weighted_score > 9
    assert summary.must_pass_failures == ("Materials and instructions support safe intended use",)


def test_raw_weights_are_normalized() -> None:
    criteria = demo_project()["criteria"].copy()
    doubled = criteria.copy()
    doubled["weight"] *= 2

    assert score_gate(criteria).weighted_score == pytest.approx(score_gate(doubled).weighted_score)
