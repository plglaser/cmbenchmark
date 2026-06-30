# New UML PyEcore Parser Specification

## Goal

Add a second UML XML/XMI parser backed by PyEcore and the official Eclipse UML2
metamodel resources. This parser is a separate parser variant, not a silent
replacement for the existing handcrafted `UML` parser.

The first supported version uses the fast path: load the UML model with PyEcore
and expose the loaded UML metamodel object graph as IR.

## Parser Identity

- Parser language: `UML-XML-PyEcore`
- Parser type: UML XML/XMI parser using PyEcore
- Parser status: supported parser variant with its own construct catalogue
- Current `UML` parser remains unchanged
- Results from `UML` and `UML-XML-PyEcore` must be treated as different parser
  representations

The parser language must be used consistently in:

- parser registry
- benchmark profiles
- IR `language`
- construct catalogue lookup
- web/API parser list
- tests

## Source Implementation

Port the implementation from:

`/Users/philipp/Projects/model-cleansing/mcp4cm/mcp4cm/parsers/uml_xml_pyecore`

Target location:

`cmbenchmark/parser/uml/uml_xml_pyecore/`

Expected structure:

```text
cmbenchmark/parser/uml/uml_xml_pyecore/
  __init__.py
  parser.py
  metamodel/
    LICENSE
    NOTICE.md
    ORIGIN.md
    plugins/
      ...
```

The implementation should be adapted to `cmbenchmark` rather than copied
verbatim.

## Vendored UML2 Resources

Copy the complete vendored UML2 metamodel resource directory from the original
implementation, including:

- `LICENSE`
- `NOTICE.md`
- `ORIGIN.md`
- Eclipse UML2 `.ecore` files
- UML primitive type libraries
- XML primitive type libraries
- UML profiles
- UML libraries
- UML metamodel pathmap resources

These files are required at runtime. The parser must fail with a clear
`CannotParseError` if any required metamodel file is missing.

Packaging must include these non-Python files. If setuptools does not include
them automatically, add package-data configuration for:

```text
cmbenchmark/parser/uml/uml_xml_pyecore/metamodel/**
```

## Import Adaptation

Replace all original `mcp4cm.*` imports with `cmbenchmark.*` equivalents.

Expected replacements:

- `mcp4cm.parsers.base` -> `cmbenchmark.parser.base`
- `mcp4cm.parsers.diagnostics` -> `cmbenchmark.types.parsing`, `cmbenchmark.types.enums`, `cmbenchmark.types.exceptions`
- `mcp4cm.parsers.ir` -> `cmbenchmark.types.ir`

The parser must implement the existing `BaseParser.parse()` contract:

```python
def parse(self, filepath: str) -> tuple[IR, ParserRunStats]
```

## IR Representation

Use the fast-path metamodel graph IR.

### Nodes

Create one IR node for each loaded UML object reachable through non-derived,
non-transient containment references.

Node fields:

- `id`: original XMI/internal id when available
- `type`: UML metaclass name, for example `Class`, `Property`, `Association`
- `name`: object `name` when available, otherwise empty string
- `data`: serializable non-name attributes and selected metadata

Do not add fields to `Node`. In particular, do not call:

```python
Node(..., eClass=...)
```

If metaclass metadata is needed, store it inside `data`, for example:

```json
{
  "eClass": "LiteralInteger"
}
```

### Edges

Create IR edges from non-derived, non-transient UML references when the target
object is also represented as an IR node.

Edge fields:

- `id`: deterministic parser-generated edge id
- `sourceId`: source object node id
- `targetId`: target object node id
- `type`: UML reference name, for example `packagedElement`, `ownedAttribute`,
  `type`, `generalization`, `memberEnd`
- `data`: reference metadata

Edge `data` should include at least:

```json
{
  "containment": true,
  "many": true,
  "index": 0
}
```

`index` is only required for multi-valued references.

### IR Metadata

IR `data` should include:

- `name`: first/root model name when available
- `rootCount`: number of root objects in the loaded PyEcore resource
- `representation`: `metamodel_graph`
- `parser`: `UML-XML-PyEcore`

The parse service will still add common metadata such as `source_path`,
`source_relpath`, and file size.

## Compatibility and Semantics

This parser intentionally exposes a lower-level UML metamodel graph. It does not
try to normalize the model into the same semantic graph shape as the existing
handcrafted `UML` parser.

Consequences:

- Construct coverage must use a separate `UML-XML-PyEcore` construct catalogue.
- Size and complexity measures describe the metamodel graph representation.
- Results are valid for this parser, but should not be compared directly against
  existing `UML` parser results without noting the representation difference.
- Reports need no special handling as long as measures are computed from valid
  IR.

## Model Loading Behavior

The parser should support common UML XML/XMI variants by registering/mapping:

- Eclipse UML2 5.x namespace
- Eclipse UML2 4.x namespace
- Eclipse UML2 3.x namespace
- Eclipse UML2 2.x namespace where already supported by the source parser
- OMG UML namespace used by the source parser
- `pathmap://UML_LIBRARIES/`
- `pathmap://UML_PROFILES/`
- `pathmap://UML_METAMODELS/`
- primitive type library URIs

The parser may sanitize files before loading when needed.

Allowed compatibility adaptations:

- remove `xmi:Extension` blocks
- remove derived `incoming` and `outgoing` attributes if PyEcore rejects them
- drop `genmymodel://` hrefs that cannot be resolved
- keep only the UML root namespace when sanitizing primitive libraries

Each compatibility adaptation should emit a parser warning with
`WarningType.COMPATIBILITY_ADAPTATION`.

Unresolved non-primitive proxies should emit
`WarningType.UNRESOLVED_REFERENCE`.

