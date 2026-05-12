import pytest
from pydantic import ValidationError

from cmbenchmark.measures.labels import LabelView, iter_labels
from cmbenchmark.measures.lexical_measures import (
    _detect_case_style,
    compute_lexical_measures,
    SimpleTokenizer,
)
from cmbenchmark.types.ir import IR, Edge, Node
from cmbenchmark.types.profile import LexicalProfile, TokenizerConfig


def _build_ir(model_id: str, labels: list[str]) -> IR:
    nodes = [
        Node(id=f"n{i}", type="Element", name=label, data={})
        for i, label in enumerate(labels, start=1)
    ]
    return IR(id=model_id, language="unknown", data={}, nodes=nodes, edges=[])


def test_detect_case_style_handles_upper_case_and_trimming() -> None:
    assert _detect_case_style("UPPER_CASE") == "UPPER_CASE"
    assert _detect_case_style("CPU_Usage") == "mixed"
    assert _detect_case_style("A_B") == "UPPER_CASE"
    assert _detect_case_style("  camelCase  ") == "camelCase"


def test_tokenizer_splits_camel_and_acronym_boundaries() -> None:
    tokenizer = SimpleTokenizer(
        TokenizerConfig(
            split_on_punct=True,
            split_camel_case=True,
            lowercase=True,
            keep_numbers=True,
        )
    )

    assert tokenizer.tokenize("camelCase") == ["camel", "case"]
    assert tokenizer.tokenize("XMLHttpRequest") == ["xml", "http", "request"]
    assert tokenizer.tokenize("myHTTPServer") == ["my", "http", "server"]


def test_tokenizer_splits_digit_letter_boundaries() -> None:
    tokenizer = SimpleTokenizer(
        TokenizerConfig(
            split_on_punct=True,
            split_camel_case=True,
            lowercase=True,
            keep_numbers=True,
        )
    )

    # New behaviour: digit-boundary splits prevent "Order2" / "task5" from
    # surviving as single tokens, so BIAS lexicons can match against them.
    assert tokenizer.tokenize("approveOrder2") == ["approve", "order", "2"]
    assert tokenizer.tokenize("task5Review") == ["task", "5", "review"]
    assert tokenizer.tokenize("v2HTTPServer") == ["v", "2", "http", "server"]


def test_tokenizer_protocol_surface_matches_implementation() -> None:
    # Regression for the protocol leak: SimpleTokenizer must NOT expose anything
    # beyond the `LabelTokenizer` protocol's `tokenize(text)` + `name`. Anything
    # extra would reintroduce implementation-typed dependencies in the measures.
    tokenizer = SimpleTokenizer(TokenizerConfig())
    public_methods = {
        attr for attr in dir(tokenizer)
        if not attr.startswith("_") and callable(getattr(tokenizer, attr))
    }
    assert public_methods == {"tokenize"}
    assert not hasattr(tokenizer, "stopwords")
    assert not hasattr(tokenizer, "tokenize_with_filters")


def test_d2m4_single_word_share_uses_present_label_denominator() -> None:
    profile = LexicalProfile(
        tokenizer=TokenizerConfig(
            split_on_punct=True,
            split_camel_case=True,
            lowercase=False,
            keep_numbers=True,
        )
    )
    ir = _build_ir("m1", ["alpha", "---"])

    dataset, per_model = compute_lexical_measures([ir], profile)
    model_d2m4 = per_model.d2_m4_single_multi_word["m1"]

    assert model_d2m4.single_word_label_count == 1
    assert model_d2m4.multi_word_label_count == 0
    assert model_d2m4.single_word_label_share == 0.5
    assert model_d2m4.multi_word_label_share == 0.0
    assert dataset.d2_m4_single_multi_word.dataset_share_single_word_labels == 0.5


# ----------------------------------------------------------------------------
# Nested-label extraction (LabelView / iter_labels)
# ----------------------------------------------------------------------------


