"""Measure service for computing measures on IR models."""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json
from cmbenchmark.types.measures import MeasureResultDataset, MeasureResultPerModel
from cmbenchmark.types.dataset import IRInfo
from cmbenchmark.types.ir import IR
from cmbenchmark.types.profile import BenchmarkProfile
from cmbenchmark.measures.parsing_measures import compute_parsing_measures
from cmbenchmark.measures.lexical_measures import compute_lexical_measures
from cmbenchmark.types.profile import ScanConfig, ParseConfig, MeasureConfig


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


def compute_measure(
    ir_path: str,
    profile: Optional[BenchmarkProfile] = None,
) -> Tuple[MeasureResultDataset, MeasureResultPerModel]:
    """
    Compute measures for all IR models in the given directory.

    Args:
        ir_path: Path to directory containing IR JSON files
        profile: Optional BenchmarkProfile configuration. If None, uses default profile.

    Returns:
        Tuple of (MeasureResultDataset, MeasureResultPerModel) containing computed measures
    """
    if profile is None:
        # Create a minimal default profile
        profile = BenchmarkProfile(
            name="default",
            version="1.0",
            output_path="./out",
            scan=ScanConfig(dataset_path="./data"),
            parse=ParseConfig(parser_language="ArchiMate-Archi"),
            measure=MeasureConfig(),
        )
    ir_dir = Path(ir_path)
    ir_files = list(ir_dir.glob("*.json"))

    if not ir_files:
        raise ValueError("No IR files found in directory")

    # Load all IR models
    ir_models: List[IR] = []
    for ir_file in ir_files:
        try:
            ir = IR.load(str(ir_file))
            ir_models.append(ir)
        except Exception as e:
            # Skip files that can't be loaded
            continue

    if not ir_models:
        raise ValueError("No valid IR models could be loaded")

    # Load IRInfo for parsing measures
    ir_info = _load_ir_info(ir_dir)
    if ir_info is None:
        raise ValueError(
            "ir_info.json not found. Please ensure parsing has been completed first. "
            "Expected locations: {ir_path}/ir_info.json or {ir_path}/../ir_info.json"
        )

    # Compute parsing measures (returns both dataset and per-model)
    parsing_dataset, parsing_per_model = compute_parsing_measures(ir_info)

    # Compute lexical measures if enabled
    lexical_dataset = None
    lexical_per_model = None
    if profile.measure.lexical.enabled:
        lexical_dataset, lexical_per_model = compute_lexical_measures(
            ir_models,
            lexical_profile=profile.measure.lexical,
        )

    # Combine metrics into MeasureResultDataset
    dataset_result = MeasureResultDataset(
        num_models=len(ir_models),
        parsing=parsing_dataset,
        lexical=lexical_dataset,
    )

    # Create per-model result
    per_model_result = MeasureResultPerModel(
        parsing=parsing_per_model,
        lexical=lexical_per_model,
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
