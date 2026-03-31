"""Measure service for computing measures on IR models."""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable, Iterator
import json
from datetime import datetime, timezone
from cmbenchmark.types.measures import MeasureResultDataset, MeasureResultPerModel
from cmbenchmark.types.dataset import IRInfo
from cmbenchmark.types.ir import IR
from cmbenchmark.types.profile import BenchmarkProfile
from cmbenchmark.measures.parsing_measures import compute_parsing_measures
from cmbenchmark.measures.lexical_measures import compute_lexical_measures
from cmbenchmark.measures.construct_measures import compute_construct_measures
from cmbenchmark.measures.size_complexity_measures import compute_size_complexity_measures
from cmbenchmark.types.profile import ScanConfig, ParseConfig, MeasureConfig, ConstructCoverageConfig
from cmbenchmark.construct_catalog import load_construct_defs

MEASURES_DIRNAME = "measures"
MEASURES_INDEX_FILENAME = "measures_index.json"


class MeasureCancelledError(Exception):
    """Raised when measure execution is cancelled via callback."""


def _load_ir_info(ir_path: Path) -> Optional[IRInfo]:
    """
    Load IRInfo from ir_info.json, checking common locations.
    
    Args:
        ir_path: Path to IR directory
        
    Returns:
        IRInfo object if found, None otherwise
    """
    # Try ir_path / "ir_info.json" (if ir_path is the parent directory)
    ir_info_path = ir_path / "ir_info.json"
    if ir_info_path.exists():
        with open(ir_info_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return IRInfo.from_dict(data)
    
    # Try ir_path.parent / "ir_info.json" (if ir_path is the ir/ subdirectory)
    ir_info_path = ir_path.parent / "ir_info.json"
    if ir_info_path.exists():
        with open(ir_info_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return IRInfo.from_dict(data)
    
    return None


def _iter_ir_models(
    ir_files: List[Path],
    cancel_requested: Optional[Callable[[], bool]] = None,
) -> Iterator[IR]:
    """Yield IR models lazily from a file list, skipping unreadable/corrupt files."""
    for ir_file in ir_files:
        if cancel_requested and cancel_requested():
            raise MeasureCancelledError("Measure job was cancelled.")
        try:
            yield IR.load(str(ir_file))
        except Exception:
            continue


def compute_measure(
    ir_path: str,
    profile: Optional[BenchmarkProfile] = None,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    cancel_requested: Optional[Callable[[], bool]] = None,
) -> Tuple[MeasureResultDataset, MeasureResultPerModel]:
    """
    Compute measures for all IR models in the given directory.

    Args:
        ir_path: Path to directory containing IR JSON files
        profile: Optional BenchmarkProfile configuration. If None, uses default profile.

    Returns:
        Tuple of (MeasureResultDataset, MeasureResultPerModel) containing computed measures
    """
    def _emit_progress(update: Dict[str, Any]) -> None:
        if progress_callback:
            progress_callback(update)

    def _check_cancelled() -> None:
        if cancel_requested and cancel_requested():
            raise MeasureCancelledError("Measure job was cancelled.")

    ir_dir = Path(ir_path)
    
    if profile is None:
        # Create a minimal default profile
        parser_language = "ArchiMate-Archi"  # Default
        # Try to infer from IR models if available
        ir_files = sorted(ir_dir.glob("*.json"))
        if ir_files:
            try:
                sample_ir = IR.load(str(ir_files[0]))
                parser_language = sample_ir.language
            except Exception:
                pass
        
        measure_config = MeasureConfig()
        measure_config.constructs = ConstructCoverageConfig(
            enabled=True,
            enable_d3_m1=True,
            enable_d3_m2=True,
            enable_d3_m3=True,
        )
        
        profile = BenchmarkProfile(
            name="default",
            version="1.0",
            output_path="./out",
            scan=ScanConfig(dataset_path="./data"),
            parse=ParseConfig(parser_language=parser_language),
            measure=measure_config,
        )
    ir_files = sorted(ir_dir.glob("*.json"))

    if not ir_files:
        raise ValueError("No IR files found in directory")

    total_models = len(ir_files)
    enabled_model_phases: List[str] = ["indexing", "parsing"]
    if profile.measure.lexical.enabled:
        enabled_model_phases.append("lexical")
    if profile.measure.constructs and profile.measure.constructs.enabled:
        enabled_model_phases.append("constructs")
    if profile.measure.size_complexity.enabled:
        enabled_model_phases.append("size_complexity")
    phase_count = len(enabled_model_phases)
    completed_model_ops = 0

    def _emit_phase_progress(
        phase: str,
        message: str,
        processed_models_in_phase: int,
        valid_models_loaded: int,
    ) -> None:
        nonlocal completed_model_ops
        processed_phase = max(0, min(total_models, processed_models_in_phase))
        processed_ops = completed_model_ops + processed_phase
        total_ops = max(1, total_models * phase_count)
        percentage = (processed_ops / total_ops) * 100.0
        _emit_progress(
            {
                "phase": phase,
                "message": message,
                "percentage": percentage,
                "counters": {
                    "total_models": total_models,
                    "processed_models": processed_phase,
                    "valid_models_loaded": valid_models_loaded,
                },
            }
        )

    _emit_phase_progress(
        phase="indexing",
        message=f"Indexing IR model files ({total_models}/{total_models}).",
        processed_models_in_phase=total_models,
        valid_models_loaded=0,
    )
    completed_model_ops += total_models

    # Load IRInfo for parsing measures
    _check_cancelled()
    ir_info = _load_ir_info(ir_dir)
    if ir_info is None:
        raise ValueError(
            "ir_info.json not found. Please ensure parsing has been completed first. "
            "Expected locations: {ir_path}/ir_info.json or {ir_path}/../ir_info.json"
        )

    # Compute parsing measures (returns both dataset and per-model)
    parsing_dataset, parsing_per_model = compute_parsing_measures(ir_info)
    valid_models_hint = (
        int(parsing_dataset.d1_m1_parse_status.n_success)
        + int(parsing_dataset.d1_m1_parse_status.n_partial)
    )
    _emit_phase_progress(
        phase="parsing",
        message=f"Computing parsing measures ({total_models}/{total_models}).",
        processed_models_in_phase=total_models,
        valid_models_loaded=valid_models_hint,
    )
    completed_model_ops += total_models

    # Compute lexical measures if enabled
    lexical_dataset = None
    lexical_per_model = None
    measured_model_count: Optional[int] = None
    if profile.measure.lexical.enabled:
        try:
            lexical_dataset, lexical_per_model = compute_lexical_measures(
                _iter_ir_models(ir_files, cancel_requested=cancel_requested),
                lexical_profile=profile.measure.lexical,
                progress_callback=lambda processed, total: _emit_phase_progress(
                    phase="lexical",
                    message=f"Computing lexical measures ({processed}/{total}).",
                    processed_models_in_phase=processed,
                    valid_models_loaded=processed,
                ),
                cancel_requested=cancel_requested,
                total_models=total_models,
            )
        except InterruptedError as exc:
            raise MeasureCancelledError(str(exc)) from exc
        measured_model_count = len(lexical_per_model.d2_m1_label_presence)
        completed_model_ops += total_models

    # Compute construct measures if enabled
    construct_dataset = None
    construct_per_model = None
    if profile.measure.constructs and profile.measure.constructs.enabled:
        constructs = load_construct_defs(profile.parse.parser_language)
        try:
            construct_dataset, construct_per_model = compute_construct_measures(
                _iter_ir_models(ir_files, cancel_requested=cancel_requested),
                constructs=constructs or {},
                progress_callback=lambda processed, total: _emit_phase_progress(
                    phase="constructs",
                    message=f"Computing construct measures ({processed}/{total}).",
                    processed_models_in_phase=processed,
                    valid_models_loaded=processed,
                ),
                cancel_requested=cancel_requested,
                total_models=total_models,
            )
        except InterruptedError as exc:
            raise MeasureCancelledError(str(exc)) from exc
        measured_model_count = measured_model_count or len(
            construct_per_model.d3_m1_construct_presence
        )
        completed_model_ops += total_models

    # Compute size & complexity measures if enabled
    size_complexity_dataset = None
    size_complexity_per_model = None
    if profile.measure.size_complexity.enabled:
        try:
            size_complexity_dataset, size_complexity_per_model = compute_size_complexity_measures(
                _iter_ir_models(ir_files, cancel_requested=cancel_requested),
                progress_callback=lambda processed, total: _emit_phase_progress(
                    phase="size_complexity",
                    message=f"Computing size/complexity measures ({processed}/{total}).",
                    processed_models_in_phase=processed,
                    valid_models_loaded=processed,
                ),
                cancel_requested=cancel_requested,
                total_models=total_models,
            )
        except InterruptedError as exc:
            raise MeasureCancelledError(str(exc)) from exc
        measured_model_count = measured_model_count or len(
            size_complexity_per_model.d4_m1_model_size
        )
        completed_model_ops += total_models

    if measured_model_count is None:
        measured_model_count = valid_models_hint if valid_models_hint > 0 else total_models

    # Combine metrics into MeasureResultDataset
    dataset_result = MeasureResultDataset(
        num_models=measured_model_count,
        parsing=parsing_dataset,
        lexical=lexical_dataset,
        constructs=construct_dataset,
        size_complexity=size_complexity_dataset,
    )

    # Create per-model result
    per_model_result = MeasureResultPerModel(
        parsing=parsing_per_model,
        lexical=lexical_per_model,
        constructs=construct_per_model,
        size_complexity=size_complexity_per_model,
    )

    _emit_progress(
        {
            "phase": "completed",
            "message": "Measure computation completed.",
            "percentage": 100.0,
            "counters": {
                "total_models": total_models,
                "processed_models": total_models,
                "valid_models_loaded": measured_model_count,
            },
        }
    )

    return dataset_result, per_model_result


def save_measure_dataset(measure: MeasureResultDataset, output_path: str) -> None:
    """
    Save dataset-level measures to JSON file.

    Args:
        measure: MeasureResultDataset object to save
        output_path: Path to output JSON file
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(measure.to_dict(), f, indent=2)


def save_measure_per_model(measure: MeasureResultPerModel, output_path: str) -> None:
    """
    Save per-model measures to JSON file.

    Args:
        measure: MeasureResultPerModel object to save
        output_path: Path to output JSON file
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(measure.to_dict(), f, indent=2)


def _collect_per_model_measure_entries(measure: MeasureResultPerModel) -> Dict[str, Dict[str, Any]]:
    """
    Convert MeasureResultPerModel into per-model records.

    Output structure:
    {
      "<model_id>": {
        "parsing": {"d1_m1_parse_status": {...}, ...},
        "lexical": {...},
        ...
      }
    }
    """
    measure_dict = measure.to_dict()
    per_model_records: Dict[str, Dict[str, Any]] = {}

    for dimension, dimension_payload in measure_dict.items():
        if not isinstance(dimension_payload, dict):
            continue
        for measure_name, measure_values in dimension_payload.items():
            if not isinstance(measure_values, dict):
                continue
            for model_id, model_value in measure_values.items():
                model_record = per_model_records.setdefault(model_id, {})
                dimension_record = model_record.setdefault(dimension, {})
                dimension_record[measure_name] = model_value

    return per_model_records


def save_measure_per_model_split(
    measure: MeasureResultPerModel,
    output_dir: str,
) -> Dict[str, Any]:
    """
    Save per-model measures into one JSON file per model.

    Writes:
      - {output_dir}/measures/{model_id}.json
      - {output_dir}/measures_index.json

    Returns:
      Index payload as dictionary.
    """
    root = Path(output_dir)
    measures_dir = root / MEASURES_DIRNAME
    measures_dir.mkdir(parents=True, exist_ok=True)

    per_model_records = _collect_per_model_measure_entries(measure)
    model_entries: List[Dict[str, Any]] = []

    for model_id in sorted(per_model_records.keys()):
        record = per_model_records[model_id]
        model_path = measures_dir / f"{model_id}.json"
        with open(model_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "model_id": model_id,
                    "measures": record,
                },
                f,
                indent=2,
            )
        model_entries.append(
            {
                "model_id": model_id,
                "path": str(Path(MEASURES_DIRNAME) / f"{model_id}.json"),
            }
        )

    index_payload: Dict[str, Any] = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "count": len(model_entries),
        "models": model_entries,
    }
    index_path = root / MEASURES_INDEX_FILENAME
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index_payload, f, indent=2)

    return index_payload


