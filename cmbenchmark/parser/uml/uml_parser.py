"""UML XMI parser for converting UML models to graph-based IR."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET

from cmbenchmark.parser.base import BaseParser, register_parser
from cmbenchmark.types.ir import IR, Node, Edge
from cmbenchmark.types.models import LossReport
from cmbenchmark.parser.uml.xmi_utils import (
    xmi_id,
    xsi_type,
    is_tool_extension,
    find_model,
    localname,
)
from cmbenchmark.parser.uml.handlers import (
    ElementHandler,
    ModelHandler,
    PackageHandler,
    ClassHandler,
    InterfaceHandler,
    AssociationHandler,
    GeneralizationHandler,
    EnumerationHandler,
    DataTypeHandler,
)


@dataclass(frozen=True)
class ParseOptions:
    """Options for UML parsing."""

    # creates a Node for each uml:Package with a "contains" edge to contained elements
    include_packages: bool = True


@dataclass
class ParseContext:
    """Context for UML parsing operations."""

    root: ET.Element
    ir: IR
    options: ParseOptions

    id_index: Dict[str, ET.Element] = field(default_factory=dict)
    parent_map: Dict[ET.Element, ET.Element] = field(default_factory=dict)

    # derived qualified names for elements we care about (classifiers, packages, etc.)
    qualified_name: Dict[str, str] = field(default_factory=dict)

    # optional: store created nodes for quick lookup
    nodes_by_id: Dict[str, Node] = field(default_factory=dict)

    def elem(self, _id: str) -> Optional[ET.Element]:
        """Get element by xmi:id."""
        return self.id_index.get(_id)

    def qname(self, _id: str) -> Optional[str]:
        """Get qualified name by xmi:id."""
        return self.qualified_name.get(_id)

    def add_node(self, node: Node) -> None:
        """Add node to IR and index."""
        self.ir.nodes.append(node)
        self.nodes_by_id[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        """Add edge to IR."""
        self.ir.edges.append(edge)


IGNORED_UNHANDLED_ELEMENTS = ["uml:Activity", "uml:StateMachine", "uml:Interaction", "uml:Dependency"]

@register_parser
class UMLXMIParser(BaseParser):
    """
    Orchestrates:
      - indexing
      - model meta extraction
      - qualifiedName computation (package nesting)
      - element-handler-based semantic parsing
    """

    language = "UML"

    def __init__(
        self,
        options: Optional[ParseOptions] = None,
        handlers: Optional[List[ElementHandler]] = None,
    ):
        """
        Initialize parser with options and handlers.

        Args:
            options: Parsing options (defaults to include_packages=True)
            handlers: List of element handler instances (defaults to standard handlers)
        """
        self.options = options or ParseOptions()
        self.handlers = handlers or self._get_default_handlers()

    def _get_default_handlers(self) -> List[ElementHandler]:
        """Get default set of element handlers."""
        return [
            ModelHandler(),
            PackageHandler(),
            ClassHandler(),
            InterfaceHandler(),
            AssociationHandler(),
            GeneralizationHandler(),
            EnumerationHandler(),
            DataTypeHandler(),
        ]

    def parse(self, filepath: str) -> Tuple[IR, LossReport]:
        """
        Parse a UML XMI file into IR.

        Args:
            filepath: Path to the XMI file

        Returns:
            Tuple of (IR object, empty LossReport)
        """
        tree = ET.parse(filepath)
        root = tree.getroot()

        model = find_model(root)
        model_id = xmi_id(model) or "model"
        model_name = model.attrib.get("name", "")

        ir = IR(id=model_id, language=self.language, data={"name": model_name})
        ctx = ParseContext(
            root=root, ir=ir, options=self.options
        )

        self._build_indices(ctx)
        self._compute_qualified_names(ctx, model)
        self._parse_elements(ctx)
        self._create_containment_edges(ctx, model)

        # Return empty loss report
        path = Path(filepath)
        loss_report = LossReport(
            parser=self.parser_id,
            loss={},
            source_relpath=str(path.name),
        )

        return ctx.ir, loss_report

    def _build_indices(self, ctx: ParseContext) -> None:
        """Build xmi:id index and parent map."""
        for e in ctx.root.iter():
            _id = xmi_id(e)
            if _id:
                ctx.id_index[_id] = e

        for parent in ctx.root.iter():
            for child in list(parent):
                ctx.parent_map[child] = parent

    def _compute_qualified_names(self, ctx: ParseContext, model: ET.Element) -> None:
        """
        Derive package-qualified names. Always computed, regardless of include_packages.
        """
        def walk(container: ET.Element, pkg_path: List[str]) -> None:
            for pe in container.findall("./packagedElement"):
                if is_tool_extension(pe):
                    continue

                pe_id = xmi_id(pe)
                pe_name = pe.attrib.get("name", "")
                pe_type = xsi_type(pe)

                if pe_type == "uml:Package":
                    # Only add non-empty package names to path to avoid "::" in qualified names
                    new_path = pkg_path + ([pe_name] if pe_name else [])
                    if pe_id and pe_name:
                        ctx.qualified_name[pe_id] = "::".join(new_path)
                    walk(pe, new_path)
                else:
                    if pe_id and pe_name:
                        ctx.qualified_name[pe_id] = "::".join(pkg_path + [pe_name])
                    walk(pe, pkg_path)

        walk(model, pkg_path=[])

    def _parse_elements(self, ctx: ParseContext) -> None:
        """Parse all elements using registered handlers."""
        # Build handler map by element type
        handler_map: Dict[str, ElementHandler] = {}
        for handler in self.handlers:
            handler_map[handler.element_type] = handler

        # Store handler map in context for use in logging
        ctx._handler_map = handler_map

        # First, handle the Model element explicitly
        model = find_model(ctx.root)
        model_handler = handler_map.get("uml:Model")
        if model_handler:
            model_handler.handle(ctx, model)

        # Process only top-level packagedElement elements (not nested elements)
        # Nested elements like type, lowerValue, upperValue are handled by their parent handlers
        def process_packaged_elements(container: ET.Element) -> None:
            """Recursively process packagedElement children."""
            for pe in container.findall("./packagedElement"):
                if is_tool_extension(pe):
                    continue

                pe_type = xsi_type(pe)
                if not pe_type:
                    continue

                # Check if we have a handler for this element type
                handler = handler_map.get(pe_type)
                if handler:
                    handler.handle(ctx, pe)
                    # Recursively process nested packages
                    if pe_type == "uml:Package":
                        process_packaged_elements(pe)
                else:
                    # Print unhandled element type
                    pe_id = xmi_id(pe)

                    # TODO: Remoe this
                    if (pe_type in IGNORED_UNHANDLED_ELEMENTS):
                        continue
                    print(f"[UNHANDLED ELEMENT] Type: {pe_type}, ID: {pe_id}, Tag: {localname(pe.tag)}")
                    # Still recurse into packages even if unhandled
                    if pe_type == "uml:Package":
                        process_packaged_elements(pe)

        # Process packaged elements starting from model
        process_packaged_elements(model)

        # Also handle nested elements (e.g., generalizations inside classes)
        # We need to process generalizations separately since they're nested
        for elem in ctx.root.iter():
            if is_tool_extension(elem):
                continue

            # Handle generalizations nested in classes/interfaces
            if xsi_type(elem) in ("uml:Class", "uml:Interface"):
                for gen in elem.findall("./generalization"):
                    gen_handler = handler_map.get("uml:Generalization")
                    if gen_handler:
                        gen_handler.handle(ctx, gen)

    def _create_containment_edges(self, ctx: ParseContext, model: ET.Element) -> None:
        """Create containment edges for packages and their contents."""
        if not ctx.options.include_packages:
            return

        def walk(container: ET.Element, current_pkg_id: Optional[str]) -> None:
            for pe in container.findall("./packagedElement"):
                if is_tool_extension(pe):
                    continue

                pe_id = xmi_id(pe)
                if not pe_id:
                    continue

                pe_type = xsi_type(pe)

                # If this is a package, recurse with new package context
                if pe_type == "uml:Package":
                    # Create containment edge from current package
                    if current_pkg_id:
                        edge_id = f"{current_pkg_id}__contains__{pe_id}"
                        if not any(e.id == edge_id for e in ctx.ir.edges):
                            ctx.add_edge(
                                Edge(
                                    id=edge_id,
                                    sourceId=current_pkg_id,
                                    targetId=pe_id,
                                    type="contains",
                                    data={},
                                )
                            )
                    walk(pe, pe_id)
                else:
                    # Non-package element: create containment edge if inside a package
                    if current_pkg_id:
                        edge_id = f"{current_pkg_id}__contains__{pe_id}"
                        if not any(e.id == edge_id for e in ctx.ir.edges):
                            ctx.add_edge(
                                Edge(
                                    id=edge_id,
                                    sourceId=current_pkg_id,
                                    targetId=pe_id,
                                    type="contains",
                                    data={"elementType": pe_type} if pe_type else {},
                                )
                            )
                    # Still recurse to catch nested packagedElement
                    walk(pe, current_pkg_id)

        # Start walking from model (top-level packages have no parent)
        walk(model, current_pkg_id=None)
