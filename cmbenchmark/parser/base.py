"""Base parser interface and registry."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from cmbenchmark.types.ir import IR
from cmbenchmark.types.models import LossReport, CannotParseError

# Global registry for parsers
_PARSER_REGISTRY: Dict[str, type] = {}

def register_parser(parser_class: type) -> type:
    """Decorator to register a parser class."""
    parser_instance = parser_class()
    _PARSER_REGISTRY[parser_instance.language] = parser_class
    return parser_class


def get_parser(language: str) -> Optional[type]:
    """Get parser class by language name."""
    return _PARSER_REGISTRY.get(language)


def get_all_parsers() -> List[type]:
    """Get all registered parser classes."""
    return list(_PARSER_REGISTRY.values())


class BaseParser(ABC):
    """Base interface for model parsers."""

    language: str
    version: str = "1.0.0"  # Parser version identifier

    @property
    def parser_id(self) -> str:
        """Get parser identifier (language@version)."""
        return f"{self.language.lower()}@{self.version}"

    @abstractmethod
    def parse(self, filepath: str) -> Tuple[IR, LossReport]:
        """
        Parse a model file into IR and return loss report.

        Args:
            filepath: Path to the model file

        Returns:
            Tuple of (IR object, LossReport object)

        Raises:
            CannotParseError: If the file is not in this parser's format
                (e.g., wrong XML root/namespace)
        """
        pass

