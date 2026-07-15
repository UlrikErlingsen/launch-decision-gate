"""Generate portable example artifacts from the canonical in-code fixtures."""

from __future__ import annotations

from pathlib import Path

from gatesignal.examples import blank_project, demo_project
from gatesignal.io import project_template, results_to_json


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "examples"


def project_json(project: dict[str, object]) -> bytes:
    metadata = dict(project["metadata"])
    tables = {key: value for key, value in project.items() if hasattr(value, "to_json")}
    return results_to_json(tables, metadata)


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    OUTPUT.joinpath("gatesignal-blank-template.xlsx").write_bytes(project_template(blank_project()))
    OUTPUT.joinpath("gatesignal-fictional-demo.xlsx").write_bytes(project_template(demo_project()))
    OUTPUT.joinpath("gatesignal-fictional-demo.json").write_bytes(project_json(demo_project()))


if __name__ == "__main__":
    main()

