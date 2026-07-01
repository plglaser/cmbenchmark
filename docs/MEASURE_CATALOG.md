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
>
> Interpretations describe the usual quality reading. They are not universal value judgments as for example, broad construct coverage is useful when a dataset should exercise a language broadly, but can indicate noise when the task expects only a focused subset of concepts.

### D1.M1 **Parse Status**

| Metric (informal) | Level | Datatype | Reporting | Used for | Interpretation |
| --- | --- | --- | --- | --- | --- |
| `n_models` | Dataset | Integer | Aggregate KPI | Denominator for all parsing status shares and indices. | Context only. Larger means a larger evaluation base, not better quality by itself. |
| `n_success, n_partial, n_failed` | Dataset | Integer | Status distribution bar chart (counts) | Absolute status distribution. | More successes are better. More partials or failures indicate reduced processability. |
| `share_success, share_partial, share_failed` | Dataset | Float | Status distribution bar/pie chart (shares) | Normalized status distribution for comparability across datasets. | Values in [0,1]. Higher success share is better, while higher partial or failed share is worse. |
| `parsing_robustness_index = (n_success + 0.5*n_partial)/n_models` | Dataset | Float | Aggregate KPI | Unscaled robustness index used to compute score. | Values in [0,1]. Higher is better because partial parses are discounted and failures contribute zero. |
| `score = ((n_success + 0.5*n_partial)/n_models)*100` | Dataset | Float | Aggregate KPI, score badge | Single robustness signal that discounts partial and failed parses. Summarizes the whole D1.M1 measure. | Values in [0,100]. Higher indicates better parser robustness for the dataset. |
| `parse_status ∈ {success, warning, failure}` | Model | Enum/String | Per-model table (`warning` shown as “Partial” in UI) | Identifies problematic models and eligibility for downstream measures. | `success` is best for downstream evidence. `warning` means usable but partial/diagnostic. `failure` excludes the model from IR-based measures. |
| `parse_error_msg` | Model | String (optional) | Per-model table | Diagnostics. Attached when parsing fails. | Diagnostic only. Presence explains a failure and is not numeric quality evidence. |

### D1.M2 **Elements Loaded vs Skipped**

| Metric (informal) | Level | Datatype | Reporting | Used for | Interpretation |
| --- | --- | --- | --- | --- | --- |
| `total_elements_loaded` | Dataset | Integer | Summary KPIs | Total loaded elements across non-failed models. | Higher usually means more analyzable content, but depends on dataset size and intended scope. |
| `total_elements_skipped` | Dataset | Integer | Summary KPIs | Total skipped elements across non-failed models. | Lower is better. Skipped content means the parser did not materialize part of the source model. |
| `dataset_skip_ratio = total_skipped/(total_loaded+total_skipped)` | Dataset | Float | Summary KPIs | Dataset-level skip intensity. | Values in [0,1]. Lower is better, with 0 meaning no observed skips. |
| `skip_ratio_stats` (`DistributionSummary`) | Dataset | Object | Summary KPIs | Mean/median spread of per-model skip ratios. | Lower center and tighter spread are better. High upper quantiles identify uneven parser coverage. |
| `n_models_with_skips` | Dataset | Integer | Summary KPIs | Count of models with at least one skipped element. | Lower is better after accounting for dataset size. |
| `share_models_with_skips` | Dataset | Float | Summary KPIs | Share of models affected by skips. | Values in [0,1]. Lower is better because fewer models lose content. |
| `score = (1 - dataset_skip_ratio)*100` | Dataset | Float | Aggregate KPI | Quality signal based on skip ratio. | Values in [0,100]. Higher is better and means less skipped content. |
| `elements_loaded, elements_skipped, skip_ratio` | Model | Integer, Integer, Float | Skip ratio histogram + Top-10 table | Per-model skip diagnostics and outlier ranking. | More loaded content is contextual. Fewer skipped elements and lower skip ratio are better. |

