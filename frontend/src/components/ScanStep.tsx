import { useState, useMemo } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ScrollArea } from './ui/scroll-area';
import { ChevronDown, ChevronRight, FileText, CheckCircle, EyeOff, FileX, Ban } from 'lucide-react';
import { apiService } from '../services/api';
import type { ScanResponse } from '../types/api';
import type { BenchmarkProfile } from '../types/profile';
import { ReadonlyField } from './profile/ReadonlyField';
import { ReadonlyListField } from './profile/ReadonlyListField';
import { ConfigCard } from './profile/ConfigCard';

interface ScanStepProps {
  onScanComplete: (result: ScanResponse) => void;
  profile: BenchmarkProfile | null;
}

export function ScanStep({ onScanComplete, profile }: ScanStepProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScanResponse | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [configOpen, setConfigOpen] = useState(true);
  const [filterCandidates, setFilterCandidates] = useState('');
  const [filterUnreadable, setFilterUnreadable] = useState('');
  const [filterTooLarge, setFilterTooLarge] = useState('');
  const [filterExcluded, setFilterExcluded] = useState('');
  const [filterDuplicates, setFilterDuplicates] = useState('');

  const countDuplicateFiles = (groups: { count: number }[]) =>
    groups.reduce((sum, group) => sum + group.count, 0);

  const totals = result?.totals;
  const duplicateFileCount = result ? countDuplicateFiles(result.duplicates_groups) : 0;

  // Memoized filtered lists
  const filteredCandidates = useMemo(() => {
    if (!result) return [];
    return result.candidates.filter((file) =>
      file.toLowerCase().includes(filterCandidates.toLowerCase())
    );
  }, [result, filterCandidates]);

  const filteredUnreadable = useMemo(() => {
    if (!result) return [];
    return result.unreadable.filter((file) =>
      file.toLowerCase().includes(filterUnreadable.toLowerCase())
    );
  }, [result, filterUnreadable]);

  const filteredTooLarge = useMemo(() => {
    if (!result) return [];
    return result.too_large.filter((file) =>
      file.toLowerCase().includes(filterTooLarge.toLowerCase())
    );
  }, [result, filterTooLarge]);

  const filteredExcluded = useMemo(() => {
    if (!result) return [];
    return result.filtered.filter((file) =>
      file.toLowerCase().includes(filterExcluded.toLowerCase())
    );
  }, [result, filterExcluded]);

  const filteredDuplicatesGroups = useMemo(() => {
    if (!result) return [];
    return result.duplicates_groups
      .map((group) => ({
        ...group,
        members: group.members.filter((file) =>
          file.toLowerCase().includes(filterDuplicates.toLowerCase())
        ),
      }))
      .filter((group) => group.members.length > 0);
  }, [result, filterDuplicates]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (!profile) {
        throw new Error('Load a benchmark profile to run the scan.');
      }
      const response = await apiService.scan({
        profile,
      });
      setResult(response);
      onScanComplete(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to scan dataset');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Step 1: Scan Dataset</CardTitle>
        <CardDescription>
          Scan a dataset directory for model files and generate statistics
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {!profile && (
            <div className="p-3 text-sm text-muted-foreground bg-muted rounded-md">
              Upload a benchmark profile to view parameters and run the scan.
            </div>
          )}

          {profile && (
            <div className="space-y-4">
              <ConfigCard title="Scan Configuration" open={configOpen} onOpenChange={setConfigOpen}>
                <ReadonlyField label="Dataset Path" value={profile.scan?.dataset_path} />
                <ReadonlyField label="Output Directory" value={profile.output_path} />
                <ReadonlyListField label="Include Patterns" values={profile.scan?.include ?? undefined} />
                <ReadonlyListField label="Exclude Patterns" values={profile.scan?.exclude ?? undefined} />
                <ReadonlyField label="Size Limit MB" value={profile.scan?.size_limit_mb ?? undefined} />
              </ConfigCard>
            </div>
          )}

          {error && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
              {error}
            </div>
          )}

          <Button type="submit" disabled={loading || !profile || result !== null}>
            {loading ? 'Scanning...' : 'Scan Dataset'}
          </Button>
        </form>

        {result && totals && (
          <div className="mt-6 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Total Seen</p>
                      <p className="text-2xl font-bold">{totals.total_seen}</p>
                    </div>
                    <FileText className="h-8 w-8 text-muted-foreground" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Candidates</p>
                      <p className="text-2xl font-bold text-green-600">{totals.candidates}</p>
                    </div>
                    <CheckCircle className="h-8 w-8 text-green-600" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Unreadable</p>
                      <p className="text-2xl font-bold text-yellow-600">{totals.unreadable}</p>
                    </div>
                    <EyeOff className="h-8 w-8 text-yellow-600" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Too Large</p>
                      <p className="text-2xl font-bold text-orange-600">{totals.too_large}</p>
                    </div>
                    <FileX className="h-8 w-8 text-orange-600" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Filtered</p>
                      <p className="text-2xl font-bold text-red-600">{totals.filtered}</p>
                    </div>
                    <Ban className="h-8 w-8 text-red-600" />
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Scan Summary</CardTitle>
                  <CardDescription>Key paths and scan metadata</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="space-y-1 text-sm">
                    <div className="flex items-center justify-between gap-4">
                      <span className="text-muted-foreground">Dataset Root</span>
                      <code className="font-mono text-xs">{result.dataset_root}</code>
                    </div>
                    <div className="flex items-center justify-between gap-4">
                      <span className="text-muted-foreground">Scanned At</span>
                      <span>{new Date(result.scanned_at).toLocaleString()}</span>
                    </div>
                    <div className="flex items-center justify-between gap-4">
                      <span className="text-muted-foreground">Dataset Info</span>
                      <code className="font-mono text-xs">
                        {(result.parameters as any).dataset_info_path || `${result.dataset_root}/dataset_info.json`}
                      </code>
                    </div>
                    {result.parameters.out && (
                      <div className="flex items-center justify-between gap-4">
                        <span className="text-muted-foreground">Output Dir</span>
                        <code className="font-mono text-xs">{result.parameters.out}</code>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Scan Breakdown</CardTitle>
                  <CardDescription>Distribution of scanned files</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {[
                    { label: 'Candidates', count: totals.candidates, color: 'bg-green-600' },
                    { label: 'Unreadable', count: totals.unreadable, color: 'bg-yellow-600' },
                    { label: 'Too Large', count: totals.too_large, color: 'bg-yellow-600' },
                    { label: 'Filtered', count: totals.filtered, color: 'bg-red-600' },
                  ].map((item) => {
                    const percentage = totals.total_seen > 0 ? (item.count / totals.total_seen) * 100 : 0;
                    return (
                      <div key={item.label}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">{item.label}</span>
                          <span className="text-sm text-muted-foreground">
                            {item.count} ({percentage.toFixed(1)}%)
                          </span>
                        </div>
                        <div className="w-full bg-muted rounded-full h-3 overflow-hidden">
                          <div className={`${item.color} h-full`} style={{ width: `${percentage}%` }} />
                        </div>
                      </div>
                    );
                  })}
                  <div className="pt-2 border-t text-sm text-muted-foreground">
                    Duplicates: {result.duplicates_groups.length} {result.duplicates_groups.length === 1 ? 'group' : 'groups'} ({duplicateFileCount}{' '}
                    {duplicateFileCount === 1 ? 'file' : 'files'})
                  </div>
                </CardContent>
              </Card>
            </div>

            {Object.keys(result.extensions).length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>File Extensions</CardTitle>
                  <CardDescription>Counts grouped by extension</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(result.extensions).map(([ext, count]) => (
                      <span key={ext} className="px-2 py-1 bg-muted rounded text-sm">
                        {ext}: {count}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            <Collapsible open={detailsOpen} onOpenChange={setDetailsOpen}>
              <CollapsibleTrigger asChild>
                <Button variant="outline" className="w-full justify-between">
                  <span>Details</span>
                  {detailsOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-4">
                <Tabs defaultValue="candidates" className="w-full">
                  <TabsList className="grid w-full grid-cols-5">
                    <TabsTrigger value="candidates">
                      Candidates ({result.totals.candidates})
                    </TabsTrigger>
                    <TabsTrigger value="unreadable">
                      Unreadable ({result.totals.unreadable})
                    </TabsTrigger>
                    <TabsTrigger value="too_large">
                      Too Large ({result.totals.too_large})
                    </TabsTrigger>
                    <TabsTrigger value="excluded">
                      Excluded ({result.totals.filtered})
                    </TabsTrigger>
                    <TabsTrigger value="duplicates">
                      Duplicates ({result.duplicates_groups.length})
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="candidates" className="mt-4">
                    <div className="space-y-2">
                      <Input
                        placeholder="Filter candidates..."
                        value={filterCandidates}
                        onChange={(e) => setFilterCandidates(e.target.value)}
                        className="font-mono"
                      />
                      <ScrollArea className="h-[400px] rounded-md border p-4">
                        <div className="space-y-1">
                          {filteredCandidates.length > 0 ? (
                            filteredCandidates.map((file, index) => (
                              <div key={index} className="text-sm font-mono py-1 px-2 hover:bg-muted rounded">
                                {file}
                              </div>
                            ))
                          ) : (
                            <div className="text-sm text-muted-foreground py-4 text-center">
                              No files found
                            </div>
                          )}
                        </div>
                      </ScrollArea>
                    </div>
                  </TabsContent>

                  <TabsContent value="unreadable" className="mt-4">
                    <div className="space-y-2">
                      <Input
                        placeholder="Filter unreadable files..."
                        value={filterUnreadable}
                        onChange={(e) => setFilterUnreadable(e.target.value)}
                        className="font-mono"
                      />
                      <ScrollArea className="h-[400px] rounded-md border p-4">
                        <div className="space-y-1">
                          {filteredUnreadable.length > 0 ? (
                            filteredUnreadable.map((file, index) => (
                              <div key={index} className="text-sm font-mono py-1 px-2 hover:bg-muted rounded">
                                {file}
                              </div>
                            ))
                          ) : (
                            <div className="text-sm text-muted-foreground py-4 text-center">
                              No files found
                            </div>
                          )}
                        </div>
                      </ScrollArea>
                    </div>
                  </TabsContent>

                  <TabsContent value="too_large" className="mt-4">
                    <div className="space-y-2">
                      <Input
                        placeholder="Filter too large files..."
                        value={filterTooLarge}
                        onChange={(e) => setFilterTooLarge(e.target.value)}
                        className="font-mono"
                      />
                      <ScrollArea className="h-[400px] rounded-md border p-4">
                        <div className="space-y-1">
                          {filteredTooLarge.length > 0 ? (
                            filteredTooLarge.map((file, index) => (
                              <div key={index} className="text-sm font-mono py-1 px-2 hover:bg-muted rounded">
                                {file}
                              </div>
                            ))
                          ) : (
                            <div className="text-sm text-muted-foreground py-4 text-center">
                              No files found
                            </div>
                          )}
                        </div>
                      </ScrollArea>
                    </div>
                  </TabsContent>

                  <TabsContent value="excluded" className="mt-4">
                    <div className="space-y-2">
                      <Input
                        placeholder="Filter excluded files..."
                        value={filterExcluded}
                        onChange={(e) => setFilterExcluded(e.target.value)}
                        className="font-mono"
                      />
                      <ScrollArea className="h-[400px] rounded-md border p-4">
                        <div className="space-y-1">
                          {filteredExcluded.length > 0 ? (
                            filteredExcluded.map((file, index) => (
                              <div key={index} className="text-sm font-mono py-1 px-2 hover:bg-muted rounded">
                                {file}
                              </div>
                            ))
                          ) : (
                            <div className="text-sm text-muted-foreground py-4 text-center">
                              No files found
                            </div>
                          )}
                        </div>
                      </ScrollArea>
                    </div>
                  </TabsContent>

                  <TabsContent value="duplicates" className="mt-4">
                    <div className="space-y-2">
                      <Input
                        placeholder="Filter duplicate files..."
                        value={filterDuplicates}
                        onChange={(e) => setFilterDuplicates(e.target.value)}
                        className="font-mono"
                      />
                      <ScrollArea className="h-[400px] rounded-md border p-4">
                        <div className="space-y-4">
                          {filteredDuplicatesGroups.length > 0 ? (
                            filteredDuplicatesGroups.map((group, groupIndex) => (
                              <div key={groupIndex} className="space-y-1">
                                <div className="text-xs font-semibold text-muted-foreground mb-1">
                                  Group {groupIndex + 1} ({group.count} files):
                                </div>
                                {group.members.map((file, fileIndex) => (
                                  <div key={fileIndex} className="text-sm font-mono py-1 px-2 hover:bg-muted rounded ml-4">
                                    {file}
                                  </div>
                                ))}
                              </div>
                            ))
                          ) : (
                            <div className="text-sm text-muted-foreground py-4 text-center">
                              No files found
                            </div>
                          )}
                        </div>
                      </ScrollArea>
                    </div>
                  </TabsContent>
                </Tabs>
              </CollapsibleContent>
            </Collapsible>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

