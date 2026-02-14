from cmbenchmark.parser.ecore.ecore_parser import EcoreParser
from cmbenchmark.types.enums import WarningType


def test_parse_ecore_with_ekeys_attribute(tmp_path):
    model_file = tmp_path / "with_ekeys.ecore"
    model_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<ecore:EPackage xmi:version="2.0"
    xmlns:xmi="http://www.omg.org/XMI"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:ecore="http://www.eclipse.org/emf/2002/Ecore"
    name="adfg" nsURI="http://www.example.org/adfg" nsPrefix="adfg">
  <eClassifiers xsi:type="ecore:EClass" name="Application">
    <eStructuralFeatures xsi:type="ecore:EReference" name="graphs" upperBound="-1"
        eType="#//Graph" containment="true" eOpposite="#//Graph/owner" eKeys="#//Graph/name"/>
  </eClassifiers>
  <eClassifiers xsi:type="ecore:EClass" name="Graph">
    <eStructuralFeatures xsi:type="ecore:EReference" name="owner" lowerBound="1" eType="#//Application"
        eOpposite="#//Application/graphs"/>
  </eClassifiers>
</ecore:EPackage>
""",
        encoding="utf-8",
    )

    parser = EcoreParser()
    parser.set_dataset_root(tmp_path / "data" / "ecore-models")
    ir, stats = parser.parse(str(model_file))

    node_types = {node.type for node in ir.nodes}
    assert "EPackage" in node_types
    assert "EClass" in node_types

    edge_types = {edge.type for edge in ir.edges}
    assert "Containment" in edge_types
    assert "Reference" in edge_types

    assert stats.warnings_by_type.get(WarningType.COMPATIBILITY_ADAPTATION, 0) == 1


def test_parse_ecore_with_generic_reference_without_etype(tmp_path):
    model_file = tmp_path / "generic_ref.ecore"
    model_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<ecore:EPackage xmi:version="2.0"
    xmlns:xmi="http://www.omg.org/XMI"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:ecore="http://www.eclipse.org/emf/2002/Ecore"
    name="m" nsURI="http://example.org/m" nsPrefix="m">
  <eClassifiers xsi:type="ecore:EClass" name="A">
    <eTypeParameters name="T"/>
    <eStructuralFeatures xsi:type="ecore:EReference" name="items" upperBound="-1">
      <eGenericType eTypeParameter="#//A/T"/>
    </eStructuralFeatures>
  </eClassifiers>
</ecore:EPackage>
""",
        encoding="utf-8",
    )

    parser = EcoreParser()
    ir, stats = parser.parse(str(model_file))

    assert len(ir.nodes) > 0
    assert stats.warnings_by_type.get(WarningType.UNSUPPORTED_GENERIC_REFERENCE, 0) >= 1
    assert stats.warnings_by_type.get(WarningType.MISSING_EDGE_ENDPOINT, 0) == 0


def test_parse_ecore_with_xml_comment_nodes(tmp_path):
    model_file = tmp_path / "with_comments.ecore"
    model_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<ecore:EPackage xmi:version="2.0"
    xmlns:xmi="http://www.omg.org/XMI"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:ecore="http://www.eclipse.org/emf/2002/Ecore"
    name="p" nsURI="http://p" nsPrefix="p">
  <eClassifiers xsi:type="ecore:EClass" name="A">
    <eStructuralFeatures xsi:type="ecore:EReference" name="b" eType="#//B" containment="true">
      <eAnnotations source="http://schema.omg.org/spec/MOF/2.0/emof.xml#Property.oppositeRoleName">
        <details key="body" value="owner"/>
        <!--details key="anotherKey" value="anotherValue"/-->
      </eAnnotations>
    </eStructuralFeatures>
  </eClassifiers>
  <eClassifiers xsi:type="ecore:EClass" name="B"/>
