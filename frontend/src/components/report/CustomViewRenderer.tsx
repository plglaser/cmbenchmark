import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { CustomViewDefinition, CustomViewPreviewResponse } from '../../types/api';

interface CustomViewRendererProps {
  view: CustomViewDefinition;
  preview: CustomViewPreviewResponse | null;
  loading?: boolean;
  error?: string | null;
}

const PIE_COLORS = ['#2563eb', '#16a34a', '#ea580c', '#9333ea', '#0ea5e9', '#dc2626', '#64748b'];

function formatNumber(value: any): string {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return String(value ?? 'N/A');
  }
  return value.toLocaleString(undefined, { maximumFractionDigits: 3 });
}

export function CustomViewRenderer({ view, preview, loading = false, error = null }: CustomViewRendererProps) {
  if (loading) {
    return <div className="h-[280px] flex items-center justify-center text-sm text-muted-foreground">Loading preview...</div>;
  }
  if (error) {
    return <div className="h-[280px] flex items-center justify-center text-sm text-destructive">{error}</div>;
  }
  if (!preview) {
    return <div className="h-[280px] flex items-center justify-center text-sm text-muted-foreground">No preview data yet.</div>;
  }

  if (preview.chart_type === 'kpi') {
    const value = preview.payload?.value;
    const field = preview.payload?.field;
    const summary = preview.payload?.summary;
    const sampleSize = preview.payload?.sample_size;
    return (
      <div className="h-[280px] flex flex-col items-center justify-center gap-2">
        <div className="text-4xl font-bold">{formatNumber(value)}</div>
        <div className="text-sm text-muted-foreground">
          {summary || 'value'} {field ? `of ${field}` : ''}
        </div>
        <div className="text-xs text-muted-foreground">Sample size: {sampleSize ?? 0}</div>
      </div>
    );
  }

  if (preview.chart_type === 'bar') {
    const items = preview.payload?.items || [];
    if (!items.length) {
      return <div className="h-[280px] flex items-center justify-center text-sm text-muted-foreground">No data points.</div>;
    }
    return (
      <div className="h-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={items}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="category" interval={0} angle={-30} textAnchor="end" height={90} />
            <YAxis />
            <Tooltip formatter={(value: any) => formatNumber(value)} />
            <Bar dataKey="value" fill="#2563eb" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (preview.chart_type === 'pie') {
    const items = preview.payload?.items || [];
    if (!items.length) {
      return <div className="h-[280px] flex items-center justify-center text-sm text-muted-foreground">No data points.</div>;
    }
    return (
      <div className="h-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={items} dataKey="value" nameKey="category" cx="50%" cy="50%" outerRadius={90} label>
              {items.map((_: any, idx: number) => (
                <Cell key={`${view.id || view.name}-pie-${idx}`} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(value: any) => formatNumber(value)} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (preview.chart_type === 'histogram') {
    const bins = preview.payload?.bins || [];
    if (!bins.length) {
      return <div className="h-[280px] flex items-center justify-center text-sm text-muted-foreground">No data points.</div>;
    }
    return (
      <div className="h-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={bins}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="bin" interval={0} angle={-30} textAnchor="end" height={90} />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" fill="#16a34a" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (preview.chart_type === 'scatter') {
    const points = preview.payload?.points || [];
    if (!points.length) {
      return <div className="h-[280px] flex items-center justify-center text-sm text-muted-foreground">No points.</div>;
    }

    const colorField = preview.payload?.color_field;
    if (!colorField) {
      return (
        <div className="h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="x" type="number" name="x" />
              <YAxis dataKey="y" type="number" name="y" />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter data={points} fill="#ea580c" />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      );
    }

    const groups = new Map<string, any[]>();
    points.forEach((point: any) => {
      const category = String(point.category || '(empty)');
      if (!groups.has(category)) {
        groups.set(category, []);
      }
      groups.get(category)?.push(point);
    });

    const groupEntries = Array.from(groups.entries()).slice(0, 8);

    return (
      <div className="h-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="x" type="number" name="x" />
            <YAxis dataKey="y" type="number" name="y" />
            <Tooltip cursor={{ strokeDasharray: '3 3' }} />
            {groupEntries.map(([category, groupPoints], idx) => (
              <Scatter
                key={`${view.id || view.name}-scatter-${category}`}
                name={category}
                data={groupPoints}
                fill={PIE_COLORS[idx % PIE_COLORS.length]}
              />
            ))}
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return <div className="h-[280px] flex items-center justify-center text-sm text-muted-foreground">Unsupported chart.</div>;
}
