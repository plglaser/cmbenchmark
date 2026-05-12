# Measure Catalog

| Dimension (Dₓ) | Measure (Dₓ.Mᵧ) | Intent | Score |
| --- | --- | --- | --- |
| **D1 Parsing** | **D1.M1 Parse Status** | Quantifies the share of models that parse successfully, partially, or fail. | ✅ |
| **D1 Parsing** | **D1.M2 Elements Loaded vs Skipped** | Assesses how much model content is dropped during parsing (skipped elements), overall and per model. | ✅ |
| **D1 Parsing** | **D1.M3 Parsing Time** | Characterizes the distribution of per-model parsing times as a scalability indicator. | ❌ |
| **D1 Parsing** | **D1.M4 File Size** | Describes model size on disk (source vs IR) and its variation across the dataset. | ❌ |
| **D1 Parsing** | **D1.M5 Warnings** | Quantifies models that trigger parser warnings and the dominance of warning types. | ✅ |
| **D2 Lexical Quality** | **D2.M1 Label Presence** | Measures label coverage where labels are expected and identifies where they are missing. | ✅ |
| **D2 Lexical Quality** | **D2.M2 Label Length** | Describes typical label lengths (characters/tokens) and the prevalence of very short or long labels. | ❌ |
| **D2 Lexical Quality** | **D2.M3 Naming Convention Consistency** | Assesses consistency of naming styles (case styles) within models and across the dataset. | ❌ |
| **D2 Lexical Quality** | **D2.M4 Single vs Multi-Word Labels** | Quantifies the share of single-word vs multi-word labels and its variation across models. | ❌ |
| **D2 Lexical Quality** | **D2.M5 Lexical Diversity** | Characterizes vocabulary diversity. | ❌ |
| **D2 Lexical Quality** | **D2.M6 Language Usage** | Characterizes language diversity. | ❌ |
| **D3 Construct Coverage** | **D3.M1 Construct Presence** | Determines which defined language constructs appear at all and how complete construct coverage is. | ✅ |
| **D3 Construct Coverage** | **D3.M3 Construct Frequency** | Analyzes how evenly constructs are used and whether construct usage is dominated by a few types. | ✅ |
| **D4 Size** | **D4.M1 Model Size** | Captures structural model size (nodes, edges, elements) and its distribution. | ❌ |
| **D4 Size** | **D4.M2 Degree** | Describes local connectivity patterns via average and median node degrees. | ❌ |
| **D4 Size** | **D4.M3 Connectivity** | Assesses model fragmentation in terms of components and isolated nodes. | ❌ |
| **D4 Size** | **D4.M4 Containment Depth** | Characterizes hierarchical depth and rootedness of containment structures. | ❌ |

> `DistributionSummary` fields used in multiple measures: `n, min, p25, median, mean, p75, max, std`.

### D1.M1 **Parse Status**

| Metric (informal) | Level | Datatype | Reporting | Used for |
| --- | --- | --- | --- | --- |
| `n_models` | Dataset | Integer | Aggregate KPI | Denominator for all parsing status shares and indices. |
| `n_success, n_partial, n_failed` | Dataset | Integer | Status distribution bar chart (counts) | Absolute status distribution. |
| `share_success, share_partial, share_failed` | Dataset | Float | Status distribution bar/pie chart (shares) | Normalized status distribution for comparability across datasets. |
| `parsing_robustness_index = (n_success + 0.5*n_partial)/n_models` | Dataset | Float | Aggregate KPI | Unscaled robustness index used to compute score. |
| `score = ((n_success + 0.5*n_partial)/n_models)*100` | Dataset | Float | Aggregate KPI, score badge | Single robustness signal that discounts partial and failed parses; summarizes the whole D1.M1 measure. |
| `parse_status ∈ {success, warning, failure}` | Model | Enum/String | Per-model table (`warning` shown as “Partial” in UI) | Identifies problematic models and eligibility for downstream measures. |
| `parse_error_msg` | Model | String (optional) | Per-model table | Diagnostics; attached when parsing fails. |

### D1.M2 **Elements Loaded vs Skipped**

