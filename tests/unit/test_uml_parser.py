from pathlib import Path

import pytest

from cmbenchmark.parser.uml.metamodel import SUPPORTED_UML_CONCEPTS
from cmbenchmark.parser.uml.uml_parser import UMLXMIParser
from cmbenchmark.types.enums import WarningType


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "uml_parser"


def _parse_file(path: Path):
    parser = UMLXMIParser()
    ir, _ = parser.parse(str(path))
    return ir


def _nodes_by_id(ir):
    return {node.id: node for node in ir.nodes}


def _edges_by_id(ir):
    return {edge.id: edge for edge in ir.edges}


@pytest.fixture
def synthetic_uml_ir():
    return _parse_file(FIXTURE_DIR / "synthetic_uml.xmi")


def test_handler_model_metadata(synthetic_uml_ir) -> None:
    ir = synthetic_uml_ir

    assert ir.data["modelId"] == "model1"
    assert ir.data["name"] == "SyntheticModel"
    assert ir.data["visibility"] == "public"
    assert ir.data["imports"] == ["http://www.omg.org/spec/UML/20131001/PrimitiveTypes.xmi#/"]


def test_handler_package_node_and_contains_edges(synthetic_uml_ir) -> None:
    ir = synthetic_uml_ir
    nodes = _nodes_by_id(ir)

    assert nodes["pkg1"].type == "Package"
    assert nodes["pkg1"].data["visibility"] == "private"

    contains = [e for e in ir.edges if e.type == "contains" and e.sourceId == "pkg1"]
    contains_targets = {edge.targetId for edge in contains}
    assert {"c1", "c2", "i1", "e1", "d1", "uc1", "uc2", "uc3"}.issubset(contains_targets)


def test_handler_class_attributes_and_operations(synthetic_uml_ir) -> None:
    nodes = _nodes_by_id(synthetic_uml_ir)

    person = nodes["c1"]
    assert person.type == "Class"
    assert person.data["visibility"] == "public"

    attr = person.data["attributes"][0]
    assert attr["id"] == "attr1"
    assert attr["name"] == "age"
    assert attr["typeRef"] == "d1"
    assert attr["visibility"] == "private"
    assert attr["isReadOnly"] is True
    assert attr["lower"] == "0"
    assert attr["upper"] == "1"
    assert attr["default"] == "18"

    op = person.data["operations"][0]
    assert op["id"] == "op1"
    assert op["name"] == "getAge"
    assert op["visibility"] == "public"
    assert op["isStatic"] is False
    assert op["parameters"][0]["id"] == "p1"


def test_handler_interface_node(synthetic_uml_ir) -> None:
    nodes = _nodes_by_id(synthetic_uml_ir)

    interface = nodes["i1"]
    assert interface.type == "Interface"
    assert interface.data["isAbstract"] is True
    assert interface.data["operations"][0]["id"] == "iop1"


def test_handler_enumeration_literals(synthetic_uml_ir) -> None:
    nodes = _nodes_by_id(synthetic_uml_ir)

    enum = nodes["e1"]
    assert enum.type == "Enumeration"
    literal_names = {lit["name"] for lit in enum.data["literals"]}
    assert literal_names == {"ACTIVE", "INACTIVE"}


def test_handler_datatype_node(synthetic_uml_ir) -> None:
    nodes = _nodes_by_id(synthetic_uml_ir)

    dtype = nodes["d1"]
    assert dtype.type == "DataType"
    assert dtype.data["visibility"] == "public"
    assert dtype.data["isAbstract"] is False


def test_handler_usecase_node_and_extension_point(synthetic_uml_ir) -> None:
    nodes = _nodes_by_id(synthetic_uml_ir)

    uc = nodes["uc1"]
    assert uc.type == "UseCase"
    assert uc.data["visibility"] == "public"
    assert uc.data["extensionPoints"][0]["id"] == "ep1"
    assert uc.data["extensionPoints"][0]["name"] == "PaymentPoint"


def test_handler_actor_node(synthetic_uml_ir) -> None:
    nodes = _nodes_by_id(synthetic_uml_ir)

    actor = nodes["a1"]
    assert actor.type == "Actor"
    assert actor.data["visibility"] == "public"
    assert actor.data["isAbstract"] is False


def test_handler_association_edge(synthetic_uml_ir) -> None:
    edges = _edges_by_id(synthetic_uml_ir)

    assoc = edges["assoc1"]
    assert assoc.type == "Association"
    assert assoc.sourceId == "c1"
    assert assoc.targetId == "c2"
    assert assoc.data["name"] == "Person_Employee"
    assert assoc.data["end1"]["aggregation"] == "composite"
    assert assoc.data["end1"]["upper"] == "1"
    assert assoc.data["end2"]["upper"] == "*"


