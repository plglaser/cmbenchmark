import { useMemo } from 'react';
import type { ReportResponse } from '../types/api';

export function useReportData(reportData: ReportResponse | null) {
  return useMemo(() => {
    if (!reportData) return null;
    // Derived report is now computed on the backend.
    return reportData;
  }, [reportData]);
}
