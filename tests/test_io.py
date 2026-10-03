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


def _project_with_rows(rows: int) -> dict:
    project = demo_project()
    criteria = project["criteria"]
    project["criteria"] = pd.concat([criteria] * (rows // len(criteria) + 1), ignore_index=True).iloc[:rows]
    return project


def _as_json_upload(project: dict) -> BytesIO:
    keys = ["criteria", "cash_flows", "volume_bridge", "risks", "brand_evidence", "challenge"]
    upload = BytesIO(results_to_json({key: project[key] for key in keys}, project["metadata"]))
    upload.name = "project.json"
    return upload


def test_local_mode_accepts_projects_beyond_every_demo_cap(monkeypatch) -> None:
    from gatesignal import limits

    monkeypatch.delenv("SIGNAL_PUBLIC", raising=False)
    assert limits.max_upload_bytes() is None and limits.max_rows_per_table() is None
    loaded = load_project(_as_json_upload(_project_with_rows(limits.DEMO_MAX_ROWS_PER_TABLE + 1)))
    assert len(loaded["criteria"]) == limits.DEMO_MAX_ROWS_PER_TABLE + 1
    monkeypatch.setattr(limits, "DEMO_MAX_UPLOAD_MB", 0)
    monkeypatch.setattr(limits, "DEMO_MAX_EXPANDED_WORKBOOK_MB", 0)
    assert len(load_project(BytesIO(project_template(demo_project())))["criteria"]) == 8


def test_public_demo_enforces_its_caps_with_a_demo_message(monkeypatch) -> None:
    import pytest

    from gatesignal import limits
    from gatesignal.errors import DataProblem

    monkeypatch.setenv("SIGNAL_PUBLIC", "1")
    with pytest.raises(DataProblem, match="20,000-row limit.*downloadable Gate Signal app has no built-in limit"):
        load_project(_as_json_upload(_project_with_rows(limits.DEMO_MAX_ROWS_PER_TABLE + 1)))
    workbook = project_template(demo_project())
    monkeypatch.setattr(limits, "DEMO_MAX_EXPANDED_WORKBOOK_MB", 0)
    with pytest.raises(DataProblem, match="unzip to at most 0 MB.*public demo only"):
        load_project(BytesIO(workbook))
    monkeypatch.setattr(limits, "DEMO_MAX_UPLOAD_MB", 0)
    with pytest.raises(DataProblem, match="project files up to 0 MB.*public demo only"):
        load_project(BytesIO(workbook))


def test_running_out_of_memory_is_reported_plainly(monkeypatch) -> None:
    import pytest

    from gatesignal import io as gate_io
    from gatesignal.errors import DataProblem, friendly_message
    from gatesignal.limits import MEMORY_MESSAGE

    def no_memory(*args, **kwargs):
        raise MemoryError

    monkeypatch.setattr(gate_io.pd, "read_excel", no_memory)
    with pytest.raises(DataProblem, match="not enough memory on this computer"):
        load_project(BytesIO(project_template(demo_project())))
    assert friendly_message(MemoryError()) == MEMORY_MESSAGE


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
