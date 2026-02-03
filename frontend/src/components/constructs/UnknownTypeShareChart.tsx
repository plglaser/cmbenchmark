import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface UnknownTypeShareChartProps {
  histogramData: Array<{ bin: string; count: number }>;
}

export function UnknownTypeShareChart({ histogramData }: UnknownTypeShareChartProps) {
  if (!histogramData || histogramData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Unknown Type Share Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">No unknown-type share data available</p>
        </CardContent>
      </Card>
    );
  }

  // Convert numeric-looking bins to % ranges when they look like shares.
  const prettyBins = histogramData.map((d) => {
    const m = String(d.bin).match(/^(-?\d+(?:\.\d+)?)-(-?\d+(?:\.\d+)?)$/);
    if (!m) return d;
    const a = Number(m[1]);
    const b = Number(m[2]);
    if (a >= 0 && b <= 1.01) {
      return { ...d, bin: `${(a * 100).toFixed(0)}-${(b * 100).toFixed(0)}%` };
    }
    return d;
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Unknown Type Share Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={prettyBins} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="bin" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" fill="#f59e0b" />
          </BarChart>
        </ResponsiveContainer>
        <p className="text-xs text-muted-foreground mt-2">
          Higher values suggest the parser encountered node/edge types not covered by the construct profile.
        </p>
      </CardContent>
    </Card>
  );
}

