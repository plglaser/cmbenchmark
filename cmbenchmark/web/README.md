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

### POST /api/scan
Scan a dataset directory for model files.

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
Returns scan results including statistics, file extensions, duplicates, etc.
The `dataset_info.json` file is saved to the profile's `output_path`.

### POST /api/parse
Parse models from `dataset_info.json` saved in the profile output directory.

**Request Body:**
```json
{
  "profile": {
    "...": "same profile structure as scan"
  }
}
```

**Response:**
Returns parse results including statistics, loss summary, and failures.

## CORS

CORS is configured to allow requests from:
- http://localhost:5173 (Vite default)
- http://localhost:3000 (alternative dev server)

