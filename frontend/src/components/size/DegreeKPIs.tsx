import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';

interface DegreeKPIsProps {
  data: {
    avg_degree_stats?: { mean?: number; median?: number };
    avg_in_degree_stats?: { mean?: number };
    avg_out_degree_stats?: { mean?: number };
    degree_median_stats?: { median?: number };
  } | null;
}

export function DegreeKPIs({ data }: DegreeKPIsProps) {
  if (!data) return null;

  const avgDegreeMean = data.avg_degree_stats?.mean ?? 0;
  const avgDegreeMedian = data.avg_degree_stats?.median ?? 0;
  const avgInMean = data.avg_in_degree_stats?.mean ?? 0;
  const avgOutMean = data.avg_out_degree_stats?.mean ?? 0;
  const medianDegreeMedian = data.degree_median_stats?.median ?? 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Key Metrics</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex justify-between">
          <span>Mean Avg Degree:</span>
          <Badge variant="outline">{avgDegreeMean.toFixed(2)}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Median Avg Degree:</span>
          <Badge variant="outline">{avgDegreeMedian.toFixed(2)}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Mean Avg In-Degree:</span>
          <Badge variant="outline">{avgInMean.toFixed(2)}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Mean Avg Out-Degree:</span>
          <Badge variant="outline">{avgOutMean.toFixed(2)}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Median of Median Degree:</span>
          <Badge variant="outline">{medianDegreeMedian.toFixed(2)}</Badge>
        </div>
      </CardContent>
    </Card>
  );
}
