# Measures (Quality Dimensions) and Frontend Report Presentation

This document summarizes the **measures currently computed** by the backend measure stage (`cmbenchmark/services/measure.py`) and how they are **transformed into a UI-ready report payload** (`cmbenchmark/services/report.py`) and **rendered in the frontend** (`frontend/src/components/ReportStep.tsx` via `frontend/src/data/dimensions.tsx`).

## Data flow (compute → derive → render)

- **Raw computed measures** (typed dataclasses): `cmbenchmark/types/measures.py`
- **Computation entrypoint**: `cmbenchmark/services/measure.py`
  - Returns **dataset-level** measures (`MeasureResultDataset`) and **per-model** measures (`MeasureResultPerModel`).
  - Persists JSON via `save_measure_dataset(...)` and `save_measure_per_model(...)` (paths determined by the caller / API).
- **Derived report payload** (UI-ready): `cmbenchmark/services/report.py`
  - `build_report_data(measures, measures_per_model, ir_info)` converts the raw JSON into chart series, histogram bins, top-N tables, etc.
  - `generate_report(...)` writes `report.json` in the output directory.
- **Frontend rendering**:
  - `frontend/src/components/ReportStep.tsx` fetches `/api/report` and renders tabbed **dimensions → measures → tiles**.
  - `frontend/src/data/dimensions.tsx` defines the dimension/measure structure and maps derived report fields into concrete React components.
  - Each tile is shown inside `ExpandableTileDialog` (so charts/tables can expand).

## Quality dimensions and measures

### D1 — Parsing (dimension id: `parsing`)

Backend source: `cmbenchmark/measures/parsing_measures.py` (called unconditionally by `compute_measure(...)`).

#### D1.M1 — Parse Status (`parse-status`)

- **Backend metrics (dataset-level)** (`D1M1ParseStatusResult`)
  - `n_models`, `n_success`, `n_partial`, `n_failed`
  - `share_success`, `share_partial`, `share_failed`
  - `parsing_robustness_index = (n_success + 0.5 * n_partial) / n_models`
  - **score**: `clamp(parsing_robustness_index, 0..1) * 100`
- **Backend metrics (per-model)** (`D1M1ParseStatusPerModel`)
  - `parse_status` (`success` | `warning` | `failure`)
  - `parse_error_msg`
- **Derived report fields** (`report.py`)
  - `parseStatus`: raw dataset-level object
  - `parseStatusChartData`: `[{"name": "Success|Partial|Failure", "value": count, "share": share}, ...]`
- **Frontend tiles** (`dimensions.tsx`)
  - **Status Distribution**: `ParseStatusChart(data = parseStatusChartData)`
  - **Key KPIs**: `ParseStatusKPIs(parseStatus = parseStatus)`
- **Frontend score badge** (`ReportStep.tsx`)
  - Measure badge shows `parseStatus.score` (fallback: `parsing_robustness_index * 100` if `score` is missing).

#### D1.M2 — Elements Loaded vs Skipped (`elements-skips`)

- **Backend logic**
  - Excludes models with `parse_status == "failure"` from this measure.
- **Backend metrics (dataset-level)** (`D1M2ElementsLoadedSkippedResult`)
  - `total_elements_loaded`, `total_elements_skipped`
  - `dataset_skip_ratio = total_skipped / (total_loaded + total_skipped)`
  - `skip_ratio_stats`: `DistributionSummary` over per-model skip ratios
  - `n_models_with_skips`, `share_models_with_skips`
  - **score**: `clamp(1 - dataset_skip_ratio, 0..1) * 100`
- **Backend metrics (per-model)** (`D1M2ElementsLoadedSkippedPerModel`)
  - `elements_loaded`, `elements_skipped`, `skip_ratio`
- **Derived report fields**
  - `parseElementsSkips`: raw dataset-level object
  - `skipRatioHistogram`: histogram bins over per-model `skip_ratio` values
  - `skipRatioTop10`: top 10 models by `skip_ratio` (includes `relpath` from `ir_info.index` when available)
