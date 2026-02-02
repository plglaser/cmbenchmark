import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';

interface ConstructPresenceKPIsProps {
  data: {
    constructs_available_count: number;
    constructs_observed_count: number;
    coverage_share: number;
    unknown_type_share_dataset: number;
    coverage_share_stats?: {
      median: number;
      mean: number;
    };
  } | null;
}

export function ConstructPresenceKPIs({ data }: ConstructPresenceKPIsProps) {
  if (!data) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Key Metrics</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex justify-between">
          <span>Available Constructs:</span>
          <Badge variant="outline">{data.constructs_available_count.toLocaleString()}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Observed Constructs:</span>
          <Badge variant="outline">
            {data.constructs_observed_count.toLocaleString()} ({(data.coverage_share * 100).toFixed(1)}%)
          </Badge>
        </div>
        <div className="flex justify-between">
          <span>Missing Constructs:</span>
          <Badge variant="outline">
            {(data.constructs_available_count - data.constructs_observed_count).toLocaleString()} ({((1 - data.coverage_share) * 100).toFixed(1)}%)
          </Badge>
        </div>
        {data.coverage_share_stats && (
          <>
            <div className="flex justify-between">
              <span>Median Model Coverage:</span>
              <Badge variant="outline">
                {(data.coverage_share_stats.median * 100).toFixed(1)}%
              </Badge>
            </div>
            <div className="flex justify-between">
              <span>Mean Model Coverage:</span>
              <Badge variant="outline">
                {(data.coverage_share_stats.mean * 100).toFixed(1)}%
              </Badge>
            </div>
          </>
        )}
        <div className="flex justify-between">
          <span>Unknown Types Share:</span>
          <Badge variant="outline">
            {(data.unknown_type_share_dataset * 100).toFixed(1)}%
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}
