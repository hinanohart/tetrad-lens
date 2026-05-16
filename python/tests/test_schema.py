"""Schema invariants — these are the cross-language contract, do not loosen."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from tetrad_lens.schema import (
    RoleSplit,
    TetradScore,
    TetradSpan,
    figure_ground_of,
)

SCHEMA_JSON = json.loads(
    (Path(__file__).resolve().parents[2] / "schema" / "tetrad-v1.json").read_text()
)


def _span(scores=(0.0, 0.0, 0.0, 0.0), tier="heuristic", **extra):
    e, o, r, v = scores
    return TetradSpan(
        enhance=TetradScore(score=e, rationale="ok" if e >= 0.5 else None),
        obsolesce=TetradScore(score=o, rationale="ok" if o >= 0.5 else None),
        retrieve=TetradScore(score=r, rationale="ok" if r >= 0.5 else None),
        reverse=TetradScore(score=v, rationale="ok" if v >= 0.5 else None),
        tier=tier,
        **extra,
    )


class TestTetradScore:
    def test_range_lo(self):
        with pytest.raises(ValidationError):
            TetradScore(score=-0.1)

    def test_range_hi(self):
        with pytest.raises(ValidationError):
            TetradScore(score=1.1)

    def test_rationale_required_when_strong(self):
        with pytest.raises(ValidationError):
            TetradScore(score=0.7)

    def test_rationale_optional_when_weak(self):
        TetradScore(score=0.2)


class TestTetradSpan:
    def test_llm_requires_confidence(self):
        with pytest.raises(ValidationError):
            _span(tier="llm")

    def test_llm_with_confidence_ok(self):
        _span(tier="llm", confidence=0.8)

    def test_heuristic_no_confidence_ok(self):
        _span(tier="heuristic")

    def test_otel_attrs_have_dot_namespace(self):
        attrs = _span(scores=(0.6, 0.0, 0.0, 0.0)).to_otel_attributes()
        assert "tetrad.enhance" in attrs
        assert "tetrad.enhance.rationale" in attrs
        assert "tetrad.schema_version" in attrs
        assert all(k.startswith(("tetrad.", "engelbart.")) for k in attrs)

    def test_otel_attrs_never_include_figure_ground(self):
        attrs = _span().to_otel_attributes()
        assert "tetrad.figure_ground" not in attrs  # derived/read-only invariant


class TestFigureGround:
    def test_unclear_when_all_low(self):
        assert figure_ground_of(_span(scores=(0.0, 0.0, 0.0, 0.0))) == "unclear"

    def test_figure_when_enhance_retrieve_high(self):
        assert figure_ground_of(_span(scores=(0.8, 0.0, 0.8, 0.0))) == "figure"

    def test_ground_when_obsolesce_reverse_high(self):
        assert figure_ground_of(_span(scores=(0.0, 0.8, 0.0, 0.8))) == "ground"

    def test_both_when_all_high(self):
        assert figure_ground_of(_span(scores=(0.8, 0.8, 0.8, 0.8))) == "both"


class TestRoleSplit:
    def test_sum_capped(self):
        with pytest.raises(ValidationError):
            RoleSplit(human=0.6, ai=0.6)


class TestJsonSchemaParity:
    """Schema JSON must match the Pydantic model on required keys."""

    def test_required_keys(self):
        required = set(SCHEMA_JSON["required"])
        # These must be present in any flattened-attr emission
        for key in (
            "tetrad.schema_version",
            "tetrad.enhance",
            "tetrad.obsolesce",
            "tetrad.retrieve",
            "tetrad.reverse",
        ):
            assert key in required

    def test_no_otel_namespace(self):
        for key in SCHEMA_JSON["properties"]:
            assert not key.startswith("otel."), "otel.* is reserved by OTel SIG"
