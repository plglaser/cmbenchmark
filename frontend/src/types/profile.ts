/** Benchmark Profile type definitions matching backend Pydantic models */

export interface TokenizerConfig {
  name: string;
  split_on_punct?: boolean;
  split_camel_case?: boolean;
  strip?: boolean;
  lowercase?: boolean;
  keep_numbers?: boolean;
  collapse_whitespace?: boolean;
  unicode_nfkc?: boolean;
  stopword_list?: string | null;
  noise_token_list?: string | null;
}

export interface LexicalProfile {
  enabled?: boolean;
  include_nodes?: boolean;
  include_edges?: boolean;
  label_attributes?: string[];
  enable_d2_m1?: boolean;
  enable_d2_m2?: boolean;
  enable_d2_m3?: boolean;
  enable_d2_m4?: boolean;
  enable_d2_m5?: boolean;
  tokenizer?: TokenizerConfig;
}

export interface ParseProfile {
  enabled?: boolean;
}

export interface SizeComplexityProfile {
  enabled?: boolean;
  enable_d4_m1?: boolean;
  enable_d4_m2?: boolean;
  enable_d4_m3?: boolean;
  enable_d4_m4?: boolean;
}

export interface ScanConfig {
  dataset_path: string;
  include?: string[] | null;
  exclude?: string[] | null;
  size_limit_mb?: number | null;
}

export interface ParseConfig {
  parser_language: string;
}

export interface MeasureConfig {
  parse?: ParseProfile;
  lexical?: LexicalProfile;
  size_complexity?: SizeComplexityProfile;
}

export interface ReportConfig {
  // Currently no specific config needed, but kept for extensibility
}

export interface BenchmarkProfile {
  name: string;
  version: string;
  output_path: string;
  scan: ScanConfig;
  parse: ParseConfig;
  measure?: MeasureConfig;
  report?: ReportConfig;
}
