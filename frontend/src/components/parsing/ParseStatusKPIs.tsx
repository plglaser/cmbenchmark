import { Badge } from '../ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface ParseStatusKPIsProps {
  parseStatus: {
    n_models: number;
    n_success: number;
    n_partial: number;
    n_failed: number;
    share_success: number;
    share_partial: number;
    share_failed: number;
    parsing_robustness_index: number;
  } | null;
}

export function ParseStatusKPIs({ parseStatus }: ParseStatusKPIsProps) {
  if (!parseStatus) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">KPI Metrics</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex justify-between">
          <span>Total Models:</span>
          <Badge variant="outline">{parseStatus.n_models}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Success:</span>
          <Badge variant="outline">
            {parseStatus.n_success} ({(parseStatus.share_success * 100).toFixed(1)}%)
          </Badge>
        </div>
        <div className="flex justify-between">
          <span>Partial:</span>
          <Badge variant="outline">
            {parseStatus.n_partial} ({(parseStatus.share_partial * 100).toFixed(1)}%)
          </Badge>
        </div>
        <div className="flex justify-between">
          <span>Failed:</span>
          <Badge variant="outline">
            {parseStatus.n_failed} ({(parseStatus.share_failed * 100).toFixed(1)}%)
          </Badge>
        </div>
        <div className="flex justify-between">
          <span>Robustness Index:</span>
          <Badge variant="outline">{parseStatus.parsing_robustness_index.toFixed(3)}</Badge>
        </div>
      </CardContent>
    </Card>
  );
}
