import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface ConstructFrequencyParetoChartProps {
  data: Array<{
    rank: number;
    constructId: string;
    count: number;
    share: number;
    cumulativeShare: number;
  }>;
  showCard?: boolean;
  title?: string;
}

export function ConstructFrequencyParetoChart({
  data,
  showCard = true,
  title = 'Construct Concentration (Pareto)',
}: ConstructFrequencyParetoChartProps) {
  if (!data || data.length === 0) {
    if (!showCard) {
      return <p className="text-muted-foreground text-center py-8">No frequency data available</p>;
    }
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">No frequency data available</p>
        </CardContent>
      </Card>
    );
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || payload.length === 0) return null;
    const row = payload[0]?.payload;
    return (
      <div className="bg-background border rounded-lg shadow-lg p-3 max-w-[360px]">
        <p className="font-medium">Rank #{row.rank}</p>
        <p className="text-sm font-mono break-all">{row.constructId}</p>
        <p className="text-sm">Count: {row.count.toLocaleString()}</p>
        <p className="text-sm">Cumulative: {(row.cumulativeShare * 100).toFixed(1)}%</p>
      </div>
    );
  };

  const content = (
    <>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 20, right: 30, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="rank" tickFormatter={(v) => `${v}`} />
          <YAxis domain={[0, 1]} tickFormatter={(v) => `${Math.round(v * 100)}%`} />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="cumulativeShare"
            name="Cumulative share"
            stroke="#8b5cf6"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
      <p className="text-xs text-muted-foreground mt-2">
        Shows how quickly a small set of constructs accounts for most occurrences (long-tail vs concentrated datasets).
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

