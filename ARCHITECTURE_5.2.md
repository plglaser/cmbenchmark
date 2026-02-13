# Architecture (Section 5.2) — CM-Benchmark Prototype

This document describes the **implemented** architecture of the CM-Benchmarking prototype in this repository.  
Focus: components, interfaces, runtime topology, and persisted artifacts. (No hypothetical modules.)

---

## 1) System Overview

The prototype is a **file-based benchmarking application**:

- **Backend (Python package `cmbenchmark/`)**
  - **CLI** (Typer): orchestrates pipeline runs from a **benchmark profile JSON**
  - **REST API** (FastAPI): exposes the same pipeline stages for the Web UI
  - **Core services**: scan/parse/measure/report (pure Python; used by both CLI and API)
  - **Parsers**: convert input model files (UML XMI, ArchiMate, Ecore) into a normalized **IR JSON**
  - **Measures**: compute dataset + per-model metrics from IR files
  - **Report builder**: derives a **UI-ready report JSON** from measures (+ optional parse diagnostics)

- **Frontend (`frontend/`)**
  - React + TypeScript + Vite UI implementing a **step-by-step workflow** (Scan → Parse → Measure → Report)
  - Talks to backend via **Axios** calls to `/api/*`
  - In production, the compiled SPA is served by FastAPI from `cmbenchmark/web/static/`

- **Persistence**
  - No database. **All state is on disk** in `profile.output_path` as JSON artifacts.

---

## 2) Component Diagram (Runtime Topology)

```mermaid
flowchart LR
  subgraph User
    U[Researcher]
  end

  subgraph CLI["CLI runtime (local)"]
    C["`cmbenchmark` (Typer CLI)\ncmbenchmark/cli.py"]
  end

  subgraph Web["Web runtime (local)"]
    B["FastAPI app\ncmbenchmark/web/main.py"]
    UI["React SPA (Vite build)\nfrontend/ → cmbenchmark/web/static/"]
  end

  subgraph Core["Core library (shared)"]
    S1["Scan service\ncmbenchmark/services/scan.py"]
    S2["Parse service\ncmbenchmark/services/parse.py"]
    S3["Measure service\ncmbenchmark/services/measure.py"]
    S4["Report service\ncmbenchmark/services/report.py"]
    P["Parsers registry + implementations\ncmbenchmark/parser/*"]
    M["Measure functions\ncmbenchmark/measures/*"]
    T["Types (Pydantic-like)\ncmbenchmark/types/*"]
    CC["Construct catalog\ncmbenchmark/construct_catalog.py"]
  end

  FS[(Filesystem\nDataset + output artifacts)]

  U -->|runs| C
  U -->|opens browser| UI
  UI <-->|HTTP JSON| B

  C --> S1 --> FS
  C --> S2 --> FS
  C --> S3 --> FS
  C --> S4 --> FS

  B --> S1
  B --> S2
  B --> S3
  B --> S4

  S2 --> P
  S3 --> M
  S3 --> CC
  S1 --> T
  S2 --> T
  S3 --> T
  S4 --> T
```

Key property: **CLI and REST API share the same services**, so stage semantics and outputs are aligned.

---

## 3) Entry Points & Interfaces

### 3.1 CLI (`cmbenchmark/cli.py`)

**Script entry point** (configured in `pyproject.toml`):

- `cmbenchmark = cmbenchmark.cli:main`

**Commands** (all profile-driven):

- `cmbenchmark scan --profile <profile.json>`
- `cmbenchmark parse --profile <profile.json>`
- `cmbenchmark measure --profile <profile.json>`
- `cmbenchmark report --profile <profile.json>`
- `cmbenchmark run --profile <profile.json>` (scan → parse → measure → report)
- `cmbenchmark web [--host ...] [--port ...] [--reload]`
  - builds the frontend (Vite) into `cmbenchmark/web/static/`
  - starts `uvicorn` serving the FastAPI app

### 3.2 REST API (`cmbenchmark/web/main.py`, `cmbenchmark/web/api/endpoints.py`)

Mounted under `/api`:

- `GET /api/parsers` → list registered parser languages
- `GET /api/construct-profile?parser_language=...` → packaged construct profile JSON (for UI introspection)
- `POST /api/scan` → run scan stage, persists `dataset_info.json`
- `POST /api/parse` → run parse stage (reads `dataset_info.json`), persists `ir/` + `ir_info.json`
- `GET /api/ir/{ir_id}?output_dir=...` → load and return one IR JSON
- `POST /api/measure` → run measure stage, persists `measures.json` + `measures_per_model.json`
- `POST /api/report` → build + persist derived `report.json`, and returns the derived payload

