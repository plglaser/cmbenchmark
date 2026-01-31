import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface FileSizeTableProps {
  data: Array<{
    modelId: string;
    sourceSize: number;
    irSize: number;
    relpath: string;
  }>;
}

export function FileSizeTable({ data }: FileSizeTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Top 10 Largest Models</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Model</TableHead>
              <TableHead>Source Size (bytes)</TableHead>
              <TableHead>IR Size (bytes)</TableHead>
              <TableHead>Compression Ratio</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.length > 0 ? (
              data.map((model, idx) => (
                <TableRow key={idx}>
                  <TableCell className="font-mono text-sm">{model.relpath}</TableCell>
                  <TableCell>{model.sourceSize.toLocaleString()}</TableCell>
                  <TableCell>{model.irSize.toLocaleString()}</TableCell>
                  <TableCell>
                    {model.sourceSize > 0
                      ? (((model.sourceSize - model.irSize) / model.sourceSize) * 100).toFixed(1)
                      : 0}
                    %
                  </TableCell>
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
