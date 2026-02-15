# cmbenchmark

A Python-based benchmarking tool for assessing datasets of conceptual models (e.g., UML, ArchiMate, Ecore).

The CLI is **profile-driven**: a single JSON file describes where the dataset lives, which parser to use, which measures to compute, and where outputs should be written.

Pipeline stages: `scan → parse → measure → report`

## Usage

### Set Up

A benchmark requires a **dataset** and a **benchmark profile** (JSON). Place the dataset in the `data/` directory (e.g., `data/eamodelset/`) and configure (or reuse) a benchmark profile (see `profiles/`). Make sure the `dataset_path` in the profile matches the path of your dataset (e.g. `../data/eamodelset/`).

### Docker

```bash
docker build -t cmbenchmark .
docker run --rm -p 8000:8000 \
  -v "$PWD/out:/out" \
  -v "$PWD/data:/data" \
  cmbenchmark
```

You can then access the Web UI at [`localhost:8000`](localhost:8000) and upload a profile.


### Web UI (without Docker)

```bash
cmbenchmark web
```

Open `http://localhost:8000`.

### Pipeline commands (without Docker)

```bash
# All commands take a required profile JSON
cmbenchmark scan --profile profile.json
cmbenchmark parse --profile profile.json
cmbenchmark measure --profile profile.json
cmbenchmark report --profile profile.json

# Or run everything in one command
cmbenchmark run --profile profile.json
```

## Profiles

Profiles are JSON files (see `profiles/`) loaded via `--profile`.

Important behavior:
- `scan.dataset_path` and `output_path` are resolved **relative to the profile file location** (unless they are absolute paths).
- `parse.parser_language` selects a parser. Currently available languages: `Ecore`, `ArchiMate-Archi`. `UML (XMI)` is work in progress.

Minimal profile shape:

```json
{
  "name": "MyBenchmark",
  "version": "1.0",
  "output_path": "../out/mybenchmark",
  "scan": {
    "dataset_path": "../data/my-dataset",
    "include": ["**/*.ecore"],
    "exclude": ["**/tmp/**"],
    "size_limit_mb": 100
  },
  "parse": {
    "parser_language": "Ecore",
    "ecore_enable_scoped_uri_mappings": false
  },
  "measure": {},
  "report": {}
}
```

## Output Structure

Output layout inside `output_path/`:

```
/out-or-your-output-path/
├── dataset_info.json
├── ir_info.json
├── ir/
│   ├── model1.json
│   └── ...
├── report.json
├── measures.json
└── measures_per_model.json
```

## Development

Use the project virtualenv so commands are reproducible across sessions:

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install deps
pip install -r requirements.txt
pip install -e .


# Init tests
pytest -q tests/unit
```
