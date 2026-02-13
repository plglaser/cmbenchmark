from cmbenchmark.parser.archimate.archimate_archi_parser import ArchiMateArchiParser
from cmbenchmark.types.enums import WarningType


def test_parse_connectors_folder_elements(tmp_path):
    model_file = tmp_path / "model.archimate"
    model_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<archimate:model xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:archimate="http://www.archimatetool.com/archimate" name="GateKeeper" id="2fa42151" version="3.1.1">
  <folder name="Business" id="9a505b7e" type="business">
    <element xsi:type="archimate:Representation" id="cb549248" name="Client"/>
  </folder>
  <folder name="Connectors" id="43cdf25e" type="connectors">
    <element xsi:type="archimate:Junction" id="255678c7" name="Junction"/>
    <element xsi:type="archimate:Junction" id="91ca0103" name="Junction"/>
  </folder>
  <folder name="Relations" id="f216c3d8" type="relations">
    <element xsi:type="archimate:TriggeringRelationship" id="272ff3ed" source="91ca0103" target="255678c7"/>
  </folder>
</archimate:model>
""",
        encoding="utf-8",
    )

    parser = ArchiMateArchiParser()
    ir, stats = parser.parse(str(model_file))

    node_by_id = {n.id: n for n in ir.nodes}

    assert "255678c7" in node_by_id
    assert node_by_id["255678c7"].type == "Junction"
    assert node_by_id["255678c7"].data["layer"] == "connectors"
    assert "91ca0103" in node_by_id

    assert len(ir.edges) == 1
    assert ir.edges[0].sourceId == "91ca0103"
    assert ir.edges[0].targetId == "255678c7"

    unresolved_count = stats.warnings_by_type.get(WarningType.UNRESOLVED_REFERENCE, 0)
    assert unresolved_count == 0


def test_parse_elements_in_nested_folders(tmp_path):
    model_file = tmp_path / "nested.archimate"
    model_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<archimate:model xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:archimate="http://www.archimatetool.com/archimate" name="Nested" id="nested-model" version="5.0.0">
  <folder name="Strategy" id="s1" type="strategy">
    <folder name="Level1" id="f1">
      <folder name="Level2" id="f2">
        <element xsi:type="archimate:Capability" id="cap-a" name="A"/>
      </folder>
      <element xsi:type="archimate:Capability" id="cap-b" name="B"/>
    </folder>
  </folder>
  <folder name="Relations" id="r1" type="relations">
    <element xsi:type="archimate:SpecializationRelationship" id="rel-1" source="cap-a" target="cap-b"/>
  </folder>
</archimate:model>
""",
        encoding="utf-8",
    )

    parser = ArchiMateArchiParser()
    ir, stats = parser.parse(str(model_file))

    node_by_id = {n.id: n for n in ir.nodes}

    assert "cap-a" in node_by_id
    assert "cap-b" in node_by_id
    assert node_by_id["cap-a"].data["layer"] == "strategy"
    assert node_by_id["cap-b"].data["layer"] == "strategy"

    assert len(ir.edges) == 1
    assert ir.edges[0].sourceId == "cap-a"
    assert ir.edges[0].targetId == "cap-b"

    unresolved_count = stats.warnings_by_type.get(WarningType.UNRESOLVED_REFERENCE, 0)
    assert unresolved_count == 0
