import { useState, useEffect, useMemo } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Badge } from './ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './ui/tooltip';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ChevronDown, ChevronRight, Eye, Info, AlertTriangle, CheckCircle, XCircle, Clock, FileText, Zap } from 'lucide-react';
import {
  type ColumnDef,
  type ColumnFiltersState,
  type SortingState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table';
import { apiService } from '../services/api';
import type { ParseResponse, ModelParseDiagnostics, ScanResponse } from '../types/api';
import type { BenchmarkProfile } from '../types/profile';
import { IRVisualization } from './IRVisualization';

const truncatePath = (path: string, maxLength: number = 50) => {
  if (path.length <= maxLength) return path;
  return path.substring(0, maxLength - 3) + '...';
};

const formatBytes = (bytes: number) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

const formatTime = (ms: number) => {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
};

const getStatusBadgeVariant = (status: string) => {
  switch (status) {
    case 'success':
      return 'default';
    case 'warning':
      return 'secondary';
    case 'failure':
      return 'destructive';
    default:
      return 'outline';
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'success':
      return <CheckCircle className="h-4 w-4 text-green-600" />;
    case 'warning':
      return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
    case 'failure':
      return <XCircle className="h-4 w-4 text-red-600" />;
    default:
      return null;
  }
};

interface ParseStepProps {
  scanResult: ScanResponse | null;
  onParseComplete: (result: ParseResponse) => void;
  profile: BenchmarkProfile | null;
}

export function ParseStep({ scanResult, onParseComplete, profile }: ParseStepProps) {
  const [parsers, setParsers] = useState<string[]>([]);
  const [selectedParser, setSelectedParser] = useState('');
  const [datasetInfoPath, setDatasetInfoPath] = useState('');
  const [outputDir, setOutputDir] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingParsers, setLoadingParsers] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ParseResponse | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [selectedDiagnostics, setSelectedDiagnostics] = useState<ModelParseDiagnostics | null>(null);
  const [selectedIrId, setSelectedIrId] = useState<string | null>(null);
  const [fileTableSorting, setFileTableSorting] = useState<SortingState>([{ id: 'relpath', desc: false }]);
  const [fileTableColumnFilters, setFileTableColumnFilters] = useState<ColumnFiltersState>([]);
  const [fileTablePagination, setFileTablePagination] = useState({ pageIndex: 0, pageSize: 20 });

  useEffect(() => {
    // Load available parsers
    apiService.getParsers()
      .then(setParsers)
      .catch((err) => {
        console.error('Failed to load parsers:', err);
        setError('Failed to load available parsers');
      })
      .finally(() => setLoadingParsers(false));
  }, []);

  // Pre-fill from profile
  useEffect(() => {
    if (profile) {
      setSelectedParser(profile.parse.parser_language);
      setOutputDir(profile.output_path);
    }
  }, [profile]);

  // Auto-fill dataset_info_path and output_dir if scan result is available
  // This should run after profile is set, so scanResult takes precedence for datasetInfoPath
  useEffect(() => {
    if (scanResult) {
      // Always set dataset_info_path from scan result (profile doesn't have this)
      const path = (scanResult.parameters as any).dataset_info_path || 
                   `${scanResult.dataset_root}/dataset_info.json`;
      setDatasetInfoPath(path);
      
      // Only set output_dir from scan result if profile is not loaded
      // (profile output_path takes precedence)
      if (!profile && scanResult.parameters.out) {
        setOutputDir(scanResult.parameters.out);
      }
    }
  }, [scanResult, profile]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (!profile) {
        throw new Error('Load a benchmark profile to run the parse step.');
      }
      const response = await apiService.parse({
        profile,
      });
      setResult(response);
      onParseComplete(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to parse dataset');
    } finally {
      setLoading(false);
    }
  };

  // Process diagnostics data for visualizations
  const diagnosticsData = useMemo(() => {
    if (!result) return null;

    const diagnostics = Object.values(result.modelParseDiagnostics);
    
    // Status distribution
    const statusCounts = {
      success: diagnostics.filter(d => d.parse_status === 'success').length,
      warning: diagnostics.filter(d => d.parse_status === 'warning').length,
      failure: diagnostics.filter(d => d.parse_status === 'failure').length,
    };

    // Warning types aggregation
    const warningTypes: Record<string, number> = {};
    diagnostics.forEach(d => {
      Object.entries(d.warnings_by_type).forEach(([type, count]) => {
        warningTypes[type] = (warningTypes[type] || 0) + count;
      });
    });

    // Parse time statistics
    const parseTimes = diagnostics.map(d => d.parse_time_ms).filter(t => t > 0);
    const avgParseTime = parseTimes.length > 0 
      ? parseTimes.reduce((a, b) => a + b, 0) / parseTimes.length 
      : 0;
    const maxParseTime = parseTimes.length > 0 ? Math.max(...parseTimes) : 0;

    // Elements statistics
    const totalElementsLoaded = diagnostics.reduce((sum, d) => sum + d.elements_loaded, 0);
    const totalElementsSkipped = diagnostics.reduce((sum, d) => sum + d.elements_skipped, 0);
    const avgElementsPerModel = diagnostics.length > 0 
      ? totalElementsLoaded / diagnostics.length 
      : 0;

    // File size statistics
    const sourceSizes = diagnostics.map(d => d.file_size_bytes_source).filter(s => s > 0);
    const irSizes = diagnostics.map(d => d.file_size_bytes_ir).filter(s => s > 0);
    const totalSourceSize = sourceSizes.reduce((sum, s) => sum + s, 0);
    const totalIrSize = irSizes.reduce((sum, s) => sum + s, 0);
    const avgCompressionRatio = totalSourceSize > 0 
      ? ((totalSourceSize - totalIrSize) / totalSourceSize) * 100 
      : 0;
    const irToSourceRatio = totalSourceSize > 0 ? totalIrSize / totalSourceSize : 0;
    const irLargerThanSource = totalSourceSize > 0 ? totalIrSize > totalSourceSize : false;

    return {
      diagnostics,
      statusCounts,
      warningTypes,
      avgParseTime,
      maxParseTime,
      totalElementsLoaded,
      totalElementsSkipped,
      avgElementsPerModel,
      totalSourceSize,
      totalIrSize,
      avgCompressionRatio,
      irToSourceRatio,
      irLargerThanSource,
    };
  }, [result]);

  // Create file list from diagnostics
  const parsedFiles = useMemo(() => {
    if (!result) return [];
    
    return Object.values(result.modelParseDiagnostics)
      .map(diag => ({
        relpath: diag.relpath,
        status: diag.parse_status,
        irId: result.index[diag.file_id] ? diag.file_id : null,
        diagnostics: diag,
      }))
      .sort((a, b) => a.relpath.localeCompare(b.relpath));
  }, [result]);

  type ParsedFileRow = (typeof parsedFiles)[number];

  const fileTableColumns = useMemo<ColumnDef<ParsedFileRow>[]>(() => {
    const sortableHeader = (label: string) => ({ column }: { column: any }) => (
      <Button
        type="button"
        variant="ghost"
        size="sm"
        className="-ml-3 h-8"
        onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
      >
        <span>{label}</span>
        {column.getIsSorted() === 'desc' ? (
          <ChevronDown className="ml-2 h-4 w-4" />
        ) : column.getIsSorted() === 'asc' ? (
          <ChevronRight className="ml-2 h-4 w-4 rotate-90" />
        ) : (
          <ChevronRight className="ml-2 h-4 w-4 opacity-50" />
        )}
      </Button>
    );

    return [
      {
        accessorKey: 'relpath',
        header: sortableHeader('File'),
        cell: ({ row }) => (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <code className="text-xs font-mono truncate block max-w-[420px]">
                  {truncatePath(row.original.relpath, 80)}
                </code>
              </TooltipTrigger>
              <TooltipContent>
                <p className="font-mono text-xs">{row.original.relpath}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        ),
      },
      {
        accessorKey: 'status',
        header: sortableHeader('Status'),
        filterFn: (row, id, value) => {
          if (!value || value === 'all') return true;
          return row.getValue(id) === value;
        },
        cell: ({ row }) => (
          <Badge variant={getStatusBadgeVariant(row.original.status)}>
            {row.original.status}
          </Badge>
        ),
      },
      {
        id: 'elements_loaded',
        accessorFn: (row) => row.diagnostics.elements_loaded,
        header: sortableHeader('Elements'),
        cell: ({ row }) => (
          <span className="text-sm">
            {row.original.diagnostics.elements_loaded}
            {row.original.diagnostics.elements_skipped > 0 && (
              <span className="text-muted-foreground"> / {row.original.diagnostics.elements_skipped} skipped</span>
            )}
          </span>
        ),
      },
      {
        id: 'parse_time_ms',
        accessorFn: (row) => row.diagnostics.parse_time_ms,
        header: sortableHeader('Time'),
        cell: ({ row }) => (
          <span className="text-sm">{formatTime(row.original.diagnostics.parse_time_ms)}</span>
        ),
      },
      {
        id: 'warning_count',
        accessorFn: (row) => row.diagnostics.warning_count,
        header: sortableHeader('Warnings'),
        cell: ({ row }) => (
          <span className="text-sm">{row.original.diagnostics.warning_count}</span>
        ),
      },
      {
        id: 'actions',
        header: () => <div className="text-right">Actions</div>,
        enableSorting: false,
        cell: ({ row }) => (
          <div className="flex justify-end gap-2">
            {row.original.status !== 'failure' && row.original.irId && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedIrId(row.original.irId!)}
              >
                <Eye className="h-4 w-4 mr-1" />
                View
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedDiagnostics(row.original.diagnostics)}
            >
              <Info className="h-4 w-4 mr-1" />
              Details
            </Button>
          </div>
        ),
      },
    ];
  }, []);

  const fileTable = useReactTable({
    data: parsedFiles,
    columns: fileTableColumns,
    state: {
      sorting: fileTableSorting,
      columnFilters: fileTableColumnFilters,
      pagination: fileTablePagination,
    },
    onSortingChange: setFileTableSorting,
    onColumnFiltersChange: setFileTableColumnFilters,
    onPaginationChange: setFileTablePagination,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Step 2: Parse Models</CardTitle>
        <CardDescription>
          Parse models from dataset_info.json and produce IR files
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="parser-language">Parser Language *</Label>
            {loadingParsers ? (
              <p className="text-sm text-muted-foreground">Loading parsers...</p>
            ) : (
              <select
                id="parser-language"
                value={selectedParser}
                onChange={(e) => setSelectedParser(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                required
                disabled={loading || result !== null || !!profile}
              >
                <option value="">Select a parser...</option>
                {parsers.map((parser) => (
                  <option key={parser} value={parser}>
                    {parser}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="dataset-info-path">Dataset Info Path *</Label>
            <Input
              id="dataset-info-path"
              type="text"
              value={datasetInfoPath}
              onChange={(e) => setDatasetInfoPath(e.target.value)}
              placeholder="/path/to/dataset_info.json"
              required
              disabled={loading || result !== null || !!profile}
            />
            <p className="text-sm text-muted-foreground">
              Path to dataset_info.json from scan stage
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="output-dir">Output Directory *</Label>
            <Input
              id="output-dir"
              type="text"
              value={outputDir}
              onChange={(e) => setOutputDir(e.target.value)}
              placeholder="/path/to/output"
              required
              disabled={loading || result !== null || !!profile}
            />
            <p className="text-sm text-muted-foreground">
              Directory where IR files and reports will be saved
            </p>
          </div>

          {error && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
              {error}
            </div>
          )}

          <Button type="submit" disabled={loading || !profile || result !== null}>
            {loading ? 'Parsing...' : 'Parse Models'}
          </Button>
        </form>

        {result && diagnosticsData && (
          <div className="mt-6 space-y-4">
            {/* Summary Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Total Candidates</p>
                      <p className="text-2xl font-bold">{result.totals.candidates_in}</p>
                    </div>
                    <FileText className="h-8 w-8 text-muted-foreground" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Success</p>
                      <p className="text-2xl font-bold text-green-600">{result.totals.parsed_success}</p>
                    </div>
                    <CheckCircle className="h-8 w-8 text-green-600" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Warning</p>
                      <p className="text-2xl font-bold text-yellow-600">{result.totals.parsed_warning}</p>
                    </div>
                    <AlertTriangle className="h-8 w-8 text-yellow-600" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Failure</p>
                      <p className="text-2xl font-bold text-red-600">{result.totals.parsed_failure}</p>
                    </div>
                    <XCircle className="h-8 w-8 text-red-600" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Status Distribution Visualization */}
            <Card>
              <CardHeader>
                <CardTitle>Parse Status Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4">
                  {Object.entries(diagnosticsData.statusCounts).map(([status, count]) => {
                    const total = result.totals.candidates_in;
                    const percentage = total > 0 ? (count / total) * 100 : 0;
                    return (
                      <div key={status} className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            {getStatusIcon(status)}
                            <span className="text-sm font-medium capitalize">{status}</span>
                          </div>
                          <span className="text-sm text-muted-foreground">{count} ({percentage.toFixed(1)}%)</span>
                        </div>
                        <div className="w-full bg-muted rounded-full h-4 overflow-hidden">
                          <div
                            className={`h-full transition-all ${
                              status === 'success' ? 'bg-green-600' :
                              status === 'warning' ? 'bg-yellow-600' :
                              'bg-red-600'
                            }`}
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Diagnostics Visualizations */}
            <Tabs defaultValue="overview" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="performance">Performance</TabsTrigger>
                <TabsTrigger value="warnings">Warnings</TabsTrigger>
                <TabsTrigger value="details">Details</TabsTrigger>
              </TabsList>

              <TabsContent value="overview" className="space-y-4 mt-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Elements Statistics */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">Elements Statistics</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div>
                        <div className="flex justify-between mb-2">
                          <span className="text-sm text-muted-foreground">Total Loaded</span>
                          <span className="text-sm font-semibold">{diagnosticsData.totalElementsLoaded.toLocaleString()}</span>
                        </div>
                        <div className="w-full bg-muted rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${diagnosticsData.totalElementsLoaded + diagnosticsData.totalElementsSkipped > 0 ? (diagnosticsData.totalElementsLoaded / (diagnosticsData.totalElementsLoaded + diagnosticsData.totalElementsSkipped)) * 100 : 0}%` }}
                          />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between mb-2">
                          <span className="text-sm text-muted-foreground">Total Skipped</span>
                          <span className="text-sm font-semibold">{diagnosticsData.totalElementsSkipped.toLocaleString()}</span>
                        </div>
                        <div className="w-full bg-muted rounded-full h-2">
                          <div
                            className="bg-orange-600 h-2 rounded-full"
                            style={{ width: `${diagnosticsData.totalElementsLoaded + diagnosticsData.totalElementsSkipped > 0 ? (diagnosticsData.totalElementsSkipped / (diagnosticsData.totalElementsLoaded + diagnosticsData.totalElementsSkipped)) * 100 : 0}%` }}
                          />
                        </div>
                      </div>
                      <div className="pt-2 border-t">
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">Avg per Model</span>
                          <span className="text-sm font-semibold">{diagnosticsData.avgElementsPerModel.toFixed(1)}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* File Size Statistics */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">File Size Statistics</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div>
                        <div className="flex justify-between mb-2">
                          <span className="text-sm text-muted-foreground">Total Source Size</span>
                          <span className="text-sm font-semibold">{formatBytes(diagnosticsData.totalSourceSize)}</span>
                        </div>
                        <div className="w-full bg-muted rounded-full h-2">
                          <div
                            className="bg-purple-600 h-2 rounded-full"
                            style={{ width: '100%' }}
                          />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between mb-2">
                          <span className="text-sm text-muted-foreground">Total IR Size</span>
                          <span className="text-sm font-semibold">{formatBytes(diagnosticsData.totalIrSize)}</span>
                        </div>
                        <div className="w-full bg-muted rounded-full h-2">
                          <div
                            className={diagnosticsData.irLargerThanSource ? 'bg-red-600 h-2 rounded-full' : 'bg-indigo-600 h-2 rounded-full'}
                            style={{ width: `${Math.min(100, diagnosticsData.totalSourceSize > 0 ? (diagnosticsData.totalIrSize / diagnosticsData.totalSourceSize) * 100 : 0)}%` }}
                          />
                        </div>
                        {diagnosticsData.totalSourceSize > 0 && (
                          <p className="mt-1 text-xs text-muted-foreground">
                            IR is {(diagnosticsData.irToSourceRatio * 100).toFixed(1)}% of source
                            {diagnosticsData.irLargerThanSource ? ' (larger than source)' : ''}
                          </p>
                        )}
                      </div>
                      <div className="pt-2 border-t">
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">Compression Ratio</span>
                          <span className="text-sm font-semibold">{diagnosticsData.avgCompressionRatio.toFixed(1)}%</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              <TabsContent value="performance" className="space-y-4 mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Parse Performance</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-muted-foreground mb-1">Average Parse Time</p>
                        <p className="text-2xl font-bold flex items-center gap-2">
                          <Clock className="h-5 w-5" />
                          {formatTime(diagnosticsData.avgParseTime)}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground mb-1">Max Parse Time</p>
                        <p className="text-2xl font-bold flex items-center gap-2">
                          <Zap className="h-5 w-5" />
                          {formatTime(diagnosticsData.maxParseTime)}
                        </p>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <p className="text-sm font-medium">Parse Time Distribution</p>
                      <div className="space-y-2">
                        {diagnosticsData.diagnostics
                          .filter(d => d.parse_time_ms > 0)
                          .sort((a, b) => b.parse_time_ms - a.parse_time_ms)
                          .slice(0, 10)
                          .map((d, idx) => {
                            const maxTime = diagnosticsData.maxParseTime || 1;
                            const percentage = (d.parse_time_ms / maxTime) * 100;
                            return (
                              <div key={idx}>
                                <div className="flex justify-between mb-1">
                                  <span className="text-xs font-mono truncate max-w-[200px]">{d.relpath}</span>
                                  <span className="text-xs text-muted-foreground">{formatTime(d.parse_time_ms)}</span>
                                </div>
                                <div className="w-full bg-muted rounded-full h-2">
                                  <div
                                    className="bg-blue-600 h-2 rounded-full"
                                    style={{ width: `${percentage}%` }}
                                  />
                                </div>
                              </div>
                            );
                          })}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="warnings" className="space-y-4 mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Warning Types</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {Object.keys(diagnosticsData.warningTypes).length === 0 ? (
                      <p className="text-sm text-muted-foreground text-center py-4">No warnings found</p>
                    ) : (
                      <div className="space-y-3">
                        {Object.entries(diagnosticsData.warningTypes)
                          .sort(([, a], [, b]) => b - a)
                          .map(([type, count]) => {
                            const totalWarnings = Object.values(diagnosticsData.warningTypes).reduce((sum, c) => sum + c, 0);
                            const percentage = (count / totalWarnings) * 100;
                            return (
                              <div key={type}>
                                <div className="flex justify-between mb-1">
                                  <span className="text-sm font-medium">{type.replace(/_/g, ' ')}</span>
                                  <span className="text-sm text-muted-foreground">{count} ({percentage.toFixed(1)}%)</span>
                                </div>
                                <div className="w-full bg-muted rounded-full h-2">
                                  <div
                                    className="bg-yellow-600 h-2 rounded-full"
                                    style={{ width: `${percentage}%` }}
                                  />
                                </div>
                              </div>
                            );
                          })}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="details" className="space-y-4 mt-4">
                <Collapsible open={detailsOpen} onOpenChange={setDetailsOpen}>
                  <CollapsibleTrigger asChild>
                    <Button variant="outline" className="w-full justify-between">
                      <span>File Details</span>
                      {detailsOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                    </Button>
                  </CollapsibleTrigger>
                  <CollapsibleContent className="mt-4">
                    <div className="space-y-3">
                      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                        <div className="flex flex-1 items-center gap-2">
                          <Input
                            placeholder="Filter by file path..."
                            value={(fileTable.getColumn('relpath')?.getFilterValue() as string) ?? ''}
                            onChange={(e) => fileTable.getColumn('relpath')?.setFilterValue(e.target.value)}
                            className="max-w-md"
                          />
                          <select
                            value={(fileTable.getColumn('status')?.getFilterValue() as string) ?? 'all'}
                            onChange={(e) => fileTable.getColumn('status')?.setFilterValue(e.target.value)}
                            className="flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                          >
                            <option value="all">All statuses</option>
                            <option value="success">success</option>
                            <option value="warning">warning</option>
                            <option value="failure">failure</option>
                          </select>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-muted-foreground">Rows</span>
                          <select
                            value={String(fileTable.getState().pagination.pageSize)}
                            onChange={(e) => fileTable.setPageSize(Number(e.target.value))}
                            className="flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                          >
                            {[10, 20, 50, 100].map((s) => (
                              <option key={s} value={String(s)}>{s}</option>
                            ))}
                          </select>
                        </div>
                      </div>

                      <div className="overflow-hidden rounded-md border">
                        <Table>
                          <TableHeader>
                            {fileTable.getHeaderGroups().map((headerGroup) => (
                              <TableRow key={headerGroup.id}>
                                {headerGroup.headers.map((header) => (
                                  <TableHead key={header.id} className={header.column.id === 'actions' ? 'text-right' : undefined}>
                                    {header.isPlaceholder
                                      ? null
                                      : flexRender(header.column.columnDef.header, header.getContext())}
                                  </TableHead>
                                ))}
                              </TableRow>
                            ))}
                          </TableHeader>
                          <TableBody>
                            {fileTable.getRowModel().rows?.length ? (
                              fileTable.getRowModel().rows.map((row) => (
                                <TableRow key={row.id}>
                                  {row.getVisibleCells().map((cell) => (
                                    <TableCell key={cell.id} className={cell.column.id === 'actions' ? 'text-right' : undefined}>
                                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                    </TableCell>
                                  ))}
                                </TableRow>
                              ))
                            ) : (
                              <TableRow>
                                <TableCell colSpan={fileTableColumns.length} className="h-24 text-center text-muted-foreground">
                                  No results.
                                </TableCell>
                              </TableRow>
                            )}
                          </TableBody>
                        </Table>
                      </div>

                      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                        <p className="text-sm text-muted-foreground">
                          Showing {fileTable.getRowModel().rows.length} of {fileTable.getFilteredRowModel().rows.length} filtered row(s)
                        </p>
                        <div className="flex items-center gap-2">
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => fileTable.setPageIndex(0)}
                            disabled={!fileTable.getCanPreviousPage()}
                          >
                            First
                          </Button>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => fileTable.previousPage()}
                            disabled={!fileTable.getCanPreviousPage()}
                          >
                            Prev
                          </Button>
                          <span className="text-sm text-muted-foreground px-2">
                            Page {fileTable.getState().pagination.pageIndex + 1} of {fileTable.getPageCount()}
                          </span>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => fileTable.nextPage()}
                            disabled={!fileTable.getCanNextPage()}
                          >
                            Next
                          </Button>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => fileTable.setPageIndex(fileTable.getPageCount() - 1)}
                            disabled={!fileTable.getCanNextPage()}
                          >
                            Last
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CollapsibleContent>
                </Collapsible>
              </TabsContent>
            </Tabs>
          </div>
        )}

        {selectedDiagnostics && (
          <Dialog open={!!selectedDiagnostics} onOpenChange={(open) => !open && setSelectedDiagnostics(null)}>
            <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Parse Diagnostics</DialogTitle>
                <DialogDescription>
                  Detailed information for: <code className="text-xs">{selectedDiagnostics.relpath}</code>
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium mb-1">Status</p>
                    <Badge variant={getStatusBadgeVariant(selectedDiagnostics.parse_status)}>
                      {selectedDiagnostics.parse_status}
                    </Badge>
                  </div>
                  <div>
                    <p className="text-sm font-medium mb-1">File ID</p>
                    <p className="text-sm text-muted-foreground font-mono">{selectedDiagnostics.file_id}</p>
                  </div>
                </div>

                {selectedDiagnostics.parse_error_msg && (
                  <div>
                    <p className="text-sm font-medium mb-1">Error Message</p>
                    <p className="text-sm text-muted-foreground bg-destructive/10 p-2 rounded">{selectedDiagnostics.parse_error_msg}</p>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium mb-1">Elements Loaded</p>
                    <p className="text-sm text-muted-foreground">{selectedDiagnostics.elements_loaded}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium mb-1">Elements Skipped</p>
                    <p className="text-sm text-muted-foreground">{selectedDiagnostics.elements_skipped}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium mb-1">Skip Ratio</p>
                    <p className="text-sm text-muted-foreground">{(selectedDiagnostics.skip_ratio * 100).toFixed(2)}%</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium mb-1">Parse Time</p>
                    <p className="text-sm text-muted-foreground">{formatTime(selectedDiagnostics.parse_time_ms)}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium mb-1">Source File Size</p>
                    <p className="text-sm text-muted-foreground">{formatBytes(selectedDiagnostics.file_size_bytes_source)}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium mb-1">IR File Size</p>
                    <p className="text-sm text-muted-foreground">{formatBytes(selectedDiagnostics.file_size_bytes_ir)}</p>
                  </div>
                </div>

                <div>
                  <p className="text-sm font-medium mb-1">Warning Count</p>
                  <p className="text-sm text-muted-foreground">{selectedDiagnostics.warning_count}</p>
                  {selectedDiagnostics.warning_count > 0 && (
                    <div className="mt-2 space-y-2">
                      <p className="text-sm font-medium">Warnings by Type:</p>
                      {Object.entries(selectedDiagnostics.warnings_by_type).map(([type, count]) => (
                        <div key={type} className="flex justify-between text-sm">
                          <span className="text-muted-foreground">{type.replace(/_/g, ' ')}</span>
                          <span>{count}</span>
                        </div>
                      ))}
                      {Object.keys(selectedDiagnostics.warning_msgs).length > 0 && (
                        <div className="mt-2">
                          <p className="text-sm font-medium mb-1">Warning Messages:</p>
                          {Object.entries(selectedDiagnostics.warning_msgs).map(([type, messages]) => (
                            <div key={type} className="mb-2">
                              <p className="text-xs font-medium text-muted-foreground">{type.replace(/_/g, ' ')}:</p>
                              <ul className="list-disc list-inside text-xs text-muted-foreground ml-2">
                                {messages.slice(0, 5).map((msg, idx) => (
                                  <li key={idx}>{msg}</li>
                                ))}
                                {messages.length > 5 && <li>... and {messages.length - 5} more</li>}
                              </ul>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </DialogContent>
          </Dialog>
        )}

        {selectedIrId && (
          <IRVisualization
            irId={selectedIrId}
            outputDir={outputDir}
            open={!!selectedIrId}
            onOpenChange={(open) => !open && setSelectedIrId(null)}
          />
        )}
      </CardContent>
    </Card>
  );
}
