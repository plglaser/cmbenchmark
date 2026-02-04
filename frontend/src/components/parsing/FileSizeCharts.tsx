import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface FileSizeChartsProps {
  sourceHistogram: Array<{ bin: string; count: number }>;
  irHistogram: Array<{ bin: string; count: number }>;
}

export function FileSizeCharts({ sourceHistogram, irHistogram }: FileSizeChartsProps) {
  const formatBytes = (bytes: number): string => {
    if (!Number.isFinite(bytes)) {
      return '-';
    }
    if (bytes < 1024) {
      return `${Math.round(bytes)} B`;
    }
    const units = ['KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let unitIndex = -1;
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex += 1;
    }
    const precision = size >= 100 ? 0 : size >= 10 ? 1 : 2;
    return `${size.toFixed(precision)} ${units[unitIndex]}`;
  };

  const formatBinLabel = (bin: string): string => {
    const parts = bin.split('-').map((part) => Number(part));
    if (parts.length === 2 && parts.every((value) => Number.isFinite(value))) {
      return `${formatBytes(parts[0])} - ${formatBytes(parts[1])}`;
    }
    const single = Number(bin);
    return Number.isFinite(single) ? formatBytes(single) : bin;
  };

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
                <XAxis dataKey="bin" tickFormatter={formatBinLabel} />
                <YAxis />
                <Tooltip labelFormatter={(label) => formatBinLabel(String(label))} />
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
                <XAxis dataKey="bin" tickFormatter={formatBinLabel} />
                <YAxis />
                <Tooltip labelFormatter={(label) => formatBinLabel(String(label))} />
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