### D1.M3 **Parsing Time**

| Metric (informal) | Level | Datatype | Reporting | Used for | Interpretation |
| --- | --- | --- | --- | --- | --- |
| `parse_time_stats` (`DistributionSummary`) | Dataset | Object | Statistics/KPI block | Distribution of parse times (ms) across non-failed models. | Lower center and upper quantiles indicate better runtime scalability for comparable model sizes. |
| `parse_time_total_ms` | Dataset | Integer | KPI | Total parsing runtime across dataset. | Lower is faster, but only comparable for similar dataset sizes and hardware. |
| `parse_time_ms` | Model | Integer | Parse-time histogram, size-vs-time scatter | Per-model runtime and scalability/outlier analysis. | Lower is faster. High values are primarily outlier diagnostics and should be read with model size. |

### D1.M4 **File Size**

| Metric (informal) | Level | Datatype | Reporting | Used for | Interpretation |
| --- | --- | --- | --- | --- | --- |
| `file_size_source_stats` (`DistributionSummary`) | Dataset | Object | Statistics/KPI block | Distribution of source file sizes. | Descriptive only. Larger files often imply larger or more verbose models, not necessarily better or worse quality. |
| `file_size_ir_stats` (`DistributionSummary`) | Dataset | Object | Statistics/KPI block | Distribution of generated IR sizes. | Descriptive only. Larger IRs may reflect richer extraction or verbosity. Interpret with parser/profile. |
| `file_size_bytes_source` | Model | Integer | Source-size histogram, top/bottom-10 tables, parse-time scatter x-axis | Per-model source size for ranking and correlation. | Descriptive/context metric. Useful for normalization and outlier analysis. |
| `file_size_bytes_ir` | Model | Integer | IR-size histogram, top/bottom-10 tables | Per-model IR size for comparison with source size. | Descriptive/context metric. Unexpectedly small IRs can indicate missing extraction, while large IRs can indicate detail or verbosity. |

### D1.M5 **Warnings**

| Metric (informal) | Level | Datatype | Reporting | Used for | Interpretation |
| --- | --- | --- | --- | --- | --- |
| `n_models_with_warnings` | Dataset | Integer | KPI | Number of models that emitted warnings. | Lower is better after accounting for dataset size. |
| `share_models_with_warnings` | Dataset | Float | KPI | Dataset-level warning prevalence. | Values in [0,1]. Lower is better because fewer models required diagnostic handling. |
| `warning_count_stats` (`DistributionSummary`) | Dataset | Object | KPI/summary | Distribution of warning counts per model. | Lower center and upper quantiles are better. High values indicate parser/model compatibility issues. |
| `warnings_per_element_stats` (`DistributionSummary`) | Dataset | Object | KPI/summary | Distribution of warning density normalized by elements. | Lower is better. Normalization makes warning intensity comparable across model sizes. |
| `total_warnings_by_type` | Dataset | Map[String→Integer] | Warnings-by-type chart | Dominant warning categories across dataset. | Diagnostic. High counts identify recurring parser limitations or dataset issues. |
| `n_models_with_warning_type` | Dataset | Map[String→Integer] | Diagnostics table/summary | Model coverage per warning type. | Diagnostic. Lower is generally better for severe warning types, but interpretation depends on warning semantics. |
| `share_models_with_warning_type` | Dataset | Map[String→Float] | Diagnostics table/summary | Prevalence share per warning type. | Values in [0,1]. Lower is generally better for problematic warning types. |
| `score = (1 - share_models_with_warnings)*100` | Dataset | Float | Aggregate KPI | Parsing quality signal based on warning prevalence. | Values in [0,100]. Higher is better because fewer models produced warnings. |
| `warning_count, warnings_by_type, warnings_per_element` | Model | Integer, Map, Float | Top models with warnings table | Per-model warning diagnostics and ranking. | Lower warning count/density is better. Warning types explain the likely cause. |

