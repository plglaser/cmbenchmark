from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
import xml.etree.ElementTree as ET

import pytest

from cmbenchmark.parser.uml.metamodel import SUPPORTED_UML_CONCEPTS
from cmbenchmark.parser.uml.uml_parser import UMLXMIParser
from cmbenchmark.parser.uml.xmi_utils import XMI_NS, XSI_NS, UML_NS


# Keep namespace prefixes stable in serialized synthetic XMI.
ET.register_namespace("xmi", XMI_NS)
ET.register_namespace("xsi", XSI_NS)
ET.register_namespace("uml", UML_NS)

XMI_ID = f"{{{XMI_NS}}}id"
XSI_TYPE = f"{{{XSI_NS}}}type"

PROFILE_PATH = (
    Path(__file__).resolve().parents[2]
    / "cmbenchmark"
    / "measures"
    / "construct_profiles"
    / "uml_constructs.json"
)
CONCEPT_IDS = [item["id"] for item in json.loads(PROFILE_PATH.read_text(encoding="utf-8"))["constructs"]]


BOOL_ATTRS = {
    "isAbstract",
    "isLeaf",
    "isReadOnly",
    "isSingleExecution",
    "isReentrant",
    "isStatic",
    "isQuery",
    "isUnique",
    "isOrdered",
    "isDerived",
    "isID",
}

DEFAULT_ATTR_VALUES = {
    "visibility": "private",
    "href": "http://example.com/PrimitiveTypes.xmi#//Integer",
    "templateParameter": "tp1 tp2",
    "owningTemplateParameter": "otp1",
    "memberEnd": "{id}_end1 {id}_end2",
    "navigableOwnedEnd": "{id}_end1 {id}_end2",
    "informationSource": "c_src",
    "informationTarget": "c_tgt",
    "classifier": "c_src c_tgt",
    "incoming": "flow_in_1 flow_in_2",
    "outgoing": "flow_out_1 flow_out_2",
    "node": "n1 n2",
    "covered": "lifeline1 lifeline2",
    "coveredBy": "mos1 mos2",
    "enclosingInteraction": "int_case",
    "start": "mos1",
    "finish": "mos2",
    "container": "region1",
    "stateMachine": "sm_case",
    "state": "state1",
    "kind": "external",
    "interactionOperator": "alt",
    "represents": "part1",
    "decomposedAs": "int_case",
    "symbol": "+",
    "value": "42",
    "fileName": "artifact.bin",
    "source": "n1",
    "target": "n2",
    "activity": "act_case",
    "sendEvent": "mos1",
    "receiveEvent": "mos2",
    "messageSort": "synchCall",
    "messageKind": "complete",
    "connector": "conn1",
    "general": "c_tgt",
    "specific": "c_src",
    "client": "c_src",
    "supplier": "c_tgt",
    "implementingClassifier": "c_src",
    "contract": "i_contract",
    "includingCase": "uc_src",
    "addition": "uc_tgt",
    "extension": "uc_src",
    "extendedCase": "uc_tgt",
    "extensionLocation": "ep1",
    "instance": "inst1",
    "parameteredElement": "param_elem_1",
    "signature": "sig1",
    "constrainingClassifier": "c_src c_tgt",
    "parameter": "tp1 tp2",
}

OWNED_NODE_TYPES = {
    "uml:ActivityFinalNode",
    "uml:ActivityParameterNode",
    "uml:CallBehaviorAction",
    "uml:CentralBufferNode",
    "uml:DataStoreNode",
    "uml:DecisionNode",
    "uml:FlowFinalNode",
    "uml:ForkNode",
    "uml:InitialNode",
    "uml:JoinNode",
    "uml:MergeNode",
    "uml:OpaqueAction",
    "uml:SendSignalAction",
}

FRAGMENT_TYPES = {
    "uml:BehaviorExecutionSpecification",
    "uml:CombinedFragment",
    "uml:ExecutionOccurrenceSpecification",
    "uml:MessageOccurrenceSpecification",
}

SUBVERTEX_TYPES = {
    "uml:FinalState",
    "uml:Pseudostate",
    "uml:State",
}


