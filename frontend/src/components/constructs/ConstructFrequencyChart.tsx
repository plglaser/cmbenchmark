import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface ConstructFrequencyChartProps {
  data: Array<{
    constructId: string;
    count: number;
    share?: number;
    group?: string;
    description?: string;
    kind?: string;
  }>;
  showCard?: boolean;
  title?: string;
}

export function ConstructFrequencyChart({
  data,
  showCard = true,
  title = 'Construct Frequency',
}: ConstructFrequencyChartProps) {
  if (!data || data.length === 0) {
    if (!showCard) {
      return <p className="text-muted-foreground text-center py-8">No data available</p>;
    }
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">No data available</p>
        </CardContent>
      </Card>
    );
  }

  // Sort by count descending and take top 20 for readability
  const sortedData = [...data]
    .sort((a, b) => (b.count || 0) - (a.count || 0))
    .slice(0, 20)
    .map((d) => {
      const short = d.constructId?.includes(':') ? d.constructId.split(':').slice(1).join(':') : d.constructId;
      return { ...d, label: short && short.length > 18 ? `${short.slice(0, 16)}…` : short };
    });

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      return (
        <div className="bg-background border rounded-lg shadow-lg p-3">
          <p className="font-medium font-mono break-all">{data.payload.constructId}</p>
          {data.payload.group && <p className="text-sm">Group: {data.payload.group}</p>}
          {data.payload.kind && <p className="text-sm text-muted-foreground">Kind: {data.payload.kind}</p>}
          <p className="text-sm">Count: {Number(data.value || 0).toLocaleString()}</p>
          {typeof data.payload.share === 'number' && (
            <p className="text-sm">Share: {(data.payload.share * 100).toFixed(2)}%</p>
          )}
          {data.payload.description && (
            <p className="text-xs text-muted-foreground mt-2 max-w-[360px]">{data.payload.description}</p>
          )}
        </div>
      );
    }
    return null;
  };

  const content = (
    <>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={sortedData}
          margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="label"
            angle={-45}
            textAnchor="end"
            height={100}
            tick={{ fontSize: 10 }}
          />
          <YAxis />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Bar dataKey="count" fill="#3b82f6" />
        </BarChart>
      </ResponsiveContainer>
      <p className="text-xs text-muted-foreground mt-2">
        Top 20 constructs by total occurrences. Hover for full IDs and metadata.
      </p>
    </>
  );

  if (!showCard) {
    return content;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>{content}</CardContent>
    </Card>
  );
}
