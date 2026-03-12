"""Handler for uml:InformationFlow elements."""

from __future__ import annotations

from typing import Set
import xml.etree.ElementTree as ET

from cmbenchmark.types.enums import WarningType
from cmbenchmark.types.ir import Edge
from cmbenchmark.parser.uml.handlers.base_handler import ElementHandler


class InformationFlowHandler(ElementHandler):
    """Map InformationFlow concepts to directed IR edges."""

    @property
    def element_type(self) -> str:
        return "uml:InformationFlow"

    def get_handled_attributes(self) -> Set[str]:
        return {"name", "informationSource", "informationTarget"}

    def get_handled_children(self) -> Set[str]:
        return set()

    def handle(self, ctx, elem: ET.Element) -> None:
        handled_attrs = self.get_handled_attributes()
        handled_children = self.get_handled_children()

        flow_id = self.require_xmi_id(ctx, elem, role="Edge")
        if not flow_id:
            return

        sources = self.split_ref_list(elem.attrib.get("informationSource"))
        targets = self.split_ref_list(elem.attrib.get("informationTarget"))
        if not sources or not targets:
            ctx.skip_with_warning(
                WarningType.MISSING_EDGE_ENDPOINT,
                f"uml:InformationFlow edge {flow_id} is missing source/target "
                f"(informationSource={sources}, informationTarget={targets})",
            )
            return

        edge_index = 0
        for source_id in sources:
            for target_id in targets:
                edge_id = flow_id if edge_index == 0 else f"{flow_id}__{edge_index}"
                edge_index += 1
                edge_data = {}
                flow_name = self.read_name(elem)
                if flow_name:
                    edge_data["name"] = flow_name
                ctx.add_edge(
                    Edge(
                        id=edge_id,
                        sourceId=source_id,
                        targetId=target_id,
                        type="InformationFlow",
                        data=edge_data,
                    )
                )

        self.log_unhandled_attributes(ctx, elem, handled_attrs)
        self.log_unhandled_children(ctx, elem, handled_children)