def _parse_xmi(tmp_path: Path, filename: str, xmi: str):
    path = tmp_path / filename
    path.write_text(xmi, encoding="utf-8")
    parser = UMLXMIParser()
    return parser.parse(str(path))


def _nodes_by_id(ir):
    return {node.id: node for node in ir.nodes}


def _edges_by_id(ir):
    return {edge.id: edge for edge in ir.edges}


# ---------- XML construction helpers ----------
def _new_elem(
    tag: str,
    *,
    xmi_id: str | None = None,
    xsi_type: str | None = None,
    attrs: Dict[str, str] | None = None,
) -> ET.Element:
    elem = ET.Element(tag)
    if xmi_id:
        elem.set(XMI_ID, xmi_id)
    if xsi_type:
        elem.set(XSI_TYPE, xsi_type)
    for key, value in (attrs or {}).items():
        elem.set(key, value)
    return elem


def _add_packaged(model: ET.Element, uml_type: str, xmi_id: str, name: str) -> ET.Element:
    elem = _new_elem("packagedElement", xmi_id=xmi_id, xsi_type=uml_type, attrs={"name": name})
    model.append(elem)
    return elem


def _create_model_root() -> tuple[ET.Element, ET.Element]:
    root = _new_elem(f"{{{XMI_NS}}}XMI")
    model = _new_elem(f"{{{UML_NS}}}Model", xmi_id="m1", attrs={"name": "SyntheticModel"})
    root.append(model)
    return root, model


def _add_baseline_elements(model: ET.Element) -> None:
    # Core references shared by many synthetic concept examples.
    _add_packaged(model, "uml:Class", "c_src", "Source")
    _add_packaged(model, "uml:Class", "c_tgt", "Target")
    _add_packaged(model, "uml:Class", "c_alt", "AltSource")
    _add_packaged(model, "uml:Class", "c_alt_tgt", "AltTarget")
    _add_packaged(model, "uml:Interface", "i_contract", "Contract")

    uc_src = _add_packaged(model, "uml:UseCase", "uc_src", "UseCaseSource")
    uc_src.append(_new_elem("extensionPoint", xmi_id="ep1", attrs={"name": "EP1", "useCase": "uc_src"}))
    _add_packaged(model, "uml:UseCase", "uc_tgt", "UseCaseTarget")

    interaction = _add_packaged(model, "uml:Interaction", "int_base", "InteractionBase")
    interaction.append(_new_elem("lifeline", xmi_id="lifeline1", attrs={"name": "L1", "interaction": "int_base"}))
    interaction.append(_new_elem("lifeline", xmi_id="lifeline2", attrs={"name": "L2", "interaction": "int_base"}))
    interaction.append(
        _new_elem(
            "fragment",
            xmi_id="mos1",
            xsi_type="uml:MessageOccurrenceSpecification",
            attrs={"covered": "lifeline1", "enclosingInteraction": "int_base"},
        )
    )
    interaction.append(
        _new_elem(
            "fragment",
            xmi_id="mos2",
            xsi_type="uml:MessageOccurrenceSpecification",
            attrs={"covered": "lifeline2", "enclosingInteraction": "int_base"},
        )
    )

    sm = _add_packaged(model, "uml:StateMachine", "sm_base", "StateMachineBase")
    region = _new_elem("region", xmi_id="region1", attrs={"stateMachine": "sm_base"})
    sm.append(region)
    region.append(_new_elem("subvertex", xmi_id="state1", xsi_type="uml:State", attrs={"name": "S1", "container": "region1"}))
    region.append(_new_elem("subvertex", xmi_id="state2", xsi_type="uml:State", attrs={"name": "S2", "container": "region1"}))

    activity = _add_packaged(model, "uml:Activity", "act_base", "ActivityBase")
    activity.append(_new_elem("ownedNode", xmi_id="n1", xsi_type="uml:OpaqueAction", attrs={"name": "N1"}))
    activity.append(_new_elem("ownedNode", xmi_id="n2", xsi_type="uml:OpaqueAction", attrs={"name": "N2"}))

    instance = _add_packaged(model, "uml:InstanceSpecification", "inst1", "InstanceOne")
    instance.append(_new_elem("slot", xmi_id="slot1", attrs={"owningInstance": "inst1", "definingFeature": "feature1"}))


