"""Handlers for uml:Dependency-like elements."""

from typing import List
import xml.etree.ElementTree as ET

from cmbenchmark.types.enums import WarningType
from cmbenchmark.types.ir import Edge
from cmbenchmark.parser.uml.handlers.base_handler import ElementHandler


class DependencyHandler(ElementHandler):
    """Handler for dependency relations (Dependency, Usage)."""

    def __init__(self, element_type: str, edge_type: str):
        self._element_type = element_type
        self._edge_type = edge_type

    @property
    def element_type(self) -> str:
        return self._element_type

    def handle(self, ctx, elem: ET.Element) -> None:
        handled_attrs = self.get_handled_attributes()
        handled_children = self.get_handled_children()

        dep_id = self.require_xmi_id(ctx, elem, role="Edge")
        if not dep_id:
            return

        clients = self.split_ref_list(elem.attrib.get("client"))
        suppliers = self.split_ref_list(elem.attrib.get("supplier"))
        if not clients or not suppliers:
            ctx.skip_with_warning(
                WarningType.MISSING_EDGE_ENDPOINT,
                f"{self._element_type} edge {dep_id} is missing client/supplier "
                f"(client={clients}, supplier={suppliers})",
            )
            return

        edge_index = 0
        for client_id in clients:
            for supplier_id in suppliers:
                edge_id = dep_id if edge_index == 0 else f"{dep_id}__{edge_index}"
                edge_index += 1
                edge_data = {}
                if "name" in elem.attrib:
                    edge_data["name"] = elem.attrib["name"]
                ctx.add_edge(
                    Edge(
                        id=edge_id,
                        sourceId=client_id,
                        targetId=supplier_id,
                        type=self._edge_type,
                        data=edge_data,
                    )
                )

        self.log_unhandled_attributes(ctx, elem, handled_attrs)
        self.log_unhandled_children(ctx, elem, handled_children)
