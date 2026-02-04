import { useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Label } from '../ui/label';
import {
  constructKindOptions,
  filterFrequencyDataByKind,
  kindFilterLabel,
  kindFilterToKinds,
  type ConstructKindFilter,
} from './constructFrequencyFilters';

interface ConstructFrequencyHeatmapProps {
  data: Array<{
    modelId: string;
    relpath: string;
    countsByConstruct: Record<string, number>;
  }> | null;
  constructCatalog?: Record<string, any> | null;
  constructTotals?: Array<{
    constructId: string;
    count: number;
    kind?: string;
  }> | null;
  maxConstructs?: number;
}

type ConstructEntry = {
  id: string;
  label: string;
};

export function ConstructFrequencyHeatmap({
  data,
  constructCatalog,
  constructTotals,
  maxConstructs = 60,
}: ConstructFrequencyHeatmapProps) {
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [kindFilter, setKindFilter] = useState<ConstructKindFilter>('all');

  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Construct × Model (Counts)</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No construct frequency data available.</p>
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
          countsByConstruct: item.countsByConstruct || {},
        }))
        .sort((a, b) => a.relpath.localeCompare(b.relpath)),
    [data]
  );

  const constructs = useMemo(() => {
    const totals = filterFrequencyDataByKind(constructTotals || [], kindFilter)
      .filter((t) => t && typeof t.constructId === 'string')
      .map((t) => ({ id: String(t.constructId), count: Number(t.count || 0) }))
      .filter((t) => t.count > 0)
      .sort((a, b) => b.count - a.count)
      .slice(0, maxConstructs)
      .map((t) => t.id);

    const kinds = kindFilterToKinds(kindFilter);
    const catalogEntries = constructCatalog ? Object.entries(constructCatalog) : [];

    let constructIds: string[] = [];
    if (totals.length > 0) {
      constructIds = totals;
    } else if (catalogEntries.length > 0) {
      constructIds = catalogEntries
        .filter(([, info]) => {
          if (!kinds?.length) return true;
          const kind = info?.kind;
          return typeof kind === 'string' && kinds.includes(kind);
        })
        .map(([id]) => String(id));
    } else {
      const constructSet = new Set<string>();
      for (const item of models) {
        Object.keys(item.countsByConstruct || {}).forEach((cid) => constructSet.add(String(cid)));
      }
      constructIds = Array.from(constructSet);
    }

    const entries: ConstructEntry[] = constructIds.map((id) => {
      const info = constructCatalog?.[id];
      const label =
        (info && typeof info.match_type === 'string' && info.match_type) ||
        (info && typeof info.id === 'string' && info.id) ||
        id;
      return { id, label: String(label) };
    });

    return entries.sort((a, b) => a.label.localeCompare(b.label));
  }, [constructTotals, constructCatalog, kindFilter, maxConstructs, models]);

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

  const maxCount = useMemo(() => {
    let maxValue = 0;
    for (const model of visibleModels) {
      for (const construct of visibleConstructs) {
        const value = Number(model.countsByConstruct?.[construct.id] || 0);
        if (value > maxValue) {
          maxValue = value;
        }
      }
    }
    return maxValue;
  }, [visibleModels, visibleConstructs]);

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
        <CardTitle className="text-base">Construct × Model (Counts)</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            <Label className="text-xs">Show</Label>
            <select
              className="h-8 rounded-md border bg-background px-2 text-xs text-foreground"
              value={kindFilter}
              onChange={(event) => setKindFilter(event.target.value as ConstructKindFilter)}
            >
              {constructKindOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            Max count: {maxCount > 0 ? maxCount.toLocaleString() : '—'} ·{' '}
            {kindFilterLabel(kindFilter)}
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
                    const count = Number(model.countsByConstruct?.[construct.id] || 0);
                    const intensity = maxCount > 0 ? count / maxCount : 0;
                    const alpha = count > 0 ? 0.2 + 0.8 * intensity : 0;
                    const title = `${construct.label} in ${model.relpath}: ${count.toLocaleString()}`;
                    return (
                      <TableCell key={`${model.modelId}:${construct.id}`} className="p-1 text-center">
                        <div
                          className="mx-auto flex h-6 min-w-[28px] items-center justify-center rounded-sm px-1 text-[10px] font-medium"
                          style={
                            count > 0
                              ? { backgroundColor: `rgba(16, 185, 129, ${alpha})` }
                              : undefined
                          }
                          title={title}
                        >
                          {count > 0 ? count.toLocaleString() : ''}
                        </div>
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
