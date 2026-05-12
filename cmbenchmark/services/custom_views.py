"""Custom report view discovery, preview, and persistence helpers."""

from __future__ import annotations

import json
import math
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple
from uuid import uuid4

from cmbenchmark.report.utils import create_histogram_data
from cmbenchmark.services.measure import load_measure_per_model_split

CUSTOM_VIEWS_FILENAME = "custom_views.json"

_SUPPORTED_CHART_TYPES = {"kpi", "bar", "pie", "histogram", "scatter"}
_SUPPORTED_SOURCES = {"dataset", "per_model"}
_SUPPORTED_FILTER_OPS = {
    "eq",
    "ne",
    "gt",
    "gte",
    "lt",
    "lte",
    "contains",
    "in",
    "not_in",
    "is_null",
    "is_not_null",
}
_SUMMARY_KEYS = {"n", "min", "p25", "median", "mean", "p75", "max", "std"}
_MAP_HINT_SUFFIXES = (
    "_by_type",
    "_by_construct",
    "present_constructs",
    "count_by_construct",
    "relative_frequency_by_construct",
    "case_style_counts",
    "case_style_share",
    "language_counts",
    "warnings_by_type",
    "unknown_type_examples",
    "label_missing_count_by_type",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def _infer_map_type(value: Mapping[str, Any]) -> str:
    value_types = set()
    for item in value.values():
        if _is_finite_number(item):
            value_types.add("number")
        elif isinstance(item, bool):
            value_types.add("boolean")
        elif isinstance(item, str):
            value_types.add("string")
        elif item is None:
            value_types.add("null")
        else:
            value_types.add("mixed")
    non_null_types = {t for t in value_types if t != "null"}
    if not non_null_types:
        return "map_mixed"
    if non_null_types == {"number"}:
        return "map_number"
    if non_null_types == {"boolean"}:
        return "map_boolean"
    if non_null_types == {"string"}:
        return "map_string"
    return "map_mixed"


def _infer_field_type(value: Any) -> str:
    if isinstance(value, Mapping):
        return _infer_map_type(value)
    if _is_finite_number(value):
        return "number"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if value is None:
        return "null"
    return "mixed"


def _merge_field_type(existing: str, incoming: str) -> str:
    if existing == incoming:
        return existing
    if existing == "null":
        return incoming
    if incoming == "null":
        return existing
    if existing.startswith("map_") or incoming.startswith("map_"):
        return existing if existing == incoming else "map_mixed"
    if {existing, incoming} <= {"number", "boolean"}:
        return "number"
    return "mixed"


def _is_summary_dict(value: Mapping[str, Any]) -> bool:
    keys = set(value.keys())
    if not keys:
        return False
    if not keys.issubset(_SUMMARY_KEYS):
        return False
    return len(keys) >= 4


def _treat_as_map_leaf(prefix: str, value: Mapping[str, Any]) -> bool:
    if not value:
        return False
    if any(prefix.endswith(suffix) for suffix in _MAP_HINT_SUFFIXES):
        return True
    if _is_summary_dict(value):
        return False
    if len(value) <= 5:
        return False
    return all(_is_scalar(v) for v in value.values())


def _flatten_record(value: Any, prefix: str, out: MutableMapping[str, Any]) -> None:
    if isinstance(value, Mapping):
        if prefix and _treat_as_map_leaf(prefix, value):
            out[prefix] = dict(value)
            return
        for key, child in value.items():
            if not isinstance(key, str):
                continue
            next_prefix = f"{prefix}.{key}" if prefix else key
            _flatten_record(child, next_prefix, out)
        return
    if prefix:
        out[prefix] = value


def _build_dataset_record(measures: Mapping[str, Any]) -> Dict[str, Any]:
    flat: Dict[str, Any] = {}
    _flatten_record(measures, "", flat)
    return flat


def _build_per_model_records(
    measures_per_model: Mapping[str, Any],
    ir_index: Optional[Mapping[str, Any]] = None,
) -> List[Dict[str, Any]]:
    rows: Dict[str, Dict[str, Any]] = {}
    for dimension, dimension_payload in measures_per_model.items():
        if not isinstance(dimension_payload, Mapping):
            continue
        for measure_name, model_payload in dimension_payload.items():
            if not isinstance(model_payload, Mapping):
                continue
            for model_id, measure_value in model_payload.items():
                if not isinstance(model_id, str):
                    continue
                row = rows.setdefault(model_id, {"model_id": model_id})
                if ir_index and model_id in ir_index:
                    row["relpath"] = str(ir_index[model_id])
                prefix = f"{dimension}.{measure_name}"
                if isinstance(measure_value, Mapping):
                    flattened: Dict[str, Any] = {}
                    _flatten_record(measure_value, prefix, flattened)
                    row.update(flattened)
                else:
                    row[prefix] = measure_value

    for model_id, row in rows.items():
        if "relpath" not in row:
            row["relpath"] = model_id

    return [rows[k] for k in sorted(rows.keys())]


def _build_field_catalog(rows: Sequence[Mapping[str, Any]], source: str) -> List[Dict[str, Any]]:
    catalog: Dict[str, Dict[str, Any]] = {}
    distinct_values: Dict[str, set[str]] = {}
    for row in rows:
        for path, value in row.items():
            if path == "":
                continue
            inferred_type = _infer_field_type(value)
            entry = catalog.get(path)
            if entry is None:
                catalog[path] = {
                    "path": path,
                    "label": path,
                    "source": source,
                    "type": inferred_type,
                    "sample": value,
                    "non_null_count": 0,
                    "count": 0,
                    "distinct_count": 0,
                    "is_unique": False,
                }
                entry = catalog[path]
            else:
                entry["type"] = _merge_field_type(str(entry["type"]), inferred_type)
            entry["count"] = int(entry["count"]) + 1
            if value is not None:
                entry["non_null_count"] = int(entry["non_null_count"]) + 1
                if entry.get("sample") is None:
                    entry["sample"] = value
                bucket = distinct_values.setdefault(path, set())
                if isinstance(value, Mapping):
                    bucket.add(json.dumps(value, sort_keys=True, default=str))
                else:
                    bucket.add(json.dumps(value, default=str))

    for path, entry in catalog.items():
        entry["distinct_count"] = len(distinct_values.get(path, set()))
        non_null_count = int(entry.get("non_null_count") or 0)
        entry["is_unique"] = non_null_count > 0 and int(entry["distinct_count"]) == non_null_count

    return sorted(catalog.values(), key=lambda x: str(x["path"]))


def load_report_inputs_for_custom_views(output_dir: str) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    root = Path(output_dir).expanduser().resolve()
    measures_path = root / "measures.json"
    measures_index_path = root / "measures_index.json"

    if not measures_path.exists():
        raise ValueError(f"Missing measures.json: {measures_path}")
    if not measures_index_path.exists():
        raise ValueError(f"Missing measures_index.json: {measures_index_path}")

    with open(measures_path, "r", encoding="utf-8") as f:
        measures = json.load(f)

    measures_per_model = load_measure_per_model_split(str(measures_index_path))

    ir_index: Dict[str, Any] = {}
    ir_info_path = root / "ir_info.json"
    if ir_info_path.exists():
        with open(ir_info_path, "r", encoding="utf-8") as f:
            ir_info = json.load(f)
        maybe_index = ir_info.get("index") if isinstance(ir_info, Mapping) else None
        if isinstance(maybe_index, Mapping):
            ir_index = dict(maybe_index)

    return measures, measures_per_model, ir_index


def get_field_catalog(
    measures: Mapping[str, Any],
    measures_per_model: Mapping[str, Any],
    ir_index: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    dataset_record = _build_dataset_record(measures)
    per_model_rows = _build_per_model_records(measures_per_model, ir_index=ir_index)

    dataset_catalog = _build_field_catalog([dataset_record], source="dataset")
    per_model_catalog = _build_field_catalog(per_model_rows, source="per_model")

    return {
        "dataset_fields": dataset_catalog,
        "per_model_fields": per_model_catalog,
        "chart_types": sorted(_SUPPORTED_CHART_TYPES),
    }


def _get_filtered_rows(rows: Sequence[Mapping[str, Any]], filters: Sequence[Mapping[str, Any]]) -> List[Mapping[str, Any]]:
    if not filters:
        return list(rows)

    def _matches(row: Mapping[str, Any], flt: Mapping[str, Any]) -> bool:
        field = str(flt.get("field") or "")
        op = str(flt.get("op") or "eq")
        expected = flt.get("value")
        actual = row.get(field)

        if op == "is_null":
            return actual is None
        if op == "is_not_null":
            return actual is not None
        if op == "eq":
            return actual == expected
        if op == "ne":
            return actual != expected
        if op in {"gt", "gte", "lt", "lte"}:
            if not _is_finite_number(actual) or not _is_finite_number(expected):
                return False
            actual_num = float(actual)
            expected_num = float(expected)
            if op == "gt":
                return actual_num > expected_num
            if op == "gte":
                return actual_num >= expected_num
            if op == "lt":
                return actual_num < expected_num
            return actual_num <= expected_num
        if op == "contains":
            if isinstance(actual, str):
                return isinstance(expected, str) and expected.lower() in actual.lower()
            if isinstance(actual, Sequence) and not isinstance(actual, (str, bytes, bytearray)):
                return expected in actual
            return False
        if op in {"in", "not_in"}:
            if not isinstance(expected, Sequence) or isinstance(expected, (str, bytes, bytearray)):
                return False
            found = actual in expected
            return found if op == "in" else not found
        raise ValueError(f"Unsupported filter operation: {op}")

    out: List[Mapping[str, Any]] = []
    for row in rows:
        include = True
        for flt in filters:
            if not _matches(row, flt):
                include = False
                break
        if include:
            out.append(row)
    return out


def _numeric_values(rows: Sequence[Mapping[str, Any]], field: str) -> List[float]:
    values: List[float] = []
    for row in rows:
        value = row.get(field)
        if _is_finite_number(value):
            values.append(float(value))
    return values


def _count_non_null_values(rows: Sequence[Mapping[str, Any]], field: str) -> int:
    count = 0
    for row in rows:
        if row.get(field) is not None:
            count += 1
    return count


def _coerce_int(value: Any, default: int, min_value: int, max_value: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(min_value, min(max_value, parsed))


def _validate_common(view: Mapping[str, Any]) -> Tuple[str, str, Dict[str, Any], List[Dict[str, Any]]]:
    chart_type = str(view.get("chart_type") or "").strip().lower()
    source = str(view.get("source") or "").strip().lower()
    config = dict(view.get("config") or {})
    filters = [dict(x) for x in (view.get("filters") or []) if isinstance(x, Mapping)]

    if chart_type not in _SUPPORTED_CHART_TYPES:
        raise ValueError(f"Unsupported chart type: {chart_type}")
    if source not in _SUPPORTED_SOURCES:
        raise ValueError(f"Unsupported source: {source}")

    return chart_type, source, config, filters


def _field_types_for_rows(rows: Sequence[Mapping[str, Any]], source: str) -> Dict[str, str]:
    return {
        str(item["path"]): str(item["type"])
        for item in _build_field_catalog(rows, source)
    }


def _require_field(field: str, field_types: Mapping[str, str], label: str) -> str:
    if not field:
        raise ValueError(f"Missing required field: {label}")
    if field not in field_types:
        raise ValueError(f"Unknown field for source: {field}")
    return str(field_types[field])


def _is_numeric_field_type(field_type: str) -> bool:
    return field_type == "number"


def _is_map_field_type(field_type: str) -> bool:
    return field_type.startswith("map_")


def _is_category_field_type(field_type: str) -> bool:
    return field_type in {"string", "boolean", "number"}


def _is_discrete_category_field_type(field_type: str) -> bool:
    return field_type in {"string", "boolean"}


def _validate_filters(filters: Sequence[Mapping[str, Any]], field_types: Mapping[str, str]) -> None:
    for flt in filters:
        field = str(flt.get("field") or "")
        op = str(flt.get("op") or "eq")
        value = flt.get("value")

        if not field:
            raise ValueError("Each filter requires a non-empty 'field'")
        if field not in field_types:
            raise ValueError(f"Filter references unknown field: {field}")
        if op not in _SUPPORTED_FILTER_OPS:
            raise ValueError(f"Unsupported filter operation: {op}")

        field_type = str(field_types[field])
        if op in {"gt", "gte", "lt", "lte"}:
            if not _is_numeric_field_type(field_type):
                raise ValueError(f"Filter op '{op}' requires numeric field: {field}")
            if not _is_finite_number(value):
                raise ValueError(f"Filter op '{op}' requires numeric value for field: {field}")
        elif op == "contains":
            if field_type != "string":
                raise ValueError(f"Filter op 'contains' requires string field: {field}")
            if not isinstance(value, str):
                raise ValueError(f"Filter op 'contains' requires string value for field: {field}")
        elif op in {"in", "not_in"}:
            if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
                raise ValueError(f"Filter op '{op}' requires list-like value for field: {field}")


def _map_items(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, Mapping):
        return []

    items: List[Dict[str, Any]] = []
    for key, raw_value in value.items():
        if isinstance(raw_value, bool):
            numeric_value = 1.0 if raw_value else 0.0
        elif _is_finite_number(raw_value):
            numeric_value = float(raw_value)
        else:
            continue
        items.append({"category": str(key), "value": numeric_value})
    return items


def _distinct_non_null_values(rows: Sequence[Mapping[str, Any]], field: str) -> List[Any]:
    distinct: Dict[str, Any] = {}
    for row in rows:
        value = row.get(field)
        if value is None:
            continue
        key = json.dumps(value, sort_keys=True, default=str)
        distinct[key] = value
    return list(distinct.values())


def _count_categories(rows: Sequence[Mapping[str, Any]], field: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        raw = row.get(field)
        if raw is None:
            continue
        label = str(raw)
        counts[label] = counts.get(label, 0) + 1
    return counts


def preview_custom_view(
    view: Mapping[str, Any],
    measures: Mapping[str, Any],
    measures_per_model: Mapping[str, Any],
    ir_index: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    chart_type, source, config, filters = _validate_common(view)

    dataset_record = _build_dataset_record(measures)
    per_model_rows = _build_per_model_records(measures_per_model, ir_index=ir_index)

    if source == "dataset":
        rows: List[Mapping[str, Any]] = [dataset_record]
    else:
        rows = per_model_rows

    field_types = _field_types_for_rows(rows, source)
    _validate_filters(filters, field_types)
    filtered_rows = _get_filtered_rows(rows, filters)

    if chart_type == "kpi":
        value_field = str(config.get("value_field") or "")
        if not value_field:
            raise ValueError("KPI requires 'value_field'")

        if source == "dataset":
            value_field_type = _require_field(value_field, field_types, "value_field")
            if _is_map_field_type(value_field_type) or value_field_type in {"mixed", "null"}:
                raise ValueError("Dataset KPI value_field must be a scalar field")
            value = filtered_rows[0].get(value_field) if filtered_rows else None
            return {
                "chart_type": "kpi",
                "payload": {
                    "value": value,
                    "field": value_field,
                    "summary": "value",
                    "sample_size": len(filtered_rows),
                },
            }

        value_field_type = _require_field(value_field, field_types, "value_field")
        if not _is_numeric_field_type(value_field_type):
            raise ValueError(f"Per-model KPI value_field must be numeric: {value_field}")
        values = _numeric_values(filtered_rows, value_field)
        if not values:
            raise ValueError(f"KPI field has no numeric values: {value_field}")
        value = float(sum(values) / len(values))

        return {
            "chart_type": "kpi",
            "payload": {
                "value": value,
                "field": value_field,
                "summary": "average",
                "sample_size": len(values),
                "min": min(values),
                "max": max(values),
            },
        }

    if chart_type == "bar":
        if source == "dataset":
            map_field = str(config.get("map_field") or "")
            if not map_field:
                raise ValueError("Dataset bar charts require 'map_field'")
            map_field_type = _require_field(map_field, field_types, "map_field")
            if map_field_type not in {"map_number", "map_boolean"}:
                raise ValueError(f"Dataset bar chart map_field must be numeric/boolean map: {map_field}")
            items = _map_items(filtered_rows[0].get(map_field) if filtered_rows else None)
            if not items:
                raise ValueError(f"Dataset bar chart field has no numeric entries: {map_field}")
            items = sorted(items, key=lambda item: float(item.get("value") or 0.0), reverse=True)
            return {
                "chart_type": "bar",
                "payload": {
                    "items": items,
                    "sample_size": len(items),
                    "x_field": map_field,
                    "y_field": "value",
                    "summary": "map_entries",
                },
            }

        x_field = str(config.get("x_field") or config.get("category_field") or "")
        y_field = str(config.get("y_field") or config.get("value_field") or "")
        if not x_field or not y_field:
            raise ValueError("Per-model bar charts require both 'x_field' and 'y_field'")
        if x_field == y_field:
            raise ValueError("Bar chart x_field and y_field must be different")
        x_field_type = _require_field(x_field, field_types, "x_field")
        y_field_type = _require_field(y_field, field_types, "y_field")
        if _is_map_field_type(x_field_type) or x_field_type in {"mixed", "null"}:
            raise ValueError(f"Bar chart x_field must be a scalar field: {x_field}")
        if not _is_numeric_field_type(y_field_type):
            raise ValueError(f"Bar chart y_field must be numeric: {y_field}")

        items: List[Dict[str, Any]] = []
        seen_labels: set[str] = set()
        for row in filtered_rows:
            raw_x = row.get(x_field)
            raw_y = row.get(y_field)
            if raw_x is None or not _is_finite_number(raw_y):
                continue
            label = str(raw_x)
            if label in seen_labels:
                raise ValueError(
                    f"Bar chart x_field must uniquely identify rows for per_model source: {x_field}"
                )
            seen_labels.add(label)
            items.append({"category": label, "value": float(raw_y)})

        if not items:
            raise ValueError("Bar chart needs at least one row with both X and Y values")

        return {
            "chart_type": "bar",
            "payload": {
                "items": items,
                "sample_size": len(items),
                "x_field": x_field,
                "y_field": y_field,
                "summary": "raw_rows",
            },
        }

    if chart_type == "pie":
        if source == "dataset":
            map_field = str(config.get("map_field") or "")
            if not map_field:
                raise ValueError("Dataset pie charts require 'map_field'")
            map_field_type = _require_field(map_field, field_types, "map_field")
            if map_field_type not in {"map_number", "map_boolean"}:
                raise ValueError(f"Dataset pie chart map_field must be numeric/boolean map: {map_field}")
            items = _map_items(filtered_rows[0].get(map_field) if filtered_rows else None)
            if len(items) < 2:
                raise ValueError(f"Dataset pie chart field must contain at least 2 entries: {map_field}")
            items = sorted(items, key=lambda item: float(item.get("value") or 0.0), reverse=True)
            return {
                "chart_type": "pie",
                "payload": {
                    "items": items,
                    "sample_size": len(items),
                    "category_field": map_field,
                    "summary": "map_entries",
                },
            }

        category_field = str(config.get("category_field") or config.get("x_field") or "")
        if not category_field:
            raise ValueError("Per-model pie charts require 'category_field'")
        category_field_type = _require_field(category_field, field_types, "category_field")
        if not _is_discrete_category_field_type(category_field_type):
            raise ValueError(f"Pie chart category_field must be string/boolean: {category_field}")

        counts = _count_categories(filtered_rows, category_field)
        if len(counts) < 2:
            raise ValueError(f"Pie chart category_field must contain at least 2 categories: {category_field}")
        if len(counts) > 12:
            raise ValueError(
                f"Pie chart category_field has too many categories ({len(counts)}). Choose a lower-cardinality field."
            )
        if all(count == 1 for count in counts.values()):
            raise ValueError(
                f"Pie chart category_field must repeat across models. Select a shared categorical field: {category_field}"
            )

        items = [
            {"category": category, "value": float(count)}
            for category, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)
        ]
        return {
            "chart_type": "pie",
            "payload": {
                "items": items,
                "sample_size": sum(counts.values()),
                "category_field": category_field,
                "summary": "counts",
            },
        }

    if chart_type == "histogram":
        if source != "per_model":
            raise ValueError("Histogram is only supported for per_model source")

        value_field = str(config.get("value_field") or "")
        if not value_field:
            raise ValueError("Histogram requires 'value_field'")
        value_field_type = _require_field(value_field, field_types, "value_field")
        if not _is_numeric_field_type(value_field_type):
            raise ValueError(f"Histogram value_field must be numeric: {value_field}")
        bins = _coerce_int(config.get("bins"), default=20, min_value=2, max_value=100)

        values = _numeric_values(filtered_rows, value_field)
        if len(values) < 2:
            raise ValueError(f"Histogram requires at least 2 numeric values: {value_field}")
        return {
            "chart_type": "histogram",
            "payload": {
                "bins": create_histogram_data(values, bins=bins),
                "value_field": value_field,
                "sample_size": len(values),
            },
        }

    if chart_type == "scatter":
        if source != "per_model":
            raise ValueError("Scatter is only supported for per_model source")

        x_field = str(config.get("x_field") or "")
        y_field = str(config.get("y_field") or "")
        color_field = str(config.get("color_field") or config.get("group_field") or "")
        if not x_field or not y_field:
            raise ValueError("Scatter requires both 'x_field' and 'y_field'")
        if x_field == y_field:
            raise ValueError("Scatter x_field and y_field must be different")
        x_field_type = _require_field(x_field, field_types, "x_field")
        y_field_type = _require_field(y_field, field_types, "y_field")
        if not _is_numeric_field_type(x_field_type):
            raise ValueError(f"Scatter x_field must be numeric: {x_field}")
        if not _is_numeric_field_type(y_field_type):
            raise ValueError(f"Scatter y_field must be numeric: {y_field}")
        if color_field:
            color_field_type = _require_field(color_field, field_types, "color_field")
            if not _is_discrete_category_field_type(color_field_type):
                raise ValueError(f"Scatter color_field must be string/boolean: {color_field}")
            distinct_categories = _distinct_non_null_values(filtered_rows, color_field)
            if len(distinct_categories) > 8:
                raise ValueError(
                    f"Scatter color_field has too many categories ({len(distinct_categories)}). Choose a lower-cardinality field."
                )

        points: List[Dict[str, Any]] = []
        for row in filtered_rows:
            x = row.get(x_field)
            y = row.get(y_field)
            if not _is_finite_number(x) or not _is_finite_number(y):
                continue
            point = {
                "x": float(x),
                "y": float(y),
                "model_id": row.get("model_id"),
                "relpath": row.get("relpath"),
            }
            if color_field:
                point["category"] = str(row.get(color_field) or "(empty)")
            points.append(point)

        if len(points) < 2:
            raise ValueError("Scatter plot requires at least 2 numeric points")

        return {
            "chart_type": "scatter",
            "payload": {
                "points": points,
                "x_field": x_field,
                "y_field": y_field,
                "color_field": color_field or None,
                "sample_size": len(points),
            },
        }

    raise ValueError(f"Unsupported chart type: {chart_type}")


def _custom_views_path(output_dir: str) -> Path:
    root = Path(output_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root / CUSTOM_VIEWS_FILENAME


def _normalize_view(view: Mapping[str, Any], view_id: Optional[str] = None) -> Dict[str, Any]:
    now_iso = _utc_now_iso()
    updated_at = view.get("updated_at")
    normalized = {
        "id": view_id or str(view.get("id") or "").strip() or uuid4().hex,
        "name": str(view.get("name") or "Untitled View").strip(),
        "description": str(view.get("description") or "").strip() or None,
        "chart_type": str(view.get("chart_type") or "").strip().lower(),
        "source": str(view.get("source") or "per_model").strip().lower(),
        "config": deepcopy(dict(view.get("config") or {})),
        "filters": [dict(x) for x in (view.get("filters") or []) if isinstance(x, Mapping)],
        "updated_at": str(updated_at) if updated_at else now_iso,
    }
    created_at = view.get("created_at")
    normalized["created_at"] = str(created_at) if created_at else now_iso
    _validate_common(normalized)
    if not normalized["name"]:
        raise ValueError("Custom view name cannot be empty")
    return normalized


def load_custom_views(output_dir: str) -> List[Dict[str, Any]]:
    path = _custom_views_path(output_dir)
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    raw_views = payload.get("views", []) if isinstance(payload, Mapping) else []
    views: List[Dict[str, Any]] = []
    for item in raw_views:
        if not isinstance(item, Mapping):
            continue
        try:
            views.append(_normalize_view(item))
        except ValueError:
            continue
    return views


def save_custom_views(output_dir: str, views: Iterable[Mapping[str, Any]]) -> None:
    normalized = [_normalize_view(v) for v in views]
    path = _custom_views_path(output_dir)
    payload = {
        "schema_version": 1,
        "updated_at": _utc_now_iso(),
        "views": normalized,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def create_custom_view(output_dir: str, view: Mapping[str, Any]) -> Dict[str, Any]:
    existing = load_custom_views(output_dir)
    normalized = _normalize_view(view)
    now_iso = _utc_now_iso()
    normalized["created_at"] = now_iso
    normalized["updated_at"] = now_iso
    ids = {v["id"] for v in existing}
    while normalized["id"] in ids:
        normalized["id"] = uuid4().hex
    existing.append(normalized)
    save_custom_views(output_dir, existing)
    return normalized


def update_custom_view(output_dir: str, view_id: str, view: Mapping[str, Any]) -> Dict[str, Any]:
    existing = load_custom_views(output_dir)
    updated = _normalize_view(view, view_id=view_id)
    updated["updated_at"] = _utc_now_iso()

    replaced = False
    new_views: List[Dict[str, Any]] = []
    for item in existing:
        if item.get("id") == view_id:
            updated["created_at"] = item.get("created_at") or updated["created_at"]
            new_views.append(updated)
            replaced = True
        else:
            new_views.append(item)

    if not replaced:
        raise ValueError(f"Custom view not found: {view_id}")

    save_custom_views(output_dir, new_views)
    return updated


def delete_custom_view(output_dir: str, view_id: str) -> bool:
    existing = load_custom_views(output_dir)
    new_views = [item for item in existing if item.get("id") != view_id]
    if len(new_views) == len(existing):
        return False
    save_custom_views(output_dir, new_views)
    return True
