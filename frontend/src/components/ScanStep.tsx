import { useCallback, useEffect, useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ScrollArea } from './ui/scroll-area';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { ChevronDown, ChevronRight, FileText, CheckCircle, EyeOff, FileX, Ban, Copy } from 'lucide-react';
import { apiService } from '../services/api';
import type { ScanResponse, ScanJobStatusResponse } from '../types/api';
import type { BenchmarkProfile } from '../types/profile';
import { ReadonlyField } from './profile/ReadonlyField';
import { ReadonlyListField } from './profile/ReadonlyListField';
import { ConfigCard } from './profile/ConfigCard';
import { StageProgressCard } from './StageProgressCard';

interface ScanStepProps {
  onScanComplete: (result: ScanResponse) => void;
  profile: BenchmarkProfile | null;
}

type ScanDetailsCategory = 'candidates' | 'filtered' | 'unreadable' | 'too_large' | 'duplicates';
type DuplicateGroup = { count: number; members: string[] };

type CategoryDetailsState = {
  items: Array<string | DuplicateGroup>;
  total: number;
  offset: number;
  limit: number;
  q: string;
  loading: boolean;
  loaded: boolean;
  error: string | null;
};

type DetailsByCategory = Record<ScanDetailsCategory, CategoryDetailsState>;

const POLL_INTERVAL_MS = 500;
const DETAILS_PAGE_SIZE = 200;
const MIN_PROGRESS_VISIBLE_MS = 900;

const createInitialDetailsState = (): DetailsByCategory => ({
  candidates: {
    items: [],
    total: 0,
    offset: 0,
    limit: DETAILS_PAGE_SIZE,
    q: '',
    loading: false,
    loaded: false,
    error: null,
  },
  filtered: {
    items: [],
    total: 0,
    offset: 0,
    limit: DETAILS_PAGE_SIZE,
    q: '',
    loading: false,
    loaded: false,
    error: null,
  },
  unreadable: {
    items: [],
    total: 0,
    offset: 0,
    limit: DETAILS_PAGE_SIZE,
    q: '',
    loading: false,
    loaded: false,
    error: null,
  },
  too_large: {
    items: [],
    total: 0,
    offset: 0,
    limit: DETAILS_PAGE_SIZE,
    q: '',
    loading: false,
    loaded: false,
    error: null,
  },
  duplicates: {
    items: [],
    total: 0,
    offset: 0,
    limit: DETAILS_PAGE_SIZE,
    q: '',
    loading: false,
    loaded: false,
    error: null,
  },
});

const tabLabel: Record<ScanDetailsCategory, string> = {
  candidates: 'Candidates',
  unreadable: 'Unreadable',
  too_large: 'Too Large',
  filtered: 'Excluded',
  duplicates: 'Duplicates',
};

const tabPlaceholder: Record<ScanDetailsCategory, string> = {
  candidates: 'Filter candidates...',
  unreadable: 'Filter unreadable files...',
  too_large: 'Filter too large files...',
  filtered: 'Filter excluded files...',
  duplicates: 'Filter duplicate files...',
};

