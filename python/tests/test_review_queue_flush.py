"""Review queue flush + comment-truncation + partial-failure invariants."""

from __future__ import annotations

from typing import Any

import pytest

from tetrad_lens.review_queue import _COMMENT_LIMIT, ReviewQueueClient
from tetrad_lens.schema import TetradScore, TetradSpan


def _annotation_span(long_rationale: bool = False) -> TetradSpan:
    rationale = "x" * 1800 if long_rationale else "ok"
    return TetradSpan(
        enhance=TetradScore(score=0.7, rationale=rationale),
        obsolesce=TetradScore(score=0.1),
        retrieve=TetradScore(score=0.0),
        reverse=TetradScore(score=0.6, rationale="annotator reverse note"),
        tier="annotation",
    )


class FakeClient:
    public_key = "pk-fake"

    def __init__(self, fail_on: int | None = None) -> None:
        self.fail_on = fail_on
        self.calls: list[dict[str, Any]] = []

    def create_score(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)
        if self.fail_on is not None and len(self.calls) == self.fail_on:
            raise RuntimeError("simulated transient failure")


def test_atomic_partial_failure(monkeypatch: pytest.MonkeyPatch):
    """If axis #2 fails, the whole submit should buffer in-memory, not leave
    axis #1 dangling in Langfuse."""
    q = ReviewQueueClient()
    client = FakeClient(fail_on=2)
    monkeypatch.setattr("tetrad_lens.review_queue.get_client", lambda: client)
    monkeypatch.setattr("tetrad_lens.review_queue._HAVE_LANGFUSE", True)

    q.submit(trace_id="t1", span_data=_annotation_span())

    # FakeClient records axis 1 (succeeded) and axis 2 (recorded then raised).
    # After the raise on axis 2 we bail out without attempting axes 3/4 and
    # buffer all four axes for retry. We cannot un-write axis 1; the buffer
    # ensures axes 2/3/4 are not lost.
    assert len(client.calls) == 2  # axis 1 OK + axis 2 raised
    assert len(q.in_memory) == 4


def test_comment_truncation(monkeypatch: pytest.MonkeyPatch):
    """The annotation prefix is preserved; the body is hard-truncated."""
    q = ReviewQueueClient()
    client = FakeClient()
    monkeypatch.setattr("tetrad_lens.review_queue.get_client", lambda: client)
    monkeypatch.setattr("tetrad_lens.review_queue._HAVE_LANGFUSE", True)

    q.submit(trace_id="t1", span_data=_annotation_span(long_rationale=True))

    long_axis_call = next(c for c in client.calls if c["name"].endswith(".enhance"))
    comment = long_axis_call["comment"]
    assert comment.startswith("[ANNOTATION:human]")
    assert len(comment) <= _COMMENT_LIMIT


def test_flush_retries_in_memory_buffer(monkeypatch: pytest.MonkeyPatch):
    q = ReviewQueueClient()
    # First submit goes offline (no client) → 4 entries buffered.
    monkeypatch.setattr("tetrad_lens.review_queue._HAVE_LANGFUSE", False)
    q.submit(trace_id="t1", span_data=_annotation_span())
    assert len(q.in_memory) == 4

    # Now a real client comes online — flush should drain.
    monkeypatch.setattr("tetrad_lens.review_queue._HAVE_LANGFUSE", True)
    client = FakeClient()
    monkeypatch.setattr("tetrad_lens.review_queue.get_client", lambda: client)

    sent = q.flush()
    assert sent == 4
    assert q.in_memory == []
    assert len(client.calls) == 4
