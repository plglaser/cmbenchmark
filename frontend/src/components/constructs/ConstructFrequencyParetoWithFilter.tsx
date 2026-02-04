import { useMemo, useState } from 'react';
import { Label } from '../ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { ConstructFrequencyParetoChart } from './ConstructFrequencyParetoChart';
import {
  constructKindOptions,
  filterFrequencyDataByKind,
  kindFilterLabel,
  type ConstructKindFilter,
} from './constructFrequencyFilters';

interface ConstructFrequencyParetoWithFilterProps {
  data: Array<{
    constructId: string;
    count: number;
    share?: number;
    group?: string;
    description?: string;
    kind?: string;
  }>;
}

type ParetoRow = {
  rank: number;
  constructId: string;
  count: number;
  share: number;
  cumulativeShare: number;
};

const buildPareto = (rows: ConstructFrequencyParetoWithFilterProps['data']): ParetoRow[] => {
  const sorted = [...rows]
    .filter((r) => r && Number(r.count || 0) > 0)
    .map((r) => ({ ...r, count: Number(r.count || 0) }))
    .sort((a, b) => b.count - a.count);

  const total = sorted.reduce((sum, row) => sum + row.count, 0);
  let cumulative = 0;
  return sorted.map((row, idx) => {
    const share = total > 0 ? row.count / total : 0;
    cumulative += share;
    return {
      rank: idx + 1,
      constructId: row.constructId,
      count: row.count,
      share,
      cumulativeShare: cumulative,
    };
  });
};

export function ConstructFrequencyParetoWithFilter({ data }: ConstructFrequencyParetoWithFilterProps) {
  const [kindFilter, setKindFilter] = useState<ConstructKindFilter>('all');

  const filteredData = useMemo(
    () => filterFrequencyDataByKind(data || [], kindFilter),
    [data, kindFilter]
  );

  const paretoData = useMemo(() => buildPareto(filteredData), [filteredData]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Construct Concentration (Pareto)</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
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

        <ConstructFrequencyParetoChart data={paretoData} showCard={false} />
        <p className="text-xs text-muted-foreground">
          Showing {kindFilterLabel(kindFilter)} only.
        </p>
      </CardContent>
    </Card>
  );
}
