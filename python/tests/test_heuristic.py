"""Heuristic tagger: deterministic, keyword-driven."""

from __future__ import annotations

from tetrad_lens.heuristic import HeuristicTagger, tag_heuristically, token_count


class TestHeuristicTagger:
    def test_empty_text_is_unclear(self):
        span = tag_heuristically("")
        assert span.enhance.score == 0.0
        assert span.obsolesce.score == 0.0
        assert span.retrieve.score == 0.0
        assert span.reverse.score == 0.0
        assert span.tier == "heuristic"

    def test_enhance_keyword(self):
        span = tag_heuristically("This will accelerate code review and optimize CI throughput.")
        assert span.enhance.score >= 0.4
        assert "accelerate" in (span.enhance.rationale or "")

    def test_reverse_keyword(self):
        span = tag_heuristically("the agent fell into an infinite loop, reward hacking the eval")
        assert span.reverse.score >= 0.4

    def test_japanese_keyword(self):
        span = tag_heuristically("このエージェントは復活させる古いワークフローを取り戻す")
        assert span.retrieve.score >= 0.4

    def test_determinism(self):
        text = "automate writing of boilerplate, deprecate manual review"
        a = tag_heuristically(text)
        b = tag_heuristically(text)
        assert a.to_otel_attributes() == b.to_otel_attributes()

    def test_custom_keywords(self):
        tagger = HeuristicTagger(enhance_kw=("widgetize",))
        span = tagger.tag("we widgetize everything now")
        assert span.enhance.score >= 0.4


class TestTokenCount:
    def test_empty(self):
        assert token_count("") == 0

    def test_simple(self):
        assert token_count("hello world") == 2
