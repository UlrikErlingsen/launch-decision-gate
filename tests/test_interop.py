"""Tests for the ChoiceSignal trial-intention and TagSignal price-evidence imports."""

import json

import pytest

from gatesignal.errors import DataProblem
from gatesignal.interop import (
    PRICE_EVIDENCE_SCHEMA,
    TRIAL_INTENTION_SCHEMA,
    read_price_evidence,
    read_trial_intention,
)


def _payload(**overrides):
    payload = {
        "schema": TRIAL_INTENTION_SCHEMA,
        "generated_by": {"product": "ChoiceSignal", "version": "1.2.0"},
        "concept": "Cold brew subscription",
        "respondents": 260,
        "trial_assumption": {
            "weights": {"Definitely would buy": 0.8},
            "weighted_trial_%": 21.08,
            "ceiling_top_two_box_%": 39.23,
            "note": "Stated intent overstates real trial.",
        },
    }
    payload.update(overrides)
    return payload


def _encode(payload) -> bytes:
    return json.dumps(payload).encode("utf-8")


def test_valid_export_round_trips_to_decimal_rates():
    result = read_trial_intention(_encode(_payload()))
    assert result["concept"] == "Cold brew subscription"
    assert result["respondents"] == 260
    assert result["weighted_trial_rate"] == pytest.approx(0.2108)
    assert result["ceiling_trial_rate"] == pytest.approx(0.3923)
    assert result["source_product"] == "ChoiceSignal"
    assert "overstates" in result["note"]


def test_wrong_schema_is_rejected():
    with pytest.raises(DataProblem, match="trial-intention"):
        read_trial_intention(_encode(_payload(schema="something.else.v9")))


def test_missing_trial_block_is_rejected():
    payload = _payload()
    del payload["trial_assumption"]
    with pytest.raises(DataProblem, match="trial_assumption"):
        read_trial_intention(_encode(payload))


def test_out_of_range_percentage_is_rejected():
    payload = _payload()
    payload["trial_assumption"]["weighted_trial_%"] = 140.0
    with pytest.raises(DataProblem, match="between 0 and 100"):
        read_trial_intention(_encode(payload))


def test_unreadable_and_empty_inputs_are_rejected():
    with pytest.raises(DataProblem):
        read_trial_intention(b"")
    with pytest.raises(DataProblem, match="readable JSON"):
        read_trial_intention(b"not json at all")
    with pytest.raises(DataProblem):
        read_trial_intention(_encode(_payload(respondents=0)))


def _price_payload(**overrides):
    payload = {
        "schema": PRICE_EVIDENCE_SCHEMA,
        "producer": {"product": "TagSignal", "version": "1.0.0"},
        "evidence_tier": "Observed transactions",
        "candidate_price": 129.0,
        "reference_price": 119.0,
        "declared_unit_cost": 41.5,
        "candidate_projected_volume": 5400.0,
        "candidate_contribution": 472500.0,
        "incremental_contribution": 31800.0,
        "incremental_contribution_interval": [12400.0, 51200.0],
        "within_observed_support": True,
        "decision_status": "Supported",
        "interpretation": "The candidate price outperforms the reference within the observed range.",
        "warning": "An aggregate price scenario is one input to a launch decision, not a launch approval.",
    }
    payload.update(overrides)
    return payload


def test_valid_price_evidence_round_trips():
    result = read_price_evidence(_encode(_price_payload()))
    assert result["candidate_price"] == pytest.approx(129.0)
    assert result["reference_price"] == pytest.approx(119.0)
    assert result["candidate_projected_volume"] == pytest.approx(5400.0)
    assert result["incremental_contribution"] == pytest.approx(31800.0)
    assert result["incremental_contribution_interval"] == pytest.approx([12400.0, 51200.0])
    assert result["within_observed_support"] is True
    assert result["evidence_tier"] == "Observed transactions"
    assert result["decision_status"] == "Supported"
    assert result["source_product"] == "TagSignal"
    assert result["source_version"] == "1.0.0"


def test_price_evidence_wrong_schema_is_rejected():
    with pytest.raises(DataProblem, match="price-evidence"):
        read_price_evidence(_encode(_price_payload(schema="signal.trial-intention.v1")))


def test_price_evidence_malformed_interval_is_rejected():
    with pytest.raises(DataProblem, match="two-number"):
        read_price_evidence(_encode(_price_payload(incremental_contribution_interval=[12400.0])))
    with pytest.raises(DataProblem, match="two-number"):
        read_price_evidence(_encode(_price_payload(incremental_contribution_interval=["low", "high"])))
    with pytest.raises(DataProblem, match="reversed"):
        read_price_evidence(_encode(_price_payload(incremental_contribution_interval=[51200.0, 12400.0])))


def test_price_evidence_negative_price_is_rejected():
    with pytest.raises(DataProblem, match="greater than zero"):
        read_price_evidence(_encode(_price_payload(candidate_price=-5.0)))
    with pytest.raises(DataProblem, match="greater than zero"):
        read_price_evidence(_encode(_price_payload(candidate_price=0.0)))


def test_price_evidence_unit_margin_arithmetic():
    result = read_price_evidence(_encode(_price_payload()))
    assert result["unit_margin"] == pytest.approx(129.0 - 41.5)
    zero_cost = read_price_evidence(_encode(_price_payload(declared_unit_cost=0.0)))
    assert zero_cost["unit_margin"] == pytest.approx(129.0)
    with pytest.raises(DataProblem, match="cannot be negative"):
        read_price_evidence(_encode(_price_payload(declared_unit_cost=-1.0)))
