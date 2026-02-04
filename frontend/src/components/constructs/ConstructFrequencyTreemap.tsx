import { useMemo } from 'react';
import { ResponsiveContainer, Treemap, Tooltip } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface ConstructFrequencyTreemapProps {
  data: Array<{
    constructId: string;
    count: number;
    share?: number;
    group?: string;
    description?: string;
    kind?: string;
  }>;
  title?: string;
  /**
   * If provided, only include constructs whose kind is in this list.
   */
  kindFilter?: string[];
  /**
   * Treemaps get unreadable with too many very small tiles; default shows top 80.
   */
  maxItems?: number;
}

export function ConstructFrequencyTreemap({
  data,
  title = 'Construct Frequency (Treemap)',
  kindFilter,
  maxItems = 80,
}: ConstructFrequencyTreemapProps) {
  const treemapData = useMemo(() => {
    const rows = (data || [])
      .filter((d) => d && typeof d.constructId === 'string')
      .filter((d) => (kindFilter?.length ? !!d.kind && kindFilter.includes(d.kind) : true))
      .map((d) => ({ ...d, count: Number(d.count || 0) }))
      .filter((d) => d.count > 0)
      .sort((a, b) => b.count - a.count)
      .slice(0, maxItems)
      .map((d) => {
        const short = d.constructId.includes(':') ? d.constructId.split(':').slice(1).join(':') : d.constructId;
        const label = short && short.length > 24 ? `${short.slice(0, 22)}…` : short;
        return {
          name: label || d.constructId,
          fullId: d.constructId,
          size: d.count,
          count: d.count,
          share: typeof d.share === 'number' ? d.share : undefined,
          group: d.group,
          kind: d.kind,
          description: d.description,
        };
      });
    return { rows };
  }, [data, maxItems]);

  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">No data available</p>
        </CardContent>
      </Card>
    );
  }

  if (treemapData.rows.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            No non-zero construct counts available.
          </p>
        </CardContent>
      </Card>
    );
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || payload.length === 0) return null;
    const row = payload?.[0]?.payload;
    if (!row) return null;
    return (
      <div className="bg-background border rounded-lg shadow-lg p-3 max-w-[420px]">
        <p className="font-medium font-mono break-all">{row.fullId ?? row.name}</p>
        {row.group && <p className="text-sm">Group: {row.group}</p>}
        {row.kind && <p className="text-sm text-muted-foreground">Kind: {row.kind}</p>}
        <p className="text-sm">Count: {Number(row.count || 0).toLocaleString()}</p>
        {typeof row.share === 'number' && <p className="text-sm">Share: {(row.share * 100).toFixed(2)}%</p>}
        {row.description && <p className="text-xs text-muted-foreground mt-2">{row.description}</p>}
      </div>
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={420}>
          <Treemap
            data={treemapData.rows}
            dataKey="size"
            nameKey="name"
            isAnimationActive={false}
            type="flat"
            stroke="#ffffff"
          >
            <Tooltip content={<CustomTooltip />} />
          </Treemap>
        </ResponsiveContainer>
        <p className="text-xs text-muted-foreground mt-2">
          Area encodes total occurrences. Hover tiles for full IDs and metadata. Showing top {Math.min(maxItems, treemapData.rows.length)} constructs.
        </p>
      </CardContent>
    </Card>
  );
}

