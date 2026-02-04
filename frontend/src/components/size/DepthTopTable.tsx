import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface DepthTopTableProps {
  data: Array<{
    modelId: string;
    relpath: string;
    maxDepth: number;
    meanDepth: number;
    rootCount: number;
    containedNodeShare: number;
  }>;
}

export function DepthTopTable({ data }: DepthTopTableProps) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Deepest Models</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">No depth data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Top 10 Models by Max Depth</CardTitle>
      </CardHeader>
      <CardContent className="overflow-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left py-2">Model</th>
              <th className="text-right py-2">Max Depth</th>
              <th className="text-right py-2">Mean Depth</th>
              <th className="text-right py-2">Roots</th>
              <th className="text-right py-2">Contained %</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.modelId} className="border-b last:border-b-0">
                <td className="py-2 pr-2 truncate max-w-[220px]" title={row.relpath}>
                  {row.relpath}
                </td>
                <td className="py-2 text-right">{row.maxDepth.toLocaleString()}</td>
                <td className="py-2 text-right">{row.meanDepth.toFixed(2)}</td>
                <td className="py-2 text-right">{row.rootCount.toLocaleString()}</td>
                <td className="py-2 text-right">{(row.containedNodeShare * 100).toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
