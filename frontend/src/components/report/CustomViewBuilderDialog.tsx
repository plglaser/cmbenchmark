import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { apiService } from '../../services/api';
import type {
  CustomViewChartType,
  CustomViewDefinition,
  CustomViewField,
  CustomViewFieldsResponse,
  CustomViewPreviewResponse,
  CustomViewSource,
} from '../../types/api';
import { CustomViewRenderer } from './CustomViewRenderer';

interface CustomViewBuilderDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  outputDir: string | null;
  fields: CustomViewFieldsResponse | null;
  onCreate: (view: CustomViewDefinition) => Promise<void>;
}

function typeIsNumeric(fieldType: string): boolean {
  return fieldType === 'number';
}

function typeIsScalar(fieldType: string): boolean {
  return fieldType === 'string' || fieldType === 'boolean' || fieldType === 'number';
}

function typeIsDiscreteCategory(fieldType: string): boolean {
  return fieldType === 'string' || fieldType === 'boolean';
}

function typeIsChartableMap(fieldType: string): boolean {
  return fieldType === 'map_number' || fieldType === 'map_boolean';
}

function selectStillValid(value: string, options: CustomViewField[]): boolean {
  if (!value) {
    return true;
  }
  return options.some((field) => field.path === value);
}

export function CustomViewBuilderDialog({
  open,
  onOpenChange,
  outputDir,
  fields,
  onCreate,
}: CustomViewBuilderDialogProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [source, setSource] = useState<CustomViewSource>('per_model');
  const [chartType, setChartType] = useState<CustomViewChartType>('kpi');
  const [valueField, setValueField] = useState('');
  const [mapField, setMapField] = useState('');
  const [categoryField, setCategoryField] = useState('');
  const [xField, setXField] = useState('');
  const [yField, setYField] = useState('');
  const [groupField, setGroupField] = useState('');
  const [bins, setBins] = useState('20');
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [preview, setPreview] = useState<CustomViewPreviewResponse | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [previewHint, setPreviewHint] = useState<string | null>('Select a chart type and matching fields to preview it.');
  const previewRequestIdRef = useRef(0);

  const sourceFields = useMemo(
    () => (source === 'dataset' ? fields?.dataset_fields ?? [] : fields?.per_model_fields ?? []),
    [fields, source]
  );

  const scalarFields = useMemo(
    () => sourceFields.filter((field) => typeIsScalar(field.type)),
    [sourceFields]
  );
  const numericFields = useMemo(
    () => sourceFields.filter((field) => typeIsNumeric(field.type)),
    [sourceFields]
  );
  const datasetValueFields = useMemo(
    () => sourceFields.filter((field) => typeIsScalar(field.type)),
    [sourceFields]
  );
  const mapFields = useMemo(
    () => sourceFields.filter((field) => typeIsChartableMap(field.type)),
    [sourceFields]
  );
  const barXFields = useMemo(
    () => sourceFields.filter((field) => typeIsScalar(field.type) && field.is_unique),
    [sourceFields]
  );
  const pieCategoryFields = useMemo(
    () =>
      sourceFields.filter(
        (field) =>
          typeIsDiscreteCategory(field.type) &&
          field.distinct_count >= 2 &&
          field.distinct_count <= 12 &&
          !field.is_unique
      ),
    [sourceFields]
  );
  const scatterGroupFields = useMemo(
    () =>
      sourceFields.filter(
        (field) =>
          typeIsDiscreteCategory(field.type) &&
          field.distinct_count >= 2 &&
          field.distinct_count <= 8
      ),
    [sourceFields]
  );

  useEffect(() => {
    if (!open) {
      previewRequestIdRef.current += 1;
      setPreview(null);
      setPreviewError(null);
      setPreviewLoading(false);
      setPreviewHint('Select a chart type and matching fields to preview it.');
      return;
    }
    setError(null);
  }, [open]);

  useEffect(() => {
    if (source === 'dataset' && (chartType === 'histogram' || chartType === 'scatter')) {
      setChartType('kpi');
    }
  }, [source, chartType]);

  useEffect(() => {
    if (!selectStillValid(valueField, source === 'dataset' ? datasetValueFields : numericFields)) {
      setValueField('');
    }
  }, [datasetValueFields, numericFields, source, valueField]);

  useEffect(() => {
    if (!selectStillValid(mapField, mapFields)) {
      setMapField('');
    }
  }, [mapField, mapFields]);

  useEffect(() => {
    if (!selectStillValid(categoryField, pieCategoryFields)) {
      setCategoryField('');
    }
  }, [categoryField, pieCategoryFields]);

  useEffect(() => {
    if (!selectStillValid(xField, barXFields.length > 0 ? barXFields : scalarFields)) {
      setXField('');
    }
  }, [barXFields, scalarFields, xField]);

  useEffect(() => {
    if (!selectStillValid(yField, numericFields)) {
      setYField('');
    }
  }, [numericFields, yField]);

  useEffect(() => {
    if (!selectStillValid(groupField, scatterGroupFields)) {
      setGroupField('');
    }
  }, [groupField, scatterGroupFields]);

  const resetForm = () => {
    setName('');
    setDescription('');
    setSource('per_model');
    setChartType('kpi');
    setValueField('');
    setMapField('');
    setCategoryField('');
    setXField('');
    setYField('');
    setGroupField('');
    setBins('20');
    setError(null);
    setPreview(null);
    setPreviewError(null);
    setPreviewLoading(false);
    setPreviewHint('Select a chart type and matching fields to preview it.');
  };

  const buildDraftView = useCallback(
    (requireName: boolean): { view: CustomViewDefinition | null; error: string | null } => {
      const trimmedName = name.trim();
      if (requireName && !trimmedName) {
        return { view: null, error: 'A view name is required.' };
      }

      const config: Record<string, any> = {};

      if (chartType === 'kpi') {
        if (!valueField) {
          return { view: null, error: 'Select a field for the KPI.' };
        }
        config.value_field = valueField;
      }

      if (chartType === 'bar') {
        if (source === 'dataset') {
          if (!mapField) {
            return { view: null, error: 'Dataset bar charts require a numeric or boolean map field.' };
          }
          config.map_field = mapField;
        } else {
          if (!xField || !yField) {
            return { view: null, error: 'Per-model bar charts require both X and Y fields.' };
          }
          if (xField === yField) {
            return { view: null, error: 'Choose different fields for X and Y.' };
          }
          config.x_field = xField;
          config.y_field = yField;
        }
      }

      if (chartType === 'pie') {
        if (source === 'dataset') {
          if (!mapField) {
            return { view: null, error: 'Dataset pie charts require a numeric or boolean map field.' };
          }
          config.map_field = mapField;
        } else {
          if (!categoryField) {
            return { view: null, error: 'Per-model pie charts require a repeated categorical field.' };
          }
          config.category_field = categoryField;
        }
      }

      if (chartType === 'histogram') {
        if (!valueField) {
          return { view: null, error: 'Select a numeric field for the histogram.' };
        }
        config.value_field = valueField;
        config.bins = Number(bins || 20);
      }

      if (chartType === 'scatter') {
        if (!xField || !yField) {
          return { view: null, error: 'Select both X and Y fields for the scatter plot.' };
        }
        if (xField === yField) {
          return { view: null, error: 'Choose different fields for X and Y.' };
        }
        config.x_field = xField;
        config.y_field = yField;
        if (groupField) {
          config.color_field = groupField;
        }
      }

      return {
        view: {
          name: trimmedName || 'Preview',
          description: description.trim() || null,
          chart_type: chartType,
          source,
          config,
          filters: [],
        },
        error: null,
      };
    },
    [
      bins,
      categoryField,
      chartType,
      description,
      groupField,
      mapField,
      name,
      source,
      valueField,
      xField,
      yField,
    ]
  );

  useEffect(() => {
    if (!open || !fields || !outputDir) {
      return;
    }

    const draft = buildDraftView(false);
    if (!draft.view) {
      previewRequestIdRef.current += 1;
      setPreview(null);
      setPreviewError(null);
      setPreviewLoading(false);
      setPreviewHint(draft.error || 'Select a chart type and matching fields to preview it.');
      return;
    }

    const requestId = previewRequestIdRef.current + 1;
    previewRequestIdRef.current = requestId;
    setPreviewLoading(true);
    setPreviewError(null);
    setPreviewHint(null);

    const timerId = window.setTimeout(async () => {
      try {
        const response = await apiService.previewCustomView(outputDir, draft.view!);
        if (previewRequestIdRef.current !== requestId) {
          return;
        }
        setPreview(response);
      } catch (err: any) {
        if (previewRequestIdRef.current !== requestId) {
          return;
        }
        setPreview(null);
        setPreviewError(err.response?.data?.detail || err.message || 'Failed to load preview');
      } finally {
        if (previewRequestIdRef.current === requestId) {
          setPreviewLoading(false);
        }
      }
    }, 350);

    return () => {
      window.clearTimeout(timerId);
    };
  }, [buildDraftView, fields, open, outputDir]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    const draft = buildDraftView(true);
    if (!draft.view) {
      setError(draft.error || 'Invalid view configuration.');
      return;
    }

    setSaving(true);
    try {
      await onCreate(draft.view);
      resetForm();
      onOpenChange(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to create custom view');
    } finally {
      setSaving(false);
    }
  };

  const allChartTypeOptions: Array<{ value: CustomViewChartType; label: string }> = [
    { value: 'kpi', label: 'KPI' },
    { value: 'bar', label: 'Bar Chart' },
    { value: 'pie', label: 'Pie Chart' },
    { value: 'histogram', label: 'Histogram' },
    { value: 'scatter', label: 'Scatter Plot' },
  ];
  const chartTypeOptions = allChartTypeOptions.filter(
    (option) => source === 'per_model' || (option.value !== 'histogram' && option.value !== 'scatter')
  );

  const previewView = useMemo<CustomViewDefinition>(
    () => ({
      name: name.trim() || 'Preview',
      description: description.trim() || null,
      chart_type: chartType,
      source,
      config: {},
      filters: [],
    }),
    [chartType, description, name, source]
  );

  const chartHelpText = useMemo(() => {
    if (chartType === 'kpi') {
      return source === 'dataset'
        ? 'Shows one scalar value directly from measures.json.'
        : 'Shows the average of one numeric per-model field from the existing measure files.';
    }
    if (chartType === 'bar') {
      return source === 'dataset'
        ? 'Uses one dataset map field and plots its entries as bars.'
        : 'Plots one bar per model row. The X field must uniquely identify each row.';
    }
    if (chartType === 'pie') {
      return source === 'dataset'
        ? 'Uses one dataset map field and plots its entries as slices.'
        : 'Counts how often each category appears across models. Only low-cardinality fields are offered.';
    }
    if (chartType === 'histogram') {
      return 'Builds a distribution from one numeric per-model field.';
    }
    return 'Plots one point per model row using two numeric fields, with optional categorical grouping.';
  }, [chartType, source]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Custom View</DialogTitle>
          <DialogDescription>
            Configure a chart directly from discovered measure fields. Invalid combinations are blocked by field type and cardinality.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-2">
            <Label htmlFor="custom-view-name">Name</Label>
            <Input
              id="custom-view-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Example: Parse time by model"
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="custom-view-description">Description</Label>
            <Input
              id="custom-view-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label htmlFor="custom-view-source">Data Source</Label>
              <select
                id="custom-view-source"
                className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                value={source}
                onChange={(e) => setSource(e.target.value as CustomViewSource)}
              >
                <option value="per_model">Per Model</option>
                <option value="dataset">Dataset</option>
              </select>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="custom-view-chart-type">Chart Type</Label>
              <select
                id="custom-view-chart-type"
                className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                value={chartType}
                onChange={(e) => setChartType(e.target.value as CustomViewChartType)}
              >
                {chartTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <p className="text-xs text-muted-foreground">{chartHelpText}</p>

          {chartType === 'kpi' && (
            <div className="grid gap-2">
              <Label htmlFor="custom-view-value-field">Field</Label>
              <select
                id="custom-view-value-field"
                className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                value={valueField}
                onChange={(e) => setValueField(e.target.value)}
              >
                <option value="">Select field</option>
                {(source === 'dataset' ? datasetValueFields : numericFields).map((field) => (
                  <option key={field.path} value={field.path}>
                    {field.path}
                  </option>
                ))}
              </select>
            </div>
          )}

          {chartType === 'bar' && source === 'dataset' && (
            <div className="grid gap-2">
              <Label htmlFor="custom-view-map-field">Map Field</Label>
              <select
                id="custom-view-map-field"
                className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                value={mapField}
                onChange={(e) => setMapField(e.target.value)}
              >
                <option value="">Select map field</option>
                {mapFields.map((field) => (
                  <option key={field.path} value={field.path}>
                    {field.path}
                  </option>
                ))}
              </select>
            </div>
          )}

          {chartType === 'bar' && source === 'per_model' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="custom-view-bar-x">X-Axis Field</Label>
                <select
                  id="custom-view-bar-x"
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                  value={xField}
                  onChange={(e) => setXField(e.target.value)}
                >
                  <option value="">Select unique row field</option>
                  {barXFields.map((field) => (
                    <option key={field.path} value={field.path}>
                      {field.path}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-muted-foreground">
                  Only unique scalar fields are offered here to avoid duplicate bar labels.
                </p>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="custom-view-bar-y">Y-Axis Field</Label>
                <select
                  id="custom-view-bar-y"
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                  value={yField}
                  onChange={(e) => setYField(e.target.value)}
                >
                  <option value="">Select numeric field</option>
                  {numericFields.map((field) => (
                    <option key={field.path} value={field.path}>
                      {field.path}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {chartType === 'pie' && source === 'dataset' && (
            <div className="grid gap-2">
              <Label htmlFor="custom-view-pie-map-field">Map Field</Label>
              <select
                id="custom-view-pie-map-field"
                className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                value={mapField}
                onChange={(e) => setMapField(e.target.value)}
              >
                <option value="">Select map field</option>
                {mapFields.map((field) => (
                  <option key={field.path} value={field.path}>
                    {field.path}
                  </option>
                ))}
              </select>
            </div>
          )}

          {chartType === 'pie' && source === 'per_model' && (
            <div className="grid gap-2">
              <Label htmlFor="custom-view-category-field">Category Field</Label>
              <select
                id="custom-view-category-field"
                className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                value={categoryField}
                onChange={(e) => setCategoryField(e.target.value)}
              >
                <option value="">Select repeated categorical field</option>
                {pieCategoryFields.map((field) => (
                  <option key={field.path} value={field.path}>
                    {field.path}
                  </option>
                ))}
              </select>
              <p className="text-xs text-muted-foreground">
                Pie charts are limited to low-cardinality categories that repeat across multiple models.
              </p>
            </div>
          )}

          {chartType === 'histogram' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="custom-view-histogram-field">Value Field</Label>
                <select
                  id="custom-view-histogram-field"
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                  value={valueField}
                  onChange={(e) => setValueField(e.target.value)}
                >
                  <option value="">Select numeric field</option>
                  {numericFields.map((field) => (
                    <option key={field.path} value={field.path}>
                      {field.path}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="custom-view-bins">Bins</Label>
                <Input
                  id="custom-view-bins"
                  type="number"
                  value={bins}
                  min={2}
                  max={100}
                  onChange={(e) => setBins(e.target.value)}
                />
              </div>
            </div>
          )}

          {chartType === 'scatter' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="custom-view-scatter-x">X Field</Label>
                <select
                  id="custom-view-scatter-x"
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                  value={xField}
                  onChange={(e) => setXField(e.target.value)}
                >
                  <option value="">Select numeric field</option>
                  {numericFields.map((field) => (
                    <option key={field.path} value={field.path}>
                      {field.path}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="custom-view-scatter-y">Y Field</Label>
                <select
                  id="custom-view-scatter-y"
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                  value={yField}
                  onChange={(e) => setYField(e.target.value)}
                >
                  <option value="">Select numeric field</option>
                  {numericFields.map((field) => (
                    <option key={field.path} value={field.path}>
                      {field.path}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid gap-2 md:col-span-2">
                <Label htmlFor="custom-view-scatter-group">Grouping Field</Label>
                <select
                  id="custom-view-scatter-group"
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                  value={groupField}
                  onChange={(e) => setGroupField(e.target.value)}
                >
                  <option value="">None</option>
                  {scatterGroupFields.map((field) => (
                    <option key={field.path} value={field.path}>
                      {field.path}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {error && <p className="text-sm text-destructive">{error}</p>}

          <div className="rounded-md border p-3 space-y-3 bg-muted/10">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium">Live Preview</p>
              {previewLoading && <p className="text-xs text-muted-foreground">Updating...</p>}
            </div>
            {previewHint && !previewError && (
              <p className="text-xs text-muted-foreground">{previewHint}</p>
            )}
            {previewError && <p className="text-xs text-destructive">{previewError}</p>}
            <CustomViewRenderer
              view={previewView}
              preview={preview}
              loading={previewLoading}
              error={previewError}
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={saving || !fields}>
              {saving ? 'Creating...' : 'Create View'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
