import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface FileSizeChartsProps {
  sourceHistogram: Array<{ bin: string; count: number }>;
  irHistogram: Array<{ bin: string; count: number }>;
}

export function FileSizeCharts({ sourceHistogram, irHistogram }: FileSizeChartsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Source File Size Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          {sourceHistogram.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={sourceHistogram}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="bin" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#ffc658" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-muted-foreground text-center py-8">No source size data available</p>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">IR File Size Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          {irHistogram.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={irHistogram}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="bin" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#82ca9d" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-muted-foreground text-center py-8">No IR size data available</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
