import { useMemo, useState } from 'react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';

type LabelRow = { label: string; count: number };

interface LexicalDiversityTopLabelsTableProps {
  data: Array<[string, number]> | Array<{ label: string; count: number }>;
  pageSizeOptions?: number[];
  title?: string;
}

export function LexicalDiversityTopLabelsTable({
  data,
  pageSizeOptions = [10, 20, 50],
  title = 'Top Labels by Occurrence',
}: LexicalDiversityTopLabelsTableProps) {
  const rows = useMemo<LabelRow[]>(() => {
    if (!Array.isArray(data)) {
      return [];
    }
    return data
      .map((entry) => {
        if (Array.isArray(entry)) {
          return { label: String(entry[0] ?? ''), count: Number(entry[1] ?? 0) };
        }
        if (entry && typeof entry === 'object') {
          return { label: String(entry.label ?? ''), count: Number(entry.count ?? 0) };
        }
        return null;
      })
      .filter((entry): entry is LabelRow => !!entry && entry.label.length > 0);
  }, [data]);

  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(pageSizeOptions[0] ?? 10);

  const totalRows = rows.length;
  const totalPages = Math.max(1, Math.ceil(totalRows / pageSize));
  const safePageIndex = Math.min(pageIndex, totalPages - 1);
  const startIndex = safePageIndex * pageSize;
  const endIndex = Math.min(startIndex + pageSize, totalRows);
  const visibleRows = rows.slice(startIndex, endIndex);
  const pageStart = totalRows === 0 ? 0 : startIndex + 1;
  const pageEnd = endIndex;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-muted-foreground">
          <div>
            Showing {pageStart}-{pageEnd} of {totalRows.toLocaleString()} labels
          </div>
          <div>Page {safePageIndex + 1} of {totalPages}</div>
        </div>

        <div className="mt-3 rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Label</TableHead>
                <TableHead className="text-right">Count</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {visibleRows.length > 0 ? (
                visibleRows.map((row, idx) => (
                  <TableRow key={`${row.label}-${idx}`}>
                    <TableCell className="font-mono text-xs">{row.label}</TableCell>
                    <TableCell className="text-right">{row.count.toLocaleString()}</TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={2} className="text-center text-muted-foreground">
                    No labels available
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>

        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setPageIndex(0)}
              disabled={safePageIndex === 0}
            >
              First
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setPageIndex((prev) => Math.max(0, prev - 1))}
              disabled={safePageIndex === 0}
            >
              Prev
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setPageIndex((prev) => Math.min(totalPages - 1, prev + 1))}
              disabled={safePageIndex >= totalPages - 1}
            >
              Next
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setPageIndex(totalPages - 1)}
              disabled={safePageIndex >= totalPages - 1}
            >
              Last
            </Button>
          </div>
          <label className="flex items-center gap-2">
            Rows
            <select
              className="h-8 rounded-md border bg-background px-2 text-xs text-foreground"
              value={pageSize}
              onChange={(event) => {
                const nextSize = Number(event.target.value) || pageSizeOptions[0] || 10;
                setPageSize(nextSize);
                setPageIndex(0);
              }}
            >
              {pageSizeOptions.map((size) => (
                <option key={size} value={size}>
                  {size}
                </option>
              ))}
            </select>
          </label>
        </div>
      </CardContent>
    </Card>
  );
}