### D2.M1 **Label Presence**

| Metric (informal) | Level | Datatype | Reporting | Used for | Interpretation |
| --- | --- | --- | --- | --- | --- |
| `dataset_label_eligible_count` | Dataset | Integer | Presence KPIs | Total eligible label slots. | Context only. Larger means more opportunities for labels, not better quality by itself. |
| `dataset_label_present_count` | Dataset | Integer | Presence KPIs | Number of non-empty labels. | Higher is usually better relative to eligible slots. |
| `dataset_label_present_share` | Dataset | Float | Presence chart + KPIs | Overall label completeness. | Values in [0,1]. Higher is better when labels are expected to support understandability. |
| `dataset_label_missing_share` | Dataset | Float | Presence chart + KPIs | Overall label missingness. | Values in [0,1]. Lower is better when eligible elements should be named. |
| `label_present_share_stats` (`DistributionSummary`) | Dataset | Object | Presence KPIs | Distribution of per-model present shares. | Higher center and lower spread toward zero indicate more consistent label completeness. |
| `label_missing_share_stats` (`DistributionSummary`) | Dataset | Object | Presence KPIs | Distribution of per-model missing shares. | Lower center and upper quantiles are better. |
| `label_missing_count_by_type` | Dataset | Map[String→Integer] | Missing-by-type chart | Which element types miss labels most. | Diagnostic. High counts identify element types where naming quality is weak or labels may not be expected. |
| `score = dataset_label_present_share*100` | Dataset | Float | Aggregate KPI | Label completeness quality score. | Values in [0,100]. Higher is better under profiles where eligible elements should be labeled. |
| `label_eligible_count, label_present_count, label_present_share, label_missing_share, label_missing_count_by_type` | Model | Integer/Float/Map | Top-10 missing-label models table | Per-model completeness diagnostics and ranking. | Higher present share and lower missing share are better. Eligible count gives context. |

### D2.M2 **Label Length**

| Metric (informal) | Level | Datatype | Reporting | Used for | Interpretation |
| --- | --- | --- | --- | --- | --- |
| `label_length_chars_median_stats` (`DistributionSummary`) | Dataset | Object | Length stats + histogram context | Distribution of per-model median character lengths. | Moderate values are usually preferable. Very short labels can be uninformative, very long labels can be unwieldy. |
| `label_length_tokens_median_stats` (`DistributionSummary`) | Dataset | Object | Length stats + histogram context | Distribution of per-model median token lengths. | Moderate values are usually preferable and task-dependent. |
| `short_label_share_stats` (`DistributionSummary`) | Dataset | Object | Length stats | Share of short labels (`<5 chars` or `<2 tokens`) across models. | Lower is often better when short labels are abbreviations, but domain-standard short labels may be valid. |
| `long_label_share_stats` (`DistributionSummary`) | Dataset | Object | Length stats | Share of long labels (`>30 chars` or `>8 tokens`) across models. | Lower is often better for concise modeling labels, but descriptive domains may require longer labels. |
| `label_count` | Model | Integer | Per-model length table | Number of present labels used in length stats. | Context only. Low counts make length statistics less reliable. |
| `label_length_chars_mean, label_length_chars_median, label_length_chars_p95` | Model | Float | Char-length histogram + top-10 table | Per-model character-length profile. | Descriptive. Extreme low or high values indicate labels to inspect. |
| `label_length_tokens_mean, label_length_tokens_median, label_length_tokens_p95` | Model | Float | Token-length histogram + top-10 table | Per-model token-length profile. | Descriptive. Extreme values may indicate underspecified labels or sentence-like labels. |
| `short_label_share, long_label_share` | Model | Float | Top-10 table | Extremes of short/long labels per model. | Values in [0,1]. Lower extremes are usually better, subject to domain vocabulary. |

### D2.M3 **Naming Convention Consistency**

