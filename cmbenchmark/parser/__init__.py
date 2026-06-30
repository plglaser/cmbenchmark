"""Parser module for conceptual models."""

from .base import BaseParser, register_parser, get_parser, get_all_parsers

# Import parser modules for registration side effects.
# Each parser class uses @register_parser at import time.
from .uml import UMLXMIParser, UMLCustom1Parser, UMLXMLPyEcoreParser  # noqa: F401
from .archimate import ArchiMateArchiParser, ArchiMateXMLParser  # noqa: F401
from .ecore import EcoreParser  # noqa: F401
from .bpmn import BPMNSignavioJSONParser  # noqa: F401

__all__ = ["BaseParser", "register_parser", "get_parser", "get_all_parsers"]
