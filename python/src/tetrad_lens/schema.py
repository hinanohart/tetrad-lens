"""Pydantic models that mirror schema/tetrad-v1.json.

Keep this in sync with the JSON schema. The JSON schema is the source of truth
for cross-language consumers; this module is the Python ergonomic layer.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

FigureGround = Literal["figure", "ground", "both", "unclear"]
Tier = Literal["heuristic", "llm", "annotation"]
EngelbartLevel = Literal["a", "b", "c"]


class TetradScore(BaseModel):
    """One axis of the tetrad: a [0,1] score plus an optional rationale."""

    score: float = Field(ge=0.0, le=1.0)
    rationale: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _require_rationale_when_strong(self) -> TetradScore:
        if self.score >= 0.5 and not (self.rationale and self.rationale.strip()):
            raise ValueError("rationale is required when score >= 0.5 (see schema/tetrad-v1.json)")
        return self


class RoleSplit(BaseModel):
    human: float = Field(ge=0.0, le=1.0, default=0.0)
    ai: float = Field(ge=0.0, le=1.0, default=0.0)

    @model_validator(mode="after")
    def _sum_le_one(self) -> RoleSplit:
        if self.human + self.ai > 1.0 + 1e-9:
            raise ValueError("human + ai must be <= 1.0 (remainder is unattributed)")
        return self


class TetradSpan(BaseModel):
    """One span's worth of tetrad-lens data, ready to be flattened into OTel attributes."""

    schema_version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    enhance: TetradScore
    obsolesce: TetradScore
    retrieve: TetradScore
    reverse: TetradScore
    tier: Tier
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    engelbart_level: EngelbartLevel | None = None
    engelbart_role_split: RoleSplit | None = None

    @model_validator(mode="after")
    def _llm_needs_confidence(self) -> TetradSpan:
        if self.tier == "llm" and self.confidence is None:
            raise ValueError("tier='llm' requires confidence to be set (Judge Reliability Harness)")
        return self

    def to_otel_attributes(self) -> dict[str, float | str]:
        """Flatten to the dotted-attribute form used by the OpenTelemetry SDK."""
        attrs: dict[str, float | str] = {
            "tetrad.schema_version": self.schema_version,
            "tetrad.enhance": self.enhance.score,
            "tetrad.obsolesce": self.obsolesce.score,
            "tetrad.retrieve": self.retrieve.score,
            "tetrad.reverse": self.reverse.score,
            "tetrad.tier": self.tier,
        }
        for axis_name, axis in (
            ("enhance", self.enhance),
            ("obsolesce", self.obsolesce),
            ("retrieve", self.retrieve),
            ("reverse", self.reverse),
        ):
            if axis.rationale:
                attrs[f"tetrad.{axis_name}.rationale"] = axis.rationale
        if self.confidence is not None:
            attrs["tetrad.confidence"] = self.confidence
        if self.engelbart_level is not None:
            attrs["engelbart.level"] = self.engelbart_level
        if self.engelbart_role_split is not None:
            attrs["engelbart.role_split.human"] = self.engelbart_role_split.human
            attrs["engelbart.role_split.ai"] = self.engelbart_role_split.ai
        return attrs


def figure_ground_of(span: TetradSpan, *, high: float = 0.6, low: float = 0.2) -> FigureGround:
    """Derive tetrad.figure_ground from the four scores.

    This is a *consumer-side* derivation. Producers MUST NOT emit
    tetrad.figure_ground directly (schema rule). Thresholds are tunable:

    * ``high`` — minimum mean (enhance+retrieve)/2 or (obsolesce+reverse)/2
      for a side to count as "dominant".
    * ``low`` — if NO axis exceeds ``low`` we return "unclear" (no signal);
      otherwise the mixed-signal case also collapses to "unclear" but the
      caller can inspect ``low`` to distinguish "weak signal" from "noisy"
      via the raw scores on the span itself.

    The schema only defines four enum values; "weak signal" and "noisy" both
    map to "unclear" by design. Keep ``low`` in the signature so callers can
    rebuild the partition without re-implementing the rest of the rule.
    """
    e, o, r, v = (
        span.enhance.score,
        span.obsolesce.score,
        span.retrieve.score,
        span.reverse.score,
    )
    figure = (e + r) / 2.0
    ground = (o + v) / 2.0
    if figure >= high and ground >= high:
        return "both"
    if figure >= high:
        return "figure"
    if ground >= high:
        return "ground"
    _ = low  # currently informational; see docstring
    return "unclear"
