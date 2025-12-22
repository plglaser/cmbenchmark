import { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { apiService } from '../services/api';
import type { ScanResponse } from '../types/api';

interface ScanStepProps {
  onScanComplete: (result: ScanResponse) => void;
}

export function ScanStep({ onScanComplete }: ScanStepProps) {
  const [datasetPath, setDatasetPath] = useState('');
  const [exclude, setExclude] = useState('');
  const [sizeLimitMb, setSizeLimitMb] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScanResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await apiService.scan({
        dataset_path: datasetPath,
        exclude: exclude || null,
        size_limit_mb: sizeLimitMb || null,
      });
      setResult(response);
      onScanComplete(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to scan dataset');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Step 1: Scan Dataset</CardTitle>
        <CardDescription>
          Scan a dataset directory for model files and generate statistics
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="dataset-path">Dataset Path *</Label>
            <Input
              id="dataset-path"
              type="text"
              value={datasetPath}
              onChange={(e) => setDatasetPath(e.target.value)}
              placeholder="/path/to/dataset"
              required
              disabled={loading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="exclude">Exclude Patterns (optional)</Label>
            <Input
              id="exclude"
              type="text"
              value={exclude}
              onChange={(e) => setExclude(e.target.value)}
              placeholder="*.xml,*.tmp"
              disabled={loading}
            />
            <p className="text-sm text-muted-foreground">
              Comma-separated list of file patterns to exclude
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="size-limit">Size Limit MB (optional)</Label>
            <Input
              id="size-limit"
              type="number"
              value={sizeLimitMb || ''}
              onChange={(e) => setSizeLimitMb(e.target.value ? parseInt(e.target.value) : null)}
              placeholder="100"
              min="1"
              disabled={loading}
            />
            <p className="text-sm text-muted-foreground">
              Maximum file size in MB (files exceeding this will be marked as too_large)
            </p>
          </div>

          {error && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
              {error}
            </div>
          )}

          <Button type="submit" disabled={loading || !datasetPath}>
            {loading ? 'Scanning...' : 'Scan Dataset'}
          </Button>
        </form>

        {result && (
          <div className="mt-6 space-y-4">
            <div className="p-4 bg-muted rounded-md">
              <h3 className="font-semibold mb-2">Scan Results</h3>
              <div className="space-y-1 text-sm">
                <p><strong>Dataset Root:</strong> {result.dataset_root}</p>
                <p><strong>Scanned At:</strong> {new Date(result.scanned_at).toLocaleString()}</p>
                <p><strong>Total Files Seen:</strong> {result.totals.total_seen}</p>
                <p><strong>Candidates:</strong> {result.totals.candidates}</p>
                <p><strong>Unreadable:</strong> {result.totals.unreadable}</p>
                <p><strong>Too Large:</strong> {result.totals.too_large}</p>
              </div>
            </div>

            {Object.keys(result.extensions).length > 0 && (
              <div className="p-4 bg-muted rounded-md">
                <h3 className="font-semibold mb-2">File Extensions</h3>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(result.extensions).map(([ext, count]) => (
                    <span key={ext} className="px-2 py-1 bg-background rounded text-sm">
                      {ext}: {count}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

