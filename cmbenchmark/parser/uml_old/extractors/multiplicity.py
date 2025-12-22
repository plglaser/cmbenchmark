"""Multiplicity extraction utilities."""

from typing import Optional
import xml.etree.ElementTree as ET
from ..xml_utils import attr


def get_multiplicity(value_elem: Optional[ET.Element]) -> Optional[str]:
    """Extract multiplicity value from lowerValue or upperValue element."""
    if value_elem is None:
        return None
    return attr(value_elem, "value") or None

