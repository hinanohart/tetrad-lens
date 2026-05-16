"""LLM tagger: position-swap, malformed JSON, per-axis fallback, confidence math."""

from __future__ import annotations

from typing import Any

import pytest

from tetrad_lens.llm_tagger import LLMTagger, _alias_map_a, _alias_map_b


def _good_response(alias_map: dict[str, str], scores: dict[str, float]) -> dict[str, Any]:
    """Build a model response that scores each axis to ``scores[axis]``."""
    return {
        alias: {
            "score": scores[axis],
            "rationale": f"axis={axis} score={scores[axis]}",
        }
        for alias, axis in alias_map.items()
    }


class FakeOllama:
    """Returns canned per-call responses in order."""

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = list(responses)
        self.calls: list[str] = []

    def __call__(self, prompt: str) -> dict[str, Any]:
        self.calls.append(prompt)
        if not self.responses:
            return {}
        return self.responses.pop(0)


def test_position_swap_renames_axes_between_calls():
    """The two prompts must use *different* alias maps so the JSON key order
    differs — otherwise position-swap is theatre."""
    a = _alias_map_a()
    b = _alias_map_b()
    assert list(a.keys()) == list(b.keys()), "alias names should be the same"
    assert list(a.values()) != list(b.values()), (
        "but the axes they point at must differ to actually swap positions"
    )


def test_agreement_yields_high_confidence(monkeypatch: pytest.MonkeyPatch):
    scores = {"enhance": 0.6, "obsolesce": 0.4, "retrieve": 0.2, "reverse": 0.4}
    fake = FakeOllama(
        [
            _good_response(_alias_map_a(), scores),
            _good_response(_alias_map_b(), scores),
        ]
    )
    tagger = LLMTagger()
    monkeypatch.setattr(tagger, "_call_ollama", fake)

    span = tagger.tag("the action")
    assert span is not None
    assert span.tier == "llm"
    assert span.confidence is not None and span.confidence > 0.95


def test_disagreement_drops_confidence(monkeypatch: pytest.MonkeyPatch):
    scores_a = {"enhance": 0.9, "obsolesce": 0.1, "retrieve": 0.8, "reverse": 0.2}
    scores_b = {"enhance": 0.1, "obsolesce": 0.9, "retrieve": 0.2, "reverse": 0.8}
    fake = FakeOllama(
        [
            _good_response(_alias_map_a(), scores_a),
            _good_response(_alias_map_b(), scores_b),
        ]
    )
    tagger = LLMTagger()
    monkeypatch.setattr(tagger, "_call_ollama", fake)

    span = tagger.tag("the action")
    assert span is not None
    # Every axis disagrees by 0.8; confidence = max(0, 1 - 2*0.8) = 0
    assert span.confidence == 0.0


def test_partial_failure_falls_back_per_axis(monkeypatch: pytest.MonkeyPatch):
    """If one axis is missing from one response, only that axis should fall
    back to heuristic — the other three keep the LLM reading."""
    scores_a = {"enhance": 0.5, "obsolesce": 0.5, "retrieve": 0.5, "reverse": 0.5}
    scores_b = dict(scores_a)
    response_a = _good_response(_alias_map_a(), scores_a)
    response_b = _good_response(_alias_map_b(), scores_b)
    # Drop the "obsolesce" axis from response_b by deleting whichever alias
    # maps to "obsolesce".
    drop_alias = next(a for a, ax in _alias_map_b().items() if ax == "obsolesce")
    del response_b[drop_alias]
    fake = FakeOllama([response_a, response_b])

    tagger = LLMTagger()
    monkeypatch.setattr(tagger, "_call_ollama", fake)

    span = tagger.tag("a benign sentence with no keyword hits")
    assert span is not None
    # The three healthy axes keep their LLM-derived scores.
    assert span.enhance.score == pytest.approx(0.5)
    assert span.retrieve.score == pytest.approx(0.5)
    assert span.reverse.score == pytest.approx(0.5)


def test_both_calls_empty_returns_none(monkeypatch: pytest.MonkeyPatch):
    fake = FakeOllama([{}, {}])
    tagger = LLMTagger()
    monkeypatch.setattr(tagger, "_call_ollama", fake)
    assert tagger.tag("x") is None
