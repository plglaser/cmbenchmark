"""Report generation."""

from pathlib import Path
from typing import Dict, Any
import json
from jinja2 import Template


def generate_report(ir_path: str, measure_path: str, output_dir: str) -> Dict[str, str]:
    """
    Generate JSON and HTML reports.

    Args:
        ir_path: Path to IR directory
        measure_path: Path to measure.json file
        output_dir: Output directory for reports

    Returns:
        Dictionary with paths to generated reports
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load measure
    with open(measure_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    # Load IR info if available
    ir_info_path = Path(ir_path).parent / "ir_info.json"
    ir_info = {}
    if ir_info_path.exists():
        with open(ir_info_path, "r", encoding="utf-8") as f:
            ir_info = json.load(f)

    # Prepare report data
    report_data = {
        "metrics": metrics,
        "ir_info": ir_info,
        "summary": {
            "num_models": metrics.get("num_models", 0),
        },
    }

    # Generate JSON report
    report_json_path = output_path / "report.json"
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    # Generate HTML report
    report_html_path = output_path / "report.html"
    html_content = _generate_html_report(report_data)
    with open(report_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return {
        "json": str(report_json_path),
        "html": str(report_html_path),
    }


def _generate_html_report(report_data: Dict[str, Any]) -> str:
    """Generate HTML report content."""
    template_str = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CMBenchmark Report</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            margin-bottom: 30px;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 15px;
        }
        .metric-card {
            background: #ecf0f1;
            padding: 20px;
            margin: 15px 0;
            border-radius: 5px;
            border-left: 4px solid #3498db;
        }
        .metric-label {
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }
        .metric-value {
            font-size: 1.5em;
            color: #27ae60;
        }
        .language-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .language-item {
            background: #fff;
            padding: 15px;
            border-radius: 5px;
            border: 1px solid #ddd;
            text-align: center;
        }
        .language-name {
            font-weight: bold;
            color: #34495e;
        }
        .language-count {
            font-size: 1.3em;
            color: #3498db;
            margin-top: 5px;
        }
        .section {
            margin: 30px 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background: #34495e;
            color: white;
            font-weight: bold;
        }
        tr:hover {
            background: #f5f5f5;
        }
        .chart-container {
            margin: 30px 0;
            padding: 20px;
            background: #fafafa;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>CMBenchmark Report</h1>
        
        <div class="section">
            <h2>Summary</h2>
            <div class="metric-card">
                <div class="metric-label">Total Models</div>
                <div class="metric-value">{{ report_data.summary.num_models }}</div>
            </div>
        </div>

        <div class="section">
            <h2>Raw Metrics Data</h2>
            <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto;">{{ report_data.metrics | tojson(indent=2) }}</pre>
        </div>
    </div>
</body>
</html>
"""
    template = Template(template_str)
    return template.render(report_data=report_data)

