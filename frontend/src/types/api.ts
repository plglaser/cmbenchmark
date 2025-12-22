/** API types matching backend Pydantic schemas */

export interface ScanRequest {
  dataset_path: string;
  exclude?: string | null;
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
  };
  totals: {
    total_seen: number;
    candidates: number;
    unreadable: number;
    too_large: number;
  };
  extensions: Record<string, number>;
  duplicates_groups: Array<{
    count: number;
    members: string[];
  }>;
  too_large: string[];
  unreadable: string[];
  candidates: string[];
}

export interface ParseRequest {
  dataset_info_path: string;
  output_dir: string;
  parser_language: string;
}

export interface ParseFailureResponse {
  relpath: string;
  ir_id: string | null;
  stage: string;
  error_class: string;
  message: string;
  parser: string;
}

export interface ParseResponse {
  dataset_root: string;
  parsed_at: string;
  parameters: {
    from_scan: string;
    parser_language: string;
  };
  totals: {
    candidates_in: number;
    parsed_ok: number;
    failed_parse: number;
  };
  loss_summary: {
    total_models: number;
    category_totals: Record<string, number>;
  };
  failures: ParseFailureResponse[];
  index: Record<string, string>;
}

export interface ErrorResponse {
  error: string;
  detail?: string;
}

