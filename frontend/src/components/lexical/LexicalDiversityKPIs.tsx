import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';

interface LexicalDiversityKPIsProps {
  data: {
    total_tokens: number;
    vocab_size: number;
    type_token_ratio: number;
    stopword_tokens: number;
    stopword_share: number;
  } | null;
}

export function LexicalDiversityKPIs({ data }: LexicalDiversityKPIsProps) {
  if (!data) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Lexical Diversity Metrics</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex justify-between">
          <span>Total Tokens:</span>
          <Badge variant="outline">{data.total_tokens.toLocaleString()}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Vocabulary Size:</span>
          <Badge variant="outline">{data.vocab_size.toLocaleString()}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Type-Token Ratio:</span>
          <Badge variant="outline">{data.type_token_ratio.toFixed(3)}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Stopword Tokens:</span>
          <Badge variant="outline">{data.stopword_tokens.toLocaleString()}</Badge>
        </div>
        <div className="flex justify-between">
          <span>Stopword Share:</span>
          <Badge variant="outline">{(data.stopword_share * 100).toFixed(1)}%</Badge>
        </div>
      </CardContent>
    </Card>
  );
}
