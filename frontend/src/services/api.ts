/** API service layer using axios */

import axios from 'axios';
import { z } from 'zod';
import type {
  ScanRequest,
  ScanResponse,
  ParseRequest,
  ParseResponse,
  MeasureRequest,
  MeasureResponse,
  ReportRequest,
  ReportResponse,
} from '../types/api';

// Use relative URL so it works in both dev (with proxy) and production (same origin)
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Zod schemas for validation
export const ScanRequestSchema = z.object({
  dataset_path: z.string().min(1, 'Dataset path is required'),
  out: z.string().min(1, 'Output directory is required'),
  include: z.array(z.string()).nullable().optional(),
  exclude: z.array(z.string()).nullable().optional(),
  size_limit_mb: z.number().positive().nullable().optional(),
});

export const ParseRequestSchema = z.object({
  dataset_info_path: z.string().min(1, 'Dataset info path is required'),
  output_dir: z.string().min(1, 'Output directory is required'),
  parser_language: z.string().min(1, 'Parser language is required'),
});

export const MeasureRequestSchema = z.object({
  ir_dir: z.string().min(1, 'IR directory is required'),
  output_dir: z.string().min(1, 'Output directory is required'),
});

export const ReportRequestSchema = z.object({
  measures_path: z.string().min(1, 'Measures path is required'),
  measures_per_model_path: z.string().min(1, 'Measures per model path is required'),
  ir_info_path: z.string().nullable().optional(),
});

// API functions
export const apiService = {
  /**
   * Get list of available parser languages
   */
  async getParsers(): Promise<string[]> {
    const response = await api.get<string[]>('/parsers');
    return response.data;
  },

  /**
   * Scan a dataset directory
   */
  async scan(request: ScanRequest): Promise<ScanResponse> {
    // Validate request
    ScanRequestSchema.parse(request);
    
    const response = await api.post<ScanResponse>('/scan', request);
    return response.data;
  },

  /**
   * Parse models from dataset info
   */
  async parse(request: ParseRequest): Promise<ParseResponse> {
    // Validate request
    ParseRequestSchema.parse(request);
    
    const response = await api.post<ParseResponse>('/parse', request);
    return response.data;
  },

  /**
   * Get IR file by ID
   */
  async getIR(irId: string, outputDir: string): Promise<any> {
    const response = await api.get(`/ir/${irId}`, {
      params: { output_dir: outputDir },
    });
    return response.data;
  },

  /**
   * Compute measures from IR models
   */
  async measure(request: MeasureRequest): Promise<MeasureResponse> {
    // Validate request
    MeasureRequestSchema.parse(request);
    
    const response = await api.post<MeasureResponse>('/measure', request);
    return response.data;
  },

  /**
   * Load measures and IR info for reporting
   */
  async report(request: ReportRequest): Promise<ReportResponse> {
    // Validate request
    ReportRequestSchema.parse(request);
    
    const response = await api.post<ReportResponse>('/report', request);
    return response.data;
  },

  /**
   * Get construct profile JSON for a given parser language (e.g. "Ecore", "ArchiMate-Archi")
   */
  async getConstructProfile(parserLanguage: string): Promise<any> {
    const response = await api.get('/construct-profile', {
      params: { parser_language: parserLanguage },
    });
    return response.data;
  },
};

export default apiService;

