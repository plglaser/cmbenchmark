from pathlib import Path

from cmbenchmark.construct_catalog import load_construct_defs
from cmbenchmark.measures.construct_measures import compute_construct_measures
from cmbenchmark.parser.uml.uml_xml_pyecore import UMLXMLPyEcoreParser


FIXTURE_XMI = Path(__file__).resolve().parent / "fixtures" / "uml_parser" / "synthetic_uml.xmi"


def test_uml_xml_pyecore_parser_emits_valid_metamodel_graph_ir() -> None:
    parser = UMLXMLPyEcoreParser()

    ir, stats = parser.parse(str(FIXTURE_XMI))

    is_valid, errors = ir.validate()
    assert is_valid, errors
    assert stats.elements_skipped == 0
    assert ir.language == "UML-XML-PyEcore"
    assert ir.data["representation"] == "metamodel_graph"
    assert ir.data["parser"] == "UML-XML-PyEcore"
    assert len(ir.nodes) > 0
    assert len(ir.edges) > 0
    assert any(node.type == "Class" for node in ir.nodes)
    assert any(edge.data.get("containment") is True for edge in ir.edges)
    assert all(set(node.to_dict()) == {"id", "type", "name", "data"} for node in ir.nodes)


def test_uml_xml_pyecore_parser_keeps_uml_type_for_primitive_typed_elements(tmp_path: Path) -> None:
    xmi = """<xmi:XMI
  xmi:version="2.1"
  xmlns:xmi="http://schema.omg.org/spec/XMI/2.1"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:uml="http://www.eclipse.org/uml2/5.0.0/UML">
  <uml:Model xmi:id="model1" name="PrimitiveModel">
    <packagedElement xsi:type="uml:Class" xmi:id="class1" name="Person">
      <ownedAttribute xmi:id="attr1" name="name">
        <type xsi:type="uml:PrimitiveType" href="http://www.omg.org/spec/UML/20131001/PrimitiveTypes.xmi#//String"/>
      </ownedAttribute>
    </packagedElement>
  </uml:Model>
</xmi:XMI>
"""
    model_path = tmp_path / "primitive_typed_property.xmi"
    model_path.write_text(xmi, encoding="utf-8")

    parser = UMLXMLPyEcoreParser()
    ir, _stats = parser.parse(str(model_path))

    property_node = next(node for node in ir.nodes if node.id == "attr1")
    assert property_node.type == "Property"
    assert property_node.data["primitiveType"] == "String"


def test_uml_xml_pyecore_construct_measures_run_with_catalogue() -> None:
    parser = UMLXMLPyEcoreParser()
    ir, _stats = parser.parse(str(FIXTURE_XMI))
    constructs = load_construct_defs("UML-XML-PyEcore")

    assert constructs is not None
    dataset, per_model = compute_construct_measures([ir], constructs)

    assert dataset.d3_m1_construct_presence.constructs_available_count > 0
    assert dataset.d3_m1_construct_presence.constructs_observed_count > 0
    assert ir.id in per_model.d3_m1_construct_presence
    assert ir.id in per_model.d3_m3_construct_frequency
