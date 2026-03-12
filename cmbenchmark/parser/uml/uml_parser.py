"""UML XMI parser for converting UML models to graph-based IR."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET

from cmbenchmark.parser.base import BaseParser, register_parser
from cmbenchmark.types.ir import IR, Node, Edge
from cmbenchmark.types.enums import WarningType
from cmbenchmark.types.parsing import ParserRunStats
from cmbenchmark.parser.uml.xmi_utils import (
    xmi_id,
    xsi_type,
    is_tool_extension,
    find_model,
    localname,
)
from cmbenchmark.parser.uml.metamodel import TAG_TO_CONCEPT, CONTAINMENT_CHILD_TAGS
from cmbenchmark.parser.uml.handlers import (
    ElementHandler,
    ModelHandler,
    PackageHandler,
    ClassHandler,
    InterfaceHandler,
    AssociationHandler,
    GeneralizationHandler,
    InterfaceRealizationHandler,
    DependencyHandler,
    EnumerationHandler,
    DataTypeHandler,
    ComponentHandler,
    UseCaseHandler,
    IncludeHandler,
    ExtendHandler,
    ActorHandler,
    SimpleNodeHandler,
    AssociationClassHandler,
    InformationFlowHandler,
    DirectedEdgeHandler,
)

IGNORED_UNHANDLED_ELEMENTS: set[str] = set()


@dataclass(frozen=True)
class ParseOptions:
    """Options for UML parsing."""

    # Create a Node for each uml:Package with "contains" edges to contained elements.
    include_packages: bool = True


@dataclass
class ParseContext:
    """Context for UML parsing operations."""

    root: ET.Element
    ir: IR
    options: ParseOptions
    run_stats: Optional[ParserRunStats] = None

    id_index: Dict[str, ET.Element] = field(default_factory=dict)
    parent_map: Dict[ET.Element, ET.Element] = field(default_factory=dict)

    nodes_by_id: Dict[str, Node] = field(default_factory=dict)
    handler_map: Dict[str, ElementHandler] = field(default_factory=dict)
    tag_handler_map: Dict[str, str] = field(default_factory=dict)

    edge_ids: set[str] = field(default_factory=set)

    def elem(self, _id: str) -> Optional[ET.Element]:
        """Get element by xmi:id."""
        return self.id_index.get(_id)

    def add_node(self, node: Node) -> None:
        """Add node to IR and index."""
        if node.id in self.nodes_by_id:
            self.skip_with_warning(
                WarningType.DUPLICATE_ID,
                f"Duplicate node id '{node.id}' encountered; keeping first node and skipping duplicate.",
            )
            return
        self.ir.nodes.append(node)
        self.nodes_by_id[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        """Add edge to IR, avoiding duplicates."""
        if edge.id in self.edge_ids:
            self.skip_with_warning(
                WarningType.DUPLICATE_ID,
                f"Duplicate edge id '{edge.id}' encountered; keeping first edge and skipping duplicate.",
            )
            return
        self.edge_ids.add(edge.id)
        self.ir.edges.append(edge)

    def warn(self, warning_type: WarningType, message: str) -> None:
        """Record warning in parser run stats when available."""
        if self.run_stats is None:
            return
        self.run_stats.add_warning(warning_type, message)

    def skip_with_warning(self, warning_type: WarningType, message: str) -> None:
        """Record skipped element + warning in parser run stats when available."""
        if self.run_stats is None:
            return
        self.run_stats.add_skip(warning_type, message)


@register_parser
class UMLXMIParser(BaseParser):
    language = "UML"

    def __init__(
        self,
        options: Optional[ParseOptions] = None,
        handlers: Optional[List[ElementHandler]] = None,
    ):
        super().__init__()
        self.options = options or ParseOptions()
        self.handlers = handlers or self._get_default_handlers()

    def _get_default_handlers(self) -> List[ElementHandler]:
        """Get default set of element handlers."""
        return [
            ModelHandler(),
            PackageHandler(),
            ClassHandler(),
            InterfaceHandler(),
            EnumerationHandler(),
            DataTypeHandler(),
            ComponentHandler(),
            UseCaseHandler(),
            ActorHandler(),
            SimpleNodeHandler(
                element_type="uml:Activity",
                node_type="Activity",
                scalar_attrs=("visibility",),
                boolean_attrs=("isReadOnly", "isSingleExecution"),
            ),
            SimpleNodeHandler(
                element_type="uml:StateMachine",
                node_type="StateMachine",
                scalar_attrs=("visibility",),
                boolean_attrs=("isReentrant",),
            ),
            SimpleNodeHandler(
                element_type="uml:Interaction",
                node_type="Interaction",
                scalar_attrs=("visibility",),
            ),
            SimpleNodeHandler(
                element_type="uml:InstanceSpecification",
                node_type="InstanceSpecification",
                scalar_attrs=("visibility",),
                list_attrs=("classifier",),
                rename_map={"classifier": "classifierRefs"},
            ),
            AssociationClassHandler(),
            SimpleNodeHandler(
                element_type="uml:Device",
                node_type="Device",
                scalar_attrs=("visibility",),
                boolean_attrs=("isLeaf",),
            ),
            SimpleNodeHandler(
                element_type="uml:Node",
                node_type="Node",
                scalar_attrs=("visibility",),
                boolean_attrs=("isLeaf",),
            ),
            SimpleNodeHandler(
                element_type="uml:Artifact",
                node_type="Artifact",
                scalar_attrs=("visibility", "fileName"),
            ),
            SimpleNodeHandler(
                element_type="uml:ExecutionEnvironment",
                node_type="ExecutionEnvironment",
                scalar_attrs=("visibility",),
                boolean_attrs=("isLeaf",),
            ),
            SimpleNodeHandler(
                element_type="uml:PrimitiveType",
                node_type="PrimitiveType",
                scalar_attrs=("visibility",),
            ),
            SimpleNodeHandler(
                element_type="uml:EnumerationLiteral",
                node_type="EnumerationLiteral",
                scalar_attrs=("visibility",),
            ),
            SimpleNodeHandler(
                element_type="uml:OpaqueAction",
                node_type="OpaqueAction",
                list_attrs=("incoming", "outgoing"),
                rename_map={"incoming": "incomingRefs", "outgoing": "outgoingRefs"},
            ),
            SimpleNodeHandler(
                element_type="uml:InitialNode",
                node_type="InitialNode",
                list_attrs=("incoming", "outgoing"),
                rename_map={"incoming": "incomingRefs", "outgoing": "outgoingRefs"},
            ),
            SimpleNodeHandler(
                element_type="uml:ActivityFinalNode",
                node_type="ActivityFinalNode",
                list_attrs=("incoming", "outgoing"),
                rename_map={"incoming": "incomingRefs", "outgoing": "outgoingRefs"},
            ),
            SimpleNodeHandler(
                element_type="uml:FlowFinalNode",
                node_type="FlowFinalNode",
                list_attrs=("incoming", "outgoing"),
                rename_map={"incoming": "incomingRefs", "outgoing": "outgoingRefs"},
            ),
            SimpleNodeHandler(
                element_type="uml:DecisionNode",
                node_type="DecisionNode",
                list_attrs=("incoming", "outgoing"),
                rename_map={"incoming": "incomingRefs", "outgoing": "outgoingRefs"},
            ),
            SimpleNodeHandler(
                element_type="uml:MergeNode",
                node_type="MergeNode",
                list_attrs=("incoming", "outgoing"),
                rename_map={"incoming": "incomingRefs", "outgoing": "outgoingRefs"},
            ),
            SimpleNodeHandler(
                element_type="uml:JoinNode",
                node_type="JoinNode",
                list_attrs=("incoming", "outgoing"),
                rename_map={"incoming": "incomingRefs", "outgoing": "outgoingRefs"},
            ),
            SimpleNodeHandler(
                element_type="uml:ForkNode",
                node_type="ForkNode",
                list_attrs=("incoming", "outgoing"),
                rename_map={"incoming": "incomingRefs", "outgoing": "outgoingRefs"},
            ),
            SimpleNodeHandler(
                element_type="uml:ActivityPartition",
                node_type="ActivityPartition",
                list_attrs=("node",),
                rename_map={"node": "nodeRefs"},
            ),
            SimpleNodeHandler(
                element_type="uml:MessageOccurrenceSpecification",
                node_type="MessageOccurrenceSpecification",
                scalar_attrs=("enclosingInteraction",),
                list_attrs=("covered",),
                rename_map={"covered": "coveredRefs"},
            ),
            SimpleNodeHandler(
                element_type="uml:ExecutionOccurrenceSpecification",
                node_type="ExecutionOccurrenceSpecification",
                scalar_attrs=("enclosingInteraction",),
                list_attrs=("covered",),
                rename_map={"covered": "coveredRefs"},
            ),
            SimpleNodeHandler(
                element_type="uml:BehaviorExecutionSpecification",
                node_type="BehaviorExecutionSpecification",
                scalar_attrs=("enclosingInteraction", "start", "finish"),
                list_attrs=("covered",),
                rename_map={"covered": "coveredRefs"},
            ),
            SimpleNodeHandler(
                element_type="uml:Collaboration",
                node_type="Collaboration",
                scalar_attrs=("visibility",),
            ),
            SimpleNodeHandler(
                element_type="uml:State",
                node_type="State",
                scalar_attrs=("visibility", "container"),
                list_attrs=("incoming", "outgoing"),
                rename_map={"incoming": "incomingRefs", "outgoing": "outgoingRefs"},
            ),
            SimpleNodeHandler(
                element_type="uml:Pseudostate",
                node_type="Pseudostate",
                scalar_attrs=("visibility", "container", "kind"),
                list_attrs=("incoming", "outgoing"),
                rename_map={"incoming": "incomingRefs", "outgoing": "outgoingRefs"},
            ),
            SimpleNodeHandler(
                element_type="uml:Region",
                node_type="Region",
                scalar_attrs=("visibility", "stateMachine", "state"),
            ),
            SimpleNodeHandler(
                element_type="uml:Lifeline",
                node_type="Lifeline",
                scalar_attrs=("visibility", "represents", "decomposedAs"),
                list_attrs=("coveredBy",),
                rename_map={"coveredBy": "coveredByRefs"},
            ),
            SimpleNodeHandler(
                element_type="uml:CombinedFragment",
                node_type="CombinedFragment",
                scalar_attrs=("visibility", "interactionOperator", "enclosingInteraction"),
                list_attrs=("covered",),
                rename_map={"covered": "coveredRefs"},
            ),
            SimpleNodeHandler(
                element_type="uml:InteractionOperand",
                node_type="InteractionOperand",
                scalar_attrs=("visibility", "enclosingInteraction", "guard"),
                list_attrs=("covered",),
                rename_map={"covered": "coveredRefs"},
            ),
            SimpleNodeHandler(
                element_type="uml:InstanceValue",
                node_type="InstanceValue",
                scalar_attrs=("instance",),
            ),
            SimpleNodeHandler(
                element_type="uml:Expression",
                node_type="Expression",
                scalar_attrs=("symbol",),
            ),
            SimpleNodeHandler(
                element_type="uml:LiteralBoolean",
                node_type="LiteralBoolean",
                scalar_attrs=("value",),
            ),
            SimpleNodeHandler(
                element_type="uml:LiteralInteger",
                node_type="LiteralInteger",
                scalar_attrs=("value",),
            ),
            SimpleNodeHandler(
                element_type="uml:LiteralReal",
                node_type="LiteralReal",
                scalar_attrs=("value",),
            ),
            SimpleNodeHandler(
                element_type="uml:LiteralString",
                node_type="LiteralString",
                scalar_attrs=("value",),
            ),
            SimpleNodeHandler(
                element_type="uml:LiteralUnlimitedNatural",
                node_type="LiteralUnlimitedNatural",
                scalar_attrs=("value",),
            ),
            AssociationHandler(),
            AssociationHandler("uml:CommunicationPath", "CommunicationPath"),
            DirectedEdgeHandler(
                element_type="uml:ControlFlow",
                edge_type="ControlFlow",
                source_attr="source",
                target_attr="target",
                scalar_attrs=("activity",),
            ),
            DirectedEdgeHandler(
                element_type="uml:ObjectFlow",
                edge_type="ObjectFlow",
                source_attr="source",
                target_attr="target",
                scalar_attrs=("activity",),
            ),
            DirectedEdgeHandler(
                element_type="uml:Transition",
                edge_type="Transition",
                source_attr="source",
                target_attr="target",
                scalar_attrs=("container", "kind"),
            ),
            DirectedEdgeHandler(
                element_type="uml:Message",
                edge_type="Message",
                source_attr="sendEvent",
                target_attr="receiveEvent",
                scalar_attrs=("messageSort", "messageKind", "connector"),
            ),
            GeneralizationHandler(),
            InterfaceRealizationHandler(),
            IncludeHandler(),
            ExtendHandler(),
            DependencyHandler("uml:Dependency", "Dependency"),
            DependencyHandler("uml:Usage", "Usage"),
            InformationFlowHandler(),
        ]

    def parse(self, filepath: str) -> Tuple[IR, ParserRunStats]:
        """Parse a UML XMI file into IR."""
        self._start_run()

        tree = ET.parse(filepath)
        root = tree.getroot()

        model = find_model(root)
        model_id = xmi_id(model) or "model"
        model_name = model.attrib.get("name", "")

        ir = IR(id=model_id, language=self.language, data={"name": model_name})
        ctx = ParseContext(root=root, ir=ir, options=self.options, run_stats=self._stats())

        self._build_indices(ctx)
        self._parse_elements(ctx, model)
        self._create_containment_edges(ctx, model)

        return ctx.ir, self._stats()

    def _build_indices(self, ctx: ParseContext) -> None:
        """Build xmi:id index and parent map."""
        for e in ctx.root.iter():
            _id = xmi_id(e)
            if _id:
                ctx.id_index[_id] = e

        for parent in ctx.root.iter():
            for child in list(parent):
                ctx.parent_map[child] = parent

    def _resolve_handler_key(self, ctx: ParseContext, elem: ET.Element) -> Optional[str]:
        """Resolve a handler key from XML tag and/or xsi:type."""
        tag_name = localname(elem.tag)

        if tag_name == "packagedElement":
            return xsi_type(elem)

        typed = xsi_type(elem)
        if typed:
            return typed

        tag_mapped = ctx.tag_handler_map.get(tag_name)
        if tag_mapped:
            return tag_mapped

        return None

    def _parse_elements(self, ctx: ParseContext, model: ET.Element) -> None:
        """Parse all model descendants using registered handlers."""
        ctx.handler_map = {h.element_type: h for h in self.handlers}
        ctx.tag_handler_map = dict(TAG_TO_CONCEPT)

        if "uml:Model" not in ctx.handler_map:
            ctx.skip_with_warning(
                WarningType.UNKNOWN_NODE_TYPE,
                "No uml:Model handler registered; parser cannot handle model root.",
            )
            return

        for elem in model.iter():
            if is_tool_extension(elem):
                continue

            handler_key = self._resolve_handler_key(ctx, elem)
            if not handler_key:
                continue

            handler = ctx.handler_map.get(handler_key)
            if handler:
                handler.handle(ctx, elem)
                continue

            # Report any typed element without a registered handler.
            elem_id = xmi_id(elem)
            elem_type = xsi_type(elem)
            if elem_type and elem_type not in IGNORED_UNHANDLED_ELEMENTS:
                ctx.skip_with_warning(
                    WarningType.UNKNOWN_NODE_TYPE,
                    f"[UNHANDLED ELEMENT] Type: {elem_type}, ID: {elem_id}, "
                    f"Tag: {localname(elem.tag)}",
                )

    def _create_containment_edges(self, ctx: ParseContext, model: ET.Element) -> None:
        """Create containment edges for packages and their contents."""
        if not ctx.options.include_packages:
            return

        self._walk_containment(ctx, model, current_pkg_id=None)

    def _child_concept_and_id(self, child: ET.Element) -> Optional[Tuple[str, str]]:
        """Resolve concept type and xmi:id for containment-relevant child elements."""
        if is_tool_extension(child):
            return None

        child_tag = localname(child.tag)
        child_id = xmi_id(child)
        if not child_id:
            return None

        if child_tag == "packagedElement":
            child_type = xsi_type(child)
            if not child_type:
                return None
            return (child_type, child_id)

        child_type = xsi_type(child)
        if child_type:
            return (child_type, child_id)

        tag_mapped = TAG_TO_CONCEPT.get(child_tag)
        if tag_mapped:
            return (tag_mapped, child_id)

        return None

    def _walk_containment(self, ctx: ParseContext, container: ET.Element, current_pkg_id: Optional[str]) -> None:
        """Recursively walk containment-relevant children."""
        for child in list(container):
            if is_tool_extension(child):
                continue

            child_tag = localname(child.tag)
            next_pkg_id = current_pkg_id

            if child_tag in CONTAINMENT_CHILD_TAGS:
                child_info = self._child_concept_and_id(child)
                if child_info:
                    child_type, child_id = child_info

                    if child_type == "uml:Package":
                        if current_pkg_id:
                            ctx.add_edge(
                                Edge(
                                    id=f"{current_pkg_id}__contains__{child_id}",
                                    sourceId=current_pkg_id,
                                    targetId=child_id,
                                    type="contains",
                                    data={},
                                )
                            )
                        next_pkg_id = child_id
                    elif current_pkg_id:
                        ctx.add_edge(
                            Edge(
                                id=f"{current_pkg_id}__contains__{child_id}",
                                sourceId=current_pkg_id,
                                targetId=child_id,
                                type="contains",
                                data={"elementType": child_type},
                            )
                        )

            self._walk_containment(ctx, child, current_pkg_id=next_pkg_id)
