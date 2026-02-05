import { Badge } from '../ui/badge';

interface ReadonlyListFieldProps {
  label: string;
  values?: Array<string | number> | null;
  emptyText?: string;
  missingText?: string;
}

export function ReadonlyListField({
  label,
  values,
  emptyText = '(none)',
  missingText = 'not explicitly set (backend default may apply)',
}: ReadonlyListFieldProps) {
  const isMissing = values === undefined || values === null;
  const isEmpty = Array.isArray(values) && values.length === 0;

  return (
    <div className="space-y-1">
      <div className="text-sm font-medium">{label}</div>
      {isMissing ? (
        <Badge variant="destructive">{missingText}</Badge>
      ) : isEmpty ? (
        <div className="text-sm text-muted-foreground">{emptyText}</div>
      ) : (
        <div className="flex flex-wrap gap-2">
          {values!.map((value, idx) => (
            <span key={idx} className="px-2 py-1 bg-muted rounded text-sm font-mono">
              {String(value)}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
