import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface MissingConstructsTableProps {
  data: Array<{
    constructId: string;
    layer?: string;
  }>;
}

export function MissingConstructsTable({ data }: MissingConstructsTableProps) {
  // Group by layer if available
  const groupedByLayer: Record<string, Array<{ constructId: string; layer?: string }>> = {};
  const ungrouped: Array<{ constructId: string; layer?: string }> = [];

  data.forEach((item) => {
    if (item.layer) {
      if (!groupedByLayer[item.layer]) {
        groupedByLayer[item.layer] = [];
      }
      groupedByLayer[item.layer].push(item);
    } else {
      ungrouped.push(item);
    }
  });

  const layers = Object.keys(groupedByLayer).sort();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Missing Constructs</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Layer</TableHead>
              <TableHead>Construct ID</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {layers.length > 0 || ungrouped.length > 0 ? (
              <>
                {layers.map((layer) =>
                  groupedByLayer[layer].map((item, idx) => (
                    <TableRow key={`${layer}-${idx}`}>
                      <TableCell>{layer}</TableCell>
                      <TableCell className="font-mono text-sm">{item.constructId}</TableCell>
                    </TableRow>
                  ))
                )}
                {ungrouped.map((item, idx) => (
                  <TableRow key={`ungrouped-${idx}`}>
                    <TableCell className="text-muted-foreground">—</TableCell>
                    <TableCell className="font-mono text-sm">{item.constructId}</TableCell>
                  </TableRow>
                ))}
              </>
            ) : (
              <TableRow>
                <TableCell colSpan={2} className="text-center text-muted-foreground">
                  All constructs are present
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
