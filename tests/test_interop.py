"""Tests for the ChoiceSignal trial-intention import."""

import json

import pytest

from gatesignal.errors import DataProblem
from gatesignal.interop import TRIAL_INTENTION_SCHEMA, read_trial_intention


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
