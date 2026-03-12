from pathlib import Path
import json
import shutil

from cmbenchmark.parser import get_all_parsers, get_parser
from cmbenchmark.services.scan import scan_dataset
from cmbenchmark.services.parse import parse_from_scan
from cmbenchmark.construct_catalog import get_construct_profile_path, load_construct_defs
from cmbenchmark.types.ir import IR


FIXTURE_XMI = Path(__file__).resolve().parent / "fixtures" / "uml_parser" / "synthetic_uml.xmi"


def test_parser_registry_contains_all_builtin_parsers() -> None:
    parser_languages = {parser_cls.language for parser_cls in get_all_parsers()}

    assert "UML" in parser_languages
    assert "Ecore" in parser_languages
    assert "ArchiMate-Archi" in parser_languages
    assert "ArchiMate-XML" in parser_languages

    assert get_parser("UML") is not None
    assert get_parser("Ecore") is not None


def test_parse_service_pipeline_with_uml(tmp_path: Path) -> None:
    dataset_root = tmp_path / "dataset"
    output_dir = tmp_path / "out"
    dataset_root.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    model_path = dataset_root / "model.xmi"
    shutil.copyfile(FIXTURE_XMI, model_path)

    dataset_info = scan_dataset(str(dataset_root), include=["*.xmi"])
    dataset_info_path = output_dir / "dataset_info.json"
    with open(dataset_info_path, "w", encoding="utf-8") as f:
        json.dump(dataset_info.to_dict(), f, indent=2)

    ir_info = parse_from_scan(
        dataset_info_path=str(dataset_info_path),
        output_dir=str(output_dir),
        parser_language="UML",
    )

    assert ir_info.totals["candidates_in"] == 1
    assert ir_info.totals["parsed_success"] + ir_info.totals["parsed_warning"] == 1
    assert ir_info.totals["parsed_failure"] == 0
    assert len(ir_info.index) == 1

    ir_id = next(iter(ir_info.index.keys()))
    ir_file = output_dir / "ir" / f"{ir_id}.json"
    assert ir_file.exists()

    ir = IR.load(str(ir_file))
    assert ir.language == "UML"
    assert any(node.type == "Class" for node in ir.nodes)


def test_construct_catalog_contains_uml_profile() -> None:
    path = get_construct_profile_path("UML")
    assert path is not None

    constructs = load_construct_defs("UML")
    assert constructs is not None
    assert "uml:Class" in constructs
    assert "uml:Association" in constructs
