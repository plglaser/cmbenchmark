import json

import pytest

from cmbenchmark.parser.bpmn.bpmn_signavio_json_parser import BPMNSignavioJSONParser
from cmbenchmark.types.enums import WarningType
from cmbenchmark.types.exceptions import CannotParseError


def _build_minimal_signavio_bpmn() -> dict:
    return {
        "resourceId": "canvas",
        "stencil": {"id": "BPMNDiagram"},
        "properties": {"name": "Synthetic BPMN"},
        "stencilset": {"namespace": "http://b3mn.org/stencilset/bpmn2.0#"},
        "childShapes": [
            {
                "resourceId": "p1",
                "stencil": {"id": "Pool"},
                "properties": {"name": "Main Pool"},
                "childShapes": [
                    {
                        "resourceId": "l1",
                        "stencil": {"id": "Lane"},
                        "properties": {"name": "Lane A"},
                        "childShapes": [
                            {
                                "resourceId": "s1",
                                "stencil": {"id": "StartNoneEvent"},
                                "properties": {"name": "Start"},
                                "childShapes": [],
                                "outgoing": [{"resourceId": "f1"}],
                            },
                            {
                                "resourceId": "t1",
                                "stencil": {"id": "Task"},
                                "properties": {"name": "Do Work"},
                                "childShapes": [],
                                "outgoing": [
                                    {"resourceId": "f2"},
                                    {"resourceId": "m1"},
                                    {"resourceId": "unknown-edge"},
                                ],
                            },
                            {
                                "resourceId": "e1",
                                "stencil": {"id": "EndNoneEvent"},
                                "properties": {"name": "End"},
                                "childShapes": [],
                                "outgoing": [],
                            },
                            {
                                "stencil": {"id": "Task"},
                                "properties": {"name": "Missing Id"},
                                "childShapes": [],
                                "outgoing": [],
                            },
                        ],
                        "outgoing": [],
                    }
                ],
                "outgoing": [],
            },
            {
                "resourceId": "d1",
                "stencil": {"id": "DataObject"},
                "properties": {"name": "Document"},
                "childShapes": [],
                "outgoing": [{"resourceId": "a1"}],
            },
            {
                "resourceId": "txt1",
                "stencil": {"id": "TextAnnotation"},
                "properties": {"name": "Note", "text": "annotation"},
                "childShapes": [],
                "outgoing": [],
            },
            {
                "resourceId": "f1",
                "stencil": {"id": "SequenceFlow"},
                "properties": {"name": "s->t"},
                "childShapes": [],
                "outgoing": [{"resourceId": "t1"}],
                "target": {"resourceId": "t1"},
            },
            {
                "resourceId": "f2",
                "stencil": {"id": "SequenceFlow"},
                "properties": {"name": "t->e"},
                "childShapes": [],
                "outgoing": [{"resourceId": "e1"}],
                "target": {"resourceId": "e1"},
            },
            {
                "resourceId": "m1",
                "stencil": {"id": "MessageFlow"},
                "properties": {"name": "t->doc"},
                "childShapes": [],
                "outgoing": [{"resourceId": "d1"}],
                "target": {"resourceId": "d1"},
            },
            {
                "resourceId": "a1",
                "stencil": {"id": "Association_Undirected"},
                "properties": {"name": "doc-note"},
                "childShapes": [],
                "outgoing": [{"resourceId": "txt1"}],
                "target": {"resourceId": "txt1"},
            },
            {
                "resourceId": "bad1",
                "stencil": {"id": "SequenceFlow"},
                "properties": {"name": "broken"},
                "childShapes": [],
                "outgoing": [],
            },
        ],
        "outgoing": [],
    }


def test_parse_signavio_bpmn_json_to_nodes_edges_and_contains(tmp_path) -> None:
    model_path = tmp_path / "model.json"
    model_path.write_text(json.dumps(_build_minimal_signavio_bpmn()), encoding="utf-8")

    parser = BPMNSignavioJSONParser()
    ir, stats = parser.parse(str(model_path))

    assert ir.language == "BPMN-Signavio-JSON"
    assert ir.data["name"] == "Synthetic BPMN"

    nodes = {node.id: node for node in ir.nodes}
    edges = {edge.id: edge for edge in ir.edges}

    assert {"canvas", "p1", "l1", "s1", "t1", "e1", "d1", "txt1"}.issubset(nodes.keys())
    assert nodes["t1"].type == "Task"
    assert nodes["txt1"].type == "TextAnnotation"
    assert "bad1" not in edges

    assert edges["f1"].type == "SequenceFlow"
    assert edges["f1"].sourceId == "s1"
    assert edges["f1"].targetId == "t1"

    assert edges["f2"].sourceId == "t1"
    assert edges["f2"].targetId == "e1"

    assert edges["m1"].type == "MessageFlow"
    assert edges["m1"].sourceId == "t1"
    assert edges["m1"].targetId == "d1"

    assert edges["a1"].type == "Association_Undirected"
    assert edges["a1"].sourceId == "d1"
    assert edges["a1"].targetId == "txt1"

    assert "contains:canvas->p1" in edges
    assert "contains:p1->l1" in edges
    assert "contains:l1->s1" in edges

    assert stats.warnings_by_type.get(WarningType.MISSING_ATTRIBUTE, 0) >= 1
    assert stats.warnings_by_type.get(WarningType.UNRESOLVED_REFERENCE, 0) >= 1
    assert stats.warnings_by_type.get(WarningType.MISSING_EDGE_ENDPOINT, 0) >= 1


def test_parse_rejects_non_signavio_json(tmp_path) -> None:
    model_path = tmp_path / "invalid.json"
    model_path.write_text(
        json.dumps(
            {
                "resourceId": "root",
                "stencil": {"id": "NotBPMN"},
                "childShapes": [],
            }
        ),
        encoding="utf-8",
    )

    parser = BPMNSignavioJSONParser()
    with pytest.raises(CannotParseError):
        parser.parse(str(model_path))
