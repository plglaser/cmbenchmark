"""ArchiMate model parser."""

from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Tuple

from cmbenchmark.parser.base import BaseParser, register_parser
from cmbenchmark.types.models import LossReport, CannotParseError
from cmbenchmark.types.ir import IR, Node, Edge
from cmbenchmark.types.loss_tracking import LossTracker, LossLocation, LossCategory
from cmbenchmark.parser.archimate_types import (
    ALL_ELEMENT_TYPES,
    ALL_RELATIONSHIP_TYPES,
    TYPE_RENAMES
)


@register_parser
class ArchiMateArchiParser(BaseParser):
    """Parser for ArchiMate models."""

    language = "ArchiMate-Archi"

    def _normalize_type(self, type_str: str) -> str:
        """
        Normalize type string by removing namespace prefix, normalizing relationship names,
        and renaming deprecated types.
        
        Args:
            type_str: Type string (e.g., "archimate:ApplicationComponent" or "archimate:UsedByRelationship")
            
        Returns:
            Normalized type string (e.g., "ApplicationComponent" or "Serving")
        """
        if not type_str:
            return ""
        
        # Step 1: Remove "archimate:" prefix if present
        if type_str.startswith("archimate:"):
            type_str = type_str[len("archimate:"):]
        
        # Step 2: Remove "Relationship" suffix if present
        if type_str.endswith("Relationship"):
            base_name = type_str[:-len("Relationship")]
            # Capitalize first letter if needed
            if base_name:
                type_str = base_name[0].upper() + base_name[1:] if len(base_name) > 1 else base_name.upper()
        
        # Step 3: Rename deprecated types
        type_str = TYPE_RENAMES.get(type_str, type_str)
        
        return type_str

    def parse(self, filepath: str) -> Tuple[IR, LossReport]:
        """
        Parse a ArchiMate model file into IR.
        
        Raises:
            CannotParseError: If the file is not a valid Archi .archimate model file.
        """
        try:
            # Parse only the root element first to check format
            context = ET.iterparse(filepath, events=("start",))
            event, root = next(context)
            
            # Check tag name and namespace
            if not root.tag.endswith("model"):
                raise CannotParseError(f"Root element is not 'model': {root.tag}")
            
            # Check Archi namespace and key attributes
            ns_archimate = root.attrib.get("xmlns:archimate")
            if not (ns_archimate and "archimatetool.com/archimate" in ns_archimate):
                # Fallback: sometimes namespace declared differently or stripped
                # Check for attribute patterns typical of Archi models
                if not ("archimate" in root.tag and "version" in root.attrib):
                    raise CannotParseError("File does not appear to be an ArchiMate model (missing namespace or version)")
        except ET.ParseError as e:
            raise CannotParseError(f"Invalid XML format: {e}")
        except StopIteration:
            raise CannotParseError("File appears to be empty or invalid XML")
        except Exception as e:
            if isinstance(e, CannotParseError):
                raise
            raise CannotParseError(f"Cannot parse file: {e}")
        
        # Now parse the full file
        tree = ET.parse(filepath)
        root = tree.getroot()
        model_id = root.attrib.get("id", "")
        model_name = root.attrib.get("name", "")
        model_version = root.attrib.get("version", "")
        model_data = { 
            "modelId": model_id,
            "name": model_name, 
            "version": model_version,
            "source_path": str(filepath)
        }

        nodes = []
        edges = []
        loss_tracker = LossTracker()

        # traverse <folder> elements
        for folder in root.findall("folder"):
            folder_type = folder.attrib.get("type", "")

            if folder_type == "diagrams":
                # Track skipped diagrams folder
                folder_id = folder.attrib.get("id", "")
                folder_name = folder.attrib.get("name", "")
                
                loss_tracker.record(
                    LossCategory.SKIPPED_SECTION,
                    "Views/diagrams not mapped to IR yet",
                    loc=LossLocation(
                        folder_type="diagrams",
                        tag="folder",
                        element_id=folder_id,
                        extra={"folder_name": folder_name} if folder_name else {}
                    )
                )
                continue  # skip Views folder for now
            
            # Each <element> is either an ArchiMate element or a relationship
            for element in folder.findall("element"):
                elem_id = element.attrib.get("id")
                if not elem_id:
                    continue
                
                xsi_type = element.attrib.get("{http://www.w3.org/2001/XMLSchema-instance}type", "")
                
                # Normalize type (remove archimate: prefix, rename deprecated types, normalize relationship names)
                normalized_type = self._normalize_type(xsi_type)
                
                # Extract element data (excluding id, type attributes, and source/target for edges)
                elem_data = {k: v for k, v in element.attrib.items() if not k.endswith("type") and k != "id"}

                # Optional documentation
                doc_elem = element.find("documentation")
                if doc_elem is not None and doc_elem.text:
                    elem_data["documentation"] = doc_elem.text.strip()
                
                if folder_type == "relations" or normalized_type in ALL_RELATIONSHIP_TYPES or xsi_type.endswith("Relationship"):
                    source = element.attrib.get("source")
                    target = element.attrib.get("target")
                    
                    # Remove source and target from elem_data since they're already in sourceId/targetId
                    edge_data = {k: v for k, v in elem_data.items() if k not in ("source", "target")}
                    edges.append(Edge(
                        id=elem_id,
                        sourceId=source,
                        targetId=target,
                        type=normalized_type,
                        data=edge_data
                    ))
                else:
                    # Extract name from elem_data and move it outside
                    node_name = elem_data.pop("name", "")
                    nodes.append(Node(
                        id=elem_id,
                        type=normalized_type,
                        name=node_name,
                        data=elem_data
                    ))
        
        # Parse <purpose> element and add to model data
        purpose_elem = root.find("purpose")
        if purpose_elem is not None and purpose_elem.text:
            model_data["documentation"] = purpose_elem.text.strip()
               
        ir = IR(
            id=model_id,
            language=self.language,
            data=model_data,
            nodes=nodes,
            edges=edges,
        )
        
        loss_report = LossReport(
            parser=self.parser_id,
            loss=loss_tracker,
            source_relpath=str(Path(filepath).name),
            schema_version=model_version,
        )
        
        return ir, loss_report
