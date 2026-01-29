"""Ecore parser for converting Ecore models to graph-based IR."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import uuid

try:
    from pyecore.resources import ResourceSet, URI
    from pyecore.ecore import (
        EPackage,
        EClass,
        EReference,
        EAttribute,
        EDataType,
        EEnum,
        EEnumLiteral,
        EOperation,
        EParameter,
    )
except ImportError:
    raise ImportError(
        "pyecore is required for Ecore parsing. Install it with: pip install pyecore"
    )

from cmbenchmark.parser.base import BaseParser, register_parser
from cmbenchmark.types.ir import IR, Node, Edge
from cmbenchmark.types.models import CannotParseError, ParserRunStats


def _generate_id(prefix: str = "") -> str:
    """Generate a unique ID for nodes/edges."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}" if prefix else uuid.uuid4().hex[:8]


def _get_name(obj: Any) -> str:
    """Get name from an Ecore object, with fallback."""
    if hasattr(obj, "name") and obj.name:
        return str(obj.name)
    return f"unnamed_{type(obj).__name__}"


@register_parser
class EcoreParser(BaseParser):
    """Parser for Ecore metamodels."""

    language = "Ecore"

    def parse(self, filepath: str) -> Tuple[IR, ParserRunStats]:
        """
        Parse an Ecore model file into IR.

        Args:
            filepath: Path to the .ecore file

        Returns:
            Tuple of (IR object, ParserRunStats)

        Raises:
            CannotParseError: If the file is not a valid Ecore model
        """
        self._start_run()
        
        path = Path(filepath)
        if not path.exists():
            raise CannotParseError(f"File does not exist: {filepath}")

        try:
            # Load the Ecore model
            rset = ResourceSet()
            resource = rset.get_resource(URI(str(path.absolute())))
            
            if not resource.contents:
                raise CannotParseError("Ecore file appears to be empty")
            
            mm_root = resource.contents[0]
            
            # Verify it's an EPackage
            if not isinstance(mm_root, EPackage):
                raise CannotParseError(
                    f"Root element is not an EPackage: {type(mm_root).__name__}"
                )
            
            # Register the metamodel
            if mm_root.nsURI:
                rset.metamodel_registry[mm_root.nsURI] = mm_root

        except Exception as e:
            if isinstance(e, CannotParseError):
                raise
            raise CannotParseError(f"Failed to load Ecore model: {e}")

        # Create IR
        model_id = _generate_id("model")
        model_name = _get_name(mm_root)
        model_data = {
            "nsURI": mm_root.nsURI or "",
            "nsPrefix": mm_root.nsPrefix or "",
        }

        ir = IR(id=model_id, language=self.language, data=model_data)

        # Track created nodes by their Ecore object for edge creation
        nodes_by_eobject: Dict[Any, Node] = {}
        edge_counter = 0
        created_edges: set = set()  # Track edges to avoid duplicates

        # Process root package first (not included in eAllContents)
        root_node = self._create_package_node(mm_root, mm_root)
        ir.nodes.append(root_node)
        nodes_by_eobject[mm_root] = root_node

        # Process all elements in the model (includes subpackages and classifiers)
        for element in mm_root.eAllContents():
            if isinstance(element, EPackage):
                node = self._create_package_node(element, mm_root)
                ir.nodes.append(node)
                nodes_by_eobject[element] = node
            elif isinstance(element, EClass):
                node = self._create_class_node(element, mm_root)
                ir.nodes.append(node)
                nodes_by_eobject[element] = node
            elif isinstance(element, EEnum):
                node = self._create_enum_node(element, mm_root)
                ir.nodes.append(node)
                nodes_by_eobject[element] = node
            elif isinstance(element, EDataType):
                node = self._create_datatype_node(element, mm_root)
                ir.nodes.append(node)
                nodes_by_eobject[element] = node

        # Process root package's direct contents
        all_elements = [mm_root] + list(mm_root.eAllContents())

        # Create edges for references, containments, and generalizations
        for element in all_elements:
            if isinstance(element, EClass):
                # Process EReferences (both containment and non-containment)
                for ref in element.eReferences:
                    if ref.eType in nodes_by_eobject:
                        edge = self._create_reference_edge(
                            element, ref, nodes_by_eobject, edge_counter
                        )
                        if edge:
                            edge_key = (edge.sourceId, edge.targetId, edge.type)
                            if edge_key not in created_edges:
                                ir.edges.append(edge)
                                created_edges.add(edge_key)
                                edge_counter += 1

                # Process ESuperTypes (generalizations)
                for super_type in element.eSuperTypes:
                    if super_type in nodes_by_eobject:
                        edge = self._create_generalization_edge(
                            element, super_type, nodes_by_eobject, edge_counter
                        )
                        if edge:
                            edge_key = (edge.sourceId, edge.targetId, edge.type)
                            if edge_key not in created_edges:
                                ir.edges.append(edge)
                                created_edges.add(edge_key)
                                edge_counter += 1

            elif isinstance(element, EPackage):
                # Create containment edges for packages
                for subpackage in element.eSubpackages:
                    if subpackage in nodes_by_eobject:
                        edge = self._create_containment_edge(
                            element, subpackage, nodes_by_eobject, edge_counter, "package"
                        )
                        if edge:
                            edge_key = (edge.sourceId, edge.targetId, edge.type)
                            if edge_key not in created_edges:
                                ir.edges.append(edge)
                                created_edges.add(edge_key)
                                edge_counter += 1

                # Create containment edges for classifiers in packages
                for classifier in element.eClassifiers:
                    if classifier in nodes_by_eobject:
                        edge = self._create_containment_edge(
                            element, classifier, nodes_by_eobject, edge_counter, "classifier"
                        )
                        if edge:
                            edge_key = (edge.sourceId, edge.targetId, edge.type)
                            if edge_key not in created_edges:
                                ir.edges.append(edge)
                                created_edges.add(edge_key)
                                edge_counter += 1

        return ir, self._stats()

    def _create_package_node(self, package: EPackage, root: EPackage) -> Node:
        """Create a node for an EPackage."""
        node_id = _generate_id("pkg")
        name = _get_name(package)

        data = {
            "nsURI": package.nsURI or "",
            "nsPrefix": package.nsPrefix or "",
        }

        return Node(id=node_id, type="EPackage", name=name, data=data)

    def _create_class_node(self, eclass: EClass, root: EPackage) -> Node:
        """Create a node for an EClass."""
        node_id = _generate_id("class")
        name = _get_name(eclass)

        # Collect attributes
        attributes = []
        for attr in eclass.eAttributes:
            # Safely get default value - pyecore uses defaultValueLiteral for string representation
            # Use getattr to safely access the attribute which may not exist
            default_value = getattr(attr, 'defaultValueLiteral', None)
            if default_value is not None:
                default_value = str(default_value)
            
            attr_data = {
                "name": _get_name(attr),
                "eType": _get_name(attr.eType) if attr.eType else None,
                "lowerBound": attr.lowerBound,
                "upperBound": attr.upperBound,
                "defaultValue": default_value,
                "required": attr.lowerBound > 0,
                "many": attr.upperBound == -1 or attr.upperBound > 1,
            }
            attributes.append(attr_data)

        # Collect operations
        operations = []
        for op in eclass.eOperations:
            op_data = {
                "name": _get_name(op),
                "eType": _get_name(op.eType) if op.eType else None,
                "parameters": [
                    {
                        "name": _get_name(param),
                        "eType": _get_name(param.eType) if param.eType else None,
                        "lowerBound": param.lowerBound,
                        "upperBound": param.upperBound,
                    }
                    for param in op.eParameters
                ],
            }
            operations.append(op_data)

        data = {
            "abstract": eclass.abstract,
            "interface": eclass.interface,
            "attributes": attributes,
            "operations": operations,
            "superTypes": [_get_name(st) for st in eclass.eSuperTypes],
        }

        return Node(id=node_id, type="EClass", name=name, data=data)

    def _create_enum_node(self, eenum: EEnum, root: EPackage) -> Node:
        """Create a node for an EEnum."""
        node_id = _generate_id("enum")
        name = _get_name(eenum)

        # Collect enum literals
        literals = []
        for literal in eenum.eLiterals:
            literal_data = {
                "name": _get_name(literal),
                "value": literal.value,
                "literal": literal.literal,
            }
            literals.append(literal_data)

        data = {
            "literals": literals,
        }

        return Node(id=node_id, type="EEnum", name=name, data=data)

    def _create_datatype_node(self, datatype: EDataType, root: EPackage) -> Node:
        """Create a node for an EDataType."""
        node_id = _generate_id("datatype")
        name = _get_name(datatype)

        data = {
            "serializable": datatype.serializable,
        }

        return Node(id=node_id, type="EDataType", name=name, data=data)

    def _create_reference_edge(
        self,
        source_class: EClass,
        ref: EReference,
        nodes_by_eobject: Dict[Any, Node],
        edge_counter: int,
    ) -> Optional[Edge]:
        """Create an edge for an EReference."""
        if ref.eType not in nodes_by_eobject:
            return None

        source_node = nodes_by_eobject[source_class]
        target_node = nodes_by_eobject[ref.eType]

        edge_id = _generate_id(f"ref_{edge_counter}")
        ref_name = _get_name(ref)

        data = {
            "name": ref_name,
            "containment": ref.containment,
            "container": ref.container,
            "lowerBound": ref.lowerBound,
            "upperBound": ref.upperBound,
            "required": ref.lowerBound > 0,
            "many": ref.upperBound == -1 or ref.upperBound > 1,
        }

        edge_type = "contains" if ref.containment else "references"

        return Edge(
            id=edge_id,
            sourceId=source_node.id,
            targetId=target_node.id,
            type=edge_type,
            data=data,
        )

    def _create_generalization_edge(
        self,
        subclass: EClass,
        superclass: EClass,
        nodes_by_eobject: Dict[Any, Node],
        edge_counter: int,
    ) -> Optional[Edge]:
        """Create an edge for a generalization relationship."""
        if subclass not in nodes_by_eobject or superclass not in nodes_by_eobject:
            return None

        source_node = nodes_by_eobject[subclass]
        target_node = nodes_by_eobject[superclass]

        edge_id = _generate_id(f"gen_{edge_counter}")

        return Edge(
            id=edge_id,
            sourceId=source_node.id,
            targetId=target_node.id,
            type="generalizes",
            data={},
        )

    def _create_containment_edge(
        self,
        container: EPackage,
        contained: Any,
        nodes_by_eobject: Dict[Any, Node],
        edge_counter: int,
        element_type: str,
    ) -> Optional[Edge]:
        """Create an edge for package containment."""
        if container not in nodes_by_eobject or contained not in nodes_by_eobject:
            return None

        source_node = nodes_by_eobject[container]
        target_node = nodes_by_eobject[contained]

        edge_id = _generate_id(f"contains_{edge_counter}")

        return Edge(
            id=edge_id,
            sourceId=source_node.id,
            targetId=target_node.id,
            type="contains",
            data={"elementType": element_type},
        )