def load_measure_per_model_split(
    measures_index_path: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    cancel_requested: Optional[Callable[[], bool]] = None,
) -> Dict[str, Any]:
    """
    Load split per-model measure files and rebuild the aggregated structure.

    Returns structure compatible with MeasureResultPerModel.to_dict().
    """
    index_path = Path(measures_index_path)
    if not index_path.exists():
        raise ValueError(f"Measures index file does not exist: {measures_index_path}")

    with open(index_path, "r", encoding="utf-8") as f:
        index_payload = json.load(f)

    model_entries = index_payload.get("models", [])
    if not isinstance(model_entries, list):
        raise ValueError("Invalid measures index format: 'models' must be a list")

    aggregated: Dict[str, Dict[str, Dict[str, Any]]] = {}
    root = index_path.parent
    total_models = len(model_entries)

    for model_index, entry in enumerate(model_entries, start=1):
        if cancel_requested and cancel_requested():
            raise InterruptedError("Report generation cancelled.")

        if not isinstance(entry, dict):
            continue
        model_id = entry.get("model_id")
        rel_path = entry.get("path")
        if not model_id or not rel_path:
            continue

        model_file = root / str(rel_path)
        if not model_file.exists():
            raise ValueError(f"Missing per-model measures file: {model_file}")

        with open(model_file, "r", encoding="utf-8") as f:
            model_payload = json.load(f)

        measures_payload = model_payload.get("measures", {})
        if not isinstance(measures_payload, dict):
            continue

        for dimension, dimension_payload in measures_payload.items():
            if not isinstance(dimension_payload, dict):
                continue
            aggregated_dimension = aggregated.setdefault(dimension, {})
            for measure_name, value in dimension_payload.items():
                model_map = aggregated_dimension.setdefault(measure_name, {})
                model_map[model_id] = value

        if progress_callback and (model_index % 10 == 0 or model_index == total_models):
            progress_callback(model_index, total_models)

    return aggregated
