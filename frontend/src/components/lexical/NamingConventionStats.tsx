import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';

interface NamingConventionStatsProps {
  entropyStats: {
    min: number;
    p25: number;
    median: number;
    mean: number;
    p75: number;
    max: number;
  } | null;
  histogramData: Array<{ bin: string; count: number }>;
}

export function NamingConventionStats({ entropyStats, histogramData }: NamingConventionStatsProps) {
  if (!entropyStats && (!histogramData || histogramData.length === 0)) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Naming Style Entropy</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">No data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Naming Style Entropy</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {entropyStats && (
          <div>
            <h4 className="text-sm font-semibold mb-2">Entropy Statistics (per Model)</h4>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span>Min:</span>
                <Badge variant="outline">{entropyStats.min.toFixed(3)}</Badge>
              </div>
              <div className="flex justify-between">
                <span>P25:</span>
                <Badge variant="outline">{entropyStats.p25.toFixed(3)}</Badge>
              </div>
              <div className="flex justify-between">
                <span>Median:</span>
                <Badge variant="outline">{entropyStats.median.toFixed(3)}</Badge>
              </div>
              <div className="flex justify-between">
                <span>Mean:</span>
                <Badge variant="outline">{entropyStats.mean.toFixed(3)}</Badge>
              </div>
              <div className="flex justify-between">
                <span>P75:</span>
                <Badge variant="outline">{entropyStats.p75.toFixed(3)}</Badge>
              </div>
              <div className="flex justify-between">
                <span>Max:</span>
                <Badge variant="outline">{entropyStats.max.toFixed(3)}</Badge>
              </div>
            </div>
          </div>
        )}
        {histogramData && histogramData.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold mb-2">Entropy Distribution</h4>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={histogramData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="bin" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#8b5cf6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
