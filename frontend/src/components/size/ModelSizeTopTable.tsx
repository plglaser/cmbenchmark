import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface ModelSizeTopTableProps {
  data: Array<{
    modelId: string;
    relpath: string;
    nodeCount: number;
    edgeCount: number;
    elementCount: number;
    edgeNodeRatio: number;
  }>;
}

export function ModelSizeTopTable({ data }: ModelSizeTopTableProps) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Largest Models</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">No model size data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Top 10 Largest Models</CardTitle>
      </CardHeader>
      <CardContent className="overflow-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left py-2">Model</th>
              <th className="text-right py-2">Nodes</th>
              <th className="text-right py-2">Edges</th>
              <th className="text-right py-2">Elements</th>
              <th className="text-right py-2">Edge/Node</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.modelId} className="border-b last:border-b-0">
                <td className="py-2 pr-2 truncate max-w-[220px]" title={row.relpath}>
                  {row.relpath}
                </td>
                <td className="py-2 text-right">{row.nodeCount.toLocaleString()}</td>
                <td className="py-2 text-right">{row.edgeCount.toLocaleString()}</td>
                <td className="py-2 text-right">{row.elementCount.toLocaleString()}</td>
                <td className="py-2 text-right">{row.edgeNodeRatio.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