def _attr_value(attr_name: str, concept_id: str, elem_id: str) -> str:
    if attr_name in BOOL_ATTRS:
        return "true"
    if attr_name == "kind" and concept_id == "uml:Pseudostate":
        return "initial"
    raw = DEFAULT_ATTR_VALUES.get(attr_name, f"{attr_name}_{elem_id}")
    return raw.format(id=elem_id)


def _concept_attrs(concept_id: str, elem_id: str) -> Dict[str, str]:
    attrs: Dict[str, str] = {}
    for attr_name in sorted(SUPPORTED_UML_CONCEPTS[concept_id].allowed_attributes):
        if attr_name == "name":
            attrs[attr_name] = f"{concept_id.split(':', 1)[1]}Name"
        else:
            attrs[attr_name] = _attr_value(attr_name, concept_id, elem_id)
    return attrs


def _append_docs_if_supported(concept_id: str, target: ET.Element) -> None:
    contract = SUPPORTED_UML_CONCEPTS[concept_id].parse_contract
    if contract and contract.include_documentation and concept_id != "uml:Model":
        target.append(
            _new_elem(
                "ownedComment",
                xmi_id=f"{target.attrib.get(XMI_ID, 'elem')}_doc",
                attrs={"body": "Doc body"},
            )
        )


def _append_child_ref_tags(concept_id: str, elem_id: str, target: ET.Element) -> Dict[str, list[str]]:
    expected: Dict[str, list[str]] = {}
    contract = SUPPORTED_UML_CONCEPTS[concept_id].parse_contract
    if contract is None:
        return expected

    for child_tag in contract.child_ref_tags:
        child_id = f"{elem_id}_{child_tag}_ref"
        target.append(_new_elem(child_tag, xmi_id=child_id))
        data_key = contract.child_ref_rename_map.get(child_tag, f"{child_tag}Refs")
        expected[data_key] = [child_id]

    return expected


# ---------- concept placement ----------
def _place_model(model: ET.Element, attrs: Dict[str, str]) -> ET.Element:
    for key, value in attrs.items():
        model.set(key, value)
    model.append(
        _new_elem(
            "packageImport",
            xmi_id="pi_case",
            attrs={"importedPackage": "http://example.com/UML/PrimitiveTypes.xmi#/"},
        )
    )
    return model


def _place_owned_node(model: ET.Element, concept_id: str, elem_id: str, attrs: Dict[str, str]) -> ET.Element:
    activity = _add_packaged(model, "uml:Activity", "act_case", "ActivityCase")
    attrs["activity"] = "act_case"
    attrs.setdefault("source", "n1")
    attrs.setdefault("target", "n2")
    node = _new_elem("ownedNode", xmi_id=elem_id, xsi_type=concept_id, attrs=attrs)
    activity.append(node)
    return node


def _place_activity_partition(model: ET.Element, concept_id: str, elem_id: str, attrs: Dict[str, str]) -> ET.Element:
    activity = _add_packaged(model, "uml:Activity", "act_case", "ActivityCase")
    group = _new_elem("ownedGroup", xmi_id=elem_id, xsi_type=concept_id, attrs=attrs)
    activity.append(group)
    return group


def _place_activity_edge(model: ET.Element, concept_id: str, elem_id: str, attrs: Dict[str, str]) -> ET.Element:
    activity = _add_packaged(model, "uml:Activity", "act_case", "ActivityCase")
    attrs["source"] = "n1"
    attrs["target"] = "n2"
    attrs["activity"] = "act_case"
    edge = _new_elem("edge", xmi_id=elem_id, xsi_type=concept_id, attrs=attrs)
    activity.append(edge)
    return edge


def _place_generalization(model: ET.Element, elem_id: str, attrs: Dict[str, str]) -> ET.Element:
    owner = _add_packaged(model, "uml:Class", "c_src", "SourceOwner")
    attrs["specific"] = "c_src"
    attrs["general"] = "c_tgt"
    rel = _new_elem("generalization", xmi_id=elem_id, attrs=attrs)
    owner.append(rel)
    return rel