</ecore:EPackage>
""",
        encoding="utf-8",
    )

    parser = EcoreParser()
    ir, stats = parser.parse(str(model_file))

    assert len(ir.nodes) > 0
    assert len(ir.edges) > 0
    assert stats.warnings_by_type.get(WarningType.COMPATIBILITY_ADAPTATION, 0) >= 1


def test_parse_ecore_with_scoped_external_mapping(tmp_path):
    model_dir = (
        tmp_path
        / "data"
        / "ecore-models"
        / "vendorx"
        / "project"
        / "plugins"
        / "org.example"
        / "model"
        / "ecore"
    )
    archive_dir = (
        tmp_path
        / "data"
        / "ecore-models"
        / "vendorx"
        / "archive"
        / "org.example"
        / "metamodels"
    )
    model_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    emof_file = archive_dir / "EMOF.ecore"
    emof_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<ecore:EPackage xmi:version="2.0"
    xmlns:xmi="http://www.omg.org/XMI"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:ecore="http://www.eclipse.org/emf/2002/Ecore"
    xmi:id="EMOF" name="EMOF" nsURI="http://example.org/emof" nsPrefix="emof">
    <eClassifiers xsi:type="ecore:EClass" name="Type"/>
</ecore:EPackage>
""",
        encoding="utf-8",
    )

    model_file = model_dir / "EssentialOCL.ecore"
    model_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<ecore:EPackage xmi:version="2.0"
    xmlns:xmi="http://www.omg.org/XMI"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:ecore="http://www.eclipse.org/emf/2002/Ecore"
    xmi:id="EssentialOCL" name="EssentialOCL" nsURI="http://example.org/ocl" nsPrefix="ocl">
  <eClassifiers xsi:type="ecore:EClass" xmi:id="EssentialOCL.AnyType" name="AnyType"
      eSuperTypes="EMOF.ecore#//Type"/>
</ecore:EPackage>
""",
        encoding="utf-8",
    )

    parser = EcoreParser()
    ir, stats = parser.parse(str(model_file))

    edge_types = {edge.type for edge in ir.edges}
    assert "Generalization" in edge_types
    assert stats.warnings_by_type.get(WarningType.UNRESOLVED_REFERENCE, 0) == 0
    assert stats.warnings_by_type.get(WarningType.MISSING_EDGE_ENDPOINT, 0) == 0


def test_parse_ecore_without_scoped_external_mapping_creates_stub_nodes(tmp_path):
    model_dir = (
        tmp_path
        / "data"
        / "ecore-models"
        / "vendorx"
        / "project"
        / "plugins"
        / "org.example"
        / "model"
        / "ecore"
    )
    archive_dir = (
        tmp_path
        / "data"
        / "ecore-models"
        / "vendorx"
        / "archive"
        / "org.example"
        / "metamodels"
    )
    model_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    (archive_dir / "EMOF.ecore").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<ecore:EPackage xmi:version="2.0"
    xmlns:xmi="http://www.omg.org/XMI"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:ecore="http://www.eclipse.org/emf/2002/Ecore"
    xmi:id="EMOF" name="EMOF" nsURI="http://example.org/emof" nsPrefix="emof">
    <eClassifiers xsi:type="ecore:EClass" name="Type"/>
</ecore:EPackage>
""",
        encoding="utf-8",
    )

    model_file = model_dir / "EssentialOCL.ecore"
    model_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<ecore:EPackage xmi:version="2.0"
    xmlns:xmi="http://www.omg.org/XMI"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:ecore="http://www.eclipse.org/emf/2002/Ecore"
    xmi:id="EssentialOCL" name="EssentialOCL" nsURI="http://example.org/ocl" nsPrefix="ocl">
  <eClassifiers xsi:type="ecore:EClass" xmi:id="EssentialOCL.AnyType" name="AnyType"
      eSuperTypes="EMOF.ecore#//Type"/>
