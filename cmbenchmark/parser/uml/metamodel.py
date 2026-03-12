"""Supported UML concepts and parsing contracts.

This module documents the parser-supported subset of the UML metamodel.
Each concept declares the attributes and children that are intentionally handled.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, Mapping


@dataclass(frozen=True)
class UMLConceptSpec:
    """Specification of a supported UML concept."""

    concept_id: str
    allowed_attributes: FrozenSet[str]
    allowed_children: FrozenSet[str]
    produces: str


SUPPORTED_UML_CONCEPTS: Mapping[str, UMLConceptSpec] = {
    "uml:Model": UMLConceptSpec(
        concept_id="uml:Model",
        allowed_attributes=frozenset({"name", "visibility"}),
        allowed_children=frozenset({"packagedElement", "packageImport", "elementImport", "ownedComment"}),
        produces="IR metadata",
    ),
    "uml:Package": UMLConceptSpec(
        concept_id="uml:Package",
        allowed_attributes=frozenset({"name", "visibility"}),
        allowed_children=frozenset({"packagedElement", "ownedComment", "packageImport", "elementImport"}),
        produces="Node(type=Package)",
    ),
    "uml:Class": UMLConceptSpec(
        concept_id="uml:Class",
        allowed_attributes=frozenset({"name", "visibility", "isAbstract", "isLeaf", "href", "templateParameter", "owningTemplateParameter"}),
        allowed_children=frozenset({
            "ownedAttribute",
            "ownedOperation",
            "generalization",
            "interfaceRealization",
            "ownedComment",
            "nestedClassifier",
            "ownedTemplateSignature",
            "templateBinding",
            "elementImport",
        }),
        produces="Node(type=Class)",
    ),
    "uml:Interface": UMLConceptSpec(
        concept_id="uml:Interface",
        allowed_attributes=frozenset({"name", "visibility", "isAbstract", "href"}),
        allowed_children=frozenset({
            "ownedOperation",
            "ownedAttribute",
            "generalization",
            "ownedComment",
            "nestedClassifier",
            "ownedTemplateSignature",
            "templateBinding",
            "elementImport",
        }),
        produces="Node(type=Interface)",
    ),
    "uml:Enumeration": UMLConceptSpec(
        concept_id="uml:Enumeration",
        allowed_attributes=frozenset({"name", "visibility", "href"}),
        allowed_children=frozenset({"ownedLiteral", "ownedComment", "ownedOperation", "ownedAttribute"}),
        produces="Node(type=Enumeration)",
    ),
    "uml:DataType": UMLConceptSpec(
        concept_id="uml:DataType",
        allowed_attributes=frozenset({"name", "visibility", "isAbstract", "href"}),
        allowed_children=frozenset({"ownedComment", "templateBinding"}),
        produces="Node(type=DataType)",
    ),
    "uml:Component": UMLConceptSpec(
        concept_id="uml:Component",
        allowed_attributes=frozenset({"name", "visibility", "isAbstract", "isLeaf"}),
        allowed_children=frozenset({
            "ownedUseCase",
            "packagedElement",
            "nestedClassifier",
            "generalization",
            "ownedComment",
            "ownedTemplateSignature",
            "ownedAttribute",
        }),
        produces="Node(type=Component)",
    ),
    "uml:UseCase": UMLConceptSpec(
        concept_id="uml:UseCase",
        allowed_attributes=frozenset({"name", "visibility", "isAbstract", "isLeaf", "href"}),
        allowed_children=frozenset({"include", "extend", "extensionPoint", "generalization", "ownedComment", "ownedUseCase"}),
        produces="Node(type=UseCase)",
    ),
    "uml:Actor": UMLConceptSpec(
        concept_id="uml:Actor",
        allowed_attributes=frozenset({"name", "visibility", "isAbstract", "isLeaf", "href"}),
        allowed_children=frozenset({"generalization", "ownedComment"}),
        produces="Node(type=Actor)",
    ),
    "uml:Activity": UMLConceptSpec(
        concept_id="uml:Activity",
        allowed_attributes=frozenset({"name", "visibility", "isReadOnly", "isSingleExecution"}),
        allowed_children=frozenset(
            {
                "ownedComment",
                "ownedBehavior",
                "ownedNode",
                "edge",
                "ownedGroup",
                "variable",
                "structuredNode",
            }
        ),
        produces="Node(type=Activity)",
    ),
    "uml:StateMachine": UMLConceptSpec(
        concept_id="uml:StateMachine",
        allowed_attributes=frozenset({"name", "visibility", "isReentrant"}),
        allowed_children=frozenset({"ownedComment", "region", "connectionPoint", "doActivity"}),
        produces="Node(type=StateMachine)",
    ),
    "uml:Interaction": UMLConceptSpec(
        concept_id="uml:Interaction",
        allowed_attributes=frozenset({"name", "visibility"}),
        allowed_children=frozenset({"ownedComment", "lifeline", "message", "fragment", "nestedClassifier"}),
        produces="Node(type=Interaction)",
    ),
    "uml:InstanceSpecification": UMLConceptSpec(
        concept_id="uml:InstanceSpecification",
        allowed_attributes=frozenset({"name", "visibility", "classifier"}),
        allowed_children=frozenset({"ownedComment", "slot", "specification"}),
        produces="Node(type=InstanceSpecification)",
    ),
    "uml:AssociationClass": UMLConceptSpec(
        concept_id="uml:AssociationClass",
        allowed_attributes=frozenset(
            {
                "name",
                "visibility",
                "isAbstract",
                "isLeaf",
                "memberEnd",
                "navigableOwnedEnd",
            }
        ),
        allowed_children=frozenset(
            {
                "ownedAttribute",
                "ownedOperation",
                "generalization",
                "interfaceRealization",
                "ownedComment",
                "nestedClassifier",
                "ownedTemplateSignature",
                "templateBinding",
                "elementImport",
                "ownedEnd",
            }
        ),
        produces="Node(type=AssociationClass)",
    ),
    "uml:CommunicationPath": UMLConceptSpec(
        concept_id="uml:CommunicationPath",
        allowed_attributes=frozenset({"name", "memberEnd", "navigableOwnedEnd"}),
        allowed_children=frozenset({"ownedEnd", "name"}),
        produces="Edge(type=CommunicationPath)",
    ),
    "uml:Device": UMLConceptSpec(
        concept_id="uml:Device",
        allowed_attributes=frozenset({"name", "visibility", "isLeaf"}),
        allowed_children=frozenset({"ownedComment", "nestedNode", "deployedArtifact"}),
        produces="Node(type=Device)",
    ),
    "uml:Node": UMLConceptSpec(
        concept_id="uml:Node",
        allowed_attributes=frozenset({"name", "visibility", "isLeaf"}),
        allowed_children=frozenset({"ownedComment", "nestedNode", "deployedArtifact"}),
        produces="Node(type=Node)",
    ),
    "uml:Artifact": UMLConceptSpec(
        concept_id="uml:Artifact",
        allowed_attributes=frozenset({"name", "visibility", "fileName"}),
        allowed_children=frozenset({"ownedComment"}),
        produces="Node(type=Artifact)",
    ),
    "uml:InformationFlow": UMLConceptSpec(
        concept_id="uml:InformationFlow",
        allowed_attributes=frozenset({"name", "informationSource", "informationTarget"}),
        allowed_children=frozenset({"ownedComment", "realization", "conveyed"}),
        produces="Edge(type=InformationFlow)",
    ),
    "uml:ExecutionEnvironment": UMLConceptSpec(
        concept_id="uml:ExecutionEnvironment",
        allowed_attributes=frozenset({"name", "visibility", "isLeaf"}),
        allowed_children=frozenset({"ownedComment", "nestedNode", "deployedArtifact"}),
        produces="Node(type=ExecutionEnvironment)",
    ),
    "uml:OpaqueAction": UMLConceptSpec(
        concept_id="uml:OpaqueAction",
        allowed_attributes=frozenset({"name", "visibility", "incoming", "outgoing"}),
        allowed_children=frozenset({"ownedComment", "inputValue", "outputValue"}),
        produces="Node(type=OpaqueAction)",
    ),
    "uml:InitialNode": UMLConceptSpec(
        concept_id="uml:InitialNode",
        allowed_attributes=frozenset({"name", "visibility", "incoming", "outgoing"}),
        allowed_children=frozenset({"ownedComment"}),
        produces="Node(type=InitialNode)",
    ),
    "uml:ActivityFinalNode": UMLConceptSpec(
        concept_id="uml:ActivityFinalNode",
        allowed_attributes=frozenset({"name", "visibility", "incoming", "outgoing"}),
        allowed_children=frozenset({"ownedComment"}),
        produces="Node(type=ActivityFinalNode)",
    ),
    "uml:FlowFinalNode": UMLConceptSpec(
        concept_id="uml:FlowFinalNode",
        allowed_attributes=frozenset({"name", "visibility", "incoming", "outgoing"}),
        allowed_children=frozenset({"ownedComment"}),
        produces="Node(type=FlowFinalNode)",
    ),
    "uml:DecisionNode": UMLConceptSpec(
        concept_id="uml:DecisionNode",
        allowed_attributes=frozenset({"name", "visibility", "incoming", "outgoing"}),
        allowed_children=frozenset({"ownedComment"}),
        produces="Node(type=DecisionNode)",
    ),
    "uml:MergeNode": UMLConceptSpec(
        concept_id="uml:MergeNode",
        allowed_attributes=frozenset({"name", "visibility", "incoming", "outgoing"}),
        allowed_children=frozenset({"ownedComment"}),
        produces="Node(type=MergeNode)",
    ),
    "uml:JoinNode": UMLConceptSpec(
        concept_id="uml:JoinNode",
        allowed_attributes=frozenset({"name", "visibility", "incoming", "outgoing"}),
        allowed_children=frozenset({"ownedComment"}),
        produces="Node(type=JoinNode)",
    ),
    "uml:ForkNode": UMLConceptSpec(
        concept_id="uml:ForkNode",
        allowed_attributes=frozenset({"name", "visibility", "incoming", "outgoing"}),
        allowed_children=frozenset({"ownedComment"}),
        produces="Node(type=ForkNode)",
    ),
    "uml:ActivityPartition": UMLConceptSpec(
        concept_id="uml:ActivityPartition",
        allowed_attributes=frozenset({"name", "visibility", "node"}),
        allowed_children=frozenset({"ownedComment", "subpartition"}),
        produces="Node(type=ActivityPartition)",
    ),
    "uml:MessageOccurrenceSpecification": UMLConceptSpec(
        concept_id="uml:MessageOccurrenceSpecification",
        allowed_attributes=frozenset({"name", "covered", "enclosingInteraction"}),
        allowed_children=frozenset({"ownedComment"}),
        produces="Node(type=MessageOccurrenceSpecification)",
    ),
    "uml:ExecutionOccurrenceSpecification": UMLConceptSpec(
        concept_id="uml:ExecutionOccurrenceSpecification",
        allowed_attributes=frozenset({"name", "covered", "enclosingInteraction"}),
        allowed_children=frozenset({"ownedComment"}),
        produces="Node(type=ExecutionOccurrenceSpecification)",
    ),
    "uml:BehaviorExecutionSpecification": UMLConceptSpec(
        concept_id="uml:BehaviorExecutionSpecification",
        allowed_attributes=frozenset({"name", "covered", "enclosingInteraction", "start", "finish"}),
        allowed_children=frozenset({"ownedComment", "generalOrdering"}),
        produces="Node(type=BehaviorExecutionSpecification)",
    ),
    "uml:Collaboration": UMLConceptSpec(
        concept_id="uml:Collaboration",
        allowed_attributes=frozenset({"name", "visibility"}),
        allowed_children=frozenset({"ownedAttribute", "ownedComment"}),
        produces="Node(type=Collaboration)",
    ),
    "uml:State": UMLConceptSpec(
        concept_id="uml:State",
        allowed_attributes=frozenset({"name", "visibility", "container", "incoming", "outgoing"}),
        allowed_children=frozenset({"ownedComment", "region", "entry", "exit", "doActivity"}),
        produces="Node(type=State)",
    ),
    "uml:Pseudostate": UMLConceptSpec(
        concept_id="uml:Pseudostate",
        allowed_attributes=frozenset({"name", "visibility", "container", "incoming", "outgoing", "kind"}),
        allowed_children=frozenset({"ownedComment"}),
        produces="Node(type=Pseudostate)",
    ),
    "uml:Region": UMLConceptSpec(
        concept_id="uml:Region",
        allowed_attributes=frozenset({"name", "visibility", "stateMachine", "state"}),
        allowed_children=frozenset({"ownedComment", "subvertex", "transition"}),
        produces="Node(type=Region)",
    ),
    "uml:Lifeline": UMLConceptSpec(
        concept_id="uml:Lifeline",
        allowed_attributes=frozenset({"name", "visibility", "represents", "decomposedAs", "coveredBy"}),
        allowed_children=frozenset({"ownedComment", "selector"}),
        produces="Node(type=Lifeline)",
    ),
    "uml:CombinedFragment": UMLConceptSpec(
        concept_id="uml:CombinedFragment",
        allowed_attributes=frozenset({"name", "visibility", "interactionOperator", "covered", "enclosingInteraction"}),
        allowed_children=frozenset({"ownedComment", "operand"}),
        produces="Node(type=CombinedFragment)",
    ),
    "uml:InteractionOperand": UMLConceptSpec(
        concept_id="uml:InteractionOperand",
        allowed_attributes=frozenset({"name", "visibility", "covered", "enclosingInteraction", "guard"}),
        allowed_children=frozenset({"ownedComment", "fragment"}),
        produces="Node(type=InteractionOperand)",
    ),
    "uml:InstanceValue": UMLConceptSpec(
        concept_id="uml:InstanceValue",
        allowed_attributes=frozenset({"name", "visibility", "instance"}),
        allowed_children=frozenset({"ownedComment"}),
        produces="Node(type=InstanceValue)",
    ),
    "uml:Expression": UMLConceptSpec(
        concept_id="uml:Expression",
        allowed_attributes=frozenset({"name", "visibility", "symbol"}),
        allowed_children=frozenset({"ownedComment", "operand"}),
        produces="Node(type=Expression)",
    ),
    "uml:LiteralBoolean": UMLConceptSpec(
        concept_id="uml:LiteralBoolean",
        allowed_attributes=frozenset({"name", "visibility", "value"}),
        allowed_children=frozenset({"ownedComment"}),
        produces="Node(type=LiteralBoolean)",
    ),
    "uml:LiteralInteger": UMLConceptSpec(
        concept_id="uml:LiteralInteger",
        allowed_attributes=frozenset({"name", "visibility", "value"}),
        allowed_children=frozenset({"ownedComment"}),
        produces="Node(type=LiteralInteger)",
    ),
    "uml:LiteralReal": UMLConceptSpec(
        concept_id="uml:LiteralReal",
        allowed_attributes=frozenset({"name", "visibility", "value"}),
        allowed_children=frozenset({"ownedComment"}),
        produces="Node(type=LiteralReal)",
    ),
    "uml:LiteralString": UMLConceptSpec(
        concept_id="uml:LiteralString",
        allowed_attributes=frozenset({"name", "visibility", "value"}),
        allowed_children=frozenset({"ownedComment"}),
        produces="Node(type=LiteralString)",
    ),
    "uml:LiteralUnlimitedNatural": UMLConceptSpec(
        concept_id="uml:LiteralUnlimitedNatural",
        allowed_attributes=frozenset({"name", "visibility", "value"}),
        allowed_children=frozenset({"ownedComment"}),
        produces="Node(type=LiteralUnlimitedNatural)",
    ),
    "uml:PrimitiveType": UMLConceptSpec(
        concept_id="uml:PrimitiveType",
        allowed_attributes=frozenset({"name", "visibility", "href"}),
        allowed_children=frozenset({"ownedComment"}),
        produces="Node(type=PrimitiveType)",
    ),
    "uml:EnumerationLiteral": UMLConceptSpec(
        concept_id="uml:EnumerationLiteral",
        allowed_attributes=frozenset({"name", "visibility"}),
        allowed_children=frozenset({"ownedComment"}),
        produces="Node(type=EnumerationLiteral)",
    ),
    "uml:Association": UMLConceptSpec(
        concept_id="uml:Association",
        allowed_attributes=frozenset({"name", "memberEnd", "navigableOwnedEnd"}),
        allowed_children=frozenset({"ownedEnd", "name"}),
        produces="Edge(type=Association)",
    ),
    "uml:ControlFlow": UMLConceptSpec(
        concept_id="uml:ControlFlow",
        allowed_attributes=frozenset({"name", "source", "target", "activity"}),
        allowed_children=frozenset({"guard"}),
        produces="Edge(type=ControlFlow)",
    ),
    "uml:ObjectFlow": UMLConceptSpec(
        concept_id="uml:ObjectFlow",
        allowed_attributes=frozenset({"name", "source", "target", "activity"}),
        allowed_children=frozenset({"guard"}),
        produces="Edge(type=ObjectFlow)",
    ),
    "uml:Transition": UMLConceptSpec(
        concept_id="uml:Transition",
        allowed_attributes=frozenset({"name", "source", "target", "container", "kind"}),
        allowed_children=frozenset({"guard", "trigger", "effect"}),
        produces="Edge(type=Transition)",
    ),
    "uml:Message": UMLConceptSpec(
        concept_id="uml:Message",
        allowed_attributes=frozenset({"name", "sendEvent", "receiveEvent", "messageSort", "messageKind", "connector"}),
        allowed_children=frozenset({"ownedComment", "argument"}),
        produces="Edge(type=Message)",
    ),
    "uml:Generalization": UMLConceptSpec(
        concept_id="uml:Generalization",
        allowed_attributes=frozenset({"name", "general", "specific"}),
        allowed_children=frozenset({"general"}),
        produces="Edge(type=Generalization)",
    ),
    "uml:InterfaceRealization": UMLConceptSpec(
        concept_id="uml:InterfaceRealization",
        allowed_attributes=frozenset({"name", "client", "supplier", "implementingClassifier", "contract"}),
        allowed_children=frozenset({"supplier", "contract"}),
        produces="Edge(type=InterfaceRealization)",
    ),
    "uml:Dependency": UMLConceptSpec(
        concept_id="uml:Dependency",
        allowed_attributes=frozenset({"name", "client", "supplier"}),
        allowed_children=frozenset(),
        produces="Edge(type=Dependency)",
    ),
    "uml:Usage": UMLConceptSpec(
        concept_id="uml:Usage",
        allowed_attributes=frozenset({"name", "client", "supplier"}),
        allowed_children=frozenset(),
        produces="Edge(type=Usage)",
    ),
    "uml:Include": UMLConceptSpec(
        concept_id="uml:Include",
        allowed_attributes=frozenset({"includingCase", "addition"}),
        allowed_children=frozenset({"addition"}),
        produces="Edge(type=includes)",
    ),
    "uml:Extend": UMLConceptSpec(
        concept_id="uml:Extend",
        allowed_attributes=frozenset({"extension", "extendedCase", "extensionLocation"}),
        allowed_children=frozenset({"extendedCase", "extensionLocation"}),
        produces="Edge(type=extends)",
    ),
}


TAG_TO_CONCEPT: Dict[str, str] = {
    "Model": "uml:Model",
    "generalization": "uml:Generalization",
    "interfaceRealization": "uml:InterfaceRealization",
    "include": "uml:Include",
    "extend": "uml:Extend",
    "ownedUseCase": "uml:UseCase",
    "ownedBehavior": "uml:Activity",
    "doActivity": "uml:StateMachine",
    "nestedNode": "uml:ExecutionEnvironment",
    "region": "uml:Region",
    "transition": "uml:Transition",
    "message": "uml:Message",
    "lifeline": "uml:Lifeline",
    "operand": "uml:InteractionOperand",
}


CONTAINMENT_CHILD_TAGS: FrozenSet[str] = frozenset(
    {
        "packagedElement",
        "ownedUseCase",
        "ownedBehavior",
        "doActivity",
        "nestedNode",
        "nestedClassifier",
        "ownedNode",
        "ownedGroup",
        "edge",
        "subvertex",
        "region",
        "transition",
        "fragment",
        "lifeline",
        "message",
        "operand",
    }
)


def concept_spec(concept_id: str) -> UMLConceptSpec:
    """Return metamodel spec for a concept id."""
    return SUPPORTED_UML_CONCEPTS[concept_id]