def _place_interface_realization(model: ET.Element, elem_id: str, attrs: Dict[str, str]) -> ET.Element:
    owner = _add_packaged(model, "uml:Class", "c_src", "SourceOwner")
    attrs["implementingClassifier"] = "c_src"
    attrs["contract"] = "i_contract"
    attrs["client"] = "c_src"
    attrs["supplier"] = "i_contract"
    rel = _new_elem("interfaceRealization", xmi_id=elem_id, attrs=attrs)
    owner.append(rel)
    return rel


def _place_usecase_relation(model: ET.Element, concept_id: str, elem_id: str, attrs: Dict[str, str]) -> ET.Element:
    uc_src = _add_packaged(model, "uml:UseCase", "uc_src", "UseCaseSource")
    uc_src.append(_new_elem("extensionPoint", xmi_id="ep1", attrs={"name": "EP1", "useCase": "uc_src"}))
    _add_packaged(model, "uml:UseCase", "uc_tgt", "UseCaseTarget")

    if concept_id == "uml:Include":
        attrs["includingCase"] = "uc_src"
        attrs["addition"] = "uc_tgt"
        rel = _new_elem("include", xmi_id=elem_id, attrs=attrs)
    else:
        attrs["extension"] = "uc_src"
        attrs["extendedCase"] = "uc_tgt"
        attrs["extensionLocation"] = "ep1"
        rel = _new_elem("extend", xmi_id=elem_id, attrs=attrs)

    uc_src.append(rel)
    return rel


def _place_region(model: ET.Element, elem_id: str, attrs: Dict[str, str]) -> ET.Element:
    sm = _add_packaged(model, "uml:StateMachine", "sm_case", "StateMachineCase")
    attrs["stateMachine"] = "sm_case"
    region = _new_elem("region", xmi_id=elem_id, attrs=attrs)
    sm.append(region)
    return region


def _place_transition(model: ET.Element, elem_id: str, attrs: Dict[str, str]) -> ET.Element:
    sm = _add_packaged(model, "uml:StateMachine", "sm_case", "StateMachineCase")
    region = _new_elem("region", xmi_id="region1", attrs={"stateMachine": "sm_case"})
    sm.append(region)
    region.append(_new_elem("subvertex", xmi_id="state1", xsi_type="uml:State", attrs={"name": "S1", "container": "region1"}))
    region.append(_new_elem("subvertex", xmi_id="state2", xsi_type="uml:State", attrs={"name": "S2", "container": "region1"}))

    attrs["source"] = "state1"
    attrs["target"] = "state2"
    attrs["container"] = "region1"
    transition = _new_elem("transition", xmi_id=elem_id, attrs=attrs)
    region.append(transition)
    return transition


