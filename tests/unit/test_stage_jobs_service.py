import json
import time
from pathlib import Path

from cmbenchmark.types.dataset import IRInfo
from cmbenchmark.types.parsing import ModelParseDiagnostics
from cmbenchmark.types.profile import BenchmarkProfile
from cmbenchmark.web.parse_jobs import create_parse_job, get_parse_job, clear_parse_jobs
from cmbenchmark.web.measure_jobs import create_measure_job, get_measure_job, clear_measure_jobs
from cmbenchmark.web.report_jobs import create_report_job, get_report_job, clear_report_jobs
import cmbenchmark.web.parse_jobs as parse_jobs_module
import cmbenchmark.web.measure_jobs as measure_jobs_module
import cmbenchmark.web.report_jobs as report_jobs_module


def _build_profile(dataset_path: Path, output_path: Path) -> BenchmarkProfile:
    return BenchmarkProfile(
        name="stage-job-test",
        version="1.0.0",
        output_path=str(output_path),
        scan={
            "dataset_path": str(dataset_path),
            "include": ["*.xmi"],
            "exclude": [],
            "size_limit_mb": None,
        },
        parse={
            "parser_language": "Ecore",
            "ecore_enable_scoped_uri_mappings": True,
        },
    )


def _wait_for_terminal(getter, job_id: str, timeout_s: float = 10.0) -> dict:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        payload = getter(job_id)
        if payload["status"] in {"completed", "failed", "cancelled"}:
            return payload
        time.sleep(0.05)
    raise AssertionError(f"Timed out waiting for job {job_id}")


def setup_function() -> None:
    clear_parse_jobs()
    clear_measure_jobs()
    clear_report_jobs()


def teardown_function() -> None:
    clear_parse_jobs()
    clear_measure_jobs()
    clear_report_jobs()


def test_parse_job_lifecycle(tmp_path: Path, monkeypatch) -> None:
    def _stub_parse_from_scan(
        dataset_info_path: str,
        output_dir: str,
        parser_language: str,
        ecore_enable_scoped_uri_mappings=True,
        **kwargs,
    ):
        return IRInfo(
            dataset_root=str(Path(dataset_info_path).parent),
            parsed_at="2026-01-01T00:00:00Z",
            parameters={"from_scan": dataset_info_path, "parser_language": parser_language},
            totals={"candidates_in": 1, "parsed_success": 1, "parsed_warning": 0, "parsed_failure": 0},
            index={"m1": "a.xmi"},
            modelParseDiagnostics={
                "m1": ModelParseDiagnostics(file_id="m1", relpath="a.xmi", parse_status="success")
            },
        )

    monkeypatch.setattr(parse_jobs_module, "parse_from_scan", _stub_parse_from_scan)

    dataset = tmp_path / "dataset"
    dataset.mkdir()
    output = tmp_path / "out"
    output.mkdir()
    (output / "dataset_info.json").write_text("{}", encoding="utf-8")
    profile = _build_profile(dataset, output)

    created = create_parse_job(profile)
    status = _wait_for_terminal(get_parse_job, created["job_id"])

    assert status["status"] == "completed"
    assert status["result"]["totals"]["parsed_success"] == 1


def test_measure_job_lifecycle(tmp_path: Path, monkeypatch) -> None:
    def _stub_compute_measure(ir_path: str, profile=None, **kwargs):
        return "dataset-measures", "per-model-measures"

    def _stub_save_dataset(measure, output_path: str):
        Path(output_path).write_text(json.dumps({"ok": True}), encoding="utf-8")

    def _stub_save_split(measure, output_dir: str):
        root = Path(output_dir)
        (root / "measures").mkdir(parents=True, exist_ok=True)
        (root / "measures" / "m1.json").write_text(json.dumps({"model_id": "m1", "measures": {}}), encoding="utf-8")
        (root / "measures_index.json").write_text(
            json.dumps({"schema_version": 1, "count": 1, "models": [{"model_id": "m1", "path": "measures/m1.json"}]}),
            encoding="utf-8",
        )

    monkeypatch.setattr(measure_jobs_module, "compute_measure", _stub_compute_measure)
    monkeypatch.setattr(measure_jobs_module, "save_measure_dataset", _stub_save_dataset)
    monkeypatch.setattr(measure_jobs_module, "save_measure_per_model_split", _stub_save_split)

    dataset = tmp_path / "dataset"
    dataset.mkdir()
    output = tmp_path / "out"
    output.mkdir()
    (output / "ir").mkdir()
    profile = _build_profile(dataset, output)

    created = create_measure_job(profile)
    status = _wait_for_terminal(get_measure_job, created["job_id"])

    assert status["status"] == "completed"
    assert status["result"]["measures_path"].endswith("measures.json")
    assert status["result"]["measures_index_path"].endswith("measures_index.json")


def test_report_job_lifecycle(tmp_path: Path, monkeypatch) -> None:
    def _stub_generate_report(
        measures_path: str,
        measures_index_path: str,
        output_dir: str,
        ir_info_path=None,
        **kwargs,
    ):
        return {"json": str(Path(output_dir) / "report.json"), "data": {"hello": "world"}}

    monkeypatch.setattr(report_jobs_module, "generate_report", _stub_generate_report)

    dataset = tmp_path / "dataset"
    dataset.mkdir()
    output = tmp_path / "out"
    output.mkdir()
    (output / "measures.json").write_text("{}", encoding="utf-8")
    (output / "measures_index.json").write_text('{"models":[]}', encoding="utf-8")
    profile = _build_profile(dataset, output)

    created = create_report_job(profile)
    status = _wait_for_terminal(get_report_job, created["job_id"])

    assert status["status"] == "completed"
    assert status["result"]["hello"] == "world"
