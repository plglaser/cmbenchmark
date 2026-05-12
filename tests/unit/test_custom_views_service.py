from pathlib import Path

import pytest

from cmbenchmark.services.custom_views import (
    create_custom_view,
    delete_custom_view,
    get_field_catalog,
    load_custom_views,
    preview_custom_view,
    save_custom_views,
    update_custom_view,
)


def _sample_measures() -> dict:
    return {
        "num_models": 2,
        "parsing": {
            "d1_m1_parse_status": {
                "n_success": 1,
                "n_partial": 1,
                "score": 75.0,
            },
            "d1_m5_warnings": {
                "total_warnings_by_type": {"A": 3, "B": 1},
            },
        },
    }


def _sample_measures_per_model() -> dict:
    return {
        "parsing": {
            "d1_m1_parse_status": {
                "m1": {"parse_status": "success", "parser_family": "demo"},
                "m2": {"parse_status": "warning", "parser_family": "demo"},
            },
            "d1_m3_parsing_time": {
                "m1": {"parse_time_ms": 10},
                "m2": {"parse_time_ms": 25},
            },
            "d1_m5_warnings": {
                "m1": {"warning_count": 0, "warnings_by_type": {"A": 0}},
                "m2": {"warning_count": 4, "warnings_by_type": {"A": 3, "B": 1}},
            },
        }
    }


def test_get_field_catalog_detects_scalar_and_map_fields():
    catalog = get_field_catalog(
        measures=_sample_measures(),
        measures_per_model=_sample_measures_per_model(),
        ir_index={"m1": "path/a", "m2": "path/b"},
    )

    dataset_fields = {field["path"]: field for field in catalog["dataset_fields"]}
    per_model_fields = {field["path"]: field for field in catalog["per_model_fields"]}

    assert dataset_fields["parsing.d1_m1_parse_status.score"]["type"] == "number"
    assert dataset_fields["parsing.d1_m5_warnings.total_warnings_by_type"]["type"] == "map_number"
    assert per_model_fields["parsing.d1_m1_parse_status.parse_status"]["type"] == "string"
    assert per_model_fields["parsing.d1_m5_warnings.warnings_by_type"]["type"] == "map_number"
    assert per_model_fields["model_id"]["is_unique"] is True
    assert per_model_fields["parsing.d1_m1_parse_status.parse_status"]["distinct_count"] == 2


def test_preview_custom_view_supports_core_chart_types():
    measures = _sample_measures()
    per_model = _sample_measures_per_model()

    kpi = preview_custom_view(
        view={
            "name": "Avg Parse Time",
            "chart_type": "kpi",
            "source": "per_model",
            "config": {"value_field": "parsing.d1_m3_parsing_time.parse_time_ms"},
            "filters": [],
        },
        measures=measures,
        measures_per_model=per_model,
        ir_index={"m1": "path/a", "m2": "path/b"},
    )
    assert kpi["chart_type"] == "kpi"
    assert kpi["payload"]["value"] == 17.5

    bar = preview_custom_view(
        view={
            "name": "Parse Status",
            "chart_type": "bar",
            "source": "per_model",
            "config": {
                "x_field": "model_id",
                "y_field": "parsing.d1_m3_parsing_time.parse_time_ms",
            },
            "filters": [],
        },
        measures=measures,
        measures_per_model=per_model,
        ir_index={"m1": "path/a", "m2": "path/b"},
    )
    assert bar["chart_type"] == "bar"
    assert len(bar["payload"]["items"]) == 2

    pie = preview_custom_view(
        view={
            "name": "Warning Types",
            "chart_type": "pie",
            "source": "dataset",
            "config": {
                "map_field": "parsing.d1_m5_warnings.total_warnings_by_type",
            },
            "filters": [],
        },
        measures=measures,
        measures_per_model=per_model,
        ir_index={"m1": "path/a", "m2": "path/b"},
    )
    assert pie["chart_type"] == "pie"
    assert pie["payload"]["items"][0]["category"] == "A"

    hist = preview_custom_view(
        view={
            "name": "Parse Time Distribution",
            "chart_type": "histogram",
            "source": "per_model",
            "config": {
                "value_field": "parsing.d1_m3_parsing_time.parse_time_ms",
                "bins": 4,
            },
            "filters": [],
        },
        measures=measures,
        measures_per_model=per_model,
        ir_index={"m1": "path/a", "m2": "path/b"},
    )
    assert hist["chart_type"] == "histogram"
    assert hist["payload"]["sample_size"] == 2

    scatter = preview_custom_view(
        view={
            "name": "Scatter",
            "chart_type": "scatter",
            "source": "per_model",
            "config": {
                "x_field": "parsing.d1_m3_parsing_time.parse_time_ms",
                "y_field": "parsing.d1_m5_warnings.warning_count",
                "color_field": "parsing.d1_m1_parse_status.parse_status",
            },
            "filters": [],
        },
        measures=measures,
        measures_per_model=per_model,
        ir_index={"m1": "path/a", "m2": "path/b"},
    )
    assert scatter["chart_type"] == "scatter"
    assert len(scatter["payload"]["points"]) == 2


