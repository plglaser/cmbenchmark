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
import { ChevronDown, ChevronRight, Eye, Info } from 'lucide-react';
import { apiService } from '../services/api';
import type { ParseResponse, ParseFailureResponse, ScanResponse } from '../types/api';
import { IRVisualization } from './IRVisualization';

interface ParseStepProps {
  scanResult: ScanResponse | null;
  onParseComplete: (result: ParseResponse) => void;
}

export function ParseStep({ scanResult, onParseComplete }: ParseStepProps) {
  const [parsers, setParsers] = useState<string[]>([]);
  const [selectedParser, setSelectedParser] = useState('');
  const [datasetInfoPath, setDatasetInfoPath] = useState('');
  const [outputDir, setOutputDir] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingParsers, setLoadingParsers] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ParseResponse | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [selectedFailure, setSelectedFailure] = useState<ParseFailureResponse | null>(null);
  const [selectedIrId, setSelectedIrId] = useState<string | null>(null);

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

  // Auto-fill dataset_info_path and output_dir if scan result is available
  useEffect(() => {
    if (scanResult) {
      // Use the dataset_info_path from scan result if available, otherwise construct it
      if (!datasetInfoPath) {
        const path = (scanResult.parameters as any).dataset_info_path || 
                     `${scanResult.dataset_root}/dataset_info.json`;
        setDatasetInfoPath(path);
      }
      // Use the same output directory from scan result
      if (!outputDir && scanResult.parameters.out) {
        setOutputDir(scanResult.parameters.out);
      }
    }
  }, [scanResult, datasetInfoPath, outputDir]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await apiService.parse({
        dataset_info_path: datasetInfoPath,
        output_dir: outputDir,
        parser_language: selectedParser,
      });
      setResult(response);
      onParseComplete(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to parse dataset');
    } finally {
      setLoading(false);
    }
  };

  // Combine successful parses and failures into a single list for the table
  const parsedFiles = useMemo(() => {
    if (!result) return [];
    
    const files: Array<{
      relpath: string;
      status: 'ok' | 'failed';
      irId: string | null;
      failure?: ParseFailureResponse;
      warningsLoss: number;
    }> = [];

    // Add successful parses (from index: ir_id -> relpath)
    Object.entries(result.index).forEach(([irId, relpath]) => {
      files.push({
        relpath,
        status: 'ok',
        irId,
        warningsLoss: 0, // TODO: Get per-file loss data from API if available
      });
    });

    // Add failures
    result.failures.forEach((failure) => {
      files.push({
        relpath: failure.relpath,
        status: 'failed',
        irId: failure.ir_id,
        failure,
        warningsLoss: 0,
      });
    });

    // Sort by relpath for consistent display
    return files.sort((a, b) => a.relpath.localeCompare(b.relpath));
  }, [result]);

  const truncatePath = (path: string, maxLength: number = 50) => {
    if (path.length <= maxLength) return path;
    return path.substring(0, maxLength - 3) + '...';
  };

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
                disabled={loading || result !== null}
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
              disabled={loading || result !== null}
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
              disabled={loading || result !== null}
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

          <Button
            type="submit"
            disabled={loading || !selectedParser || !datasetInfoPath || !outputDir || result !== null}
          >
            {loading ? 'Parsing...' : 'Parse Models'}
          </Button>
        </form>

        {result && (
          <div className="mt-6 space-y-4">
            <div className="p-4 bg-muted rounded-md">
              <h3 className="font-semibold mb-2">Parse Results</h3>
              <div className="space-y-1 text-sm">
                <p><strong>Dataset Root:</strong> {result.dataset_root}</p>
                <p><strong>Parsed At:</strong> {new Date(result.parsed_at).toLocaleString()}</p>
                <p><strong>Parser:</strong> {result.parameters.parser_language}</p>
                <p><strong>Candidates In:</strong> {result.totals.candidates_in}</p>
                <p><strong>Parsed OK:</strong> {result.totals.parsed_ok}</p>
                <p><strong>Failed Parse:</strong> {result.totals.failed_parse}</p>
              </div>
            </div>

            {result.loss_summary.total_models > 0 && (
              <div className="p-4 bg-muted rounded-md">
                <h3 className="font-semibold mb-2">Loss Summary</h3>
                <div className="space-y-1 text-sm">
                  <p><strong>Total Models:</strong> {result.loss_summary.total_models}</p>
                  {Object.keys(result.loss_summary.category_totals).length > 0 && (
                    <div>
                      <p className="font-medium">Category Totals:</p>
                      <ul className="list-disc list-inside ml-2">
                        {Object.entries(result.loss_summary.category_totals).map(([category, count]) => (
                          <li key={category}>{category}: {count}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}

            {result.failures.length > 0 && (
              <div className="p-4 bg-destructive/10 rounded-md">
                <h3 className="font-semibold mb-2 text-destructive">Parse Failures ({result.failures.length})</h3>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {result.failures.slice(0, 10).map((failure, idx) => (
                    <div key={idx} className="text-sm">
                      <p><strong>{failure.relpath}</strong></p>
                      <p className="text-muted-foreground">{failure.error_class}: {failure.message}</p>
                    </div>
                  ))}
                  {result.failures.length > 10 && (
                    <p className="text-sm text-muted-foreground">
                      ... and {result.failures.length - 10} more failures
                    </p>
                  )}
                </div>
              </div>
            )}

            <Collapsible open={detailsOpen} onOpenChange={setDetailsOpen}>
              <CollapsibleTrigger asChild>
                <Button variant="outline" className="w-full justify-between">
                  <span>Details</span>
                  {detailsOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-4">
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-[40%]">File</TableHead>
                        <TableHead className="w-[15%]">Status</TableHead>
                        <TableHead className="w-[15%]">Warnings/Loss</TableHead>
                        <TableHead className="w-[30%] text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {parsedFiles.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={4} className="text-center text-muted-foreground">
                            No files parsed
                          </TableCell>
                        </TableRow>
                      ) : (
                        parsedFiles.map((file, idx) => (
                          <TableRow key={`${file.relpath}-${idx}`}>
                            <TableCell>
                              <TooltipProvider>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <code className="text-xs font-mono truncate block max-w-[300px]">
                                      {truncatePath(file.relpath)}
                                    </code>
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    <p className="font-mono text-xs">{file.relpath}</p>
                                  </TooltipContent>
                                </Tooltip>
                              </TooltipProvider>
                            </TableCell>
                            <TableCell>
                              <Badge
                                variant={file.status === 'ok' ? 'success' : 'destructive'}
                              >
                                {file.status === 'ok' ? 'OK' : 'Failed'}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <span className="text-sm">{file.warningsLoss}</span>
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex justify-end gap-2">
                                {file.status === 'ok' && file.irId && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setSelectedIrId(file.irId!)}
                                  >
                                    <Eye className="h-4 w-4 mr-1" />
                                    View
                                  </Button>
                                )}
                                {file.status === 'failed' && file.failure && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setSelectedFailure(file.failure!)}
                                  >
                                    <Info className="h-4 w-4 mr-1" />
                                    Details
                                  </Button>
                                )}
                              </div>
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </div>
              </CollapsibleContent>
            </Collapsible>
          </div>
        )}

        {selectedFailure && (
          <Dialog open={!!selectedFailure} onOpenChange={(open) => !open && setSelectedFailure(null)}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Parse Error Details</DialogTitle>
                <DialogDescription>
                  Error information for: <code className="text-xs">{selectedFailure.relpath}</code>
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div>
                  <p className="text-sm font-medium mb-1">Error Class</p>
                  <p className="text-sm text-muted-foreground font-mono">{selectedFailure.error_class}</p>
                </div>
                <div>
                  <p className="text-sm font-medium mb-1">Message</p>
                  <p className="text-sm text-muted-foreground">{selectedFailure.message}</p>
                </div>
                <div>
                  <p className="text-sm font-medium mb-1">Stage</p>
                  <p className="text-sm text-muted-foreground">{selectedFailure.stage}</p>
                </div>
                {selectedFailure.ir_id && (
                  <div>
                    <p className="text-sm font-medium mb-1">IR ID</p>
                    <p className="text-sm text-muted-foreground font-mono">{selectedFailure.ir_id}</p>
                  </div>
                )}
                <div>
                  <p className="text-sm font-medium mb-1">Parser</p>
                  <p className="text-sm text-muted-foreground">{selectedFailure.parser}</p>
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
