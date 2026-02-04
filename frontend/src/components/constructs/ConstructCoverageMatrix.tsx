import { useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';

interface ConstructCoverageMatrixProps {
  data: Array<{
    modelId: string;
    relpath: string;
    presentConstructs: Record<string, boolean>;
  }> | null;
  constructCatalog?: Record<string, any> | null;
  maxConstructs?: number;
}

type ConstructEntry = {
  id: string;
  label: string;
};

export function ConstructCoverageMatrix({
  data,
  constructCatalog,
  maxConstructs = 80,
}: ConstructCoverageMatrixProps) {
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(20);

  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Coverage Matrix</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No construct presence data available.</p>
        </CardContent>
      </Card>
    );
  }

  const models = useMemo(
    () =>
      [...data]
        .map((item) => ({
          modelId: String(item.modelId),
          relpath: String(item.relpath || item.modelId),
          presentConstructs: item.presentConstructs || {},
        }))
        .sort((a, b) => a.relpath.localeCompare(b.relpath)),
    [data]
  );

  const catalogEntries = constructCatalog ? Object.entries(constructCatalog) : [];
  let constructs: ConstructEntry[] = [];

  if (catalogEntries.length > 0) {
    constructs = catalogEntries.map(([id, info]) => {
      const label =
        (info && typeof info.match_type === 'string' && info.match_type) ||
        (info && typeof info.id === 'string' && info.id) ||
        id;
      return {
        id: String(id),
        label: String(label),
      };
    });
  } else {
    const constructSet = new Set<string>();
    for (const item of models) {
      Object.keys(item.presentConstructs || {}).forEach((cid) => constructSet.add(String(cid)));
    }
    constructs = Array.from(constructSet).map((id) => ({ id, label: id }));
  }

  constructs.sort((a, b) => a.label.localeCompare(b.label));

  const totalModels = models.length;
  const totalConstructs = constructs.length;
  const visibleConstructs = constructs.slice(0, maxConstructs);
  const totalPages = Math.max(1, Math.ceil(totalModels / pageSize));
  const safePageIndex = Math.min(pageIndex, totalPages - 1);
  const startIndex = safePageIndex * pageSize;
  const endIndex = startIndex + pageSize;
  const visibleModels = models.slice(startIndex, endIndex);
  const hasMoreModels = totalModels > visibleModels.length;
  const hasMoreConstructs = totalConstructs > visibleConstructs.length;

  const getModelLabel = (relpath: string) => {
    const parts = relpath.split('/');
    return parts[parts.length - 1] || relpath;
  };
  const truncateLabel = (value: string, maxLength = 18) =>
    value.length > maxLength ? `${value.slice(0, maxLength - 1)}…` : value;

  const pageStart = totalModels === 0 ? 0 : startIndex + 1;
  const pageEnd = Math.min(endIndex, totalModels);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Coverage Matrix</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-sm bg-emerald-500" />
            Present
          </div>
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-sm bg-muted border" />
            Absent
          </div>
          {(hasMoreModels || hasMoreConstructs) && (
            <span>
              Showing {visibleConstructs.length} of {totalConstructs} constructs and{' '}
              {pageStart}-{pageEnd} of {totalModels} models.
            </span>
          )}
        </div>

        <div className="mt-4 max-h-[520px] overflow-auto rounded-md border">
          <Table className="min-w-max">
            <TableHeader>
              <TableRow>
                <TableHead className="sticky left-0 z-10 min-w-[220px] bg-background">
                  Model
                </TableHead>
                {visibleConstructs.map((construct) => (
                  <TableHead
                    key={construct.id}
                    className="min-w-[84px] text-[10px] font-normal text-muted-foreground"
                  >
                    <span title={construct.label}>{construct.label}</span>
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {visibleModels.map((model) => (
                <TableRow key={model.modelId}>
                  <TableCell className="sticky left-0 z-10 min-w-[220px] bg-background">
                    <div className="text-xs font-medium" title={model.relpath}>
                      {truncateLabel(getModelLabel(model.relpath))}
                    </div>
                  </TableCell>
                  {visibleConstructs.map((construct) => {
                    const present = Boolean(model.presentConstructs?.[construct.id]);
                    const title = `${construct.label} in ${model.relpath}: ${
                      present ? 'present' : 'absent'
                    }`;
                    return (
                      <TableCell key={`${model.modelId}:${construct.id}`} className="p-1">
                        <div
                          className={`mx-auto h-4 w-4 rounded-sm ${
                            present ? 'bg-emerald-500' : 'bg-muted border'
                          }`}
                          title={title}
                        />
                      </TableCell>
                    );
                  })}
                </TableRow>
              ))}
              {visibleModels.length === 0 && (
                <TableRow>
                  <TableCell colSpan={visibleConstructs.length + 1} className="text-center text-muted-foreground">
                    No models available.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>

        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs text-muted-foreground">
          <div>
            Page {safePageIndex + 1} of {totalPages}
          </div>
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
            <label className="ml-2 flex items-center gap-2">
              Rows
              <select
                className="h-8 rounded-md border bg-background px-2 text-xs text-foreground"
                value={pageSize}
                onChange={(event) => {
                  const nextSize = Number(event.target.value) || 20;
                  setPageSize(nextSize);
                  setPageIndex(0);
                }}
              >
                {[10, 20, 30, 40, 50].map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
