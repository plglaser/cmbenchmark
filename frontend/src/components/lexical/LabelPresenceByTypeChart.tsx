import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface LabelPresenceByTypeChartProps {
  data: Array<{ type: string; missingShare: number }>;
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
    'Missing Share': (item.missingShare * 100).toFixed(1),
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Missing Labels by Element Type</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="type" 
              angle={-45}
              textAnchor="end"
              height={100}
              interval={0}
            />
            <YAxis />
            <Tooltip formatter={(value: any) => `${value}%`} />
            <Legend />
            <Bar dataKey="Missing Share" fill="#ef4444" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
