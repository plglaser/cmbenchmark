import { useState, useEffect, useMemo } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Badge } from './ui/badge';
import { apiService } from '../services/api';
import type { MeasureResponse, ReportResponse } from '../types/api';
import type { BenchmarkProfile } from '../types/profile';
import { createDimensions } from '../data/dimensions';
import { ScoreRadar } from './report/ScoreRadar';
import { ExpandableTileDialog } from './report/ExpandableTileDialog';

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
      if (!profile) {
        throw new Error('Load a benchmark profile to build the report.');
      }
      const response = await apiService.report({
        profile,
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
  const parsingScoreData = useMemo(() => {
    if (!reportData) return [];
    return [
      { measure: 'Parse Status', score: reportData?.parseStatus?.score },
      { measure: 'Elements & Skips', score: reportData?.parseElementsSkips?.score },
      { measure: 'Warnings', score: reportData?.parseWarnings?.score },
    ]
      .filter((item) => Number.isFinite(item.score))
      .map((item) => ({ measure: item.measure, score: Number(item.score) }));
  }, [reportData]);
  const constructScoreData = useMemo(() => {
    if (!reportData) return [];
    return [
      { measure: 'Construct Presence', score: reportData?.constructPresence?.score },
      { measure: 'Construct Frequency', score: reportData?.constructFrequency?.score },
    ]
      .filter((item) => Number.isFinite(item.score))
      .map((item) => ({ measure: item.measure, score: Number(item.score) }));
  }, [reportData]);

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

            <Button type="submit" disabled={loading || !profile}>
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
                {dimensions.map((dimension) => {
                  const score = getDimensionScore(dimension.id);
                  return (
                    <TabsTrigger key={dimension.id} value={dimension.id}>
                      <span className="flex items-center gap-2">
                        <span>{dimension.name}</span>
                        {score !== null && (
                          <Badge variant={getScoreVariant(score)} className="text-[10px]">
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
                    {dimension.id === 'parsing' && parsingScoreData.length > 0 && (
                      <div className="mb-4">
                        <ScoreRadar
                          title="Parsing Score Radar"
                          data={parsingScoreData}
                          stroke="#2563eb"
                          fill="#60a5fa"
                        />
                      </div>
                    )}
                    {dimension.id === 'construct-coverage' && constructScoreData.length > 0 && (
                      <div className="mb-4">
                        <ScoreRadar
                          title="Construct Coverage Score Radar"
                          data={constructScoreData}
                          stroke="#10b981"
                          fill="#34d399"
                        />
                      </div>
                    )}
                    {/* Measures tab bar (separate from dimension tab bar) */}
                    <div className="mt-2 border rounded-md bg-muted/30 p-2">
                      <TabsList className="w-full flex flex-wrap justify-start gap-2 h-auto bg-transparent p-0">
                        {dimension.measures.map((measure) => {
                          const score = getMeasureScore(measure.id);
                          return (
                            <TabsTrigger key={measure.id} value={measure.id} className="text-sm">
                              <span className="flex items-center gap-2">
                                <span>{measure.name}</span>
                                {score !== null && (
                                  <Badge variant={getScoreVariant(score)} className="text-[10px]">
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
      </CardContent>
    </Card>
  );
}
