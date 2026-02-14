import { Badge } from '../ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface ElementsSkipsKPIsProps {
  data: {
    totalModelsEvaluated: number;
    modelsWithSkips: number;
    modelsWithoutSkips: number;
    modelsWithSkipsShare: number;
    totalElementsLoaded: number;
    totalElementsSkipped: number;
    totalElementsProcessed: number;
    datasetSkipRatio: number;
    datasetLoadRatio: number;
    avgSkipRatio: number;
    medianSkipRatio: number;
  } | null;
}

export function ElementsSkipsKPIs({ data }: ElementsSkipsKPIsProps) {
  if (!data) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Summary KPIs</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex justify-between">
          <span>Models Evaluated:</span>
          <Badge variant="outline">{data.totalModelsEvaluated.toLocaleString()}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Models with Skips:</span>
          <Badge variant="outline">
            {data.modelsWithSkips.toLocaleString()} ({(data.modelsWithSkipsShare * 100).toFixed(1)}%)
          </Badge>
        </div>
        <div className="flex justify-between">
          <span>Models without Skips:</span>
          <Badge variant="outline">{data.modelsWithoutSkips.toLocaleString()}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Total Elements Processed:</span>
          <Badge variant="outline">{data.totalElementsProcessed.toLocaleString()}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Elements Loaded:</span>
          <Badge variant="outline">
            {data.totalElementsLoaded.toLocaleString()} ({(data.datasetLoadRatio * 100).toFixed(1)}%)
          </Badge>
        </div>
        <div className="flex justify-between">
          <span>Elements Skipped:</span>
          <Badge variant="outline">
            {data.totalElementsSkipped.toLocaleString()} ({(data.datasetSkipRatio * 100).toFixed(1)}%)
          </Badge>
        </div>
        <div className="flex justify-between">
          <span>Mean Skip Ratio (Model):</span>
          <Badge variant="outline">{(data.avgSkipRatio * 100).toFixed(1)}%</Badge>
        </div>
        <div className="flex justify-between">
          <span>Median Skip Ratio (Model):</span>
          <Badge variant="outline">{(data.medianSkipRatio * 100).toFixed(1)}%</Badge>
        </div>
      </CardContent>
    </Card>
  );
}
