import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';

interface LabelPresenceKPIsProps {
  data: {
    dataset_label_eligible_count: number;
    dataset_label_present_count: number;
    dataset_label_present_share: number;
    dataset_label_missing_share: number;
    label_completeness_index: number;
    completeness_category: string;
  } | null;
}

export function LabelPresenceKPIs({ data }: LabelPresenceKPIsProps) {
  if (!data) return null;

  const getCategoryColor = (category: string) => {
    switch (category.toLowerCase()) {
      case 'high':
        return 'bg-green-500/10 text-green-700 dark:text-green-400';
      case 'moderate':
        return 'bg-yellow-500/10 text-yellow-700 dark:text-yellow-400';
      case 'low':
        return 'bg-red-500/10 text-red-700 dark:text-red-400';
      default:
        return 'bg-gray-500/10 text-gray-700 dark:text-gray-400';
    }
  };

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
        <div className="flex justify-between">
          <span>Completeness Index:</span>
          <Badge variant="outline">{data.label_completeness_index.toFixed(3)}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Completeness Category:</span>
          <Badge className={getCategoryColor(data.completeness_category)}>
            {data.completeness_category.toUpperCase()}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}
