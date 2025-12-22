"""Handler for uml:Class elements."""

from typing import Any, Dict, List, Optional, Set
import xml.etree.ElementTree as ET

from cmbenchmark.types.ir import Node
from cmbenchmark.parser.uml.handlers.base_handler import ElementHandler
from cmbenchmark.parser.uml.xmi_utils import (
    xmi_id,
    xsi_type,
    is_tool_extension,
    read_multiplicity,
    href_to_type_ref,
    parse_boolean,
    localname,
)


class ClassHandler(ElementHandler):
    """Handler for uml:Class elements."""

    @property
    def element_type(self) -> str:
        return "uml:Class"

    def get_handled_attributes(self) -> Set[str]:
        return {"name", "isAbstract", "visibility"}

    def get_handled_children(self) -> Set[str]:
        return {"ownedAttribute", "ownedOperation", "generalization", "ownedComment"}

    def handle(self, ctx, elem: ET.Element) -> None:
        """Create Class node with attributes and operations."""
        handled_attrs = self.get_handled_attributes()
        handled_children = self.get_handled_children()

        class_id = xmi_id(elem)
        if not class_id:
            return

        name = elem.attrib.get("name", "")
        data: Dict[str, Any] = {}

        # Qualified name
        qn = ctx.qname(class_id)
        if qn:
            data["qualifiedName"] = qn

        # isAbstract attribute
        is_abstract = parse_boolean(elem.attrib.get("isAbstract"))
        if is_abstract is not None:
            data["isAbstract"] = is_abstract

        # Visibility
        if "visibility" in elem.attrib:
            data["visibility"] = elem.attrib["visibility"]

        # Documentation
        doc = self._extract_documentation(elem)
        if doc:
            data["documentation"] = doc

        # Attributes
        attrs = self._parse_owned_attributes(ctx, elem)
        if attrs:
            data["attributes"] = attrs

        # Operations
        ops = self._parse_owned_operations(ctx, elem)
        if ops:
            data["operations"] = ops

        # Create or update node
        if class_id not in ctx.nodes_by_id:
            ctx.add_node(Node(id=class_id, type="Class", name=name, data=data))
        else:
            # Merge data if node already exists
            existing = ctx.nodes_by_id[class_id]
            existing.data.update(
                {k: v for k, v in data.items() if k not in existing.data}
            )

        # Log unhandled attributes and children
        self.log_unhandled_attributes(ctx, elem, handled_attrs)
        self.log_unhandled_children(ctx, elem, handled_children)

    def _extract_documentation(self, elem: ET.Element) -> str:
        """Extract documentation from ownedComment elements."""
        bodies = []
        for comment in elem.findall("./ownedComment"):
            if is_tool_extension(comment):
                continue
            body = comment.attrib.get("body")
            if body:
                bodies.append(body)
        return "\n".join(bodies) if bodies else ""

    def _parse_owned_attributes(
        self, ctx, class_elem: ET.Element
    ) -> List[Dict[str, Any]]:
        """Parse ownedAttribute elements (excluding association ends)."""
        out: List[Dict[str, Any]] = []
        for attr in class_elem.findall("./ownedAttribute"):
            if is_tool_extension(attr):
                continue
            
            # TODO: Remove this?
            # Exclude association ends
            if "association" in attr.attrib or "owningAssociation" in attr.attrib:
                continue

            attr_id = xmi_id(attr)
            if not attr_id:
                continue

            item: Dict[str, Any] = {"id": attr_id}

            attr_name = attr.attrib.get("name")
            if attr_name:
                item["name"] = attr_name

            # Type resolution
            type_ref = self._resolve_property_type(ctx, attr)
            if type_ref:
                item["type"] = type_ref
            type_id = attr.attrib.get("type")
            if type_id:
                item["typeRef"] = type_id

            # Multiplicity
            mult = read_multiplicity(attr)
            item.update(mult)

            # Visibility
            if "visibility" in attr.attrib:
                item["visibility"] = attr.attrib["visibility"]

            # Boolean attributes
            for k in ("isStatic", "isDerived", "isReadOnly"):
                bool_val = parse_boolean(attr.attrib.get(k))
                if bool_val is not None:
                    item[k] = bool_val

            # Default value
            default_value = attr.find("./defaultValue")
            if default_value is not None and "value" in default_value.attrib:
                item["default"] = default_value.attrib["value"]

            out.append(item)

        return out

    def _parse_owned_operations(
        self, ctx, class_elem: ET.Element
    ) -> List[Dict[str, Any]]:
        """Parse ownedOperation elements."""
        out: List[Dict[str, Any]] = []
        for op in class_elem.findall("./ownedOperation"):
            if is_tool_extension(op):
                continue

            op_id = xmi_id(op)
            if not op_id:
                continue

            item: Dict[str, Any] = {"id": op_id}

            op_name = op.attrib.get("name")
            if op_name:
                item["name"] = op_name

            # Visibility
            if "visibility" in op.attrib:
                item["visibility"] = op.attrib["visibility"]

            # Parameters
            params = []
            for param in op.findall("./ownedParameter"):
                if is_tool_extension(param):
                    continue
                param_id = xmi_id(param)
                if param_id:
                    param_data: Dict[str, Any] = {"id": param_id}
                    param_name = param.attrib.get("name")
                    if param_name:
                        param_data["name"] = param_name
                    
                    # Direction
                    if param.attrib.get("direction") == "return":
                        param_data["direction"] = "return"
                    
                    # isUnique attribute
                    is_unique = parse_boolean(param.attrib.get("isUnique"))
                    if is_unique is not None:
                        param_data["isUnique"] = is_unique
                    
                    # Type resolution (check nested type first, then referenced type)
                    type_elem = param.find("./type")
                    if type_elem is not None and "href" in type_elem.attrib:
                        # Nested type with href (e.g., PrimitiveType)
                        param_data["type"] = href_to_type_ref(type_elem.attrib["href"])
                    else:
                        # Referenced type (via type attribute)
                        type_id = param.attrib.get("type")
                        if type_id:
                            # Try to resolve qualified name, fallback to ID
                            type_qname = ctx.qname(type_id)
                            if type_qname:
                                param_data["type"] = type_qname
                            param_data["typeRef"] = type_id
                    
                    params.append(param_data)
            if params:
                item["parameters"] = params

            out.append(item)

        return out

    def _resolve_property_type(self, ctx, prop: ET.Element) -> Optional[str]:
        """Resolve the type reference for a property."""
        # Check for referenced type
        type_id = prop.attrib.get("type")
        if type_id:
            return ctx.qname(type_id) or type_id

        # Check for nested type with href
        type_elem = prop.find("./type")
        if type_elem is not None and "href" in type_elem.attrib:
            return href_to_type_ref(type_elem.attrib["href"])

        return None

