"""Handler for uml:Association elements."""

from typing import Any, Dict, List, Optional, Set
import xml.etree.ElementTree as ET

from cmbenchmark.types.ir import Edge
from cmbenchmark.parser.uml.handlers.base_handler import ElementHandler
from cmbenchmark.parser.uml.xmi_utils import (
    xmi_id,
    xsi_type,
    is_tool_extension,
    read_multiplicity,
    localname,
)


class AssociationHandler(ElementHandler):
    """Handler for uml:Association elements.
    
    This handler can be extended for other association types (e.g., from UseCase diagrams).
    """

    @property
    def element_type(self) -> str:
        return "uml:Association"

    def get_handled_attributes(self) -> Set[str]:
        return {"name", "memberEnd", "navigableOwnedEnd"}

    def get_handled_children(self) -> Set[str]:
        return {"ownedEnd"}

    def handle(self, ctx, elem: ET.Element) -> None:
        """Create Association edge from ownedEnd elements."""
        handled_attrs = self.get_handled_attributes()
        handled_children = self.get_handled_children()

        assoc_id = xmi_id(elem)
        if not assoc_id:
            return

        # Parse association ends
        ends = []
        for end in elem.findall("./ownedEnd"):
            if is_tool_extension(end):
                continue
            end_data = self._parse_association_end(ctx, end, elem)
            if end_data:
                ends.append(end_data)

        if len(ends) < 2:
            # Print incomplete association
            print(f"[UNHANDLED ELEMENT] Association {assoc_id} has fewer than 2 ends")
            return

        end1, end2 = ends[0], ends[1]

        # Determine source and target (use first end as source, second as target)
        # This can be overridden in subclasses for different association types
        source_id = end1["typeId"]
        target_id = end2["typeId"]

        # Build edge data
        data: Dict[str, Any] = {
            "end1": {
                "id": end1["id"],
                "name": end1.get("name"),
                "lower": end1.get("lower"),
                "upper": end1.get("upper"),
            },
            "end2": {
                "id": end2["id"],
                "name": end2.get("name"),
                "lower": end2.get("lower"),
                "upper": end2.get("upper"),
            },
        }

        # Remove None values
        for end_key in ["end1", "end2"]:
            data[end_key] = {k: v for k, v in data[end_key].items() if v is not None}

        assoc_name = elem.attrib.get("name")
        if assoc_name:
            data["name"] = assoc_name

        # Create edge
        ctx.add_edge(
            Edge(
                id=assoc_id,
                sourceId=source_id,
                targetId=target_id,
                type="Association",
                data=data,
            )
        )

        # Log unhandled attributes and children
        self.log_unhandled_attributes(ctx, elem, handled_attrs)
        self.log_unhandled_children(ctx, elem, handled_children)

    def _parse_association_end(
        self, ctx, end: ET.Element, assoc: ET.Element
    ) -> Optional[Dict[str, Any]]:
        """Parse an association end and return its data."""
        end_id = xmi_id(end)
        if not end_id:
            return None

        type_id = end.attrib.get("type")
        if not type_id:
            return None

        end_data: Dict[str, Any] = {
            "id": end_id,
            "typeId": type_id,
        }

        # Name
        name = end.attrib.get("name")
        if name:
            end_data["name"] = name

        # Multiplicity
        mult = read_multiplicity(end)
        end_data.update(mult)

        # Aggregation
        aggregation = end.attrib.get("aggregation")
        if aggregation and aggregation != "none":
            end_data["aggregation"] = aggregation

        return end_data

