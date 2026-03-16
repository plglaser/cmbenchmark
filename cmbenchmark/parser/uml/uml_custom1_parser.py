"""Parser for custom UML assignment-style model files.

The expected input format is assignment-based text, for example:

class_attributes = {"ClassA": ["name:string"]}
associations = [{"class1": "ClassA", "class2": "ClassB"}]
inheritance = [{"parent_class": "Base", "child_classes": ["ClassA"]}]
compositions = [{"parent_class": "Whole", "child_class": "Part"}]
enums = {"Status": ["Open", "Closed"]}
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from cmbenchmark.parser.base import BaseParser, register_parser
from cmbenchmark.types.enums import WarningType
from cmbenchmark.types.exceptions import CannotParseError
from cmbenchmark.types.ir import Edge, IR, Node
from cmbenchmark.types.parsing import ParserRunStats


SUPPORTED_BLOCKS = {
    "class_attributes",
    "associations",
    "inheritance",
    "compositions",
    "enums",
}


def _norm_name(value: str) -> str:
    return value.strip().lower()


def _class_id(norm_name: str) -> str:
    return f"class::{norm_name}"


def _enum_id(norm_name: str) -> str:
    return f"enum::{norm_name}"


@dataclass
class _ClassEntry:
    norm_name: str
    display_name: str
    defined_in_class_attributes: bool = False
    attributes: List[Dict[str, Any]] = field(default_factory=list)


@register_parser
class UMLCustom1Parser(BaseParser):
    """Parser for the custom UML assignment format."""

    language = "UML-custom1"

    def parse(self, filepath: str) -> Tuple[IR, ParserRunStats]:
        self._start_run()
        model_path = Path(filepath)
        source = model_path.read_text(encoding="utf-8")
        first_nonempty = self._first_nonempty_line(source)

        if first_nonempty.startswith("<"):
            raise CannotParseError("File appears to be XML, not UML-custom1 assignment format.")

        blocks = self._parse_assignment_blocks(source, filepath)
        if not blocks:
            raise CannotParseError("No supported top-level blocks found for UML-custom1 format.")

        class_attributes = self._as_dict(blocks.get("class_attributes"), "class_attributes")
        associations = self._as_list(blocks.get("associations"), "associations")
        inheritance = self._as_list(blocks.get("inheritance"), "inheritance")
        compositions = self._as_list(blocks.get("compositions"), "compositions")
        enums = self._as_dict(blocks.get("enums"), "enums")

        class_entries = self._collect_classes(
            class_attributes=class_attributes,
            associations=associations,
            inheritance=inheritance,
            compositions=compositions,
            enums=enums,
        )

        ir = IR(
            id=model_path.stem or model_path.name or "model",
            language=self.language,
            data={
                "name": model_path.stem or model_path.name,
                "sourceFormat": "uml-custom1",
                "blocksPresent": sorted(k for k in blocks.keys() if k in SUPPORTED_BLOCKS),
            },
        )

        for entry in class_entries.values():
            node_data: Dict[str, Any] = {}
            if entry.attributes:
                node_data["attributes"] = entry.attributes
            if not entry.defined_in_class_attributes:
                node_data["implicit"] = True
            ir.nodes.append(
                Node(
                    id=_class_id(entry.norm_name),
                    type="Class",
                    name=entry.display_name,
                    data=node_data,
                )
            )

        self._append_enum_nodes(ir, enums)
        self._append_association_edges(ir, associations, class_entries)
        self._append_generalization_edges(ir, inheritance, class_entries)
        self._append_composition_edges(ir, compositions, class_entries)

        return ir, self._stats()

    def _first_nonempty_line(self, text: str) -> str:
        for line in text.splitlines():
            stripped = line.strip()
            if stripped:
                return stripped
        return ""

    def _parse_assignment_blocks(self, source: str, filepath: str) -> Dict[str, Any]:
        try:
            module = ast.parse(source, filename=filepath)
        except SyntaxError as exc:
            raise CannotParseError(f"Invalid UML-custom1 assignment syntax: {exc}") from exc

        blocks: Dict[str, Any] = {}
        for stmt in module.body:
            if not isinstance(stmt, ast.Assign):
                continue
            if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
                continue
            block_name = stmt.targets[0].id
            if block_name not in SUPPORTED_BLOCKS:
                continue
            try:
                blocks[block_name] = ast.literal_eval(stmt.value)
            except Exception:
                self.warn(
                    WarningType.OTHER,
                    f"Could not parse block '{block_name}' as a Python literal; block ignored.",
                )
        return blocks

    def _as_dict(self, value: Any, block_name: str) -> Dict[str, Any]:
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        self.warn(WarningType.OTHER, f"Block '{block_name}' is not a dict; treating as empty.")
        return {}

    def _as_list(self, value: Any, block_name: str) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        self.warn(WarningType.OTHER, f"Block '{block_name}' is not a list; treating as empty.")
        return []

    def _collect_classes(
        self,
        *,
        class_attributes: Dict[str, Any],
        associations: List[Any],
        inheritance: List[Any],
        compositions: List[Any],
        enums: Dict[str, Any],
    ) -> Dict[str, _ClassEntry]:
        classes: Dict[str, _ClassEntry] = {}

        for class_name, attrs in class_attributes.items():
            if not isinstance(class_name, str):
                continue
            entry = self._ensure_class(classes, class_name, preferred_from_definition=True)
            entry.defined_in_class_attributes = True
            parsed_attrs = self._parse_attribute_list(attrs, enums=enums)
            if parsed_attrs:
                entry.attributes.extend(parsed_attrs)

        for assoc in associations:
            if not isinstance(assoc, dict):
                continue
            self._ensure_class(classes, assoc.get("class1", ""))
            self._ensure_class(classes, assoc.get("class2", ""))

        for inh in inheritance:
            if not isinstance(inh, dict):
                continue
            self._ensure_class(classes, inh.get("parent_class", ""))
            child_classes = inh.get("child_classes", [])
            if isinstance(child_classes, list):
                for child in child_classes:
                    self._ensure_class(classes, child)

        for comp in compositions:
            if not isinstance(comp, dict):
                continue
            self._ensure_class(classes, comp.get("parent_class", ""))
            self._ensure_class(classes, comp.get("child_class", ""))

        return classes

    def _ensure_class(
        self,
        classes: Dict[str, _ClassEntry],
        raw_name: Any,
        *,
        preferred_from_definition: bool = False,
    ) -> Optional[_ClassEntry]:
        if not isinstance(raw_name, str):
            return None
        name = raw_name.strip()
        if not name:
            return None
        norm = _norm_name(name)
        existing = classes.get(norm)
        if existing is None:
            entry = _ClassEntry(norm_name=norm, display_name=name)
            classes[norm] = entry
            return entry
        if preferred_from_definition and not existing.defined_in_class_attributes:
            existing.display_name = name
        return existing

    def _parse_attribute_list(self, attrs: Any, *, enums: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not isinstance(attrs, list):
            return []
        out: List[Dict[str, Any]] = []
        for raw_attr in attrs:
            if not isinstance(raw_attr, str):
                continue
            token = raw_attr.strip()
            if not token:
                continue

            attr_name = token
            type_name: Optional[str] = None
            if ":" in token:
                attr_name, type_name = token.split(":", 1)
                attr_name = attr_name.strip()
                type_name = type_name.strip() or None

            if not attr_name:
                continue

            parsed: Dict[str, Any] = {"name": attr_name}
            if type_name:
                parsed["type"] = type_name
                if _norm_name(type_name) == "enumeration":
                    enum_name = self._resolve_enum_name(attr_name, enums.keys())
                    if enum_name:
                        parsed["enum"] = enum_name
            out.append(parsed)
        return out

    def _resolve_enum_name(self, attr_name: str, enum_names: Iterable[str]) -> Optional[str]:
        names = [name for name in enum_names if isinstance(name, str) and name.strip()]
        if not names:
            return None

        attr_norm = _norm_name(attr_name)
        if not attr_norm:
            return names[0] if len(names) == 1 else None

        scored: List[Tuple[int, str]] = []
        for enum_name in names:
            enum_norm = _norm_name(enum_name)
            score = 0
            if enum_norm == attr_norm:
                score = 100
            elif enum_norm == f"{attr_norm}type":
                score = 90
            elif enum_norm.endswith(attr_norm) or enum_norm.startswith(attr_norm):
                score = 50
            elif attr_norm in enum_norm:
                score = 25
            if score > 0:
                scored.append((score, enum_name))

        if scored:
            scored.sort(key=lambda item: item[0], reverse=True)
            top_score = scored[0][0]
            top_names = [name for score, name in scored if score == top_score]
            if len(top_names) == 1:
                return top_names[0]

        if len(names) == 1:
            return names[0]
        return None

    def _append_enum_nodes(self, ir: IR, enums: Dict[str, Any]) -> None:
        for enum_name, literals_raw in enums.items():
            if not isinstance(enum_name, str):
                continue
            enum_norm = _norm_name(enum_name)
            if not enum_norm:
                continue

            literals: List[str] = []
            if isinstance(literals_raw, list):
                literals = [str(item) for item in literals_raw if isinstance(item, str)]

            ir.nodes.append(
                Node(
                    id=_enum_id(enum_norm),
                    type="Enumeration",
                    name=enum_name,
                    data={"literals": literals},
                )
            )

            for idx, literal in enumerate(literals):
                literal_id = f"{_enum_id(enum_norm)}::literal::{idx}"
                ir.nodes.append(
                    Node(
                        id=literal_id,
                        type="EnumerationLiteral",
                        name=literal,
                        data={"enum": enum_name},
                    )
                )
                ir.edges.append(
                    Edge(
                        id=f"{_enum_id(enum_norm)}::contains::{idx}",
                        sourceId=_enum_id(enum_norm),
                        targetId=literal_id,
                        type="contains",
                        data={},
                    )
                )

    def _append_association_edges(
        self,
        ir: IR,
        associations: List[Any],
        classes: Dict[str, _ClassEntry],
    ) -> None:
        assoc_index = 0
        for assoc in associations:
            if not isinstance(assoc, dict):
                continue
            class1 = self._class_entry_from_raw(classes, assoc.get("class1"))
            class2 = self._class_entry_from_raw(classes, assoc.get("class2"))
            if class1 is None or class2 is None:
                self.skip_with_warning(
                    WarningType.MISSING_EDGE_ENDPOINT,
                    "Skipping association with missing class1/class2.",
                )
                continue

            end1 = {
                "class": class1.display_name,
                "role": str(assoc.get("role_class1") or ""),
                "cardinality": str(assoc.get("cardinality_class1") or ""),
            }
            end2 = {
                "class": class2.display_name,
                "role": str(assoc.get("role_class2") or ""),
                "cardinality": str(assoc.get("cardinality_class2") or ""),
            }

            edge_data: Dict[str, Any] = {"end1": end1, "end2": end2}
            assoc_name = assoc.get("name")
            if isinstance(assoc_name, str) and assoc_name.strip():
                edge_data["name"] = assoc_name.strip()

            ir.edges.append(
                Edge(
                    id=f"assoc::{assoc_index}",
                    sourceId=_class_id(class1.norm_name),
                    targetId=_class_id(class2.norm_name),
                    type="Association",
                    data=edge_data,
                )
            )
            assoc_index += 1

    def _append_generalization_edges(
        self,
        ir: IR,
        inheritance: List[Any],
        classes: Dict[str, _ClassEntry],
    ) -> None:
        edge_index = 0
        for inh in inheritance:
            if not isinstance(inh, dict):
                continue
            parent = self._class_entry_from_raw(classes, inh.get("parent_class"))
            child_classes = inh.get("child_classes", [])
            if parent is None or not isinstance(child_classes, list):
                continue

            for child_raw in child_classes:
                child = self._class_entry_from_raw(classes, child_raw)
                if child is None:
                    continue
                ir.edges.append(
                    Edge(
                        id=f"gen::{edge_index}",
                        sourceId=_class_id(child.norm_name),
                        targetId=_class_id(parent.norm_name),
                        type="Generalization",
                        data={"specific": child.display_name, "general": parent.display_name},
                    )
                )
                edge_index += 1

    def _append_composition_edges(
        self,
        ir: IR,
        compositions: List[Any],
        classes: Dict[str, _ClassEntry],
    ) -> None:
        edge_index = 0
        for comp in compositions:
            if not isinstance(comp, dict):
                continue
            parent = self._class_entry_from_raw(classes, comp.get("parent_class"))
            child = self._class_entry_from_raw(classes, comp.get("child_class"))
            if parent is None or child is None:
                continue

            edge_data: Dict[str, Any] = {"relationshipType": "composition"}
            cardinality = comp.get("cardinality")
            if isinstance(cardinality, str) and cardinality.strip():
                edge_data["cardinality"] = cardinality.strip()

            ir.edges.append(
                Edge(
                    id=f"composition::{edge_index}",
                    sourceId=_class_id(parent.norm_name),
                    targetId=_class_id(child.norm_name),
                    type="Composition",
                    data=edge_data,
                )
            )
            edge_index += 1

    def _class_entry_from_raw(
        self,
        classes: Dict[str, _ClassEntry],
        raw_name: Any,
    ) -> Optional[_ClassEntry]:
        if not isinstance(raw_name, str):
            return None
        norm = _norm_name(raw_name)
        if not norm:
            return None
        return classes.get(norm)
