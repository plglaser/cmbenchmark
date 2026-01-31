# CM-Benchmark Application Steps Summary

This document provides a detailed summary of each step in the CM-Benchmark application pipeline: **Scan**, **Parse**, **Measure**, and **Report**.

---

## 1. SCAN Step

### CLI Signature
```bash
cmbenchmark scan <dataset-path> [--out <outdir>] [--include <pattern>...] [--exclude <pattern>...] [--size-limit <MB>]
```

### Input Parameters
- **`dataset_path`** (required): Path to the dataset directory to scan
- **`--out`** (optional): Output directory (default: `"out"`)
- **`--include`** (optional, repeatable): File patterns to include (e.g., `*.xml`, `*.xmi`). If not provided, uses default patterns: `*.xmi`, `*.uml`, `*.xml`, `*.bpmn`, `*.bpmn2`, `*.ecore`, `*.archimate`
- **`--exclude`** (optional, repeatable): File patterns to exclude (applied after include filtering)
- **`--size-limit`** (optional): Maximum file size in MB (files exceeding this are marked as `too_large`)

### Output
- **File**: `{out}/dataset_info.json`
- **Type**: `DatasetInfo` object containing:
  - `dataset_root`: Absolute path to dataset directory
  - `scanned_at`: ISO timestamp of scan
  - `parameters`: Scan parameters used (include/exclude patterns, size_limit)
  - `totals`: Summary statistics (total_seen, candidates, unreadable, too_large, filtered)
  - `extensions`: Count of files by extension
  - `duplicates_groups`: Groups of duplicate files (by hash)
  - `too_large`: List of files exceeding size limit
  - `unreadable`: List of files that couldn't be read
  - `candidates`: List of candidate file paths (relative to dataset root)
  - `filtered`: List of files filtered out by include/exclude patterns

### Detailed Processing Steps

1. **Initialize**
   - Resolve and validate dataset directory path
   - Check directory exists, is readable, and is actually a directory
   - Determine include patterns (use provided or default: `*.xmi`, `*.uml`, `*.xml`, `*.bpmn`, `*.bpmn2`, `*.ecore`, `*.archimate`)
   - Normalize exclude patterns (empty list if None)

2. **Build Candidate File List**
   - Recursively walk directory tree using `rglob("*")`
   - For each file found:
     - Increment `total_seen` counter
     - Check if file matches include patterns (matches against filename, relative path, or absolute path)
     - If no match, add to `filtered_files` and continue
     - Check if file matches exclude patterns
     - If matches exclude, add to `filtered_files` and continue
     - Otherwise, add to `candidate_files` list

3. **Sanity & Safety Checks**
   - For each candidate file:
     - Track file extension counts
     - Check file readability (try to read at least 1 byte)
     - If unreadable, add to `unreadable_files` and continue
     - Check file size against `size_limit_mb` (if specified)
     - If too large, add to `too_large_files`
     - Compute SHA256 hash of file content (for duplicate detection)
     - Group files by hash in `file_hashes` dictionary

4. **Duplicate Detection**
   - Build duplicate groups: for each hash with 2+ files, create a group
   - Sort files in each group deterministically (by relative path)
   - Mark all but the first file in each group as duplicates to exclude

5. **Build Final Candidates List**
   - Create final candidates list excluding:
     - Files in `too_large_files`
     - Files in `unreadable_files`
     - Duplicate files (all but first in each duplicate group)
   - Store relative paths (relative to dataset root)

6. **Create Summary**
   - Generate timestamp (`scanned_at`)
   - Create `DatasetInfo` object with all collected information
   - Save to `{out}/dataset_info.json`

---

## 2. PARSE Step

### CLI Signature
```bash
cmbenchmark parse <parser> [--from-scan <dataset_info.json>] [--out <outdir>]
```

### Input Parameters
- **`parser`** (required): Parser language name (e.g., `"UML"`, `"BPMN"`, `"ArchiMate"`, `"ArchiMate-Archi"`, `"ArchiMate-XML"`, `"Ecore"`)
- **`--from-scan`** (optional): Path to `dataset_info.json` from scan stage. If not provided, looks for it in output directory
- **`--out`** (optional): Output directory (default: `"out"`)

