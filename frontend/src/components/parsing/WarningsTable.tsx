import { Badge } from '../ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface WarningsTableProps {
  data: Array<{
    modelId: string;
    warningCount: number;
    warningsByType: Record<string, number>;
    relpath: string;
  }>;
}

export function WarningsTable({ data }: WarningsTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Models with Most Warnings</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Model</TableHead>
              <TableHead>Warning Count</TableHead>
              <TableHead>Warning Types</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.length > 0 ? (
              data.map((model, idx) => (
                <TableRow key={idx}>
                  <TableCell className="font-mono text-sm">{model.relpath}</TableCell>
                  <TableCell>{model.warningCount}</TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(model.warningsByType).map(([type, count]) => (
                        <Badge key={type} variant="outline">
                          {type}: {count}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={3} className="text-center text-muted-foreground">
                  No warnings found
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
