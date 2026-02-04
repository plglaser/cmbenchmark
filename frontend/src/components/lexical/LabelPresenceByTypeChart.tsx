import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface LabelPresenceByTypeChartProps {
  data: Array<{ type: string; missingCount: number }>;
}

export function LabelPresenceByTypeChart({ data }: LabelPresenceByTypeChartProps) {
  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Missing Labels by Element Type</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">No data available</p>
        </CardContent>
      </Card>
    );
  }

  const chartData = data.map((item) => ({
    type: item.type,
    'Missing Count': item.missingCount,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Missing Labels by Element Type</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 10, right: 20, left: 20, bottom: 10 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis type="category" dataKey="type" width={120} />
            <Tooltip formatter={(value: any) => Number(value).toLocaleString()} />
            <Bar dataKey="Missing Count" fill="#ef4444" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
