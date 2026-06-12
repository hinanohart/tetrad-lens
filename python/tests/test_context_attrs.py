"""tetrad_context + tag_current_span actually set the attributes on the span."""

from __future__ import annotations

from opentelemetry import baggage, context, trace
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


def test_rationale_not_propagated_into_baggage():
    # Baggage is serialized into outbound HTTP headers and reaches every
    # downstream service. Free-text rationale must never be propagated, but
    # numeric/categorical signals should be.
    _make_exporter()
    token = context.attach(context.get_current())
    try:
        with tetrad_context("test"):
            tag_current_span(_span_data(), propagate_baggage=True)
        bag = baggage.get_all()
        assert bag.get("tetrad.enhance") == "0.7"
        assert bag.get("tetrad.tier") == "heuristic"
        assert "tetrad.enhance.rationale" not in bag
        assert "tetrad.reverse.rationale" not in bag
        assert not any(k.endswith(".rationale") for k in bag)
    finally:
        context.detach(token)