## Performance Requirements

The original implementation initializes the UML metamodel lazily per parser
instance and creates a temporary directory for sanitized primitive libraries.
This is acceptable, but the port should avoid obvious repeated work.

Recommended behavior:

- initialize the UML and Types packages lazily
- cache initialized metamodel packages per parser instance
- sanitize primitive libraries once per parser instance
- create a fresh `ResourceSet` per parsed model
- reuse URI mappings when constructing each `ResourceSet`
- cache class-level lists of attributes/references during IR extraction
- avoid resolving every proxy repeatedly
- avoid walking derived/transient references when building the IR

Do not use a global mutable `ResourceSet` for all models unless it is proven
safe. Per-model resource sets reduce cross-model contamination and stale proxy
state.

Potential future optimization:

- process-level shared immutable metamodel bootstrap cache
- optional parser cleanup method for temporary directories
- deterministic edge ids based on source id, reference name, target id, and
  index instead of a counter, if duplicate handling remains clear

## Parser Registration

Add and export the parser so it appears in `get_all_parsers()` and can be
resolved through `get_parser("UML-XML-PyEcore")`.

Expected files to update during implementation:

- `cmbenchmark/parser/uml/__init__.py`
- `cmbenchmark/parser/__init__.py`
- tests that assert builtin parser registry contents

Do not change the current `parser = UMLXMIParser` alias unless there is a
specific reason. The default UML parser should remain the current handcrafted
parser.

## Construct Catalogue

Create a new construct profile for the PyEcore representation:

`cmbenchmark/measures/construct_profiles/uml_xml_pyecore_constructs.json`

Register it in:

`cmbenchmark/construct_catalog.py`

Mapping:

```python
"UML-XML-PyEcore": "uml_xml_pyecore_constructs.json"
```

The construct catalogue must match the metamodel graph IR, not the handcrafted
semantic UML IR.

Recommended catalogue strategy:

- node constructs for UML metaclasses, for example `Class`, `Association`,
  `Property`, `Operation`, `Package`, `Model`, `UseCase`, `Actor`, `Activity`,
  `StateMachine`, `Interaction`, `Component`, `Interface`, `Enumeration`
- edge constructs for important UML references, for example
  `packagedElement`, `ownedAttribute`, `ownedOperation`, `ownedEnd`,
  `memberEnd`, `type`, `generalization`, `interfaceRealization`, `supplier`,
  `client`
- containment constructs may match `data.containment == true`
- group constructs by UML area in `meta.group`, for example `structure`,
  `behavior`, `interaction`, `deployment`, `usecase`, `profile`, `metadata`

The catalogue does not need to be identical in size to the full UML metamodel
for the first version. It should cover the constructs expected in the target
datasets and make unknown types visible through D3 diagnostics.

## Benchmark Profile

Add a profile JSON, for example:

`profiles/profile-modelset-uml-pyecore.json`

Use:

```json
{
  "parse": {
    "parser_language": "UML-XML-PyEcore"
  }
}
```

The profile can otherwise mirror the existing UML profile unless the output path
or enabled measures need to differ.

Recommended output path:

```json
"output_path": "../out/modelset-uml-pyecore"
```

## Testing Requirements

Add focused unit tests for:

- parser registry contains `UML-XML-PyEcore`
- construct catalogue lookup works for `UML-XML-PyEcore`
- parser can parse `tests/unit/fixtures/uml_parser/synthetic_uml.xmi`
- parse service pipeline can run with `parser_language="UML-XML-PyEcore"`
- generated IR validates with `IR.validate()`
- nodes contain only valid `Node` dataclass fields
- construct measures can run using the new construct catalogue

Recommended assertions for the parser fixture:

- at least one node exists
- at least one edge exists
- `ir.language == "UML-XML-PyEcore"`
- at least one expected UML node type appears, for example `Class`
- at least one containment edge has `data.containment == true`

Run at minimum:

```bash
.venv/bin/python -m pytest -q tests/unit/test_parser_integration.py
```

If dedicated tests are added:

```bash
.venv/bin/python -m pytest -q tests/unit/test_uml_xml_pyecore_parser.py
```

## Implementation Checklist

1. Copy parser source into `cmbenchmark/parser/uml/uml_xml_pyecore/`.
2. Copy complete vendored `metamodel/` directory.
3. Preserve metamodel license and notice files.
4. Adapt imports to `cmbenchmark`.
5. Fix `Node` construction incompatibilities.
6. Add parser registration/export.
7. Ensure metamodel resources are included as package data.
8. Add `uml_xml_pyecore_constructs.json`.
9. Register the construct profile in `construct_catalog.py`.
10. Add `profiles/profile-modelset-uml-pyecore.json`.
11. Add parser and pipeline tests.
12. Run unit tests.
13. Compare output against the existing `UML` parser on a small dataset and
    document representation differences.

## Non-Goals for First Version

- Replacing the existing `UML` parser
- Producing IR identical to the handcrafted `UML` parser
- Hiding representation differences in reports
- Full semantic normalization of UML associations, generalizations, and
  stereotypes
- Complete coverage of every UML metaclass in the first construct catalogue

## Future Work

After the fast path is stable, consider a second semantic mapping layer that
turns the PyEcore model into an IR closer to the current handcrafted UML parser.
That would allow better cross-parser comparison while keeping PyEcore loading
robustness.

Possible future additions:

- explicit stereotype/profile extraction into `node.data`
- semantic association/generalization edges in addition to raw reference edges
- configurable IR mode: `metamodel_graph` vs `semantic_graph`
- parser-level performance benchmarks
- side-by-side comparison report for `UML` and `UML-XML-PyEcore`