Also:

- `GET /health` → health check

### 3.3 Frontend API integration (`frontend/src/services/api.ts`)

Frontend uses:

- Axios base URL: `/api` (relative; works behind Vite proxy in dev and same-origin in prod)
- Zod: basic request shape validation (passes profile through)

Dev server:

- Vite proxy forwards `/api/*` → `http://localhost:8000` (see `frontend/vite.config.ts`)

---

## 4) Configuration Model (Benchmark Profile)

All runs (CLI and REST) are configured via a **Benchmark Profile JSON** that matches `cmbenchmark/types/profile.py`:

- **Top-level**
  - `name`, `version`
  - `output_path`: directory where artifacts are written
- **scan**
  - `dataset_path`
  - `include` / `exclude` glob patterns (optional)
  - `size_limit_mb` (optional)
- **parse**
  - `parser_language` (string key selecting a registered parser)
- **measure** (optional; defaults exist in backend type)
  - `lexical` toggles + tokenizer config
  - `constructs` toggles (optional)
  - `size_complexity` toggles

Path resolution behavior:

- **CLI**: `BenchmarkProfile.load_from_file(...)` resolves **relative** `scan.dataset_path` and `output_path` relative to the profile file location.
- **REST**: `_normalize_profile(...)` resolves `scan.dataset_path` and `output_path` to absolute paths (expands `~`).

---

## 5) Parser Subsystem

### 5.1 Registry

Parsers implement `BaseParser` and register via the `@register_parser` decorator (`cmbenchmark/parser/base.py`).

The backend advertises available languages via:

- `GET /api/parsers`

### 5.2 Implemented parsers (current repo)

Registered `language` keys:

- `UML` → `cmbenchmark/parser/uml/uml_parser.py` (UML XMI → IR graph)
- `ArchiMate-Archi` → `cmbenchmark/parser/archimate/archimate_archi_parser.py`
- `ArchiMate-XML` → `cmbenchmark/parser/archimate/archimate_xml_parser.py`
- `Ecore` → `cmbenchmark/parser/ecore/ecore_parser.py`

Each parse run produces:

- `IR` object: nodes + edges + metadata
- `ParserRunStats`: skipped elements + warnings (used in diagnostics)

---

## 6) Measurement Subsystem

The measure stage computes:

- **Dataset-level measures** (`MeasureResultDataset`) → written to `measures.json`
- **Per-model measures** (`MeasureResultPerModel`) → written to `measures_per_model.json`

Measure categories (modules):

- **Parsing measures (D1)**: derived from `ir_info.json` (`cmbenchmark/measures/parsing_measures.py`)
- **Lexical measures (D2)**: derived from IR labels, enabled by profile (`cmbenchmark/measures/lexical_measures.py`)
- **Construct measures (D3)**: compares IR types against a construct catalog/profile (`cmbenchmark/measures/construct_measures.py`, `cmbenchmark/construct_catalog.py`)
- **Size & complexity (D4)**: graph size/structure metrics (`cmbenchmark/measures/size_complexity_measures.py`)

Construct profiles (packaged):

- JSON in `cmbenchmark/measures/construct_profiles/*.json`
- Served to UI via `GET /api/construct-profile`

---

## 7) Reporting Subsystem (Derived “UI-ready” Report)

Reporting is implemented as a **derivation layer** (not a static HTML generator):

- Input: `measures.json`, `measures_per_model.json`, optional `ir_info.json`
- Output:
  - persists `report.json` (derived payload)
  - returns the derived payload from `POST /api/report` for immediate rendering

Purpose:

- keep the frontend “thin” by centralizing chart/table shaping in Python (`cmbenchmark/services/report.py`)

---

## 8) Artifact & Directory Layout

All artifacts are written to `profile.output_path`:

```
<output_path>/
  dataset_info.json
  ir_info.json
  ir/
    <modelId>.json
    ...
  measures.json
  measures_per_model.json
  report.json
```

Notes:

- IR files use a deterministic **file ID** derived from the SHA256 hash (first 16 hex chars).
- Parse stage recreates (cleans) `<output_path>/ir/` per run to avoid mixing stale IR files.

---

## 9) Frontend Structure (High-level)

The UI is a staged workflow:

- `frontend/src/App.tsx`: profile upload + stage gating
- Step components:
  - `ScanStep.tsx` → calls `/api/scan`
  - `ParseStep.tsx` → calls `/api/parse`
  - `MeasureStep.tsx` → calls `/api/measure`
  - `ReportStep.tsx` → calls `/api/report` and renders charts/tables

Visualization uses client-side chart components (e.g., Recharts) fed by the **derived** report payload.

