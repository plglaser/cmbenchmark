"""Services module for cmbenchmark."""

from .scan import scan_dataset
from .measure import (
    compute_measure,
    save_measure_dataset,
    save_measure_per_model,
    save_measure_per_model_split,
    load_measure_per_model_split,
)
from .report import generate_report, save_report
from .custom_views import (
    get_field_catalog,
    load_custom_views,
    create_custom_view,
    update_custom_view,
    delete_custom_view,
    preview_custom_view,
)

__all__ = [
    "scan_dataset",
    "compute_measure",
    "save_measure_dataset",
    "save_measure_per_model",
    "save_measure_per_model_split",
    "load_measure_per_model_split",
    "generate_report",
    "save_report",
    "get_field_catalog",
    "load_custom_views",
    "create_custom_view",
    "update_custom_view",
    "delete_custom_view",
    "preview_custom_view",
]
