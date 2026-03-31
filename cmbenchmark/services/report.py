"""Report-building service.

This module builds a *derived* report JSON payload for the frontend, mirroring the
transformations previously done in `frontend/src/hooks/useReportData.ts`.

The goal is for report jobs (`/api/report-jobs/{id}` result payload) to return a
stable, UI-ready structure (chart series, histogram bins, top-N tables, etc.) so
the frontend can stay "thin".
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Callable

from cmbenchmark.report.utils import _get, create_histogram_data, create_share_histogram_data
from cmbenchmark.report.parsing import build_parsing_report
from cmbenchmark.report.lexical import build_lexical_report
from cmbenchmark.report.constructs import build_constructs_report
from cmbenchmark.report.size import build_size_report
from cmbenchmark.services.measure import load_measure_per_model_split


class ReportCancelledError(Exception):
    """Raised when report generation is cancelled via callback."""


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
    measures_index_path: str,
    output_dir: str,
    ir_info_path: Optional[str] = None,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    cancel_requested: Optional[Callable[[], bool]] = None,
) -> Dict[str, Any]:
    """Build and persist the derived report JSON."""
    def _emit_progress(update: Dict[str, Any]) -> None:
        if progress_callback:
            progress_callback(update)

    def _check_cancelled() -> None:
        if cancel_requested and cancel_requested():
            raise ReportCancelledError("Report job was cancelled.")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    _emit_progress(
        {
            "phase": "initializing",
            "message": "Loading report inputs.",
            "percentage": 0.0,
            "counters": {
                "total_models": 0,
                "processed_models": 0,
            },
        }
    )

    _check_cancelled()
    with open(measures_path, "r", encoding="utf-8") as f:
        measures = json.load(f)

    try:
        measures_per_model = load_measure_per_model_split(
            measures_index_path,
            progress_callback=lambda processed, total: _emit_progress(
                {
                    "phase": "loading_per_model_measures",
                    "message": f"Loading per-model measures ({processed}/{total}).",
                    "percentage": 15.0 + ((processed / max(1, total)) * 70.0),
                    "counters": {
                        "total_models": total,
                        "processed_models": processed,
                    },
                }
            ),
            cancel_requested=cancel_requested,
        )
    except InterruptedError as exc:
        raise ReportCancelledError(str(exc)) from exc

    model_ids = set()
    for dimension_payload in measures_per_model.values():
        if not isinstance(dimension_payload, Mapping):
            continue
        for measure_payload in dimension_payload.values():
            if isinstance(measure_payload, Mapping):
                model_ids.update(measure_payload.keys())
    total_models = len(model_ids)

    ir_info = None
    if ir_info_path is None:
        default_ir_info = output_path / "ir_info.json"
        if default_ir_info.exists():
            ir_info_path = str(default_ir_info)

    if ir_info_path:
        p = Path(ir_info_path)
        if p.exists():
            _check_cancelled()
            with open(p, "r", encoding="utf-8") as f:
                ir_info = json.load(f)

    _check_cancelled()
    _emit_progress(
        {
            "phase": "building_report",
            "message": "Building derived report payload.",
            "percentage": 92.0,
            "counters": {
                "total_models": total_models,
                "processed_models": total_models,
            },
        }
    )
    derived = build_report_data(
        measures=measures,
        measures_per_model=measures_per_model,
        ir_info=ir_info,
    )

    report_path = output_path / "report.json"
    _check_cancelled()
    save_report(derived, str(report_path))

    _emit_progress(
        {
            "phase": "completed",
            "message": "Report generation completed.",
            "percentage": 100.0,
            "counters": {
                "total_models": total_models,
                "processed_models": total_models,
            },
        }
    )

    return {"json": str(report_path), "data": derived}
