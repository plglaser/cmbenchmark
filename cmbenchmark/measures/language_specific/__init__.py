"""Language-specific metrics."""

from typing import List, Dict, Any
from collections import defaultdict
from cmbenchmark.types.ir import IR
from .uml_metrics import compute_uml_metrics
from .bpmn_metrics import compute_bpmn_metrics
from .validation.archimate_validation import validate_archimate

__all__ = ["compute_language_specific_metrics"]


def compute_language_specific_metrics(ir_models: List[IR]) -> Dict[str, Any]:
    """Compute all language-specific metrics."""
    # Group models by language
    models_by_language = defaultdict(list)
    for ir in ir_models:
        models_by_language[ir.language].append(ir)
    
    results = {
        "metrics": {}
    }
    
    # TODO: Refactor this (models_by_language does not exist anymore)

    # Compute UML metrics if UML models exist
    if "UML" in models_by_language:
        results["metrics"]["UML"] = compute_uml_metrics(models_by_language["UML"])
    
    # Compute BPMN metrics if BPMN models exist
    if "BPMN" in models_by_language:
        results["metrics"]["BPMN"] = compute_bpmn_metrics(models_by_language["BPMN"])
    
    # Compute ArchiMate metrics and validation if ArchiMate models exist
    archimate_languages = ["ArchiMate-Archi", "ArchiMate-XML"]
    for lang in archimate_languages:
        if lang in models_by_language:
            # Compute validation for all ArchiMate models
            all_validation_errors = []
            for ir in models_by_language[lang]:
                validation_errors = validate_archimate(ir)
                if validation_errors:
                    all_validation_errors.extend(validation_errors)
            
            # Initialize metrics dict for this language if it doesn't exist
            if lang not in results["metrics"]:
                results["metrics"][lang] = {}
            
            # Add validation errors to metrics
            results["metrics"][lang]["validation"] = all_validation_errors
    
    return results

