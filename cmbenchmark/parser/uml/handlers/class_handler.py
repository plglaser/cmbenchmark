"""Handler for uml:Class elements."""

from typing import Any, Dict, List, Optional, Set
import xml.etree.ElementTree as ET

from cmbenchmark.types.ir import Node
from cmbenchmark.parser.uml.handlers.base_handler import ElementHandler
from cmbenchmark.parser.uml.xmi_utils import (
    xmi_id,
    is_tool_extension,
    read_multiplicity,
    parse_boolean,
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

        # isAbstract attribute
        is_abstract = parse_boolean(elem.attrib.get("isAbstract"))
        if is_abstract is not None:
            data["isAbstract"] = is_abstract

        # Visibility
        if "visibility" in elem.attrib:
            data["visibility"] = elem.attrib["visibility"]

        # Documentation
        doc = self.extract_documentation(elem)
        if doc:
            data["documentation"] = doc

        # Attributes
        attrs = self._parse_owned_attributes(ctx, elem)
        if attrs:
            data["attributes"] = attrs

        # Operations
        ops = self.parse_owned_operations(ctx, elem)
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
            type_ref = self.resolve_property_type(ctx, attr)
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