def test_handler_generalization_edge(synthetic_uml_ir) -> None:
    edges = _edges_by_id(synthetic_uml_ir)

    gen = edges["gen1"]
    assert gen.type == "Generalization"
    assert gen.sourceId == "c2"
    assert gen.targetId == "c1"


def test_handler_interface_realization_edge(synthetic_uml_ir) -> None:
    edges = _edges_by_id(synthetic_uml_ir)

    rel = edges["ir1"]
    assert rel.type == "InterfaceRealization"
    assert rel.sourceId == "c2"
    assert rel.targetId == "i1"


def test_handler_dependency_edge(synthetic_uml_ir) -> None:
    edges = _edges_by_id(synthetic_uml_ir)

    dep = edges["dep1"]
    assert dep.type == "Dependency"
    assert dep.sourceId == "c1"
    assert dep.targetId == "i1"


def test_handler_usage_edge(synthetic_uml_ir) -> None:
    edges = _edges_by_id(synthetic_uml_ir)

    usage = edges["use1"]
    assert usage.type == "Usage"
    assert usage.sourceId == "c2"
    assert usage.targetId == "d1"


def test_handler_include_edge(synthetic_uml_ir) -> None:
    edges = _edges_by_id(synthetic_uml_ir)

    include = edges["inc1"]
    assert include.type == "includes"
    assert include.sourceId == "uc1"
    assert include.targetId == "uc2"


def test_handler_extend_edge_and_extension_point_resolution(synthetic_uml_ir) -> None:
    edges = _edges_by_id(synthetic_uml_ir)

    extend = edges["ext1"]
    assert extend.type == "extends"
    assert extend.sourceId == "uc3"
    assert extend.targetId == "uc1"
    assert extend.data["extensionLocation"] == "ep1"
    assert extend.data["extensionPoint"] == "PaymentPoint"


def test_handler_component_and_owned_usecase(synthetic_uml_ir) -> None:
    nodes = _nodes_by_id(synthetic_uml_ir)

    component = nodes["comp1"]
    assert component.type == "Component"
    assert component.data["visibility"] == "public"
    assert component.data["isLeaf"] is False

    # ownedUseCase has no xsi:type, must still be parsed as a UseCase node.
    assert nodes["uc_comp"].type == "UseCase"


def test_supported_concepts_have_handlers() -> None:
    parser = UMLXMIParser()
    handler_ids = {handler.element_type for handler in parser.handlers}

    for concept_id in SUPPORTED_UML_CONCEPTS:
        assert concept_id in handler_ids


def test_name_child_elements_are_parsed_without_unhandled_child_warning(tmp_path, capsys) -> None:
    xmi = """<?xml version="1.0" encoding="UTF-8"?>
<xmi:XMI xmlns:xmi="http://schema.omg.org/spec/XMI/2.1"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xmlns:uml="http://www.eclipse.org/uml2/5.0.0/UML">
  <uml:Model xmi:id="m1">
    <name>Model From Child</name>
    <packagedElement xsi:type="uml:Class" xmi:id="c1">
      <name>Class From Child</name>
    </packagedElement>
    <packagedElement xsi:type="uml:Component" xmi:id="cmp1">
      <name xsi:nil="true"/>
    </packagedElement>
  </uml:Model>
</xmi:XMI>
"""
    path = tmp_path / "name_child.xmi"
    path.write_text(xmi, encoding="utf-8")

    parser = UMLXMIParser()
    ir, _ = parser.parse(str(path))
    nodes = _nodes_by_id(ir)

    assert ir.data["name"] == "Model From Child"
    assert nodes["c1"].name == "Class From Child"
    assert nodes["cmp1"].name == ""

    captured = capsys.readouterr()
    assert "Child: name" not in captured.out


def test_xmi_type_fallback_is_supported(tmp_path) -> None:
    xmi = """<?xml version="1.0" encoding="UTF-8"?>
<xmi:XMI xmlns:xmi="http://schema.omg.org/spec/XMI/2.1"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xmlns:uml="http://www.eclipse.org/uml2/5.0.0/UML">
  <uml:Model xmi:id="m1" xmi:type="uml:Model" name="ModelA">
    <packagedElement xmi:type="uml:Class" xmi:id="c1" name="ClassA"/>
  </uml:Model>
</xmi:XMI>
"""
    path = tmp_path / "xmi_type.xmi"
    path.write_text(xmi, encoding="utf-8")

    parser = UMLXMIParser()
    ir, _ = parser.parse(str(path))
    nodes = _nodes_by_id(ir)

    assert ir.data["name"] == "ModelA"
    assert "c1" in nodes
    assert nodes["c1"].type == "Class"


