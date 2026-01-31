import { useMemo } from 'react';
import type { ReportResponse } from '../types/api';

export function useReportData(reportData: ReportResponse | null) {
  return useMemo(() => {
    if (!reportData) return null;

    const measures = reportData.measures;
    const measuresPerModel = reportData.measures_per_model;
    const irInfo = reportData.ir_info;

    // Helper function to create histogram data
    const createHistogramData = (values: number[], bins: number = 20) => {
      if (values.length === 0) return [];
      const min = Math.min(...values);
      const max = Math.max(...values);
      if (min === max) return [{ bin: `${min}`, count: values.length }];
      const binWidth = (max - min) / bins;
      const binsData: number[] = new Array(bins).fill(0);
      values.forEach((v) => {
        const binIndex = Math.min(Math.floor((v - min) / binWidth), bins - 1);
        binsData[binIndex]++;
      });
      return binsData.map((count, i) => ({
        bin: `${(min + i * binWidth).toFixed(0)}-${(min + (i + 1) * binWidth).toFixed(0)}`,
        count,
      }));
    };

    // D1.M1 - Parse Status
    const parseStatus = measures?.parsing?.d1_m1_parse_status;
    const parseStatusChartData = parseStatus
      ? [
          { name: 'Success', value: parseStatus.n_success, share: parseStatus.share_success },
          { name: 'Partial', value: parseStatus.n_partial, share: parseStatus.share_partial },
          { name: 'Failure', value: parseStatus.n_failed, share: parseStatus.share_failed },
        ]
      : [];

    // D1.M2 - Elements & Skips
    const skipRatios =
      measuresPerModel?.parsing?.d1_m2_elements_loaded_skipped
        ? Object.values(measuresPerModel.parsing.d1_m2_elements_loaded_skipped).map(
            (m: any) => m.skip_ratio
          )
        : [];
    const skipRatioHistogram = createHistogramData(skipRatios);
    const skipRatioTop10 = measuresPerModel?.parsing?.d1_m2_elements_loaded_skipped
      ? Object.entries(measuresPerModel.parsing.d1_m2_elements_loaded_skipped)
          .map(([modelId, data]: [string, any]) => ({
            modelId,
            skipRatio: data.skip_ratio,
            elementsLoaded: data.elements_loaded,
            elementsSkipped: data.elements_skipped,
            relpath: irInfo?.index?.[modelId] || modelId,
          }))
          .sort((a, b) => b.skipRatio - a.skipRatio)
          .slice(0, 10)
      : [];

    // D1.M3 - Parsing Time
    const parseTimes =
      measuresPerModel?.parsing?.d1_m3_parsing_time
        ? Object.values(measuresPerModel.parsing.d1_m3_parsing_time).map((m: any) => m.parse_time_ms)
        : [];
    const parseTimeHistogram = createHistogramData(parseTimes);
    const parseTimeScatterData = measuresPerModel?.parsing?.d1_m3_parsing_time &&
      measuresPerModel?.parsing?.d1_m4_file_size
      ? Object.keys(measuresPerModel.parsing.d1_m3_parsing_time)
          .map((modelId) => {
            const timeData = measuresPerModel.parsing.d1_m3_parsing_time[modelId];
            const sizeData = measuresPerModel.parsing.d1_m4_file_size[modelId];
            return {
              fileSize: sizeData?.file_size_bytes_source || 0,
              parseTime: timeData?.parse_time_ms || 0,
            };
          })
          .filter((d) => d.fileSize > 0 && d.parseTime > 0)
      : [];

    // D1.M4 - File Sizes
    const sourceSizes =
      measuresPerModel?.parsing?.d1_m4_file_size
        ? Object.values(measuresPerModel.parsing.d1_m4_file_size).map(
            (m: any) => m.file_size_bytes_source
          )
        : [];
    const irSizes =
      measuresPerModel?.parsing?.d1_m4_file_size
        ? Object.values(measuresPerModel.parsing.d1_m4_file_size).map(
            (m: any) => m.file_size_bytes_ir
          )
        : [];
    const sourceSizeHistogram = createHistogramData(sourceSizes);
    const irSizeHistogram = createHistogramData(irSizes);
    const fileSizeTop10 = measuresPerModel?.parsing?.d1_m4_file_size
      ? Object.entries(measuresPerModel.parsing.d1_m4_file_size)
          .map(([modelId, data]: [string, any]) => ({
            modelId,
            sourceSize: data.file_size_bytes_source,
            irSize: data.file_size_bytes_ir,
            relpath: irInfo?.index?.[modelId] || modelId,
          }))
          .sort((a, b) => b.sourceSize - a.sourceSize)
          .slice(0, 10)
      : [];

    // D1.M5 - Warnings
    const warningsByType = measures?.parsing?.d1_m5_warnings?.total_warnings_by_type || {};
    const warningsChartData = Object.entries(warningsByType).map(([type, count]) => ({
      type,
      count: count as number,
    }));
    const modelsWithWarnings = measuresPerModel?.parsing?.d1_m5_warnings
      ? Object.entries(measuresPerModel.parsing.d1_m5_warnings)
          .map(([modelId, data]: [string, any]) => ({
            modelId,
            warningCount: data.warning_count,
            warningsByType: data.warnings_by_type || {},
            relpath: irInfo?.index?.[modelId] || modelId,
          }))
          .filter((m) => m.warningCount > 0)
          .sort((a, b) => b.warningCount - a.warningCount)
          .slice(0, 10)
      : [];

    // D2.M1 - Label Presence
    const labelPresence = measures?.lexical?.d2_m1_label_presence;
    const labelPresenceChartData = labelPresence
      ? {
          present: labelPresence.dataset_label_present_count,
          missing: labelPresence.dataset_label_eligible_count - labelPresence.dataset_label_present_count,
          presentShare: labelPresence.dataset_label_present_share,
          missingShare: labelPresence.dataset_label_missing_share,
        }
      : null;
    const labelPresenceByType = labelPresence?.label_missing_share_by_type
      ? Object.entries(labelPresence.label_missing_share_by_type).map(([type, share]) => ({
          type,
          missingShare: share as number,
        }))
      : [];

    // D2.M2 - Label Length
    const labelLength = measures?.lexical?.d2_m2_label_length;
    const labelLengthCharsMedians =
      measuresPerModel?.lexical?.d2_m2_label_length
        ? Object.values(measuresPerModel.lexical.d2_m2_label_length).map((m: any) => m.label_length_chars_median)
        : [];
    const labelLengthTokensMedians =
      measuresPerModel?.lexical?.d2_m2_label_length
        ? Object.values(measuresPerModel.lexical.d2_m2_label_length).map((m: any) => m.label_length_tokens_median)
        : [];
    const labelLengthCharsHistogram = createHistogramData(labelLengthCharsMedians);
    const labelLengthTokensHistogram = createHistogramData(labelLengthTokensMedians);
    const labelLengthTop10 = measuresPerModel?.lexical?.d2_m2_label_length
      ? Object.entries(measuresPerModel.lexical.d2_m2_label_length)
          .map(([modelId, data]: [string, any]) => ({
            modelId,
            relpath: irInfo?.index?.[modelId] || modelId,
            charsMedian: data.label_length_chars_median,
            tokensMedian: data.label_length_tokens_median,
            shortShare: data.short_label_share,
            longShare: data.long_label_share,
          }))
          .sort((a, b) => b.charsMedian - a.charsMedian)
          .slice(0, 10)
      : [];

    // D2.M3 - Naming Convention
    const namingConvention = measures?.lexical?.d2_m3_naming_convention;
    const namingConventionChartData = namingConvention?.dataset_case_style_counts
      ? Object.entries(namingConvention.dataset_case_style_counts).map(([caseStyle, count]) => ({
          caseStyle,
          count: count as number,
          share: (namingConvention.dataset_case_style_share?.[caseStyle] as number) || 0,
        }))
      : [];
    const namingStyleEntropies =
      measuresPerModel?.lexical?.d2_m3_naming_convention
        ? Object.values(measuresPerModel.lexical.d2_m3_naming_convention).map((m: any) => m.naming_style_entropy)
        : [];
    const namingStyleEntropyHistogram = createHistogramData(namingStyleEntropies);

    // D2.M4 - Single vs Multi Word
    const singleMultiWord = measures?.lexical?.d2_m4_single_multi_word;
    const singleMultiWordChartData = singleMultiWord
      ? {
          single: singleMultiWord.total_single_word_labels,
          multi: singleMultiWord.total_multi_word_labels,
          singleShare: singleMultiWord.dataset_share_single_word_labels,
          multiShare: 1 - singleMultiWord.dataset_share_single_word_labels,
        }
      : null;
    const singleWordShares =
      measuresPerModel?.lexical?.d2_m4_single_multi_word
        ? Object.values(measuresPerModel.lexical.d2_m4_single_multi_word).map((m: any) => m.single_word_label_share)
        : [];
    const singleWordShareHistogram = createHistogramData(singleWordShares);

    // D2.M5 - Lexical Diversity
    const lexicalDiversity = measures?.lexical?.d2_m5_lexical_diversity;
    const lexicalDiversityTop10 = measuresPerModel?.lexical?.d2_m5_lexical_diversity
      ? Object.entries(measuresPerModel.lexical.d2_m5_lexical_diversity)
          .map(([modelId, data]: [string, any]) => ({
            modelId,
            relpath: irInfo?.index?.[modelId] || modelId,
            totalTokens: data.total_tokens,
            vocabSize: data.vocab_size,
            typeTokenRatio: data.type_token_ratio,
            stopwordShare: data.stopword_share,
          }))
          .sort((a, b) => b.typeTokenRatio - a.typeTokenRatio)
          .slice(0, 10)
      : [];

    return {
      parseStatus,
      parseStatusChartData,
      skipRatioHistogram,
      skipRatioTop10,
      parseTimeHistogram,
      parseTimeScatterData,
      sourceSizeHistogram,
      irSizeHistogram,
      fileSizeTop10,
      warningsChartData,
      modelsWithWarnings,
      // Lexical measures
      labelPresence,
      labelPresenceChartData,
      labelPresenceByType,
      labelLength,
      labelLengthCharsHistogram,
      labelLengthTokensHistogram,
      labelLengthTop10,
      namingConvention,
      namingConventionChartData,
      namingStyleEntropies,
      namingStyleEntropyHistogram,
      singleMultiWord,
      singleMultiWordChartData,
      singleWordShares,
      singleWordShareHistogram,
      lexicalDiversity,
      lexicalDiversityTop10,
    };
  }, [reportData]);
}
