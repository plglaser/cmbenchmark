import { useEffect, useMemo, useState } from 'react';
import { Info } from 'lucide-react';
import { apiService } from '../../services/api';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { ScrollArea } from '../ui/scroll-area';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Tooltip, TooltipContent, TooltipTrigger } from '../ui/tooltip';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';

type ConstructProfileJson = {
  language?: string;
  constructs?: Array<{
    id: string;
    kind: string;
    match_type: string;
    match_data_equals?: Record<string, any>;
    meta?: Record<string, any>;
    description?: string;
  }>;
};

function inferParserLanguageFromCatalog(catalog?: Record<string, any>): string | null {
  const keys = catalog ? Object.keys(catalog) : [];
  const first = keys[0];
  if (!first) return null;
  if (first.startsWith('ecore:')) return 'Ecore';
  if (first.startsWith('archimate:')) return 'ArchiMate-Archi';
  return null;
}

function getGroup(meta?: Record<string, any>): string {
  if (!meta) return '—';
  return meta.layer || meta.group || meta.relationship_group || meta.category || '—';
}

function metaForDisplay(meta?: Record<string, any>): Record<string, any> | null {
  if (!meta) return null;
  // These keys are already shown in the "Group" column (or are purely categorization).
  const { layer, group, relationship_group, category, ...rest } = meta;
  return Object.keys(rest).length > 0 ? rest : null;
}

export function ConstructProfileDialog({
  constructCatalog,
  parserLanguage,
}: {
  constructCatalog?: Record<string, any> | null;
  parserLanguage?: string | null;
}) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useState<ConstructProfileJson | null>(null);
  const [query, setQuery] = useState('');

  const effectiveParserLanguage =
    parserLanguage || inferParserLanguageFromCatalog(constructCatalog || undefined);

  useEffect(() => {
    if (!open) return;
    if (profile || loading) return;
    if (!effectiveParserLanguage) {
      setError('Could not infer parser language for construct profile.');
      return;
    }

    setLoading(true);
    setError(null);
    apiService
      .getConstructProfile(effectiveParserLanguage)
      .then((data) => setProfile(data))
      .catch((e: any) => setError(e?.response?.data?.detail || e?.message || 'Failed to load construct profile'))
      .finally(() => setLoading(false));
  }, [open, profile, loading, effectiveParserLanguage]);

  const constructs = profile?.constructs || [];

  const stats = useMemo(() => {
    const groupCounts: Record<string, number> = {};
    const kindCounts: Record<string, number> = {};
    constructs.forEach((c) => {
      const g = getGroup(c.meta);
      groupCounts[g] = (groupCounts[g] || 0) + 1;
      kindCounts[c.kind] = (kindCounts[c.kind] || 0) + 1;
    });
    const groups = Object.keys(groupCounts).length;
    return { groups, groupCounts, kindCounts };
  }, [constructs]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return constructs;
    return constructs.filter((c) => {
      const hay = `${c.id} ${c.kind} ${c.match_type} ${getGroup(c.meta)} ${c.description || ''} ${JSON.stringify(c.match_data_equals || {})} ${JSON.stringify(c.meta || {})}`.toLowerCase();
      return hay.includes(q);
    });
  }, [constructs, query]);

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      const ga = getGroup(a.meta);
      const gb = getGroup(b.meta);
      if (ga !== gb) return ga.localeCompare(gb);
      if (a.kind !== b.kind) return a.kind.localeCompare(b.kind);
      return a.id.localeCompare(b.id);
    });
  }, [filtered]);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <Tooltip>
        <TooltipTrigger asChild>
          <DialogTrigger asChild>
            <Button variant="outline" size="icon" aria-label="Show construct profile">
              <Info className="h-4 w-4" />
            </Button>
          </DialogTrigger>
        </TooltipTrigger>
        <TooltipContent sideOffset={6}>Show construct profile (catalog + match rules)</TooltipContent>
      </Tooltip>

      <DialogContent className="w-[95vw] max-w-6xl max-h-[85vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle>Construct Profile</DialogTitle>
          <DialogDescription>
            {effectiveParserLanguage ? (
              <span>
                Source: <span className="font-mono">{effectiveParserLanguage}</span>
              </span>
            ) : (
              'Source: unknown'
            )}
          </DialogDescription>
        </DialogHeader>

        {loading && <p className="text-sm text-muted-foreground">Loading construct profile…</p>}
        {error && (
          <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
            {error}
          </div>
        )}

        {profile && (
          <div className="space-y-3 min-h-0">
            <div className="flex flex-wrap gap-2 items-center">
              <Badge variant="outline">Language: {profile.language || '—'}</Badge>
              <Badge variant="outline">Constructs: {constructs.length.toLocaleString()}</Badge>
              <Badge variant="outline">Groups: {stats.groups.toLocaleString()}</Badge>
            </div>

            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Filter (id, group/layer, kind, match_type, meta, description)…"
            />

            <ScrollArea className="h-[60vh] border rounded-md">
              <Table className="table-fixed">
                <TableHeader>
                  <TableRow>
                    <TableHead>Group</TableHead>
                    <TableHead>Construct</TableHead>
                    <TableHead>Match</TableHead>
                    <TableHead>Description</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sorted.length > 0 ? (
                    sorted.map((c) => {
                      const group = getGroup(c.meta);
                      const matchDataObj =
                        c.match_data_equals && Object.keys(c.match_data_equals).length > 0
                          ? c.match_data_equals
                          : null;
                      const metaObj = metaForDisplay(c.meta);
                      return (
                        <TableRow key={c.id}>
                          <TableCell className="whitespace-nowrap align-top w-[140px]">{group}</TableCell>
                          <TableCell className="align-top w-[320px] whitespace-normal">
                            <div className="font-mono text-sm break-all">{c.id}</div>
                            <div className="text-xs text-muted-foreground">{c.kind}</div>
                          </TableCell>
                          <TableCell className="text-sm align-top w-[360px] whitespace-normal">
                            <div className="font-mono break-all">{c.match_type}</div>
                            {matchDataObj && (
                              <div className="text-xs text-muted-foreground break-all mt-1">
                                data={JSON.stringify(matchDataObj)}
                              </div>
                            )}
                            {metaObj && (
                              <div className="text-xs text-muted-foreground break-all mt-1">
                                meta={JSON.stringify(metaObj)}
                              </div>
                            )}
                          </TableCell>
                          <TableCell className="text-sm align-top whitespace-normal">
                            {c.description ? c.description : <span className="text-muted-foreground">—</span>}
                          </TableCell>
                        </TableRow>
                      );
                    })
                  ) : (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center text-muted-foreground">
                        No matches
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </ScrollArea>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

