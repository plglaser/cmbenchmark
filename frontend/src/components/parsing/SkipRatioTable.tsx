import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface SkipRatioTableProps {
  data: Array<{
    modelId: string;
    skipRatio: number;
    elementsLoaded: number;
    elementsSkipped: number;
    relpath: string;
  }>;
}

export function SkipRatioTable({ data }: SkipRatioTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Top 10 Models with Highest Skip Ratio</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Model</TableHead>
              <TableHead>Skip Ratio</TableHead>
              <TableHead>Elements Loaded</TableHead>
              <TableHead>Elements Skipped</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.length > 0 ? (
              data.map((model, idx) => (
                <TableRow key={idx}>
                  <TableCell className="font-mono text-sm">{model.relpath}</TableCell>
                  <TableCell>{(model.skipRatio * 100).toFixed(2)}%</TableCell>
                  <TableCell>{model.elementsLoaded}</TableCell>
                  <TableCell>{model.elementsSkipped}</TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-muted-foreground">
                  No data available
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
