# cmbenchmark

A Python-based benchmarking tool for assessing datasets of conceptual models (e.g., UML, ArchiMate, BPMN, Ecore).

## Requirements

- Node.js

## Installation

```bash
pip install -e .
```

## Development

Use the project virtualenv so commands are reproducible across sessions:

```bash
.venv/bin/python -m pip install -e .
.venv/bin/python -m pytest -q
```

## Usage

## Docker

```bash
docker build -t cmbenchmark .
docker run --rm -p 8000:8000 \
  -v "$PWD/out:/out" \
  -v "$PWD/data:/data" \
  cmbenchmark
```

You can then access the Web UI at `http://0.0.0.0:8000`. 

### Web UI

```bash
cmbenchmark web
```

You can then access the Web UI at `http://localhost:8000`. 

### Individual Commands

```bash
# Scan dataset directory
cmbenchmark scan <dataset-path>

# Parse and normalize models into IR
cmbenchmark parse <dataset-path> [--out <outdir>]

# Compute measures on IR models
cmbenchmark measure <ir-path> [--out <outdir>]

# Generate report
cmbenchmark report <ir-path> <measure-path> [--out <outdir>]
```

### Full Pipeline

```bash
# Run full pipeline (scan → parse → measure → report)
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
├── measure.json
├── report.json
└── report.html
```
