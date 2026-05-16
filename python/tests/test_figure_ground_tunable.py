"""figure_ground_of thresholds must be tunable per consumer."""

from __future__ import annotations

import pytest

from tetrad_lens import TetradScore, TetradSpan, figure_ground_of


def _span(scores: tuple[float, float, float, float]) -> TetradSpan:
    e, o, r, v = scores
    return TetradSpan(
        enhance=TetradScore(score=e, rationale="ok" if e >= 0.5 else None),
        obsolesce=TetradScore(score=o, rationale="ok" if o >= 0.5 else None),
        retrieve=TetradScore(score=r, rationale="ok" if r >= 0.5 else None),
        reverse=TetradScore(score=v, rationale="ok" if v >= 0.5 else None),
        tier="heuristic",
    )


def test_default_threshold_borderline_unclear():
    # 0.55 mean on each side → below default high=0.6 → unclear
    s = _span((0.55, 0.55, 0.55, 0.55))
    assert figure_ground_of(s) == "unclear"


def test_tunable_lower_threshold_flips_to_both():
    s = _span((0.55, 0.55, 0.55, 0.55))
    assert figure_ground_of(s, high=0.5) == "both"


def test_tunable_higher_threshold_keeps_unclear():
    s = _span((0.7, 0.0, 0.7, 0.0))
    assert figure_ground_of(s) == "figure"
    assert figure_ground_of(s, high=0.8) == "unclear"


def test_low_param_kept_in_signature():
    # Currently informational; callers should be able to pass it without
    # TypeError so the API stays stable for v0.1.x.
    s = _span((0.7, 0.0, 0.7, 0.0))
    assert figure_ground_of(s, high=0.6, low=0.3) == "figure"


def test_invalid_threshold_does_not_crash():
    # Pathological inputs should not raise — calling with high=2.0 means
    # nothing crosses, so we get "unclear".
    s = _span((1.0, 1.0, 1.0, 1.0))
    assert figure_ground_of(s, high=2.0) == "unclear"


def test_zero_threshold_promotes_everything():
    # With high=0.0 every span is "both" — by design.
    s = _span((0.0, 0.0, 0.0, 0.0))
    assert figure_ground_of(s, high=0.0) == "both"


def test_threshold_validation_lazy():
    # We do not aggressively validate threshold ranges; document this is OK.
    s = _span((0.5, 0.5, 0.5, 0.5))
    with pytest.MonkeyPatch.context() as _:
        figure_ground_of(s, high=-1.0)  # should not raise
