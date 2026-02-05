import { Badge } from '../ui/badge';

interface ReadonlyFieldProps {
  label: string;
  value: string | number | boolean | null | undefined;
  missingText?: string;
}

export function ReadonlyField({
  label,
  value,
  missingText = 'not explicitly set (backend default may apply)',
}: ReadonlyFieldProps) {
  const isMissing =
    value === null ||
    value === undefined ||
    (typeof value === 'string' && value.trim() === '');

  return (
    <div className="space-y-1">
      <div className="text-sm font-medium">{label}</div>
      {isMissing ? (
        <Badge variant="destructive">{missingText}</Badge>
      ) : typeof value === 'boolean' ? (
        <Badge variant={value ? 'success' : 'secondary'}>
          {value ? 'Yes' : 'No'}
        </Badge>
      ) : (
        <div className="text-sm font-mono break-all">{String(value)}</div>
      )}
    </div>
  );
}
