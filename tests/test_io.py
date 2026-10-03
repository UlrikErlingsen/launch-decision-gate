from __future__ import annotations

from io import BytesIO
import json
import zipfile

import pandas as pd

from gatesignal.examples import demo_project
from gatesignal.io import load_project, project_template, results_to_excel, results_to_json, safe_for_spreadsheet, tables_to_csv_zip


def test_excel_template_round_trip_preserves_all_project_tables() -> None:
    project = demo_project()
    loaded = load_project(BytesIO(project_template(project)))

    assert loaded["metadata"]["project_name"] == project["metadata"]["project_name"]
    for key in ["criteria", "cash_flows", "volume_bridge", "risks", "brand_evidence", "challenge"]:
        assert not loaded[key].empty
        assert list(loaded[key].columns) == list(project[key].columns)


def test_json_round_trip_preserves_tables() -> None:
    project = demo_project()
    tables = {
        key: project[key]
        for key in ["criteria", "cash_flows", "volume_bridge", "risks", "brand_evidence", "challenge"]
    }
    raw = results_to_json(tables, project["metadata"])
    upload = BytesIO(raw)
    upload.name = "project.json"

    loaded = load_project(upload)

    assert loaded["metadata"]["project_name"] == "LoopDose cleaning concentrate system"
    assert len(loaded["criteria"]) == 8
    assert len(loaded["brand_evidence"]) == 8


def test_spreadsheet_exports_neutralize_formula_like_text() -> None:
    frame = pd.DataFrame({"note": ["=2+2", " +SUM(A1:A2)", "ordinary"], "amount": [-10, 5, 3]})
    safe = safe_for_spreadsheet(frame)

    assert safe.loc[0, "note"] == "'=2+2"
    assert safe.loc[1, "note"].startswith("'")
    assert safe.loc[2, "note"] == "ordinary"
    assert safe.loc[0, "amount"] == -10

    workbook = pd.read_excel(BytesIO(results_to_excel({"Results": frame})))
    assert workbook.loc[0, "note"] == "'=2+2"


def test_csv_zip_contains_accessible_equivalent_tables() -> None:
    raw = tables_to_csv_zip({"Decision summary": pd.DataFrame({"decision": ["HOLD"]})})

    with zipfile.ZipFile(BytesIO(raw)) as archive:
        assert archive.namelist() == ["Decision_summary.csv"]
        assert "HOLD" in archive.read("Decision_summary.csv").decode("utf-8")


def test_json_export_contains_no_nonstandard_nan_tokens() -> None:
    raw = results_to_json({"results": pd.DataFrame({"irr": [None]})}, {"project": "Test"})

    assert json.loads(raw)["results"] == [{"irr": None}]


def test_upload_cap_follows_the_50_mb_tier_and_the_variable_only_lowers_it(monkeypatch) -> None:
    from gatesignal import io as gate_io

    for requested, expected in [("200", 50), ("1000", 50), ("10", 10), ("0", 1), ("not a number", 50)]:
        monkeypatch.setenv("GATESIGNAL_MAX_UPLOAD_MB", requested)
        assert gate_io._configured_upload_mb() == expected
    monkeypatch.delenv("GATESIGNAL_MAX_UPLOAD_MB")
    assert gate_io._configured_upload_mb() == gate_io.TIER_MAX_UPLOAD_MB == 50
    # A full-size workbook may unzip to the usual 4-8x without hitting the zip-bomb guard (it was 100 MB, i.e. 2x).
    assert gate_io.MAX_EXPANDED_WORKBOOK_BYTES >= 8 * 50 * 1024 * 1024


def test_size_limit_messages_name_the_caps(monkeypatch) -> None:
    import pytest

    from gatesignal import io as gate_io
    from gatesignal.errors import DataProblem

    workbook = project_template(demo_project())
    monkeypatch.setattr(gate_io, "MAX_EXPANDED_WORKBOOK_BYTES", 1024)
    with pytest.raises(DataProblem, match="expands beyond 0 MB when unzipped"):
        load_project(BytesIO(workbook))
    monkeypatch.setattr(gate_io, "MAX_UPLOAD_BYTES", 16)
    with pytest.raises(DataProblem, match=f"larger than Gate Signal's {gate_io.MAX_UPLOAD_MB} MB limit"):
        load_project(BytesIO(workbook))


def test_unrelated_workbook_sheets_are_not_needed_to_load_a_project() -> None:
    from openpyxl import load_workbook

    book = load_workbook(BytesIO(project_template(demo_project())))
    notes = book.create_sheet("Working notes")
    for row in range(200):
        notes.append([f"note {row}", "=1+1", row])
    buffer = BytesIO()
    book.save(buffer)
    loaded = load_project(BytesIO(buffer.getvalue()))
    assert len(loaded["criteria"]) == 8
    assert "working_notes" not in loaded
