import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';

interface ConstructFrequencyKPIsProps {
  data: {
    dataset_total_construct_instances?: number;
    dataset_utilization_entropy?: number;
  } | null;
  frequencyData?: Array<{ constructId: string; share?: number }> | null;
}

export function ConstructFrequencyKPIs({ data, frequencyData }: ConstructFrequencyKPIsProps) {
  if (!data) return null;

  const totalInstances = Number(data.dataset_total_construct_instances || 0);
  const utilizationEntropy = Number(data.dataset_utilization_entropy || 0);
  const maxShare = Math.max(
    0,
    ...((frequencyData || []).map((row) => Number(row.share || 0)) || [])
  );
  const activeConstructs = (frequencyData || []).filter((row) => Number(row.share || 0) > 0).length;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Key Metrics</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex justify-between">
          <span>Total Construct Instances:</span>
          <Badge variant="outline">{totalInstances.toLocaleString()}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Utilization Entropy:</span>
          <Badge variant="outline">{utilizationEntropy.toFixed(2)}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Active Constructs:</span>
          <Badge variant="outline">{activeConstructs.toLocaleString()}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Top Construct Share:</span>
          <Badge variant="outline">{(maxShare * 100).toFixed(1)}%</Badge>
        </div>
      </CardContent>
    </Card>
  );
}
