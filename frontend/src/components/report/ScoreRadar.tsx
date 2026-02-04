import {
  ResponsiveContainer,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Tooltip,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface ScoreRadarProps {
  title: string;
  data: Array<{ measure: string; score: number }>;
  stroke: string;
  fill: string;
}

export function ScoreRadar({ title, data, stroke, fill }: ScoreRadarProps) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">No score data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={data}>
            <PolarGrid />
            <PolarAngleAxis dataKey="measure" />
            <PolarRadiusAxis domain={[0, 100]} tickCount={6} />
            <Tooltip formatter={(value) => [`${Number(value).toFixed(1)}`, 'Score']} />
            <Radar dataKey="score" stroke={stroke} fill={fill} fillOpacity={0.45} />
          </RadarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
