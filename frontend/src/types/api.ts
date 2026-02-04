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
  // NOTE: This is a *derived* payload built on the backend (mirrors the old
  // `useReportData()` hook output). The frontend should render this directly.
  parseStatus?: any | null;
  parseStatusChartData: Array<{ name: string; value: number; share: number }>;
  skipRatioHistogram: Array<{ bin: string; count: number }>;
  skipRatioTop10: Array<{
    modelId: string;
    skipRatio: number;
    elementsLoaded: number;
    elementsSkipped: number;
    relpath: string;
  }>;
  parseTimeHistogram: Array<{ bin: string; count: number }>;
  parseTimeScatterData: Array<{ fileSize: number; parseTime: number }>;
  sourceSizeHistogram: Array<{ bin: string; count: number }>;
  irSizeHistogram: Array<{ bin: string; count: number }>;
  fileSizeTop10: Array<{ modelId: string; sourceSize: number; irSize: number; relpath: string }>;
  fileSizeBottom10: Array<{ modelId: string; sourceSize: number; irSize: number; relpath: string }>;
  warningsChartData: Array<{ type: string; count: number }>;
  modelsWithWarnings: Array<{
    modelId: string;
    warningCount: number;
    warningsByType: Record<string, number>;
    relpath: string;
  }>;

  labelPresence?: any | null;
  labelPresenceChartData?: { present: number; missing: number; presentShare: number; missingShare: number } | null;
  labelPresenceByType: Array<{ type: string; missingShare: number }>;

  labelLength?: any | null;
  labelLengthCharsHistogram: Array<{ bin: string; count: number }>;
  labelLengthTokensHistogram: Array<{ bin: string; count: number }>;
  labelLengthTop10: Array<{
    modelId: string;
    relpath: string;
    charsMedian: number;
    tokensMedian: number;
    shortShare: number;
    longShare: number;
  }>;

  namingConvention?: any | null;
  namingConventionChartData: Array<{ caseStyle: string; count: number; share: number }>;
  namingStyleEntropies: number[];
  namingStyleEntropyHistogram: Array<{ bin: string; count: number }>;

  singleMultiWord?: any | null;
  singleMultiWordChartData?: { single: number; multi: number; singleShare: number; multiShare: number } | null;
  singleWordShares: number[];
  singleWordShareHistogram: Array<{ bin: string; count: number }>;

  lexicalDiversity?: any | null;
  lexicalDiversityTop10: Array<{
    modelId: string;
    relpath: string;
    totalTokens: number;
    vocabSize: number;
    typeTokenRatio: number;
    stopwordShare: number;
  }>;

  constructPresence?: any | null;
  constructCatalog: Record<string, any>;
  constructDimensionScore?: number | null;
  constructPresenceChartData?: { observed: number; missing: number; observedShare: number; missingShare: number } | null;
  constructPresencePerModel: Array<{
    modelId: string;
    relpath: string;
    presentConstructs: Record<string, boolean>;
  }>;
  coverageShareHistogram: Array<{ bin: string; count: number }>;
  unknownTypeShareHistogram: Array<{ bin: string; count: number }>;
  lowestCoverage: Array<any>;
  highestCoverage: Array<any>;
  missingConstructs: Array<any>;
  unknownTypes: Array<{ type: string; count: number }>;
  coverageByGroup: Array<any>;
  coverageByKind: Array<any>;
  constructFrequency?: any | null;
  constructFrequencyData: Array<any>;
  constructFrequencyPareto: Array<any>;
  constructFrequencyByGroup: Array<any>;
  constructFrequencyPerModel: Array<{
    modelId: string;
    relpath: string;
    countsByConstruct: Record<string, number>;
  }>;
  constructFrequencyTotalsHistogram: Array<{ bin: string; count: number }>;
  constructFrequencyEntropyHistogram: Array<{ bin: string; count: number }>;
  constructFrequencyTopModels: Array<{
    modelId: string;
    relpath: string;
    totalConstructInstances: number;
    utilizationEntropy: number;
  }>;
  constructFrequencyPerModelShares: Array<{
    modelId: string;
    relpath: string;
    sharesByConstruct: Record<string, number>;
    totalConstructInstances: number;
    utilizationEntropy: number;
  }>;
}