### Output
- **Directory**: `{out}/ir/` - Contains individual IR JSON files (one per successfully parsed model)
- **File**: `{out}/ir_info.json`
- **Type**: `IRInfo` object containing:
  - `dataset_root`: Path to dataset directory
  - `parsed_at`: ISO timestamp of parsing
  - `parameters`: Parser language and source dataset_info path
  - `totals`: Summary statistics (candidates_in, parsed_success, parsed_warning, parsed_failure)
  - `index`: Mapping from IR ID to relative file path (`ir_id -> relpath`)
  - `modelParseDiagnostics`: Per-model diagnostics including:
    - `file_id`: SHA256 hash-based ID (first 16 chars)
    - `relpath`: Relative path to source file
    - `parse_status`: `"success"`, `"warning"`, or `"failure"`
    - `parse_time_ms`: Parsing time in milliseconds
    - `elements_loaded`: Number of elements (nodes + edges) loaded
    - `elements_skipped`: Number of elements skipped during parsing
    - `warning_count`: Total number of warnings
    - `warnings_by_type`: Count of warnings by type
    - `warning_msgs`: Warning messages by type
    - `parse_error_msg`: Error message if parsing failed
    - `file_size_bytes_source`: Source file size
    - `file_size_bytes_ir`: IR file size

### Detailed Processing Steps

1. **Initialize**
   - Load `dataset_info.json` from scan stage
   - Validate dataset root directory exists
   - Create output directory structure: `{out}/ir/`
   - Get parser class by language name (case-insensitive matching)
   - Instantiate parser
   - Generate timestamp (`parsed_at`)
   - Initialize tracking structures:
     - `totals`: Counters for candidates_in, parsed_success, parsed_warning, parsed_failure
     - `index`: Mapping from IR ID to relative path
     - `model_diagnostics`: Mapping from IR ID to diagnostics

2. **Process Each Candidate File**
   For each candidate file from `dataset_info.candidates`:
   
   a. **File Preparation**
      - Resolve absolute file path
      - Compute deterministic file ID using SHA256 hash (first 16 characters)
      - Initialize `ModelParseDiagnostics` with file_id and relpath
      - Get source file size
   
   b. **Parse with Timing**
      - Start parser run
      - Record parse start time
      - Attempt to parse file using parser's `parse()` method
      - Record parse end time and compute duration
      - If successful:
        - Set IR ID to file_id
        - Update diagnostics with:
          - Parse time (milliseconds)
          - Elements loaded (nodes + edges count)
          - Elements skipped
          - Warning count and details
        - Determine parse status:
          - `"success"`: No warnings and no skipped elements
          - `"warning"`: Has warnings or skipped elements, but elements were loaded
          - `"failure"`: No elements loaded
      - If exception occurs:
        - Record parse time
        - Set status to `"failure"`
        - Store error message
   
   c. **Save IR File** (if parsing succeeded)
      - Add metadata to IR:
        - `source_path`: Absolute path to source file
        - `source_relpath`: Relative path
        - `filesize`: Source file size
      - Save IR to `{ir_dir}/{ir_id}.json`
      - Get IR file size
      - Update index: `index[ir_id] = relpath`
      - Store diagnostics: `model_diagnostics[ir_id] = diagnostics`
   
   d. **Update Totals**
      - Increment appropriate counter based on parse status:
        - `parsed_success` for "success"
        - `parsed_warning` for "warning"
        - `parsed_failure` for "failure"

3. **Build IRInfo Object**
   - Create `IRInfo` object with all collected information
   - Include dataset root, timestamp, parameters, totals, index, and diagnostics

4. **Save Output Files**
   - Save `ir_info.json` to output directory
   - Return `IRInfo` object

---

## 3. MEASURE Step

### CLI Signature
```bash
cmbenchmark measure <ir-path> [--out <outdir>] [--profile <profile.json>]
```

### Input Parameters
- **`ir_path`** (required): Path to directory containing IR JSON files (typically `{out}/ir/`)
- **`--out`** (optional): Output directory (default: `"out"`)
- **`--profile`** (optional): Path to benchmark profile JSON file for configuring measures

### Output
- **File**: `{out}/measures.json` - Dataset-level measures
- **File**: `{out}/measures_per_model.json` - Per-model measures
- **Type**: 
  - `MeasureResultDataset`: Aggregated measures across all models
  - `MeasureResultPerModel`: Measures for each individual model

**MeasureResultDataset** contains:
- `num_models`: Total number of models
- `avg_elements_per_model`: Average elements per model
- `avg_nodes_per_model`: Average nodes per model
- `avg_edges_per_model`: Average edges per model
- `total_elements`: Total elements across all models
- `total_nodes`: Total nodes across all models
- `total_edges`: Total edges across all models
- `edge_to_node_ratio`: Ratio of edges to nodes
- `language_specific`: Language-specific metrics (UML, BPMN, ArchiMate, etc.)
- `parsing`: Parsing measures (dataset-level)
- `lexical`: Lexical measures (dataset-level, if enabled)

**MeasureResultPerModel** contains:
- `parsing`: Per-model parsing measures
- `lexical`: Per-model lexical measures (if enabled)

