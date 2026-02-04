import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';

interface ConnectivityKPIsProps {
  data: {
    total_components: number;
    total_isolated_nodes: number;
    n_components_stats?: { mean?: number; median?: number };
    isolated_node_share_stats?: { mean?: number };
    largest_component_size_stats?: { median?: number };
  } | null;
}

export function ConnectivityKPIs({ data }: ConnectivityKPIsProps) {
  if (!data) return null;

  const meanComponents = data.n_components_stats?.mean ?? 0;
  const medianLargest = data.largest_component_size_stats?.median ?? 0;
  const meanIsolatedShare = data.isolated_node_share_stats?.mean ?? 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Key Metrics</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex justify-between">
          <span>Total Components:</span>
          <Badge variant="outline">{data.total_components.toLocaleString()}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Total Isolated Nodes:</span>
          <Badge variant="outline">{data.total_isolated_nodes.toLocaleString()}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Mean Components / Model:</span>
          <Badge variant="outline">{meanComponents.toFixed(2)}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Median Largest Component:</span>
          <Badge variant="outline">{medianLargest.toFixed(1)}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Mean Isolated Share:</span>
          <Badge variant="outline">{(meanIsolatedShare * 100).toFixed(1)}%</Badge>
        </div>
      </CardContent>
    </Card>
  );
}
