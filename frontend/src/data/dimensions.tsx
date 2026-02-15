import { Dimension } from '../types/report';
import { ParseStatusChart } from '../components/parsing/ParseStatusChart';
import { ParseStatusKPIs } from '../components/parsing/ParseStatusKPIs';
import { SkipRatioChart } from '../components/parsing/SkipRatioChart';
import { SkipRatioTable } from '../components/parsing/SkipRatioTable';
import { ElementsSkipsKPIs } from '../components/parsing/ElementsSkipsKPIs';
import { ParseTimeChart } from '../components/parsing/ParseTimeChart';
import { ParseTimeScatter } from '../components/parsing/ParseTimeScatter';
import { FileSizeCharts } from '../components/parsing/FileSizeCharts';
import { FileSizeTable } from '../components/parsing/FileSizeTable';
import { WarningsChart } from '../components/parsing/WarningsChart';
import { WarningsTable } from '../components/parsing/WarningsTable';
import { HistogramCard } from '../components/size/HistogramCard';
import { ModelSizeKPIs } from '../components/size/ModelSizeKPIs';
import { ModelSizeScatter } from '../components/size/ModelSizeScatter';
import { ModelSizeTopTable } from '../components/size/ModelSizeTopTable';
import { DegreeKPIs } from '../components/size/DegreeKPIs';
import { DegreeTopTable } from '../components/size/DegreeTopTable';
import { ConnectivityKPIs } from '../components/size/ConnectivityKPIs';
import { ConnectivityTopTable } from '../components/size/ConnectivityTopTable';
import { DepthKPIs } from '../components/size/DepthKPIs';
import { DepthTopTable } from '../components/size/DepthTopTable';
import { LabelPresenceChart } from '../components/lexical/LabelPresenceChart';
import { LabelPresenceKPIs } from '../components/lexical/LabelPresenceKPIs';
import { LabelPresenceByTypeChart } from '../components/lexical/LabelPresenceByTypeChart';
import { LabelPresenceMissingTable } from '../components/lexical/LabelPresenceMissingTable';
import { LabelLengthChart } from '../components/lexical/LabelLengthChart';
import { LabelLengthStats } from '../components/lexical/LabelLengthStats';
import { LabelLengthTable } from '../components/lexical/LabelLengthTable';
import { NamingConventionChart } from '../components/lexical/NamingConventionChart';
import { NamingConventionStats } from '../components/lexical/NamingConventionStats';
import { SingleMultiWordChart } from '../components/lexical/SingleMultiWordChart';
import { SingleMultiWordStats } from '../components/lexical/SingleMultiWordStats';
import { LexicalDiversityKPIs } from '../components/lexical/LexicalDiversityKPIs';
import { LexicalDiversityTable } from '../components/lexical/LexicalDiversityTable';
import { LexicalDiversityTopLabelsTable } from '../components/lexical/LexicalDiversityTopLabelsTable';
import { LanguageUsageChart } from '../components/lexical/LanguageUsageChart';
import { LanguageUsageBarChart } from '../components/lexical/LanguageUsageBarChart';
import { LanguageUsageKPIs } from '../components/lexical/LanguageUsageKPIs';
import { ConstructPresenceKPIs } from '../components/constructs/ConstructPresenceKPIs';
import { ConstructPresenceChart } from '../components/constructs/ConstructPresenceChart';
import { ConstructCoverageMatrix } from '../components/constructs/ConstructCoverageMatrix';
import { CoverageShareChart } from '../components/constructs/CoverageShareChart';
import { CoverageByGroupChart } from '../components/constructs/CoverageByGroupChart';
import { MissingConstructsTable } from '../components/constructs/MissingConstructsTable';
import { CoverageOutliersTable } from '../components/constructs/CoverageOutliersTable';
import { UnknownTypesTable } from '../components/constructs/UnknownTypesTable';
import { UnknownTypeShareChart } from '../components/constructs/UnknownTypeShareChart';
import { ConstructFrequencyByGroupChart } from '../components/constructs/ConstructFrequencyByGroupChart';
import { ConstructFrequencyTreemapWithFilter } from '../components/constructs/ConstructFrequencyTreemapWithFilter';
import { ConstructFrequencyChartWithFilter } from '../components/constructs/ConstructFrequencyChartWithFilter';
import { ConstructFrequencyParetoWithFilter } from '../components/constructs/ConstructFrequencyParetoWithFilter';
import { ConstructFrequencyHeatmap } from '../components/constructs/ConstructFrequencyHeatmap';
import { ConstructFrequencyKPIs } from '../components/constructs/ConstructFrequencyKPIs';
import { ConstructFrequencyTotalsChart } from '../components/constructs/ConstructFrequencyTotalsChart';
import { ConstructFrequencyEntropyChart } from '../components/constructs/ConstructFrequencyEntropyChart';
import { ConstructFrequencyTopModelsTable } from '../components/constructs/ConstructFrequencyTopModelsTable';
import { ConstructFrequencyShareHeatmap } from '../components/constructs/ConstructFrequencyShareHeatmap';

