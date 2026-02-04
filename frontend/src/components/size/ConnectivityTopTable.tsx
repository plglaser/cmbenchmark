import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface ConnectivityTopTableProps {
  data: Array<{
    modelId: string;
    relpath: string;
    isolatedNodeShare: number;
    isolatedNodeCount: number;
    nComponents: number;
    largestComponentSize: number;
  }>;
}

export function ConnectivityTopTable({ data }: ConnectivityTopTableProps) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Most Fragmented Models</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">No connectivity data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Top 10 Models by Isolated Share</CardTitle>
      </CardHeader>
      <CardContent className="overflow-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left py-2">Model</th>
              <th className="text-right py-2">Isolated %</th>
              <th className="text-right py-2">Isolated</th>
              <th className="text-right py-2">Components</th>
              <th className="text-right py-2">Largest Comp.</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.modelId} className="border-b last:border-b-0">
                <td className="py-2 pr-2 truncate max-w-[220px]" title={row.relpath}>
                  {row.relpath}
                </td>
                <td className="py-2 text-right">{(row.isolatedNodeShare * 100).toFixed(1)}%</td>
                <td className="py-2 text-right">{row.isolatedNodeCount.toLocaleString()}</td>
                <td className="py-2 text-right">{row.nComponents.toLocaleString()}</td>
                <td className="py-2 text-right">{row.largestComponentSize.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