| Metric (informal) | Level | Datatype | Reporting | Used for |
| --- | --- | --- | --- | --- |
| `total_elements_loaded` | Dataset | Integer | Summary KPIs | Total loaded elements across non-failed models. |
| `total_elements_skipped` | Dataset | Integer | Summary KPIs | Total skipped elements across non-failed models. |
| `dataset_skip_ratio = total_skipped/(total_loaded+total_skipped)` | Dataset | Float | Summary KPIs | Dataset-level skip intensity. |
| `skip_ratio_stats` (`DistributionSummary`) | Dataset | Object | Summary KPIs | Mean/median spread of per-model skip ratios. |
| `n_models_with_skips` | Dataset | Integer | Summary KPIs | Count of models with at least one skipped element. |
| `share_models_with_skips` | Dataset | Float | Summary KPIs | Share of models affected by skips. |
| `score = (1 - dataset_skip_ratio)*100` | Dataset | Float | Aggregate KPI | Quality signal based on skip ratio. |
| `elements_loaded, elements_skipped, skip_ratio` | Model | Integer, Integer, Float | Skip ratio histogram + Top-10 table | Per-model skip diagnostics and outlier ranking. |

### D1.M3 **Parsing Time**

| Metric (informal) | Level | Datatype | Reporting | Used for |
| --- | --- | --- | --- | --- |
| `parse_time_stats` (`DistributionSummary`) | Dataset | Object | Statistics/KPI block | Distribution of parse times (ms) across non-failed models. |
| `parse_time_total_ms` | Dataset | Integer | KPI | Total parsing runtime across dataset. |
| `parse_time_ms` | Model | Integer | Parse-time histogram, size-vs-time scatter | Per-model runtime and scalability/outlier analysis. |

### D1.M4 **File Size**

| Metric (informal) | Level | Datatype | Reporting | Used for |
| --- | --- | --- | --- | --- |
| `file_size_source_stats` (`DistributionSummary`) | Dataset | Object | Statistics/KPI block | Distribution of source file sizes. |
| `file_size_ir_stats` (`DistributionSummary`) | Dataset | Object | Statistics/KPI block | Distribution of generated IR sizes. |
| `file_size_bytes_source` | Model | Integer | Source-size histogram, top/bottom-10 tables, parse-time scatter x-axis | Per-model source size for ranking and correlation. |
| `file_size_bytes_ir` | Model | Integer | IR-size histogram, top/bottom-10 tables | Per-model IR size for comparison with source size. |

### D1.M5 **Warnings**

| Metric (informal) | Level | Datatype | Reporting | Used for |
| --- | --- | --- | --- | --- |
| `n_models_with_warnings` | Dataset | Integer | KPI | Number of models that emitted warnings. |
| `share_models_with_warnings` | Dataset | Float | KPI | Dataset-level warning prevalence. |
| `warning_count_stats` (`DistributionSummary`) | Dataset | Object | KPI/summary | Distribution of warning counts per model. |
| `warnings_per_element_stats` (`DistributionSummary`) | Dataset | Object | KPI/summary | Distribution of warning density normalized by elements. |
| `total_warnings_by_type` | Dataset | Map[String→Integer] | Warnings-by-type chart | Dominant warning categories across dataset. |
| `n_models_with_warning_type` | Dataset | Map[String→Integer] | Diagnostics table/summary | Model coverage per warning type. |
| `share_models_with_warning_type` | Dataset | Map[String→Float] | Diagnostics table/summary | Prevalence share per warning type. |
| `score = (1 - share_models_with_warnings)*100` | Dataset | Float | Aggregate KPI | Parsing quality signal based on warning prevalence. |
| `warning_count, warnings_by_type, warnings_per_element` | Model | Integer, Map, Float | Top models with warnings table | Per-model warning diagnostics and ranking. |

### D2.M1 **Label Presence**

