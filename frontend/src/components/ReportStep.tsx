import { useState, useEffect, useMemo } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { apiService } from '../services/api';
import type { MeasureResponse, ReportResponse } from '../types/api';
import type { BenchmarkProfile } from '../types/profile';
import { createDimensions } from '../data/dimensions';

interface ReportStepProps {
  measureResult: MeasureResponse | null;
  onReportComplete?: (result: ReportResponse) => void;
  profile: BenchmarkProfile | null;
}

export function ReportStep({ measureResult, onReportComplete, profile }: ReportStepProps) {
  const [measuresPath, setMeasuresPath] = useState('');
  const [measuresPerModelPath, setMeasuresPerModelPath] = useState('');
  const [irInfoPath, setIrInfoPath] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reportData, setReportData] = useState<ReportResponse | null>(null);
  const [selectedDimensionId, setSelectedDimensionId] = useState<string>('parsing');
  const [selectedMeasureId, setSelectedMeasureId] = useState<string | null>(null);

  // Auto-fill paths from measure result or profile
  useEffect(() => {
    if (measureResult) {
      if (!measuresPath) {
        setMeasuresPath(measureResult.measures_path);
      }
      if (!measuresPerModelPath) {
        setMeasuresPerModelPath(measureResult.measures_per_model_path);
      }
      // Try to infer ir_info.json path from measures path
      if (!irInfoPath && measureResult.output_dir) {
        setIrInfoPath(`${measureResult.output_dir}/ir_info.json`);
      }
    } else if (profile) {
      // Pre-fill from profile output path
      const outputPath = profile.output_path;
      if (!measuresPath) {
        setMeasuresPath(`${outputPath}/measures.json`);
      }
      if (!measuresPerModelPath) {
        setMeasuresPerModelPath(`${outputPath}/measures_per_model.json`);
      }
      if (!irInfoPath) {
        setIrInfoPath(`${outputPath}/ir_info.json`);
      }
    }
  }, [measureResult, profile]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await apiService.report({
        measures_path: measuresPath,
        measures_per_model_path: measuresPerModelPath,
        ir_info_path: irInfoPath || null,
      });
      setReportData(response);
      if (onReportComplete) {
        onReportComplete(response);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load report data');
    } finally {
      setLoading(false);
    }
  };

  const dimensions = useMemo(
    () => (reportData ? createDimensions(reportData) : []),
    [reportData]
  );

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
            <div className="space-y-2">
              <Label htmlFor="measures-path">Measures Path (measures.json) *</Label>
              <Input
                id="measures-path"
                type="text"
                className="font-mono"
                value={measuresPath}
                onChange={(e) => setMeasuresPath(e.target.value)}
                placeholder="/path/to/measures.json"
                required
                disabled={loading || !!profile}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="measures-per-model-path">
                Measures Per Model Path (measures_per_model.json) *
              </Label>
              <Input
                id="measures-per-model-path"
                type="text"
                className="font-mono"
                value={measuresPerModelPath}
                onChange={(e) => setMeasuresPerModelPath(e.target.value)}
                placeholder="/path/to/measures_per_model.json"
                required
                disabled={loading || !!profile}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="ir-info-path">IR Info Path (ir_info.json) - Optional</Label>
              <Input
                id="ir-info-path"
                type="text"
                className="font-mono"
                value={irInfoPath}
                onChange={(e) => setIrInfoPath(e.target.value)}
                placeholder="/path/to/ir_info.json"
                disabled={loading || !!profile}
              />
              <p className="text-sm text-muted-foreground">
                Used for linking models in tables (optional)
              </p>
            </div>

            {error && (
              <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
                {error}
              </div>
            )}

            <Button type="submit" disabled={loading || !measuresPath || !measuresPerModelPath}>
              {loading ? 'Loading...' : 'Load Report'}
            </Button>
          </form>
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
              <TabsList className="grid w-full grid-cols-5">
                {dimensions.map((dimension) => (
                  <TabsTrigger key={dimension.id} value={dimension.id}>
                    {dimension.name}
                  </TabsTrigger>
                ))}
              </TabsList>

              {dimensions.map((dimension) => (
                <TabsContent key={dimension.id} value={dimension.id} className="mt-6">
                  <Tabs
                    value={selectedMeasureId ?? dimension.measures[0]?.id ?? ''}
                    onValueChange={(value) => setSelectedMeasureId(value)}
                    className="w-full"
                  >
                    {/* Measures tab bar (separate from dimension tab bar) */}
                    <div className="mt-2 border rounded-md bg-muted/30 p-2">
                      <TabsList className="w-full flex flex-wrap justify-start gap-2 h-auto bg-transparent p-0">
                        {dimension.measures.map((measure) => (
                          <TabsTrigger key={measure.id} value={measure.id} className="text-sm">
                            {measure.name}
                          </TabsTrigger>
                        ))}
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
                            {measure.tiles.map((tile) => (
                              <div key={tile.id} className="min-w-0">
                                {tile.component}
                              </div>
                            ))}
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
      </CardContent>
    </Card>
  );
}