| Metric (informal) | Level | Datatype | Reporting | Used for | Interpretation |
| --- | --- | --- | --- | --- | --- |
| `naming_style_entropy_stats` (`DistributionSummary`) | Dataset | Object | Entropy stats panel | Distribution of per-model naming-style entropy. | Lower entropy means more consistent naming style. Very low is best when a single convention is expected. |
| `dataset_case_style_counts` | Dataset | Map[String→Integer] | Case-style distribution chart | Absolute usage by naming style (camelCase, snake_case, etc.). | Descriptive. Dominance of one expected style suggests consistency. |
| `dataset_case_style_share` | Dataset | Map[String→Float] | Case-style distribution chart | Relative usage by naming style. | Values per style in [0,1]. Higher share for the intended style is better. |
| `case_style_counts` | Model | Map[String→Integer] | Diagnostics | Per-model naming-style frequency counts. | Diagnostic. Mixed counts show convention variation. |
| `case_style_share` | Model | Map[String→Float] | Diagnostics | Per-model naming-style shares. | Higher share for the intended style is better when a naming convention exists. |
| `naming_style_entropy` | Model | Float | Entropy histogram | Per-model naming consistency/diversity indicator. | Lower is more consistent. Higher indicates mixed conventions and is usually worse for readability. |

### D2.M4 **Single vs Multi-Word Labels**

| Metric (informal) | Level | Datatype | Reporting | Used for | Interpretation |
| --- | --- | --- | --- | --- | --- |
| `total_single_word_labels` | Dataset | Integer | Single-vs-multi chart + stats | Total single-token labels in dataset. | Descriptive. Not better by itself because concise and compound labels can both be appropriate. |
| `total_multi_word_labels` | Dataset | Integer | Single-vs-multi chart + stats | Total multi-token labels in dataset. | Descriptive. Not better by itself and depends on modeling style. |
| `dataset_share_single_word_labels` | Dataset | Float | Single-vs-multi chart + stats | Dataset-level preference for single-word labels. | Values in [0,1]. Interpretation is profile-dependent, with extremes suggesting terse or verbose labeling styles. |
| `share_single_word_labels_stats` (`DistributionSummary`) | Dataset | Object | Stats panel + histogram context | Distribution of per-model single-word shares. | Descriptive. High spread means inconsistent label style across models. |
| `single_word_label_count, multi_word_label_count` | Model | Integer | Diagnostics | Per-model tokenization counts for label style. | Descriptive. Compare against model size and domain conventions. |
| `single_word_label_share, multi_word_label_share` | Model | Float | Single-word-share histogram | Per-model label style balance. | Values in [0,1]. Neither direction is universally better, but extreme values may warrant inspection. |

### D2.M5 **Lexical Diversity**

| Metric (informal) | Level | Datatype | Reporting | Used for | Interpretation |
| --- | --- | --- | --- | --- | --- |
| `total_tokens` | Dataset | Integer | Diversity KPIs | Total token volume in labeled text. | Context only. Larger token volume supports more stable diversity estimates. |
| `vocab_size` | Dataset | Integer | Diversity KPIs | Distinct token count. | Higher can indicate richer vocabulary, but may also reflect inconsistent spelling, synonyms, or noise. |
| `type_token_ratio` | Dataset | Float | Diversity KPIs | Dataset-level lexical diversity indicator. | Values in [0,1]. Higher means more diverse vocabulary, but better/worse depends on domain consistency needs. |
| `top_labels` | Dataset | List[(String, Integer)] | Top-labels table | Most frequent normalized label strings. | Diagnostic. High repetition can be expected for common constructs or indicate generic naming. |
| `top_tokens` | Dataset | List[(String, Integer)] | Diagnostics (report data) | Most frequent tokens after tokenization. | Diagnostic. Dominant tokens reveal vocabulary themes or repeated generic terms. |
| `total_tokens, vocab_size, type_token_ratio` | Model | Integer/Float | Top-10 lexical-diversity table | Per-model diversity ranking and comparison. | Token counts give context. Higher diversity is useful for varied domains but can indicate inconsistency in controlled vocabularies. |

