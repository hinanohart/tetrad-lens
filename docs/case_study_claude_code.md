# Case study: Claude Code + tetrad-lens

## Setup

Install the SDK and the Claude Code skill:

```bash
pip install "tetrad-lens[mcp]"
mkdir -p ~/.claude/skills
cp -r skills/tetrad-lens ~/.claude/skills/
```

Register the MCP server (same module as the Cline adapter — the protocol is shared):

```jsonc
// ~/.claude/mcp_servers.json
{
  "tetrad-lens": {
    "command": "python",
    "args": ["-m", "tetrad_lens.adapters.cline_mcp"]
  }
}
```

## Scenario

A user asks Claude Code: **"add a CSV export endpoint to the analytics service, and pre-warm it with the last 30 days of data."**

## What the three-tier tagger sees

Claude Code's plan, as captured by Langfuse:

> "I'll add `GET /export/csv` to the analytics service. To avoid first-hit latency, I'll schedule a nightly job that builds the CSV ahead of time and stores it in object storage."

Tier 1 (heuristic) returns:

```json
{
  "tetrad.enhance":   0.6,
  "tetrad.obsolesce": 0.0,
  "tetrad.retrieve":  0.0,
  "tetrad.reverse":   0.0,
  "tetrad.tier":      "heuristic",
  "tetrad.enhance.rationale": "enhance keywords matched: optimize, throughput"
}
```

The skill (via `mcp__tetrad-lens__tetrad_tag use_llm=true`) escalates to Tier 2:

```json
{
  "tetrad.enhance":   0.7,
  "tetrad.obsolesce": 0.2,
  "tetrad.retrieve":  0.55,
  "tetrad.reverse":   0.45,
  "tetrad.tier":      "llm",
  "tetrad.confidence": 0.81,
  "tetrad.retrieve.rationale":
    "Pre-warming retrieves the older 'nightly batch + static file' pattern that interactive APIs had moved away from.",
  "tetrad.reverse.rationale":
    "At the limit, a stale pre-built CSV reverses into 'fresh-data API that lies' — exactly the failure mode pre-warming was meant to avoid."
}
```

## What the reviewer does

`confidence=0.81 >= 0.8`, so the span is **not** auto-queued for review. The user reads the four scores in the skill's response and decides whether to add a TTL or a freshness check before the CSV is served.

## What changed because of tetrad-lens

This is the kind of decision that a fast-moving code-gen session usually skips. Surfacing the `retrieve` and `reverse` axes as part of the agent's own output makes the second-order consequences visible at the moment of choice, not three sprints later when somebody files a stale-data bug.

## Engelbart H-LAM/T context

This case also writes `engelbart.level = "b"` on the parent span — the user is using Claude Code to improve *how they write the analytics service*, not just the service itself. The Bootstrap Institute's ABC framing (1990s) is what we're encoding; the original Engelbart 1962 SRI report should be cited for the broader H-LAM/T concept, not for the A/B/C levels themselves.
