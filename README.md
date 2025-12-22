# cmbenchmark

A Python-based benchmarking tool for assessing datasets of conceptual models (e.g., UML, ArchiMate, BPMN, Ecore).

## Installation

```bash
pip install -e .
```

## Usage

### Individual Commands

```bash
# Scan dataset directory
cmbenchmark scan <dataset-path>

# Parse and normalize models into IR
cmbenchmark parse <dataset-path> [--out <outdir>]

# Compute metrics on IR models
cmbenchmark metrics <ir-path> [--out <outdir>]

# Generate report
cmbenchmark report <ir-path> <metrics-path> [--out <outdir>]
```

### Full Pipeline

```bash
# Run full pipeline (scan → parse → metrics → report)
cmbenchmark run <dataset-path> [--out <outdir>]
```

## Output Structure

Default output layout in `/out/`:

```
/out/
├── dataset_info.json
├── ir_info.json
├── ir/
│   ├── model1.json
│   └── ...
├── metrics.json
├── report.json
└── report.html
```

