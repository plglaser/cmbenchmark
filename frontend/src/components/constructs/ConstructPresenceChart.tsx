import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface ConstructPresenceChartProps {
  data: {
    observed: number;
    missing: number;
    observedShare: number;
    missingShare: number;
  } | null;
}

export function ConstructPresenceChart({ data }: ConstructPresenceChartProps) {
  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Construct Coverage Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            No data available. Make sure construct coverage is enabled in your profile and measures were recomputed.
          </p>
        </CardContent>
      </Card>
    );
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const row = payload[0]?.payload;
      return (
        <div className="bg-background border rounded-lg shadow-lg p-3">
          <p className="font-medium">Construct Coverage</p>
          <p className="text-sm">Observed: {Number(row?.Observed || 0).toLocaleString()} ({(data.observedShare * 100).toFixed(1)}%)</p>
          <p className="text-sm">Missing: {Number(row?.Missing || 0).toLocaleString()} ({(data.missingShare * 100).toFixed(1)}%)</p>
        </div>
      );
    }
    return null;
  };

  const chartData = [
    {
      name: 'Constructs',
      Observed: data.observed,
      Missing: data.missing,
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Construct Coverage</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis hide />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Bar dataKey="Observed" stackId="a" fill="#10b981" />
            <Bar dataKey="Missing" stackId="a" fill="#ef4444" />
          </BarChart>
        </ResponsiveContainer>
        <p className="text-xs text-muted-foreground mt-2">
          “Observed” means a construct appears at least once in the dataset (not how often it appears).
        </p>
      </CardContent>
    </Card>
  );
}
