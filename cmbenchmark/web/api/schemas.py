"""Pydantic schemas for API requests and responses."""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from cmbenchmark.services.scan import DEFAULT_INCLUDE_PATTERNS


# Request schemas
class ScanRequest(BaseModel):
    """Request schema for scan endpoint."""
    dataset_path: str = Field(..., description="Path to dataset directory")
    out: str = Field(..., description="Path to output directory for dataset_info.json")
    include: Optional[List[str]] = Field(None, description=f"List of file patterns to include. If not provided, uses default patterns: {', '.join(DEFAULT_INCLUDE_PATTERNS)}. Patterns match filenames (e.g., '*.xml') or relative paths from dataset root (e.g., 'subdir/*').")
    exclude: Optional[List[str]] = Field(None, description="List of file patterns to exclude. Applied after include filtering. Patterns match filenames (e.g., '*.tmp') or relative paths from dataset root (e.g., 'test/*', 'backup/**').")
    size_limit_mb: Optional[int] = Field(None, description="Maximum file size in MB")


class ParseRequest(BaseModel):
    """Request schema for parse endpoint."""
    dataset_info_path: str = Field(..., description="Path to dataset_info.json from scan stage")
    output_dir: str = Field(..., description="Path to output directory")
    parser_language: str = Field(..., description="Parser language to use (e.g., UML, BPMN, ArchiMate)")


# Response schemas
class ScanResponse(BaseModel):
    """Response schema for scan endpoint."""
    dataset_root: str
    scanned_at: str
    parameters: Dict[str, Any]
    totals: Dict[str, int]
    extensions: Dict[str, int]
    duplicates_groups: List[Dict[str, Any]]
    too_large: List[str]
    unreadable: List[str]
    candidates: List[str]
    filtered: List[str]


class ModelParseDiagnosticsResponse(BaseModel):
    """Response schema for model parse diagnostics."""
    file_id: str
    relpath: str
    parse_status: str  # "success", "warning", or "failure"
    parse_error_msg: Optional[str] = None
    elements_loaded: int = 0
    elements_skipped: int = 0
    parse_time_ms: int = 0
    file_size_bytes_source: int = 0
    file_size_bytes_ir: int = 0
    warning_count: int = 0
    warnings_by_type: Dict[str, int] = {}
    warning_msgs: Dict[str, List[str]] = {}
    skip_ratio: float = 0.0
    warnings_per_element: float = 0.0


class ParseResponse(BaseModel):
    """Response schema for parse endpoint."""
    dataset_root: str
    parsed_at: str
    parameters: Dict[str, Any]
    totals: Dict[str, int]
    index: Dict[str, str]
    modelParseDiagnostics: Dict[str, ModelParseDiagnosticsResponse] = {}


class MeasureRequest(BaseModel):
    """Request schema for measure endpoint."""
    ir_dir: str = Field(..., description="Path to IR directory containing IR JSON files")
    output_dir: str = Field(..., description="Path to output directory for measures JSON files")
    profile_path: Optional[str] = Field(None, description="Optional path to benchmark profile JSON file for measure configuration")


class MeasureResponse(BaseModel):
    """Response schema for measure endpoint."""
    measures_path: str = Field(..., description="Path to measures.json file")
    measures_per_model_path: str = Field(..., description="Path to measures_per_model.json file")
    output_dir: str = Field(..., description="Output directory where measures were saved")


class ReportRequest(BaseModel):
    """Request schema for report endpoint."""
    measures_path: str = Field(..., description="Path to measures.json file")
    measures_per_model_path: str = Field(..., description="Path to measures_per_model.json file")
    ir_info_path: Optional[str] = Field(None, description="Path to ir_info.json file (optional, for linking to models)")


class DerivedHistogramBin(BaseModel):
    bin: str
    count: int


class DerivedParseStatusChartItem(BaseModel):
    name: str
    value: int
    share: float


class DerivedSkipRatioTopItem(BaseModel):
    modelId: str
    skipRatio: float
    elementsLoaded: int
    elementsSkipped: int
    relpath: str


class DerivedParseTimeScatterItem(BaseModel):
    fileSize: int
    parseTime: int


class DerivedFileSizeTopItem(BaseModel):
    modelId: str
    sourceSize: int
    irSize: int
    relpath: str


class DerivedWarningsChartItem(BaseModel):
    type: str
    count: int


class DerivedWarningsTopItem(BaseModel):
    modelId: str
    warningCount: int
    warningsByType: Dict[str, int] = Field(default_factory=dict)
    relpath: str