def test_association_with_unresolved_end_is_counted_as_skipped(tmp_path) -> None:
    xmi = """<?xml version="1.0" encoding="UTF-8"?>
<xmi:XMI xmlns:xmi="http://schema.omg.org/spec/XMI/2.1"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xmlns:uml="http://www.eclipse.org/uml2/5.0.0/UML">
  <uml:Model xmi:id="m1" name="ModelA">
    <packagedElement xsi:type="uml:Class" xmi:id="c1" name="ClassA"/>
    <packagedElement xsi:type="uml:Association" xmi:id="a1" name="Broken" memberEnd="e1">
      <ownedEnd xmi:id="e1" name="endA" type="c1" owningAssociation="a1" association="a1"/>
    </packagedElement>
  </uml:Model>
</xmi:XMI>
"""
    path = tmp_path / "broken_assoc.xmi"
    path.write_text(xmi, encoding="utf-8")

    parser = UMLXMIParser()
    ir, stats = parser.parse(str(path))

    edges = _edges_by_id(ir)
    assert "a1" not in edges

    assert stats.elements_skipped == 1
    assert stats.warning_count == 1
    assert stats.warnings_by_type[WarningType.MISSING_EDGE_ENDPOINT] == 1
    assert any("Association a1 has fewer than 2 resolved ends" in msg for msg in stats.warning_msgs[WarningType.MISSING_EDGE_ENDPOINT])

def test_typed_child_tags_prefer_xsi_type_over_tag_mapping(tmp_path) -> None:
    xmi = """<?xml version="1.0" encoding="UTF-8"?>
<xmi:XMI xmlns:xmi="http://schema.omg.org/spec/XMI/2.1"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xmlns:uml="http://www.eclipse.org/uml2/5.0.0/UML">
  <uml:Model xmi:id="m1" name="ModelA">
    <packagedElement xsi:type="uml:Class" xmi:id="c1" name="ClassA">
      <ownedBehavior xsi:type="uml:StateMachine" xmi:id="sm_owned" name="OwnedStateMachine"/>
    </packagedElement>
    <packagedElement xsi:type="uml:StateMachine" xmi:id="sm1" name="StateMachineA">
      <region xmi:id="r1" stateMachine="sm1">
        <subvertex xsi:type="uml:State" xmi:id="s1" name="State1" container="r1">
          <doActivity xsi:type="uml:Activity" xmi:id="act_do" name="DoActivity"/>
        </subvertex>
      </region>
    </packagedElement>
    <packagedElement xsi:type="uml:Node" xmi:id="n1" name="NodeA">
      <nestedNode xsi:type="uml:Node" xmi:id="node_nested" name="NestedNode"/>
    </packagedElement>
  </uml:Model>
</xmi:XMI>
"""
    path = tmp_path / "typed_child_tags.xmi"
    path.write_text(xmi, encoding="utf-8")

    parser = UMLXMIParser()
    ir, _ = parser.parse(str(path))
    nodes = _nodes_by_id(ir)

    assert nodes["sm_owned"].type == "StateMachine"
    assert nodes["act_do"].type == "Activity"
    assert nodes["node_nested"].type == "Node"


def test_class_parses_template_related_attributes(tmp_path) -> None:
    xmi = """<?xml version="1.0" encoding="UTF-8"?>
<xmi:XMI xmlns:xmi="http://schema.omg.org/spec/XMI/2.1"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xmlns:uml="http://www.eclipse.org/uml2/5.0.0/UML">
  <uml:Model xmi:id="m1" name="ModelA">
    <packagedElement xsi:type="uml:Class"
                     xmi:id="c1"
                     name="ClassA"
                     href="http://example.com/C"
                     templateParameter="tp1 tp2"
                     owningTemplateParameter="otp1"/>
  </uml:Model>
</xmi:XMI>
"""
    path = tmp_path / "class_template_attrs.xmi"
    path.write_text(xmi, encoding="utf-8")

    parser = UMLXMIParser()
    ir, _ = parser.parse(str(path))
    nodes = _nodes_by_id(ir)
    class_node = nodes["c1"]

    assert class_node.data["href"] == "http://example.com/C"
    assert class_node.data["templateParameter"] == ["tp1", "tp2"]
    assert class_node.data["owningTemplateParameter"] == "otp1"