export function createDimensions(reportData: any, parserLanguage?: string | null): Dimension[] {
  const parsingData = reportData;

  return [
    {
      id: 'parsing',
      name: 'Parsing',
      description: 'Correctness and robustness of parsing.',
      measures: [
        {
          id: 'parse-status',
          name: 'Parse Status (D1.M1)',
          description: 'How often parsing produces a valid model.',
          tiles: [
            {
              id: 'status-chart',
              title: 'Status Distribution',
              component: (
                <ParseStatusChart data={parsingData?.parseStatusChartData || []} />
              ),
            },
            {
              id: 'status-kpis',
              title: 'Key KPIs',
              component: <ParseStatusKPIs parseStatus={parsingData?.parseStatus || null} />,
            },
          ],
        },
        {
          id: 'elements-skips',
          name: 'Elements & Skips (D1.M2)',
          description: 'Elements loaded vs skipped during parsing.',
          tiles: [
            {
              id: 'skip-ratio-chart',
              title: 'Skip Ratio Distribution',
              component: (
                <SkipRatioChart histogramData={parsingData?.skipRatioHistogram || []} />
              ),
            },
            {
              id: 'skip-ratio-table',
              title: 'Top 10 Models with Highest Skip Ratio',
              component: <SkipRatioTable data={parsingData?.skipRatioTop10 || []} />,
            },
            {
              id: 'elements-skips-kpis',
              title: 'Summary KPIs',
              component: <ElementsSkipsKPIs data={parsingData?.parseElementsSkipsSummary || null} />,
            },
          ],
        },
        {
          id: 'parsing-time',
          name: 'Parsing Time (D1.M3)',
          description: 'Time taken to parse models.',
          tiles: [
            {
              id: 'parse-time-chart',
              title: 'Parse Time Distribution',
              component: (
                <ParseTimeChart histogramData={parsingData?.parseTimeHistogram || []} />
              ),
            },
            {
              id: 'parse-time-scatter',
              title: 'File Size vs Parse Time',
              component: (
                <ParseTimeScatter data={parsingData?.parseTimeScatterData || []} />
              ),
            },
          ],
        },
        {
          id: 'file-sizes',
          name: 'File Sizes (D1.M4)',
          description: 'Source and IR file sizes.',
          tiles: [
            {
              id: 'file-size-charts',
              title: 'File Size Distributions',
              component: (
                <FileSizeCharts
                  sourceHistogram={parsingData?.sourceSizeHistogram || []}
                  irHistogram={parsingData?.irSizeHistogram || []}
                />
              ),
            },
            {
              id: 'file-size-table',
              title: 'Top 10 Largest Models',
              component: <FileSizeTable data={parsingData?.fileSizeTop10 || []} />,
            },
            {
              id: 'file-size-table-smallest',
              title: 'Top 10 Smallest Models',
              component: (
                <FileSizeTable
                  data={parsingData?.fileSizeBottom10 || []}
                  title="Top 10 Smallest Models"
                />
              ),
            },
          ],
        },
        {
          id: 'warnings',
          name: 'Warnings (D1.M5)',
          description: 'Warnings generated during parsing.',
          tiles: [
            {
              id: 'warnings-chart',
              title: 'Warnings by Type',
              component: (
                <WarningsChart data={parsingData?.warningsChartData || []} />
              ),
            },
            {
              id: 'warnings-table',
              title: 'Models with Most Warnings',
              component: <WarningsTable data={parsingData?.modelsWithWarnings || []} />,
            },
          ],
        },
      ],
    },
    {
      id: 'lexical-quality',
      name: 'Lexical Quality',
      description: 'Quality of lexical elements in models.',
      measures: [
        {
          id: 'label-presence',
          name: 'Label Presence (D2.M1)',
          description: 'Completeness of labels in models.',
          tiles: [
            {
              id: 'presence-chart',
              title: 'Label Presence Distribution',
              component: (
                <LabelPresenceChart data={parsingData?.labelPresenceChartData || null} />
              ),
            },
            {
              id: 'presence-kpis',
              title: 'Key Metrics',
              component: <LabelPresenceKPIs data={parsingData?.labelPresence || null} />,
            },
            {
              id: 'presence-by-type',
              title: 'Missing Labels by Element Type',
              component: (
                <LabelPresenceByTypeChart data={parsingData?.labelPresenceByType || []} />
              ),
            },
            {
              id: 'presence-missing-top10',
              title: 'Top 10 Models with Most Missing Labels',
              component: (
                <LabelPresenceMissingTable data={parsingData?.labelMissingTop10 || []} />
              ),
            },
          ],
        },
        {
          id: 'label-length',
          name: 'Label Length (D2.M2)',
          description: 'Distribution of label lengths in characters and tokens.',
          tiles: [
            {
              id: 'length-chars-chart',
              title: 'Character Length Distribution',
              component: (
                <LabelLengthChart
                  histogramData={parsingData?.labelLengthCharsHistogram || []}
                  label="Character Length Distribution"
                />
              ),
            },
            {
              id: 'length-tokens-chart',
              title: 'Token Length Distribution',
              component: (
                <LabelLengthChart
                  histogramData={parsingData?.labelLengthTokensHistogram || []}
                  label="Token Length Distribution"
                />
              ),
            },
            {
              id: 'length-stats',
              title: 'Length Statistics',
              component: <LabelLengthStats data={parsingData?.labelLength || null} />,
            },
            {
              id: 'length-table',
              title: 'Top 10 Models by Label Length',
              component: <LabelLengthTable data={parsingData?.labelLengthTop10 || []} />,
            },
          ],
        },
        {
          id: 'naming-convention',
          name: 'Naming Convention (D2.M3)',
          description: 'Consistency of naming conventions (case styles) across models.',
          tiles: [
            {
              id: 'naming-chart',
              title: 'Case Style Distribution',
              component: (
                <NamingConventionChart data={parsingData?.namingConventionChartData || []} />
              ),
            },
            {
              id: 'naming-stats',
              title: 'Naming Style Entropy',
              component: (() => {
                const entropyStats = parsingData?.namingConvention?.naming_style_entropy_stats;
                const stats = entropyStats
                  ? {
                      min: entropyStats.min ?? 0,
                      p25: entropyStats.p25 ?? 0,
                      median: entropyStats.median ?? 0,
                      mean: entropyStats.mean ?? 0,
                      p75: entropyStats.p75 ?? 0,
                      max: entropyStats.max ?? 0,
                    }
                  : null;
                return (
                  <NamingConventionStats
                    entropyStats={stats}
                    histogramData={parsingData?.namingStyleEntropyHistogram || []}
                  />
                );
              })(),
            },
          ],
        },
        {
          id: 'single-multi-word',
          name: 'Single vs Multi-Word (D2.M4)',
          description: 'Distribution of single-word vs multi-word labels.',
          tiles: [
            {
              id: 'single-multi-chart',
              title: 'Single vs Multi-Word Labels',
              component: (
                <SingleMultiWordChart data={parsingData?.singleMultiWordChartData || null} />
              ),
            },
            {
              id: 'single-multi-stats',
              title: 'Statistics',
              component: (
                <SingleMultiWordStats
                  datasetData={parsingData?.singleMultiWord || null}
                  shareStats={parsingData?.singleMultiWord?.share_single_word_labels_stats || null}
                  histogramData={parsingData?.singleWordShareHistogram || []}
                />
              ),
            },
          ],
        },
        {
          id: 'lexical-diversity',
          name: 'Lexical Diversity (D2.M5)',
          description: 'Vocabulary richness and diversity of labels.',
          tiles: [
            {
              id: 'diversity-kpis',
              title: 'Diversity Metrics',
              component: <LexicalDiversityKPIs data={parsingData?.lexicalDiversity || null} />,
            },
            {
              id: 'diversity-table',
              title: 'Top 10 Models by Lexical Diversity',
              component: <LexicalDiversityTable data={parsingData?.lexicalDiversityTop10 || []} />,
            },
            {
              id: 'top-labels-table',
              title: 'Top Labels by Occurrence',
              component: (
                <LexicalDiversityTopLabelsTable
                  data={parsingData?.lexicalDiversity?.top_labels || []}
                />
              ),
            },
          ],
        },
        {
          id: 'language-usage',
          name: 'Language Usage (D2.M6)',
          description: 'Detected natural language usage across model labels.',
          tiles: [
            {
              id: 'language-usage-pie',
              title: 'Language Distribution',
              component: <LanguageUsageChart data={parsingData?.languageUsagePieData || []} />,
            },
            {
              id: 'language-usage-kpis',
              title: 'Key Metrics',
              component: <LanguageUsageKPIs data={parsingData?.languageUsageData || []} />,
            },
            {
              id: 'language-usage-bar',
              title: 'Top Languages',
              component: <LanguageUsageBarChart data={parsingData?.languageUsageData || []} />,
            },
          ],
        },
      ],
    },
    {
      id: 'size-complexity',
      name: 'Size & Complexity',
      description: 'Size and structural complexity of models.',
      measures: [
        {
          id: 'model-size',
          name: 'Model Size (D4.M1)',
          description: 'Node/edge counts and size distribution across models.',
          tiles: [
            {
              id: 'model-size-kpis',
              title: 'Key Metrics',
              component: <ModelSizeKPIs data={parsingData?.modelSize || null} />,
            },
            {
              id: 'model-size-nodes',
              title: 'Node Count Distribution',
              component: (
                <HistogramCard
                  title="Node Count Distribution"
                  histogramData={parsingData?.modelSizeNodeHistogram || []}
                  barColor="#10b981"
                />
              ),
            },
            {
              id: 'model-size-edges',
              title: 'Edge Count Distribution',
              component: (
                <HistogramCard
                  title="Edge Count Distribution"
                  histogramData={parsingData?.modelSizeEdgeHistogram || []}
                  barColor="#38bdf8"
                />
              ),
            },
            {
              id: 'model-size-scatter',
              title: 'Nodes vs Edges per Model',
              component: (
                <ModelSizeScatter data={parsingData?.modelSizeScatterData || []} />
              ),
            },
            {
              id: 'model-size-elements',
              title: 'Element Count Distribution',
              component: (
                <HistogramCard
                  title="Element Count Distribution"
                  histogramData={parsingData?.modelSizeElementHistogram || []}
                  barColor="#f97316"
                />
              ),
            },
            {
              id: 'model-size-ratio',
              title: 'Edge/Node Ratio Distribution',
              component: (
                <HistogramCard
                  title="Edge/Node Ratio Distribution"
                  histogramData={parsingData?.modelSizeEdgeNodeRatioHistogram || []}
                  barColor="#8b5cf6"
                />
              ),
            },
            {
              id: 'model-size-top',
              title: 'Top 10 Largest Models',
              component: <ModelSizeTopTable data={parsingData?.modelSizeTop10 || []} />,
            },
          ],
        },
        {
          id: 'degree',
          name: 'Degree (D4.M2)',
          description: 'Average degree and degree distributions per model.',
          tiles: [
            {
              id: 'degree-kpis',
              title: 'Key Metrics',
              component: <DegreeKPIs data={parsingData?.degree || null} />,
            },
            {
              id: 'degree-avg',
              title: 'Average Degree Distribution',
              component: (
                <HistogramCard
                  title="Average Degree Distribution"
                  histogramData={parsingData?.avgDegreeHistogram || []}
                  barColor="#0ea5e9"
                />
              ),
            },
            {
              id: 'degree-avg-in',
              title: 'Average In-Degree Distribution',
              component: (
                <HistogramCard
                  title="Average In-Degree Distribution"
                  histogramData={parsingData?.avgInDegreeHistogram || []}
                  barColor="#22c55e"
                />
              ),
            },
            {
              id: 'degree-avg-out',
              title: 'Average Out-Degree Distribution',
              component: (
                <HistogramCard
                  title="Average Out-Degree Distribution"
                  histogramData={parsingData?.avgOutDegreeHistogram || []}
                  barColor="#f59e0b"
                />
              ),
            },
            {
              id: 'degree-median',
              title: 'Median Degree Distribution',
              component: (
                <HistogramCard
                  title="Median Degree Distribution"
                  histogramData={parsingData?.degreeMedianHistogram || []}
                  barColor="#a855f7"
                />
              ),
            },
            {
              id: 'degree-top',
              title: 'Top 10 Models by Avg Degree',
              component: <DegreeTopTable data={parsingData?.degreeTop10 || []} />,
            },
          ],
        },
        {
          id: 'connectivity',
          name: 'Connectivity (D4.M3)',
          description: 'Components and isolated nodes across models.',
          tiles: [
            {
              id: 'connectivity-kpis',
              title: 'Key Metrics',
              component: <ConnectivityKPIs data={parsingData?.connectivity || null} />,
            },
            {
              id: 'components-hist',
              title: 'Component Count Distribution',
              component: (
                <HistogramCard
                  title="Component Count Distribution"
                  histogramData={parsingData?.nComponentsHistogram || []}
                  barColor="#3b82f6"
                />
              ),
            },
            {
              id: 'largest-component-hist',
              title: 'Largest Component Size Distribution',
              component: (
                <HistogramCard
                  title="Largest Component Size Distribution"
                  histogramData={parsingData?.largestComponentSizeHistogram || []}
                  barColor="#6366f1"
                />
              ),
            },
            {
              id: 'isolated-share-hist',
              title: 'Isolated Node Share Distribution',
              component: (
                <HistogramCard
                  title="Isolated Node Share Distribution"
                  histogramData={parsingData?.isolatedNodeShareHistogram || []}
                  barColor="#ec4899"
                />
              ),
            },
            {
              id: 'connectivity-top',
              title: 'Top 10 Models by Isolated Share',
              component: <ConnectivityTopTable data={parsingData?.connectivityTop10 || []} />,
            },
          ],
        },
        {
          id: 'containment-depth',
          name: 'Containment Depth (D4.M4)',
          description: 'Depth of containment hierarchies and nesting.',
          tiles: [
            {
              id: 'depth-kpis',
              title: 'Key Metrics',
              component: <DepthKPIs data={parsingData?.containmentDepth || null} />,
            },
            {
              id: 'max-depth-hist',
              title: 'Max Depth Distribution',
              component: (
                <HistogramCard
                  title="Max Depth Distribution"
                  histogramData={parsingData?.maxDepthHistogram || []}
                  barColor="#f97316"
                />
              ),
            },
            {
              id: 'mean-depth-hist',
              title: 'Mean Depth Distribution',
              component: (
                <HistogramCard
                  title="Mean Depth Distribution"
                  histogramData={parsingData?.meanDepthHistogram || []}
                  barColor="#14b8a6"
                />
              ),
            },
            {
              id: 'contained-share-hist',
              title: 'Contained Node Share Distribution',
              component: (
                <HistogramCard
                  title="Contained Node Share Distribution"
                  histogramData={parsingData?.containedNodeShareHistogram || []}
                  barColor="#84cc16"
                />
              ),
            },
            {
              id: 'depth-top',
              title: 'Top 10 Models by Max Depth',
              component: <DepthTopTable data={parsingData?.depthTop10 || []} />,
            },
          ],
        },
      ],
    },
    {
      id: 'construct-coverage',
      name: 'Construct Coverage',
      description: 'Coverage of language constructs in models.',
      measures: [
        {
          id: 'construct-presence',
          name: 'Construct Presence (D3.M1)',
          description: 'Which constructs appear at least once in the dataset.',
          tiles: [
            {
              id: 'presence-chart',
              title: 'Coverage Summary',
              component: (
                <ConstructPresenceChart data={parsingData?.constructPresenceChartData || null} />
              ),
            },
            {
              id: 'presence-kpis',
              title: 'Key Metrics',
              component: (
                <ConstructPresenceKPIs
                  data={parsingData?.constructPresence || null}
                  constructCatalog={parsingData?.constructCatalog || null}
                  parserLanguage={parserLanguage}
                />
              ),
            },
            {
              id: 'coverage-matrix',
              title: 'Coverage Matrix (Construct × Model)',
              component: (
                <ConstructCoverageMatrix
                  data={parsingData?.constructPresencePerModel || []}
                  constructCatalog={parsingData?.constructCatalog || null}
                />
              ),
            },
            {
              id: 'coverage-share-dist',
              title: 'Coverage Share Distribution',
              component: <CoverageShareChart histogramData={parsingData?.coverageShareHistogram || []} />,
            },
            {
              id: 'coverage-by-group',
              title: 'Coverage by Group',
              component: <CoverageByGroupChart data={parsingData?.coverageByGroup || []} />,
            },
            {
              id: 'missing-constructs',
              title: 'Missing Constructs',
              component: <MissingConstructsTable data={parsingData?.missingConstructs || []} />,
            },
            {
              id: 'lowest-coverage',
              title: 'Top 10 Models with Lowest Coverage',
              component: (
                <CoverageOutliersTable
                  data={parsingData?.lowestCoverage || []}
                  title="Top 10 Models with Lowest Coverage"
                />
              ),
            },
            {
              id: 'highest-coverage',
              title: 'Top 10 Models with Highest Coverage',
              component: (
                <CoverageOutliersTable
                  data={parsingData?.highestCoverage || []}
                  title="Top 10 Models with Highest Coverage"
                />
              ),
            },
            {
              id: 'unknown-share-dist',
              title: 'Unknown Type Share Distribution',
              component: <UnknownTypeShareChart histogramData={parsingData?.unknownTypeShareHistogram || []} />,
            },
            {
              id: 'unknown-types',
              title: 'Top Unknown Types',
              component: <UnknownTypesTable data={parsingData?.unknownTypes || []} />,
            },
          ],
        },
        {
          id: 'construct-frequency',
          name: 'Construct Frequency (D3.M3)',
          description: 'Counts per construct at model and dataset level.',
          tiles: [
            {
              id: 'frequency-kpis',
              title: 'Key Metrics',
              component: (
                <ConstructFrequencyKPIs
                  data={parsingData?.constructFrequency || null}
                  frequencyData={parsingData?.constructFrequencyData || []}
                />
              ),
            },
            {
              id: 'frequency-total-hist',
              title: 'Total Construct Instances (Models)',
              component: (
                <ConstructFrequencyTotalsChart
                  histogramData={parsingData?.constructFrequencyTotalsHistogram || []}
                />
              ),
            },
            {
              id: 'frequency-entropy-hist',
              title: 'Utilization Entropy (Models)',
              component: (
                <ConstructFrequencyEntropyChart
                  histogramData={parsingData?.constructFrequencyEntropyHistogram || []}
                />
              ),
            },
            {
              id: 'frequency-top-models',
              title: 'Top Models by Construct Instances',
              component: (
                <ConstructFrequencyTopModelsTable
                  data={parsingData?.constructFrequencyTopModels || []}
                />
              ),
            },
            {
              id: 'frequency-chart',
              title: 'Construct Frequency',
              component: (
                <ConstructFrequencyChartWithFilter data={parsingData?.constructFrequencyData || []} />
              ),
            },
            {
              id: 'frequency-treemap',
              title: 'Frequency Treemap',
              component: (
                <ConstructFrequencyTreemapWithFilter data={parsingData?.constructFrequencyData || []} />
              ),
            },
            {
              id: 'frequency-pareto',
              title: 'Construct Concentration',
              component: (
                <ConstructFrequencyParetoWithFilter data={parsingData?.constructFrequencyData || []} />
              ),
            },
            {
              id: 'frequency-by-group',
              title: 'Frequency by Group',
              component: (
                <ConstructFrequencyByGroupChart data={parsingData?.constructFrequencyByGroup || []} />
              ),
            },
            {
              id: 'frequency-heatmap',
              title: 'Construct × Model (Counts)',
              component: (
                <ConstructFrequencyHeatmap
                  data={parsingData?.constructFrequencyPerModel || []}
                  constructCatalog={parsingData?.constructCatalog || null}
                  constructTotals={parsingData?.constructFrequencyData || []}
                />
              ),
            },
            {
              id: 'frequency-share-heatmap',
              title: 'Construct × Model (Share)',
              component: (
                <ConstructFrequencyShareHeatmap
                  data={parsingData?.constructFrequencyPerModelShares || []}
                  constructCatalog={parsingData?.constructCatalog || null}
                  constructTotals={parsingData?.constructFrequencyData || []}
                />
              ),
            },
          ],
        },
      ],
    },
  ];
}
