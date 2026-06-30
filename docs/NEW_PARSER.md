# Creating a New Parser

This document describes how to add a parser to `cmbenchmark` and make it usable
by the scan, parse, measure, and report pipeline.

## Parser Contract

All parsers implement `BaseParser` from `cmbenchmark.parser.base`.

Minimum parser shape:

```python
from typing import Tuple

from cmbenchmark.parser.base import BaseParser, register_parser
from cmbenchmark.types.exceptions import CannotParseError
from cmbenchmark.types.ir import IR, Node, Edge
from cmbenchmark.types.parsing import ParserRunStats


@register_parser
class MyParser(BaseParser):
    language = "My-Language"
    version = "1.0.0"

    def parse(self, filepath: str) -> Tuple[IR, ParserRunStats]:
        self._start_run()

        if not filepath.endswith(".myext"):
            raise CannotParseError("Not a My-Language model file.")

        ir = IR(
            id="temporary-model-id",
            language=self.language,
            data={"name": ""},
            nodes=[],
            edges=[],
        )

        return ir, self._stats()
```

The parse service overwrites `ir.id` with a deterministic file id and adds
source metadata. The parser should still set a useful temporary id, usually from
the model root or filename, because direct parser tests may inspect it.

## IR Requirements

The parser must return an `IR` with valid `Node` and `Edge` objects.

Node fields:

- `id`: stable, non-empty node id
- `type`: construct/type name used by measures and construct catalogues
- `name`: user-facing label when available, otherwise `""`
- `data`: JSON-serializable metadata

Edge fields:

- `id`: stable, non-empty edge id
- `sourceId`: id of an existing node
- `targetId`: id of an existing node
- `type`: construct/type name used by measures and construct catalogues
- `data`: JSON-serializable metadata

Always run `ir.validate()` in parser tests. Invalid edge endpoints will break
downstream size and construct measures.

Do not add custom dataclass fields to `Node`, `Edge`, or `IR`. Put parser-specific
metadata in `data`.

## Warnings and Skips

Use parser stats to record partial parsing.

Use `self.warn(...)` when an element is kept but something is imperfect:

```python
from cmbenchmark.types.enums import WarningType

self.warn(
    WarningType.UNRESOLVED_REFERENCE,
    "Reference target 'abc' could not be resolved.",
)
```

Use `self.skip_with_warning(...)` when an element is intentionally dropped:

```python
self.skip_with_warning(
    WarningType.UNKNOWN_NODE_TYPE,
    "Skipped unsupported element type 'Foo'.",
)
```

Common warning types are defined in `cmbenchmark.types.enums.WarningType`.
Prefer an existing warning type before adding a new one.

## File Location

Place parser code under `cmbenchmark/parser/<language>/`.

Examples:

- `cmbenchmark/parser/ecore/ecore_parser.py`
- `cmbenchmark/parser/archimate/archimate_archi_parser.py`
- `cmbenchmark/parser/uml/uml_xml_pyecore/parser.py`

Simple parser layout:

```text
cmbenchmark/parser/my_language/
  __init__.py
  my_language_parser.py
```

Parser with runtime resources:

```text
cmbenchmark/parser/my_language/
  __init__.py
  parser.py
  resources/
    ...
```

If runtime resources are needed, include them in `pyproject.toml` package data.

Example:

```toml
[tool.setuptools.package-data]
cmbenchmark = ["parser/my_language/resources/**/*"]
```

## Registration

Parsers are registered through the `@register_parser` decorator at import time.

Add the parser to its package `__init__.py`:

```python
from cmbenchmark.parser.my_language.my_language_parser import MyParser

__all__ = ["MyParser"]
```

Then import it from `cmbenchmark/parser/__init__.py` for registration side
effects:

```python
from .my_language import MyParser  # noqa: F401
```

After this, the parser should appear in:

```python
from cmbenchmark.parser import get_parser, get_all_parsers

assert get_parser("My-Language") is not None
```

## Parser Language Naming

Choose a stable `language` string. This string is part of the public pipeline
contract and appears in:

- benchmark profiles
- generated IR files
- construct catalogue lookup
- API parser lists
- reports and diagnostics
- tests

Use a new language string when the parser emits a materially different IR
representation. For example, `UML` and `UML-XML-PyEcore` are separate because
their IR graph semantics differ.

## Construct Catalogue

Construct measures require a catalogue for the parser language.

Add a JSON file under:

