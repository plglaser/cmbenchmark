import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { ConstructProfileDialog } from './ConstructProfileDialog';

interface ConstructPresenceKPIsProps {
  data: {
    constructs_available_count: number;
    constructs_observed_count: number;
    coverage_share: number;
    unknown_type_share_dataset: number;
    unknown_node_type_count_dataset?: number;
    unknown_edge_type_count_dataset?: number;
    coverage_share_stats?: {
      median: number;
      mean: number;
    };
  } | null;
  constructCatalog?: Record<string, any> | null;
  parserLanguage?: string | null;
}

export function ConstructPresenceKPIs({ data, constructCatalog, parserLanguage }: ConstructPresenceKPIsProps) {
  if (!data) return null;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="text-base">Key Metrics</CardTitle>
          <ConstructProfileDialog constructCatalog={constructCatalog} parserLanguage={parserLanguage} />
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex justify-between">
          <span>Available Constructs:</span>
          <Badge variant="outline">{data.constructs_available_count.toLocaleString()}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Observed Constructs:</span>
          <Badge variant="outline">
            {data.constructs_observed_count.toLocaleString()} ({(data.coverage_share * 100).toFixed(1)}%)
          </Badge>
        </div>
        <div className="flex justify-between">
          <span>Missing Constructs:</span>
          <Badge variant="outline">
            {(data.constructs_available_count - data.constructs_observed_count).toLocaleString()} ({((1 - data.coverage_share) * 100).toFixed(1)}%)
          </Badge>
        </div>
        {data.coverage_share_stats && (
          <>
            <div className="flex justify-between">
              <span>Median Model Coverage:</span>
              <Badge variant="outline">
                {(data.coverage_share_stats.median * 100).toFixed(1)}%
              </Badge>
            </div>
            <div className="flex justify-between">
              <span>Mean Model Coverage:</span>
              <Badge variant="outline">
                {(data.coverage_share_stats.mean * 100).toFixed(1)}%
              </Badge>
            </div>
          </>
        )}
        <div className="flex justify-between">
          <span>Unknown Types Share:</span>
          <Badge variant="outline">
            {(data.unknown_type_share_dataset * 100).toFixed(1)}%
          </Badge>
        </div>
        {(typeof data.unknown_node_type_count_dataset === 'number' ||
          typeof data.unknown_edge_type_count_dataset === 'number') && (
          <>
            <div className="flex justify-between">
              <span>Unknown Node Types (count):</span>
              <Badge variant="outline">{(data.unknown_node_type_count_dataset ?? 0).toLocaleString()}</Badge>
            </div>
            <div className="flex justify-between">
              <span>Unknown Edge Types (count):</span>
              <Badge variant="outline">{(data.unknown_edge_type_count_dataset ?? 0).toLocaleString()}</Badge>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
