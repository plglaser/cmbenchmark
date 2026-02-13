from cmbenchmark.measures.lexical_measures import (
    _detect_case_style,
    compute_lexical_measures,
    SimpleTokenizer,
)
from cmbenchmark.types.ir import IR, Node
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


def test_d2m5_stopword_count_uses_raw_tokens() -> None:
    profile = LexicalProfile(
        tokenizer=TokenizerConfig(
            split_on_punct=True,
            split_camel_case=True,
            lowercase=False,
            keep_numbers=True,
            stopword_list="en_default",
        )
    )
    ir = _build_ir("m1", ["The System", "A Model"])

    dataset, per_model = compute_lexical_measures([ir], profile)
    model_d2m5 = per_model.d2_m5_lexical_diversity["m1"]

    # Stopwords are removed from model_tokens but still counted for stopword metrics.
    assert model_d2m5.total_tokens == 2
    assert model_d2m5.stopword_tokens == 2
    assert model_d2m5.stopword_share == 0.5
    assert dataset.d2_m5_lexical_diversity.stopword_share == 0.5


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
