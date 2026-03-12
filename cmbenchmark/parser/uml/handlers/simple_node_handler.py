"""Generic handler for UML concepts mapped to simple IR nodes."""

from __future__ import annotations

from typing import Dict, Mapping, Optional, Sequence, Set
import xml.etree.ElementTree as ET

from cmbenchmark.parser.uml.handlers.base_handler import ElementHandler


class SimpleNodeHandler(ElementHandler):
    """Configurable node handler for concepts represented as simple nodes."""

    def __init__(
        self,
        *,
        element_type: str,
        node_type: str,
        scalar_attrs: Sequence[str] = (),
        boolean_attrs: Sequence[str] = (),
        list_attrs: Sequence[str] = (),
        rename_map: Optional[Mapping[str, str]] = None,
        include_documentation: bool = True,
        log_unhandled: bool = True,
    ):
        self._element_type = element_type
        self._node_type = node_type
        self._scalar_attrs = tuple(scalar_attrs)
        self._boolean_attrs = tuple(boolean_attrs)
        self._list_attrs = tuple(list_attrs)
        self._rename_map = dict(rename_map or {})
        self._include_documentation = include_documentation
        self._log_unhandled = log_unhandled

    @property
    def element_type(self) -> str:
        return self._element_type

    def get_handled_attributes(self) -> Set[str]:
        return {
            "name",
            *self._scalar_attrs,
            *self._boolean_attrs,
            *self._list_attrs,
        }

    def get_handled_children(self) -> Set[str]:
        handled = set()
        if self._include_documentation:
            handled.add("ownedComment")
        return handled

    def handle(self, ctx, elem: ET.Element) -> None:
        handled_attrs = self.get_handled_attributes()
        handled_children = self.get_handled_children()

        node_id = self.require_xmi_id(ctx, elem, role="Node")
        if not node_id:
            return

        data: Dict[str, object] = self.collect_attributes(
            elem,
            scalar_attrs=self._scalar_attrs,
            boolean_attrs=self._boolean_attrs,
            list_attrs=self._list_attrs,
            rename_map=self._rename_map,
        )

        if self._include_documentation:
            doc = self.extract_documentation(elem)
            if doc:
                data["documentation"] = doc

        self.upsert_node(
            ctx,
            node_id=node_id,
            node_type=self._node_type,
            name=self.read_name(elem),
            data=data,
        )

        if self._log_unhandled:
            self.log_unhandled_attributes(ctx, elem, handled_attrs)
            self.log_unhandled_children(ctx, elem, handled_children)
