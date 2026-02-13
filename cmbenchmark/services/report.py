"""Report-building service.

This module builds a *derived* report JSON payload for the frontend, mirroring the
transformations previously done in `frontend/src/hooks/useReportData.ts`.

The goal is for `/api/report` to return a stable, UI-ready structure (chart
series, histogram bins, top-N tables, etc.) so the frontend can stay "thin".
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from cmbenchmark.report.utils import _get
from cmbenchmark.report.parsing import build_parsing_report
from cmbenchmark.report.lexical import build_lexical_report
from cmbenchmark.report.constructs import build_constructs_report
from cmbenchmark.report.size import build_size_report


def build_report_data(
    measures: Mapping[str, Any],
    measures_per_model: Mapping[str, Any],
    ir_info: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a derived report payload for the UI."""
    ir_index = _get(ir_info, "index", default={}) if ir_info else {}
    if not isinstance(ir_index, Mapping):
        ir_index = {}

    parsing_section = build_parsing_report(measures, measures_per_model, ir_index)
    lexical_section = build_lexical_report(measures, measures_per_model, ir_index)
    constructs_section = build_constructs_report(measures, measures_per_model, ir_index)
    size_section = build_size_report(measures, measures_per_model, ir_index)

    return {
        **parsing_section,
        **lexical_section,
        **constructs_section,
        **size_section,
    }


def save_report(derived: Mapping[str, Any], output_path: str) -> None:
    """Persist derived report JSON to disk."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dict(derived), f, indent=2)


def generate_report(
    measures_path: str,
    measures_per_model_path: str,
    output_dir: str,
    ir_info_path: Optional[str] = None,
) -> Dict[str, str]:
    """Build and persist the derived report JSON."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    with open(measures_path, "r", encoding="utf-8") as f:
        measures = json.load(f)

    with open(measures_per_model_path, "r", encoding="utf-8") as f:
        measures_per_model = json.load(f)

    ir_info = None
    if ir_info_path is None:
        default_ir_info = output_path / "ir_info.json"
        if default_ir_info.exists():
            ir_info_path = str(default_ir_info)

    if ir_info_path:
        p = Path(ir_info_path)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                ir_info = json.load(f)

    derived = build_report_data(
        measures=measures,
        measures_per_model=measures_per_model,
        ir_info=ir_info,
    )

    report_path = output_path / "report.json"
    save_report(derived, str(report_path))

    return {"json": str(report_path), "data": derived}
