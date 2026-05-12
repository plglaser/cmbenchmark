"""Label extraction for D2 (and downstream D5) measures.

A `LabelView` is a single labelled thing in the IR: a top-level node or edge, or a
nested attribute/operation/literal carried inside `node.data`.  Measures consume
`LabelView`s instead of poking at `node.data` directly, so the IR's nested-label
layout lives in exactly one place.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, Literal, Optional, Sequence, Tuple

from cmbenchmark.types.ir import IR


# Whitelist of attribute names that may appear in `LexicalProfile.label_attributes`.
# Keeping this list small protects the extractor from being asked to read
# non-string fields (e.g. `data`, `attributes`) and silently coerce them to None.
KNOWN_LABEL_ATTRS: Tuple[str, ...] = ("name", "label", "displayName", "title")


LabelKind = Literal["Node", "Edge", "Attribute", "Operation", "Literal"]


# Nested children carried inside `node.data` by the parsers.
# Each entry maps the dict key in `node.data` to the LabelKind we emit and the
# singular suffix appended to the parent node's `type` for the synthesized
# `LabelView.type`.
_NESTED_CHILD_SPECS: Tuple[Tuple[str, LabelKind, str], ...] = (
    ("attributes", "Attribute", "attribute"),
    ("operations", "Operation", "operation"),
    ("literals", "Literal", "literal"),
)


@dataclass(frozen=True)
class LabelView:
    """A single labelled thing pulled out of the IR.

    Top-level nodes/edges produce one `LabelView` each; nested children
    (`attributes`, `operations`, `literals` lists in `node.data`) produce one
    `LabelView` per list entry, even when the entry has an empty/missing name —
    the extractor doesn't suppress empties so downstream "missing label"
    measures can see them.
    """

    id: str
    kind: LabelKind
    type: str
    name: str
    parent_node_id: Optional[str] = None
    extras: Dict[str, Any] = field(default_factory=dict)


def _resolve_text_from_attrs(obj: Any, label_attributes: Sequence[str]) -> Optional[str]:
    """Find the first whitelisted label attribute on `obj` that holds a string.

    Looks first as a real attribute (e.g. `Node.name`), then falls back to a
    `data` dict entry (e.g. `Edge.data["name"]`).  Returns `None` when no
    candidate yields a string value, so callers can distinguish "slot is
    empty" from "slot does not exist".
    """
    data = getattr(obj, "data", None) if not isinstance(obj, dict) else obj
    for attr in label_attributes:
        if attr not in KNOWN_LABEL_ATTRS:
            continue
        if not isinstance(obj, dict):
            val = getattr(obj, attr, None)
            if isinstance(val, str):
                return val
            if val is not None:
                # Slot exists on the object but is not a string — treat as missing.
                return None
        if isinstance(data, dict) and attr in data:
            val = data[attr]
            if isinstance(val, str):
                return val
    return None


def _resolve_text_from_dict(d: Dict[str, Any], label_attributes: Sequence[str]) -> Optional[str]:
    """Like `_resolve_text_from_attrs`, but for a nested-child dict from `node.data`."""
    for attr in label_attributes:
        if attr not in KNOWN_LABEL_ATTRS:
            continue
        val = d.get(attr)
        if isinstance(val, str):
            return val
    return None


def iter_labels(
    ir: IR,
    *,
    include_nodes: bool = True,
    include_edges: bool = False,
    include_nested_labels: bool = True,
    label_attributes: Sequence[str] = ("name",),
) -> Iterator[LabelView]:
    """Yield every label-bearing thing in the IR.

    Nodes yield one `LabelView` each.  When `include_nested_labels=True`, any
    entries in `node.data["attributes"]`, `node.data["operations"]`,
    `node.data["literals"]` also yield one `LabelView` each — this is what
    surfaces UML attribute/operation/literal names and Ecore EAttribute /
    EOperation / EEnumLiteral names to D2 (and downstream D5).
    """
    if include_nodes:
        for n in ir.nodes:
            text = _resolve_text_from_attrs(n, label_attributes)
            yield LabelView(
                id=n.id,
                kind="Node",
                type=n.type,
                name=text if text is not None else "",
                extras=n.data if isinstance(n.data, dict) else {},
            )
            if include_nested_labels and isinstance(n.data, dict):
                for list_key, child_kind, type_suffix in _NESTED_CHILD_SPECS:
                    children = n.data.get(list_key)
                    if not isinstance(children, list):
                        continue
                    for idx, child in enumerate(children):
                        if isinstance(child, dict):
                            child_text = _resolve_text_from_dict(child, label_attributes)
                            extras = child
                        elif isinstance(child, str):
                            child_text = child
                            extras = {}
                        else:
                            child_text = None
                            extras = {}
                        yield LabelView(
                            id=f"{n.id}::{type_suffix}::{idx}",
                            kind=child_kind,
                            type=f"{n.type}.{type_suffix}",
                            name=child_text if child_text is not None else "",
                            parent_node_id=n.id,
                            extras=extras,
                        )

    if include_edges:
        for e in ir.edges:
            text = _resolve_text_from_attrs(e, label_attributes)
            yield LabelView(
                id=e.id,
                kind="Edge",
                type=e.type,
                name=text if text is not None else "",
                extras=e.data if isinstance(e.data, dict) else {},
            )
