import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';

interface ConstructFrequencyTopModelsTableProps {
  data: Array<{
    modelId: string;
    relpath: string;
    totalConstructInstances: number;
    utilizationEntropy: number;
  }>;
}

export function ConstructFrequencyTopModelsTable({ data }: ConstructFrequencyTopModelsTableProps) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Top Models by Construct Instances</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">No construct totals available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Top Models by Construct Instances</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Model</TableHead>
              <TableHead className="text-right">Total Instances</TableHead>
              <TableHead className="text-right">Utilization Entropy</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((row) => (
              <TableRow key={row.modelId}>
                <TableCell className="font-mono text-xs" title={row.relpath}>
                  {row.relpath}
                </TableCell>
                <TableCell className="text-right">{row.totalConstructInstances.toLocaleString()}</TableCell>
                <TableCell className="text-right">{row.utilizationEntropy.toFixed(2)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
