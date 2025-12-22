"""XML utility functions for UML parsing."""

from typing import List, Optional
import xml.etree.ElementTree as ET


def local(tag: str) -> str:
    """Extract local tag name, stripping namespace prefix."""
    return tag.split("}", 1)[-1]  # works for both "{ns}tag" and "tag"


def children(elem: ET.Element, local_name: str) -> List[ET.Element]:
    """Get all direct children with the given local tag name."""
    return [c for c in elem if local(c.tag) == local_name]


def first_child(elem: ET.Element, local_name: str) -> Optional[ET.Element]:
    """Get the first direct child with the given local tag name."""
    for c in elem:
        if local(c.tag) == local_name:
            return c
    return None


def attr(elem: ET.Element, name: str, default: str = "") -> str:
    """Get an attribute value with a default."""
    return elem.get(name, default) or default


def get_xmi_id(elem: ET.Element) -> Optional[str]:
    """Get xmi:id attribute value."""
    return elem.get("{http://schema.omg.org/spec/XMI/2.1}id")


def get_xsi_type(elem: ET.Element) -> str:
    """Get xsi:type attribute value."""
    xsi_ns = "http://www.w3.org/2001/XMLSchema-instance"
    return elem.get(f"{{{xsi_ns}}}type", "")