### Detailed Processing Steps

1. **Initialize**
   - Load benchmark profile (or use default if not provided)
   - Validate IR directory exists
   - Find all IR JSON files in directory (`*.json`)

2. **Load IR Models**
   - For each IR JSON file:
     - Attempt to load IR model using `IR.load()`
     - Skip files that can't be loaded (log error, continue)
   - Validate at least one valid IR model was loaded

3. **Load IRInfo**
   - Attempt to load `ir_info.json` from:
     - `{ir_path}/ir_info.json` (if ir_path is parent directory)
     - `{ir_path}/../ir_info.json` (if ir_path is ir/ subdirectory)
   - Required for parsing measures computation

4. **Compute Cross-Language Metrics**
   - Compute size and shape metrics:
     - Total/average elements, nodes, edges
     - Edge-to-node ratio
   - Compute diversity metrics (if implemented)

5. **Compute Language-Specific Metrics**
   - Group models by language
   - For each language:
     - **UML**: Compute UML-specific metrics (class metrics, attribute metrics, inheritance metrics, etc.)
     - **BPMN**: Compute BPMN-specific metrics
     - **ArchiMate**: Compute ArchiMate validation errors

6. **Compute Parsing Measures**
   - Analyze `IRInfo` to compute:
     - Parse success/warning/failure rates
     - Warning statistics (by type)
     - Parse time statistics
     - Elements loaded/skipped statistics
   - Returns both dataset-level and per-model parsing measures

7. **Compute Lexical Measures** (if enabled in profile)
   - Analyze naming conventions:
     - Naming pattern statistics (camelCase, snake_case, etc.)
     - Naming consistency metrics
     - Vocabulary diversity (entropy)
     - Naming length statistics
   - Returns both dataset-level and per-model lexical measures

8. **Combine Results**
   - Create `MeasureResultDataset` with:
     - Cross-language metrics
     - Language-specific metrics
     - Parsing measures
     - Lexical measures (if enabled)
   - Create `MeasureResultPerModel` with:
     - Per-model parsing measures
     - Per-model lexical measures (if enabled)

9. **Save Output Files**
   - Save `measures.json` (dataset-level)
   - Save `measures_per_model.json` (per-model)

---

## 4. REPORT Step

### CLI Signature
```bash
cmbenchmark report <ir-path> <measure-path> [--out <outdir>]
```

### Input Parameters
- **`ir_path`** (required): Path to IR directory (used to locate `ir_info.json`)
- **`measure_path`** (required): Path to `measures.json` file
- **`--out`** (optional): Output directory (default: `"out"`)

### Output
- **File**: `{out}/report.json` - JSON report with all metrics and IR info
- **File**: `{out}/report.html` - HTML report for visualization

**Report Structure**:
- `metrics`: All measures from `measures.json`
- `ir_info`: IR information from `ir_info.json` (if available)
- `summary`: Summary statistics (e.g., num_models)

### Detailed Processing Steps

1. **Initialize**
   - Validate IR directory exists
   - Validate measure file exists
   - Create output directory if it doesn't exist

2. **Load Data**
   - Load `measures.json` file
   - Attempt to load `ir_info.json` from:
     - `{ir_path}/../ir_info.json` (parent directory of IR directory)
   - If `ir_info.json` not found, use empty dict

3. **Prepare Report Data**
   - Combine metrics and IR info into report data structure:
     ```python
     {
         "metrics": <loaded measures>,
         "ir_info": <loaded ir_info or {}>,
         "summary": {
             "num_models": <from metrics>
         }
     }
     ```

4. **Generate JSON Report**
   - Create `report.json` with complete report data
   - Pretty-printed JSON (indent=2)

5. **Generate HTML Report**
   - Use Jinja2 template to render HTML
   - Template includes:
     - Summary section (total models)
     - Cross-language metrics section:
       - Average elements per model
       - Average nodes per model
       - Average edges per model
       - Edge-to-node ratio
     - Language-specific metrics section (if available)
     - Raw metrics data section (pretty-printed JSON)
   - Apply CSS styling for modern, readable presentation
   - Save to `report.html`

6. **Return Report Paths**
   - Return dictionary with paths to both JSON and HTML reports

---

## Pipeline Flow

The full pipeline can be run with a single command:

```bash
cmbenchmark run <dataset-path> <parser> [--out <outdir>]
```

This executes all four steps sequentially:
1. **Scan** → `dataset_info.json`
2. **Parse** → `ir/` directory + `ir_info.json`
3. **Measure** → `measures.json` + `measures_per_model.json`
4. **Report** → `report.json` + `report.html`

Each step validates that required inputs from previous steps exist before proceeding.
