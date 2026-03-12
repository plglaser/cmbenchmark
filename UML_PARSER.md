# UML Parser Overview

This document explains how the UML XMI parser works in this project and how UML concepts are mapped into the graph IR (`Node`/`Edge`).

## Scope

The parser is implemented in:

- `cmbenchmark/parser/uml/uml_parser.py`
- `cmbenchmark/parser/uml/handlers/*.py`
- `cmbenchmark/parser/uml/metamodel.py`
- `cmbenchmark/parser/uml/xmi_utils.py`

It parses UML XMI into the IR defined in `cmbenchmark/types/ir.py`.

## Input and Output

Input:

- UML XMI file (`.xmi`)
- Concept type is read from `xsi:type` with fallback to `xmi:type`

Output:

- `IR` object with:
- `ir.data` (model-level metadata)
- `ir.nodes` (`Node(id, type, name, data)`)
- `ir.edges` (`Edge(id, sourceId, targetId, type, data)`)

## Parsing Pipeline

1. Parse XML tree and find the UML model root.
2. Initialize IR with model id/name.
3. Build lookup indexes:
- `id_index`: `xmi:id -> XML element`
- `parent_map`: child element -> parent element
4. Iterate over all model descendants (`model.iter()`).
5. Resolve handler for each element:
- `packagedElement`: use its UML type (`xsi:type`/`xmi:type`)
- specific tags mapped via `TAG_TO_CONCEPT` (`generalization`, `include`, etc.)
- fallback: use element type attribute
6. Execute concept-specific handler.
7. Optionally create `contains` edges for package containment (`ParseOptions.include_packages=True`).
8. Return `IR` and `ParserRunStats`.

## Core Parsing Behavior

Name extraction:

- Prefer `name` attribute.
- Fallback to child `<name>` element.
- Supports `<name xsi:nil="true"/>` as empty name.

Type reference extraction for properties:

- Prefer `type="..."` id reference.
- Fallback to child `<type href="...">` and normalize via `href_to_type_ref(...)`.

Deduplication:

- Nodes are deduplicated by `node.id`.
- Edges are deduplicated by `edge.id`.

Tool-extension elements skipped during parsing:

- `Extension`, `eAnnotations`, `details`

## UML Concept to Graph Mapping

| UML Concept | Recognized As | Graph Artifact | Graph Type | Direction | Key Data Mapping |
|---|---|---|---|---|---|
| `uml:Model` | model element | `ir.data` | N/A | N/A | `modelId`, `name`, `visibility`, `xmi_version`, `imports` |
| `uml:Package` | `packagedElement` | `Node` | `Package` | N/A | `visibility`, `documentation` |
| `uml:Class` | `packagedElement` | `Node` | `Class` | N/A | `visibility`, `isAbstract`, `isLeaf`, `documentation`, parsed `attributes`, parsed `operations` |
| `uml:Interface` | `packagedElement` | `Node` | `Interface` | N/A | `visibility`, `isAbstract`, `documentation`, parsed `operations` |
| `uml:Enumeration` | `packagedElement` | `Node` | `Enumeration` | N/A | `visibility`, `documentation`, parsed `literals` |
| `uml:DataType` | `packagedElement` | `Node` | `DataType` | N/A | `visibility`, `isAbstract`, `documentation` |
| `uml:Component` | `packagedElement` | `Node` | `Component` | N/A | `visibility`, `isAbstract`, `isLeaf`, `documentation` |
| `uml:UseCase` | `packagedElement` or `ownedUseCase` | `Node` | `UseCase` | N/A | `visibility`, `isAbstract`, `isLeaf`, `documentation`, `extensionPoints` |
| `uml:Actor` | `packagedElement` | `Node` | `Actor` | N/A | `visibility`, `isAbstract`, `isLeaf` |
| `uml:Association` | `packagedElement` | `Edge` | `Association` | `end1.typeId -> end2.typeId` | `name`, `end1`, `end2` payloads (multiplicity, aggregation, flags, etc.) |
| `uml:Generalization` | tag `generalization` or typed element | `Edge` | `Generalization` | `specific -> general` | `general`, `specific`, optional `name` |
| `uml:InterfaceRealization` | tag `interfaceRealization` or typed element | `Edge` | `InterfaceRealization` | implementing classifier/client -> contract/supplier | `client`, `supplier`, `implementingClassifier`, `contract`, optional `name` |
| `uml:Dependency` | `packagedElement` | `Edge` | `Dependency` | `client -> supplier` | optional `name`; supports multi-client/supplier cartesian expansion |
| `uml:Usage` | `packagedElement` | `Edge` | `Usage` | `client -> supplier` | optional `name`; supports multi-client/supplier cartesian expansion |
| `uml:Include` | tag `include` | `Edge` | `includes` | `includingCase -> addition` | no extra data |
| `uml:Extend` | tag `extend` | `Edge` | `extends` | `extension -> extendedCase` | `extensionLocation`, resolved `extensionPoint` name (if available) |

## Additional Derived Graph Edges

Containment edge generation (`type="contains"`):

- Emitted between packages and contained elements.
- For package -> package, data is empty.
- For package -> non-package, data contains `elementType`.
- Enabled by `ParseOptions.include_packages`.

## Attribute/Child Parsing Details

Class attributes (`ownedAttribute`, excluding association ends):

- Captures `id`, optional `name`, type (`typeRef` or normalized external `type`), multiplicity (`lower`, `upper`), visibility, boolean flags, aggregation, default value.

Operations (`ownedOperation`) and parameters (`ownedParameter`):

- Reused across class/interface parsing via base helper methods.
- Captures operation name/visibility/flags and parameter direction/type/multiplicity.

Enumeration literals (`ownedLiteral`):

- Captures literal `id` and optional `name`.

Use case extension points (`extensionPoint`):

- Captures `id`, optional `name`, `useCaseRef`, and selected attributes.

## Warnings, Skips, and Diagnostics

The parser produces `ParserRunStats` consumed by parse-stage model diagnostics (`cmbenchmark/services/parse.py`).

Current skip integration:

- Broken associations with fewer than 2 resolved typed ends are skipped and recorded as:
- `WarningType.MISSING_EDGE_ENDPOINT`
- `elements_skipped += 1`
- warning message stored in `warning_msgs`

Unresolved/unsupported packaged element types:

- Printed as `[UNHANDLED ELEMENT] ...` when not in ignore list.
- Certain UML types are intentionally ignored (for example Activity/StateMachine/Interaction families listed in `IGNORED_UNHANDLED_ELEMENTS`).

## Handler Resolution Rules

Resolution order per XML element:

1. If element tag is `packagedElement`: use UML type (`xsi:type`/`xmi:type`).
2. Else if tag is mapped in `TAG_TO_CONCEPT`: use mapped UML concept.
3. Else fallback to UML type on that element.

This allows parsing of nested non-`packagedElement` relations like `generalization`, `include`, and `extend`.

## Notes on IR IDs

Inside the UML parser, `IR.id` starts as model id (`xmi:id`).
In the parse service, this id is replaced with a deterministic file hash before saving IR files.

## Extending the UML Parser

To add a new UML concept:

1. Add a concept spec to `SUPPORTED_UML_CONCEPTS` in `metamodel.py`.
2. Implement a new handler in `handlers/` with `element_type` and `handle(...)`.
3. Register the handler in `UMLXMIParser._get_default_handlers()`.
4. Add tag mapping in `TAG_TO_CONCEPT` if the concept appears as a non-`packagedElement` child tag.
5. Add/adjust unit tests in `tests/unit/test_uml_parser.py`.
