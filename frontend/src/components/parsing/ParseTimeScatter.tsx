import { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface ParseTimeScatterProps {
  data: Array<{ fileSize: number; parseTime: number }>;
}

export function ParseTimeScatter({ data }: ParseTimeScatterProps) {
  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">File Size vs Parse Time</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">No scatter plot data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">File Size vs Parse Time</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <CartesianGrid />
            <XAxis type="number" dataKey="fileSize" name="File Size (bytes)" unit=" bytes" />
            <YAxis type="number" dataKey="parseTime" name="Parse Time" unit=" ms" />
            <Tooltip cursor={{ strokeDasharray: '3 3' }} />
            <Scatter dataKey="parseTime" data={data} fill="#8884d8" />
          </ScatterChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
