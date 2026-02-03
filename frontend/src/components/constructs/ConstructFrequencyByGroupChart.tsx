import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface ConstructFrequencyByGroupChartProps {
  data: Array<{
    group: string;
    count: number;
    share: number;
  }>;
}

export function ConstructFrequencyByGroupChart({ data }: ConstructFrequencyByGroupChartProps) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Frequency by Group</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">No group frequency data available</p>
        </CardContent>
      </Card>
    );
  }

  const displayData = data.map((d) => ({
    ...d,
    groupLabel: d.group.length > 14 ? `${d.group.slice(0, 12)}…` : d.group,
  }));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || payload.length === 0) return null;
    const row = payload[0]?.payload;
    return (
      <div className="bg-background border rounded-lg shadow-lg p-3">
        <p className="font-medium">{label}</p>
        <p className="text-sm">Count: {row.count.toLocaleString()}</p>
        <p className="text-sm">Share: {(row.share * 100).toFixed(1)}%</p>
      </div>
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Frequency by Group</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={displayData} margin={{ top: 20, right: 20, left: 10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="groupLabel" />
            <YAxis />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="count" fill="#06b6d4" />
          </BarChart>
        </ResponsiveContainer>
        <p className="text-xs text-muted-foreground mt-2">
          Groups use the construct profile’s category (e.g., ArchiMate layer). This highlights which parts of the language dominate the dataset.
        </p>
      </CardContent>
    </Card>
  );
}

