"""CLI interface for cmbenchmark."""

from pathlib import Path
from typing import Optional, List
import typer
import subprocess
import sys
import shutil
from rich.console import Console
from rich.table import Table
import json

from cmbenchmark.services import scan_dataset, generate_report
from cmbenchmark.services.measure import compute_measure, save_measure_dataset, save_measure_per_model
from cmbenchmark.services.parse import parse_from_scan
from cmbenchmark.services.scan import DEFAULT_INCLUDE_PATTERNS
from cmbenchmark.utils import info, section, success, warn, error, step
from cmbenchmark.types.profile import BenchmarkProfile

# Import parsers to register them
from cmbenchmark.parser.uml import parser as uml_parser  # noqa: F401
from cmbenchmark.parser.archimate import ArchiMateArchiParser  # noqa: F401
from cmbenchmark.parser.archimate import ArchiMateXMLParser  # noqa: F401
from cmbenchmark.parser.ecore import EcoreParser  # noqa: F401

app = typer.Typer(help="CMBenchmark - A benchmarking tool for conceptual models")
console = Console()


def _run_full_pipeline(dataset_path: str, parser: str, out: Optional[str]):
    """Internal function to run the full pipeline."""
    output_dir = Path(out) if out else Path("out")
    output_dir.mkdir(parents=True, exist_ok=True)

    section("Running full CMBenchmark pipeline")

    # Step 1: Scan
    info("Step 1: Scanning dataset...")
    _run_scan(dataset_path, str(output_dir), include=None, exclude=None, size_limit=None)
    console.print()

    # Step 2: Parse
    info("Step 2: Parsing models...")
    dataset_info_path = output_dir / "dataset_info.json"
    if dataset_info_path.exists():
        _run_parse_from_scan(str(dataset_info_path), str(output_dir), parser)
    else:
        warn("Warning: No dataset_info.json found, skipping parse step")
    console.print()

    # Step 3: Measure
    ir_dir = output_dir / "ir"
    if not ir_dir.exists() or not list(ir_dir.glob("*.json")):
        warn("Warning: No IR files found, skipping measure")
    else:
        info("Step 3: Computing measures...")
        _run_measure(str(ir_dir), str(output_dir), profile=None)
        console.print()

    # Step 4: Report
    measure_file = output_dir / "measures.json"
    if not measure_file.exists():
        warn("Warning: No measure file found, skipping report")
    else:
        info("Step 4: Generating report...")
        _run_report(str(ir_dir), str(measure_file), str(output_dir))
        console.print()

    success("Pipeline complete!")
    console.print(f"  Output directory: {output_dir}")


@app.command()
def run(
    dataset_path: str = typer.Argument(..., help="Path to dataset directory"),
    parser: str = typer.Argument(..., help="Parser language to use (e.g., UML, BPMN, ArchiMate)"),
    out: Optional[str] = typer.Option(None, "--out", help="Output directory"),
):
    """Run full pipeline sequentially (scan → parse → measure → report)."""
    _run_full_pipeline(dataset_path, parser, out)


def _run_scan(dataset_path: str, out: str, include: Optional[List[str]] = None, exclude: Optional[List[str]] = None, size_limit: Optional[int] = None):
    """Internal function to run scan."""
    output_dir = Path(out)
    output_dir.mkdir(parents=True, exist_ok=True)

    with step("Scanning dataset..."):
        dataset_info = scan_dataset(dataset_path, include=include, exclude=exclude, size_limit_mb=size_limit)

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
    dataset_path: str = typer.Argument(..., help="Path to dataset directory"),
    out: Optional[str] = typer.Option(None, "--out", help="Output directory"),
    include: Optional[List[str]] = typer.Option(None, "--include", help=f"File pattern to include (repeatable). If not provided, uses default patterns: {', '.join(DEFAULT_INCLUDE_PATTERNS)}. Patterns match filenames (e.g., '*.xml') or relative paths from dataset root (e.g., 'subdir/*')."),
    exclude: Optional[List[str]] = typer.Option(None, "--exclude", help="File pattern to exclude (repeatable). Applied after include filtering. Patterns match filenames (e.g., '*.tmp') or relative paths from dataset root (e.g., 'test/*', 'backup/**')."),
    size_limit: Optional[int] = typer.Option(None, "--size-limit", help="Size limit for individual files in MB"),
):
    """Scan dataset directory for model files and basic statistics."""
    output_dir = out if out else "out"
    _run_scan(dataset_path, output_dir, include=include, exclude=exclude, size_limit=size_limit)


