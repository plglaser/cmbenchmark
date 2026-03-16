from pathlib import Path

import pytest

from cmbenchmark.parser.uml.uml_custom1_parser import UMLCustom1Parser
from cmbenchmark.types.exceptions import CannotParseError


def _write_model(tmp_path: Path, filename: str, content: str) -> Path:
    path = tmp_path / filename
    path.write_text(content, encoding="utf-8")
    return path


def test_parse_custom1_with_normalization_and_implicit_classes(tmp_path: Path) -> None:
    model_path = _write_model(
        tmp_path,
        "football-model",
        """
class_attributes = {
    'FootballTeam': [],
    "FootballPlayer": ['name:string', 'age:int', 'nickname', 'position:enumeration']
}

associations = [{
    'class1': 'footballteam',
    'class2': 'FOOTBALLPLAYER',
    'cardinality_class1': '',
    'cardinality_class2': '*',
    'name': '',
    'role_class1': '',
    'role_class2': 'players'
}]

inheritance = [{
    'parent_class': 'Entity',
    'child_classes': ['FootballPlayer']
}]

compositions = [{
    'parent_class': 'FootballTeam',
    'child_class': 'Coach',
    'cardinality': '1',
}]

enums = {
    'Position': ["forward", "goalkeeper"]
}
""",
    )

    parser = UMLCustom1Parser()
    ir, _ = parser.parse(str(model_path))

    assert ir.language == "UML-custom1"

    class_nodes = [node for node in ir.nodes if node.type == "Class"]
    assert {"footballteam", "footballplayer", "entity", "coach"} <= {
        node.name.lower() for node in class_nodes
    }

    football_player = next(node for node in class_nodes if node.name == "FootballPlayer")
    attributes = football_player.data.get("attributes", [])
    attrs_by_name = {a["name"]: a for a in attributes}
    assert attrs_by_name["name"]["type"] == "string"
    assert attrs_by_name["age"]["type"] == "int"
    assert "type" not in attrs_by_name["nickname"]
    assert attrs_by_name["position"]["type"] == "enumeration"
    assert attrs_by_name["position"]["enum"] == "Position"

    assoc = next(edge for edge in ir.edges if edge.type == "Association")
    assert assoc.sourceId == "class::footballteam"
    assert assoc.targetId == "class::footballplayer"
    assert assoc.data["end2"]["role"] == "players"

    generalization = next(edge for edge in ir.edges if edge.type == "Generalization")
    assert generalization.sourceId == "class::footballplayer"
    assert generalization.targetId == "class::entity"

    composition = next(edge for edge in ir.edges if edge.id.startswith("composition::"))
    assert composition.type == "Composition"
    assert composition.sourceId == "class::footballteam"
    assert composition.targetId == "class::coach"
    assert composition.data["relationshipType"] == "composition"
    assert composition.data["cardinality"] == "1"

    enum_nodes = [node for node in ir.nodes if node.type == "Enumeration"]
    assert len(enum_nodes) == 1
    assert enum_nodes[0].name == "Position"

    enum_literal_nodes = [node for node in ir.nodes if node.type == "EnumerationLiteral"]
    assert len(enum_literal_nodes) == 2


def test_parse_custom1_with_missing_optional_blocks(tmp_path: Path) -> None:
    model_path = _write_model(
        tmp_path,
        "minimal-model",
        """
class_attributes = {
    "OnlyClass": []
}
""",
    )

    parser = UMLCustom1Parser()
    ir, _ = parser.parse(str(model_path))

    assert len([node for node in ir.nodes if node.type == "Class"]) == 1
    assert not ir.edges


def test_parse_custom1_rejects_xml_input(tmp_path: Path) -> None:
    model_path = _write_model(
        tmp_path,
        "not-custom1.xmi",
        "<uml:Model></uml:Model>",
    )

    parser = UMLCustom1Parser()
    with pytest.raises(CannotParseError):
        parser.parse(str(model_path))