def _uml_class_with_children(model_id: str = "m1") -> IR:
    """A UML class node with two attributes, two operations, one literal slot."""
    return IR(
        id=model_id,
        language="UML",
        data={},
        nodes=[
            Node(
                id="c1",
                type="UML.Class",
                name="Order",
                data={
                    "attributes": [
                        {"name": "orderId"},
                        {"name": "totalAmount"},
                        {"name": ""},  # eligible-but-missing nested slot
                    ],
                    "operations": [
                        {"name": "submitOrder"},
                        {"name": "cancelOrder"},
                    ],
                    "literals": [
                        "PENDING",
                        {"name": "SHIPPED"},
                    ],
                },
            ),
            Node(id="c2", type="UML.Class", name="Customer", data={}),
        ],
        edges=[],
    )


def test_iter_labels_walks_top_level_and_nested_children() -> None:
    ir = _uml_class_with_children()

    views = list(iter_labels(ir))

    kinds_by_name = {(v.kind, v.name) for v in views}
    # Two nodes plus 3 attributes (one with empty name), 2 operations, 2 literals.
    assert ("Node", "Order") in kinds_by_name
    assert ("Node", "Customer") in kinds_by_name
    assert ("Attribute", "orderId") in kinds_by_name
    assert ("Attribute", "totalAmount") in kinds_by_name
    assert ("Attribute", "") in kinds_by_name
    assert ("Operation", "submitOrder") in kinds_by_name
    assert ("Operation", "cancelOrder") in kinds_by_name
    assert ("Literal", "PENDING") in kinds_by_name
    assert ("Literal", "SHIPPED") in kinds_by_name
    assert len(views) == 9


def test_iter_labels_synthesizes_typed_subkind_for_children() -> None:
    ir = _uml_class_with_children()

    views = [v for v in iter_labels(ir) if v.parent_node_id == "c1"]
    types = {v.type for v in views}

    assert "UML.Class.attribute" in types
    assert "UML.Class.operation" in types
    assert "UML.Class.literal" in types


def test_iter_labels_skips_nested_when_disabled() -> None:
    ir = _uml_class_with_children()

    views = list(iter_labels(ir, include_nested_labels=False))

    assert [v.kind for v in views] == ["Node", "Node"]


def test_d2m1_counts_nested_attribute_and_operation_names() -> None:
    ir = _uml_class_with_children()
    profile = LexicalProfile()

    dataset, per_model = compute_lexical_measures([ir], profile)
    m1 = per_model.d2_m1_label_presence["m1"]

    # 2 nodes + 3 attrs + 2 ops + 2 literals = 9 eligible slots; 1 missing
    # ("Attribute" with empty name).
    assert m1.label_eligible_count == 9
    assert m1.label_present_count == 8
    assert m1.label_missing_count_by_type == {"UML.Class.attribute": 1}


def test_d2m1_ignores_nested_when_flag_off() -> None:
    ir = _uml_class_with_children()
    profile = LexicalProfile(include_nested_labels=False)

    _, per_model = compute_lexical_measures([ir], profile)
    m1 = per_model.d2_m1_label_presence["m1"]

    assert m1.label_eligible_count == 2
    assert m1.label_present_count == 2


def test_d2m1_excludes_uml_technical_value_nodes_from_eligibility() -> None:
    ir = IR(
        id="m1",
        language="UML",
        data={},
        nodes=[
            Node(id="c1", type="Class", name="Order", data={}),
            Node(id="c2", type="Class", name="", data={}),
            Node(id="l1", type="LiteralBoolean", name="", data={"value": "true"}),
            Node(id="l2", type="LiteralInteger", name="", data={"value": "1"}),
            Node(id="l3", type="LiteralReal", name="", data={"value": "3.14"}),
            Node(id="l4", type="LiteralString", name="", data={"value": "approved"}),
            Node(id="l5", type="LiteralUnlimitedNatural", name="", data={"value": "*"}),
            Node(id="m1", type="MessageOccurrenceSpecification", name="", data={}),
            Node(id="e1", type="ExecutionOccurrenceSpecification", name="", data={}),
            Node(id="b1", type="BehaviorExecutionSpecification", name="", data={}),
            Node(id="r1", type="Region", name="region", data={"stateMachine": "sm1"}),
            Node(id="ctp1", type="ClassifierTemplateParameter", name="", data={"signature": "sig1"}),
            Node(id="cf1", type="CombinedFragment", name="loop", data={"enclosingInteraction": "i1"}),
            Node(id="rts1", type="RedefinableTemplateSignature", name="RedefinableTemplate_C", data={}),
        ],
        edges=[],
    )
    profile = LexicalProfile()

    _, per_model = compute_lexical_measures([ir], profile)
    m1 = per_model.d2_m1_label_presence["m1"]

    # Only the two class nodes remain eligible for D2.M1.
    assert m1.label_eligible_count == 2
    assert m1.label_present_count == 1
    assert m1.label_missing_count_by_type == {"Class": 1}