export function ScanStep({ onScanComplete, profile }: ScanStepProps) {
  const [loading, setLoading] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScanResponse | null>(null);
  const [scanSummary, setScanSummary] = useState<ScanJobStatusResponse['result'] | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<ScanJobStatusResponse | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [configOpen, setConfigOpen] = useState(true);
  const [activeDetailsTab, setActiveDetailsTab] = useState<ScanDetailsCategory>('candidates');
  const [detailsByCategory, setDetailsByCategory] = useState<DetailsByCategory>(
    createInitialDetailsState()
  );

  const totals = result?.totals;
  const duplicateGroupsCount = Number(scanSummary?.duplicates_groups_count ?? 0);
  const duplicateFileCount = Number(scanSummary?.duplicates_files_count ?? 0);

  const progress = jobStatus?.progress;
  const progressPercentage =
    typeof progress?.percentage === 'number'
      ? Math.max(0, Math.min(100, progress.percentage))
      : null;
  const progressCounters = progress?.counters ?? {};
  const totalFiles = Number(progressCounters.total_files ?? progressCounters.total_seen ?? 0);
  const filesProcessed = Number(progressCounters.files_processed ?? progressCounters.total_seen ?? 0);

  const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

  const pollUntilTerminal = async (scanJobId: string): Promise<ScanJobStatusResponse> => {
    while (true) {
      const status = await apiService.getScanJob(scanJobId);
      setJobStatus(status);
      if (status.status === 'completed' || status.status === 'failed' || status.status === 'cancelled') {
        return status;
      }
      await delay(POLL_INTERVAL_MS);
    }
  };

  const fetchCategoryPage = useCallback(
    async (
      category: ScanDetailsCategory,
      overrides?: Partial<Pick<CategoryDetailsState, 'offset' | 'limit' | 'q'>>
    ) => {
      if (!jobId) {
        return;
      }

      let request: Pick<CategoryDetailsState, 'offset' | 'limit' | 'q'> = {
        offset: 0,
        limit: DETAILS_PAGE_SIZE,
        q: '',
      };
      setDetailsByCategory((prev) => {
        const current = prev[category];
        request = {
          offset: overrides?.offset ?? current.offset,
          limit: overrides?.limit ?? current.limit,
          q: overrides?.q ?? current.q,
        };
        return {
          ...prev,
          [category]: {
            ...current,
            ...request,
            loading: true,
            error: null,
          },
        };
      });

      try {
        const page = await apiService.getScanJobFiles(
          jobId,
          category,
          request.offset,
          request.limit,
          request.q
        );
        setDetailsByCategory((prev) => ({
          ...prev,
          [category]: {
            ...prev[category],
            items: page.items,
            total: page.total,
            offset: page.offset,
            limit: page.limit,
            loading: false,
            loaded: true,
            error: null,
          },
        }));
      } catch (err: any) {
        setDetailsByCategory((prev) => ({
          ...prev,
          [category]: {
            ...prev[category],
            loading: false,
            error: err.response?.data?.detail || err.message || 'Failed to load page',
          },
        }));
      }
    },
    [jobId]
  );

  useEffect(() => {
    if (!detailsOpen || !jobId || !result) {
      return;
    }
    const state = detailsByCategory[activeDetailsTab];
    if (!state.loaded && !state.loading) {
      void fetchCategoryPage(activeDetailsTab, { offset: 0 });
    }
  }, [detailsOpen, activeDetailsTab, detailsByCategory, fetchCategoryPage, jobId, result]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    setScanSummary(null);
    setActiveDetailsTab('candidates');
    setDetailsByCategory(createInitialDetailsState());
    const runStartedAtMs = Date.now();

    try {
      if (!profile) {
        throw new Error('Load a benchmark profile to run the scan.');
      }

      const created = await apiService.startScanJob({ profile });
      setJobId(created.job_id);

      const finalStatus = await pollUntilTerminal(created.job_id);
      if (finalStatus.status === 'failed') {
        throw new Error(finalStatus.error || 'Scan job failed');
      }
      if (finalStatus.status === 'cancelled') {
        throw new Error('Scan job was cancelled');
      }
      if (finalStatus.status !== 'completed' || !finalStatus.result) {
        throw new Error('Scan job did not complete successfully');
      }

      const scanResult: ScanResponse = {
        dataset_root: finalStatus.result.dataset_root,
        scanned_at: finalStatus.result.scanned_at,
        parameters: finalStatus.result.parameters,
        totals: finalStatus.result.totals,
        extensions: finalStatus.result.extensions,
        duplicates_groups: [],
        too_large: [],
        unreadable: [],
        candidates: [],
        filtered: [],
      };

      setScanSummary(finalStatus.result);
      setResult(scanResult);
      onScanComplete(scanResult);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to scan dataset');
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
      await apiService.cancelScanJob(jobId);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to cancel scan job');
      setCancelling(false);
    }
  };

  const renderCategoryTab = (category: ScanDetailsCategory) => {
    const state = detailsByCategory[category];
    const pageStart = state.total > 0 ? state.offset + 1 : 0;
    const pageEnd = Math.min(state.offset + state.items.length, state.total);
    const pageNumber = Math.floor(state.offset / state.limit) + 1;
    const totalPages = Math.max(1, Math.ceil(state.total / state.limit));

    return (
      <div className="space-y-3">
        <div className="flex gap-2">
          <Input
            placeholder={tabPlaceholder[category]}
            value={state.q}
            onChange={(e) =>
              setDetailsByCategory((prev) => ({
                ...prev,
                [category]: {
                  ...prev[category],
                  q: e.target.value,
                },
              }))
            }
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                void fetchCategoryPage(category, { offset: 0 });
              }
            }}
            className="font-mono"
          />
          <Button type="button" variant="outline" onClick={() => void fetchCategoryPage(category, { offset: 0 })}>
            Search
          </Button>
        </div>

        {state.error && (
          <div className="rounded-md bg-destructive/10 p-2 text-sm text-destructive">{state.error}</div>
        )}

        <div className="rounded-md border">
          <ScrollArea className="h-[400px]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[90px]">#</TableHead>
                  {category === 'duplicates' ? (
                    <>
                      <TableHead className="w-[120px]">Files</TableHead>
                      <TableHead>Members</TableHead>
                    </>
                  ) : (
                    <TableHead>Path</TableHead>
                  )}
                </TableRow>
              </TableHeader>
              <TableBody>
                {state.loading ? (
                  <TableRow>
                    <TableCell colSpan={category === 'duplicates' ? 3 : 2} className="py-8 text-center text-muted-foreground">
                      Loading page...
                    </TableCell>
                  </TableRow>
                ) : state.items.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={category === 'duplicates' ? 3 : 2} className="py-8 text-center text-muted-foreground">
                      No rows found
                    </TableCell>
                  </TableRow>
                ) : (
                  state.items.map((item, index) => {
                    const rowNumber = state.offset + index + 1;
                    if (category === 'duplicates') {
                      const group = item as DuplicateGroup;
                      return (
                        <TableRow key={rowNumber}>
                          <TableCell className="font-mono text-xs">{rowNumber}</TableCell>
                          <TableCell>{group.count}</TableCell>
                          <TableCell className="font-mono text-xs">
                            <div className="line-clamp-2">{group.members.join(' | ')}</div>
                          </TableCell>
                        </TableRow>
                      );
                    }
                    return (
                      <TableRow key={`${rowNumber}-${String(item)}`}>
                        <TableCell className="font-mono text-xs">{rowNumber}</TableCell>
                        <TableCell className="font-mono text-xs">{String(item)}</TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </ScrollArea>
        </div>

        <div className="flex flex-col gap-2 text-sm text-muted-foreground md:flex-row md:items-center md:justify-between">
          <span>
            Showing {pageStart}-{pageEnd} of {state.total}
          </span>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={state.loading || state.offset === 0}
              onClick={() => void fetchCategoryPage(category, { offset: 0 })}
            >
              First
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={state.loading || state.offset === 0}
              onClick={() => void fetchCategoryPage(category, { offset: Math.max(0, state.offset - state.limit) })}
            >
              Prev
            </Button>
            <span className="px-2">
              Page {pageNumber} of {totalPages}
            </span>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={state.loading || state.offset + state.limit >= state.total}
              onClick={() => void fetchCategoryPage(category, { offset: state.offset + state.limit })}
            >
              Next
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={state.loading || state.offset + state.limit >= state.total}
              onClick={() =>
                void fetchCategoryPage(category, {
                  offset: Math.max(0, (Math.ceil(state.total / state.limit) - 1) * state.limit),
                })
              }
            >
              Last
            </Button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Step 1: Scan Dataset</CardTitle>
        <CardDescription>Scan a dataset directory for model files and generate statistics</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {!profile && (
            <div className="rounded-md bg-muted p-3 text-sm text-muted-foreground">
              Upload a benchmark profile to view parameters and run the scan.
            </div>
          )}

          {profile && (
            <div className="space-y-4">
              <ConfigCard title="Scan Configuration" open={configOpen} onOpenChange={setConfigOpen}>
                <ReadonlyField label="Dataset Path" value={profile.scan?.dataset_path} />
                <ReadonlyField label="Output Directory" value={profile.output_path} />
                <ReadonlyListField label="Include Patterns" values={profile.scan?.include ?? undefined} />
                <ReadonlyListField label="Exclude Patterns" values={profile.scan?.exclude ?? undefined} />
                <ReadonlyField label="Size Limit MB" value={profile.scan?.size_limit_mb ?? undefined} />
              </ConfigCard>
            </div>
          )}

          {error && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}

          <div className="flex gap-2">
            <Button type="submit" disabled={loading || !profile || result !== null}>
              {loading ? 'Scanning...' : 'Scan Dataset'}
            </Button>
            {loading && (
              <Button type="button" variant="outline" onClick={handleCancel} disabled={cancelling}>
                {cancelling ? 'Cancelling...' : 'Cancel'}
              </Button>
            )}
          </div>
        </form>

        {loading && jobStatus && (
          <StageProgressCard
            title="Scan Progress"
            status={jobStatus.status}
            phase={progress?.phase}
            message={progress?.message || 'Scan job is running.'}
            percentage={progressPercentage}
            processed={filesProcessed}
            total={totalFiles}
            unitLabel="files"
            details={[
              { label: 'Filtered', value: Number(progressCounters.filtered ?? 0) },
              { label: 'Candidates', value: Number(progressCounters.candidate_total ?? 0) },
              { label: 'Unreadable', value: Number(progressCounters.unreadable ?? 0) },
              { label: 'Too Large', value: Number(progressCounters.too_large ?? 0) },
              { label: 'Duplicates', value: Number(progressCounters.duplicates_groups ?? 0) },
            ]}
          />
        )}

        {result && totals && (
          <div className="mt-6 space-y-4">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-6">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Total Seen</p>
                      <p className="text-2xl font-bold">{totals.total_seen}</p>
                    </div>
                    <FileText className="h-8 w-8 text-muted-foreground" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Candidates</p>
                      <p className="text-2xl font-bold text-green-600">{totals.candidates}</p>
                    </div>
                    <CheckCircle className="h-8 w-8 text-green-600" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Unreadable</p>
                      <p className="text-2xl font-bold text-yellow-600">{totals.unreadable}</p>
                    </div>
                    <EyeOff className="h-8 w-8 text-yellow-600" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Too Large</p>
                      <p className="text-2xl font-bold text-orange-600">{totals.too_large}</p>
                    </div>
                    <FileX className="h-8 w-8 text-orange-600" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Filtered</p>
                      <p className="text-2xl font-bold text-red-600">{totals.filtered}</p>
                    </div>
                    <Ban className="h-8 w-8 text-red-600" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Duplicates</p>
                      <p className="text-xl font-bold text-blue-600">{duplicateGroupsCount} groups</p>
                      <p className="text-xs text-muted-foreground">{duplicateFileCount} files</p>
                    </div>
                    <Copy className="h-8 w-8 text-blue-600" />
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Scan Summary</CardTitle>
                  <CardDescription>Key paths and scan metadata</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="space-y-1 text-sm">
                    <div className="flex items-center justify-between gap-4">
                      <span className="text-muted-foreground">Dataset Root</span>
                      <code className="font-mono text-xs">{result.dataset_root}</code>
                    </div>
                    <div className="flex items-center justify-between gap-4">
                      <span className="text-muted-foreground">Scanned At</span>
                      <span>{new Date(result.scanned_at).toLocaleString()}</span>
                    </div>
                    <div className="flex items-center justify-between gap-4">
                      <span className="text-muted-foreground">Dataset Info</span>
                      <code className="font-mono text-xs">
                        {(result.parameters as any).dataset_info_path || `${result.dataset_root}/dataset_info.json`}
                      </code>
                    </div>
                    {result.parameters.out && (
                      <div className="flex items-center justify-between gap-4">
                        <span className="text-muted-foreground">Output Dir</span>
                        <code className="font-mono text-xs">{result.parameters.out}</code>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Scan Breakdown</CardTitle>
                  <CardDescription>Distribution of scanned files</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {[
                    { label: 'Candidates', count: totals.candidates, color: 'bg-green-600' },
                    { label: 'Unreadable', count: totals.unreadable, color: 'bg-yellow-600' },
                    { label: 'Too Large', count: totals.too_large, color: 'bg-yellow-600' },
                    { label: 'Filtered', count: totals.filtered, color: 'bg-red-600' },
                  ].map((item) => {
                    const percentage = totals.total_seen > 0 ? (item.count / totals.total_seen) * 100 : 0;
                    return (
                      <div key={item.label}>
                        <div className="mb-1 flex items-center justify-between">
                          <span className="text-sm font-medium">{item.label}</span>
                          <span className="text-sm text-muted-foreground">
                            {item.count} ({percentage.toFixed(1)}%)
                          </span>
                        </div>
                        <div className="h-3 w-full overflow-hidden rounded-full bg-muted">
                          <div className={`${item.color} h-full`} style={{ width: `${percentage}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            </div>

            {Object.keys(result.extensions).length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>File Extensions</CardTitle>
                  <CardDescription>Counts grouped by extension</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(result.extensions).map(([ext, count]) => (
                      <span key={ext} className="rounded bg-muted px-2 py-1 text-sm">
                        {ext}: {count}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            <Collapsible open={detailsOpen} onOpenChange={setDetailsOpen}>
              <CollapsibleTrigger asChild>
                <Button variant="outline" className="w-full justify-between">
                  <span>Details</span>
                  {detailsOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-4">
                <Tabs
                  value={activeDetailsTab}
                  onValueChange={(value) => setActiveDetailsTab(value as ScanDetailsCategory)}
                  className="w-full"
                >
                  <TabsList className="grid w-full grid-cols-5">
                    <TabsTrigger value="candidates">{tabLabel.candidates} ({result.totals.candidates})</TabsTrigger>
                    <TabsTrigger value="unreadable">{tabLabel.unreadable} ({result.totals.unreadable})</TabsTrigger>
                    <TabsTrigger value="too_large">{tabLabel.too_large} ({result.totals.too_large})</TabsTrigger>
                    <TabsTrigger value="filtered">{tabLabel.filtered} ({result.totals.filtered})</TabsTrigger>
                    <TabsTrigger value="duplicates">{tabLabel.duplicates} ({duplicateGroupsCount})</TabsTrigger>
                  </TabsList>

                  <TabsContent value="candidates" className="mt-4">
                    {renderCategoryTab('candidates')}
                  </TabsContent>
                  <TabsContent value="unreadable" className="mt-4">
                    {renderCategoryTab('unreadable')}
                  </TabsContent>
                  <TabsContent value="too_large" className="mt-4">
                    {renderCategoryTab('too_large')}
                  </TabsContent>
                  <TabsContent value="filtered" className="mt-4">
                    {renderCategoryTab('filtered')}
                  </TabsContent>
                  <TabsContent value="duplicates" className="mt-4">
                    {renderCategoryTab('duplicates')}
                  </TabsContent>
                </Tabs>
              </CollapsibleContent>
            </Collapsible>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