- **Frontend tiles**
  - **Skip Ratio Distribution**: `SkipRatioChart(histogramData = skipRatioHistogram)`
  - **Top 10 Models with Highest Skip Ratio**: `SkipRatioTable(data = skipRatioTop10)`
- **Frontend score badge**
  - Measure badge shows `parseElementsSkips.score`.

#### D1.M3 — Parsing Time (`parsing-time`)

- **Backend logic**
  - Excludes failed models.
- **Backend metrics (dataset-level)** (`D1M3ParsingTimeResult`)
  - `parse_time_stats`: `DistributionSummary` over per-model parse times (ms)
  - `parse_time_total_ms`
  - (No score field in this measure type.)
- **Backend metrics (per-model)** (`D1M3ParsingTimePerModel`)
  - `parse_time_ms`
- **Derived report fields**
  - `parseTimeHistogram`: histogram over per-model `parse_time_ms`
  - `parseTimeScatterData`: points `{fileSize, parseTime}` (joined with D1.M4 per-model sizes; only includes points with both > 0)
- **Frontend tiles**
  - **Parse Time Distribution**: `ParseTimeChart(histogramData = parseTimeHistogram)`
  - **File Size vs Parse Time**: `ParseTimeScatter(data = parseTimeScatterData)`

#### D1.M4 — File Size (`file-sizes`)

- **Backend logic**
  - Excludes failed models.
- **Backend metrics (dataset-level)** (`D1M4FileSizeResult`)
  - `file_size_source_stats`: `DistributionSummary`
  - `file_size_ir_stats`: `DistributionSummary`
  - (No score.)
- **Backend metrics (per-model)** (`D1M4FileSizePerModel`)
  - `file_size_bytes_source`, `file_size_bytes_ir`
- **Derived report fields**
  - `sourceSizeHistogram`, `irSizeHistogram`: histograms over per-model sizes
  - `fileSizeTop10`: top 10 by `file_size_bytes_source`
  - `fileSizeBottom10`: bottom 10 by `file_size_bytes_source`
- **Frontend tiles**
  - **File Size Distributions**: `FileSizeCharts(sourceHistogram, irHistogram)`
  - **Top 10 Largest Models**: `FileSizeTable(data = fileSizeTop10)`
  - **Top 10 Smallest Models**: `FileSizeTable(data = fileSizeBottom10)`

#### D1.M5 — Warnings (`warnings`)

- **Backend logic**
  - Excludes failed models.
- **Backend metrics (dataset-level)** (`D1M5WarningsResult`)
  - `n_models_with_warnings`, `share_models_with_warnings`
  - `warning_count_stats`: `DistributionSummary` over per-model warning counts
  - `warnings_per_element_stats`: `DistributionSummary`
  - `total_warnings_by_type`, `n_models_with_warning_type`, `share_models_with_warning_type`
  - **score**: `clamp(1 - share_models_with_warnings, 0..1) * 100`
- **Backend metrics (per-model)** (`D1M5WarningsPerModel`)
  - `warning_count`, `warnings_by_type`, `warnings_per_element`
- **Derived report fields**
  - `parseWarnings`: raw dataset-level object
  - `warningsChartData`: dataset-level totals by warning type
  - `modelsWithWarnings`: top 10 models with `warning_count > 0`
- **Frontend tiles**
  - **Warnings by Type**: `WarningsChart(data = warningsChartData)`
  - **Models with Most Warnings**: `WarningsTable(data = modelsWithWarnings)`
- **Frontend score badge**
  - Measure badge shows `parseWarnings.score`.

#### Parsing dimension score badge (tabs)

`report.py` computes `parsingDimensionScore` as the **mean of the three scores** if all are present: **D1.M1 + D1.M2 + D1.M5**. `ReportStep.tsx` shows this badge for the `parsing` dimension tab.

