import time
from pathlib import Path

from cmbenchmark.services.scan import ScanCancelledError
from cmbenchmark.types.dataset import DatasetInfo
from cmbenchmark.types.profile import BenchmarkProfile
from cmbenchmark.web.scan_jobs import (
    clear_scan_jobs,
    create_scan_job,
    get_scan_job,
    get_scan_job_files,
    cancel_scan_job,
    SCAN_FILES_MAX_LIMIT,
)
import cmbenchmark.web.scan_jobs as scan_jobs_module


def _build_profile(dataset_path: Path, output_path: Path) -> BenchmarkProfile:
    return BenchmarkProfile(
        name="scan-job-test",
        version="1.0.0",
        output_path=str(output_path),
        scan={
            "dataset_path": str(dataset_path),
            "include": ["*.xmi", "*.xml"],
            "exclude": [],
            "size_limit_mb": None,
        },
        parse={
            "parser_language": "Ecore",
            "ecore_enable_scoped_uri_mappings": True,
        },
    )


def _wait_for_terminal(job_id: str, timeout_s: float = 10.0) -> dict:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        payload = get_scan_job(job_id)
        if payload["status"] in {"completed", "failed", "cancelled"}:
            return payload
        time.sleep(0.05)
    raise AssertionError(f"Timed out waiting for job {job_id}")


def setup_function() -> None:
    clear_scan_jobs()


def teardown_function() -> None:
    clear_scan_jobs()


def test_scan_job_lifecycle_and_files_endpoint(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    (dataset / "a.xmi").write_text("<a/>", encoding="utf-8")
    (dataset / "b.xml").write_text("<b/>", encoding="utf-8")
    (dataset / "c.txt").write_text("ignored", encoding="utf-8")

    output = tmp_path / "out"
    profile = _build_profile(dataset, output)

    create_resp = create_scan_job(profile)
    job_id = create_resp["job_id"]

    status = _wait_for_terminal(job_id)
    assert status["status"] == "completed"
    assert status["result"]["totals"]["total_seen"] == 3
    assert status["result"]["totals"]["candidates"] == 2
    assert status["result"]["duplicates_files_count"] == 0

    dataset_info_path = Path(status["result"]["parameters"]["dataset_info_path"])
    assert dataset_info_path.exists()

    files_payload = get_scan_job_files(
        job_id=job_id,
        category="candidates",
        offset=0,
        limit=1,
    )
    assert files_payload["total"] == 2
    assert len(files_payload["items"]) == 1

    filtered_payload = get_scan_job_files(
        job_id=job_id,
        category="filtered",
        offset=0,
        limit=10,
        query="c.txt",
    )
    assert filtered_payload["total"] == 1
    assert filtered_payload["items"] == ["c.txt"]


def test_scan_job_cancel(tmp_path: Path, monkeypatch) -> None:
    def _slow_scan_dataset(
        dataset_path: str,
        include=None,
        exclude=None,
        size_limit_mb=None,
        progress_callback=None,
        cancel_requested=None,
    ) -> DatasetInfo:
        for i in range(200):
            if cancel_requested and cancel_requested():
                raise ScanCancelledError("cancelled")
            if progress_callback:
                progress_callback(
                    {
                        "phase": "analyzing",
                        "message": "working",
                        "percentage": float(i) / 2.0,
                        "counters": {"total_seen": i},
                    }
                )
            time.sleep(0.005)
        return DatasetInfo(
            dataset_root=str(Path(dataset_path).resolve()),
            scanned_at="2026-01-01T00:00:00Z",
            parameters={"include": include or [], "exclude": exclude or [], "size_limit_mb": size_limit_mb},
            totals={"total_seen": 0, "candidates": 0, "unreadable": 0, "too_large": 0, "filtered": 0},
            extensions={},
            duplicates_groups=[],
            too_large=[],
            unreadable=[],
            candidates=[],
            filtered=[],
        )

    monkeypatch.setattr(scan_jobs_module, "scan_dataset", _slow_scan_dataset)

    dataset = tmp_path / "dataset"
    dataset.mkdir()
    output = tmp_path / "out"
    profile = _build_profile(dataset, output)

    created = create_scan_job(profile)
    job_id = created["job_id"]

    cancel_requested = cancel_scan_job(job_id)
    assert cancel_requested is True

    status = _wait_for_terminal(job_id)
    assert status["status"] == "cancelled"


def test_scan_job_files_limit_validation(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    (dataset / "a.xmi").write_text("<a/>", encoding="utf-8")
    output = tmp_path / "out"
    profile = _build_profile(dataset, output)

    created = create_scan_job(profile)
    job_id = created["job_id"]
    _wait_for_terminal(job_id)

    payload = get_scan_job_files(
        job_id=job_id,
        category="candidates",
        offset=0,
        limit=SCAN_FILES_MAX_LIMIT,
    )
    assert payload["total"] == 1

    try:
        get_scan_job_files(job_id=job_id, category="candidates", offset=0, limit=SCAN_FILES_MAX_LIMIT + 1)
    except ValueError as exc:
        assert "limit must be in range" in str(exc)
    else:
        raise AssertionError("Expected ValueError for out-of-range limit")
