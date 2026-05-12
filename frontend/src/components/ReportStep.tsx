import { useState, useMemo, useEffect, useCallback } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Badge } from './ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible';
import { apiService } from '../services/api';
import type {
  CustomViewDefinition,
  CustomViewFieldsResponse,
  CustomViewPreviewResponse,
  ReportResponse,
  StageJobStatusResponse,
} from '../types/api';
import type { BenchmarkProfile } from '../types/profile';
import { createDimensions } from '../data/dimensions';
import { ExpandableTileDialog } from './report/ExpandableTileDialog';
import { StageProgressCard } from './StageProgressCard';
import { CustomViewBuilderDialog } from './report/CustomViewBuilderDialog';
import { CustomViewRenderer } from './report/CustomViewRenderer';

interface ReportStepProps {
  onReportComplete?: (result: ReportResponse) => void;
  profile: BenchmarkProfile | null;
}

const POLL_INTERVAL_MS = 500;
const MIN_PROGRESS_VISIBLE_MS = 900;

export function ReportStep({ onReportComplete, profile }: ReportStepProps) {
  const [loading, setLoading] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reportData, setReportData] = useState<ReportResponse | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<StageJobStatusResponse | null>(null);
  const [selectedDimensionId, setSelectedDimensionId] = useState<string>('parsing');
  const [selectedMeasureId, setSelectedMeasureId] = useState<string | null>(null);
  const [configOpen, setConfigOpen] = useState(true);
  const [customViews, setCustomViews] = useState<CustomViewDefinition[]>([]);
  const [customFields, setCustomFields] = useState<CustomViewFieldsResponse | null>(null);
  const [customPreviews, setCustomPreviews] = useState<Record<string, CustomViewPreviewResponse | null>>({});
  const [customPreviewErrors, setCustomPreviewErrors] = useState<Record<string, string>>({});
  const [customLoading, setCustomLoading] = useState(false);
  const [customError, setCustomError] = useState<string | null>(null);
  const [builderOpen, setBuilderOpen] = useState(false);

  const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

  const pollUntilTerminal = async (reportJobId: string): Promise<StageJobStatusResponse> => {
    while (true) {
      const status = await apiService.getReportJob(reportJobId);
      setJobStatus(status);
      if (status.status === 'completed' || status.status === 'failed' || status.status === 'cancelled') {
        return status;
      }
      await delay(POLL_INTERVAL_MS);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const runStartedAtMs = Date.now();

    try {
      if (!profile) {
        throw new Error('Load a benchmark profile to build the report.');
      }
      const created = await apiService.startReportJob({
        profile,
      });
      setJobId(created.job_id);

      const finalStatus = await pollUntilTerminal(created.job_id);
      if (finalStatus.status === 'failed') {
        throw new Error(finalStatus.error || 'Report job failed');
      }
      if (finalStatus.status === 'cancelled') {
        throw new Error('Report job was cancelled');
      }
      if (finalStatus.status !== 'completed' || !finalStatus.result) {
        throw new Error('Report job did not complete successfully');
      }

      const response = finalStatus.result as ReportResponse;
      setReportData(response);
      if (onReportComplete) {
        onReportComplete(response);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load report data');
    } finally {
      const elapsedMs = Date.now() - runStartedAtMs;
      if (elapsedMs < MIN_PROGRESS_VISIBLE_MS) {
        await delay(MIN_PROGRESS_VISIBLE_MS - elapsedMs);
      }
      setLoading(false);
      setCancelling(false);
    }
  };

  const handleCancel = async () => {
    if (!jobId) {
      return;
    }
    setCancelling(true);
    try {
      await apiService.cancelReportJob(jobId);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to cancel report job');
      setCancelling(false);
    }
  };

  const dimensions = useMemo(
    () => (reportData ? createDimensions(reportData, profile?.parse?.parser_language ?? null) : []),
    [reportData, profile]
  );

  const getMeasureScore = (measureId: string): number | null => {
    if (measureId === 'parse-status') {
      const score = reportData?.parseStatus?.score;
      if (Number.isFinite(score)) {
        return Number(score);
      }
      const robustnessIndex = reportData?.parseStatus?.parsing_robustness_index;
      return Number.isFinite(robustnessIndex) ? Number(robustnessIndex) * 100 : null;
    }
    if (measureId === 'elements-skips') {
      const score = reportData?.parseElementsSkips?.score;
      return Number.isFinite(score) ? Number(score) : null;
    }
    if (measureId === 'warnings') {
      const score = reportData?.parseWarnings?.score;
      return Number.isFinite(score) ? Number(score) : null;
    }
    if (measureId === 'construct-presence') {
      const score = reportData?.constructPresence?.score;
      return Number.isFinite(score) ? Number(score) : null;
    }
    if (measureId === 'construct-frequency') {
      const score = reportData?.constructFrequency?.score;
      return Number.isFinite(score) ? Number(score) : null;
    }
    if (measureId === 'label-presence') {
      const score = reportData?.labelPresence?.score;
      return Number.isFinite(score) ? Number(score) : null;
    }
    return null;
  };

  const getScoreVariant = (score: number): 'destructive' | 'secondary' | 'success' => {
    if (score < 40) {
      return 'destructive';
    }
    if (score < 70) {
      return 'secondary';
    }
    return 'success';
  };

  const getDimensionScore = (dimensionId: string): number | null => {
    if (dimensionId === 'parsing') {
      const score = reportData?.parsingDimensionScore;
      return Number.isFinite(score) ? Number(score) : null;
    }
    if (dimensionId === 'construct-coverage') {
      const score = reportData?.constructDimensionScore;
      return Number.isFinite(score) ? Number(score) : null;
    }
    return null;
  };

  // Get current dimension and measure
  const currentDimension = dimensions.find((d) => d.id === selectedDimensionId);

  // Auto-select first measure when dimension changes
  useEffect(() => {
    if (currentDimension && currentDimension.measures.length > 0) {
      if (!selectedMeasureId || !currentDimension.measures.find((m) => m.id === selectedMeasureId)) {
        setSelectedMeasureId(currentDimension.measures[0].id);
      }
    }
  }, [selectedDimensionId, currentDimension, selectedMeasureId]);

  const outputDir = profile?.output_path ?? null;

  const loadCustomViewState = useCallback(async () => {
    if (!reportData || !outputDir) {
      return;
    }
    setCustomLoading(true);
    setCustomError(null);
    try {
      const [fieldsResponse, viewsResponse] = await Promise.all([
        apiService.getReportFields(outputDir),
        apiService.getCustomViews(outputDir),
      ]);
      setCustomFields(fieldsResponse);
      setCustomViews(viewsResponse.views);

      if (!viewsResponse.views.length) {
        setCustomPreviews({});
        setCustomPreviewErrors({});
        return;
      }

      const previewEntries = await Promise.all(
        viewsResponse.views.map(async (view, idx) => {
          const id = view.id || `${view.name}-${idx}`;
          try {
            const preview = await apiService.previewCustomView(outputDir, view);
            return { id, preview, error: null as string | null };
          } catch (err: any) {
            const message = err.response?.data?.detail || err.message || 'Failed to load preview';
            return { id, preview: null, error: message };
          }
        })
      );

      const nextPreviews: Record<string, CustomViewPreviewResponse | null> = {};
      const nextErrors: Record<string, string> = {};
      previewEntries.forEach(({ id, preview, error: previewError }) => {
        nextPreviews[id] = preview;
        if (previewError) {
          nextErrors[id] = previewError;
        }
      });
      setCustomPreviews(nextPreviews);
      setCustomPreviewErrors(nextErrors);
    } catch (err: any) {
      setCustomError(err.response?.data?.detail || err.message || 'Failed to load custom view configuration');
    } finally {
      setCustomLoading(false);
    }
  }, [reportData, outputDir]);

  useEffect(() => {
    if (!reportData || !outputDir) {
      return;
    }
    loadCustomViewState();
  }, [reportData, outputDir, loadCustomViewState]);

  const handleCreateCustomView = async (view: CustomViewDefinition) => {
    if (!outputDir) {
      throw new Error('Output directory is missing from profile.');
    }
    const created = await apiService.createCustomView(outputDir, view);
    setCustomViews((prev) => [...prev, created]);
    if (created.id) {
      try {
        const preview = await apiService.previewCustomView(outputDir, created);
        setCustomPreviews((prev) => ({ ...prev, [created.id!]: preview }));
        setCustomPreviewErrors((prev) => {
          const next = { ...prev };
          delete next[created.id!];
          return next;
        });
      } catch (err: any) {
        const message = err.response?.data?.detail || err.message || 'Failed to load preview';
        setCustomPreviewErrors((prev) => ({ ...prev, [created.id!]: message }));
      }
    }
  };

  const handleDeleteCustomView = async (viewId?: string) => {
    if (!outputDir || !viewId) {
      return;
    }
    if (!window.confirm('Delete this custom view?')) {
      return;
    }
    try {
      await apiService.deleteCustomView(outputDir, viewId);
      setCustomViews((prev) => prev.filter((view) => view.id !== viewId));
      setCustomPreviews((prev) => {
        const next = { ...prev };
        delete next[viewId];
        return next;
      });
      setCustomPreviewErrors((prev) => {
        const next = { ...prev };
        delete next[viewId];
        return next;
      });
    } catch (err: any) {
      setCustomError(err.response?.data?.detail || err.message || 'Failed to delete custom view');
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Step 4: Report</CardTitle>
        <CardDescription>
          View dashboards of computed measures.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {!reportData && (
          <form onSubmit={handleSubmit} className="space-y-4">
            {!profile && (
              <div className="p-3 text-sm text-muted-foreground bg-muted rounded-md">
                Upload a benchmark profile to view parameters and load the report.
              </div>
            )}

            {profile && (
              <div className="space-y-4">
                <Collapsible open={configOpen} onOpenChange={setConfigOpen}>
                  <div className="rounded-md border">
                    <CollapsibleTrigger asChild>
                      <button
                        type="button"
                        className="w-full flex items-center justify-between px-4 py-3 text-sm font-semibold"
                      >
                        <span>Report Configuration</span>
                        <span className="text-xs text-muted-foreground">
                          {configOpen ? 'Hide' : 'Show'}
                        </span>
                      </button>
                    </CollapsibleTrigger>
                    <CollapsibleContent className="px-4 pb-4">
                      <p className="text-sm text-muted-foreground">
                        Report uses the profile output directory and generated measures. No additional parameters.
                      </p>
                    </CollapsibleContent>
                  </div>
                </Collapsible>
              </div>
            )}

            {error && (
              <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
                {error}
              </div>
            )}

            <div className="flex gap-2">
              <Button type="submit" disabled={loading || !profile}>
                {loading ? 'Loading...' : 'Load Report'}
              </Button>
              {loading && (
                <Button type="button" variant="outline" onClick={handleCancel} disabled={cancelling}>
                  {cancelling ? 'Cancelling...' : 'Cancel'}
                </Button>
              )}
            </div>
          </form>
        )}

        {loading && jobStatus && (
          <StageProgressCard
            title="Report Progress"
            status={jobStatus.status}
            phase={jobStatus.progress?.phase}
            message={jobStatus.progress?.message || 'Report job is running.'}
            percentage={jobStatus.progress?.percentage}
            processed={Number(jobStatus.progress?.counters?.processed_models ?? 0)}
            total={Number(jobStatus.progress?.counters?.total_models ?? 0)}
            unitLabel="models"
          />
        )}

        {reportData && dimensions.length > 0 && (
          <div className="mt-6">
            <Tabs
              value={selectedDimensionId}
              onValueChange={(value) => {
                setSelectedDimensionId(value);
                setSelectedMeasureId(null);
              }}
              className="w-full"
            >
              <TabsList className="flex w-full flex-wrap gap-2 rounded-xl bg-muted/40 p-1.5 shadow-sm border border-border/60">
                {dimensions.map((dimension) => {
                  const score = getDimensionScore(dimension.id);
                  return (
                    <TabsTrigger
                      key={dimension.id}
                      value={dimension.id}
                      className="flex-1 min-w-[160px] justify-center rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm"
                    >
                      <span className="flex items-center gap-2">
                        <span>{dimension.name}</span>
                        {score !== null && (
                          <Badge variant={getScoreVariant(score)} className="text-[10px] h-5 px-2">
                            {Math.round(score)}
                          </Badge>
                        )}
                      </span>
                    </TabsTrigger>
                  );
                })}
              </TabsList>

              {dimensions.map((dimension) => (
                <TabsContent key={dimension.id} value={dimension.id} className="mt-6">
                  <Tabs
                    value={selectedMeasureId ?? dimension.measures[0]?.id ?? ''}
                    onValueChange={(value) => setSelectedMeasureId(value)}
                    className="w-full"
                  >
                    {/* Measures tab bar (separate from dimension tab bar) */}
                    <div className="mt-3 rounded-xl border border-border/60 bg-muted/20 p-2 shadow-sm">
                      <TabsList className="flex w-full flex-wrap justify-start gap-2 h-auto bg-transparent p-0">
                        {dimension.measures.map((measure) => {
                          const score = getMeasureScore(measure.id);
                          return (
                            <TabsTrigger
                              key={measure.id}
                              value={measure.id}
                              className="rounded-full px-3 py-1.5 text-sm font-medium text-muted-foreground data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm"
                            >
                              <span className="flex items-center gap-2">
                                <span>{measure.name}</span>
                                {score !== null && (
                                  <Badge variant={getScoreVariant(score)} className="text-[10px] h-5 px-2">
                                    {Math.round(score)}
                                  </Badge>
                                )}
                              </span>
                            </TabsTrigger>
                          );
                        })}
                      </TabsList>
                    </div>

                    {dimension.measures.map((measure) => (
                      <TabsContent key={measure.id} value={measure.id} className="mt-6">
                        <div className="space-y-6">
                          <div>
                            <h3 className="text-lg font-semibold mb-1">{measure.name}</h3>
                            {measure.description && (
                              <p className="text-sm text-muted-foreground mb-4">
                                {measure.description}
                              </p>
                            )}
                          </div>

                          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                            {measure.tiles.map((tile) => {
                              const tileKey = `${dimension.id}:${measure.id}:${tile.id}`;
                              return (
                                <ExpandableTileDialog key={tileKey} title={tile.title}>
                                  {tile.component}
                                </ExpandableTileDialog>
                              );
                            })}
                          </div>
                        </div>
                      </TabsContent>
                    ))}
                  </Tabs>
                </TabsContent>
              ))}
            </Tabs>
          </div>
        )}

        {reportData && (
          <div className="mt-8 border-t pt-6 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h3 className="text-lg font-semibold">Custom Views</h3>
                <p className="text-sm text-muted-foreground">
                  Create your own charts from dataset-level or per-model measure fields.
                </p>
              </div>
              <div className="flex gap-2">
                <Button type="button" variant="outline" onClick={loadCustomViewState} disabled={customLoading || !outputDir}>
                  Refresh
                </Button>
                <Button type="button" onClick={() => setBuilderOpen(true)} disabled={!customFields || !outputDir}>
                  Create View
                </Button>
              </div>
            </div>

            {customError && (
              <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
                {customError}
              </div>
            )}

            {customLoading && customViews.length === 0 && (
              <div className="p-3 text-sm text-muted-foreground bg-muted rounded-md">
                Loading custom view metadata...
              </div>
            )}

            {!customLoading && customViews.length === 0 && (
              <div className="p-3 text-sm text-muted-foreground bg-muted rounded-md">
                No custom views yet. Create your first custom view.
              </div>
            )}

            {customViews.length > 0 && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {customViews.map((view) => {
                  const key = view.id || view.name;
                  return (
                    <div key={key} className="space-y-2">
                      <div className="flex items-center justify-between px-1">
                        <div className="text-xs text-muted-foreground truncate">
                          {view.description || view.chart_type}
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteCustomView(view.id)}
                          disabled={!view.id}
                        >
                          Delete
                        </Button>
                      </div>
                      <ExpandableTileDialog title={view.name}>
                        <CustomViewRenderer
                          view={view}
                          preview={customPreviews[key] || null}
                          loading={customLoading && !customPreviews[key] && !customPreviewErrors[key]}
                          error={customPreviewErrors[key] || null}
                        />
                      </ExpandableTileDialog>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </CardContent>

      <CustomViewBuilderDialog
        open={builderOpen}
        onOpenChange={setBuilderOpen}
        outputDir={outputDir}
        fields={customFields}
        onCreate={handleCreateCustomView}
      />
    </Card>
  );
}
