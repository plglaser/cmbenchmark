"""CLI interface for cmbenchmark."""

from pathlib import Path
from typing import Optional
import typer
import json
import subprocess
import shutil
from rich.console import Console
from rich.table import Table

from cmbenchmark.services import scan_dataset, generate_report
from cmbenchmark.services.measure import compute_measure, save_measure_dataset, save_measure_per_model_split
from cmbenchmark.services.parse import parse_from_scan
from cmbenchmark.utils import info, section, success, warn, error, step
from cmbenchmark.types.profile import BenchmarkProfile

# Import parsers to register them
from cmbenchmark.parser.uml import parser as uml_parser  # noqa: F401
from cmbenchmark.parser.archimate import ArchiMateArchiParser  # noqa: F401
from cmbenchmark.parser.archimate import ArchiMateXMLParser  # noqa: F401
from cmbenchmark.parser.ecore import EcoreParser  # noqa: F401
from cmbenchmark.parser.bpmn import BPMNSignavioJSONParser  # noqa: F401

import uvicorn

app = typer.Typer(help="CMBenchmark - A benchmarking tool for conceptual models")
console = Console()


def _run_full_pipeline(profile: BenchmarkProfile):
    """Internal function to run the full pipeline."""
    output_dir = Path(profile.output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    section(f"Running full CMBenchmark pipeline: {profile.name}")

    # Step 1: Scan
    info("Step 1: Scanning dataset...")
    _run_scan(profile, str(output_dir))
    console.print()

    # Step 2: Parse
    info("Step 2: Parsing models...")
    dataset_info_path = output_dir / "dataset_info.json"
    if dataset_info_path.exists():
        _run_parse_from_scan(profile, str(dataset_info_path), str(output_dir))
    else:
        warn("Warning: No dataset_info.json found, skipping parse step")
    console.print()

    # Step 3: Measure
    ir_dir = output_dir / "ir"
    if not ir_dir.exists() or not list(ir_dir.glob("*.json")):
        warn("Warning: No IR files found, skipping measure")
    else:
        info("Step 3: Computing measures...")
        _run_measure(profile, str(ir_dir), str(output_dir))
        console.print()

    # Step 4: Report
    measure_file = output_dir / "measures.json"
    if not measure_file.exists():
        warn("Warning: No measure file found, skipping report")
    else:
        info("Step 4: Generating report...")
        _run_report(profile, str(ir_dir), str(measure_file), str(output_dir))
        console.print()

    success("Pipeline complete!")
    console.print(f"  Output directory: {output_dir}")


@app.command()
def run(
    profile: str = typer.Option(..., "--profile", help="Path to benchmark profile JSON file"),
):
    """Run full pipeline sequentially (scan → parse → measure → report)."""
    benchmark_profile = BenchmarkProfile.load_from_file(profile)
    _run_full_pipeline(benchmark_profile)


def _run_scan(profile: BenchmarkProfile, out: str):
    """Internal function to run scan."""
    output_dir = Path(out)
    output_dir.mkdir(parents=True, exist_ok=True)

    scan_config = profile.scan
    with step("Scanning dataset..."):
        dataset_info = scan_dataset(
            scan_config.dataset_path,
            include=scan_config.include,
            exclude=scan_config.exclude,
            size_limit_mb=scan_config.size_limit_mb,
        )

    # Save dataset info
    info_path = output_dir / "dataset_info.json"
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(dataset_info.to_dict(), f, indent=2)

    success("Dataset scan complete")
    console.print(f"  Total files seen: {dataset_info.totals['total_seen']}")
    console.print(f"  Candidates: {dataset_info.totals['candidates']}")
    console.print(f"  Unreadable: {dataset_info.totals['unreadable']}")
    console.print(f"  Too large: {dataset_info.totals['too_large']}")
    console.print(f"  Duplicate groups: {len(dataset_info.duplicates_groups)}")
    console.print(f"  Output: {info_path}")


@app.command()
def scan(
    profile: str = typer.Option(..., "--profile", help="Path to benchmark profile JSON file"),
):
    """Scan dataset directory for model files and basic statistics."""
    benchmark_profile = BenchmarkProfile.load_from_file(profile)
    output_dir = benchmark_profile.output_path
    _run_scan(benchmark_profile, output_dir)


def _run_parse_from_scan(profile: BenchmarkProfile, dataset_info_path: str, out: str):
    """Internal function to run parse from scan results."""
    output_dir = Path(out)
    output_dir.mkdir(parents=True, exist_ok=True)

    parse_config = profile.parse
    with step("Parsing models..."):
        ir_info = parse_from_scan(
            dataset_info_path,
            str(output_dir),
            parse_config.parser_language,
            ecore_enable_scoped_uri_mappings=getattr(
                parse_config, "ecore_enable_scoped_uri_mappings", None
            ),
        )

    # Display results
    totals = ir_info.totals
    ir_dir = output_dir / "ir"
    ir_info_path = output_dir / "ir_info.json"

    success("Parsing complete")
    console.print(f"  Candidates: {totals['candidates_in']}")
    console.print(f"  Parsed Success: {totals['parsed_success']}")
    console.print(f"  Parsed Warning: {totals['parsed_warning']}")
    console.print(f"  Parsed Failure: {totals['parsed_failure']}")
    console.print(f"  IR directory: {ir_dir}")
    console.print(f"  IR info: {ir_info_path}")


@app.command()
def parse(
    profile: str = typer.Option(..., "--profile", help="Path to benchmark profile JSON file"),
):
    """Parse and normalize models into IR."""
    benchmark_profile = BenchmarkProfile.load_from_file(profile)
    output_dir = Path(benchmark_profile.output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Resolve dataset_info.json path
    dataset_info_path = output_dir / "dataset_info.json"
    if not dataset_info_path.exists():
        error("No dataset_info.json found. Please run 'scan' first.")
        raise typer.Exit(1)

    _run_parse_from_scan(benchmark_profile, str(dataset_info_path), str(output_dir))


def _run_measure(profile: BenchmarkProfile, ir_path: str, out: str):
    """Internal function to run measure."""
    ir_dir = Path(ir_path)
    if not ir_dir.exists():
        error(f"IR path does not exist: {ir_path}")
        raise typer.Exit(1)

    output_dir = Path(out)
    output_dir.mkdir(parents=True, exist_ok=True)

    with step("Computing measures..."):
        measure_dataset, measure_per_model = compute_measure(str(ir_dir), profile=profile)

    # Save dataset-level measures
    measure_dataset_path = output_dir / "measures.json"
    save_measure_dataset(measure_dataset, str(measure_dataset_path))

    # Save per-model measures in split layout
    save_measure_per_model_split(measure_per_model, str(output_dir))
    measures_dir = output_dir / "measures"
    measures_index_path = output_dir / "measures_index.json"

    success("Measure computation complete")
    console.print(f"  Dataset measures: {measure_dataset_path}")
    console.print(f"  Per-model measures directory: {measures_dir}")
    console.print(f"  Per-model measures index: {measures_index_path}")

    # Display summary
    table = Table(title="Measure Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Number of Models", str(measure_dataset.num_models))

    console.print("\n")
    console.print(table)


@app.command()
def measure(
    profile: str = typer.Option(..., "--profile", help="Path to benchmark profile JSON file"),
):
    """Compute measures on IR models."""
    benchmark_profile = BenchmarkProfile.load_from_file(profile)
    output_dir = Path(benchmark_profile.output_path)
    ir_dir = output_dir / "ir"
    
    if not ir_dir.exists():
        error(f"IR directory does not exist: {ir_dir}")
        raise typer.Exit(1)
    
    _run_measure(benchmark_profile, str(ir_dir), str(output_dir))


def _run_report(profile: BenchmarkProfile, ir_path: str, measure_path: str, out: str):
    """Internal function to run report."""
    ir_dir = Path(ir_path)
    measure_file = Path(measure_path)

    if not ir_dir.exists():
        error(f"IR path does not exist: {ir_path}")
        raise typer.Exit(1)

    if not measure_file.exists():
        error(f"Measure file does not exist: {measure_path}")
        raise typer.Exit(1)

    output_dir = Path(out)
    output_dir.mkdir(parents=True, exist_ok=True)

    with step("Generating report..."):
        measures_index_path = output_dir / "measures_index.json"
        if not measures_index_path.exists():
            error(f"Measures index file does not exist: {measures_index_path}")
            raise typer.Exit(1)

        ir_info_path = output_dir / "ir_info.json"
        report_paths = generate_report(
            str(measure_file),
            str(measures_index_path),
            str(output_dir),
            str(ir_info_path) if ir_info_path.exists() else None,
        )

    success("Report generation complete")
    console.print(f"  JSON report: {report_paths['json']}")


@app.command()
def report(
    profile: str = typer.Option(..., "--profile", help="Path to benchmark profile JSON file"),
):
    """Generate JSON + HTML report."""
    benchmark_profile = BenchmarkProfile.load_from_file(profile)
    output_dir = Path(benchmark_profile.output_path)
    ir_dir = output_dir / "ir"
    measure_file = output_dir / "measures.json"
    
    if not measure_file.exists():
        error(f"Measures file does not exist: {measure_file}")
        raise typer.Exit(1)
    
    _run_report(benchmark_profile, str(ir_dir), str(measure_file), str(output_dir))


@app.command()
def web(
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload (development mode)"),
):
    """Start the web UI (builds frontend and starts backend server)."""
    section("Starting CM Benchmark Web UI")
    
    # Get project root (cli.py is in cmbenchmark/cmbenchmark/, so parent.parent is project root)
    project_root = Path(__file__).parent.parent
    frontend_dir = project_root / "frontend"
    web_dir = Path(__file__).parent / "web"
    static_dir = web_dir / "static"
    
    # Check if frontend directory exists
    if not frontend_dir.exists():
        error(f"Frontend directory not found: {frontend_dir}")
        raise typer.Exit(1)
    
    # Check if npm is available
    npm_cmd = shutil.which("npm")
    if not npm_cmd:
        error("npm not found. Please install Node.js and npm.")
        raise typer.Exit(1)
    
    # Ensure static directory exists
    static_dir.mkdir(parents=True, exist_ok=True)
    
    # Build frontend
    info("Building frontend...")
    try:
        with step("Running npm install..."):
            result = subprocess.run(
                [npm_cmd, "install"],
                cwd=str(frontend_dir),
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                console.print(result.stdout)
                console.print(result.stderr)
                error(f"npm install failed")
                raise typer.Exit(1)
        
        with step("Building frontend..."):
            result = subprocess.run(
                [npm_cmd, "run", "build"],
                cwd=str(frontend_dir),
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                console.print(result.stdout)
                console.print(result.stderr)
                error(f"Frontend build failed")
                raise typer.Exit(1)
        
        success(f"Frontend built successfully to {static_dir}")
    except typer.Exit:
        raise
    except Exception as e:
        error(f"Failed to build frontend: {e}")
        raise typer.Exit(1)
    
    # Check if static directory was created and has content
    if not static_dir.exists():
        error(f"Static directory not found after build: {static_dir}")
        raise typer.Exit(1)
    
    index_file = static_dir / "index.html"
    if not index_file.exists():
        error(f"Frontend build incomplete: index.html not found in {static_dir}")
        raise typer.Exit(1)
    
    # Start FastAPI server (import app after build so main.py sees static_dir)
    from cmbenchmark.web.main import app as fastapi_app

    info(f"Starting backend server on http://{host}:{port}")
    success("Web UI is ready!")
    console.print(f"  Open your browser at: http://{host}:{port}")
    console.print("  Press CTRL+C to stop the server")
    console.print()
    
    try:
        uvicorn.run(
            fastapi_app,
            host=host,
            port=port,
            reload=reload,
        )
    except ImportError:
        error("uvicorn not installed. Please install it: pip install uvicorn[standard]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        info("Server stopped by user")
    except Exception as e:
        error(f"Failed to start server: {e}")
        raise typer.Exit(1)


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
