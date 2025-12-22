import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { apiService } from '../services/api';
import type { ParseResponse, ScanResponse } from '../types/api';

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

  // Auto-fill dataset_info_path if scan result is available
  useEffect(() => {
    if (scanResult && !datasetInfoPath) {
      // Use the dataset_info_path from scan result if available, otherwise construct it
      const path = (scanResult.parameters as any).dataset_info_path || 
                   `${scanResult.dataset_root}/dataset_info.json`;
      setDatasetInfoPath(path);
    }
  }, [scanResult, datasetInfoPath]);

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
                disabled={loading}
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
              disabled={loading}
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
              disabled={loading}
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
            disabled={loading || !selectedParser || !datasetInfoPath || !outputDir}
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
          </div>
        )}
      </CardContent>
    </Card>
  );
}

