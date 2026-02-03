import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { useMemo, useState } from 'react';

interface MissingConstructsTableProps {
  data: Array<{
    constructId: string;
    group?: string;
    kind?: string;
    description?: string;
  }>;
}

export function MissingConstructsTable({ data }: MissingConstructsTableProps) {
  const [query, setQuery] = useState('');
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return data;
    return data.filter((d) => {
      const hay = `${d.group || ''} ${d.kind || ''} ${d.constructId || ''} ${d.description || ''}`.toLowerCase();
      return hay.includes(q);
    });
  }, [data, query]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Missing Constructs</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-3">
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter by group, construct id, or description…"
          />
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Group</TableHead>
              <TableHead>Construct</TableHead>
              <TableHead>Description</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.length > 0 ? (
              filtered.map((item, idx) => (
                <TableRow key={idx}>
                  <TableCell>{item.group || <span className="text-muted-foreground">—</span>}</TableCell>
                  <TableCell>
                    <div className="font-mono text-sm break-all">{item.constructId}</div>
                    {item.kind && <div className="text-xs text-muted-foreground">{item.kind}</div>}
                  </TableCell>
                  <TableCell className="text-sm">
                    {item.description ? item.description : <span className="text-muted-foreground">—</span>}
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={3} className="text-center text-muted-foreground">
                  {data.length === 0 ? 'All constructs are present' : 'No matches'}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
