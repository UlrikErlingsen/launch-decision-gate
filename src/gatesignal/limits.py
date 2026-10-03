"""Data limits: none when Gate Signal runs on your own computer, hard caps only on a public demo.

Run locally (standalone, inside a local Signal Hub or on an internal company server), the app imposes no limit on
project-file size, table rows or evidence imports; the computer's memory is the limit. A public demo sets
``SIGNAL_PUBLIC=1`` and then every cap below protects the shared server. All caps live in this module and are read at
call time.
"""

from __future__ import annotations

import os

# Demo caps, applied only when SIGNAL_PUBLIC=1. They are the limits of earlier releases.
DEMO_MAX_UPLOAD_MB = 50
DEMO_MAX_ROWS_PER_TABLE = 20_000
DEMO_MAX_EXPANDED_WORKBOOK_MB = 500  # zip-bomb guard: workbook XML normally unzips to about 5x its file size
DEMO_MAX_INTEROP_MB = 5

DEMO_NOTE = "This is a limit of the public demo only; the downloadable Gate Signal app has no built-in limit."
MEMORY_MESSAGE = (
    "There is not enough memory on this computer for this project file. Close other programs, remove unrelated "
    "sheets or embedded objects, or run Gate Signal on a computer with more memory."
)


def is_public() -> bool:
    """True on a public demo (``SIGNAL_PUBLIC=1``); independent of Hub mode (``SIGNAL_HUB``)."""
    return os.environ.get("SIGNAL_PUBLIC") == "1"


def max_upload_bytes() -> int | None:
    return DEMO_MAX_UPLOAD_MB * 1024 * 1024 if is_public() else None


def max_rows_per_table() -> int | None:
    return DEMO_MAX_ROWS_PER_TABLE if is_public() else None


def max_expanded_workbook_bytes() -> int | None:
    return DEMO_MAX_EXPANDED_WORKBOOK_MB * 1024 * 1024 if is_public() else None


def max_interop_bytes() -> int | None:
    return DEMO_MAX_INTEROP_MB * 1024 * 1024 if is_public() else None


def demo_limit(message: str) -> str:
    """A capped message: what was exceeded, plus the reminder that only the demo has the cap."""
    return f"{message} {DEMO_NOTE}"
