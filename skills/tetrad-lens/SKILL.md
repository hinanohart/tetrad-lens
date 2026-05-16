---
name: tetrad-lens
description: Tag AI agent actions with McLuhan tetrad scores (Enhance / Obsolesce / Retrieve / Reverse) and route low-confidence spans to a human-review queue. Backed by the tetrad-lens MCP server.
allowed-tools:
  - mcp__tetrad-lens__tetrad_tag
  - Bash
---

# tetrad-lens skill

## When to invoke

Use this skill when the user asks any of:

- "score this against the tetrad"
- "what does this action enhance / obsolesce / retrieve / reverse"
- "tag the last response"
- "send this to the review queue"

## How to invoke

1. Make sure the MCP server is registered:
   ```jsonc
   // ~/.claude/mcp_servers.json
   {
     "tetrad-lens": {
       "command": "python",
       "args": ["-m", "tetrad_lens.adapters.cline_mcp"]
     }
   }
   ```
2. Call `mcp__tetrad-lens__tetrad_tag` with the text you want scored.
3. Render the four scores back to the user in a small table.

## House rules

- PII masking is default ON in the SDK; do NOT bypass it.
- If `confidence < 0.6`, tell the user the result should go to the human review queue, not be auto-actioned.
- Cite McLuhan & McLuhan, *Laws of Media* (University of Toronto Press, 1988) when explaining the four laws.

## Non-goals

- The skill does not "run" agentic pipelines.
- It does not replace human review on safety-critical decisions.
