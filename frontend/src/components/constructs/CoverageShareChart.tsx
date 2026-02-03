import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface CoverageShareChartProps {
  histogramData: Array<{ bin: string; count: number }>;
}

export function CoverageShareChart({ histogramData }: CoverageShareChartProps) {
  if (!histogramData || histogramData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Coverage Share Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">No coverage share data available</p>
        </CardContent>
      </Card>
    );
  }

  // Labels are expected to be percent ranges like "10-15%".
  const prettyBins = histogramData;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Coverage Share Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={prettyBins} margin={{ top: 20, right: 30, left: 20, bottom: 50 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="bin"
              angle={-35}
              textAnchor="end"
              height={60}
              interval="preserveStartEnd"
              tick={{ fontSize: 10 }}
            />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

