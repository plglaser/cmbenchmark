"""Pydantic schemas for API requests and responses."""

from typing import Dict, List, Any, Optional, Literal
from pydantic import BaseModel, Field
from cmbenchmark.types.profile import BenchmarkProfile


# Request schemas
class ProfileRequest(BaseModel):
    """Request schema carrying a benchmark profile."""
    profile: BenchmarkProfile = Field(..., description="Benchmark profile JSON")


class ScanRequest(ProfileRequest):
    """Request schema for scan endpoint."""


class ParseRequest(ProfileRequest):
    """Request schema for parse endpoint."""


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


class ScanJobCreateResponse(BaseModel):
    """Response schema for creating scan jobs."""
    job_id: str
    status: str
    created_at: str
    status_url: str


class ScanJobStatusResponse(BaseModel):
    """Response schema for scan job status."""
    job_id: str
    job_type: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    progress: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    cancel_requested: bool = False


class ScanJobFilesResponse(BaseModel):
    """Response schema for paginated scan-file details."""
    job_id: str
    category: str
    offset: int
    limit: int
    total: int
    items: List[Any] = Field(default_factory=list)


class ScanJobCancelResponse(BaseModel):
    """Response schema for scan job cancellation requests."""
    job_id: str
    status: str
    cancel_requested: bool


class StageJobCreateResponse(BaseModel):
    """Generic response schema for creating async stage jobs."""
    job_id: str
    status: str
    created_at: str
    status_url: str


class StageJobStatusResponse(BaseModel):
    """Generic response schema for stage job status."""
    job_id: str
    job_type: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    progress: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    cancel_requested: bool = False


class StageJobCancelResponse(BaseModel):
    """Generic response schema for stage job cancellation requests."""
    job_id: str
    status: str
    cancel_requested: bool


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


class MeasureRequest(ProfileRequest):
    """Request schema for measure endpoint."""


class MeasureResponse(BaseModel):
    """Response schema for measure endpoint."""
    measures_path: str = Field(..., description="Path to measures.json file")
    measures_dir: str = Field(..., description="Path to directory with per-model measure JSON files")
    measures_index_path: str = Field(..., description="Path to measures_index.json file")
    output_dir: str = Field(..., description="Output directory where measures were saved")


class ReportRequest(ProfileRequest):
    """Request schema for report endpoint."""


class CustomViewFilter(BaseModel):
    """Filter clause for custom view data selection."""
    field: str
    op: Literal[
        "eq",
        "ne",
        "gt",
        "gte",
        "lt",
        "lte",
        "contains",
        "in",
        "not_in",
        "is_null",
        "is_not_null",
    ] = "eq"
    value: Optional[Any] = None


class CustomViewDefinition(BaseModel):
    """Declarative custom view definition."""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    chart_type: Literal["kpi", "bar", "pie", "histogram", "scatter"]
    source: Literal["dataset", "per_model"] = "per_model"
    config: Dict[str, Any] = Field(default_factory=dict)
    filters: List[CustomViewFilter] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CustomViewField(BaseModel):
    """Discoverable field metadata for custom view builder UI."""
    path: str
    label: str
    source: Literal["dataset", "per_model"]
    type: str
    sample: Optional[Any] = None
    non_null_count: int = 0
    count: int = 0
    distinct_count: int = 0
    is_unique: bool = False


class CustomViewFieldsResponse(BaseModel):
    """Field catalog for custom view configuration."""
    dataset_fields: List[CustomViewField] = Field(default_factory=list)
    per_model_fields: List[CustomViewField] = Field(default_factory=list)
    chart_types: List[str] = Field(default_factory=list)


class CustomViewListResponse(BaseModel):
    """Saved custom views for an output directory."""
    output_dir: str
    views: List[CustomViewDefinition] = Field(default_factory=list)


class CustomViewMutationRequest(BaseModel):
    """Create/update request for custom views."""
    output_dir: str
    view: CustomViewDefinition


class CustomViewPreviewRequest(BaseModel):
    """Preview request for custom view definitions."""
    output_dir: str
    view: CustomViewDefinition


class CustomViewPreviewResponse(BaseModel):
    """Preview response for custom views."""
    chart_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class CustomViewDeleteResponse(BaseModel):
    """Delete response for custom views."""
    output_dir: str
    view_id: str
    deleted: bool


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


class DerivedParseElementsSkipsSummary(BaseModel):
    totalModelsEvaluated: int
    modelsWithSkips: int
    modelsWithoutSkips: int
    modelsWithSkipsShare: float
    totalElementsLoaded: int
    totalElementsSkipped: int
    totalElementsProcessed: int
    datasetSkipRatio: float
    datasetLoadRatio: float
    avgSkipRatio: float
    medianSkipRatio: float


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
    missingCount: int


class DerivedLabelMissingTopItem(BaseModel):
    modelId: str
    relpath: str
    eligibleCount: int
    presentCount: int
    missingCount: int


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


class DerivedLanguageUsageItem(BaseModel):
    language: str
    count: int
    share: float


class DerivedLanguageUsagePieItem(BaseModel):
    name: str
    value: int
    share: float


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


class DerivedModelSizeScatterItem(BaseModel):
    modelId: str
    relpath: str
    nodeCount: int
    edgeCount: int


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
    languageUsage: Optional[Dict[str, Any]] = None
    constructPresence: Optional[Dict[str, Any]] = None
    constructFrequency: Optional[Dict[str, Any]] = None
    constructDimensionScore: Optional[float] = None
    modelSize: Optional[Dict[str, Any]] = None
    degree: Optional[Dict[str, Any]] = None
    connectivity: Optional[Dict[str, Any]] = None
    containmentDepth: Optional[Dict[str, Any]] = None

    # Derived chart/table payloads
    parseStatusChartData: List[DerivedParseStatusChartItem] = Field(default_factory=list)
    parseElementsSkipsSummary: Optional[DerivedParseElementsSkipsSummary] = None
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
    labelMissingTop10: List[DerivedLabelMissingTopItem] = Field(default_factory=list)

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
    languageUsageData: List[DerivedLanguageUsageItem] = Field(default_factory=list)
    languageUsagePieData: List[DerivedLanguageUsagePieItem] = Field(default_factory=list)

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
    modelSizeScatterData: List[DerivedModelSizeScatterItem] = Field(default_factory=list)
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
