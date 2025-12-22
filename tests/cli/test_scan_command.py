from typer.testing import CliRunner
from cmbenchmark.cli import app
import json

runner = CliRunner()

def test_cli_scan_success(tmp_path):
    # Create dataset
    (tmp_path / "a.xmi").write_text("<m/>")

    # Run CLI
    result = runner.invoke(app, ["scan", str(tmp_path), "--out", str(tmp_path / "out")])

    assert result.exit_code == 0
    assert "Dataset scan complete" in result.stdout

    # Output file created
    output_file = tmp_path / "out" / "dataset_info.json"
    assert output_file.exists()

    data = json.loads(output_file.read_text())
    assert data["totals"]["candidates"] == 1


def test_cli_size_limit(tmp_path):
    small = tmp_path / "a.xmi"
    big = tmp_path / "b.xmi"
    small.write_bytes(b"x")
    big.write_bytes(b"x" * 2000000)

    out = tmp_path / "o"

    result = runner.invoke(app, ["scan", str(tmp_path), "--size-limit", "1", "--out", str(out)])
    assert result.exit_code == 0

    data = json.loads((out / "dataset_info.json").read_text())
    assert len(data["too_large"]) == 1


def test_cli_scan_invalid_path():
    result = runner.invoke(app, ["scan", "nonexistent"])
    assert result.exit_code != 0
    assert "does not exist" in result.stdout