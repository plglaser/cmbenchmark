import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';

interface LanguageUsageKPIsProps {
  data: Array<{ language: string; count: number; share: number }>;
}

export function LanguageUsageKPIs({ data }: LanguageUsageKPIsProps) {
  if (!data || data.length === 0) return null;

  const total = data.reduce((acc, d) => acc + (d.count ?? 0), 0);
  const distinct = data.length;
  const top = data[0];
  const unknown = data.find((d) => d.language === 'unknown');

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Language Usage KPIs</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex justify-between">
          <span>Models counted:</span>
          <Badge variant="outline">{total.toLocaleString()}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Distinct languages:</span>
          <Badge variant="outline">{distinct.toLocaleString()}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Top language:</span>
          <Badge variant="outline">
            {top?.language} ({((top?.share ?? 0) * 100).toFixed(1)}%)
          </Badge>
        </div>
        <div className="flex justify-between">
          <span>Unknown:</span>
          <Badge variant="outline">
            {(unknown?.count ?? 0).toLocaleString()} ({(((unknown?.share ?? 0) * 100) as number).toFixed(1)}%)
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}