def test_missing_edge_endpoints_are_reported_as_skips(tmp_path) -> None:
    xmi = """<?xml version="1.0" encoding="UTF-8"?>
<xmi:XMI xmlns:xmi="http://schema.omg.org/spec/XMI/2.1"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xmlns:uml="http://www.eclipse.org/uml2/5.0.0/UML">
  <uml:Model xmi:id="m1" name="ModelA">
    <packagedElement xsi:type="uml:Class" xmi:id="c1" name="C1"/>
    <packagedElement xsi:type="uml:Class" xmi:id="c2" name="C2"/>
    <packagedElement xsi:type="uml:Dependency" xmi:id="dep1" client="c1"/>
    <packagedElement xsi:type="uml:InformationFlow" xmi:id="if1" informationSource="c1"/>
    <packagedElement xsi:type="uml:ControlFlow" xmi:id="cf1" source="c1"/>
    <packagedElement xsi:type="uml:Class" xmi:id="c3" name="C3">
      <generalization xmi:id="gen1"/>
    </packagedElement>
    <packagedElement xsi:type="uml:UseCase" xmi:id="u1" name="U1">
      <include xmi:id="inc1" includingCase="u1"/>
      <extend xmi:id="ext1" extension="u1"/>
    </packagedElement>
  </uml:Model>
</xmi:XMI>
"""
    path = tmp_path / "missing_edge_endpoints.xmi"
    path.write_text(xmi, encoding="utf-8")

    parser = UMLXMIParser()
    _, stats = parser.parse(str(path))

    assert stats.warnings_by_type[WarningType.MISSING_EDGE_ENDPOINT] >= 6
    assert stats.elements_skipped >= 6


def test_duplicate_ids_are_reported(tmp_path) -> None:
    xmi = """<?xml version="1.0" encoding="UTF-8"?>
<xmi:XMI xmlns:xmi="http://schema.omg.org/spec/XMI/2.1"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xmlns:uml="http://www.eclipse.org/uml2/5.0.0/UML">
  <uml:Model xmi:id="m1" name="ModelA">
    <packagedElement xsi:type="uml:Class" xmi:id="c1" name="ClassA"/>
    <packagedElement xsi:type="uml:Class" xmi:id="c1" name="ClassA_Duplicate"/>
    <packagedElement xsi:type="uml:Class" xmi:id="c2" name="ClassB"/>
    <packagedElement xsi:type="uml:Dependency" xmi:id="dep1" client="c1" supplier="c2"/>
    <packagedElement xsi:type="uml:Dependency" xmi:id="dep1" client="c1" supplier="c2"/>
  </uml:Model>
</xmi:XMI>
"""
    path = tmp_path / "duplicate_ids.xmi"
    path.write_text(xmi, encoding="utf-8")

    parser = UMLXMIParser()
    ir, stats = parser.parse(str(path))

    nodes = _nodes_by_id(ir)
    edges = _edges_by_id(ir)
    assert nodes["c1"].name == "ClassA"
    assert "dep1" in edges
    assert stats.warnings_by_type[WarningType.DUPLICATE_ID] >= 2
    assert stats.elements_skipped >= 2


def test_unhandled_packaged_element_is_reported_in_stats(tmp_path) -> None:
    xmi = """<?xml version="1.0" encoding="UTF-8"?>
<xmi:XMI xmlns:xmi="http://schema.omg.org/spec/XMI/2.1"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xmlns:uml="http://www.eclipse.org/uml2/5.0.0/UML">
  <uml:Model xmi:id="m1" name="ModelA">
    <packagedElement xsi:type="uml:UnknownConcept" xmi:id="u1" name="Unknown"/>
  </uml:Model>
</xmi:XMI>
"""
    path = tmp_path / "unknown_packaged_element.xmi"
    path.write_text(xmi, encoding="utf-8")

    parser = UMLXMIParser()
    _, stats = parser.parse(str(path))

    assert stats.warnings_by_type[WarningType.UNKNOWN_NODE_TYPE] == 1
    assert stats.elements_skipped == 1


def test_unhandled_typed_non_packaged_element_is_reported_in_stats(tmp_path) -> None:
    xmi = """<?xml version="1.0" encoding="UTF-8"?>
<xmi:XMI xmlns:xmi="http://schema.omg.org/spec/XMI/2.1"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xmlns:uml="http://www.eclipse.org/uml2/5.0.0/UML">
  <uml:Model xmi:id="m1" name="ModelA">
    <packagedElement xsi:type="uml:Activity" xmi:id="act1" name="Act">
      <ownedNode xsi:type="uml:SendSignalAction" xmi:id="ssa1" name="Send"/>
    </packagedElement>
  </uml:Model>
</xmi:XMI>
"""
    path = tmp_path / "unknown_typed_non_packaged.xmi"
    path.write_text(xmi, encoding="utf-8")

    parser = UMLXMIParser()
    _, stats = parser.parse(str(path))

    assert stats.warnings_by_type[WarningType.UNKNOWN_NODE_TYPE] == 1
    assert stats.elements_skipped == 1


