import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface LabelPresenceChartProps {
  data: {
    present: number;
    missing: number;
    presentShare: number;
    missingShare: number;
  } | null;
}

const COLORS = ['#10b981', '#ef4444'];

export function LabelPresenceChart({ data }: LabelPresenceChartProps) {
  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Label Presence Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">No data available</p>
        </CardContent>
      </Card>
    );
  }

  const chartData = [
    { name: 'Present', value: data.present, share: data.presentShare },
    { name: 'Missing', value: data.missing, share: data.missingShare },
  ];

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      return (
        <div className="bg-background border rounded-lg shadow-lg p-3">
          <p className="font-medium">{data.name}</p>
          <p className="text-sm">
            Count: {data.value.toLocaleString()}
          </p>
          <p className="text-sm">
            Share: {(data.payload.share * 100).toFixed(1)}%
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Label Presence Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, share }) => `${name}: ${(share * 100).toFixed(1)}%`}
              outerRadius={100}
              fill="#8884d8"
              dataKey="value"
            >
              {chartData.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
