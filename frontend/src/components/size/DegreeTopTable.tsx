import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface DegreeTopTableProps {
  data: Array<{
    modelId: string;
    relpath: string;
    avgDegree: number;
    avgInDegree: number;
    avgOutDegree: number;
    degreeMedian: number;
  }>;
}

export function DegreeTopTable({ data }: DegreeTopTableProps) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Highest Average Degree</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">No degree data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Top 10 Models by Avg Degree</CardTitle>
      </CardHeader>
      <CardContent className="overflow-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left py-2">Model</th>
              <th className="text-right py-2">Avg Degree</th>
              <th className="text-right py-2">Avg In</th>
              <th className="text-right py-2">Avg Out</th>
              <th className="text-right py-2">Median Degree</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.modelId} className="border-b last:border-b-0">
                <td className="py-2 pr-2 truncate max-w-[220px]" title={row.relpath}>
                  {row.relpath}
                </td>
                <td className="py-2 text-right">{row.avgDegree.toFixed(2)}</td>
                <td className="py-2 text-right">{row.avgInDegree.toFixed(2)}</td>
                <td className="py-2 text-right">{row.avgOutDegree.toFixed(2)}</td>
                <td className="py-2 text-right">{row.degreeMedian.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
