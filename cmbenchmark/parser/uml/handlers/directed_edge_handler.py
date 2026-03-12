"""Generic handler for directed UML relationships."""

from __future__ import annotations

from typing import Dict, Mapping, Optional, Sequence, Set
import xml.etree.ElementTree as ET

from cmbenchmark.types.enums import WarningType
from cmbenchmark.types.ir import Edge
from cmbenchmark.parser.uml.handlers.base_handler import ElementHandler


class DirectedEdgeHandler(ElementHandler):
    """Map typed relationship elements to directed IR edges."""

    def __init__(
        self,
        *,
        element_type: str,
        edge_type: str,
        source_attr: str,
        target_attr: str,
        source_child_tag: Optional[str] = None,
        target_child_tag: Optional[str] = None,
        scalar_attrs: Sequence[str] = (),
        list_attrs: Sequence[str] = (),
        rename_map: Optional[Mapping[str, str]] = None,
        include_name: bool = True,
    ):
        self._element_type = element_type
        self._edge_type = edge_type
        self._source_attr = source_attr
        self._target_attr = target_attr
        self._source_child_tag = source_child_tag or source_attr
        self._target_child_tag = target_child_tag or target_attr
        self._scalar_attrs = tuple(scalar_attrs)
        self._list_attrs = tuple(list_attrs)
        self._rename_map = dict(rename_map or {})
        self._include_name = include_name

    @property
    def element_type(self) -> str:
        return self._element_type

    def get_handled_attributes(self) -> Set[str]:
        return {
            "name" if self._include_name else "",
            self._source_attr,
            self._target_attr,
            *self._scalar_attrs,
            *self._list_attrs,
        } - {""}

    def get_handled_children(self) -> Set[str]:
        return {self._source_child_tag, self._target_child_tag}

    def handle(self, ctx, elem: ET.Element) -> None:
        handled_attrs = self.get_handled_attributes()
        handled_children = self.get_handled_children()

        rel_id = self.require_xmi_id(ctx, elem, role="Edge")
        if not rel_id:
            return

        source_refs = self.split_ref_list(
            self.resolve_reference(elem, self._source_attr, self._source_child_tag)
        )
        target_refs = self.split_ref_list(
            self.resolve_reference(elem, self._target_attr, self._target_child_tag)
        )
        if not source_refs or not target_refs:
            ctx.skip_with_warning(
                WarningType.MISSING_EDGE_ENDPOINT,
                f"{self._element_type} edge {rel_id} is missing source/target "
                f"({self._source_attr}={source_refs}, {self._target_attr}={target_refs})",
            )
            return

        edge_data: Dict[str, object] = self.collect_attributes(
            elem,
            scalar_attrs=self._scalar_attrs,
            list_attrs=self._list_attrs,
            rename_map=self._rename_map,
        )
        if self._include_name:
            name = self.read_name(elem)
            if name:
                edge_data["name"] = name

        edge_index = 0
        for source_id in source_refs:
            for target_id in target_refs:
                edge_id = rel_id if edge_index == 0 else f"{rel_id}__{edge_index}"
                edge_index += 1
                ctx.add_edge(
                    Edge(
                        id=edge_id,
                        sourceId=source_id,
                        targetId=target_id,
                        type=self._edge_type,
                        data=edge_data,
                    )
                )

        self.log_unhandled_attributes(ctx, elem, handled_attrs)
        self.log_unhandled_children(ctx, elem, handled_children)