def _place_interaction_related(model: ET.Element, concept_id: str, elem_id: str, attrs: Dict[str, str]) -> ET.Element:
    interaction_id = elem_id if concept_id == "uml:Interaction" else "int_case"
    interaction = _add_packaged(model, "uml:Interaction", interaction_id, "InteractionCase")

    interaction.append(_new_elem("lifeline", xmi_id="lifeline1", attrs={"name": "L1", "interaction": interaction_id}))
    interaction.append(_new_elem("lifeline", xmi_id="lifeline2", attrs={"name": "L2", "interaction": interaction_id}))
    interaction.append(
        _new_elem(
            "fragment",
            xmi_id="mos1",
            xsi_type="uml:MessageOccurrenceSpecification",
            attrs={"covered": "lifeline1", "enclosingInteraction": interaction_id},
        )
    )
    interaction.append(
        _new_elem(
            "fragment",
            xmi_id="mos2",
            xsi_type="uml:MessageOccurrenceSpecification",
            attrs={"covered": "lifeline2", "enclosingInteraction": interaction_id},
        )
    )

    if concept_id == "uml:Interaction":
        for key, value in attrs.items():
            interaction.set(key, value)
        return interaction

    if concept_id == "uml:Lifeline":
        attrs["interaction"] = interaction_id
        node = _new_elem("lifeline", xmi_id=elem_id, attrs=attrs)
        interaction.append(node)
        return node

    if concept_id == "uml:Message":
        attrs["interaction"] = interaction_id
        attrs["sendEvent"] = "mos1"
        attrs["receiveEvent"] = "mos2"
        edge = _new_elem("message", xmi_id=elem_id, attrs=attrs)
        interaction.append(edge)
        return edge

    if concept_id == "uml:InteractionOperand":
        attrs["enclosingInteraction"] = interaction_id
        attrs["covered"] = "lifeline1"
        attrs["guard"] = "guard_attr"
        combined = _new_elem(
            "fragment",
            xmi_id="cf_parent",
            xsi_type="uml:CombinedFragment",
            attrs={"enclosingInteraction": interaction_id},
        )
        interaction.append(combined)
        operand = _new_elem("operand", xmi_id=elem_id, attrs=attrs)
        combined.append(operand)
        return operand

    attrs["enclosingInteraction"] = interaction_id
    if concept_id == "uml:BehaviorExecutionSpecification":
        attrs["covered"] = "lifeline1"
        attrs["start"] = "mos1"
        attrs["finish"] = "mos2"
    if concept_id == "uml:ExecutionOccurrenceSpecification":
        attrs["covered"] = "lifeline2"
    if concept_id == "uml:MessageOccurrenceSpecification":
        attrs["covered"] = "lifeline1"
        attrs.setdefault("message", "msg_ref")
        attrs.setdefault("toAfter", "mos2")
    if concept_id == "uml:CombinedFragment":
        attrs["covered"] = "lifeline1"

    fragment = _new_elem("fragment", xmi_id=elem_id, xsi_type=concept_id, attrs=attrs)
    interaction.append(fragment)
    return fragment


def _place_subvertex(model: ET.Element, concept_id: str, elem_id: str, attrs: Dict[str, str]) -> ET.Element:
    sm = _add_packaged(model, "uml:StateMachine", "sm_case", "StateMachineCase")
    region = _new_elem("region", xmi_id="region1", attrs={"stateMachine": "sm_case"})
    sm.append(region)
    attrs["container"] = "region1"
    subvertex = _new_elem("subvertex", xmi_id=elem_id, xsi_type=concept_id, attrs=attrs)
    region.append(subvertex)
    return subvertex


def _place_literal_value(model: ET.Element, concept_id: str, elem_id: str, attrs: Dict[str, str]) -> ET.Element:
    if concept_id in {"uml:LiteralInteger", "uml:LiteralUnlimitedNatural", "uml:LiteralBoolean"}:
        cls = _add_packaged(model, "uml:Class", "class_case", "ClassCase")
        owner = _new_elem("ownedAttribute", xmi_id="attr_case", attrs={"name": "attr"})
        cls.append(owner)

        tag = {
            "uml:LiteralInteger": "lowerValue",
            "uml:LiteralUnlimitedNatural": "upperValue",
            "uml:LiteralBoolean": "defaultValue",
        }[concept_id]
        literal = _new_elem(tag, xmi_id=elem_id, xsi_type=concept_id, attrs=attrs)
        owner.append(literal)
        return literal

    if concept_id in {"uml:Expression", "uml:InstanceValue", "uml:LiteralReal"}:
        inst = _add_packaged(model, "uml:InstanceSpecification", "inst_case", "InstanceCase")
        slot = _new_elem("slot", xmi_id="slot_case", attrs={"owningInstance": "inst_case", "definingFeature": "feature1"})
        inst.append(slot)
        value = _new_elem("value", xmi_id=elem_id, xsi_type=concept_id, attrs=attrs)
        slot.append(value)
        return value

    # LiteralString
    activity = _add_packaged(model, "uml:Activity", "act_case", "ActivityCase")
    flow = _new_elem(
        "edge",
        xmi_id="edge_case",
        xsi_type="uml:ControlFlow",
        attrs={"source": "n1", "target": "n2", "activity": "act_case"},
    )
    activity.append(flow)
    guard = _new_elem("guard", xmi_id=elem_id, xsi_type=concept_id, attrs=attrs)
    flow.append(guard)
    return guard


