"""Cline MCP adapter.

Exposes a single MCP tool, `tetrad_tag`, that accepts a snippet of text and
returns the tetrad scores in the same shape the SDK uses. Cline (or any other
MCP client) registers this server via its `mcpServers` config.

Run as a stand-alone server:

    python -m tetrad_lens.adapters.cline_mcp

Or, in Cline's config:

    {
      "mcpServers": {
        "tetrad-lens": {
          "command": "python",
          "args": ["-m", "tetrad_lens.adapters.cline_mcp"]
        }
      }
    }

If the `mcp` package is not installed (`pip install tetrad-lens[mcp]`), the
module logs a message and exits non-zero rather than silently doing nothing.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from tetrad_lens.heuristic import tag_heuristically
from tetrad_lens.llm_tagger import LLMTagger
from tetrad_lens.masking import mask_text


def _tag(text: str, use_llm: bool) -> dict[str, Any]:
    masked = mask_text(text)
    if use_llm:
        llm = LLMTagger()
        span = llm.tag(masked)
        if span is not None:
            return span.to_otel_attributes()
    span = tag_heuristically(masked)
    return span.to_otel_attributes()


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

    @server.tool()  # type: ignore[misc, untyped-decorator]
    def tetrad_tag(text: str, use_llm: bool = False) -> str:
        """Return tetrad attributes for the given text as a JSON string.

        Args:
            text: snippet of agent output, code, plan, or transcript to tag.
            use_llm: if true, prefer the LLM-assisted tagger (requires Ollama).
        """
        return json.dumps(_tag(text, use_llm=use_llm), ensure_ascii=False)

    server.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