---

### D2 — Lexical Quality (dimension id: `lexical-quality`)

Backend source: `cmbenchmark/measures/lexical_measures.py` (computed if `profile.measure.lexical.enabled`).

Lexical measures are computed over **label-eligible elements** based on `LexicalProfile`:
- `include_nodes` / `include_edges`
- `label_attributes` (default: `["name"]`)
- `tokenizer` settings (used for token-based measures)

#### D2.M1 — Label Presence (`label-presence`)

- **Backend metrics (dataset-level)** (`D2M1LabelPresenceDataset`)
  - `dataset_label_eligible_count`, `dataset_label_present_count`
  - `dataset_label_present_share` (micro-average), `dataset_label_missing_share`
  - Distribution across models: `label_present_share_stats`, `label_missing_share_stats`
  - `label_missing_count_by_type` (dataset-level missing counts grouped by element type)
  - **score**: `dataset_label_present_share * 100`
- **Backend metrics (per-model)** (`D2M1LabelPresencePerModel`)
  - `label_eligible_count`, `label_present_count`
  - `label_present_share`, `label_missing_share`
  - `label_missing_count_by_type`
- **Derived report fields**
  - `labelPresence`: raw dataset-level object
  - `labelPresenceChartData`: `{present, missing, presentShare, missingShare}`
  - `labelPresenceByType`: sorted missing counts by element type
  - `labelMissingTop10`: top 10 models by missing label count
- **Frontend tiles**
  - **Label Presence Distribution**: `LabelPresenceChart(data = labelPresenceChartData)`
  - **Key Metrics**: `LabelPresenceKPIs(data = labelPresence)`
  - **Missing Labels by Element Type**: `LabelPresenceByTypeChart(data = labelPresenceByType)`
  - **Top 10 Models with Most Missing Labels**: `LabelPresenceMissingTable(data = labelMissingTop10)`
- **Frontend score badge**
  - Measure badge shows `labelPresence.score`.

#### D2.M2 — Label Length (`label-length`)

- **Backend metrics (per-model)** (`D2M2LabelLengthPerModel`)
  - `label_count`
  - Character length: `label_length_chars_mean`, `label_length_chars_median`, `label_length_chars_p95`
  - Token length: `label_length_tokens_mean`, `label_length_tokens_median`, `label_length_tokens_p95`
  - `short_label_share` (chars < 5 OR tokens < 2), `long_label_share` (chars > 30 OR tokens > 8)
- **Backend metrics (dataset-level)** (`D2M2LabelLengthDataset`)
  - `label_length_chars_median_stats` and `label_length_tokens_median_stats` (distribution over **per-model medians**)
  - `short_label_share_stats`, `long_label_share_stats` (distribution over models)
- **Derived report fields**
  - `labelLength`: raw dataset-level object
  - `labelLengthCharsHistogram`: histogram over per-model `label_length_chars_median`
  - `labelLengthTokensHistogram`: histogram over per-model `label_length_tokens_median`
  - `labelLengthTop10`: top 10 models by `charsMedian`
- **Frontend tiles**
  - **Character Length Distribution**: `LabelLengthChart(histogramData = labelLengthCharsHistogram)`
  - **Token Length Distribution**: `LabelLengthChart(histogramData = labelLengthTokensHistogram)`
  - **Length Statistics**: `LabelLengthStats(data = labelLength)`
  - **Top 10 Models by Label Length**: `LabelLengthTable(data = labelLengthTop10)`

#### D2.M3 — Naming Convention Consistency (`naming-convention`)

- **Backend metrics (per-model)** (`D2M3NamingConventionPerModel`)
  - `case_style_counts`, `case_style_share`
  - `naming_style_entropy` (Shannon entropy over detected case styles)
