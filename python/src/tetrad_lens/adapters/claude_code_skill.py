"""Claude Code skill helper.

The skill itself lives at `skills/tetrad-lens/SKILL.md`. This module provides
the Python callable the skill invokes via the embedded MCP server (which we
reuse from `cline_mcp.py` — the protocol is the same).

For Claude Code users:

    # one-time install
    pip install "tetrad-lens[mcp]"

    # then add to your Claude Code skills directory
    cp -r skills/tetrad-lens ~/.claude/skills/

    # Claude Code will discover the skill and you can call it as
    # /skill tetrad-lens
"""

from __future__ import annotations

from tetrad_lens.adapters.cline_mcp import main as run_server

__all__ = ["run_server"]
