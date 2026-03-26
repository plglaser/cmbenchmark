"""BPMN parser module."""

from .bpmn_signavio_json_parser import BPMNSignavioJSONParser

# Export parser alias for CLI compatibility.
parser = BPMNSignavioJSONParser

__all__ = ["BPMNSignavioJSONParser", "parser"]