def _place_template_related(model: ET.Element, concept_id: str, elem_id: str, attrs: Dict[str, str]) -> ET.Element:
    cls = _add_packaged(model, "uml:Class", "class_case", "ClassCase")

    if concept_id == "uml:ClassifierTemplateParameter":
        signature = _new_elem("ownedTemplateSignature", xmi_id="sig1", xsi_type="uml:RedefinableTemplateSignature")
        cls.append(signature)
        attrs["signature"] = "sig1"
        param = _new_elem("ownedParameter", xmi_id=elem_id, xsi_type=concept_id, attrs=attrs)
        signature.append(param)
        return param

    # RedefinableTemplateSignature
    attrs["parameter"] = "tp1 tp2"
    signature = _new_elem("ownedTemplateSignature", xmi_id=elem_id, xsi_type=concept_id, attrs=attrs)
    signature.append(_new_elem("ownedParameter", xmi_id="tp1", xsi_type="uml:ClassifierTemplateParameter"))
    signature.append(_new_elem("ownedParameter", xmi_id="tp2", xsi_type="uml:ClassifierTemplateParameter"))
    cls.append(signature)
    return signature


def _place_misc_special(model: ET.Element, concept_id: str, elem_id: str, attrs: Dict[str, str]) -> ET.Element:
    if concept_id == "uml:Port":
        cls = _add_packaged(model, "uml:Class", "class_case", "ClassCase")
        port = _new_elem("ownedAttribute", xmi_id=elem_id, xsi_type="uml:Port", attrs=attrs)
        cls.append(port)
        return port

    if concept_id == "uml:EnumerationLiteral":
        enum = _add_packaged(model, "uml:Enumeration", "enum_case", "EnumCase")
        literal = _new_elem("ownedLiteral", xmi_id=elem_id, xsi_type="uml:EnumerationLiteral", attrs=attrs)
        enum.append(literal)
        return literal

    # ExecutionEnvironment
    node = _add_packaged(model, "uml:Node", "node_case", "NodeCase")
    nested = _new_elem("nestedNode", xmi_id=elem_id, xsi_type="uml:ExecutionEnvironment", attrs=attrs)
    node.append(nested)
    return nested


def _place_association_like(model: ET.Element, concept_id: str, elem_id: str, attrs: Dict[str, str]) -> ET.Element:
    assoc = _new_elem("packagedElement", xmi_id=elem_id, xsi_type=concept_id, attrs=attrs)
    assoc.append(_new_elem("ownedEnd", xmi_id=f"{elem_id}_end1", attrs={"name": "end1", "type": "c_src"}))
    assoc.append(_new_elem("ownedEnd", xmi_id=f"{elem_id}_end2", attrs={"name": "end2", "type": "c_tgt"}))
    model.append(assoc)
    return assoc


def _place_default_packaged(model: ET.Element, concept_id: str, elem_id: str, attrs: Dict[str, str]) -> ET.Element:
    elem = _new_elem("packagedElement", xmi_id=elem_id, xsi_type=concept_id, attrs=attrs)
    model.append(elem)
    return elem


