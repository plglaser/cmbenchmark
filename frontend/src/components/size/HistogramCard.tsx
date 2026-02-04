import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface HistogramCardProps {
  title: string;
  histogramData: Array<{ bin: string; count: number }>;
  emptyMessage?: string;
  barColor?: string;
}

export function HistogramCard({
  title,
  histogramData,
  emptyMessage = 'No data available',
  barColor = '#6366f1',
}: HistogramCardProps) {
  if (!histogramData || histogramData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">{emptyMessage}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={histogramData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="bin" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" fill={barColor} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
