"""Handler for uml:AssociationClass elements."""

from __future__ import annotations

from typing import Any, Dict, List, Set
import xml.etree.ElementTree as ET

from cmbenchmark.types.enums import WarningType
from cmbenchmark.parser.uml.handlers.base_handler import ElementHandler
from cmbenchmark.parser.uml.xmi_utils import xsi_type, is_tool_extension, read_multiplicity


class AssociationClassHandler(ElementHandler):
    """Map AssociationClass concepts to IR nodes with class-like payload."""

    @property
    def element_type(self) -> str:
        return "uml:AssociationClass"

    def get_handled_attributes(self) -> Set[str]:
        return {
            "name",
            "visibility",
            "isAbstract",
            "isLeaf",
            "memberEnd",
            "navigableOwnedEnd",
        }

    def get_handled_children(self) -> Set[str]:
        return {"ownedAttribute", "ownedOperation", "ownedComment", "ownedEnd"}

    def handle(self, ctx, elem: ET.Element) -> None:
        handled_attrs = self.get_handled_attributes()
        handled_children = self.get_handled_children()

        assoc_class_id = self.require_xmi_id(ctx, elem, role="Node")
        if not assoc_class_id:
            return

        data: Dict[str, Any] = self.collect_attributes(
            elem,
            scalar_attrs=("visibility",),
            boolean_attrs=("isAbstract", "isLeaf"),
            list_attrs=("memberEnd", "navigableOwnedEnd"),
        )

        doc = self.extract_documentation(elem)
        if doc:
            data["documentation"] = doc

        attrs = self._parse_owned_attributes(ctx, elem)
        if attrs:
            data["attributes"] = attrs

        ops = self.parse_owned_operations(ctx, elem)
        if ops:
            data["operations"] = ops

        self.upsert_node(
            ctx,
            node_id=assoc_class_id,
            node_type="AssociationClass",
            name=self.read_name(elem),
            data=data,
        )

        self.log_unhandled_attributes(ctx, elem, handled_attrs)
        self.log_unhandled_children(ctx, elem, handled_children)

    def _parse_owned_attributes(self, ctx, owner_elem: ET.Element) -> List[Dict[str, Any]]:
        """Parse class-owned attributes and skip association-end style attributes."""
        out: List[Dict[str, Any]] = []
        for attr in owner_elem.findall("./ownedAttribute"):
            if is_tool_extension(attr):
                continue

            if "association" in attr.attrib or "owningAssociation" in attr.attrib:
                continue

            attr_id = self.require_xmi_id(ctx, attr, role="AssociationClass ownedAttribute")
            if not attr_id:
                continue

            item: Dict[str, Any] = {"id": attr_id}
            attr_name = self.read_name(attr)
            if attr_name:
                item["name"] = attr_name

            type_id = attr.attrib.get("type")
            if type_id:
                item["typeRef"] = type_id
            else:
                resolved_type = self.resolve_property_type(ctx, attr)
                if resolved_type:
                    item["type"] = resolved_type
                else:
                    attr_type = xsi_type(attr) or "ownedAttribute"
                    ctx.warn(
                        WarningType.INVALID_TYPE_REFERENCE,
                        f"Attribute {attr_id} ({attr_type}) has no resolvable type reference.",
                    )

            item.update(read_multiplicity(attr))
            item.update(
                self.collect_attributes(
                    attr,
                    scalar_attrs=("visibility",),
                    boolean_attrs=(
                        "isStatic",
                        "isDerived",
                        "isReadOnly",
                        "isUnique",
                        "isOrdered",
                        "isID",
                        "isLeaf",
                    ),
                )
            )

            aggregation = attr.attrib.get("aggregation")
            if aggregation and aggregation != "none":
                item["aggregation"] = aggregation

            default_value = attr.find("./defaultValue")
            if default_value is not None and "value" in default_value.attrib:
                item["default"] = default_value.attrib["value"]

            out.append(item)

        return out
