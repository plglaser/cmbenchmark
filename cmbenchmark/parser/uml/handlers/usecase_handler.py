"""Handler for uml:UseCase elements."""

from typing import Any, Dict, List, Optional, Set
import xml.etree.ElementTree as ET

from cmbenchmark.types.ir import Node, Edge
from cmbenchmark.parser.uml.handlers.base_handler import ElementHandler
from cmbenchmark.parser.uml.xmi_utils import (
    xmi_id,
    is_tool_extension,
)


class UseCaseHandler(ElementHandler):
    """Handler for uml:UseCase elements."""

    @property
    def element_type(self) -> str:
        return "uml:UseCase"

    def get_handled_attributes(self) -> Set[str]:
        return {"name", "visibility"}

    def get_handled_children(self) -> Set[str]:
        return {"extensionPoint", "include", "extend", "ownedComment"}

    def handle(self, ctx, elem: ET.Element) -> None:
        """Create UseCase node and handle include/extend relationships."""
        handled_attrs = self.get_handled_attributes()
        handled_children = self.get_handled_children()

        usecase_id = xmi_id(elem)
        if not usecase_id:
            return

        name = elem.attrib.get("name", "")
        data: Dict[str, Any] = {}

        # Visibility
        if "visibility" in elem.attrib:
            data["visibility"] = elem.attrib["visibility"]

        # Documentation
        doc = self.extract_documentation(elem)
        if doc:
            data["documentation"] = doc

        # Extension points
        extension_points = self._parse_extension_points(ctx, elem)
        if extension_points:
            data["extensionPoints"] = extension_points

        # Create UseCase node
        if usecase_id not in ctx.nodes_by_id:
            ctx.add_node(Node(id=usecase_id, type="UseCase", name=name, data=data))
        else:
            # Merge data if node already exists
            existing = ctx.nodes_by_id[usecase_id]
            existing.data.update(
                {k: v for k, v in data.items() if k not in existing.data}
            )

        # Handle include relationships
        self._handle_includes(ctx, elem)

        # Handle extend relationships
        self._handle_extends(ctx, elem)

        # Log unhandled attributes and children
        self.log_unhandled_attributes(ctx, elem, handled_attrs)
        self.log_unhandled_children(ctx, elem, handled_children)

    def _parse_extension_points(
        self, ctx, usecase_elem: ET.Element
    ) -> List[Dict[str, Any]]:
        """Parse extensionPoint elements."""
        out: List[Dict[str, Any]] = []
        for ext_point in usecase_elem.findall("./extensionPoint"):
            if is_tool_extension(ext_point):
                continue

            ext_point_id = xmi_id(ext_point)
            if not ext_point_id:
                continue

            item: Dict[str, Any] = {"id": ext_point_id}

            ext_point_name = ext_point.attrib.get("name")
            if ext_point_name:
                item["name"] = ext_point_name

            # useCase reference (should be the same as the parent UseCase)
            use_case_ref = ext_point.attrib.get("useCase")
            if use_case_ref:
                item["useCaseRef"] = use_case_ref

            out.append(item)

        return out

    def _handle_includes(self, ctx, usecase_elem: ET.Element) -> None:
        """Handle include relationships: includingCase -> addition."""
        usecase_id = xmi_id(usecase_elem)
        if not usecase_id:
            return

        for include_elem in usecase_elem.findall("./include"):
            if is_tool_extension(include_elem):
                continue

            include_id = xmi_id(include_elem)
            including_case = include_elem.attrib.get("includingCase")
            addition = include_elem.attrib.get("addition")

            if not including_case or not addition:
                continue

            # Create edge: includingCase -> addition
            edge_id = f"{include_id}" if include_id else f"{including_case}__includes__{addition}"

            ctx.add_edge(
                Edge(
                    id=edge_id,
                    sourceId=including_case,
                    targetId=addition,
                    type="includes",
                    data={},
                )
            )

    def _handle_extends(self, ctx, usecase_elem: ET.Element) -> None:
        """Handle extend relationships: extension -> extendedCase."""
        usecase_id = xmi_id(usecase_elem)
        if not usecase_id:
            return

        for extend_elem in usecase_elem.findall("./extend"):
            if is_tool_extension(extend_elem):
                continue

            extend_id = xmi_id(extend_elem)
            extension = extend_elem.attrib.get("extension")
            extended_case = extend_elem.attrib.get("extendedCase")
            extension_location = extend_elem.attrib.get("extensionLocation")

            if not extension or not extended_case:
                continue

            # Build edge data
            edge_data: Dict[str, Any] = {}
            
            # Add extensionLocation if present
            if extension_location:
                edge_data["extensionLocation"] = extension_location
                
                # Try to resolve extension point name if extensionLocation is provided
                ext_point_elem = ctx.elem(extension_location)
                if ext_point_elem is not None:
                    ext_point_name = ext_point_elem.attrib.get("name")
                    if ext_point_name:
                        edge_data["extensionPoint"] = ext_point_name

            # Create edge: extension -> extendedCase
            edge_id = f"{extend_id}" if extend_id else f"{extension}__extends__{extended_case}"

            ctx.add_edge(
                Edge(
                    id=edge_id,
                    sourceId=extension,
                    targetId=extended_case,
                    type="extends",
                    data=edge_data,
                )
            )

