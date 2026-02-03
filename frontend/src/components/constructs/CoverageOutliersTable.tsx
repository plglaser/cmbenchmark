import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';

interface CoverageOutliersTableProps {
  data: Array<{
    modelId: string;
    relpath: string;
    coverageShare: number;
    constructsObservedCount?: number;
    constructsAvailableCount?: number;
    unknownTypeShare?: number;
    unknownNodeTypeCount?: number;
    unknownEdgeTypeCount?: number;
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
              <TableHead>Observed</TableHead>
              <TableHead>Unknown share</TableHead>
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
                  <TableCell className="text-sm">
                    {typeof model.constructsObservedCount === 'number' && typeof model.constructsAvailableCount === 'number'
                      ? `${model.constructsObservedCount}/${model.constructsAvailableCount}`
                      : <span className="text-muted-foreground">—</span>}
                  </TableCell>
                  <TableCell className="text-sm">
                    {typeof model.unknownTypeShare === 'number'
                      ? (
                        <div>
                          <Badge variant="outline">{(model.unknownTypeShare * 100).toFixed(1)}%</Badge>
                          {(typeof model.unknownNodeTypeCount === 'number' || typeof model.unknownEdgeTypeCount === 'number') && (
                            <div className="text-xs text-muted-foreground mt-1">
                              {`N:${(model.unknownNodeTypeCount ?? 0).toLocaleString()} / E:${(model.unknownEdgeTypeCount ?? 0).toLocaleString()}`}
                            </div>
                          )}
                        </div>
                      )
                      : <span className="text-muted-foreground">—</span>}
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
