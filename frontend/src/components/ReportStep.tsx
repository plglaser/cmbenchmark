import { useState, useEffect, useMemo } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ScrollArea } from './ui/scroll-area';
import { apiService } from '../services/api';
import type { MeasureResponse, ReportResponse } from '../types/api';
import type { BenchmarkProfile } from '../types/profile';
import { useReportData } from '../hooks/useReportData';
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

  // Process report data
  const processedData = useReportData(reportData);
  const dimensions = useMemo(
    () => (processedData ? createDimensions(processedData) : []),
    [processedData]
  );

  // Get current dimension and measure
  const currentDimension = dimensions.find((d) => d.id === selectedDimensionId);
  const currentMeasure =
    currentDimension?.measures.find((m) => m.id === selectedMeasureId) ||
    (currentDimension && currentDimension.measures.length > 0
      ? currentDimension.measures[0]
      : null);

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
                  <div className="flex gap-6 h-[calc(100vh-300px)] min-h-[600px]">
                    {/* Sidebar - Measures List */}
                    <div className="w-64 flex-shrink-0 border-r pr-4">
                      <ScrollArea className="h-full">
                        <div className="space-y-1">
                          {dimension.measures.map((measure) => (
                            <button
                              key={measure.id}
                              onClick={() => setSelectedMeasureId(measure.id)}
                              className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
                                selectedMeasureId === measure.id
                                  ? 'bg-primary text-primary-foreground'
                                  : 'hover:bg-muted'
                              }`}
                            >
                              <div className="font-medium">{measure.name}</div>
                              {measure.description && (
                                <div className="text-xs opacity-80 mt-1">{measure.description}</div>
                              )}
                            </button>
                          ))}
                        </div>
                      </ScrollArea>
                    </div>

                    {/* Main Content - Tiles Grid */}
                    <div className="flex-1 overflow-auto">
                      {currentMeasure && (
                        <div className="space-y-6">
                          <div>
                            <h3 className="text-lg font-semibold mb-1">{currentMeasure.name}</h3>
                            {currentMeasure.description && (
                              <p className="text-sm text-muted-foreground mb-4">
                                {currentMeasure.description}
                              </p>
                            )}
                          </div>
                          <div className="grid grid-cols-2 gap-4">
                            {currentMeasure.tiles.map((tile) => (
                              <div key={tile.id} className="min-w-0">
                                {tile.component}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </TabsContent>
              ))}
            </Tabs>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
