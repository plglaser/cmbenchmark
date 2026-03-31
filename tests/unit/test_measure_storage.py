import json
from pathlib import Path

from cmbenchmark.types.measures import MeasureResultPerModel
from cmbenchmark.services.measure import (
    MEASURES_DIRNAME,
    MEASURES_INDEX_FILENAME,
    save_measure_per_model_split,
    load_measure_per_model_split,
)
from cmbenchmark.services.report import generate_report


def _sample_per_model_payload() -> dict:
    return {
        "parsing": {
            "d1_m1_parse_status": {
                "m1": {"parse_status": "success", "parse_error_msg": None},
                "m2": {"parse_status": "warning", "parse_error_msg": None},
            },
            "d1_m2_elements_loaded_skipped": {
                "m1": {"elements_loaded": 10, "elements_skipped": 0, "skip_ratio": 0.0},
                "m2": {"elements_loaded": 5, "elements_skipped": 5, "skip_ratio": 0.5},
            },
            "d1_m3_parsing_time": {
                "m1": {"parse_time_ms": 100},
                "m2": {"parse_time_ms": 200},
            },
            "d1_m4_file_size": {
                "m1": {"file_size_bytes_source": 120, "file_size_bytes_ir": 80},
                "m2": {"file_size_bytes_source": 240, "file_size_bytes_ir": 140},
            },
            "d1_m5_warnings": {
                "m1": {"warning_count": 0, "warnings_by_type": {}, "warnings_per_element": 0.0},
                "m2": {"warning_count": 2, "warnings_by_type": {"x": 2}, "warnings_per_element": 0.4},
            },
        }
    }


def test_split_measure_storage_roundtrip(tmp_path: Path) -> None:
    per_model = MeasureResultPerModel.from_dict(_sample_per_model_payload())
    index_payload = save_measure_per_model_split(per_model, str(tmp_path))

    measures_dir = tmp_path / MEASURES_DIRNAME
    index_path = tmp_path / MEASURES_INDEX_FILENAME

    assert measures_dir.exists()
    assert index_path.exists()
    assert index_payload["count"] == 2
    assert (measures_dir / "m1.json").exists()
    assert (measures_dir / "m2.json").exists()

    aggregated = load_measure_per_model_split(str(index_path))
    assert aggregated["parsing"]["d1_m1_parse_status"]["m2"]["parse_status"] == "warning"
    assert aggregated["parsing"]["d1_m4_file_size"]["m1"]["file_size_bytes_ir"] == 80


def test_generate_report_from_split_measure_storage(tmp_path: Path) -> None:
    per_model = MeasureResultPerModel.from_dict(_sample_per_model_payload())
    save_measure_per_model_split(per_model, str(tmp_path))

    measures = {
        "parsing": {
            "d1_m1_parse_status": {
                "n_success": 1,
                "share_success": 0.5,
                "n_partial": 1,
                "share_partial": 0.5,
                "n_failed": 0,
                "share_failed": 0.0,
            },
            "d1_m2_elements_loaded_skipped": {
                "total_elements_loaded": 15,
                "total_elements_skipped": 5,
                "dataset_skip_ratio": 0.25,
                "skip_ratio_stats": {"mean": 0.25, "median": 0.25},
                "n_models_with_skips": 1,
                "share_models_with_skips": 0.5,
            },
            "d1_m5_warnings": {"total_warnings_by_type": {"x": 2}},
        }
    }
    measures_path = tmp_path / "measures.json"
    with open(measures_path, "w", encoding="utf-8") as f:
        json.dump(measures, f, indent=2)

    result = generate_report(
        measures_path=str(measures_path),
        measures_index_path=str(tmp_path / MEASURES_INDEX_FILENAME),
        output_dir=str(tmp_path),
    )

    assert (tmp_path / "report.json").exists()
    assert "parseStatusChartData" in result["data"]
    assert len(result["data"]["skipRatioTop10"]) == 2
