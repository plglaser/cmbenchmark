import { useMemo, useState } from 'react';
import { Label } from '../ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { ConstructFrequencyChart } from './ConstructFrequencyChart';
import {
  constructKindOptions,
  filterFrequencyDataByKind,
  kindFilterLabel,
  type ConstructKindFilter,
} from './constructFrequencyFilters';

interface ConstructFrequencyChartWithFilterProps {
  data: Array<{
    constructId: string;
    count: number;
    share?: number;
    group?: string;
    description?: string;
    kind?: string;
  }>;
}

export function ConstructFrequencyChartWithFilter({ data }: ConstructFrequencyChartWithFilterProps) {
  const [kindFilter, setKindFilter] = useState<ConstructKindFilter>('all');

  const filteredData = useMemo(
    () => filterFrequencyDataByKind(data || [], kindFilter),
    [data, kindFilter]
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Construct Frequency (Top 20)</CardTitle>
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

        <ConstructFrequencyChart data={filteredData} showCard={false} />
        <p className="text-xs text-muted-foreground">
          Showing {kindFilterLabel(kindFilter)} only.
        </p>
      </CardContent>
    </Card>
  );
}
