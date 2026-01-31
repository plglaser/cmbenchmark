import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface LabelLengthTableProps {
  data: Array<{
    modelId: string;
    relpath: string;
    charsMedian: number;
    tokensMedian: number;
    shortShare: number;
    longShare: number;
  }>;
}

export function LabelLengthTable({ data }: LabelLengthTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Top 10 Models by Label Length</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Model</TableHead>
              <TableHead>Chars (Median)</TableHead>
              <TableHead>Tokens (Median)</TableHead>
              <TableHead>Short Share</TableHead>
              <TableHead>Long Share</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.length > 0 ? (
              data.map((model, idx) => (
                <TableRow key={idx}>
                  <TableCell className="font-mono text-sm">{model.relpath}</TableCell>
                  <TableCell>{model.charsMedian.toFixed(1)}</TableCell>
                  <TableCell>{model.tokensMedian.toFixed(1)}</TableCell>
                  <TableCell>{(model.shortShare * 100).toFixed(1)}%</TableCell>
                  <TableCell>{(model.longShare * 100).toFixed(1)}%</TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground">
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