def test_simple_node_unhandled_attributes_are_warned(tmp_path) -> None:
    xmi = """<?xml version="1.0" encoding="UTF-8"?>
<xmi:XMI xmlns:xmi="http://schema.omg.org/spec/XMI/2.1"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xmlns:uml="http://www.eclipse.org/uml2/5.0.0/UML">
  <uml:Model xmi:id="m1" name="ModelA">
    <packagedElement xsi:type="uml:Activity" xmi:id="act1" name="Act" foo="bar"/>
  </uml:Model>
</xmi:XMI>
"""
    path = tmp_path / "simple_node_unhandled_attr.xmi"
    path.write_text(xmi, encoding="utf-8")

    parser = UMLXMIParser()
    _, stats = parser.parse(str(path))

    assert stats.warnings_by_type[WarningType.OTHER] >= 1
    assert any(
        "UNHANDLED ATTRIBUTE" in msg and "foo" in msg
        for msg in stats.warning_msgs[WarningType.OTHER]
    )


def test_missing_owned_operation_and_parameter_ids_are_counted_as_skipped(tmp_path) -> None:
    xmi = """<?xml version="1.0" encoding="UTF-8"?>
<xmi:XMI xmlns:xmi="http://schema.omg.org/spec/XMI/2.1"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xmlns:uml="http://www.eclipse.org/uml2/5.0.0/UML">
  <uml:Model xmi:id="m1" name="ModelA">
    <packagedElement xsi:type="uml:Class" xmi:id="c1" name="ClassA">
      <ownedOperation name="opNoId">
        <ownedParameter name="pNoId"/>
      </ownedOperation>
      <ownedOperation xmi:id="op1" name="opWithParamNoId">
        <ownedParameter name="pNoId2"/>
      </ownedOperation>
    </packagedElement>
  </uml:Model>
</xmi:XMI>
"""
    path = tmp_path / "missing_operation_parameter_ids.xmi"
    path.write_text(xmi, encoding="utf-8")

    parser = UMLXMIParser()
    _, stats = parser.parse(str(path))

    assert stats.warnings_by_type[WarningType.MISSING_ATTRIBUTE] >= 2
    assert stats.elements_skipped >= 2


def test_new_concepts_in_ignored_set_are_mapped(tmp_path) -> None:
    xmi = """<?xml version="1.0" encoding="UTF-8"?>
<xmi:XMI xmlns:xmi="http://schema.omg.org/spec/XMI/2.1"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xmlns:uml="http://www.eclipse.org/uml2/5.0.0/UML">
  <uml:Model xmi:id="m1" name="ModelA">
    <packagedElement xsi:type="uml:Package" xmi:id="pkg1" name="Pkg">
      <packagedElement xsi:type="uml:Class" xmi:id="c1" name="Class1"/>
      <packagedElement xsi:type="uml:Class" xmi:id="c2" name="Class2"/>
      <packagedElement xsi:type="uml:Activity" xmi:id="act1" name="ActivityA"/>
      <packagedElement xsi:type="uml:StateMachine" xmi:id="sm1" name="StateMachineA"/>
      <packagedElement xsi:type="uml:Interaction" xmi:id="in1" name="InteractionA"/>
      <packagedElement xsi:type="uml:InstanceSpecification" xmi:id="ins1" name="InstanceA" classifier="c1 c2"/>
      <packagedElement xsi:type="uml:AssociationClass" xmi:id="ac1" name="AssocClassA" memberEnd="ac_end1 ac_end2" navigableOwnedEnd="ac_end1 ac_end2">
        <ownedEnd xmi:id="ac_end1" type="c1"/>
        <ownedEnd xmi:id="ac_end2" type="c2"/>
        <ownedAttribute xmi:id="ac_attr1" name="score">
          <type xsi:type="uml:PrimitiveType" href="http://www.omg.org/spec/UML/20131001/PrimitiveTypes.xmi#//Integer"/>
        </ownedAttribute>
      </packagedElement>
      <packagedElement xsi:type="uml:Device" xmi:id="dev1" name="DeviceA"/>
      <packagedElement xsi:type="uml:Node" xmi:id="node1" name="NodeA"/>
      <packagedElement xsi:type="uml:Artifact" xmi:id="art1" name="ArtifactA"/>
      <packagedElement xsi:type="uml:ExecutionEnvironment" xmi:id="ee1" name="ExecA"/>
      <packagedElement xsi:type="uml:PrimitiveType" xmi:id="pt1" name="PrimitiveA"/>
      <packagedElement xsi:type="uml:EnumerationLiteral" xmi:id="el1" name="LiteralA"/>
      <packagedElement xsi:type="uml:CommunicationPath" xmi:id="cp1" name="Lan" memberEnd="cp_end1 cp_end2" navigableOwnedEnd="cp_end1 cp_end2">
        <ownedEnd xmi:id="cp_end1" type="node1"/>
        <ownedEnd xmi:id="cp_end2" type="dev1"/>
      </packagedElement>
      <packagedElement xsi:type="uml:InformationFlow" xmi:id="if1" name="FlowA" informationSource="node1" informationTarget="dev1"/>
    </packagedElement>
  </uml:Model>
</xmi:XMI>
"""
    path = tmp_path / "new_concepts.xmi"
    path.write_text(xmi, encoding="utf-8")

    parser = UMLXMIParser()
    ir, _ = parser.parse(str(path))
    nodes = _nodes_by_id(ir)
    edges = _edges_by_id(ir)

    assert nodes["act1"].type == "Activity"
    assert nodes["sm1"].type == "StateMachine"
    assert nodes["in1"].type == "Interaction"
    assert nodes["ins1"].type == "InstanceSpecification"
    assert nodes["ins1"].data["classifierRefs"] == ["c1", "c2"]
    assert nodes["ac1"].type == "AssociationClass"
    assert nodes["dev1"].type == "Device"
    assert nodes["node1"].type == "Node"
    assert nodes["art1"].type == "Artifact"
    assert nodes["ee1"].type == "ExecutionEnvironment"
    assert nodes["pt1"].type == "PrimitiveType"
    assert nodes["el1"].type == "EnumerationLiteral"

    assert edges["cp1"].type == "CommunicationPath"
    assert edges["cp1"].sourceId == "node1"
    assert edges["cp1"].targetId == "dev1"

    assert edges["if1"].type == "InformationFlow"
    assert edges["if1"].sourceId == "node1"
    assert edges["if1"].targetId == "dev1"


