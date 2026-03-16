"""Helpers for resolving packaged construct catalogs."""

from __future__ import annotations

import json
import importlib.resources
from pathlib import Path
from typing import Dict, Optional, Any

from cmbenchmark.types.constructs import ConstructDef


_LANGUAGE_TO_PROFILE = {
    "ArchiMate-Archi": "archimate_constructs.json",
    "ArchiMate-XML": "archimate_constructs.json",
    "Ecore": "ecore_constructs.json",
    "UML": "uml_constructs.json",
    "UML-custom1": "uml_constructs.json",
}


def get_construct_profile_path(parser_language: str) -> Optional[Path]:
    """Return the packaged construct profile path for a parser language."""
    profile_file = _LANGUAGE_TO_PROFILE.get(parser_language)
    if not profile_file:
        return None

    try:
        try:
            package = importlib.resources.files("cmbenchmark.measures.construct_profiles")
            file_path = package / profile_file
            if file_path.is_file():
                return Path(file_path)
        except (AttributeError, TypeError):
            with importlib.resources.path("cmbenchmark.measures.construct_profiles", profile_file) as p:
                return Path(p)
    except Exception:
        try:
            import cmbenchmark.measures.construct_profiles as constructs_module

            module_path = Path(constructs_module.__file__).parent
            file_path = module_path / profile_file
            if file_path.exists():
                return file_path
        except Exception:
            pass

    return None


def load_construct_profile_json(parser_language: str) -> Optional[Dict[str, Any]]:
    """Load the raw construct profile JSON for UI introspection."""
    profile_path = get_construct_profile_path(parser_language)
    if not profile_path:
        return None
    with open(profile_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_construct_defs(parser_language: str) -> Optional[Dict[str, ConstructDef]]:
    """Load construct definitions for matching IR models."""
    profile_data = load_construct_profile_json(parser_language)
    if not profile_data:
        return None

    constructs_list = profile_data.get("constructs", [])
    constructs_dict: Dict[str, ConstructDef] = {}
    for construct_item in constructs_list:
        construct_def = ConstructDef(
            id=construct_item["id"],
            description=construct_item.get("description", ""),
            kind=construct_item["kind"],
            match_type=construct_item["match_type"],
            match_data_equals=construct_item.get("match_data_equals", {}),
            meta=construct_item.get("meta", {}),
        )
        constructs_dict[construct_def.id] = construct_def

    return constructs_dict
