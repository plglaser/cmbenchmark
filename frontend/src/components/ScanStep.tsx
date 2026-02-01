import { useState, useMemo, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ScrollArea } from './ui/scroll-area';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { apiService } from '../services/api';
import type { ScanResponse } from '../types/api';
import type { BenchmarkProfile } from '../types/profile';

interface ScanStepProps {
  onScanComplete: (result: ScanResponse) => void;
  profile: BenchmarkProfile | null;
}

interface PatternInputProps {
  label: string;
  patterns: string[];
  onAdd: (pattern: string) => void;
  onRemove: (index: number) => void;
  placeholder: string;
  helpText: React.ReactNode;
  disabled: boolean;
}

function PatternInput({ label, patterns, onAdd, onRemove, placeholder, helpText, disabled }: PatternInputProps) {
  const [inputValue, setInputValue] = useState('');

  const handleAdd = () => {
    if (inputValue.trim()) {
      onAdd(inputValue.trim());
      setInputValue('');
    }
  };

  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <div className="flex gap-2">
        <Input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              handleAdd();
            }
          }}
          placeholder={placeholder}
          disabled={disabled}
          className="font-mono"
        />
        <Button
          type="button"
          onClick={handleAdd}
          disabled={disabled || !inputValue.trim()}
          variant="outline"
        >
          Add
        </Button>
      </div>
      {patterns.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-2">
          {patterns.map((pattern, index) => (
            <span
              key={index}
              className="inline-flex items-center gap-1 px-2 py-1 bg-muted rounded text-sm"
            >
              {pattern}
              <button
                type="button"
                onClick={() => onRemove(index)}
                className="text-muted-foreground hover:text-foreground"
                disabled={disabled}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
      <p className="text-sm text-muted-foreground">{helpText}</p>
    </div>
  );
}

export function ScanStep({ onScanComplete, profile }: ScanStepProps) {
  const [folderName, setFolderName] = useState('');
  const [out, setOut] = useState('');
  const [includePatterns, setIncludePatterns] = useState<string[]>([]);
  const [excludePatterns, setExcludePatterns] = useState<string[]>([]);
  const [sizeLimitMb, setSizeLimitMb] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScanResponse | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [filterCandidates, setFilterCandidates] = useState('');
  const [filterUnreadable, setFilterUnreadable] = useState('');
  const [filterTooLarge, setFilterTooLarge] = useState('');
  const [filterExcluded, setFilterExcluded] = useState('');
  const [filterDuplicates, setFilterDuplicates] = useState('');

  // Pre-fill from profile
  useEffect(() => {
    if (profile) {
      setFolderName(profile.scan.dataset_path);
      setOut(profile.output_path);
      if (profile.scan.include) {
        setIncludePatterns(profile.scan.include);
      }
      if (profile.scan.exclude) {
        setExcludePatterns(profile.scan.exclude);
      }
      if (profile.scan.size_limit_mb !== null && profile.scan.size_limit_mb !== undefined) {
        setSizeLimitMb(profile.scan.size_limit_mb);
      }
    }
  }, [profile]);

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
      const response = await apiService.scan({
        dataset_path: folderName,
        out: out,
        include: includePatterns.length > 0 ? includePatterns : null,
        exclude: excludePatterns.length > 0 ? excludePatterns : null,
        size_limit_mb: sizeLimitMb || null,
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
          <div className="space-y-2">
            <Label htmlFor="dataset-path">Dataset Path *</Label>
            <Input
              id="dataset-path"
              type="text"
              className="font-mono"
              
              // webkitdirectory=""
              // directory=""
              // multiple
              value={folderName}
              onChange={(e) => setFolderName(e.target.value)}
              placeholder="/path/to/dataset"
              required
              disabled={loading || result !== null || !!profile}
              /*
              onChange={(e) => {
                const files = Array.from(e.currentTarget.files ?? []);
                if (files.length === 0) {
                  setFolderName("");
                  return;
                }
            
                const rel = (files[0] as any).webkitRelativePath as string | undefined;
                // TODO: properly split name to select correct dataset path
                const name = rel?.split("/")[0] ?? "Selected folder";
            
                setFolderName(rel);
              }}*/
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="out">Output Directory *</Label>
            <Input
              id="out"
              type="text"
              value={out}
              onChange={(e) => setOut(e.target.value)}
              placeholder="/path/to/output"
              required
              className="font-mono"
              disabled={loading || result !== null || !!profile}
            />
            <p className="text-sm text-muted-foreground">
              Directory where <code className="font-mono">dataset_info.json</code> will be saved
            </p>
          </div>

          <PatternInput
            label="Include Patterns (optional)"
            patterns={includePatterns}
            onAdd={(pattern) => setIncludePatterns([...includePatterns, pattern])}
            onRemove={(index) => setIncludePatterns(includePatterns.filter((_, i) => i !== index))}
            placeholder="*.xml"
            helpText={
              <>
                If not provided, uses default patterns:{' '}
                <code className="font-mono">*.xmi</code>,{' '}
                <code className="font-mono">*.uml</code>,{' '}
                <code className="font-mono">*.xml</code>,{' '}
                <code className="font-mono">*.bpmn</code>,{' '}
                <code className="font-mono">*.bpmn2</code>,{' '}
                <code className="font-mono">*.ecore</code>,{' '}
                <code className="font-mono">*.archimate</code>
              </>
            }
            disabled={loading || result !== null || !!profile}
          />

          <PatternInput
            label="Exclude Patterns (optional)"
            patterns={excludePatterns}
            onAdd={(pattern) => setExcludePatterns([...excludePatterns, pattern])}
            onRemove={(index) => setExcludePatterns(excludePatterns.filter((_, i) => i !== index))}
            placeholder="test/*"
            helpText={
              <>
                Applied after include filtering. Patterns match filenames (e.g.,{' '}
                <code className="font-mono">*.tmp</code>) or relative paths from dataset root (e.g.,{' '}
                <code className="font-mono">test/*</code>).
              </>
            }
            disabled={loading || result !== null || !!profile}
          />

          <div className="space-y-2">
            <Label htmlFor="size-limit">Size Limit MB (optional)</Label>
            <Input
              id="size-limit"
              type="number"
              value={sizeLimitMb || ''}
              onChange={(e) => setSizeLimitMb(e.target.value ? parseInt(e.target.value) : null)}
              placeholder="100"
              min="1"
              disabled={loading || result !== null || !!profile}
            />
            <p className="text-sm text-muted-foreground">
              Maximum file size in MB (files exceeding this will be marked as too_large)
            </p>
          </div>

          {error && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
              {error}
            </div>
          )}

          <Button type="submit" disabled={loading || !folderName || !out || result !== null}>
            {loading ? 'Scanning...' : 'Scan Dataset'}
          </Button>
        </form>

        {result && (
          <div className="mt-6 space-y-4">
            <div className="p-4 bg-muted rounded-md">
              <h3 className="font-semibold mb-2">Scan Results</h3>
              <div className="space-y-1 text-sm">
                <p><strong>Dataset Root:</strong> {result.dataset_root}</p>
                <p><strong>Scanned At:</strong> {new Date(result.scanned_at).toLocaleString()}</p>
                <p><strong>Total Files Seen:</strong> {result.totals.total_seen}</p>
                <p><strong>Candidates:</strong> {result.totals.candidates}</p>
                <p><strong>Unreadable:</strong> {result.totals.unreadable}</p>
                <p><strong>Too Large:</strong> {result.totals.too_large}</p>
                <p><strong>Filtered:</strong> {result.totals.filtered}</p>
                <p><strong>Duplicates:</strong> {result.duplicates_groups.length} {result.duplicates_groups.length === 1 ? 'group' : 'groups'} ({result.duplicates_groups.reduce((sum, group) => sum + group.count, 0)} {result.duplicates_groups.reduce((sum, group) => sum + group.count, 0) === 1 ? 'file' : 'files'})</p>
              </div>
            </div>

            {Object.keys(result.extensions).length > 0 && (
              <div className="p-4 bg-muted rounded-md">
                <h3 className="font-semibold mb-2">File Extensions</h3>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(result.extensions).map(([ext, count]) => (
                    <span key={ext} className="px-2 py-1 bg-background rounded text-sm">
                      {ext}: {count}
                    </span>
                  ))}
                </div>
              </div>
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