- **Backend metrics (dataset-level)** (`D2M3NamingConventionDataset`)
  - `dataset_case_style_counts`, `dataset_case_style_share`
  - `naming_style_entropy_stats` (distribution over per-model entropies)
- **Derived report fields**
  - `namingConvention`: raw dataset-level object
  - `namingConventionChartData`: dataset case-style counts + shares
  - `namingStyleEntropyHistogram`: histogram over per-model `naming_style_entropy`
- **Frontend tiles**
  - **Case Style Distribution**: `NamingConventionChart(data = namingConventionChartData)`
  - **Naming Style Entropy**: `NamingConventionStats(entropyStats, histogramData = namingStyleEntropyHistogram)`

#### D2.M4 — Single vs Multi-Word Labels (`single-multi-word`)

- **Backend metrics (per-model)** (`D2M4SingleMultiWordPerModel`)
  - `single_word_label_count`, `multi_word_label_count`
  - `single_word_label_share`, `multi_word_label_share`
- **Backend metrics (dataset-level)** (`D2M4SingleMultiWordDataset`)
  - `total_single_word_labels`, `total_multi_word_labels`
  - `dataset_share_single_word_labels`
  - `share_single_word_labels_stats` (distribution over per-model shares)
- **Derived report fields**
  - `singleMultiWord`: raw dataset-level object
  - `singleMultiWordChartData`: `{single, multi, singleShare, multiShare}`
  - `singleWordShareHistogram`: histogram over per-model `single_word_label_share`
- **Frontend tiles**
  - **Single vs Multi-Word Labels**: `SingleMultiWordChart(data = singleMultiWordChartData)`
  - **Statistics**: `SingleMultiWordStats(datasetData = singleMultiWord, shareStats, histogramData = singleWordShareHistogram)`

#### D2.M5 — Lexical Diversity (`lexical-diversity`)

- **Backend metrics (per-model)** (`D2M5LexicalDiversityPerModel`)
  - `total_tokens`, `vocab_size`
  - `type_token_ratio = vocab_size / total_tokens`
  - `stopword_tokens`, `stopword_share` (only if stopwords are configured)
- **Backend metrics (dataset-level)** (`D2M5LexicalDiversityDataset`)
  - `total_tokens`, `vocab_size`, `type_token_ratio`
  - `stopword_tokens`, `stopword_share`
  - `top_labels` (top 50 label strings by occurrence), `top_tokens` (top 50 tokens)
- **Derived report fields**
  - `lexicalDiversity`: raw dataset-level object (contains `top_labels`)
  - `lexicalDiversityTop10`: top 10 models by `typeTokenRatio`
- **Frontend tiles**
  - **Diversity Metrics**: `LexicalDiversityKPIs(data = lexicalDiversity)`
  - **Top 10 Models by Lexical Diversity**: `LexicalDiversityTable(data = lexicalDiversityTop10)`
  - **Top Labels by Occurrence**: `LexicalDiversityTopLabelsTable(data = lexicalDiversity.top_labels)`

---

### D3 — Construct Coverage (dimension id: `construct-coverage`)

Backend source: `cmbenchmark/measures/construct_measures.py` (computed if `profile.measure.constructs.enabled` and construct definitions exist for `profile.parse.parser_language`).

> Note: `ConstructCoverageConfig` includes `enable_d3_m2`, but the current implementation computes **D3.M1** and **D3.M3** only.

#### D3.M1 — Construct Presence (`construct-presence`)

- **Backend metrics (per-model)** (`D3M1ConstructPresencePerModel`)
  - `constructs_available_count`, `constructs_observed_count`, `coverage_share`
  - `present_constructs`: `construct_id -> bool` (availability filtered to non-`UNKNOWN*` constructs)
  - Unknown type diagnostics: `unknown_node_type_count`, `unknown_edge_type_count`, `unknown_type_share`, `unknown_type_examples` (top 10)