### D2.M6 **Language Usage**

| Metric (informal) | Level | Datatype | Reporting | Used for | Interpretation |
| --- | --- | --- | --- | --- | --- |
| `language_counts` | Dataset | Map[String→Integer] | Language distribution pie/bar + KPIs | Dataset language composition (`en`, `de`, `unknown`, ...). | Descriptive. A dominant expected language improves comparability, while mixed/unknown language may affect lexical analyses. |
| `language` | Model | String (ISO-like code or `unknown`) | Aggregated into language charts | Per-model detected language from merged label text. | Diagnostic. `unknown` or unexpected languages reduce confidence in language-dependent measures. |

### D3.M1 **Construct Presence**

| Metric (informal) | Level | Datatype | Reporting | Used for | Interpretation |
| --- | --- | --- | --- | --- | --- |
| `constructs_available_count` | Dataset | Integer | Coverage KPIs/chart | Denominator of catalog constructs (excluding `UNKNOWN*`). | Context only. Defines the construct universe for the selected profile. |
| `constructs_observed_count` | Dataset | Integer | Coverage KPIs/chart | Number of constructs observed at least once. | Higher indicates broader coverage of the construct catalog, but may be noise if the benchmark expects a narrow subset. |
| `coverage_share = observed/available` | Dataset | Float | Coverage KPIs/chart | Dataset construct coverage. | Values in [0,1]. Higher is better for broad-coverage benchmarks, but task-dependent for focused datasets. |
| `coverage_share_stats` (`DistributionSummary`) | Dataset | Object | Coverage-share histogram context | Distribution of per-model coverage shares. | Higher center indicates broader per-model coverage. High spread means models differ strongly in construct breadth. |
| `unknown_type_share_dataset` | Dataset | Float | Coverage KPIs | Share of elements with unknown types dataset-wide. | Values in [0,1]. Lower is better because unknown types reduce interpretability and profile fit. |
| `unknown_node_type_count_dataset, unknown_edge_type_count_dataset` | Dataset | Integer | Unknown-types diagnostics | Absolute unknown-type counts by kind. | Lower is better after accounting for dataset size. |
| `unknown_type_examples_dataset` | Dataset | Map[String→Integer] | Unknown-types table | Top unknown raw types (dataset-level). | Diagnostic. Frequent unknown examples indicate missing mappings or out-of-profile content. |
| `construct_catalog` | Dataset | Map[ConstructId→Metadata] | KPIs/matrix/filtering | Metadata for labels, groups, and kinds in UI/report. | Reference data only. No quality direction. |
| `missing_constructs` | Dataset | List[Object] | Missing-constructs table | Constructs never observed in dataset. | Diagnostic. Missing constructs are bad for broad-coverage benchmarks but expected for focused tasks. |
| `coverage_by_group, coverage_by_kind` | Dataset | Map[String→Object] | Coverage-by-group charts | Coverage breakdown by semantic grouping. | Higher coverage in expected groups is better. Unexpected groups may indicate noise or scope drift. |
| `score = coverage_share*(1-unknown_type_share_dataset)*100` | Dataset | Float | Aggregate KPI | Presence quality score balancing coverage and unknowns. | Values in [0,100]. Higher is better when broad construct coverage and low unknown share are desired. |
| `constructs_available_count, constructs_observed_count, coverage_share` | Model | Integer/Float | Coverage matrix + lowest/highest coverage tables | Per-model construct coverage strength. | Higher coverage means broader construct use, but the desired level depends on the task and model type. |
| `present_constructs` | Model | Map[ConstructId→Bool] | Coverage matrix | Construct-by-model presence grid. | Diagnostic. Expected constructs should be present, unexpected constructs may indicate noise. |
| `unknown_node_type_count, unknown_edge_type_count, unknown_type_share, unknown_type_examples` | Model | Integer/Float/Map | Coverage outlier tables + unknown-share histogram | Per-model unknown-type diagnostics. | Lower unknown counts/share are better. Examples explain parser or profile gaps. |

