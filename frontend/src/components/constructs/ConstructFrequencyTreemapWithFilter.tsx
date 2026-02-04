import { useMemo, useState } from 'react';
import { Label } from '../ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { ConstructFrequencyTreemap } from './ConstructFrequencyTreemap';
import {
  constructKindOptions,
  filterFrequencyDataByKind,
  kindFilterLabel,
  type ConstructKindFilter,
} from './constructFrequencyFilters';

interface ConstructFrequencyTreemapWithFilterProps {
  data: Array<{
    constructId: string;
    count: number;
    share?: number;
    group?: string;
    description?: string;
    kind?: string;
  }>;
}

export function ConstructFrequencyTreemapWithFilter({ data }: ConstructFrequencyTreemapWithFilterProps) {
  const [kindFilter, setKindFilter] = useState<ConstructKindFilter>('all');

  const filteredData = useMemo(
    () => filterFrequencyDataByKind(data || [], kindFilter),
    [data, kindFilter]
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          Construct Frequency (Treemap) · {kindFilterLabel(kindFilter)}
        </CardTitle>
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

        <ConstructFrequencyTreemap data={filteredData} showCard={false} />
      </CardContent>
    </Card>
  );
}