def _insert_supported_concept(
    model: ET.Element,
    concept_id: str,
    elem_id: str,
    attrs: Dict[str, str],
) -> tuple[ET.Element, Dict[str, str], Dict[str, list[str]]]:
    if concept_id == "uml:Model":
        target = _place_model(model, attrs)
    elif concept_id in OWNED_NODE_TYPES:
        target = _place_owned_node(model, concept_id, elem_id, attrs)
    elif concept_id == "uml:ActivityPartition":
        target = _place_activity_partition(model, concept_id, elem_id, attrs)
    elif concept_id in {"uml:ControlFlow", "uml:ObjectFlow"}:
        target = _place_activity_edge(model, concept_id, elem_id, attrs)
    elif concept_id == "uml:Generalization":
        target = _place_generalization(model, elem_id, attrs)
    elif concept_id == "uml:InterfaceRealization":
        target = _place_interface_realization(model, elem_id, attrs)
    elif concept_id in {"uml:Include", "uml:Extend"}:
        target = _place_usecase_relation(model, concept_id, elem_id, attrs)
    elif concept_id == "uml:Region":
        target = _place_region(model, elem_id, attrs)
    elif concept_id == "uml:Transition":
        target = _place_transition(model, elem_id, attrs)
    elif concept_id in {"uml:Interaction", "uml:Lifeline", "uml:Message", "uml:InteractionOperand"} | FRAGMENT_TYPES:
        target = _place_interaction_related(model, concept_id, elem_id, attrs)
    elif concept_id in SUBVERTEX_TYPES:
        target = _place_subvertex(model, concept_id, elem_id, attrs)
    elif concept_id in {
        "uml:LiteralInteger",
        "uml:LiteralUnlimitedNatural",
        "uml:LiteralBoolean",
        "uml:Expression",
        "uml:InstanceValue",
        "uml:LiteralReal",
        "uml:LiteralString",
    }:
        target = _place_literal_value(model, concept_id, elem_id, attrs)
    elif concept_id in {"uml:ClassifierTemplateParameter", "uml:RedefinableTemplateSignature"}:
        target = _place_template_related(model, concept_id, elem_id, attrs)
    elif concept_id in {"uml:Port", "uml:EnumerationLiteral", "uml:ExecutionEnvironment"}:
        target = _place_misc_special(model, concept_id, elem_id, attrs)
    elif concept_id in {"uml:Association", "uml:CommunicationPath"}:
        target = _place_association_like(model, concept_id, elem_id, attrs)
    else:
        target = _place_default_packaged(model, concept_id, elem_id, attrs)

    _append_docs_if_supported(concept_id, target)
    child_refs = _append_child_ref_tags(concept_id, elem_id, target)
    return target, attrs, child_refs


def _build_supported_case_xmi(concept_id: str, elem_id: str) -> tuple[str, Dict[str, str], Dict[str, list[str]]]:
    root, model = _create_model_root()
    _add_baseline_elements(model)

    attrs = _concept_attrs(concept_id, elem_id)
    _, attrs, child_refs = _insert_supported_concept(model, concept_id, elem_id, attrs)

    xml_text = ET.tostring(root, encoding="unicode", short_empty_elements=False)
    xmi = f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_text}\n'
    return xmi, attrs, child_refs


# ---------- assertions ----------
def _assert_supported_artifact(
    concept_id: str,
    elem_id: str,
    ir,
    attrs: Dict[str, str],
    child_refs: Dict[str, list[str]],
) -> None:
    concept = SUPPORTED_UML_CONCEPTS[concept_id]
    contract = concept.parse_contract
    assert contract is not None

    if concept_id == "uml:Model":
        assert ir.data["modelId"] == "m1"
        assert ir.data.get("name") == attrs.get("name", "SyntheticModel")
        if "visibility" in attrs:
            assert ir.data["visibility"] == attrs["visibility"]
        assert ir.data["imports"] == ["http://example.com/UML/PrimitiveTypes.xmi#/"]
        return

    nodes = _nodes_by_id(ir)
    edges = _edges_by_id(ir)

    if concept.produces.startswith("Node("):
        assert elem_id in nodes, f"Missing node for {concept_id}"
        node = nodes[elem_id]
        assert node.type == (contract.node_type or node.type)
        if contract.include_name and "name" in attrs:
            assert node.name == attrs["name"]
        data = node.data
    else:
        assert elem_id in edges, f"Missing edge for {concept_id}"
        edge = edges[elem_id]
        assert edge.type == (contract.edge_type or edge.type)

        if contract.source_attr and contract.target_attr:
            assert edge.sourceId == attrs[contract.source_attr].split()[0]
            assert edge.targetId == attrs[contract.target_attr].split()[0]

        data = edge.data
        if contract.include_name and "name" in attrs:
            assert data.get("name") == attrs["name"]

    for attr_name in contract.scalar_attrs:
        if attr_name in attrs:
            data_key = contract.rename_map.get(attr_name, attr_name)
            assert data.get(data_key) == attrs[attr_name]

    for attr_name in contract.boolean_attrs:
        if attr_name in attrs:
            data_key = contract.rename_map.get(attr_name, attr_name)
            assert data.get(data_key) is True

    for attr_name in contract.list_attrs:
        if attr_name in attrs:
            data_key = contract.rename_map.get(attr_name, attr_name)
            assert data.get(data_key) == attrs[attr_name].split()

    for data_key, expected_ids in child_refs.items():
        assert data.get(data_key) == expected_ids

    if contract.include_documentation and concept_id != "uml:Model":
        assert "Doc body" in data.get("documentation", "")