def test_non_packaged_elements_from_new_concepts_are_mapped_and_contained(tmp_path) -> None:
    xmi = """<?xml version="1.0" encoding="UTF-8"?>
<xmi:XMI xmlns:xmi="http://schema.omg.org/spec/XMI/2.1"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xmlns:uml="http://www.eclipse.org/uml2/5.0.0/UML">
  <uml:Model xmi:id="m1" name="ModelA">
    <packagedElement xsi:type="uml:Package" xmi:id="pkg1" name="Pkg">
      <packagedElement xsi:type="uml:Activity" xmi:id="act1" name="ActivityA">
        <ownedBehavior xsi:type="uml:Activity" xmi:id="act2" name="NestedActivity"/>
      </packagedElement>
      <packagedElement xsi:type="uml:StateMachine" xmi:id="sm1" name="StateMachineA">
        <region xmi:id="reg1" stateMachine="sm1">
          <subvertex xsi:type="uml:State" xmi:id="state1" name="S1" container="reg1">
            <doActivity xsi:type="uml:StateMachine" xmi:id="sm2" name="NestedStateMachine"/>
          </subvertex>
        </region>
      </packagedElement>
      <packagedElement xsi:type="uml:Node" xmi:id="node1" name="NodeA">
        <nestedNode xsi:type="uml:ExecutionEnvironment" xmi:id="ee2" name="NestedExecEnv"/>
      </packagedElement>
    </packagedElement>
  </uml:Model>
</xmi:XMI>
"""
    path = tmp_path / "non_packaged_new_concepts.xmi"
    path.write_text(xmi, encoding="utf-8")

    parser = UMLXMIParser()
    ir, _ = parser.parse(str(path))
    nodes = _nodes_by_id(ir)
    edges = _edges_by_id(ir)

    assert nodes["act2"].type == "Activity"
    assert nodes["sm2"].type == "StateMachine"
    assert nodes["ee2"].type == "ExecutionEnvironment"

    assert edges["pkg1__contains__act2"].type == "contains"
    assert edges["pkg1__contains__sm2"].type == "contains"
    assert edges["pkg1__contains__ee2"].type == "contains"