class DerivedLabelPresenceChartData(BaseModel):
    present: int
    missing: int
    presentShare: float
    missingShare: float


class DerivedLabelPresenceByTypeItem(BaseModel):
    type: str
    missingShare: float


class DerivedLabelLengthTopItem(BaseModel):
    modelId: str
    relpath: str
    charsMedian: float
    tokensMedian: float
    shortShare: float
    longShare: float


class DerivedNamingConventionChartItem(BaseModel):
    caseStyle: str
    count: int
    share: float


class DerivedSingleMultiWordChartData(BaseModel):
    single: int
    multi: int
    singleShare: float
    multiShare: float


class DerivedLexicalDiversityTopItem(BaseModel):
    modelId: str
    relpath: str
    totalTokens: int
    vocabSize: int
    typeTokenRatio: float
    stopwordShare: float


class DerivedConstructPresenceChartData(BaseModel):
    observed: int
    missing: int
    observedShare: float
    missingShare: float


class DerivedCoverageOutlierItem(BaseModel):
    modelId: str
    relpath: str
    coverageShare: float
    constructsObservedCount: int
    constructsAvailableCount: int
    unknownTypeShare: float
    unknownNodeTypeCount: int
    unknownEdgeTypeCount: int


class DerivedMissingConstructItem(BaseModel):
    constructId: str
    group: Optional[str] = None
    description: Optional[str] = None
    kind: Optional[str] = None


class DerivedUnknownTypeItem(BaseModel):
    type: str
    count: int


class DerivedCoverageByGroupItem(BaseModel):
    group: str
    available: int
    observed: int
    missing: int
    coverageShare: float


class DerivedCoverageByKindItem(BaseModel):
    kind: str
    available: int
    observed: int
    missing: int
    coverageShare: float


class DerivedConstructFrequencyItem(BaseModel):
    constructId: str
    count: int
    share: float
    group: Optional[str] = None
    description: Optional[str] = None
    kind: Optional[str] = None


class DerivedConstructFrequencyParetoItem(BaseModel):
    rank: int
    constructId: str
    count: int
    share: float
    cumulativeShare: float


class DerivedConstructFrequencyByGroupItem(BaseModel):
    group: str
    count: int
    share: float


class DerivedConstructFrequencyPerModelItem(BaseModel):
    modelId: str
    relpath: str
    countsByConstruct: Dict[str, int] = Field(default_factory=dict)


class DerivedConstructFrequencyPerModelShareItem(BaseModel):
    modelId: str
    relpath: str
    sharesByConstruct: Dict[str, float] = Field(default_factory=dict)
    totalConstructInstances: int
    utilizationEntropy: float


class DerivedConstructFrequencyTopModelItem(BaseModel):
    modelId: str
    relpath: str
    totalConstructInstances: int
    utilizationEntropy: float


class DerivedConstructPresencePerModelItem(BaseModel):
    modelId: str
    relpath: str
    presentConstructs: Dict[str, bool] = Field(default_factory=dict)


class DerivedModelSizeTopItem(BaseModel):
    modelId: str
    relpath: str
    nodeCount: int
    edgeCount: int
    elementCount: int
    edgeNodeRatio: float


class DerivedDegreeTopItem(BaseModel):
    modelId: str
    relpath: str
    avgDegree: float
    avgInDegree: float
    avgOutDegree: float
    degreeMedian: float


class DerivedConnectivityTopItem(BaseModel):
    modelId: str
    relpath: str
    isolatedNodeShare: float
    isolatedNodeCount: int
    nComponents: int
    largestComponentSize: int


class DerivedDepthTopItem(BaseModel):
    modelId: str
    relpath: str
    maxDepth: int
    meanDepth: float
    rootCount: int
    containedNodeShare: float


