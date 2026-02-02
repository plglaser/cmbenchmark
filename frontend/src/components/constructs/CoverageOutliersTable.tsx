import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';

interface CoverageOutliersTableProps {
  data: Array<{
    modelId: string;
    relpath: string;
    coverageShare: number;
  }>;
  title: string;
}

export function CoverageOutliersTable({ data, title }: CoverageOutliersTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Model</TableHead>
              <TableHead>Coverage</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.length > 0 ? (
              data.map((model, idx) => (
                <TableRow key={idx}>
                  <TableCell className="font-mono text-sm">{model.relpath}</TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {(model.coverageShare * 100).toFixed(1)}%
                    </Badge>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={2} className="text-center text-muted-foreground">
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