### D3.M3 **Construct Frequency**

| Metric (informal) | Level | Datatype | Reporting | Used for | Interpretation |
| --- | --- | --- | --- | --- | --- |
| `dataset_count_by_construct` | Dataset | Map[ConstructId→Integer] | Frequency charts/treemap/pareto/heatmap | Absolute usage of each construct in dataset. | Descriptive. Expected constructs should appear, while dominant unexpected constructs can indicate noise. |
| `dataset_total_construct_instances` | Dataset | Integer | Frequency KPIs | Total counted construct instances. | Context only. Larger totals support more stable frequency estimates. |
| `dataset_relative_frequency_by_construct` | Dataset | Map[ConstructId→Float] | Share heatmap + pareto | Relative usage profile by construct. | Values per construct in [0,1]. Desirable profile depends on expected construct mix. |
| `dataset_utilization_entropy` | Dataset | Float (0..1) | Frequency KPIs | Evenness of construct utilization. | Values in [0,1]. Higher means more even use, useful for balanced-coverage benchmarks but not always better for specialized tasks. |
| `score = dataset_utilization_entropy*100` | Dataset | Float | Aggregate KPI | Frequency-balance score. | Values in [0,100]. Higher means more balanced construct utilization under profiles where balance is desired. |
| `count_by_construct` | Model | Map[ConstructId→Integer] | Per-model frequency heatmaps | Per-model construct counts. | Diagnostic. Counts should match the expected modeling task and scale. |
| `total_construct_instances` | Model | Integer | Totals histogram + top-model table | Model-level volume of construct usage. | Context only. Larger models naturally tend to have more instances. |
| `relative_frequency_by_construct` | Model | Map[ConstructId→Float] | Share heatmap | Model-level normalized construct mix. | Values per construct in [0,1]. Compare against expected construct mix. |
| `utilization_entropy` | Model | Float | Entropy histogram | Per-model utilization evenness. | Higher means more even construct use. Desirable only when the model is expected to exercise multiple constructs. |

### D4.M1 **Model Size**

| Metric (informal) | Level | Datatype | Reporting | Used for | Interpretation |
| --- | --- | --- | --- | --- | --- |
| `total_node_count, total_edge_count, total_element_count` | Dataset | Integer | Model-size KPIs | Aggregate structural volume. | Context only. Larger datasets/models are not inherently better or worse. |
| `node_count_stats, edge_count_stats, element_count_stats` (`DistributionSummary`) | Dataset | Object | KPI stats panels | Distribution of size metrics across models. | Descriptive. Extremes and spread identify unusually small or large models. |
| `edge_node_ratio_stats` (`DistributionSummary`) | Dataset | Object | KPI stats panels | Distribution of edge density (`edges/nodes`). | Descriptive. Higher means denser relational structure, but desirability depends on language and task. |
| `node_count, edge_count, element_count, edge_node_ratio` | Model | Integer/Float | Histograms, scatter, top-10 table | Per-model size profile and outlier ranking. | Descriptive. Useful for outlier detection and normalizing other measures. |

### D4.M2 **Degree**

