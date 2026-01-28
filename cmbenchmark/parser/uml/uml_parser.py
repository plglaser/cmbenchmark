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
    UseCaseHandler,
    ActorHandler,
)

IGNORED_UNHANDLED_ELEMENTS: set[str] = {
    "uml:Activity",
    "uml:StateMachine",
    "uml:Interaction",
    "uml:Dependency",
    "uml:InstanceSpecification",
}

# Element types that contain nested packagedElement children that should be recursed into
RECURSE_PACKAGED_TYPES: set[str] = {"uml:Package", "uml:UseCase"}

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

    # store created nodes for quick lookup
    nodes_by_id: Dict[str, Node] = field(default_factory=dict)
    
    # handler map for element type -> handler lookup
    handler_map: Dict[str, ElementHandler] = field(default_factory=dict)
    
    # track edge IDs to avoid duplicate edges
    edge_ids: set[str] = field(default_factory=set)

    def elem(self, _id: str) -> Optional[ET.Element]:
        """Get element by xmi:id."""
        return self.id_index.get(_id)

    def add_node(self, node: Node) -> None:
        """Add node to IR and index."""
        self.ir.nodes.append(node)
        self.nodes_by_id[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        """Add edge to IR, avoiding duplicates."""
        if edge.id in self.edge_ids:
            print(f"[DUPLICATE EDGE] {edge.id}")
            return
        self.edge_ids.add(edge.id)
        self.ir.edges.append(edge)


@register_parser
class UMLXMIParser(BaseParser):
    language = "UML"

    def __init__(
        self,
        options: Optional[ParseOptions] = None,
        handlers: Optional[List[ElementHandler]] = None,
    ):
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
            UseCaseHandler(),
            ActorHandler(),
        ]

    def parse(self, filepath: str) -> Tuple[IR, LossReport]:
        """
        Parse a UML XMI file into IR.

        Args:
            filepath: Path to the XMI file

        Returns:
            Tuple of (IR object, LossReport)
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

    def _parse_packaged_element_metadata(
        self, pe: ET.Element
    ) -> Optional[Tuple[str, str]]:
        """Parse packagedElement metadata, skipping tool extensions.
        
        Returns:
            Tuple of (pe_type, pe_id) if valid, None if should be skipped
        """
        if is_tool_extension(pe):
            return None
        
        pe_type = xsi_type(pe)
        if not pe_type:
            return None
        
        pe_id = xmi_id(pe)
        if not pe_id:
            return None
        
        return (pe_type, pe_id)

    def _parse_elements(self, ctx: ParseContext) -> None:
        """Parse all elements using registered handlers.
        
        Parsing happens in stages:
        1. Build handler map
        2. Handle top-level Model element
        3. Process top-level packagedElement elements (recursively)
        4. Process nested elements (e.g., generalizations inside classes)
        """
        # Build handler map by element type
        ctx.handler_map = {h.element_type: h for h in self.handlers}

        # Stage 1: Handle the Model element explicitly
        model = find_model(ctx.root)
        model_handler = ctx.handler_map.get("uml:Model")
        if model_handler:
            model_handler.handle(ctx, model)
        else:
            print(f"[UNHANDLED MODEL] {localname(model.tag)}")
            return

        # Stage 2: Process top-level packagedElement elements
        # Attributes and nested elements like type, lowerValue, upperValue are handled by their parent handlers
        self._process_packaged_elements(ctx, model)

        # Stage 3: Process nested elements (e.g., generalizations inside classes)
        # We need to process generalizations separately since they're nested
        self._process_nested_generalizations(ctx)

    def _process_packaged_elements(self, ctx: ParseContext, container: ET.Element) -> None:
        """Recursively process packagedElement children."""
        for pe in container.findall("./packagedElement"):
            metadata = self._parse_packaged_element_metadata(pe)
            if not metadata:
                continue
            
            pe_type, pe_id = metadata

            # Check if we have a handler for this element type
            handler = ctx.handler_map.get(pe_type)
            if handler:
                handler.handle(ctx, pe)
                # Recursively process nested packages and use cases
                if pe_type in RECURSE_PACKAGED_TYPES:
                    self._process_packaged_elements(ctx, pe)
            else:
                # Print unhandled element type
                if pe_type in IGNORED_UNHANDLED_ELEMENTS:
                    continue
                print(f"[UNHANDLED ELEMENT] Type: {pe_type}, ID: {pe_id}, Tag: {localname(pe.tag)}")
                
                # Still recurse into packages and use cases even if unhandled
                if pe_type in RECURSE_PACKAGED_TYPES:
                    self._process_packaged_elements(ctx, pe)

    def _process_nested_generalizations(self, ctx: ParseContext) -> None:
        """Process generalizations nested in classes/interfaces."""
        for elem in ctx.root.iter():
            if is_tool_extension(elem):
                continue

            # Handle generalizations
            for gen in elem.findall("./generalization"):
                    gen_handler = ctx.handler_map.get("uml:Generalization")
                    if gen_handler:
                        gen_handler.handle(ctx, gen)
                        
                

    def _create_containment_edges(self, ctx: ParseContext, model: ET.Element) -> None:
        """Create containment edges for packages and their contents."""
        if not ctx.options.include_packages:
            return

        # Start walking from model (top-level packages have no parent)
        self._walk_containment(ctx, model, current_pkg_id=None)

    def _walk_containment(
        self, ctx: ParseContext, container: ET.Element, current_pkg_id: Optional[str]
    ) -> None:
        """Recursively walk packagedElement children to create containment edges."""
        for pe in container.findall("./packagedElement"):
            metadata = self._parse_packaged_element_metadata(pe)
            if not metadata:
                continue
            
            pe_type, pe_id = metadata

            # If this is a package, recurse with new package context
            if pe_type == "uml:Package":
                # Create containment edge from current package
                if current_pkg_id:
                    edge_id = f"{current_pkg_id}__contains__{pe_id}"
                    ctx.add_edge(
                        Edge(
                            id=edge_id,
                            sourceId=current_pkg_id,
                            targetId=pe_id,
                            type="contains",
                            data={},
                        )
                    )
                self._walk_containment(ctx, pe, pe_id)
            else:
                # Non-package element: create containment edge if inside a package
                if current_pkg_id:
                    edge_id = f"{current_pkg_id}__contains__{pe_id}"
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
                self._walk_containment(ctx, pe, current_pkg_id)
