import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '../ui/collapsible';

interface ConfigCardProps {
  title: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
  subtitle?: string;
}

export function ConfigCard({ title, open, onOpenChange, children, subtitle }: ConfigCardProps) {
  return (
    <Collapsible open={open} onOpenChange={onOpenChange}>
      <div className="rounded-md border">
        <CollapsibleTrigger asChild>
          <button
            type="button"
            className="w-full flex items-center justify-between px-4 py-3 text-sm font-semibold"
          >
            <span>{title}</span>
            <span className="text-xs text-muted-foreground">{open ? 'Hide' : 'Show'}</span>
          </button>
        </CollapsibleTrigger>
        <CollapsibleContent className="px-4 pb-4 space-y-3">
          {subtitle && <div className="text-sm text-muted-foreground">{subtitle}</div>}
          {children}
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}