# ----------------------------------------------------------------------------
# enable_d2_mX flags actually gate per-model storage
# ----------------------------------------------------------------------------


def test_enable_d2_m_flags_skip_per_model_storage_when_off() -> None:
    ir = _build_ir("m1", ["alpha"])
    profile = LexicalProfile(
        enable_d2_m1=False,
        enable_d2_m2=False,
        enable_d2_m3=False,
        enable_d2_m4=False,
        enable_d2_m5=False,
        enable_d2_m6=False,
    )

    dataset, per_model = compute_lexical_measures([ir], profile)

    assert per_model.d2_m1_label_presence == {}
    assert per_model.d2_m2_label_length == {}
    assert per_model.d2_m3_naming_convention == {}
    assert per_model.d2_m4_single_multi_word == {}
    assert per_model.d2_m5_lexical_diversity == {}
    assert per_model.d2_m6_language_usage == {}
    # Dataset-level structures still present (typed), just zero-valued.
    assert dataset.d2_m1_label_presence.dataset_label_eligible_count == 0
    assert dataset.d2_m6_language_usage.language_counts == {}


def test_enable_d2_m4_alone_keeps_share_consistent_when_m1_off() -> None:
    # Regression: dataset share denominator used to come from M1 accumulators,
    # so flipping M1 off silently zeroed M4's share. Now M4 owns its own
    # denominator, so the share is correct regardless of M1.
    ir = _build_ir("m1", ["alpha", "Two Words"])
    profile = LexicalProfile(enable_d2_m1=False, enable_d2_m4=True)

    dataset, per_model = compute_lexical_measures([ir], profile)
    m4_ds = dataset.d2_m4_single_multi_word

    assert per_model.d2_m4_single_multi_word["m1"].single_word_label_count == 1
    assert per_model.d2_m4_single_multi_word["m1"].multi_word_label_count == 1
    assert m4_ds.total_single_word_labels == 1
    assert m4_ds.total_multi_word_labels == 1
    assert m4_ds.dataset_share_single_word_labels == 0.5


# ----------------------------------------------------------------------------
# label_attributes whitelist
# ----------------------------------------------------------------------------


def test_label_attributes_validator_rejects_unknown_attribute() -> None:
    with pytest.raises(ValidationError) as excinfo:
        LexicalProfile(label_attributes=["data"])
    msg = str(excinfo.value)
    assert "data" in msg
    assert "label_attributes" in msg


def test_label_attributes_validator_accepts_known_aliases() -> None:
    profile = LexicalProfile(label_attributes=["name", "label", "displayName"])
    assert profile.label_attributes == ["name", "label", "displayName"]


def test_noise_token_list_field_was_removed_from_tokenizer_config() -> None:
    # TokenizerConfig forbids extra fields; old `noise_token_list` JSON keys
    # must be cleaned up by callers (we did this in profiles/*.json).
    with pytest.raises(ValidationError):
        TokenizerConfig(noise_token_list="generic_noise_v1")  # type: ignore[call-arg]


def test_stopword_list_field_was_removed_from_tokenizer_config() -> None:
    # TokenizerConfig is strict; old `stopword_list` JSON keys must be cleaned
    # up by callers (we did this in profiles/*.json).
    with pytest.raises(ValidationError):
        TokenizerConfig(stopword_list="en_default")  # type: ignore[call-arg]
