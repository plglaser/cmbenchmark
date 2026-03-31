import { Badge } from './ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { CheckCircle2, Loader2, XCircle } from 'lucide-react';

type DetailItem = {
  label: string;
  value: number | string;
};

interface StageProgressCardProps {
  title: string;
  status: string;
  phase?: string;
  message?: string;
  percentage?: number | null;
  processed?: number;
  total?: number;
  unitLabel?: string;
  details?: DetailItem[];
}

const getStatusVariant = (status: string): 'default' | 'secondary' | 'destructive' | 'outline' => {
  if (status === 'completed') return 'default';
  if (status === 'failed' || status === 'cancelled') return 'destructive';
  if (status === 'cancel_requested') return 'secondary';
  return 'outline';
};

const getStatusIcon = (status: string) => {
  if (status === 'completed') return <CheckCircle2 className="h-4 w-4 text-green-600" />;
  if (status === 'failed' || status === 'cancelled') return <XCircle className="h-4 w-4 text-destructive" />;
  return <Loader2 className="h-4 w-4 animate-spin text-primary" />;
};

export function StageProgressCard({
  title,
  status,
  phase,
  message,
  percentage,
  processed,
  total,
  unitLabel = 'items',
  details = [],
}: StageProgressCardProps) {
  const computedPercent =
    typeof percentage === 'number'
      ? percentage
      : typeof processed === 'number' && typeof total === 'number' && total > 0
        ? (processed / total) * 100
        : 0;
  const safePercent = Math.max(0, Math.min(100, computedPercent));

  return (
    <Card className="mt-4 border-primary/20 bg-gradient-to-br from-primary/5 via-background to-background">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="text-base">{title}</CardTitle>
          <div className="flex items-center gap-2">
            {getStatusIcon(status)}
            <Badge variant={getStatusVariant(status)}>{status.replace('_', ' ')}</Badge>
          </div>
        </div>
        <CardDescription>{message || 'Processing stage.'}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium capitalize">{phase || 'running'}</span>
            <span className="font-semibold tabular-nums">{safePercent.toFixed(1)}%</span>
          </div>
          <div className="relative h-3 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-gradient-to-r from-sky-500 via-cyan-500 to-emerald-500 transition-all duration-500"
              style={{ width: `${safePercent}%` }}
            />
          </div>
          {typeof processed === 'number' && typeof total === 'number' && total >= 0 && (
            <p className="text-xs text-muted-foreground tabular-nums">
              {processed} / {total} {unitLabel}
            </p>
          )}
        </div>
        {details.length > 0 && (
          <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground md:grid-cols-4">
            {details.map((item) => (
              <div key={item.label} className="rounded bg-muted/60 px-2 py-1">
                <span className="font-medium">{item.label}:</span> {item.value}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