| Metric (informal) | Level | Datatype | Reporting | Used for |
| --- | --- | --- | --- | --- |
| `dataset_label_eligible_count` | Dataset | Integer | Presence KPIs | Total eligible label slots. |
| `dataset_label_present_count` | Dataset | Integer | Presence KPIs | Number of non-empty labels. |
| `dataset_label_present_share` | Dataset | Float | Presence chart + KPIs | Overall label completeness. |
| `dataset_label_missing_share` | Dataset | Float | Presence chart + KPIs | Overall label missingness. |
| `label_present_share_stats` (`DistributionSummary`) | Dataset | Object | Presence KPIs | Distribution of per-model present shares. |
| `label_missing_share_stats` (`DistributionSummary`) | Dataset | Object | Presence KPIs | Distribution of per-model missing shares. |
| `label_missing_count_by_type` | Dataset | Map[String→Integer] | Missing-by-type chart | Which element types miss labels most. |
| `score = dataset_label_present_share*100` | Dataset | Float | Aggregate KPI | Label completeness quality score. |
| `label_eligible_count, label_present_count, label_present_share, label_missing_share, label_missing_count_by_type` | Model | Integer/Float/Map | Top-10 missing-label models table | Per-model completeness diagnostics and ranking. |

### D2.M2 **Label Length**

| Metric (informal) | Level | Datatype | Reporting | Used for |
| --- | --- | --- | --- | --- |
| `label_length_chars_median_stats` (`DistributionSummary`) | Dataset | Object | Length stats + histogram context | Distribution of per-model median character lengths. |
| `label_length_tokens_median_stats` (`DistributionSummary`) | Dataset | Object | Length stats + histogram context | Distribution of per-model median token lengths. |
| `short_label_share_stats` (`DistributionSummary`) | Dataset | Object | Length stats | Share of short labels (`<5 chars` or `<2 tokens`) across models. |
| `long_label_share_stats` (`DistributionSummary`) | Dataset | Object | Length stats | Share of long labels (`>30 chars` or `>8 tokens`) across models. |
| `label_count` | Model | Integer | Per-model length table | Number of present labels used in length stats. |
| `label_length_chars_mean, label_length_chars_median, label_length_chars_p95` | Model | Float | Char-length histogram + top-10 table | Per-model character-length profile. |
| `label_length_tokens_mean, label_length_tokens_median, label_length_tokens_p95` | Model | Float | Token-length histogram + top-10 table | Per-model token-length profile. |
| `short_label_share, long_label_share` | Model | Float | Top-10 table | Extremes of short/long labels per model. |

### D2.M3 **Naming Convention Consistency**

| Metric (informal) | Level | Datatype | Reporting | Used for |
| --- | --- | --- | --- | --- |
| `naming_style_entropy_stats` (`DistributionSummary`) | Dataset | Object | Entropy stats panel | Distribution of per-model naming-style entropy. |
| `dataset_case_style_counts` | Dataset | Map[String→Integer] | Case-style distribution chart | Absolute usage by naming style (camelCase, snake_case, etc.). |
| `dataset_case_style_share` | Dataset | Map[String→Float] | Case-style distribution chart | Relative usage by naming style. |
| `case_style_counts` | Model | Map[String→Integer] | Diagnostics | Per-model naming-style frequency counts. |
| `case_style_share` | Model | Map[String→Float] | Diagnostics | Per-model naming-style shares. |
| `naming_style_entropy` | Model | Float | Entropy histogram | Per-model naming consistency/diversity indicator. |

### D2.M4 **Single vs Multi-Word Labels**

| Metric (informal) | Level | Datatype | Reporting | Used for |
| --- | --- | --- | --- | --- |
| `total_single_word_labels` | Dataset | Integer | Single-vs-multi chart + stats | Total single-token labels in dataset. |
| `total_multi_word_labels` | Dataset | Integer | Single-vs-multi chart + stats | Total multi-token labels in dataset. |
| `dataset_share_single_word_labels` | Dataset | Float | Single-vs-multi chart + stats | Dataset-level preference for single-word labels. |
| `share_single_word_labels_stats` (`DistributionSummary`) | Dataset | Object | Stats panel + histogram context | Distribution of per-model single-word shares. |
| `single_word_label_count, multi_word_label_count` | Model | Integer | Diagnostics | Per-model tokenization counts for label style. |
| `single_word_label_share, multi_word_label_share` | Model | Float | Single-word-share histogram | Per-model label style balance. |

### D2.M5 **Lexical Diversity**

