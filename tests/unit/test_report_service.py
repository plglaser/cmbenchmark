from cmbenchmark.services.report import (
    build_report_data,
    create_histogram_data,
    create_share_histogram_data,
)


def test_create_histogram_data_counts_sum():
    values = [1, 2, 3, 4, 5, 6]
    hist = create_histogram_data(values, bins=3)
    assert sum(b["count"] for b in hist) == len(values)
    assert len(hist) == 3


def test_create_share_histogram_data_clamps_and_counts_sum():
    values = [-0.5, 0.0, 0.25, 1.0, 1.5]
    hist = create_share_histogram_data(values, bins=5)
    assert sum(b["count"] for b in hist) == len(values)
    assert all(isinstance(b["bin"], str) and "%" in b["bin"] for b in hist)


def test_histogram_small_sample_has_readable_ranges():
    hist = create_histogram_data([14.0, 14.3, 15.0])
    assert hist == [
        {"bin": "14.00-14.50", "count": 2},
        {"bin": "14.50-15.00", "count": 1},
    ]


def test_histogram_preserves_small_values_and_filters_nonfinite_data():
    assert create_histogram_data([None, "invalid", float("nan"), float("inf")]) == []
    assert create_histogram_data([0.00125, 0.00125, None]) == [
        {"bin": "0.00125", "count": 2}
    ]
    hist = create_histogram_data([0.001, 0.0011, 0.0012])
    assert len(hist) == 2
    assert sum(row["count"] for row in hist) == 3
    for row in hist:
        lower, upper = map(float, row["bin"].split("-"))
        assert lower < upper


def test_histogram_caps_default_bins_and_keeps_empty_intervals():
    hist = create_histogram_data(list(range(1000)))
    assert len(hist) == 20
    assert sum(row["count"] for row in hist) == 1000
    hist = create_histogram_data([0, 0, 0, 10], bins=3)
    assert [row["count"] for row in hist] == [3, 0, 1]
    assert create_histogram_data([0, 1, 2], bins=0) == create_histogram_data([0, 1, 2])


def test_share_histogram_adapts_precision_to_narrow_ranges():
    hist = create_share_histogram_data([0.14001, 0.14002, 0.14003])
    assert len(hist) == 2
    assert sum(row["count"] for row in hist) == 3
    for row in hist:
        lower, upper = map(float, row["bin"].removesuffix("%").split("-"))
        assert lower < upper
    assert create_share_histogram_data([0.125, 0.125]) == [
        {"bin": "12.5%", "count": 2}
    ]


def test_build_report_data_top10_and_relpath_mapping():
    measures = {
        "parsing": {
            "d1_m1_parse_status": {"n_success": 1, "share_success": 1.0, "n_partial": 0, "share_partial": 0.0, "n_failed": 0, "share_failed": 0.0},
            "d1_m2_elements_loaded_skipped": {
                "total_elements_loaded": 20,
                "total_elements_skipped": 10,
                "dataset_skip_ratio": 10 / 30,
                "skip_ratio_stats": {"mean": 0.5, "median": 0.5},
                "n_models_with_skips": 2,
                "share_models_with_skips": 1.0,
            },
            "d1_m5_warnings": {"total_warnings_by_type": {"x": 2}},
        },
        "lexical": {
            "d2_m1_label_presence": {
                "dataset_label_eligible_count": 10,
                "dataset_label_present_count": 7,
                "dataset_label_present_share": 0.7,
                "dataset_label_missing_share": 0.3,
                "label_missing_count_by_type": {"A": 2},
            }
        },
        "constructs": {
            "d3_m1_construct_presence": {
                "constructs_available_count": 2,
                "constructs_observed_count": 1,
                "coverage_share": 0.5,
                "construct_catalog": {"C1": {"group": "G", "description": "D", "kind": "K"}},
            }
        },
    }

    measures_per_model = {
        "parsing": {
            "d1_m2_elements_loaded_skipped": {
                "m1": {"skip_ratio": 0.9, "elements_loaded": 10, "elements_skipped": 9},
                "m2": {"skip_ratio": 0.1, "elements_loaded": 10, "elements_skipped": 1},
            },
            "d1_m4_file_size": {"m1": {"file_size_bytes_source": 100, "file_size_bytes_ir": 10}},
            "d1_m5_warnings": {"m1": {"warning_count": 5, "warnings_by_type": {"x": 5}}},
        },
        "constructs": {"d3_m1_construct_presence": {"m1": {"coverage_share": 0.2}}},
        "lexical": {
            "d2_m1_label_presence": {
                "m1": {"label_eligible_count": 5, "label_present_count": 2},
                "m2": {"label_eligible_count": 3, "label_present_count": 3},
            }
        },
    }

    ir_info = {"index": {"m1": "rel/m1.json"}}

    derived = build_report_data(measures, measures_per_model, ir_info)
    assert derived["skipRatioTop10"][0]["modelId"] == "m1"
    assert derived["skipRatioTop10"][0]["relpath"] == "rel/m1.json"
    assert derived["parseElementsSkipsSummary"]["totalElementsLoaded"] == 20
    assert derived["parseElementsSkipsSummary"]["totalElementsSkipped"] == 10
    assert derived["parseElementsSkipsSummary"]["totalElementsProcessed"] == 30
    assert derived["parseElementsSkipsSummary"]["modelsWithSkips"] == 2
    assert derived["parseElementsSkipsSummary"]["totalModelsEvaluated"] == 2
    assert len(derived["skipRatioTop10"]) <= 10
    assert derived["parseStatusChartData"][0]["name"] == "Success"
    assert derived["labelMissingTop10"][0]["missingCount"] == 3
