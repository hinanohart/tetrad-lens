"""Tier 2: LLM-assisted tagger.

Calls a local Ollama model twice with the four laws presented in two different
orders (position-swap consensus, mitigates the position bias documented in
arXiv 2603.05399 / 2605.06939) and computes a per-axis disagreement metric.
The disagreement feeds `tetrad.confidence` so consumers can route low-confidence
spans to the human review queue.

This module is deliberately conservative: if Ollama is not available it returns
an empty result rather than guessing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from tetrad_lens.schema import TetradScore, TetradSpan

_AXES = ("enhance", "obsolesce", "retrieve", "reverse")

_PROMPT_HEADER = (
    "You are scoring an AI agent action against the McLuhan tetrad "
    "(Laws of Media, McLuhan & McLuhan 1988). For each of the four laws, "
    "return a score in [0, 1] and a one-sentence rationale. "
    "Reply in strict JSON with keys: enhance, obsolesce, retrieve, reverse, "
    "each a {score, rationale} object. No prose outside the JSON.\n\n"
)

_AXIS_DEFINITIONS = {
    "enhance": "What does the action enhance, amplify, intensify, or accelerate?",
    "obsolesce": "What does the action render obsolete or displace?",
    "retrieve": "What previously obsolesced practice does the action revive?",
    "reverse": "When pushed to its limits, what does the action reverse into?",
}


def _build_prompt(text: str, order: tuple[str, ...]) -> str:
    parts = [_PROMPT_HEADER, f"Action under review:\n```\n{text}\n```\n\n", "Laws:\n"]
    for axis in order:
        parts.append(f"- {axis}: {_AXIS_DEFINITIONS[axis]}\n")
    parts.append("\nReturn JSON only.")
    return "".join(parts)


@dataclass
class LLMTagger:
    """Position-swap consensus tagger backed by an Ollama-compatible local model."""

    model: str = "llama3.2"
    host: str | None = None
    timeout_s: float = 30.0

    def _call_ollama(self, prompt: str) -> dict[str, Any]:
        try:
            import ollama  # type: ignore[import-not-found]
        except Exception:
            return {}
        client = ollama.Client(host=self.host) if self.host else ollama.Client()
        response = client.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            format="json",
            options={"temperature": 0.0, "num_predict": 512},
        )
        try:
            content = response["message"]["content"]
            parsed: dict[str, Any] = json.loads(content)
            return parsed
        except Exception:
            return {}

    def tag(self, text: str) -> TetradSpan | None:
        order_a: tuple[str, ...] = _AXES
        order_b: tuple[str, ...] = tuple(reversed(_AXES))

        result_a = self._call_ollama(_build_prompt(text, order_a))
        if not result_a:
            return None
        result_b = self._call_ollama(_build_prompt(text, order_b))
        if not result_b:
            return None

        axes: dict[str, TetradScore] = {}
        disagreements: list[float] = []
        for axis in _AXES:
            try:
                score_a = float(result_a[axis]["score"])
                score_b = float(result_b[axis]["score"])
                rationale_a = str(result_a[axis].get("rationale", "") or "")
                rationale_b = str(result_b[axis].get("rationale", "") or "")
            except (KeyError, TypeError, ValueError):
                return None
            mean = (score_a + score_b) / 2.0
            disagreements.append(abs(score_a - score_b))
            chosen_rationale = rationale_a if len(rationale_a) >= len(rationale_b) else rationale_b
            axes[axis] = TetradScore(
                score=max(0.0, min(1.0, mean)),
                rationale=(chosen_rationale or None) if mean >= 0.5 else (chosen_rationale or None),
            )

        # Confidence falls as disagreement rises. avg disagreement of 0 -> conf 1.0,
        # avg disagreement of 0.5 -> conf ~0.0.
        avg_disagree = sum(disagreements) / len(disagreements)
        confidence = max(0.0, 1.0 - 2.0 * avg_disagree)

        return TetradSpan(
            enhance=axes["enhance"],
            obsolesce=axes["obsolesce"],
            retrieve=axes["retrieve"],
            reverse=axes["reverse"],
            tier="llm",
            confidence=confidence,
        )
