/** API service layer using axios */

import axios from 'axios';
import { z } from 'zod';
import type {
  ScanRequest,
  ScanJobCreateResponse,
  ScanJobStatusResponse,
  ScanJobFilesResponse,
  ScanJobCancelResponse,
  StageJobCreateResponse,
  StageJobStatusResponse,
  StageJobCancelResponse,
  ParseRequest,
  MeasureRequest,
  ReportRequest,
  CustomViewFieldsResponse,
  CustomViewListResponse,
  CustomViewDefinition,
  CustomViewPreviewResponse,
  CustomViewDeleteResponse,
} from '../types/api';

// Use relative URL so it works in both dev (with proxy) and production (same origin)
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const MAX_SCAN_FILES_LIMIT = 2000;
const MIN_SCAN_FILES_LIMIT = 1;

// Zod schemas for validation
export const ScanRequestSchema = z.object({
  profile: z.object({}).passthrough(),
});

export const ParseRequestSchema = z.object({
  profile: z.object({}).passthrough(),
});

export const MeasureRequestSchema = z.object({
  profile: z.object({}).passthrough(),
});

export const ReportRequestSchema = z.object({
  profile: z.object({}).passthrough(),
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

  async startScanJob(request: ScanRequest): Promise<ScanJobCreateResponse> {
    ScanRequestSchema.parse(request);
    const response = await api.post<ScanJobCreateResponse>('/scan-jobs', request);
    return response.data;
  },

  async getScanJob(jobId: string): Promise<ScanJobStatusResponse> {
    const response = await api.get<ScanJobStatusResponse>(`/scan-jobs/${jobId}`);
    return response.data;
  },

  async getScanJobFiles(
    jobId: string,
    category: 'candidates' | 'filtered' | 'unreadable' | 'too_large' | 'duplicates',
    offset = 0,
    limit = 100,
    q = ''
  ): Promise<ScanJobFilesResponse> {
    const safeOffset = Math.max(0, Math.floor(offset));
    const safeLimit = Math.min(
      MAX_SCAN_FILES_LIMIT,
      Math.max(MIN_SCAN_FILES_LIMIT, Math.floor(limit))
    );
    const response = await api.get<ScanJobFilesResponse>(`/scan-jobs/${jobId}/files`, {
      params: { category, offset: safeOffset, limit: safeLimit, q },
    });
    return response.data;
  },

  async cancelScanJob(jobId: string): Promise<ScanJobCancelResponse> {
    const response = await api.delete<ScanJobCancelResponse>(`/scan-jobs/${jobId}`);
    return response.data;
  },

  async startParseJob(request: ParseRequest): Promise<StageJobCreateResponse> {
    ParseRequestSchema.parse(request);
    const response = await api.post<StageJobCreateResponse>('/parse-jobs', request);
    return response.data;
  },

  async getParseJob(jobId: string): Promise<StageJobStatusResponse> {
    const response = await api.get<StageJobStatusResponse>(`/parse-jobs/${jobId}`);
    return response.data;
  },

  async cancelParseJob(jobId: string): Promise<StageJobCancelResponse> {
    const response = await api.delete<StageJobCancelResponse>(`/parse-jobs/${jobId}`);
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

  async startMeasureJob(request: MeasureRequest): Promise<StageJobCreateResponse> {
    MeasureRequestSchema.parse(request);
    const response = await api.post<StageJobCreateResponse>('/measure-jobs', request);
    return response.data;
  },

  async getMeasureJob(jobId: string): Promise<StageJobStatusResponse> {
    const response = await api.get<StageJobStatusResponse>(`/measure-jobs/${jobId}`);
    return response.data;
  },

  async cancelMeasureJob(jobId: string): Promise<StageJobCancelResponse> {
    const response = await api.delete<StageJobCancelResponse>(`/measure-jobs/${jobId}`);
    return response.data;
  },

  async startReportJob(request: ReportRequest): Promise<StageJobCreateResponse> {
    ReportRequestSchema.parse(request);
    const response = await api.post<StageJobCreateResponse>('/report-jobs', request);
    return response.data;
  },

  async getReportJob(jobId: string): Promise<StageJobStatusResponse> {
    const response = await api.get<StageJobStatusResponse>(`/report-jobs/${jobId}`);
    return response.data;
  },

  async cancelReportJob(jobId: string): Promise<StageJobCancelResponse> {
    const response = await api.delete<StageJobCancelResponse>(`/report-jobs/${jobId}`);
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

  async getReportFields(outputDir: string): Promise<CustomViewFieldsResponse> {
    const response = await api.get<CustomViewFieldsResponse>('/report-fields', {
      params: { output_dir: outputDir },
    });
    return response.data;
  },

  async getCustomViews(outputDir: string): Promise<CustomViewListResponse> {
    const response = await api.get<CustomViewListResponse>('/custom-views', {
      params: { output_dir: outputDir },
    });
    return response.data;
  },

  async createCustomView(outputDir: string, view: CustomViewDefinition): Promise<CustomViewDefinition> {
    const response = await api.post<CustomViewDefinition>('/custom-views', {
      output_dir: outputDir,
      view,
    });
    return response.data;
  },

  async updateCustomView(outputDir: string, viewId: string, view: CustomViewDefinition): Promise<CustomViewDefinition> {
    const response = await api.put<CustomViewDefinition>(`/custom-views/${viewId}`, {
      output_dir: outputDir,
      view,
    });
    return response.data;
  },

  async deleteCustomView(outputDir: string, viewId: string): Promise<CustomViewDeleteResponse> {
    const response = await api.delete<CustomViewDeleteResponse>(`/custom-views/${viewId}`, {
      params: { output_dir: outputDir },
    });
    return response.data;
  },

  async previewCustomView(outputDir: string, view: CustomViewDefinition): Promise<CustomViewPreviewResponse> {
    const response = await api.post<CustomViewPreviewResponse>('/custom-views/preview', {
      output_dir: outputDir,
      view,
    });
    return response.data;
  },
};

export default apiService;
