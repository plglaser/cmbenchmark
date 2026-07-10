# CM Benchmark Web API

FastAPI REST API for the CM Benchmark tool.

## Setup

1. Install dependencies (add to your requirements.txt or install directly):
```bash
pip install fastapi uvicorn[standard]
```

2. Run the API server:
```bash
# From the project root
uvicorn cmbenchmark.web.main:app --reload --port 8000
```

Or using Python:
```python
from cmbenchmark.web.main import app
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)
```

The API will be available at http://localhost:8000

API documentation (Swagger UI) will be available at http://localhost:8000/docs

## Endpoints

### GET /api/parsers
Get list of available parser languages.

### POST /api/scan-jobs
Create an asynchronous scan job.

**Request Body:**
```json
{
  "profile": {
    "name": "Example",
    "version": "1.0",
    "output_path": "/path/to/output",
    "scan": {
      "dataset_path": "/path/to/dataset",
      "include": ["*.xml"],
      "exclude": ["**/tmp/**"],
      "size_limit_mb": 100
    },
    "parse": {
      "parser_language": "ArchiMate-Archi"
    }
  }
}
```

**Response:**
Returns `202 Accepted` with a `job_id`.

### GET /api/scan-jobs/{job_id}
Get current scan job status, progress, and final summary when completed.

### GET /api/scan-jobs/{job_id}/files
Get paginated file details for a completed scan job.

Query params:
- `category`: `candidates | filtered | unreadable | too_large | duplicates`
- `offset`: pagination offset
- `limit`: page size (max 2000)
- `q`: optional substring filter

### DELETE /api/scan-jobs/{job_id}
Request cancellation for a queued/running scan job.

### POST /api/parse-jobs
Create an asynchronous parse job.

**Request Body:**
```json
{
  "profile": {
    "...": "same profile structure as scan"
  }
}
```

### GET /api/parse-jobs/{job_id}
Get parse job status and result.

### DELETE /api/parse-jobs/{job_id}
Request cancellation for parse job.

### POST /api/measure-jobs
Create an asynchronous measure job.

Result artifacts:
- `measures.json`
- `measures_index.json`
- `measures/{model_id}.json`

### GET /api/measure-jobs/{job_id}
Get measure job status and result.

### DELETE /api/measure-jobs/{job_id}
Request cancellation for measure job.

### POST /api/report-jobs
Create an asynchronous report job.

Derived report payload now includes D5 (Bias) fields when `measure.bias.enabled=true`:
- `genderSurface*` (D5.M1.1 Facet Coding; lexical + name fallback across all included labels)
- `localeSurface*` (D5.M3.1 Geography × Surface Coding)

Each D5 block exposes an `insufficient` flag (`insufficient_evidence` at measure level)
to indicate low-sample outputs (`min_n` from the bias profile).

### GET /api/report-jobs/{job_id}
Get report job status and result.

### DELETE /api/report-jobs/{job_id}
Request cancellation for report job.

### GET /api/report-fields
Discover dataset/per-model fields from `measures.json` and split model measure files.

Query params:
- `output_dir`: output directory containing measure artifacts

### GET /api/custom-views
List saved custom view definitions for an output directory.

Query params:
- `output_dir`: output directory containing `custom_views.json`

### POST /api/custom-views
Create and persist a custom view definition.

### PUT /api/custom-views/{view_id}
Update a persisted custom view definition.

### DELETE /api/custom-views/{view_id}
Delete a persisted custom view definition.

Query params:
- `output_dir`: output directory containing `custom_views.json`

### POST /api/custom-views/preview
Compute a preview payload for a custom view definition against the current measure outputs.

## CORS

CORS is configured to allow requests from:
- http://localhost:5173 (Vite default)
- http://localhost:3000 (alternative dev server)
