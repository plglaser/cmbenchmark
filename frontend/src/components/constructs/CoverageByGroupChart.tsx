import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface CoverageByGroupChartProps {
  data: Array<{
    group: string;
    available: number;
    observed: number;
    missing: number;
    coverageShare: number;
  }>;
  title?: string;
}

export function CoverageByGroupChart({ data, title = 'Coverage by Group' }: CoverageByGroupChartProps) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">No group breakdown available</p>
        </CardContent>
      </Card>
    );
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || payload.length === 0) return null;
    const row = payload[0]?.payload;
    return (
      <div className="bg-background border rounded-lg shadow-lg p-3">
        <p className="font-medium">{label}</p>
        <p className="text-sm">Coverage: {(row.coverageShare * 100).toFixed(1)}%</p>
        <p className="text-sm">Observed: {row.observed.toLocaleString()} / {row.available.toLocaleString()}</p>
        <p className="text-sm text-muted-foreground">Missing: {row.missing.toLocaleString()}</p>
      </div>
    );
  };

  // Recharts doesn't do horizontal scroll nicely; keep labels short and use tooltip for details.
  const displayData = data.map((d) => ({
    ...d,
    groupLabel: d.group.length > 14 ? `${d.group.slice(0, 12)}…` : d.group,
    coveragePct: Math.round(d.coverageShare * 1000) / 10,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={displayData} margin={{ top: 20, right: 20, left: 10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="groupLabel" />
            <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="coveragePct" name="Coverage" fill="#10b981" />
          </BarChart>
        </ResponsiveContainer>
        <p className="text-xs text-muted-foreground mt-2">
          Bars show % of constructs observed at least once, grouped by profile category (e.g., ArchiMate layer).
        </p>
      </CardContent>
    </Card>
  );
}

