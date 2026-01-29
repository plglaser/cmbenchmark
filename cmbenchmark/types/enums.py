"""Enum types for cmbenchmark."""

from enum import Enum
from typing import Literal


class WarningType(str, Enum):
    """Types of warnings that can occur during parsing."""
    UNKNOWN_NODE_TYPE = "UNKNOWN_NODE_TYPE"
    UNKNOWN_EDGE_TYPE = "UNKNOWN_EDGE_TYPE"
    DUPLICATE_ID = "DUPLICATE_ID"
    UNRESOLVED_REFERENCE = "UNRESOLVED_REFERENCE"
    MISSING_ATTRIBUTE = "MISSING_ATTRIBUTE"
    OTHER = "OTHER"


ParseStatus = Literal["success", "warning", "failure"]
