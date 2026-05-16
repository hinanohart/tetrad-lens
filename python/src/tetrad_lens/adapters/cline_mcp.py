"""Cline / Claude Code MCP adapter.

Exposes one MCP tool, ``tetrad_tag``, that accepts a snippet of text and
returns the tetrad scores in the same shape the SDK uses. The protocol is
plain MCP over stdio — any MCP client (Cline, Claude Code, OpenHands, custom)
can mount it.

Run as a stand-alone server::

    python -m tetrad_lens.adapters.cline_mcp

Cline config (``mcpServers`` block in Cline settings)::

    {
      "mcpServers": {
        "tetrad-lens": {
          "command": "python",
          "args": ["-m", "tetrad_lens.adapters.cline_mcp"]
        }
      }
    }

Claude Code config (drop into ``.mcp.json`` at the repo root, or merge into
``~/.claude.json``)::

    {
      "mcpServers": {
        "tetrad-lens": {
          "command": "python",
          "args": ["-m", "tetrad_lens.adapters.cline_mcp"]
        }
      }
    }

If the ``mcp`` package is not installed (``pip install tetrad-lens[mcp]``),
the module logs a message and exits non-zero rather than silently doing
nothing.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from tetrad_lens.heuristic import tag_heuristically
from tetrad_lens.llm_tagger import LLMTagger
from tetrad_lens.masking import mask_text

_LOG = logging.getLogger(__name__)


def _tag(text: str, use_llm: bool) -> dict[str, Any]:
    masked = mask_text(text)
    fallback_reason: str | None = None
    span = None
    if use_llm:
        try:
            span = LLMTagger().tag(masked)
        except Exception as exc:
            fallback_reason = f"llm_tagger_raised: {exc.__class__.__name__}"
            _LOG.warning("LLM tagger raised; falling back to heuristic: %s", exc)
        if span is None and fallback_reason is None:
            fallback_reason = "ollama_unreachable_or_empty_response"
    if span is None:
        span = tag_heuristically(masked)
    attrs = span.to_otel_attributes()
    if fallback_reason:
        attrs["tetrad._fallback_reason"] = fallback_reason
    return attrs


_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "text": {
            "type": "string",
            "description": (
                "Snippet of agent output, code, plan, or transcript to score against the "
                "McLuhan tetrad (Enhance / Obsolesce / Retrieve / Reverse). PII is masked "
                "before scoring."
            ),
            "minLength": 1,
            "maxLength": 100_000,
        },
        "use_llm": {
            "type": "boolean",
            "description": (
                "If true, run the LLM-assisted tagger (Tier 2; requires Ollama running "
                "locally). On failure or unavailability the response includes "
                "`tetrad._fallback_reason` and the heuristic result."
            ),
            "default": False,
        },
    },
    "required": ["text"],
    "additionalProperties": False,
}


def main() -> int:
    try:
        from mcp.server.fastmcp import FastMCP  # type: ignore[import-not-found]
    except Exception:
        sys.stderr.write(
            "tetrad_lens.adapters.cline_mcp: install with `pip install tetrad-lens[mcp]` "
            "to run the MCP server.\n"
        )
        return 2

    server = FastMCP("tetrad-lens")

    # FastMCP introspects type hints, but supplying name + description here gives
    # downstream MCP clients (Cline, Claude Code) a nicer tool card. The
    # JSON-Schema mirror is documented in `_INPUT_SCHEMA` above for clients that
    # introspect schemas directly via the MCP `tools/list` method.
    @server.tool(  # type: ignore[misc, untyped-decorator]
        name="tetrad_tag",
        description=(
            "Score a text snippet against the McLuhan tetrad (Enhance / Obsolesce / "
            "Retrieve / Reverse). PII is masked. Set use_llm=true for the Tier 2 "
            "LLM-assisted tagger; otherwise the deterministic Tier 1 heuristic runs. "
            "Returns the OpenTelemetry attribute dict the tetrad-lens SDK produces."
        ),
    )
    def tetrad_tag(text: str, use_llm: bool = False) -> str:
        return json.dumps(_tag(text, use_llm=use_llm), ensure_ascii=False)

    server.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