- **Backend metrics (dataset-level)** (`D3M1ConstructPresenceDataset`)
  - `constructs_available_count`, `constructs_observed_count`, `coverage_share`
  - `coverage_share_stats` (distribution over per-model coverage shares)
  - `unknown_type_share_dataset`
  - `construct_catalog` (construct metadata for UI)
  - `missing_constructs` (never observed)
  - `coverage_by_group`, `coverage_by_kind`
  - Dataset unknown type counts + examples
  - **score**: `100 * coverage_share_dataset * (1 - unknown_type_share_dataset)` clamped to `[0, 100]`
- **Derived report fields**
  - `constructPresence`: raw dataset-level object
  - `constructCatalog`: copied from `constructPresence.construct_catalog`
  - `constructPresenceChartData`: `{observed, missing, observedShare, missingShare}`
  - `constructPresencePerModel`: per-model rows `{modelId, relpath, presentConstructs}`
  - `coverageShareHistogram`: histogram over per-model `coverage_share`
  - `unknownTypeShareHistogram`: histogram over per-model `unknown_type_share`
  - `lowestCoverage` / `highestCoverage`: outlier tables (10 each)
  - `missingConstructs`: dataset list of missing constructs
  - `unknownTypes`: dataset top unknown types
  - `coverageByGroup`: sorted breakdown (group → available/observed/missing/share)
  - (Also computed but not currently used in tiles: `coverageByKind`.)
- **Frontend tiles**
  - **Coverage Summary**: `ConstructPresenceChart(data = constructPresenceChartData)`
  - **Key Metrics**: `ConstructPresenceKPIs(data = constructPresence, constructCatalog, parserLanguage)`
  - **Coverage Matrix**: `ConstructCoverageMatrix(data = constructPresencePerModel, constructCatalog)`
  - **Coverage Share Distribution**: `CoverageShareChart(histogramData = coverageShareHistogram)`
  - **Coverage by Group**: `CoverageByGroupChart(data = coverageByGroup)`
  - **Missing Constructs**: `MissingConstructsTable(data = missingConstructs)`
  - **Lowest/Highest Coverage**: `CoverageOutliersTable(data = lowestCoverage / highestCoverage)`
  - **Unknown Type Share Distribution**: `UnknownTypeShareChart(histogramData = unknownTypeShareHistogram)`
  - **Top Unknown Types**: `UnknownTypesTable(data = unknownTypes)`
- **Frontend score badge**
  - Measure badge shows `constructPresence.score`.

#### D3.M3 — Construct Frequency (`construct-frequency`)

- **Backend metrics (per-model)** (`D3M3ConstructFrequencyPerModel`)
  - `count_by_construct`, `total_construct_instances`
  - `relative_frequency_by_construct`
  - `utilization_entropy` (normalized to `[0, 1]`)
- **Backend metrics (dataset-level)** (`D3M3ConstructFrequencyDataset`)
  - `dataset_count_by_construct`
  - `dataset_total_construct_instances`
  - `dataset_relative_frequency_by_construct`
  - `dataset_utilization_entropy`
  - **score**: `100 * dataset_utilization_entropy` (clamped)
- **Derived report fields**
  - `constructFrequency`: raw dataset-level object
  - `constructFrequencyData`: dataset table combining counts, share, and metadata (group/kind/description from `constructCatalog`)
  - `constructFrequencyByGroup`: dataset counts grouped by `group`
  - Per-model views:
    - `constructFrequencyPerModel`: per-model counts map (sparse)
    - `constructFrequencyPerModelShares`: per-model shares map (sparse) + totals + entropy
    - `constructFrequencyTopModels`: top 10 models by `totalConstructInstances`
  - Histograms:
    - `constructFrequencyTotalsHistogram`: histogram over per-model totals
    - `constructFrequencyEntropyHistogram`: histogram over per-model entropies (treated as share-like values)
  - `constructFrequencyPareto`: precomputed cumulative share series (present in payload; UI components may recompute from `constructFrequencyData`)
