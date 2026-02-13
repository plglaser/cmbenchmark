import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface LanguageUsageBarChartProps {
  data: Array<{ language: string; count: number; share: number }>;
}

export function LanguageUsageBarChart({ data }: LanguageUsageBarChartProps) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Language Frequency</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">No data available</p>
        </CardContent>
      </Card>
    );
  }

  const chartData = data.slice(0, 15).map((d) => ({
    language: d.language,
    count: d.count,
    sharePct: (d.share * 100).toFixed(1),
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Language Frequency (Top 15)</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={chartData} margin={{ top: 20, right: 20, left: 10, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="language"
              angle={-45}
              textAnchor="end"
              height={90}
              interval={0}
            />
            <YAxis />
            <Tooltip
              formatter={(value: any, name: string, props: any) => {
                if (name === 'count') {
                  const pct = props?.payload?.sharePct;
                  return [`${value} (${pct}%)`, 'count'];
                }
                return [value, name];
              }}
            />
            <Bar dataKey="count" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