def test_custom_view_persistence_crud(tmp_path: Path):
    output_dir = tmp_path / "out"
    output_dir.mkdir()

    save_custom_views(str(output_dir), [])
    assert load_custom_views(str(output_dir)) == []

    created = create_custom_view(
        str(output_dir),
        {
            "name": "My KPI",
            "chart_type": "kpi",
            "source": "dataset",
            "config": {"value_field": "num_models"},
            "filters": [],
        },
    )
    assert created["id"]

    loaded = load_custom_views(str(output_dir))
    assert len(loaded) == 1

    updated = update_custom_view(
        str(output_dir),
        created["id"],
        {
            "name": "My KPI Updated",
            "chart_type": "kpi",
            "source": "dataset",
            "config": {"value_field": "num_models"},
            "filters": [],
        },
    )
    assert updated["name"] == "My KPI Updated"

    assert delete_custom_view(str(output_dir), created["id"]) is True
    assert load_custom_views(str(output_dir)) == []


def test_preview_rejects_invalid_chart_combinations_and_fields():
    measures = _sample_measures()
    per_model = _sample_measures_per_model()
    ir_index = {"m1": "path/a", "m2": "path/b"}

    with pytest.raises(ValueError, match="Histogram is only supported for per_model source"):
        preview_custom_view(
            view={
                "name": "Invalid Histogram Source",
                "chart_type": "histogram",
                "source": "dataset",
                "config": {"value_field": "parsing.d1_m1_parse_status.score"},
                "filters": [],
            },
            measures=measures,
            measures_per_model=per_model,
            ir_index=ir_index,
        )

    with pytest.raises(ValueError, match="Unknown field for source"):
        preview_custom_view(
            view={
                "name": "Unknown Field",
                "chart_type": "kpi",
                "source": "per_model",
                "config": {"value_field": "does.not.exist"},
                "filters": [],
            },
            measures=measures,
            measures_per_model=per_model,
            ir_index=ir_index,
        )

    with pytest.raises(ValueError, match="must uniquely identify rows"):
        preview_custom_view(
            view={
                "name": "Invalid Bar",
                "chart_type": "bar",
                "source": "per_model",
                "config": {
                    "x_field": "parsing.d1_m1_parse_status.parser_family",
                    "y_field": "parsing.d1_m3_parsing_time.parse_time_ms",
                },
                "filters": [],
            },
            measures=measures,
            measures_per_model=per_model,
            ir_index=ir_index,
        )

    with pytest.raises(ValueError, match="must be string/boolean"):
        preview_custom_view(
            view={
                "name": "Invalid Pie",
                "chart_type": "pie",
                "source": "per_model",
                "config": {
                    "category_field": "parsing.d1_m5_warnings.warning_count",
                },
                "filters": [],
            },
            measures=measures,
            measures_per_model=per_model,
            ir_index=ir_index,
        )

    with pytest.raises(ValueError, match="Scatter y_field must be numeric"):
        preview_custom_view(
            view={
                "name": "Invalid Scatter",
                "chart_type": "scatter",
                "source": "per_model",
                "config": {
                    "x_field": "parsing.d1_m3_parsing_time.parse_time_ms",
                    "y_field": "parsing.d1_m1_parse_status.parse_status",
                },
                "filters": [],
            },
            measures=measures,
            measures_per_model=per_model,
            ir_index=ir_index,
        )


def test_preview_rejects_invalid_filter_config():
    measures = _sample_measures()
    per_model = _sample_measures_per_model()
    ir_index = {"m1": "path/a", "m2": "path/b"}

    with pytest.raises(ValueError, match="Unsupported filter operation"):
        preview_custom_view(
            view={
                "name": "Invalid Filter",
                "chart_type": "kpi",
                "source": "per_model",
                "config": {"value_field": "parsing.d1_m3_parsing_time.parse_time_ms"},
                "filters": [{"field": "parsing.d1_m3_parsing_time.parse_time_ms", "op": "between", "value": [1, 2]}],
            },
            measures=measures,
            measures_per_model=per_model,
            ir_index=ir_index,
        )

    with pytest.raises(ValueError, match="requires numeric field"):
        preview_custom_view(
            view={
                "name": "Invalid Numeric Filter",
                "chart_type": "kpi",
                "source": "per_model",
                "config": {"value_field": "parsing.d1_m3_parsing_time.parse_time_ms"},
                "filters": [{"field": "parsing.d1_m1_parse_status.parse_status", "op": "gt", "value": 0}],
            },
            measures=measures,
            measures_per_model=per_model,
            ir_index=ir_index,
        )
