"""SDK smoke tests — the decorator should be importable and callable even
without a live Langfuse client or OTel exporter."""

from __future__ import annotations

from tetrad_lens import install_processor, observe
from tetrad_lens.schema import TetradScore, TetradSpan
from tetrad_lens.sdk import tag_current_span, tetrad_context


def test_install_processor_idempotent():
    install_processor()
    install_processor()


def test_observe_wraps_callable():
    @observe(name="x")
    def add(a: int, b: int) -> int:
        return a + b

    assert add(1, 2) == 3


def test_tag_current_span_no_op_when_no_active_span():
    span = TetradSpan(
        enhance=TetradScore(score=0.0),
        obsolesce=TetradScore(score=0.0),
        retrieve=TetradScore(score=0.0),
        reverse=TetradScore(score=0.0),
        tier="heuristic",
    )
    tag_current_span(span)  # should not raise


def test_tetrad_context_manager():
    with tetrad_context("test-span") as s:
        assert s is not None
