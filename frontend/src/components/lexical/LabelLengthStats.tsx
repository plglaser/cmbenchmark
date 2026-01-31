import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';

interface LabelLengthStatsProps {
  data: {
    label_length_chars_median_stats: {
      min: number;
      p25: number;
      median: number;
      mean: number;
      p75: number;
      max: number;
    };
    label_length_tokens_median_stats: {
      min: number;
      p25: number;
      median: number;
      mean: number;
      p75: number;
      max: number;
    };
  } | null;
}

export function LabelLengthStats({ data }: LabelLengthStatsProps) {
  if (!data) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Length Statistics</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h4 className="text-sm font-semibold mb-2">Characters (Median per Model)</h4>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span>Min:</span>
              <Badge variant="outline">{data.label_length_chars_median_stats.min.toFixed(1)}</Badge>
            </div>
            <div className="flex justify-between">
              <span>P25:</span>
              <Badge variant="outline">{data.label_length_chars_median_stats.p25.toFixed(1)}</Badge>
            </div>
            <div className="flex justify-between">
              <span>Median:</span>
              <Badge variant="outline">{data.label_length_chars_median_stats.median.toFixed(1)}</Badge>
            </div>
            <div className="flex justify-between">
              <span>Mean:</span>
              <Badge variant="outline">{data.label_length_chars_median_stats.mean.toFixed(1)}</Badge>
            </div>
            <div className="flex justify-between">
              <span>P75:</span>
              <Badge variant="outline">{data.label_length_chars_median_stats.p75.toFixed(1)}</Badge>
            </div>
            <div className="flex justify-between">
              <span>Max:</span>
              <Badge variant="outline">{data.label_length_chars_median_stats.max.toFixed(1)}</Badge>
            </div>
          </div>
        </div>
        <div>
          <h4 className="text-sm font-semibold mb-2">Tokens (Median per Model)</h4>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span>Min:</span>
              <Badge variant="outline">{data.label_length_tokens_median_stats.min.toFixed(1)}</Badge>
            </div>
            <div className="flex justify-between">
              <span>P25:</span>
              <Badge variant="outline">{data.label_length_tokens_median_stats.p25.toFixed(1)}</Badge>
            </div>
            <div className="flex justify-between">
              <span>Median:</span>
              <Badge variant="outline">{data.label_length_tokens_median_stats.median.toFixed(1)}</Badge>
            </div>
            <div className="flex justify-between">
              <span>Mean:</span>
              <Badge variant="outline">{data.label_length_tokens_median_stats.mean.toFixed(1)}</Badge>
            </div>
            <div className="flex justify-between">
              <span>P75:</span>
              <Badge variant="outline">{data.label_length_tokens_median_stats.p75.toFixed(1)}</Badge>
            </div>
            <div className="flex justify-between">
              <span>Max:</span>
              <Badge variant="outline">{data.label_length_tokens_median_stats.max.toFixed(1)}</Badge>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
