"""UML XMI model parser."""

import xml.etree.ElementTree as ET
import logging
from pathlib import Path
from typing import Tuple
from cmbenchmark.parser.base import BaseParser, register_parser, CannotParseError
from cmbenchmark.types.models import LossReport
from cmbenchmark.types.ir import IR

from .indexer import build_index
from .context import ParseContext
from .builder import build_nodes, build_edges
from .registry import create_registry
from .xml_utils import local, get_xmi_id, attr, first_child
from .extractors.documentation import extract_documentation

logger = logging.getLogger(__name__)


@register_parser
class UmlXmiParser(BaseParser):
    """Parser for UML XMI models."""

    language = "UML-old"

    def __init__(self):
        """Initialize parser with handler registry."""
        super().__init__()
        self.registry = create_registry()

    def parse(self, filepath: str) -> Tuple[IR, LossReport]:
        """
        Parse a UML model file into IR using a modular approach.

        Args:
            filepath: Path to the XMI/UML file

        Returns:
            Tuple of (IR object, LossReport object)

        Raises:
            CannotParseError: If the file is not a valid XMI/UML file
        """
        path = Path(filepath)
        
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
        except ET.ParseError as e:
            raise CannotParseError(f"Invalid XML: {e}")

        # Check if this is an XMI file
        if local(root.tag) != "XMI":
            raise CannotParseError("Not a valid XMI file")

        # Extract model element
        model_elem = None
        for elem in root.iter():
            if local(elem.tag) == "Model":
                model_elem = elem
                break
        if model_elem is None:
            raise CannotParseError("No UML Model element found")

        # Extract model metadata
        model_id = get_xmi_id(model_elem) or ""
        model_name = attr(model_elem, "name")

        # Extract XMI version and UML namespace from root
        xmi_version = root.get("{http://schema.omg.org/spec/XMI/2.1}version", "")
        uml_namespace = "http://www.eclipse.org/uml2/5.0.0/UML"

        # Extract imports
        imports = []
        for package_import in root.iter():
            if local(package_import.tag) == "packageImport":
                imported_package = first_child(package_import, "importedPackage")
                if imported_package is not None:
                    href = attr(imported_package, "href")
                    if href:
                        imports.append(href)

        # Extract documentation from model annotations
        documentation = extract_documentation(model_elem)

        # Build model data
        model_data = {
            "modelId": model_id,
            "name": model_name,
            "xmi_version": xmi_version,
            "uml_namespace": uml_namespace,
            "imports": imports,
        }
        if documentation:
            model_data["documentation"] = documentation

        # Build index
        index = build_index(root)

        # Create parse context
        ctx = ParseContext(
            index=index,
            id_to_name={},
            warnings=[]
        )

        # Build nodes (this will populate ctx.id_to_name)
        nodes = build_nodes(ctx, self.registry)

        # Build edges
        edges = build_edges(ctx, self.registry)

        # Log warnings if any
        if ctx.warnings:
            for warning in ctx.warnings:
                logger.warning(warning)

        # Create IR
        ir = IR(
            id=path.stem,
            language=self.language,
            data=model_data,
            nodes=nodes,
            edges=edges,
        )

        # Create loss report (include warnings if desired)
        loss_report = LossReport(
            parser=self.parser_id,
            loss={},
            source_relpath=str(path.name),
        )

        return ir, loss_report