`cmbenchmark/measures/construct_profiles/`

Example:

```json
{
  "language": "My-Language",
  "constructs": [
    {
      "id": "my:Entity",
      "kind": "node_type",
      "match_type": "Entity",
      "match_data_equals": {},
      "meta": {
        "group": "structure"
      },
      "description": "Entity node."
    },
    {
      "id": "my:relatesTo",
      "kind": "edge_type",
      "match_type": "relatesTo",
      "match_data_equals": {},
      "meta": {
        "group": "relationship"
      },
      "description": "Relationship edge."
    }
  ]
}
```

Register it in `cmbenchmark/construct_catalog.py`:

```python
_LANGUAGE_TO_PROFILE = {
    ...
    "My-Language": "my_language_constructs.json",
}
```

Supported construct kinds are implemented by `ConstructDef`:

- `node_type`
- `edge_type`
- `node_edge_type`
- `node_feature`
- `edge_feature`
- `node_edge_feature`

`match_type` is compared to `node.type` or `edge.type`.
`match_data_equals` is compared against `node.data` or `edge.data`.

## Benchmark Profile

Add a profile in `profiles/` when the parser should be runnable from the normal
workflow.

Minimum parse configuration:

```json
{
  "parse": {
    "parser_language": "My-Language"
  }
}
```

A full profile also needs `name`, `version`, `output_path`, `scan`, `measure`,
and `report` sections. Copy the closest existing profile and change:

- `name`
- `output_path`
- `scan.dataset_path`
- `scan.include`
- `parse.parser_language`

## Tests

Add focused parser tests and update integration tests.

Recommended dedicated test file:

`tests/unit/test_my_language_parser.py`

Test direct parser behavior:

```python
def test_my_parser_emits_valid_ir() -> None:
    parser = MyParser()
    ir, stats = parser.parse("tests/unit/fixtures/my_language/model.myext")

    is_valid, errors = ir.validate()
    assert is_valid, errors
    assert ir.language == "My-Language"
    assert len(ir.nodes) > 0
```

Update `tests/unit/test_parser_integration.py`:

- registry contains the parser language
- `get_parser("My-Language")` resolves
- construct catalogue lookup works
- parse service can run with `parser_language="My-Language"`

If the parser has a construct catalogue, add a smoke test that construct
measures run:

```python
from cmbenchmark.construct_catalog import load_construct_defs
from cmbenchmark.measures.construct_measures import compute_construct_measures

constructs = load_construct_defs("My-Language")
dataset, per_model = compute_construct_measures([ir], constructs or {})
assert dataset.d3_m1_construct_presence.constructs_available_count > 0
```

Run:

```bash
.venv/bin/python -m pytest -q tests/unit/test_my_language_parser.py
.venv/bin/python -m pytest -q tests/unit/test_parser_integration.py
.venv/bin/python -m pytest -q tests/unit
```

## Implementation Checklist

1. Create parser package under `cmbenchmark/parser/<language>/`.
2. Implement a `BaseParser` subclass.
3. Decorate the parser class with `@register_parser`.
4. Return valid `IR`, `Node`, `Edge`, and `ParserRunStats`.
5. Raise `CannotParseError` for unsupported or malformed files.
6. Record warnings and skipped elements through parser stats.
7. Export the parser from package `__init__.py`.
8. Import the parser from `cmbenchmark/parser/__init__.py`.
9. Add package-data config if the parser needs runtime resources.
10. Add a construct catalogue.
11. Register the construct catalogue in `construct_catalog.py`.
12. Add a benchmark profile.
13. Add parser and pipeline tests.
14. Run focused and full unit tests.

## Design Guidance

Prefer an IR representation that matches the measures you want to interpret.

If two parsers for the same modeling language expose different graph semantics,
give them different `language` strings and separate construct catalogues. This
keeps reports defensible and prevents silent metric drift.

Use deterministic ids where possible. If source files do not provide ids, derive
ids from stable paths, element positions, or normalized names. Avoid Python
object ids in persisted IR.

Keep parser-specific raw details in `data`, but avoid dumping huge source
fragments into every node. Large `data` payloads inflate IR files and slow
measure/report generation.

For XML-based formats, prefer structured XML APIs and namespace-aware parsing.
For JSON-based formats, parse JSON once and validate expected structure before
building IR.

For parsers that rely on external metamodels or libraries, isolate bootstrap and
resource loading so parser tests can fail with clear diagnostics when resources
are missing.
