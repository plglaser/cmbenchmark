"""Parser module for conceptual models."""

from .base import BaseParser, register_parser, get_parser, get_all_parsers
from cmbenchmark.types.models import LossReport

__all__ = ["BaseParser", "register_parser", "get_parser", "get_all_parsers", "LossReport"]

