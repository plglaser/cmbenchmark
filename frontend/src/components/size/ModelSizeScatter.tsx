import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface ModelSizeScatterProps {
  data: Array<{ modelId: string; relpath: string; nodeCount: number; edgeCount: number }>;
}

export function ModelSizeScatter({ data }: ModelSizeScatterProps) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Nodes vs Edges per Model</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">No scatter plot data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Nodes vs Edges per Model</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <CartesianGrid />
            <XAxis type="number" dataKey="nodeCount" name="Nodes" />
            <YAxis type="number" dataKey="edgeCount" name="Edges" />
            <Tooltip
              cursor={{ strokeDasharray: '3 3' }}
              formatter={(value, name) => [Number(value).toLocaleString(), name]}
              labelFormatter={(label, payload) => {
                const relpath = payload?.[0]?.payload?.relpath;
                return relpath ? `Model: ${relpath}` : `Nodes: ${label}`;
              }}
            />
            <Scatter dataKey="edgeCount" data={data} fill="#f97316" />
          </ScatterChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