| Metric (informal) | Level | Datatype | Reporting | Used for |
| --- | --- | --- | --- | --- |
| `total_tokens` | Dataset | Integer | Diversity KPIs | Total token volume in labeled text. |
| `vocab_size` | Dataset | Integer | Diversity KPIs | Distinct token count. |
| `type_token_ratio` | Dataset | Float | Diversity KPIs | Dataset-level lexical diversity indicator. |
| `top_labels` | Dataset | List[(String, Integer)] | Top-labels table | Most frequent normalized label strings. |
| `top_tokens` | Dataset | List[(String, Integer)] | Diagnostics (report data) | Most frequent tokens after tokenization. |
| `total_tokens, vocab_size, type_token_ratio` | Model | Integer/Float | Top-10 lexical-diversity table | Per-model diversity ranking and comparison. |

### D2.M6 **Language Usage**

| Metric (informal) | Level | Datatype | Reporting | Used for |
| --- | --- | --- | --- | --- |
| `language_counts` | Dataset | Map[String→Integer] | Language distribution pie/bar + KPIs | Dataset language composition (`en`, `de`, `unknown`, ...). |
| `language` | Model | String (ISO-like code or `unknown`) | Aggregated into language charts | Per-model detected language from merged label text. |

### D3.M1 **Construct Presence**

| Metric (informal) | Level | Datatype | Reporting | Used for |
| --- | --- | --- | --- | --- |
| `constructs_available_count` | Dataset | Integer | Coverage KPIs/chart | Denominator of catalog constructs (excluding `UNKNOWN*`). |
| `constructs_observed_count` | Dataset | Integer | Coverage KPIs/chart | Number of constructs observed at least once. |
| `coverage_share = observed/available` | Dataset | Float | Coverage KPIs/chart | Dataset construct coverage. |
| `coverage_share_stats` (`DistributionSummary`) | Dataset | Object | Coverage-share histogram context | Distribution of per-model coverage shares. |
| `unknown_type_share_dataset` | Dataset | Float | Coverage KPIs | Share of elements with unknown types dataset-wide. |
| `unknown_node_type_count_dataset, unknown_edge_type_count_dataset` | Dataset | Integer | Unknown-types diagnostics | Absolute unknown-type counts by kind. |
| `unknown_type_examples_dataset` | Dataset | Map[String→Integer] | Unknown-types table | Top unknown raw types (dataset-level). |
| `construct_catalog` | Dataset | Map[ConstructId→Metadata] | KPIs/matrix/filtering | Metadata for labels, groups, and kinds in UI/report. |
| `missing_constructs` | Dataset | List[Object] | Missing-constructs table | Constructs never observed in dataset. |
| `coverage_by_group, coverage_by_kind` | Dataset | Map[String→Object] | Coverage-by-group charts | Coverage breakdown by semantic grouping. |
| `score = coverage_share*(1-unknown_type_share_dataset)*100` | Dataset | Float | Aggregate KPI | Presence quality score balancing coverage and unknowns. |
| `constructs_available_count, constructs_observed_count, coverage_share` | Model | Integer/Float | Coverage matrix + lowest/highest coverage tables | Per-model construct coverage strength. |
| `present_constructs` | Model | Map[ConstructId→Bool] | Coverage matrix | Construct-by-model presence grid. |
| `unknown_node_type_count, unknown_edge_type_count, unknown_type_share, unknown_type_examples` | Model | Integer/Float/Map | Coverage outlier tables + unknown-share histogram | Per-model unknown-type diagnostics. |

### D3.M3 **Construct Frequency**

| Metric (informal) | Level | Datatype | Reporting | Used for |
| --- | --- | --- | --- | --- |
| `dataset_count_by_construct` | Dataset | Map[ConstructId→Integer] | Frequency charts/treemap/pareto/heatmap | Absolute usage of each construct in dataset. |
| `dataset_total_construct_instances` | Dataset | Integer | Frequency KPIs | Total counted construct instances. |
| `dataset_relative_frequency_by_construct` | Dataset | Map[ConstructId→Float] | Share heatmap + pareto | Relative usage profile by construct. |
| `dataset_utilization_entropy` | Dataset | Float (0..1) | Frequency KPIs | Evenness of construct utilization. |
| `score = dataset_utilization_entropy*100` | Dataset | Float | Aggregate KPI | Frequency-balance score. |
| `count_by_construct` | Model | Map[ConstructId→Integer] | Per-model frequency heatmaps | Per-model construct counts. |
| `total_construct_instances` | Model | Integer | Totals histogram + top-model table | Model-level volume of construct usage. |
| `relative_frequency_by_construct` | Model | Map[ConstructId→Float] | Share heatmap | Model-level normalized construct mix. |
| `utilization_entropy` | Model | Float | Entropy histogram | Per-model utilization evenness. |

