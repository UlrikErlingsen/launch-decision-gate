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
