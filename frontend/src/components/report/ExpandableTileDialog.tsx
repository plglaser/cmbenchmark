import { ReactNode, useState } from 'react';
import { Maximize2 } from 'lucide-react';
import { Button } from '../ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';

export function ExpandableTileDialog({
  title,
  children,
  dialogClassName,
}: {
  title: string;
  children: ReactNode;
  dialogClassName?: string;
}) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <div className="relative min-w-0">
        <div className="absolute right-2 top-2 z-10">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="h-8 w-8 border bg-background/80 backdrop-blur"
            onClick={() => setOpen(true)}
            aria-label={`Expand ${title}`}
          >
            <Maximize2 className="h-4 w-4" />
          </Button>
        </div>

        {children}
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent
          className={
            dialogClassName ?? 'w-[95vw] max-w-6xl max-h-[90vh] overflow-auto'
          }
        >
          <DialogHeader>
            <DialogTitle>{title}</DialogTitle>
          </DialogHeader>

          {/* Re-use the same tile content in the dialog */}
          <div className="min-w-0">{children}</div>
        </DialogContent>
      </Dialog>
    </>
  );
}