</ecore:EPackage>
""",
        encoding="utf-8",
    )

    parser = EcoreParser()
    parser.set_enable_scoped_uri_mappings(False)
    ir, stats = parser.parse(str(model_file))

    edge_types = {edge.type for edge in ir.edges}
    assert "Generalization" in edge_types
    assert stats.warnings_by_type.get(WarningType.UNRESOLVED_REFERENCE, 0) >= 1
    assert stats.warnings_by_type.get(WarningType.MISSING_EDGE_ENDPOINT, 0) == 0
    assert any(
        node.type == "EClass" and node.name == "Type" and node.data.get("external") is True
        for node in ir.nodes
    )


def test_parse_ecore_with_href_fragment_uses_external_stub_node(tmp_path):
    model_dir = tmp_path / "xmi"
    model_dir.mkdir(parents=True, exist_ok=True)

    model_file = model_dir / "EssentialOCL.ecore"
    model_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<ecore:EPackage xmi:version="2.0"
    xmlns:xmi="http://www.omg.org/XMI"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:ecore="http://www.eclipse.org/emf/2002/Ecore"
    xmi:id="EssentialOCL" name="EssentialOCL" nsURI="http://example.org/ocl" nsPrefix="ocl">
  <eClassifiers xsi:type="ecore:EClass" xmi:id="EssentialOCL.AnyType" name="AnyType">
    <eSuperTypes href="EMOF.ecore#EMOF.Type"/>
  </eClassifiers>
</ecore:EPackage>
""",
        encoding="utf-8",
    )

    parser = EcoreParser()
    parser.set_enable_scoped_uri_mappings(False)
    ir, stats = parser.parse(str(model_file))

    assert any(edge.type == "Generalization" for edge in ir.edges)
    assert stats.warnings_by_type.get(WarningType.MISSING_EDGE_ENDPOINT, 0) == 0
    assert any(
        node.type == "EClass"
        and node.name == "Type"
        and node.data.get("external") is True
        and node.data.get("originResource") == "EMOF.ecore"
        for node in ir.nodes
    )


def test_parse_ecore_recovers_external_reference_target_from_raw_etype(tmp_path):
    model_dir = tmp_path / "db2entity"
    model_dir.mkdir(parents=True, exist_ok=True)

    model_file = model_dir / "Db2EntityDsl.ecore"
    model_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<ecore:EPackage xmi:version="2.0"
    xmlns:xmi="http://www.omg.org/XMI"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:ecore="http://www.eclipse.org/emf/2002/Ecore"
    name="db2EntityDsl" nsURI="http://example.org/db2entity" nsPrefix="db2EntityDsl">
  <eClassifiers xsi:type="ecore:EClass" name="EntityColumnMapper"
      eSuperTypes="../../missing/DbDsl.ecore#//AbstractColumnMapper">
    <eStructuralFeatures xsi:type="ecore:EReference" name="entity"
        eType="ecore:EClass ../../missing/EntityDsl.ecore#//Attribute"/>
  </eClassifiers>
</ecore:EPackage>
""",
        encoding="utf-8",
    )

    parser = EcoreParser()
    parser.set_enable_scoped_uri_mappings(False)
    ir, stats = parser.parse(str(model_file))

    assert stats.warnings_by_type.get(WarningType.UNRESOLVED_REFERENCE, 0) >= 1
    assert stats.warnings_by_type.get(WarningType.MISSING_EDGE_ENDPOINT, 0) == 0
    assert any(edge.type == "Reference" for edge in ir.edges)
    assert any(
        node.type == "EClass"
        and node.name == "Attribute"
        and node.data.get("external") is True
        for node in ir.nodes
    )


def test_parse_ecore_recovers_internal_subpackage_target_from_raw_etype(tmp_path):
    model_dir = tmp_path / "proto.mbpmn.services" / "model"
    model_dir.mkdir(parents=True, exist_ok=True)

    model_file = model_dir / "services.ecore"
    model_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<ecore:EPackage xmi:version="2.0"
    xmlns:xmi="http://www.omg.org/XMI"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:ecore="http://www.eclipse.org/emf/2002/Ecore"
    name="services" nsURI="http://example.org/services" nsPrefix="services">
  <eSubpackages name="services" nsURI="services.services" nsPrefix="services">
    <eClassifiers xsi:type="ecore:EClass" name="Interface"
        eSuperTypes="../../proto.mbpmn.foundation/model/foundation.ecore#//foundation/RootElement">
      <eStructuralFeatures xsi:type="ecore:EReference" name="operations"
          lowerBound="1" upperBound="-1" eType="#//services/Operation" containment="true"/>
    </eClassifiers>
    <eClassifiers xsi:type="ecore:EClass" name="Operation"
        eSuperTypes="../../proto.mbpmn.foundation/model/foundation.ecore#//foundation/BaseElement"/>
  </eSubpackages>
</ecore:EPackage>
""",
        encoding="utf-8",
    )

    parser = EcoreParser()
    parser.set_enable_scoped_uri_mappings(False)
    ir, stats = parser.parse(str(model_file))

    assert stats.warnings_by_type.get(WarningType.UNRESOLVED_REFERENCE, 0) >= 1
    assert stats.warnings_by_type.get(WarningType.MISSING_EDGE_ENDPOINT, 0) == 0
    assert any(edge.type == "Containment" for edge in ir.edges)
