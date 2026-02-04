import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';

interface LabelPresenceKPIsProps {
  data: {
    dataset_label_eligible_count: number;
    dataset_label_present_count: number;
    dataset_label_present_share: number;
    dataset_label_missing_share: number;
  } | null;
}

export function LabelPresenceKPIs({ data }: LabelPresenceKPIsProps) {
  if (!data) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Key Metrics</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex justify-between">
          <span>Eligible Labels:</span>
          <Badge variant="outline">{data.dataset_label_eligible_count.toLocaleString()}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Present Labels:</span>
          <Badge variant="outline">
            {data.dataset_label_present_count.toLocaleString()} ({(data.dataset_label_present_share * 100).toFixed(1)}%)
          </Badge>
        </div>
        <div className="flex justify-between">
          <span>Missing Labels:</span>
          <Badge variant="outline">
            {(data.dataset_label_eligible_count - data.dataset_label_present_count).toLocaleString()} ({(data.dataset_label_missing_share * 100).toFixed(1)}%)
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}
