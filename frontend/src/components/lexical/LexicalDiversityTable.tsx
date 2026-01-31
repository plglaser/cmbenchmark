import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface LexicalDiversityTableProps {
  data: Array<{
    modelId: string;
    relpath: string;
    totalTokens: number;
    vocabSize: number;
    typeTokenRatio: number;
    stopwordShare: number;
  }>;
}

export function LexicalDiversityTable({ data }: LexicalDiversityTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Top 10 Models by Lexical Diversity</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Model</TableHead>
              <TableHead>Total Tokens</TableHead>
              <TableHead>Vocab Size</TableHead>
              <TableHead>TTR</TableHead>
              <TableHead>Stopword Share</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.length > 0 ? (
              data.map((model, idx) => (
                <TableRow key={idx}>
                  <TableCell className="font-mono text-sm">{model.relpath}</TableCell>
                  <TableCell>{model.totalTokens.toLocaleString()}</TableCell>
                  <TableCell>{model.vocabSize.toLocaleString()}</TableCell>
                  <TableCell>{model.typeTokenRatio.toFixed(3)}</TableCell>
                  <TableCell>{(model.stopwordShare * 100).toFixed(1)}%</TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground">
                  No data available
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
