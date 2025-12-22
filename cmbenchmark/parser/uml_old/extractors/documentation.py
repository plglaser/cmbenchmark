"""Documentation extraction utilities."""

from typing import Optional
import xml.etree.ElementTree as ET
from ..xml_utils import local, attr


def extract_documentation(element: ET.Element) -> Optional[str]:
    """Extract documentation from eAnnotations."""
    for ext in element.iter():
        if local(ext.tag) == "Extension":
            for ann in ext.iter():
                if local(ann.tag) == "eAnnotations":
                    if attr(ann, "source") == "genmymodel":
                        for detail in ann.iter():
                            if local(detail.tag) == "details":
                                if attr(detail, "key") == "gmm-documentation":
                                    value = attr(detail, "value")
                                    if value:
                                        return value
    return None

