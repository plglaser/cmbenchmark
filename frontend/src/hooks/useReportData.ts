import { useMemo } from 'react';
import type { ReportResponse } from '../types/api';

export function useReportData(reportData: ReportResponse | null) {
  return useMemo(() => {
    if (!reportData) return null;


    // TODO: Move this to server-side later
    
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

    // Histogram helper specialized for shares in [0, 1] with percent bins (prevents "0-0%" labels).
    const createShareHistogramData = (values: number[], bins: number = 20) => {
      if (values.length === 0) return [];
      const clamped = values
        .map((v) => (Number.isFinite(v) ? Math.max(0, Math.min(1, v)) : 0))
        .filter((v) => Number.isFinite(v));
      if (clamped.length === 0) return [];

      const min = Math.min(...clamped);
      const max = Math.max(...clamped);
      if (min === max) {
        const p = (min * 100).toFixed(1);
        return [{ bin: `${p}-${p}%`, count: clamped.length }];
      }

      const binWidth = (max - min) / bins;
      const binsData: number[] = new Array(bins).fill(0);
      clamped.forEach((v) => {
        const binIndex = Math.min(Math.floor((v - min) / binWidth), bins - 1);
        binsData[binIndex]++;
      });

      return binsData.map((count, i) => {
        const a = min + i * binWidth;
        const b = min + (i + 1) * binWidth;
        // Use 0 decimals for wide ranges, 1 decimal for narrow ones.
        const decimals = (max - min) < 0.2 ? 1 : 0;
        const fa = (a * 100).toFixed(decimals);
        const fb = (b * 100).toFixed(decimals);
        return { bin: `${fa}-${fb}%`, count };
      });
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

    // D3.M1 - Construct Presence
    const constructPresence = measures?.constructs?.d3_m1_construct_presence;
    const constructCatalog: Record<string, any> = constructPresence?.construct_catalog || {};
    const constructPresencePerModel = measuresPerModel?.constructs?.d3_m1_construct_presence;
    
    // Debug: log if constructs data is missing
    if (!measures?.constructs) {
      console.debug('Construct coverage data not found in measures. Make sure construct coverage is enabled in the profile and measures were recomputed.');
    }
    const constructPresenceChartData = constructPresence
      ? {
          observed: constructPresence.constructs_observed_count,
          missing: constructPresence.constructs_available_count - constructPresence.constructs_observed_count,
          observedShare: constructPresence.coverage_share,
          missingShare: 1 - constructPresence.coverage_share,
        }
      : null;
    
    const coverageShares = measuresPerModel?.constructs?.d3_m1_construct_presence
      ? Object.values(measuresPerModel.constructs.d3_m1_construct_presence).map((m: any) => m.coverage_share)
      : [];
    const coverageShareHistogram = createShareHistogramData(coverageShares);

    const unknownTypeShares = constructPresencePerModel
      ? Object.values(constructPresencePerModel).map((m: any) => m.unknown_type_share ?? 0)
      : [];
    const unknownTypeShareHistogram = createShareHistogramData(unknownTypeShares);
    
    // Top 10 models with lowest/highest coverage
    const coverageOutliers = constructPresencePerModel
      ? Object.entries(constructPresencePerModel)
          .map(([modelId, data]: [string, any]) => ({
            modelId,
            relpath: irInfo?.index?.[modelId] || modelId,
            coverageShare: data.coverage_share,
            constructsObservedCount: data.constructs_observed_count,
            constructsAvailableCount: data.constructs_available_count,
            unknownTypeShare: data.unknown_type_share,
            unknownNodeTypeCount: data.unknown_node_type_count,
            unknownEdgeTypeCount: data.unknown_edge_type_count,
          }))
      : [];
    const lowestCoverage = [...coverageOutliers].sort((a, b) => a.coverageShare - b.coverageShare).slice(0, 10);
    const highestCoverage = [...coverageOutliers].sort((a, b) => b.coverageShare - a.coverageShare).slice(0, 10);
    
    // Missing constructs (constructs never observed)
    const missingConstructs =
      constructPresence?.missing_constructs && Array.isArray(constructPresence.missing_constructs)
        ? constructPresence.missing_constructs.map((m: any) => ({
            constructId: m.constructId,
            group: m.group,
            description: m.description,
            kind: m.kind,
          }))
        : constructPresence && constructPresencePerModel
          ? (() => {
              const allPresent = new Set<string>();
              const allConstructs = new Set<string>();
              
              // Collect all constructs that were present in at least one model
              Object.values(constructPresencePerModel).forEach((m: any) => {
                Object.entries(m.present_constructs || {}).forEach(([cid, present]: [string, any]) => {
                  allConstructs.add(cid);
                  if (present) allPresent.add(cid);
                });
              });
              
              // Find constructs that were never present
              const missing = Array.from(allConstructs).filter((cid) => !allPresent.has(cid));
              
              return missing.map((cid) => ({ constructId: cid }));
            })()
          : [];
    
    // Unknown types (aggregate from all models)
    const unknownTypes =
      constructPresence?.unknown_type_examples_dataset
        ? Object.entries(constructPresence.unknown_type_examples_dataset)
            .map(([type, count]: [string, any]) => ({ type, count: Number(count) || 0 }))
            .sort((a, b) => b.count - a.count)
            .slice(0, 25)
        : constructPresencePerModel
          ? (() => {
              const typeCounts: Record<string, number> = {};
              Object.values(constructPresencePerModel).forEach((m: any) => {
                Object.entries(m.unknown_type_examples || {}).forEach(([type, count]: [string, any]) => {
                  typeCounts[type] = (typeCounts[type] || 0) + (Number(count) || 0);
                });
              });
              return Object.entries(typeCounts)
                .map(([type, count]) => ({ type, count }))
                .sort((a, b) => b.count - a.count)
                .slice(0, 10);
            })()
          : [];

    const coverageByGroup = constructPresence?.coverage_by_group
      ? Object.entries(constructPresence.coverage_by_group)
          .map(([group, stats]: [string, any]) => ({
            group,
            available: Number(stats.available) || 0,
            observed: Number(stats.observed) || 0,
            missing: Number(stats.missing) || 0,
            coverageShare: Number(stats.coverage_share) || 0,
          }))
          .sort((a, b) => a.coverageShare - b.coverageShare)
      : [];

    const coverageByKind = constructPresence?.coverage_by_kind
      ? Object.entries(constructPresence.coverage_by_kind)
          .map(([kind, stats]: [string, any]) => ({
            kind,
            available: Number(stats.available) || 0,
            observed: Number(stats.observed) || 0,
            missing: Number(stats.missing) || 0,
            coverageShare: Number(stats.coverage_share) || 0,
          }))
          .sort((a, b) => a.coverageShare - b.coverageShare)
      : [];

    // D3.M3 - Construct Frequency
    const constructFrequency = measures?.constructs?.d3_m3_construct_frequency;
    const constructFrequencyData = constructFrequency?.dataset_count_by_construct
      ? Object.entries(constructFrequency.dataset_count_by_construct)
          .map(([constructId, count]: [string, any]) => ({
            constructId,
            count: Number(count) || 0,
            share: 0,
            group: constructCatalog?.[constructId]?.group,
            description: constructCatalog?.[constructId]?.description,
            kind: constructCatalog?.[constructId]?.kind,
          }))
          .sort((a, b) => b.count - a.count)
      : [];

    const totalConstructCount = constructFrequencyData.reduce((acc, d) => acc + (d.count || 0), 0);
    constructFrequencyData.forEach((d) => {
      d.share = totalConstructCount > 0 ? (d.count || 0) / totalConstructCount : 0;
    });

    const constructFrequencyPareto = (() => {
      let cumulative = 0;
      return constructFrequencyData.map((d, idx) => {
        cumulative += d.share || 0;
        return {
          rank: idx + 1,
          constructId: d.constructId,
          count: d.count,
          share: d.share,
          cumulativeShare: cumulative,
        };
      });
    })();

    const constructFrequencyByGroup = (() => {
      const byGroup: Record<string, number> = {};
      constructFrequencyData.forEach((d) => {
        const group = d.group || '—';
        byGroup[group] = (byGroup[group] || 0) + (d.count || 0);
      });
      const total = Object.values(byGroup).reduce((acc, v) => acc + v, 0);
      return Object.entries(byGroup)
        .map(([group, count]) => ({ group, count, share: total > 0 ? count / total : 0 }))
        .sort((a, b) => b.count - a.count);
    })();

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
      // Construct measures
      constructPresence,
      constructCatalog,
      constructPresenceChartData,
      coverageShareHistogram,
      unknownTypeShareHistogram,
      lowestCoverage,
      highestCoverage,
      missingConstructs,
      unknownTypes,
      coverageByGroup,
      coverageByKind,
      constructFrequency,
      constructFrequencyData,
      constructFrequencyPareto,
      constructFrequencyByGroup,
    };
  }, [reportData]);
}
