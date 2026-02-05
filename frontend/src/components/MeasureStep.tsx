import { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Loader2, CheckCircle2, FileJson } from 'lucide-react';
import { apiService } from '../services/api';
import type { MeasureResponse } from '../types/api';
import type { BenchmarkProfile } from '../types/profile';
import { ReadonlyField } from './profile/ReadonlyField';
import { ReadonlyListField } from './profile/ReadonlyListField';
import { ConfigCard } from './profile/ConfigCard';

interface MeasureStepProps {
  onMeasureComplete: (result: MeasureResponse) => void;
  profile: BenchmarkProfile | null;
}

export function MeasureStep({ onMeasureComplete, profile }: MeasureStepProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MeasureResponse | null>(null);
  const [parseConfigOpen, setParseConfigOpen] = useState(false);
  const [lexicalConfigOpen, setLexicalConfigOpen] = useState(false);
  const [constructConfigOpen, setConstructConfigOpen] = useState(false);
  const [sizeConfigOpen, setSizeConfigOpen] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (!profile) {
        throw new Error('Load a benchmark profile to compute measures.');
      }
      const response = await apiService.measure({
        profile,
      });
      setResult(response);
      onMeasureComplete(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to compute measures');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Step 3: Compute Measures</CardTitle>
        <CardDescription>
          Compute dataset-level and per-model measures from the IR models.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {!profile && (
            <div className="p-3 text-sm text-muted-foreground bg-muted rounded-md">
              Upload a benchmark profile to view parameters and run measure computation.
            </div>
          )}

          {profile && (
            <div className="space-y-6">
              {!profile.measure && (
                <ReadonlyField label="Measure Config" value={undefined} />
              )}

              {profile.measure && (
                <>
                  <ConfigCard title="Parsing Measures" open={parseConfigOpen} onOpenChange={setParseConfigOpen}>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <ReadonlyField label="Enabled" value={profile.measure.parse?.enabled} />
                    </div>
                  </ConfigCard>

                  <ConfigCard title="Lexical Measures" open={lexicalConfigOpen} onOpenChange={setLexicalConfigOpen}>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <ReadonlyField label="Enabled" value={profile.measure.lexical?.enabled} />
                      <ReadonlyField label="Include Nodes" value={profile.measure.lexical?.include_nodes} />
                      <ReadonlyField label="Include Edges" value={profile.measure.lexical?.include_edges} />
                      <ReadonlyListField
                        label="Label Attributes"
                        values={profile.measure.lexical?.label_attributes ?? undefined}
                      />
                      <ReadonlyField label="Enable D2.M1" value={profile.measure.lexical?.enable_d2_m1} />
                      <ReadonlyField label="Enable D2.M2" value={profile.measure.lexical?.enable_d2_m2} />
                      <ReadonlyField label="Enable D2.M3" value={profile.measure.lexical?.enable_d2_m3} />
                      <ReadonlyField label="Enable D2.M4" value={profile.measure.lexical?.enable_d2_m4} />
                      <ReadonlyField label="Enable D2.M5" value={profile.measure.lexical?.enable_d2_m5} />
                    </div>

                    <div className="pt-2 border-t space-y-3">
                      <div className="text-sm font-semibold">Tokenizer</div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <ReadonlyField label="Name" value={profile.measure.lexical?.tokenizer?.name} />
                        <ReadonlyField label="Split on Punct" value={profile.measure.lexical?.tokenizer?.split_on_punct} />
                        <ReadonlyField label="Split Camel Case" value={profile.measure.lexical?.tokenizer?.split_camel_case} />
                        <ReadonlyField label="Strip" value={profile.measure.lexical?.tokenizer?.strip} />
                        <ReadonlyField label="Lowercase" value={profile.measure.lexical?.tokenizer?.lowercase} />
                        <ReadonlyField label="Keep Numbers" value={profile.measure.lexical?.tokenizer?.keep_numbers} />
                        <ReadonlyField
                          label="Collapse Whitespace"
                          value={profile.measure.lexical?.tokenizer?.collapse_whitespace}
                        />
                        <ReadonlyField label="Unicode NFKC" value={profile.measure.lexical?.tokenizer?.unicode_nfkc} />
                        <ReadonlyField label="Stopword List" value={profile.measure.lexical?.tokenizer?.stopword_list} />
                        <ReadonlyField label="Noise Token List" value={profile.measure.lexical?.tokenizer?.noise_token_list} />
                      </div>
                    </div>
                  </ConfigCard>

                  <ConfigCard title="Construct Measures" open={constructConfigOpen} onOpenChange={setConstructConfigOpen}>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <ReadonlyField label="Enabled" value={profile.measure.constructs?.enabled} />
                      <ReadonlyField label="Enable D3.M1" value={profile.measure.constructs?.enable_d3_m1} />
                      <ReadonlyField label="Enable D3.M2" value={profile.measure.constructs?.enable_d3_m2} />
                      <ReadonlyField label="Enable D3.M3" value={profile.measure.constructs?.enable_d3_m3} />
                    </div>
                  </ConfigCard>

                  <ConfigCard title="Size & Complexity" open={sizeConfigOpen} onOpenChange={setSizeConfigOpen}>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <ReadonlyField label="Enabled" value={profile.measure.size_complexity?.enabled} />
                      <ReadonlyField label="Enable D4.M1" value={profile.measure.size_complexity?.enable_d4_m1} />
                      <ReadonlyField label="Enable D4.M2" value={profile.measure.size_complexity?.enable_d4_m2} />
                      <ReadonlyField label="Enable D4.M3" value={profile.measure.size_complexity?.enable_d4_m3} />
                      <ReadonlyField label="Enable D4.M4" value={profile.measure.size_complexity?.enable_d4_m4} />
                    </div>
                  </ConfigCard>
                </>
              )}
            </div>
          )}

          {error && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
              {error}
            </div>
          )}

          <Button type="submit" disabled={loading || !profile || result !== null}>
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Computing measures...
              </>
            ) : (
              'Compute Measures'
            )}
          </Button>
        </form>

        {result && (
          <div className="mt-6 space-y-4">
            <div className="p-4 bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-900 rounded-md">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-semibold text-green-900 dark:text-green-100 mb-2">
                    Measures computed successfully.
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2 text-green-800 dark:text-green-200">
                      <CheckCircle2 className="h-4 w-4" />
                      <FileJson className="h-4 w-4" />
                      <code className="font-mono">{result.measures_path}</code>
                      <span className="text-muted-foreground">(dataset-level)</span>
                    </div>
                    <div className="flex items-center gap-2 text-green-800 dark:text-green-200">
                      <CheckCircle2 className="h-4 w-4" />
                      <FileJson className="h-4 w-4" />
                      <code className="font-mono">{result.measures_per_model_path}</code>
                      <span className="text-muted-foreground">(per-model)</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
