"""Handler for uml:Model elements."""

from typing import Any, Dict, Set
import xml.etree.ElementTree as ET

from cmbenchmark.parser.uml.handlers.base_handler import ElementHandler
from cmbenchmark.parser.uml.xmi_utils import (
    xmi_id,
    is_tool_extension,
    XMI_NS,
)


class ModelHandler(ElementHandler):
    """Handler for uml:Model root elements."""

    @property
    def element_type(self) -> str:
        return "uml:Model"

    def get_handled_attributes(self) -> Set[str]:
        return {"name", "visibility"}

    def get_handled_children(self) -> Set[str]:
        return {"packageImport", "ownedComment", "packagedElement"}

    def handle(self, ctx, elem: ET.Element) -> None:
        """Extract model metadata and store in IR data."""
        handled_attrs = self.get_handled_attributes()
        handled_children = self.get_handled_children()

        model_id = xmi_id(elem) or "model"
        model_name = elem.attrib.get("name", "")

        # Extract XMI version and UML namespace from root
        root = ctx.root
        xmi_version = root.attrib.get(f"{{{XMI_NS}}}version")
        
        # Extract UML namespace from xmlns:uml attribute
        uml_ns = None
        for ns, uri in root.attrib.items():
            if ns.startswith("xmlns:uml"):
                uml_ns = uri
                break

        # Collect package imports
        imports = []
        for pi in elem.findall("./packageImport"):
            if is_tool_extension(pi):
                continue
            imported = pi.find("./importedPackage")
            if imported is not None and "href" in imported.attrib:
                imports.append(imported.attrib["href"])

        # Update IR data
        ctx.ir.data.update({
            "modelId": model_id,
            "name": model_name,
        })
        
        # Visibility
        if "visibility" in elem.attrib:
            ctx.ir.data["visibility"] = elem.attrib["visibility"]
        if xmi_version:
            ctx.ir.data["xmi_version"] = xmi_version
        if uml_ns:
            ctx.ir.data["uml_namespace"] = uml_ns
        if imports:
            ctx.ir.data["imports"] = imports

        # Log unhandled attributes and children
        self.log_unhandled_attributes(ctx, elem, handled_attrs)
        self.log_unhandled_children(ctx, elem, handled_children)

