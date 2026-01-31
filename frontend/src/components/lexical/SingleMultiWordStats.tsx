import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';

interface SingleMultiWordStatsProps {
  datasetData: {
    total_single_word_labels: number;
    total_multi_word_labels: number;
    dataset_share_single_word_labels: number;
  } | null;
  shareStats: {
    min: number;
    p25: number;
    median: number;
    mean: number;
    p75: number;
    max: number;
  } | null;
  histogramData: Array<{ bin: string; count: number }>;
}

export function SingleMultiWordStats({ datasetData, shareStats, histogramData }: SingleMultiWordStatsProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Statistics</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {datasetData && (
          <div>
            <h4 className="text-sm font-semibold mb-2">Dataset Totals</h4>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span>Single Word Labels:</span>
                <Badge variant="outline">{datasetData.total_single_word_labels.toLocaleString()}</Badge>
              </div>
              <div className="flex justify-between">
                <span>Multi Word Labels:</span>
                <Badge variant="outline">{datasetData.total_multi_word_labels.toLocaleString()}</Badge>
              </div>
              <div className="flex justify-between">
                <span>Single Word Share:</span>
                <Badge variant="outline">{(datasetData.dataset_share_single_word_labels * 100).toFixed(1)}%</Badge>
              </div>
            </div>
          </div>
        )}
        {shareStats && (
          <div>
            <h4 className="text-sm font-semibold mb-2">Single Word Share (per Model)</h4>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span>Min:</span>
                <Badge variant="outline">{(shareStats.min * 100).toFixed(1)}%</Badge>
              </div>
              <div className="flex justify-between">
                <span>P25:</span>
                <Badge variant="outline">{(shareStats.p25 * 100).toFixed(1)}%</Badge>
              </div>
              <div className="flex justify-between">
                <span>Median:</span>
                <Badge variant="outline">{(shareStats.median * 100).toFixed(1)}%</Badge>
              </div>
              <div className="flex justify-between">
                <span>Mean:</span>
                <Badge variant="outline">{(shareStats.mean * 100).toFixed(1)}%</Badge>
              </div>
              <div className="flex justify-between">
                <span>P75:</span>
                <Badge variant="outline">{(shareStats.p75 * 100).toFixed(1)}%</Badge>
              </div>
              <div className="flex justify-between">
                <span>Max:</span>
                <Badge variant="outline">{(shareStats.max * 100).toFixed(1)}%</Badge>
              </div>
            </div>
          </div>
        )}
        {histogramData.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold mb-2">Single Word Share Distribution</h4>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={histogramData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="bin" />
                <YAxis />
                <Tooltip formatter={(value: any) => `${value} models`} />
                <Bar dataKey="count" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
