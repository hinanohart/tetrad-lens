"""Tier 1: heuristic tagger.

Keyword and structural rules. Deterministic. Cheap. Wrong often, but in
predictable ways — that is the point. Tier 2 (LLM) and Tier 3 (human) are for
the cases this tier punts on.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field

from tetrad_lens.schema import TetradScore, TetradSpan

# Rules are intentionally minimal and easy to extend per-project.
DEFAULT_ENHANCE_KEYWORDS: tuple[str, ...] = (
    "speed up",
    "accelerate",
    "optimize",
    "throughput",
    "automate writing",
    "高速化",
    "加速",
    "効率化",
    "強化",
)
DEFAULT_OBSOLESCE_KEYWORDS: tuple[str, ...] = (
    "deprecate",
    "replace",
    "no longer needed",
    "remove manual",
    "陳腐化",
    "不要",
    "置き換え",
)
DEFAULT_RETRIEVE_KEYWORDS: tuple[str, ...] = (
    "revive",
    "bring back",
    "rediscover",
    "long-form",
    "復活",
    "取り戻",
    "再発見",
)
DEFAULT_REVERSE_KEYWORDS: tuple[str, ...] = (
    "infinite loop",
    "reward hacking",
    "hallucinat",
    "spam",
    "abuse",
    "暴走",
    "反転",
    "ハルシネーション",
)


def _hit_score(text: str, keywords: Sequence[str]) -> tuple[float, list[str]]:
    """Return (score in [0,1], list of matched keywords)."""
    hits: list[str] = []
    lowered = text.lower()
    for kw in keywords:
        if kw.lower() in lowered:
            hits.append(kw)
    if not hits:
        return 0.0, hits
    # Capped logistic: 1 hit -> 0.4, 2 -> 0.6, 3 -> 0.75, 4+ -> 0.85
    table = [0.0, 0.4, 0.6, 0.75, 0.85]
    return table[min(len(hits), len(table) - 1)], hits


@dataclass
class HeuristicTagger:
    enhance_kw: Sequence[str] = field(default_factory=lambda: DEFAULT_ENHANCE_KEYWORDS)
    obsolesce_kw: Sequence[str] = field(default_factory=lambda: DEFAULT_OBSOLESCE_KEYWORDS)
    retrieve_kw: Sequence[str] = field(default_factory=lambda: DEFAULT_RETRIEVE_KEYWORDS)
    reverse_kw: Sequence[str] = field(default_factory=lambda: DEFAULT_REVERSE_KEYWORDS)

    def tag(self, text: str) -> TetradSpan:
        e_score, e_hits = _hit_score(text, self.enhance_kw)
        o_score, o_hits = _hit_score(text, self.obsolesce_kw)
        r_score, r_hits = _hit_score(text, self.retrieve_kw)
        v_score, v_hits = _hit_score(text, self.reverse_kw)

        def _rationale(label: str, hits: list[str]) -> str | None:
            if not hits:
                return None
            return f"{label} keywords matched: {', '.join(hits)}"

        return TetradSpan(
            enhance=TetradScore(score=e_score, rationale=_rationale("enhance", e_hits)),
            obsolesce=TetradScore(score=o_score, rationale=_rationale("obsolesce", o_hits)),
            retrieve=TetradScore(score=r_score, rationale=_rationale("retrieve", r_hits)),
            reverse=TetradScore(score=v_score, rationale=_rationale("reverse", v_hits)),
            tier="heuristic",
        )


# Module-level convenience for the most common call site.
_DEFAULT = HeuristicTagger()


def tag_heuristically(text: str) -> TetradSpan:
    return _DEFAULT.tag(text)


# Tiny utility: count whitespace-separated tokens (used elsewhere for length-based heuristics).
_WS = re.compile(r"\s+")


def token_count(text: str) -> int:
    return len(_WS.split(text.strip())) if text.strip() else 0
