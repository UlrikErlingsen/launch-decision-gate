"""Safe project-bundle input and portable decision-pack exports."""

from __future__ import annotations

from io import BytesIO
import json
import os
from pathlib import Path
import re
from typing import BinaryIO
import zipfile

import pandas as pd

from .errors import DataProblem


MAX_UPLOAD_MB = max(1, min(int(os.getenv("GATESIGNAL_MAX_UPLOAD_MB", "50")), 200))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
MAX_EXPANDED_WORKBOOK_BYTES = 100 * 1024 * 1024
MAX_ROWS_PER_TABLE = 20_000
ILLEGAL_XML_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
TABLE_KEYS = ["criteria", "cash_flows", "volume_bridge", "risks", "brand_evidence", "challenge"]


def _source_bytes(source: str | Path | bytes | BinaryIO) -> tuple[bytes, str]:
    if isinstance(source, (str, Path)):
        path = Path(source)
        return path.read_bytes(), path.name
    if isinstance(source, bytes):
        return source, "project.xlsx"
    name = Path(getattr(source, "name", "project.xlsx")).name
    if hasattr(source, "seek"):
        source.seek(0)
    return source.read(), name


def _clean_tables(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    cleaned: dict[str, pd.DataFrame] = {}
    for name, frame in tables.items():
        key = str(name).strip().casefold().replace(" ", "_")
        if key == "cash_flow":
            key = "cash_flows"
        if key not in TABLE_KEYS or frame is None or (frame.empty and len(frame.columns) == 0):
            continue
        if len(frame) > MAX_ROWS_PER_TABLE:
            raise DataProblem(f"The {key.replace('_', ' ')} table exceeds the {MAX_ROWS_PER_TABLE:,}-row safety limit.")
        copy = frame.copy()
        copy.columns = [str(column).strip() for column in copy.columns]
        cleaned[key] = copy
    if not cleaned:
        raise DataProblem("No GateSignal tables were found. Use the downloadable project template as the starting point.")
    return cleaned


def load_project(source: str | Path | bytes | BinaryIO) -> dict[str, object]:
    """Load a GateSignal `.xlsx` or `.json` project without executing content."""
    raw, source_name = _source_bytes(source)
    if not raw:
        raise DataProblem("This project file is empty.")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise DataProblem(f"This project file is larger than the configured {MAX_UPLOAD_MB} MB limit.")
    extension = Path(source_name).suffix.lower()
    try:
        if extension == ".xlsx":
            with zipfile.ZipFile(BytesIO(raw)) as workbook:
                expanded = sum(member.file_size for member in workbook.infolist())
                if expanded > MAX_EXPANDED_WORKBOOK_BYTES:
                    raise DataProblem("This workbook expands beyond 100 MB. Remove unrelated sheets or embedded objects.")
            sheets = pd.read_excel(BytesIO(raw), sheet_name=None)
            tables = _clean_tables(sheets)
            metadata_sheet = next(
                (frame for name, frame in sheets.items() if str(name).strip().casefold() == "metadata"),
                None,
            )
            metadata: dict[str, object] = {}
            if metadata_sheet is not None and {"field", "value"}.issubset(metadata_sheet.columns):
                metadata = dict(zip(metadata_sheet["field"].astype(str), metadata_sheet["value"], strict=False))
        elif extension == ".json":
            payload = json.loads(raw.decode("utf-8-sig"))
            if not isinstance(payload, dict):
                raise DataProblem("GateSignal JSON must contain a project object.")
            metadata = payload.get("metadata", {}) if isinstance(payload.get("metadata", {}), dict) else {}
            tables = _clean_tables(
                {
                    key: pd.DataFrame(payload[key])
                    for key in TABLE_KEYS
                    if key in payload and isinstance(payload[key], list)
                }
            )
        else:
            raise DataProblem("Please use a GateSignal .xlsx or .json project file.")
    except DataProblem:
        raise
    except Exception as exc:
        raise DataProblem("The project could not be read. Start from the GateSignal template and keep the sheet names.") from exc
    return {"metadata": metadata, **tables, "source_name": source_name}


def safe_for_spreadsheet(frame: pd.DataFrame) -> pd.DataFrame:
    """Neutralize cells that spreadsheet programs could interpret as formulas."""
    safe = frame.copy()
    for column in safe.columns:
        def neutralize(value: object) -> object:
            if not isinstance(value, str):
                return value
            cleaned = ILLEGAL_XML_CHARACTERS.sub("", value)
            return "'" + cleaned if cleaned.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")) else cleaned

        safe[column] = safe[column].map(neutralize)
    return safe


def results_to_excel(tables: dict[str, pd.DataFrame]) -> bytes:
    """Create an in-memory evidence pack with readable sheets."""
    if not tables:
        raise DataProblem("There are no GateSignal tables to export.")
    output = BytesIO()
    used: set[str] = set()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for raw_name, frame in tables.items():
            base = re.sub(r"[\\/*?:\[\]]", "-", str(raw_name))[:31] or "Results"
            name = base
            suffix = 2
            while name in used:
                tail = f"_{suffix}"
                name = base[: 31 - len(tail)] + tail
                suffix += 1
            used.add(name)
            safe = safe_for_spreadsheet(frame)
            safe.to_excel(writer, sheet_name=name, index=False)
            sheet = writer.sheets[name]
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            for cells in sheet.columns:
                widths = [len(str(cell.value)) if cell.value is not None else 0 for cell in cells[:2000]]
                sheet.column_dimensions[cells[0].column_letter].width = min(max(widths, default=8) + 2, 48)
    return output.getvalue()


def results_to_json(tables: dict[str, pd.DataFrame], metadata: dict[str, object]) -> bytes:
    """Serialize decision evidence and metadata as UTF-8 JSON."""
    payload: dict[str, object] = {
        "metadata": metadata,
        **{name: json.loads(frame.to_json(orient="records", date_format="iso")) for name, frame in tables.items()},
    }
    return json.dumps(payload, indent=2, default=str, allow_nan=False).encode("utf-8")


def tables_to_csv_zip(tables: dict[str, pd.DataFrame]) -> bytes:
    """Package equivalent accessible CSV tables in one archive."""
    output = BytesIO()
    with zipfile.ZipFile(output, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for raw_name, frame in tables.items():
            filename = re.sub(r"[^A-Za-z0-9._-]+", "_", str(raw_name).strip()).strip("_") or "results"
            archive.writestr(f"{filename}.csv", safe_for_spreadsheet(frame).to_csv(index=False))
    return output.getvalue()


def project_template(project: dict[str, object]) -> bytes:
    """Export an editable GateSignal project bundle."""
    metadata = project.get("metadata", {})
    metadata_frame = pd.DataFrame(
        [{"field": key, "value": value} for key, value in dict(metadata).items()]
    )
    tables = {"Metadata": metadata_frame}
    labels = {
        "criteria": "Criteria",
        "cash_flows": "Cash flows",
        "volume_bridge": "Volume bridge",
        "risks": "Risks",
        "brand_evidence": "Brand evidence",
        "challenge": "Challenge",
    }
    tables.update({labels[key]: project[key] for key in TABLE_KEYS if isinstance(project.get(key), pd.DataFrame)})
    return results_to_excel(tables)
