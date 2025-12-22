"""Core context classes for UML parsing."""

from dataclasses import dataclass
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET


@dataclass
class ElementView:
    """Canonical view of an XML element for parsing."""
    
    elem: ET.Element
    id: str
    name: str
    metaclass: str
    tag_local: str
    container_id: Optional[str]
    qname_parts: List[str]


@dataclass
class ParseContext:
    """Context for parsing operations."""
    
    index: Dict[str, ElementView]
    id_to_name: Dict[str, str]
    warnings: List[str]

