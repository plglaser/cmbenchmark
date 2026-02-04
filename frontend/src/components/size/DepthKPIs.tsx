import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';

interface DepthKPIsProps {
  data: {
    total_contained_nodes: number;
    total_root: number;
    max_depth_stats?: { mean?: number; median?: number };
    mean_depth_stats?: { mean?: number };
    contained_node_share_stats?: { mean?: number };
  } | null;
}

export function DepthKPIs({ data }: DepthKPIsProps) {
  if (!data) return null;

  const meanMaxDepth = data.max_depth_stats?.mean ?? 0;
  const medianMaxDepth = data.max_depth_stats?.median ?? 0;
  const meanDepth = data.mean_depth_stats?.mean ?? 0;
  const meanContainedShare = data.contained_node_share_stats?.mean ?? 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Key Metrics</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex justify-between">
          <span>Total Roots:</span>
          <Badge variant="outline">{data.total_root.toLocaleString()}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Total Contained Nodes:</span>
          <Badge variant="outline">{data.total_contained_nodes.toLocaleString()}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Mean Max Depth:</span>
          <Badge variant="outline">{meanMaxDepth.toFixed(2)}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Median Max Depth:</span>
          <Badge variant="outline">{medianMaxDepth.toFixed(2)}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Mean Depth:</span>
          <Badge variant="outline">{meanDepth.toFixed(2)}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Mean Contained Share:</span>
          <Badge variant="outline">{(meanContainedShare * 100).toFixed(1)}%</Badge>
        </div>
      </CardContent>
    </Card>
  );
}
