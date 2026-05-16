"""Tier 2: LLM-assisted tagger.

Calls a local Ollama model twice with the four laws presented under different
permutations so the model cannot anchor on a fixed position. We then average
the two readings per axis and turn the per-axis disagreement into a
``tetrad.confidence`` score so consumers can route low-confidence spans to the
human review queue. The position-bias and reliability framing follows the
Judge Reliability Harness (arXiv 2603.05399) and the bias-stress numbers in
arXiv 2605.06939.

Key correctness invariants:

* The two prompts use *renamed* axis aliases (``law_1..law_4``) so the JSON
  output key order genuinely varies between calls — simply re-ordering the
  bullet list under the prompt header would still funnel the model toward the
  canonical key order in the JSON shape requirement.
* If the model returns malformed JSON or refuses to answer for a single axis,
  the tagger logs at WARNING and falls back **per axis** to the heuristic
  tagger rather than discarding the whole span.
* If the Ollama package is not installed at all the tagger logs once and
  returns ``None`` so callers can route to heuristic.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from tetrad_lens.heuristic import HeuristicTagger
from tetrad_lens.schema import TetradScore, TetradSpan

_LOG = logging.getLogger(__name__)

_AXES: tuple[str, str, str, str] = ("enhance", "obsolesce", "retrieve", "reverse")

_AXIS_DEFINITIONS = {
    "enhance": "What does the action enhance, amplify, intensify, or accelerate?",
    "obsolesce": "What does the action render obsolete or displace?",
    "retrieve": "What previously obsolesced practice does the action revive?",
    "reverse": "When pushed to its limits, what does the action reverse into?",
}


def _build_aliased_prompt(text: str, alias_to_axis: dict[str, str]) -> str:
    """Build a prompt that asks for scores by alias name (``law_1`` etc.).

    The JSON output is required to use the alias names in the order they
    appear in ``alias_to_axis``. The caller decodes them back to the canonical
    axis names. This is what makes position-swap actually mitigate position
    bias: the model genuinely sees four different label sets between the two
    calls, not just the same JSON keys in a different bullet order.
    """
    aliases_in_order = list(alias_to_axis.keys())
    json_shape = ", ".join(f'"{a}"' for a in aliases_in_order)
    parts = [
        "You are scoring an AI agent action against the McLuhan tetrad "
        "(Laws of Media, McLuhan & McLuhan 1988).\n",
        f"For each of the four laws, return a score in [0, 1] and a one-sentence rationale. "
        f"Reply in strict JSON with exactly these keys in this order: {json_shape}. "
        f'Each value is a {{"score": <number in [0,1]>, "rationale": <one sentence>}} object. '
        f"No prose outside the JSON.\n\n",
        f"Action under review:\n```\n{text}\n```\n\n",
        "Laws:\n",
    ]
    for alias, axis in alias_to_axis.items():
        parts.append(f"- {alias}: {_AXIS_DEFINITIONS[axis]}\n")
    parts.append("\nReturn JSON only.")
    return "".join(parts)


def _alias_map_a() -> dict[str, str]:
    return {f"law_{i + 1}": axis for i, axis in enumerate(_AXES)}


def _alias_map_b() -> dict[str, str]:
    reversed_axes = tuple(reversed(_AXES))
    return {f"law_{i + 1}": axis for i, axis in enumerate(reversed_axes)}


@dataclass
class LLMTagger:
    """Position-swap consensus tagger backed by an Ollama-compatible local model."""

    model: str = "llama3.2"
    host: str | None = None
    timeout_s: float = 30.0
    num_predict: int = 1024
    heuristic_fallback: HeuristicTagger = field(default_factory=HeuristicTagger)

    def _call_ollama(self, prompt: str) -> dict[str, Any]:
        try:
            import ollama  # type: ignore[import-not-found]
        except Exception:
            _LOG.warning("ollama package not installed; LLM tagger will return None")
            return {}
        try:
            client = ollama.Client(host=self.host) if self.host else ollama.Client()
            response = client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                format="json",
                options={"temperature": 0.0, "num_predict": self.num_predict},
            )
            content = response["message"]["content"]
            parsed: dict[str, Any] = json.loads(content)
            return parsed
        except Exception as exc:
            _LOG.warning("Ollama call failed: %s", exc)
            return {}

    @staticmethod
    def _decode_aliased(
        result: dict[str, Any], alias_to_axis: dict[str, str]
    ) -> dict[str, tuple[float, str] | None]:
        """Return a per-axis (score, rationale) map. Missing/malformed axes are ``None``."""
        decoded: dict[str, tuple[float, str] | None] = {axis: None for axis in _AXES}
        for alias, axis in alias_to_axis.items():
            entry = result.get(alias)
            if not isinstance(entry, dict):
                continue
            score_raw = entry.get("score")
            rationale_raw = entry.get("rationale", "") or ""
            try:
                score = float(score_raw)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                continue
            score = max(0.0, min(1.0, score))
            decoded[axis] = (score, str(rationale_raw))
        return decoded

    def tag(self, text: str) -> TetradSpan | None:
        prompt_a = _build_aliased_prompt(text, _alias_map_a())
        prompt_b = _build_aliased_prompt(text, _alias_map_b())

        raw_a = self._call_ollama(prompt_a)
        raw_b = self._call_ollama(prompt_b)
        if not raw_a and not raw_b:
            return None

        decoded_a = self._decode_aliased(raw_a, _alias_map_a())
        decoded_b = self._decode_aliased(raw_b, _alias_map_b())

        fallback = self.heuristic_fallback.tag(text)
        fallback_axes: dict[str, TetradScore] = {
            "enhance": fallback.enhance,
            "obsolesce": fallback.obsolesce,
            "retrieve": fallback.retrieve,
            "reverse": fallback.reverse,
        }

        axes: dict[str, TetradScore] = {}
        disagreements: list[float] = []
        fell_back_axes: list[str] = []
        for axis in _AXES:
            a = decoded_a.get(axis)
            b = decoded_b.get(axis)
            if a is None and b is None:
                axes[axis] = fallback_axes[axis]
                fell_back_axes.append(axis)
                # Heuristic and LLM disagree maximally by definition; assign 0.5
                # so the confidence penalty is non-zero but not crushing.
                disagreements.append(0.5)
                continue
            if a is None:
                score, rationale = b  # type: ignore[misc]
                disagreements.append(0.5)
            elif b is None:
                score, rationale = a
                disagreements.append(0.5)
            else:
                score_a, rationale_a = a
                score_b, rationale_b = b
                score = (score_a + score_b) / 2.0
                disagreements.append(abs(score_a - score_b))
                rationale = rationale_a if len(rationale_a) >= len(rationale_b) else rationale_b

            # Schema requires a rationale when score >= 0.5 — supply a placeholder
            # if the model omitted one rather than letting the Pydantic validator
            # blow up the whole span.
            if score >= 0.5 and not (rationale or "").strip():
                rationale = "LLM tagger returned no rationale; review recommended."

            axes[axis] = TetradScore(score=score, rationale=(rationale or None))

        avg_disagree = sum(disagreements) / len(disagreements)
        confidence = max(0.0, 1.0 - 2.0 * avg_disagree)

        if fell_back_axes:
            _LOG.warning(
                "LLM tagger fell back to heuristic for axes %s; confidence reduced to %.2f",
                fell_back_axes,
                confidence,
            )

        return TetradSpan(
            enhance=axes["enhance"],
            obsolesce=axes["obsolesce"],
            retrieve=axes["retrieve"],
            reverse=axes["reverse"],
            tier="llm",
            confidence=confidence,
        )
