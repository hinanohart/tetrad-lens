"""Review queue invariants: ANNOTATION tier wins, four scores written, in-memory fallback works."""

from __future__ import annotations

import pytest

from tetrad_lens.review_queue import ReviewQueueClient
from tetrad_lens.schema import TetradScore, TetradSpan


def _annotation_span():
    return TetradSpan(
        enhance=TetradScore(score=0.7, rationale="annotator says enhances X"),
        obsolesce=TetradScore(score=0.1),
        retrieve=TetradScore(score=0.0),
        reverse=TetradScore(score=0.6, rationale="annotator says reverses into Y"),
        tier="annotation",
    )


def test_rejects_non_annotation_tier():
    q = ReviewQueueClient()
    bad = TetradSpan(
        enhance=TetradScore(score=0.0),
        obsolesce=TetradScore(score=0.0),
        retrieve=TetradScore(score=0.0),
        reverse=TetradScore(score=0.0),
        tier="heuristic",
    )
    with pytest.raises(ValueError):
        q.submit(trace_id="t1", span_data=bad)


def test_in_memory_writes_four_axes():
    q = ReviewQueueClient(config_name="tetrad_v1")
    q.submit(trace_id="t1", span_data=_annotation_span(), annotator="me")
    names = {entry["name"] for entry in q.in_memory if entry["trace_id"] == "t1"}
    assert names == {
        "tetrad_v1.enhance",
        "tetrad_v1.obsolesce",
        "tetrad_v1.retrieve",
        "tetrad_v1.reverse",
    }