class DerivedReportResponse(BaseModel):
    """Response schema for derived report endpoint (UI-ready)."""

    # Raw-ish measure objects that KPI components render directly
    parseStatus: Optional[Dict[str, Any]] = None
    parseElementsSkips: Optional[Dict[str, Any]] = None
    parseWarnings: Optional[Dict[str, Any]] = None
    parsingDimensionScore: Optional[float] = None
    labelPresence: Optional[Dict[str, Any]] = None
    labelLength: Optional[Dict[str, Any]] = None
    namingConvention: Optional[Dict[str, Any]] = None
    singleMultiWord: Optional[Dict[str, Any]] = None
    lexicalDiversity: Optional[Dict[str, Any]] = None
    constructPresence: Optional[Dict[str, Any]] = None
    constructFrequency: Optional[Dict[str, Any]] = None
    constructDimensionScore: Optional[float] = None
    modelSize: Optional[Dict[str, Any]] = None
    degree: Optional[Dict[str, Any]] = None
    connectivity: Optional[Dict[str, Any]] = None
    containmentDepth: Optional[Dict[str, Any]] = None

    # Derived chart/table payloads
    parseStatusChartData: List[DerivedParseStatusChartItem] = Field(default_factory=list)
    skipRatioHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    skipRatioTop10: List[DerivedSkipRatioTopItem] = Field(default_factory=list)
    parseTimeHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    parseTimeScatterData: List[DerivedParseTimeScatterItem] = Field(default_factory=list)
    sourceSizeHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    irSizeHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    fileSizeTop10: List[DerivedFileSizeTopItem] = Field(default_factory=list)
    fileSizeBottom10: List[DerivedFileSizeTopItem] = Field(default_factory=list)
    warningsChartData: List[DerivedWarningsChartItem] = Field(default_factory=list)
    modelsWithWarnings: List[DerivedWarningsTopItem] = Field(default_factory=list)

    labelPresenceChartData: Optional[DerivedLabelPresenceChartData] = None
    labelPresenceByType: List[DerivedLabelPresenceByTypeItem] = Field(default_factory=list)

    labelLengthCharsHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    labelLengthTokensHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    labelLengthTop10: List[DerivedLabelLengthTopItem] = Field(default_factory=list)

    namingConventionChartData: List[DerivedNamingConventionChartItem] = Field(default_factory=list)
    namingStyleEntropies: List[float] = Field(default_factory=list)
    namingStyleEntropyHistogram: List[DerivedHistogramBin] = Field(default_factory=list)

    singleMultiWordChartData: Optional[DerivedSingleMultiWordChartData] = None
    singleWordShares: List[float] = Field(default_factory=list)
    singleWordShareHistogram: List[DerivedHistogramBin] = Field(default_factory=list)

    lexicalDiversityTop10: List[DerivedLexicalDiversityTopItem] = Field(default_factory=list)

    constructCatalog: Dict[str, Any] = Field(default_factory=dict)
    constructPresenceChartData: Optional[DerivedConstructPresenceChartData] = None
    constructPresencePerModel: List[DerivedConstructPresencePerModelItem] = Field(default_factory=list)
    coverageShareHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    unknownTypeShareHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    lowestCoverage: List[DerivedCoverageOutlierItem] = Field(default_factory=list)
    highestCoverage: List[DerivedCoverageOutlierItem] = Field(default_factory=list)
    missingConstructs: List[DerivedMissingConstructItem] = Field(default_factory=list)
    unknownTypes: List[DerivedUnknownTypeItem] = Field(default_factory=list)
    coverageByGroup: List[DerivedCoverageByGroupItem] = Field(default_factory=list)
    coverageByKind: List[DerivedCoverageByKindItem] = Field(default_factory=list)
    constructFrequencyData: List[DerivedConstructFrequencyItem] = Field(default_factory=list)
    constructFrequencyPareto: List[DerivedConstructFrequencyParetoItem] = Field(default_factory=list)
    constructFrequencyByGroup: List[DerivedConstructFrequencyByGroupItem] = Field(default_factory=list)
    constructFrequencyPerModel: List[DerivedConstructFrequencyPerModelItem] = Field(default_factory=list)
    constructFrequencyTotalsHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    constructFrequencyEntropyHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    constructFrequencyTopModels: List[DerivedConstructFrequencyTopModelItem] = Field(default_factory=list)
    constructFrequencyPerModelShares: List[DerivedConstructFrequencyPerModelShareItem] = Field(default_factory=list)

    modelSizeNodeHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    modelSizeEdgeHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    modelSizeElementHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    modelSizeEdgeNodeRatioHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    modelSizeTop10: List[DerivedModelSizeTopItem] = Field(default_factory=list)

    avgDegreeHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    avgInDegreeHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    avgOutDegreeHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    degreeMedianHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    degreeTop10: List[DerivedDegreeTopItem] = Field(default_factory=list)

    nComponentsHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    largestComponentSizeHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    isolatedNodeCountHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    isolatedNodeShareHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    connectivityTop10: List[DerivedConnectivityTopItem] = Field(default_factory=list)

    maxDepthHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    meanDepthHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    containedNodeShareHistogram: List[DerivedHistogramBin] = Field(default_factory=list)
    depthTop10: List[DerivedDepthTopItem] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: Optional[str] = None

