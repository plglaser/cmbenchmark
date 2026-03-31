from dataclasses import asdict

from cmbenchmark.measures.lexical_measures import compute_lexical_measures
from cmbenchmark.measures.construct_measures import compute_construct_measures
from cmbenchmark.measures.size_complexity_measures import compute_size_complexity_measures
from cmbenchmark.types.constructs import ConstructDef
from cmbenchmark.types.ir import IR, Node, Edge
from cmbenchmark.types.profile import LexicalProfile, TokenizerConfig


def _build_models() -> list[IR]:
    ir1 = IR(
        id="m1",
        language="BPMN",
        data={},
        nodes=[
            Node(id="n1", type="Task", name="CreateOrder", data={}),
            Node(id="n2", type="Task", name="Validate Order", data={}),
        ],
        edges=[
            Edge(id="e1", sourceId="n1", targetId="n2", type="Flow", data={}),
        ],
    )
    ir2 = IR(
        id="m2",
        language="BPMN",
        data={},
        nodes=[
            Node(id="n3", type="Task", name="ShipItem", data={}),
            Node(id="n4", type="Task", name="Invoice Item", data={}),
        ],
        edges=[
            Edge(id="e2", sourceId="n3", targetId="n4", type="Flow", data={}),
        ],
    )
    return [ir1, ir2]


def test_lexical_measures_match_for_list_and_iterable() -> None:
    models = _build_models()
    profile = LexicalProfile(
        tokenizer=TokenizerConfig(
            split_on_punct=True,
            split_camel_case=True,
            lowercase=True,
            keep_numbers=True,
        )
    )

    dataset_list, per_model_list = compute_lexical_measures(models, profile)
    dataset_iter, per_model_iter = compute_lexical_measures(
        (m for m in models),
        profile,
        total_models=len(models),
    )

    assert asdict(dataset_list) == asdict(dataset_iter)
    assert asdict(per_model_list) == asdict(per_model_iter)


def test_construct_measures_match_for_list_and_iterable() -> None:
    models = _build_models()
    constructs = {
        "bpmn:Task": ConstructDef(
            id="bpmn:Task",
            kind="node_type",
            match_type="Task",
            description="Task",
            meta={"layer": "activity"},
        ),
        "bpmn:Flow": ConstructDef(
            id="bpmn:Flow",
            kind="edge_type",
            match_type="Flow",
            description="Flow",
            meta={"layer": "flow"},
        ),
    }

    dataset_list, per_model_list = compute_construct_measures(models, constructs)
    dataset_iter, per_model_iter = compute_construct_measures(
        (m for m in models),
        constructs,
        total_models=len(models),
    )

    assert asdict(dataset_list) == asdict(dataset_iter)
    assert asdict(per_model_list) == asdict(per_model_iter)


def test_size_complexity_measures_match_for_list_and_iterable() -> None:
    models = _build_models()

    dataset_list, per_model_list = compute_size_complexity_measures(models)
    dataset_iter, per_model_iter = compute_size_complexity_measures(
        (m for m in models),
        total_models=len(models),
    )

    assert asdict(dataset_list) == asdict(dataset_iter)
    assert asdict(per_model_list) == asdict(per_model_iter)
