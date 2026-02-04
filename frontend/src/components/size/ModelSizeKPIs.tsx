import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';

interface ModelSizeKPIsProps {
  data: {
    total_node_count: number;
    total_edge_count: number;
    total_element_count: number;
    node_count_stats?: { median?: number; mean?: number };
    edge_count_stats?: { median?: number; mean?: number };
    element_count_stats?: { median?: number; mean?: number };
    edge_node_ratio_stats?: { median?: number; mean?: number };
  } | null;
}

export function ModelSizeKPIs({ data }: ModelSizeKPIsProps) {
  if (!data) return null;

  const nodeMedian = data.node_count_stats?.median ?? 0;
  const edgeMedian = data.edge_count_stats?.median ?? 0;
  const elementMedian = data.element_count_stats?.median ?? 0;
  const ratioMean = data.edge_node_ratio_stats?.mean ?? 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Key Metrics</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex justify-between">
          <span>Total Nodes:</span>
          <Badge variant="outline">{data.total_node_count.toLocaleString()}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Total Edges:</span>
          <Badge variant="outline">{data.total_edge_count.toLocaleString()}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Total Elements:</span>
          <Badge variant="outline">{data.total_element_count.toLocaleString()}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Median Nodes / Model:</span>
          <Badge variant="outline">{nodeMedian.toFixed(1)}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Median Edges / Model:</span>
          <Badge variant="outline">{edgeMedian.toFixed(1)}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Median Elements / Model:</span>
          <Badge variant="outline">{elementMedian.toFixed(1)}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Mean Edge/Node Ratio:</span>
          <Badge variant="outline">{ratioMean.toFixed(2)}</Badge>
        </div>
      </CardContent>
    </Card>
  );
}