def test_activity_flow_and_literal_concepts_are_mapped(tmp_path) -> None:
    xmi = """<?xml version="1.0" encoding="UTF-8"?>
<xmi:XMI xmlns:xmi="http://schema.omg.org/spec/XMI/2.1"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xmlns:uml="http://www.eclipse.org/uml2/5.0.0/UML">
  <uml:Model xmi:id="m1" name="ModelA">
    <packagedElement xsi:type="uml:Package" xmi:id="pkg1" name="Pkg">
      <packagedElement xsi:type="uml:Activity" xmi:id="act1" name="ActivityA">
        <ownedNode xsi:type="uml:InitialNode" xmi:id="n1" name="InitialNode" outgoing="e1"/>
        <ownedNode xsi:type="uml:OpaqueAction" xmi:id="n2" name="OpenMainPage" incoming="e1" outgoing="e2"/>
        <ownedNode xsi:type="uml:DecisionNode" xmi:id="n3" name="DecisionNode" incoming="e2" outgoing="e3 e4"/>
        <ownedNode xsi:type="uml:MergeNode" xmi:id="n4" name="MergeNode" incoming="e3 e4" outgoing="e5"/>
        <ownedNode xsi:type="uml:ForkNode" xmi:id="n5" name="ForkNode" incoming="e5" outgoing="e6 e7"/>
        <ownedNode xsi:type="uml:JoinNode" xmi:id="n6" name="JoinNode" incoming="e6 e7" outgoing="e8 e9"/>
        <ownedNode xsi:type="uml:FlowFinalNode" xmi:id="n7" name="FlowFinalNode" incoming="e8"/>
        <ownedNode xsi:type="uml:ActivityFinalNode" xmi:id="n8" name="ActivityFinalNode" incoming="e9"/>
        <ownedGroup xsi:type="uml:ActivityPartition" xmi:id="grp1" name="PartitionA" node="n2 n3"/>
        <edge xsi:type="uml:ControlFlow" xmi:id="e1" name="ControlFlow1" activity="act1" source="n1" target="n2">
          <guard xsi:type="uml:LiteralString" xmi:id="guard1" value="true"/>
        </edge>
        <edge xsi:type="uml:ObjectFlow" xmi:id="e2" name="ObjectFlow1" activity="act1" source="n2" target="n3"/>
        <edge xsi:type="uml:ControlFlow" xmi:id="e3" activity="act1" source="n3" target="n4"/>
        <edge xsi:type="uml:ControlFlow" xmi:id="e4" activity="act1" source="n3" target="n4"/>
        <edge xsi:type="uml:ControlFlow" xmi:id="e5" activity="act1" source="n4" target="n5"/>
        <edge xsi:type="uml:ControlFlow" xmi:id="e6" activity="act1" source="n5" target="n6"/>
        <edge xsi:type="uml:ControlFlow" xmi:id="e7" activity="act1" source="n5" target="n6"/>
        <edge xsi:type="uml:ControlFlow" xmi:id="e8" activity="act1" source="n6" target="n7"/>
        <edge xsi:type="uml:ControlFlow" xmi:id="e9" activity="act1" source="n6" target="n8"/>
      </packagedElement>
      <packagedElement xsi:type="uml:Class" xmi:id="c1" name="ClassA">
        <ownedAttribute xmi:id="attr1" name="score">
          <lowerValue xsi:type="uml:LiteralInteger" xmi:id="lit_i" value="0"/>
          <upperValue xsi:type="uml:LiteralUnlimitedNatural" xmi:id="lit_u" value="*"/>
          <defaultValue xsi:type="uml:LiteralBoolean" xmi:id="lit_b" value="true"/>
        </ownedAttribute>
      </packagedElement>
      <packagedElement xsi:type="uml:InstanceSpecification" xmi:id="ins1" name="Info" classifier="c1">
        <slot xmi:id="slot1" owningInstance="ins1" definingFeature="attr1">
          <value xsi:type="uml:Expression" xmi:id="expr1" symbol="x+1"/>
          <value xsi:type="uml:InstanceValue" xmi:id="iv1" instance="ins1"/>
          <value xsi:type="uml:LiteralReal" xmi:id="lit_r" value="3.14"/>
        </slot>
      </packagedElement>
    </packagedElement>
  </uml:Model>
</xmi:XMI>
"""
    path = tmp_path / "activity_flow_and_literals.xmi"
    path.write_text(xmi, encoding="utf-8")

    parser = UMLXMIParser()
    ir, _ = parser.parse(str(path))
    nodes = _nodes_by_id(ir)
    edges = _edges_by_id(ir)

    assert nodes["n1"].type == "InitialNode"
    assert nodes["n2"].type == "OpaqueAction"
    assert nodes["n3"].type == "DecisionNode"
    assert nodes["n4"].type == "MergeNode"
    assert nodes["n5"].type == "ForkNode"
    assert nodes["n6"].type == "JoinNode"
    assert nodes["n7"].type == "FlowFinalNode"
    assert nodes["n8"].type == "ActivityFinalNode"
    assert nodes["grp1"].type == "ActivityPartition"
    assert nodes["lit_i"].type == "LiteralInteger"
    assert nodes["lit_u"].type == "LiteralUnlimitedNatural"
    assert nodes["lit_b"].type == "LiteralBoolean"
    assert nodes["expr1"].type == "Expression"
    assert nodes["iv1"].type == "InstanceValue"
    assert nodes["lit_r"].type == "LiteralReal"

    assert edges["e1"].type == "ControlFlow"
    assert edges["e1"].sourceId == "n1"
    assert edges["e1"].targetId == "n2"
    assert edges["e2"].type == "ObjectFlow"
    assert edges["e2"].sourceId == "n2"
    assert edges["e2"].targetId == "n3"


