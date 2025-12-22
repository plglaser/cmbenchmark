"""UML parser module."""

from cmbenchmark.parser.uml.uml_parser import UMLXMIParser, ParseOptions, ParseContext

# Export parser as 'parser' to match CLI expectations
parser = UMLXMIParser

__all__ = ["UMLXMIParser", "ParseOptions", "ParseContext", "parser"]