| Metric (informal) | Level | Datatype | Reporting | Used for | Interpretation |
| --- | --- | --- | --- | --- | --- |
| `avg_degree_stats, avg_in_degree_stats, avg_out_degree_stats` (`DistributionSummary`) | Dataset | Object | Degree KPIs | Dataset-level connectivity tendency. | Higher means more connected models. Better/worse depends on expected modeling style and may flag over- or under-connected structures. |
| `degree_median_stats` (`DistributionSummary`) | Dataset | Object | Degree KPIs | Distribution of per-model median node degree. | Descriptive. Very low values can indicate sparse or fragmented models, while very high values can indicate dense hubs. |
| `avg_degree, avg_in_degree, avg_out_degree, degree_median` | Model | Float | Degree histograms + top-10 table | Per-model connectivity intensity and directionality. | Descriptive. Interpret with model type because neither high nor low degree is universally better. |
| `degree_stats, in_degree_stats, out_degree_stats` (`DistributionSummary`) | Model | Object | Diagnostics | Intra-model degree distribution details. | Diagnostic. Skew and outliers reveal hubs, isolated areas, or unusual directionality. |

### D4.M3 **Connectivity**

| Metric (informal) | Level | Datatype | Reporting | Used for | Interpretation |
| --- | --- | --- | --- | --- | --- |
| `n_components_stats` (`DistributionSummary`) | Dataset | Object | Connectivity KPIs + component histogram context | Distribution of connected-component counts. | Lower usually means less fragmentation when one coherent model graph is expected. |
| `largest_component_size_stats` (`DistributionSummary`) | Dataset | Object | Connectivity KPIs + histogram context | Distribution of largest-component sizes. | Higher relative to model size usually indicates a more coherent graph. |
| `isolated_node_count_stats` (`DistributionSummary`) | Dataset | Object | Connectivity KPIs + histogram context | Distribution of isolated-node counts. | Lower is usually better when elements should participate in relations. |
| `isolated_node_share_stats` (`DistributionSummary`) | Dataset | Object | Connectivity KPIs + share histogram context | Distribution of isolation severity. | Values in [0,1]. Lower usually indicates better structural integration. |
| `total_components, total_isolated_nodes` | Dataset | Integer | Connectivity KPIs | Aggregate fragmentation counters. | Lower is usually better after accounting for dataset/model size. |
| `n_components, largest_component_size, isolated_node_count, isolated_node_share` | Model | Integer/Float | Connectivity histograms + top-10 isolated-share table | Per-model fragmentation diagnostics. | Fewer components and isolated nodes are usually better. Largest component should be read relative to model size. |
| `component_size_stats` (`DistributionSummary`) | Model | Object | Diagnostics | Component size spread within each model. | Diagnostic. Many tiny components indicate fragmentation unless the task expects separate submodels. |

### D4.M4 **Containment Depth**

| Metric (informal) | Level | Datatype | Reporting | Used for | Interpretation |
| --- | --- | --- | --- | --- | --- |
| `max_depth_stats` (`DistributionSummary`) | Dataset | Object | Depth KPIs + histogram context | Distribution of maximum containment depth per model. | Descriptive. Deeper structures can reflect meaningful hierarchy or over-nesting. |
| `mean_depth_stats` (`DistributionSummary`) | Dataset | Object | Depth KPIs + histogram context | Distribution of mean containment depth per model. | Descriptive. Moderate/deeper values suggest hierarchical organization, but ideal depth is language- and task-dependent. |
| `contained_node_share_stats` (`DistributionSummary`) | Dataset | Object | Depth KPIs + share histogram context | Distribution of contained-node shares. | Values in [0,1]. Higher means more nodes participate in containment, usually better when containment is expected. |
| `total_contained_nodes, total_root` | Dataset | Integer | Depth KPIs | Aggregate containment counters. | Context only. Many roots may indicate fragmentation or expected independent top-level elements. |
| `max_depth, mean_depth, median_depth, root_count, contained_node_share` | Model | Integer/Float | Depth histograms + top-10 depth table | Per-model hierarchy depth diagnostics. | Higher contained-node share is usually better. Depth/root counts depend on the expected hierarchy. |
| `depth_stats` (`DistributionSummary`) | Model | Object | Diagnostics | Full node-depth distribution within model. | Diagnostic. Extreme depth or many roots should be inspected against the modeling task. |