def test_interaction_and_state_machine_concepts_are_mapped(tmp_path) -> None:
    xmi = """<?xml version="1.0" encoding="UTF-8"?>
<xmi:XMI xmlns:xmi="http://schema.omg.org/spec/XMI/2.1"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xmlns:uml="http://www.eclipse.org/uml2/5.0.0/UML">
  <uml:Model xmi:id="m1" name="ModelA">
    <packagedElement xsi:type="uml:Package" xmi:id="pkg1" name="Pkg">
      <packagedElement xsi:type="uml:Interaction" xmi:id="in1" name="InteractionA">
        <lifeline xmi:id="lif1" name="Client"/>
        <lifeline xmi:id="lif2" name="Server"/>
        <fragment xsi:type="uml:MessageOccurrenceSpecification" xmi:id="mos1" covered="lif1" enclosingInteraction="in1"/>
        <fragment xsi:type="uml:MessageOccurrenceSpecification" xmi:id="mos2" covered="lif2" enclosingInteraction="in1"/>
        <message xmi:id="msg1" name="request" sendEvent="mos1" receiveEvent="mos2" messageSort="synchCall"/>
        <fragment xsi:type="uml:ExecutionOccurrenceSpecification" xmi:id="eos1" covered="lif2" enclosingInteraction="in1"/>
        <fragment xsi:type="uml:BehaviorExecutionSpecification" xmi:id="bes1" covered="lif2" enclosingInteraction="in1" start="mos2" finish="eos1"/>
        <fragment xsi:type="uml:CombinedFragment" xmi:id="cf1" name="loop" interactionOperator="loop" enclosingInteraction="in1">
          <operand xmi:id="op1" name="operand1"/>
        </fragment>
        <nestedClassifier xsi:type="uml:Collaboration" xmi:id="col1" name="Collab1"/>
      </packagedElement>
      <packagedElement xsi:type="uml:StateMachine" xmi:id="sm1" name="StateMachineA">
        <region xmi:id="r1" stateMachine="sm1">
          <subvertex xsi:type="uml:Pseudostate" xmi:id="ps1" name="Initial" container="r1" kind="initial"/>
          <subvertex xsi:type="uml:State" xmi:id="s1" name="State1" container="r1"/>
          <subvertex xsi:type="uml:State" xmi:id="s2" name="State2" container="r1"/>
          <transition xmi:id="t1" source="ps1" target="s1" container="r1"/>
          <transition xmi:id="t2" source="s1" target="s2" container="r1"/>
        </region>
      </packagedElement>
    </packagedElement>
  </uml:Model>
</xmi:XMI>
"""
    path = tmp_path / "interaction_and_state_machine.xmi"
    path.write_text(xmi, encoding="utf-8")

    parser = UMLXMIParser()
    ir, _ = parser.parse(str(path))
    nodes = _nodes_by_id(ir)
    edges = _edges_by_id(ir)

    assert nodes["lif1"].type == "Lifeline"
    assert nodes["lif2"].type == "Lifeline"
    assert nodes["mos1"].type == "MessageOccurrenceSpecification"
    assert nodes["mos2"].type == "MessageOccurrenceSpecification"
    assert nodes["eos1"].type == "ExecutionOccurrenceSpecification"
    assert nodes["bes1"].type == "BehaviorExecutionSpecification"
    assert nodes["cf1"].type == "CombinedFragment"
    assert nodes["op1"].type == "InteractionOperand"
    assert nodes["col1"].type == "Collaboration"
    assert nodes["r1"].type == "Region"
    assert nodes["ps1"].type == "Pseudostate"
    assert nodes["s1"].type == "State"
    assert nodes["s2"].type == "State"

    assert edges["msg1"].type == "Message"
    assert edges["msg1"].sourceId == "mos1"
    assert edges["msg1"].targetId == "mos2"
    assert edges["t1"].type == "Transition"
    assert edges["t1"].sourceId == "ps1"
    assert edges["t1"].targetId == "s1"
    assert edges["t2"].type == "Transition"
    assert edges["t2"].sourceId == "s1"
    assert edges["t2"].targetId == "s2"
