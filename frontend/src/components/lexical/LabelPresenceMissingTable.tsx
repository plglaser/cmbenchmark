import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';

interface LabelPresenceMissingTableProps {
  data: Array<{
    modelId: string;
    relpath: string;
    eligibleCount: number;
    presentCount: number;
    missingCount: number;
  }>;
}

export function LabelPresenceMissingTable({ data }: LabelPresenceMissingTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Top 10 Models with Most Missing Labels</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Model</TableHead>
              <TableHead>Missing</TableHead>
              <TableHead>Present</TableHead>
              <TableHead>Eligible</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.length > 0 ? (
              data.map((model, idx) => (
                <TableRow key={idx}>
                  <TableCell className="font-mono text-sm">{model.relpath}</TableCell>
                  <TableCell>{model.missingCount.toLocaleString()}</TableCell>
                  <TableCell>{model.presentCount.toLocaleString()}</TableCell>
                  <TableCell>{model.eligibleCount.toLocaleString()}</TableCell>
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
