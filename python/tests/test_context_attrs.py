"""tetrad_context + tag_current_span actually set the attributes on the span."""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from tetrad_lens import (
    TetradScore,
    TetradSpan,
    tag_current_span,
    tetrad_context,
)


def _make_exporter() -> InMemorySpanExporter:
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return exporter


def _span_data() -> TetradSpan:
    return TetradSpan(
        enhance=TetradScore(score=0.7, rationale="strong enhance"),
        obsolesce=TetradScore(score=0.1),
        retrieve=TetradScore(score=0.0),
        reverse=TetradScore(score=0.6, rationale="strong reverse"),
        tier="heuristic",
    )


def test_tag_current_span_attaches_to_active_span():
    exporter = _make_exporter()
    with tetrad_context("test"):
        tag_current_span(_span_data())

    spans = exporter.get_finished_spans()
    assert len(spans) >= 1
    attrs = spans[-1].attributes or {}
    assert attrs.get("tetrad.enhance") == 0.7
    assert attrs.get("tetrad.reverse") == 0.6
    assert attrs.get("tetrad.tier") == "heuristic"
    assert "tetrad.figure_ground" not in attrs  # producer must not set


def test_tag_current_span_no_active_span_is_noop():
    # Outside any tracer context, calling tag_current_span must not raise.
    tag_current_span(_span_data())
