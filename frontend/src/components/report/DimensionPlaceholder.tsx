import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';

interface DimensionPlaceholderProps {
  name: string;
  description?: string;
}

export function DimensionPlaceholder({ name, description }: DimensionPlaceholderProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{name}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground text-center py-8">
          This dimension is coming soon. Measures will be displayed here once implemented.
        </p>
      </CardContent>
    </Card>
  );
}