### D4.M1 **Model Size**

| Metric (informal) | Level | Datatype | Reporting | Used for |
| --- | --- | --- | --- | --- |
| `total_node_count, total_edge_count, total_element_count` | Dataset | Integer | Model-size KPIs | Aggregate structural volume. |
| `node_count_stats, edge_count_stats, element_count_stats` (`DistributionSummary`) | Dataset | Object | KPI stats panels | Distribution of size metrics across models. |
| `edge_node_ratio_stats` (`DistributionSummary`) | Dataset | Object | KPI stats panels | Distribution of edge density (`edges/nodes`). |
| `node_count, edge_count, element_count, edge_node_ratio` | Model | Integer/Float | Histograms, scatter, top-10 table | Per-model size profile and outlier ranking. |

### D4.M2 **Degree**

| Metric (informal) | Level | Datatype | Reporting | Used for |
| --- | --- | --- | --- | --- |
| `avg_degree_stats, avg_in_degree_stats, avg_out_degree_stats` (`DistributionSummary`) | Dataset | Object | Degree KPIs | Dataset-level connectivity tendency. |
| `degree_median_stats` (`DistributionSummary`) | Dataset | Object | Degree KPIs | Distribution of per-model median node degree. |
| `avg_degree, avg_in_degree, avg_out_degree, degree_median` | Model | Float | Degree histograms + top-10 table | Per-model connectivity intensity and directionality. |
| `degree_stats, in_degree_stats, out_degree_stats` (`DistributionSummary`) | Model | Object | Diagnostics | Intra-model degree distribution details. |

### D4.M3 **Connectivity**

| Metric (informal) | Level | Datatype | Reporting | Used for |
| --- | --- | --- | --- | --- |
| `n_components_stats` (`DistributionSummary`) | Dataset | Object | Connectivity KPIs + component histogram context | Distribution of connected-component counts. |
| `largest_component_size_stats` (`DistributionSummary`) | Dataset | Object | Connectivity KPIs + histogram context | Distribution of largest-component sizes. |
| `isolated_node_count_stats` (`DistributionSummary`) | Dataset | Object | Connectivity KPIs + histogram context | Distribution of isolated-node counts. |
| `isolated_node_share_stats` (`DistributionSummary`) | Dataset | Object | Connectivity KPIs + share histogram context | Distribution of isolation severity. |
| `total_components, total_isolated_nodes` | Dataset | Integer | Connectivity KPIs | Aggregate fragmentation counters. |
| `n_components, largest_component_size, isolated_node_count, isolated_node_share` | Model | Integer/Float | Connectivity histograms + top-10 isolated-share table | Per-model fragmentation diagnostics. |
| `component_size_stats` (`DistributionSummary`) | Model | Object | Diagnostics | Component size spread within each model. |

### D4.M4 **Containment Depth**

| Metric (informal) | Level | Datatype | Reporting | Used for |
| --- | --- | --- | --- | --- |
| `max_depth_stats` (`DistributionSummary`) | Dataset | Object | Depth KPIs + histogram context | Distribution of maximum containment depth per model. |
| `mean_depth_stats` (`DistributionSummary`) | Dataset | Object | Depth KPIs + histogram context | Distribution of mean containment depth per model. |
| `contained_node_share_stats` (`DistributionSummary`) | Dataset | Object | Depth KPIs + share histogram context | Distribution of contained-node shares. |
| `total_contained_nodes, total_root` | Dataset | Integer | Depth KPIs | Aggregate containment counters. |
| `max_depth, mean_depth, median_depth, root_count, contained_node_share` | Model | Integer/Float | Depth histograms + top-10 depth table | Per-model hierarchy depth diagnostics. |
| `depth_stats` (`DistributionSummary`) | Model | Object | Diagnostics | Full node-depth distribution within model. |