- **Frontend tiles**
  - **Key Metrics**: `ConstructFrequencyKPIs(data = constructFrequency, frequencyData = constructFrequencyData)`
  - **Total Construct Instances (Models)**: `ConstructFrequencyTotalsChart(histogramData = constructFrequencyTotalsHistogram)`
  - **Utilization Entropy (Models)**: `ConstructFrequencyEntropyChart(histogramData = constructFrequencyEntropyHistogram)`
  - **Top Models by Construct Instances**: `ConstructFrequencyTopModelsTable(data = constructFrequencyTopModels)`
  - Dataset-level frequency visualizations (all backed by `constructFrequencyData` and filter UI):
    - `ConstructFrequencyChartWithFilter`
    - `ConstructFrequencyTreemapWithFilter`
    - `ConstructFrequencyParetoWithFilter`
    - `ConstructFrequencyByGroupChart(data = constructFrequencyByGroup)`
  - Cross model × construct:
    - **Counts heatmap**: `ConstructFrequencyHeatmap(data = constructFrequencyPerModel, constructCatalog, constructTotals = constructFrequencyData)`
    - **Share heatmap**: `ConstructFrequencyShareHeatmap(data = constructFrequencyPerModelShares, ...)`
- **Frontend score badge**
  - Measure badge shows `constructFrequency.score`.

#### Construct coverage dimension score badge (tabs)

`report.py` forwards `constructDimensionScore` from `measures["constructs"]["score"]` (computed as the mean of D3.M1 and D3.M3 scores). `ReportStep.tsx` shows this badge for the `construct-coverage` dimension tab.

---

### D4 — Size & Complexity (dimension id: `size-complexity`)

Backend source: `cmbenchmark/measures/size_complexity_measures.py` (computed if `profile.measure.size_complexity.enabled`).

These measures currently do **not** define a `score` field; the UI focuses on distributions and top-N tables.

#### D4.M1 — Model Size (`model-size`)

- **Backend metrics (per-model)** (`D4M1ModelSizePerModel`)
  - `node_count`, `edge_count`, `element_count`, `edge_node_ratio`
- **Backend metrics (dataset-level)** (`D4M1ModelSizeDataset`)
  - Totals: `total_node_count`, `total_edge_count`, `total_element_count`
  - Distributions across models: `node_count_stats`, `edge_count_stats`, `element_count_stats`, `edge_node_ratio_stats`
- **Derived report fields**
  - `modelSize`: raw dataset-level object
  - Histograms: `modelSizeNodeHistogram`, `modelSizeEdgeHistogram`, `modelSizeElementHistogram`, `modelSizeEdgeNodeRatioHistogram`
  - `modelSizeScatterData`: `{nodeCount, edgeCount}` points per model
  - `modelSizeTop10`: top 10 by `elementCount`
- **Frontend tiles**
  - KPIs: `ModelSizeKPIs(data = modelSize)`
  - Histograms: `HistogramCard(...)` for node/edge/element/ratio
  - Scatter: `ModelSizeScatter(data = modelSizeScatterData)`
  - Table: `ModelSizeTopTable(data = modelSizeTop10)`

#### D4.M2 — Degree (`degree`)

- **Backend metrics (per-model)** (`D4M2DegreePerModel`)
  - `avg_degree`, `avg_in_degree`, `avg_out_degree`, `degree_median`
  - `degree_stats`, `in_degree_stats`, `out_degree_stats` (DistributionSummary over node-level degrees within the model)
- **Backend metrics (dataset-level)** (`D4M2DegreeDataset`)
  - Distributions across models: `avg_degree_stats`, `avg_in_degree_stats`, `avg_out_degree_stats`, `degree_median_stats`
- **Derived report fields**
  - `degree`: raw dataset-level object
  - Histograms: `avgDegreeHistogram`, `avgInDegreeHistogram`, `avgOutDegreeHistogram`, `degreeMedianHistogram`
  - `degreeTop10`: top 10 models by `avgDegree`
