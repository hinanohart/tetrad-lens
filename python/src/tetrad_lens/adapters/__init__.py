"""Adapters for the two v0.1 host environments.

- `cline_mcp` — a minimal MCP server you can register with Cline that exposes
  a `tetrad_tag` tool the editor agent can call to add tetrad attributes.
- `claude_code_skill` — a thin helper that pairs with the
  `skills/tetrad-lens/SKILL.md` skill manifest to do the same inside Claude Code.

v0.2+ may add Aider, OpenHands, etc. once their plugin APIs stabilise.
"""
