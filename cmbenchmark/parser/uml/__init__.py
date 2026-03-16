"""UML parser module."""

from cmbenchmark.parser.uml.uml_parser import UMLXMIParser, ParseOptions, ParseContext
from cmbenchmark.parser.uml.uml_custom1_parser import UMLCustom1Parser

# Export parser as 'parser' to match CLI expectations
parser = UMLXMIParser

__all__ = ["UMLXMIParser", "UMLCustom1Parser", "ParseOptions", "ParseContext", "parser"]
