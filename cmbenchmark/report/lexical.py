from __future__ import annotations

from typing import Any, Dict, List, Mapping

from cmbenchmark.report.utils import _get, _is_finite_number, create_histogram_data


def build_lexical_report(
    measures: Mapping[str, Any],
    measures_per_model: Mapping[str, Any],
    ir_index: Mapping[str, Any],
) -> Dict[str, Any]:
    """Build derived lexical report fields (D2.*)."""

    # D2.M1 - Label Presence
    label_presence = _get(measures, "lexical", "d2_m1_label_presence")
    if isinstance(label_presence, Mapping):
        eligible = int(label_presence.get("dataset_label_eligible_count", 0) or 0)
        present = int(label_presence.get("dataset_label_present_count", 0) or 0)
        label_presence_chart_data = {
            "present": present,
            "missing": eligible - present,
            "presentShare": float(label_presence.get("dataset_label_present_share", 0) or 0),
            "missingShare": float(label_presence.get("dataset_label_missing_share", 0) or 0),
        }
        lm_by_type = label_presence.get("label_missing_count_by_type") or {}
    else:
        label_presence_chart_data = None
        lm_by_type = {}
    if not isinstance(lm_by_type, Mapping):
        lm_by_type = {}
    label_presence_by_type = sorted(
        [{"type": str(t), "missingCount": int(c or 0)} for t, c in lm_by_type.items()],
        key=lambda x: x["missingCount"],
        reverse=True,
    )

    d2_m1 = _get(measures_per_model, "lexical", "d2_m1_label_presence", default={})
    if not isinstance(d2_m1, Mapping):
        d2_m1 = {}
    label_missing_rows: List[Dict[str, Any]] = []
    if d2_m1:
        for model_id, data in d2_m1.items():
            if not isinstance(data, Mapping):
                continue
            eligible = int(data.get("label_eligible_count", 0) or 0)
            present = int(data.get("label_present_count", 0) or 0)
            missing = max(0, eligible - present)
            if missing <= 0:
                continue
            label_missing_rows.append(
                {
                    "modelId": model_id,
                    "relpath": str(ir_index.get(model_id) or model_id),
                    "eligibleCount": eligible,
                    "presentCount": present,
                    "missingCount": missing,
                }
            )
    label_missing_top10 = sorted(label_missing_rows, key=lambda x: x["missingCount"], reverse=True)[:10]

    # D2.M2 - Label Length
    label_length = _get(measures, "lexical", "d2_m2_label_length")
    d2_m2 = _get(measures_per_model, "lexical", "d2_m2_label_length", default={})
    if not isinstance(d2_m2, Mapping):
        d2_m2 = {}
    label_length_chars_medians = [
        v.get("label_length_chars_median") for v in d2_m2.values() if isinstance(v, Mapping)
    ]
    label_length_tokens_medians = [
        v.get("label_length_tokens_median") for v in d2_m2.values() if isinstance(v, Mapping)
    ]
    label_length_chars_histogram = create_histogram_data(label_length_chars_medians)
    label_length_tokens_histogram = create_histogram_data(label_length_tokens_medians)
    label_length_top10 = (
        sorted(
            [
                {
                    "modelId": model_id,
                    "relpath": str(ir_index.get(model_id) or model_id),
                    "charsMedian": float(data.get("label_length_chars_median", 0) or 0),
                    "tokensMedian": float(data.get("label_length_tokens_median", 0) or 0),
                    "shortShare": float(data.get("short_label_share", 0) or 0),
                    "longShare": float(data.get("long_label_share", 0) or 0),
                }
                for model_id, data in d2_m2.items()
                if isinstance(data, Mapping)
            ],
            key=lambda x: x["charsMedian"],
            reverse=True,
        )[:10]
        if d2_m2
        else []
    )

    # D2.M3 - Naming Convention
    naming_convention = _get(measures, "lexical", "d2_m3_naming_convention")
    if isinstance(naming_convention, Mapping):
        counts = naming_convention.get("dataset_case_style_counts") or {}
        shares = naming_convention.get("dataset_case_style_share") or {}
    else:
        counts, shares = {}, {}
    if not isinstance(counts, Mapping):
        counts = {}
    if not isinstance(shares, Mapping):
        shares = {}
    naming_convention_chart_data = [
        {
            "caseStyle": str(case_style),
            "count": int(count or 0),
            "share": float(shares.get(case_style, 0) or 0),
        }
        for case_style, count in counts.items()
    ]
    d2_m3 = _get(measures_per_model, "lexical", "d2_m3_naming_convention", default={})
    if not isinstance(d2_m3, Mapping):
        d2_m3 = {}
    naming_style_entropies = [
        float(x)
        for x in (v.get("naming_style_entropy") for v in d2_m3.values() if isinstance(v, Mapping))
        if _is_finite_number(x)
    ]
    naming_style_entropy_histogram = create_histogram_data(naming_style_entropies)

    # D2.M4 - Single vs Multi Word
    single_multi_word = _get(measures, "lexical", "d2_m4_single_multi_word")
    if isinstance(single_multi_word, Mapping):
        single = int(single_multi_word.get("total_single_word_labels", 0) or 0)
        multi = int(single_multi_word.get("total_multi_word_labels", 0) or 0)
        single_share = float(single_multi_word.get("dataset_share_single_word_labels", 0) or 0)
        single_multi_word_chart_data = {
            "single": single,
            "multi": multi,
            "singleShare": single_share,
            "multiShare": 1 - single_share,
        }
    else:
        single_multi_word_chart_data = None
    d2_m4 = _get(measures_per_model, "lexical", "d2_m4_single_multi_word", default={})
    if not isinstance(d2_m4, Mapping):
        d2_m4 = {}
    single_word_shares = [
        float(x)
        for x in (v.get("single_word_label_share") for v in d2_m4.values() if isinstance(v, Mapping))
        if _is_finite_number(x)
    ]
    single_word_share_histogram = create_histogram_data(single_word_shares)

    # D2.M5 - Lexical Diversity
    lexical_diversity = _get(measures, "lexical", "d2_m5_lexical_diversity")
    d2_m5 = _get(measures_per_model, "lexical", "d2_m5_lexical_diversity", default={})
    if not isinstance(d2_m5, Mapping):
        d2_m5 = {}
    lexical_diversity_top10 = (
        sorted(
            [
                {
                    "modelId": model_id,
                    "relpath": str(ir_index.get(model_id) or model_id),
                    "totalTokens": int(data.get("total_tokens", 0) or 0),
                    "vocabSize": int(data.get("vocab_size", 0) or 0),
                    "typeTokenRatio": float(data.get("type_token_ratio", 0) or 0),
                }
                for model_id, data in d2_m5.items()
                if isinstance(data, Mapping)
            ],
            key=lambda x: x["typeTokenRatio"],
            reverse=True,
        )[:10]
        if d2_m5
        else []
    )

    # D2.M6 - Language Usage
    language_usage = _get(measures, "lexical", "d2_m6_language_usage")
    d2_m6 = _get(measures_per_model, "lexical", "d2_m6_language_usage", default={})
    if not isinstance(d2_m6, Mapping):
        d2_m6 = {}

    lang_counts_raw = (
        _get(language_usage, "language_counts", default={}) if isinstance(language_usage, Mapping) else {}
    )
    if not isinstance(lang_counts_raw, Mapping):
        lang_counts_raw = {}

    # Prefer dataset-level counts, but fall back to per-model if needed.
    lang_counts: Dict[str, int] = {
        str(k): int(v or 0) for k, v in lang_counts_raw.items() if int(v or 0) >= 0
    }
    if not lang_counts and d2_m6:
        for v in d2_m6.values():
            if not isinstance(v, Mapping):
                continue
            code = v.get("language") or "unknown"
            lang_counts[str(code)] = lang_counts.get(str(code), 0) + 1

    total_models_for_lang = sum(lang_counts.values())
    language_usage_data = sorted(
        [
            {
                "language": lang,
                "count": int(cnt),
                "share": (int(cnt) / total_models_for_lang) if total_models_for_lang > 0 else 0.0,
            }
            for lang, cnt in lang_counts.items()
            if int(cnt) > 0
        ],
        key=lambda x: x["count"],
        reverse=True,
    )

    # Pie chart: keep it readable (top 8 + Other)
    language_usage_pie_data: List[Dict[str, Any]] = []
    if language_usage_data:
        top_n = 8
        top = language_usage_data[:top_n]
        rest = language_usage_data[top_n:]
        other_count = sum(int(x.get("count", 0) or 0) for x in rest)
        other_share = sum(float(x.get("share", 0) or 0) for x in rest)
        language_usage_pie_data = [
            {"name": str(x["language"]), "value": int(x["count"]), "share": float(x["share"])}
            for x in top
        ]
        if other_count > 0:
            language_usage_pie_data.append({"name": "other", "value": int(other_count), "share": float(other_share)})

    return {
        "labelPresence": label_presence,
        "labelPresenceChartData": label_presence_chart_data,
        "labelPresenceByType": label_presence_by_type,
        "labelMissingTop10": label_missing_top10,
        "labelLength": label_length,
        "labelLengthCharsHistogram": label_length_chars_histogram,
        "labelLengthTokensHistogram": label_length_tokens_histogram,
        "labelLengthTop10": label_length_top10,
        "namingConvention": naming_convention,
        "namingConventionChartData": naming_convention_chart_data,
        "namingStyleEntropies": naming_style_entropies,
        "namingStyleEntropyHistogram": naming_style_entropy_histogram,
        "singleMultiWord": single_multi_word,
        "singleMultiWordChartData": single_multi_word_chart_data,
        "singleWordShares": single_word_shares,
        "singleWordShareHistogram": single_word_share_histogram,
        "lexicalDiversity": lexical_diversity,
        "lexicalDiversityTop10": lexical_diversity_top10,
        "languageUsage": language_usage,
        "languageUsageData": language_usage_data,
        "languageUsagePieData": language_usage_pie_data,
    }

