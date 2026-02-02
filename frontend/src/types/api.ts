/** API types matching backend Pydantic schemas */

export interface ScanRequest {
  dataset_path: string;
  out: string;
  include?: string[] | null;
  exclude?: string[] | null;
  size_limit_mb?: number | null;
}

export interface ScanResponse {
  dataset_root: string;
  scanned_at: string;
  parameters: {
    include: string[];
    exclude: string[];
    size_limit_mb?: number | null;
    dataset_info_path?: string;
    out?: string;
  };
  totals: {
    total_seen: number;
    candidates: number;
    unreadable: number;
    too_large: number;
    filtered: number;
  };
  extensions: Record<string, number>;
  duplicates_groups: Array<{
    count: number;
    members: string[];
  }>;
  too_large: string[];
  unreadable: string[];
  candidates: string[];
  filtered: string[];
}

export interface ParseRequest {
  dataset_info_path: string;
  output_dir: string;
  parser_language: string;
}

export interface ModelParseDiagnostics {
  file_id: string;
  relpath: string;
  parse_status: 'success' | 'warning' | 'failure';
  parse_error_msg: string | null;
  elements_loaded: number;
  elements_skipped: number;
  parse_time_ms: number;
  file_size_bytes_source: number;
  file_size_bytes_ir: number;
  warning_count: number;
  warnings_by_type: Record<string, number>;
  warning_msgs: Record<string, string[]>;
  skip_ratio: number;
  warnings_per_element: number;
}

export interface ParseResponse {
  dataset_root: string;
  parsed_at: string;
  parameters: {
    from_scan: string;
    parser_language: string;
    output_dir?: string;
  };
  totals: {
    candidates_in: number;
    parsed_success: number;
    parsed_warning: number;
    parsed_failure: number;
  };
  index: Record<string, string>;
  modelParseDiagnostics: Record<string, ModelParseDiagnostics>;
}

export interface ErrorResponse {
  error: string;
  detail?: string;
}

export interface IRData {
  id: string;
  language: string;
  data: {
    modelId?: string;
    name?: string;
    version?: string;
    source_path?: string;
    source_relpath?: string;
    filesize?: number;
    documentation?: string;
    [key: string]: any;
  };
  nodes: Array<{
    id: string;
    type: string;
    name: string;
    data: Record<string, any>;
  }>;
  edges: Array<{
    id: string;
    sourceId: string;
    targetId: string;
    type: string;
    data: Record<string, any>;
  }>;
}

export interface MeasureRequest {
  ir_dir: string;
  output_dir: string;
  profile_path?: string | null;
}

export interface MeasureResponse {
  measures_path: string;
  measures_per_model_path: string;
  output_dir: string;
}

export interface ReportRequest {
  measures_path: string;
  measures_per_model_path: string;
  ir_info_path?: string | null;
}

export interface ReportResponse {
  measures: any; // Dataset-level measures
  measures_per_model: any; // Per-model measures
  ir_info?: any | null; // IR info for linking models
}
