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
  "dataset_path": "/path/to/dataset",
  "exclude": "*.xml,*.tmp",  // optional
  "size_limit_mb": 100  // optional
}
```

**Response:**
Returns scan results including statistics, file extensions, duplicates, etc.
The `dataset_info.json` file is automatically saved to the dataset root directory.

### POST /api/parse
Parse models from dataset_info.json.

**Request Body:**
```json
{
  "dataset_info_path": "/path/to/dataset_info.json",
  "output_dir": "/path/to/output",
  "parser_language": "UML"
}
```

**Response:**
Returns parse results including statistics, loss summary, and failures.

## CORS

CORS is configured to allow requests from:
- http://localhost:5173 (Vite default)
- http://localhost:3000 (alternative dev server)

