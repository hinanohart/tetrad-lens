# Case study: Cline + tetrad-lens

## Setup

Cline is configured with a single MCP server pointing at `tetrad-lens`:

```jsonc
// Cline config
{
  "mcpServers": {
    "tetrad-lens": {
      "command": "python",
      "args": ["-m", "tetrad_lens.adapters.cline_mcp"]
    }
  }
}
```

Langfuse Cloud (or self-hosted) is reachable; the SDK auto-installs the `LangfuseSpanProcessor` the first time `@observe(...)` is hit.

## Scenario

A developer asks Cline to **"refactor `legacy_billing.py` to use the new event-bus client and delete the old polling job"**.

## What the three-tier tagger sees

The Cline session emits the following plan as part of its tool calls:

> "I will replace the polling loop with `EventBusClient.subscribe(...)`. The old `poll_billing()` function will be removed; downstream callers will receive events via callback. This will reduce DB load and remove ~120 lines of code."

Tier 1 (heuristic) immediately scores:

```json
{
  "tetrad.enhance":   0.6,
  "tetrad.obsolesce": 0.6,
  "tetrad.retrieve":  0.0,
  "tetrad.reverse":   0.0,
  "tetrad.tier":      "heuristic",
  "tetrad.enhance.rationale":   "enhance keywords matched: reduce, throughput-like phrasing",
  "tetrad.obsolesce.rationale": "obsolesce keywords matched: replace, remove manual"
}
```

The reviewer (or a follow-up Tier 2 call) asks the LLM tagger to look again. Tier 2 returns:

```json
{
  "tetrad.enhance":   0.55,
  "tetrad.obsolesce": 0.7,
  "tetrad.retrieve":  0.0,
  "tetrad.reverse":   0.35,
  "tetrad.tier":      "llm",
  "tetrad.confidence": 0.72,
  "tetrad.reverse.rationale":
    "At the limit, removing the poll job removes the only fallback if the event bus stalls — the change could reverse into 'silent under-billing' rather than 'lower DB load'."
}
```

That `reverse=0.35` is the McLuhan-shaped contribution: a plain code-review tool would not have surfaced it. Because `confidence=0.72 < 0.8`, the span is also queued to the Langfuse Score filter for a human reviewer to confirm.

## What the reviewer does

The reviewer opens the Langfuse dashboard, filters on `tetrad_v1.reverse > 0.3`, and lands on this span. They agree with the LLM's reading, post the annotation via `ReviewQueueClient.submit(...)` (which tags the score with the `[ANNOTATION:<annotator>]` comment prefix and `metadata.tetrad_lens.source = "ANNOTATION"` — the Langfuse v4 score API no longer takes a `source=` kwarg directly), and add a comment: *"need a watchdog on EventBusClient before the polling job is deleted"*. The annotation now becomes the authoritative reading for downstream analytics.

## What changed because of tetrad-lens

Without `tetrad-lens` the reviewer would have approved the refactor on a plain code-quality basis. With it, the **reverse axis** caught a second-order risk that nobody had asked about — exactly what McLuhan's fourth law is for.

## Repro

```bash
pip install "tetrad-lens[mcp,ollama]"
python -m tetrad_lens.adapters.cline_mcp &
# then follow the Cline MCP config above and run the scenario
```