def _assert_composition_case(tmp_path: Path) -> None:
    xmi = """<?xml version="1.0" encoding="UTF-8"?>
<xmi:XMI xmlns:xmi="http://schema.omg.org/spec/XMI/2.1"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xmlns:uml="http://www.eclipse.org/uml2/5.0.0/UML">
  <uml:Model xmi:id="m1" name="SyntheticModel">
    <packagedElement xsi:type="uml:Class" xmi:id="c_src" name="Source"/>
    <packagedElement xsi:type="uml:Class" xmi:id="c_tgt" name="Target"/>
    <packagedElement xsi:type="uml:Association" xmi:id="comp_assoc" name="WholePart"
                     memberEnd="comp_assoc_end1 comp_assoc_end2"
                     navigableOwnedEnd="comp_assoc_end1 comp_assoc_end2">
      <ownedEnd xmi:id="comp_assoc_end1" name="whole" type="c_src" aggregation="composite"/>
      <ownedEnd xmi:id="comp_assoc_end2" name="part" type="c_tgt"/>
    </packagedElement>
  </uml:Model>
</xmi:XMI>
"""
    ir, _ = _parse_xmi(tmp_path, "uml_composition_case.xmi", xmi)
    edge = _edges_by_id(ir)["comp_assoc"]

    assert edge.type == "Composition"
    assert edge.sourceId == "c_src"
    assert edge.targetId == "c_tgt"
    assert edge.data["associationId"] == "comp_assoc"
    assert edge.data["wholeEndId"] == "comp_assoc_end1"
    assert edge.data["partEndId"] == "comp_assoc_end2"


def _assert_contains_case(tmp_path: Path) -> None:
    xmi = """<?xml version="1.0" encoding="UTF-8"?>
<xmi:XMI xmlns:xmi="http://schema.omg.org/spec/XMI/2.1"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xmlns:uml="http://www.eclipse.org/uml2/5.0.0/UML">
  <uml:Model xmi:id="m1" name="SyntheticModel">
    <packagedElement xsi:type="uml:Package" xmi:id="pkg_case" name="Pkg">
      <packagedElement xsi:type="uml:Class" xmi:id="c_in_pkg" name="ClassInPkg"/>
    </packagedElement>
  </uml:Model>
</xmi:XMI>
"""
    ir, _ = _parse_xmi(tmp_path, "uml_contains_case.xmi", xmi)
    edge = _edges_by_id(ir)["pkg_case__contains__c_in_pkg"]

    assert edge.type == "contains"
    assert edge.sourceId == "pkg_case"
    assert edge.targetId == "c_in_pkg"
    assert edge.data["elementType"] == "uml:Class"


def _run_concept_case(tmp_path: Path, concept_id: str) -> None:
    if concept_id == "uml:Composition":
        _assert_composition_case(tmp_path)
        return

    if concept_id == "uml:Contains":
        _assert_contains_case(tmp_path)
        return

    assert concept_id in SUPPORTED_UML_CONCEPTS
    elem_id = f"elem_{concept_id.split(':', 1)[1].lower()}"

    xmi, attrs, child_refs = _build_supported_case_xmi(concept_id, elem_id)
    ir, _ = _parse_xmi(tmp_path, f"{elem_id}.xmi", xmi)

    _assert_supported_artifact(concept_id, elem_id, ir, attrs, child_refs)


@pytest.mark.parametrize("concept_id", CONCEPT_IDS, ids=lambda c: c.replace("uml:", ""))
def test_uml_parser_concept_contracts(tmp_path: Path, concept_id: str) -> None:
    """Each concept from the UML profile is validated with a synthetic UML XMI case."""
    _run_concept_case(tmp_path, concept_id)