- **Frontend tiles**
  - KPIs: `DegreeKPIs(data = degree)`
  - Histograms: `HistogramCard(...)`
  - Table: `DegreeTopTable(data = degreeTop10)`

#### D4.M3 — Connectivity (`connectivity`)

- **Backend metrics (per-model)** (`D4M3ConnectivityPerModel`)
  - `n_components`, `largest_component_size`
  - `isolated_node_count`, `isolated_node_share`
  - `component_size_stats` (distribution of component sizes within the model)
- **Backend metrics (dataset-level)** (`D4M3ConnectivityDataset`)
  - Distributions across models: `n_components_stats`, `largest_component_size_stats`, `isolated_node_count_stats`, `isolated_node_share_stats`
  - Totals: `total_components`, `total_isolated_nodes`
- **Derived report fields**
  - `connectivity`: raw dataset-level object
  - Histograms: `nComponentsHistogram`, `largestComponentSizeHistogram`, `isolatedNodeCountHistogram`, `isolatedNodeShareHistogram`
  - `connectivityTop10`: top 10 models by `isolatedNodeShare`
- **Frontend tiles**
  - KPIs: `ConnectivityKPIs(data = connectivity)`
  - Histograms: `HistogramCard(...)`
  - Table: `ConnectivityTopTable(data = connectivityTop10)`

#### D4.M4 — Containment Depth (`containment-depth`)

- **Backend logic**
  - Attempts to interpret containment edges based on language:
    - ArchiMate: `composition`, `aggregation`
    - Ecore: `contains`, `containment`, or `edge.data.containment == true`
    - Fallback: best-effort
- **Backend metrics (per-model)** (`D4M4ContainmentDepthPerModel`)
  - `max_depth`, `mean_depth`, `median_depth`
  - `depth_stats` (distribution of node depths within the model)
  - `root_count`, `contained_node_share`
- **Backend metrics (dataset-level)** (`D4M4ContainmentDepthDataset`)
  - Distributions across models: `max_depth_stats`, `mean_depth_stats`, `contained_node_share_stats`
  - Totals: `total_contained_nodes`, `total_root`
- **Derived report fields**
  - `containmentDepth`: raw dataset-level object
  - Histograms: `maxDepthHistogram`, `meanDepthHistogram`, `containedNodeShareHistogram`
  - `depthTop10`: top 10 models by `maxDepth`
- **Frontend tiles**
  - KPIs: `DepthKPIs(data = containmentDepth)`
  - Histograms: `HistogramCard(...)`
  - Table: `DepthTopTable(data = depthTop10)`

---

## Presentation rules (tabs and badges)

`frontend/src/components/ReportStep.tsx` adds small numeric badges:

- **Dimension tab badges**
  - `parsing`: `parsingDimensionScore` (derived in `report.py` from D1.M1, D1.M2, D1.M5)
  - `construct-coverage`: `constructDimensionScore` (from construct measures dataset score)
  - Other dimensions currently show **no** dimension badge.

- **Measure tab badges** (only where `getMeasureScore(...)` is implemented)
  - `parse-status`: D1.M1 score
  - `elements-skips`: D1.M2 score
  - `warnings`: D1.M5 score
  - `label-presence`: D2.M1 score
  - `construct-presence`: D3.M1 score
  - `construct-frequency`: D3.M3 score
  - Other measures currently show **no** score badge.

## Notes and “computed but not currently used” fields

- `report.py` returns some fields that are not currently wired into tiles (e.g. `coverageByKind`, `constructFrequencyPareto`), but they are still part of the derived `ReportResponse` and may be useful for future UI enhancements.
- Several raw measure objects contain rich `DistributionSummary` statistics. In many cases the UI charts rely on **histograms built from per-model values** (derived in `report.py`) rather than directly plotting these summaries.