def _run_parse_from_scan(dataset_info_path: str, out: str, parser_language: str):
    """Internal function to run parse from scan results."""
    output_dir = Path(out)
    output_dir.mkdir(parents=True, exist_ok=True)

    with step("Parsing models..."):
        ir_info = parse_from_scan(dataset_info_path, str(output_dir), parser_language)

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
    parser: str = typer.Argument(..., help="Parser language to use (e.g., UML, BPMN, ArchiMate)"),
    from_scan: Optional[str] = typer.Option(
        None,
        "--from-scan",
        help="Path to dataset_info.json from scan stage. If not provided, will try to find it in output directory.",
    ),
    out: Optional[str] = typer.Option(None, "--out", help="Output directory"),
):
    """Parse and normalize models into IR."""
    output_dir = Path(out) if out else Path("out")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Resolve dataset_info.json path
    if from_scan:
        dataset_info_path = from_scan
    else:
        # Try to find dataset_info.json in output directory
        dataset_info_path = output_dir / "dataset_info.json"
        if not dataset_info_path.exists():
            error("No dataset_info.json found. Please run 'scan' first or provide --from-scan.")
            raise typer.Exit(1)
        dataset_info_path = str(dataset_info_path)

    _run_parse_from_scan(dataset_info_path, str(output_dir), parser)


def _load_profile(profile_path: Optional[str]) -> Optional[BenchmarkProfile]:
    """Load BenchmarkProfile from JSON file."""
    if not profile_path:
        return None
    
    profile_file = Path(profile_path)
    if not profile_file.exists():
        error(f"Profile file does not exist: {profile_path}")
        raise typer.Exit(1)
    
    try:
        with open(profile_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return BenchmarkProfile(**data)
    except Exception as e:
        error(f"Failed to load profile: {e}")
        raise typer.Exit(1)


def _run_measure(ir_path: str, out: str, profile: Optional[BenchmarkProfile] = None):
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

    # Save per-model measures
    measure_per_model_path = output_dir / "measures_per_model.json"
    save_measure_per_model(measure_per_model, str(measure_per_model_path))

    success("Measure computation complete")
    console.print(f"  Dataset measures: {measure_dataset_path}")
    console.print(f"  Per-model measures: {measure_per_model_path}")

    # Display summary
    table = Table(title="Measure Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Number of Models", str(measure_dataset.num_models))
    if measure_dataset.avg_elements_per_model:
        table.add_row(
            "Avg Elements/Model",
            str(measure_dataset.avg_elements_per_model),
        )

    console.print("\n")
    console.print(table)


@app.command()
def measure(
    ir_path: str = typer.Argument(..., help="Path to IR directory"),
    out: Optional[str] = typer.Option(None, "--out", help="Output directory"),
    profile: Optional[str] = typer.Option(None, "--profile", help="Path to benchmark profile JSON file"),
):
    """Compute measures on IR models."""
    output_dir = out if out else "out"
    benchmark_profile = _load_profile(profile)
    _run_measure(ir_path, output_dir, profile=benchmark_profile)


def _run_report(ir_path: str, measure_path: str, out: str):
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
        report_paths = generate_report(str(ir_dir), str(measure_file), str(output_dir))

    success("Report generation complete")
    console.print(f"  JSON report: {report_paths['json']}")
    console.print(f"  HTML report: {report_paths['html']}")


@app.command()
def report(
    ir_path: str = typer.Argument(..., help="Path to IR directory"),
    measure_path: str = typer.Argument(..., help="Path to measures.json file"),
    out: Optional[str] = typer.Option(None, "--out", help="Output directory"),
):
    """Generate JSON + HTML report."""
    output_dir = out if out else "out"
    _run_report(ir_path, measure_path, output_dir)


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
    
    # Start FastAPI server
    info(f"Starting backend server on http://{host}:{port}")
    success("Web UI is ready!")
    console.print(f"  Open your browser at: http://{host}:{port}")
    console.print("  Press CTRL+C to stop the server")
    console.print()
    
    try:
        import uvicorn
        from cmbenchmark.web.main import app as fastapi_app
        
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

