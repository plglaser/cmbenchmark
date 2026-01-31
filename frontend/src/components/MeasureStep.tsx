import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Loader2, CheckCircle2, FileJson } from 'lucide-react';
import { apiService } from '../services/api';
import type { ParseResponse, MeasureResponse } from '../types/api';

interface MeasureStepProps {
  parseResult: ParseResponse | null;
  onMeasureComplete: (result: MeasureResponse) => void;
}

export function MeasureStep({ parseResult, onMeasureComplete }: MeasureStepProps) {
  const [irDir, setIrDir] = useState('');
  const [outputDir, setOutputDir] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MeasureResponse | null>(null);

  // Auto-fill IR directory and output directory if parse result is available
  useEffect(() => {
    if (parseResult && parseResult.parameters.output_dir) {
      const outputPath = parseResult.parameters.output_dir;
      // IR directory is typically in output_dir/ir
      if (!irDir) {
        setIrDir(`${outputPath}/ir`);
      }
      // Use the same output directory from parse result
      if (!outputDir) {
        setOutputDir(outputPath);
      }
    }
  }, [parseResult]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await apiService.measure({
        ir_dir: irDir,
        output_dir: outputDir,
      });
      setResult(response);
      onMeasureComplete(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to compute measures');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Step 3: Compute Measures</CardTitle>
        <CardDescription>
          Compute dataset-level and per-model measures from the IR models.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="ir-dir">IR Directory *</Label>
            <Input
              id="ir-dir"
              type="text"
              className="font-mono"
              value={irDir}
              onChange={(e) => setIrDir(e.target.value)}
              placeholder="/path/to/output/ir"
              required
              disabled={loading || result !== null}
            />
            <p className="text-sm text-muted-foreground">
              Directory containing IR JSON files (pre-filled from previous step)
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="output-dir-measure">Output Directory *</Label>
            <Input
              id="output-dir-measure"
              type="text"
              value={outputDir}
              onChange={(e) => setOutputDir(e.target.value)}
              placeholder="/path/to/output"
              required
              className="font-mono"
              disabled={loading || result !== null}
            />
            <p className="text-sm text-muted-foreground">
              Directory where <code className="font-mono">measures.json</code> and{' '}
              <code className="font-mono">measures_per_model.json</code> will be saved (pre-filled)
            </p>
          </div>

          {error && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
              {error}
            </div>
          )}

          <Button type="submit" disabled={loading || !irDir || !outputDir || result !== null}>
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Computing measures...
              </>
            ) : (
              'Compute Measures'
            )}
          </Button>
        </form>

        {result && (
          <div className="mt-6 space-y-4">
            <div className="p-4 bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-900 rounded-md">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-semibold text-green-900 dark:text-green-100 mb-2">
                    Measures computed successfully.
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2 text-green-800 dark:text-green-200">
                      <CheckCircle2 className="h-4 w-4" />
                      <FileJson className="h-4 w-4" />
                      <code className="font-mono">{result.measures_path}</code>
                      <span className="text-muted-foreground">(dataset-level)</span>
                    </div>
                    <div className="flex items-center gap-2 text-green-800 dark:text-green-200">
                      <CheckCircle2 className="h-4 w-4" />
                      <FileJson className="h-4 w-4" />
                      <code className="font-mono">{result.measures_per_model_path}</code>
                      <span className="text-muted-foreground">(per-model)</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
