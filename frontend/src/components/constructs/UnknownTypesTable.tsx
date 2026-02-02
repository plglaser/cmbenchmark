import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface UnknownTypesTableProps {
  data: Array<{
    type: string;
    count: number;
  }>;
}

export function UnknownTypesTable({ data }: UnknownTypesTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Top Unknown Types</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Type</TableHead>
              <TableHead>Count</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.length > 0 ? (
              data.map((item, idx) => (
                <TableRow key={idx}>
                  <TableCell className="font-mono text-sm">{item.type}</TableCell>
                  <TableCell>{item.count.toLocaleString()}</TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={2} className="text-center text-muted-foreground">
                  No unknown types found
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
