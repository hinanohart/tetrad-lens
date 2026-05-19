# tetrad-lens

> A McLuhan-tetrad-shaped attribute schema and three-tier tagger for AI agent traces, on top of Langfuse and OpenTelemetry.

[![CI](https://github.com/hinanohart/tetrad-lens/actions/workflows/ci.yml/badge.svg)](https://github.com/hinanohart/tetrad-lens/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Schema](https://img.shields.io/badge/schema-tetrad--v1-7c3aed.svg)](schema/tetrad-v1.json)

> **v0.1.0 status**: ship-published on GitHub, not yet on PyPI. Install from source as shown below until the PyPI Trusted Publisher is live (tracked in [issue #5](https://github.com/hinanohart/tetrad-lens/issues/5) alongside the co-maintainer ask).

---

## What it is

`tetrad-lens` adds **four McLuhan-shaped attributes** to every AI agent span:

| Attribute            | Question (McLuhan & McLuhan, *Laws of Media*, 1988) |
|----------------------|---------------------------------------------------|
| `tetrad.enhance`     | What does it enhance, amplify, intensify, accelerate? |
| `tetrad.obsolesce`   | What does it render obsolete or displace? |
| `tetrad.retrieve`    | What previously obsolesced practice does it revive? |
| `tetrad.reverse`     | When pushed to its limits, what does it reverse into? |

Each one is a score in `[0, 1]` plus a free-text rationale. They are written as OpenTelemetry span attributes under the `tetrad.*` namespace, picked up by Langfuse, and made queryable from the standard Langfuse Scores filter.

A second axis records the **Engelbart H-LAM/T augmentation level** the trace lives at (`engelbart.level ∈ {a, b, c}`, using the Bootstrap Institute 1990s ABC framing on top of Engelbart's 1962 SRI report).

## What it is not

- Not a standalone observability platform — it is a plugin on top of [Langfuse](https://langfuse.com).
- Not an authoritative LLM judge — the human-review queue (`ScoreSource=ANNOTATION`) always overrides automated tags.
- Not an agent OS. A `Layer 4` self-running pipeline was considered and dropped during design; see [`docs/architecture.md`](docs/architecture.md).
- Not a McLuhan estate publication — the four laws and the *Laws of Media* book are credited per `CITATION.cff`.

## Why

Observability for AI agents in 2026 is good at *what the agent did* and bad at *what the agent's action means*. McLuhan's tetrad gives a shape for the second question that takes a couple of hours to learn, and (importantly) surfaces the **reverse** axis — the second-order failure mode — that fast iteration loops tend to skip past.

If your agent ships a refactor that enhances throughput but reverses into silent under-billing, you want `tetrad.reverse` lighting up before the migration runs, not in the post-mortem.

## Install

Until v0.1.0 lands on PyPI, install from this repo:

```bash
# core
pip install "git+https://github.com/hinanohart/tetrad-lens@v0.1.0#subdirectory=python"

# + Cline / Claude Code MCP adapter
pip install "tetrad-lens[mcp] @ git+https://github.com/hinanohart/tetrad-lens@v0.1.0#subdirectory=python"

# + LLM-assisted tagger (requires a local Ollama instance)
pip install "tetrad-lens[ollama] @ git+https://github.com/hinanohart/tetrad-lens@v0.1.0#subdirectory=python"
```

Once PyPI is live, this collapses to the conventional form:

```bash
pip install "tetrad-lens"           # core
pip install "tetrad-lens[mcp]"      # + MCP adapter
pip install "tetrad-lens[ollama]"   # + LLM-assisted tagger
```

## Quickstart

```python
from tetrad_lens import observe, tag_current_span, tag_heuristically

@observe(name="my-step")
def do_thing(plan: str) -> dict[str, str]:
    span_data = tag_heuristically(plan)   # Tier 1 (deterministic)
    tag_current_span(span_data)           # attaches tetrad.* attributes
    return {"plan": plan, "tetrad": span_data.to_otel_attributes()}

do_thing(
    "Replace the nightly poll job with the new event bus. "
    "If the bus ever stalls, billing reconciliation silently halts."
)
```

The second sentence in the input is what `tetrad.reverse` should fire on — pushed to its limit, the change reverses into "no billing at all". Open Langfuse and filter `attribute["tetrad.reverse"] >= 0.5` to surface those spans; more filter recipes are in [`examples/langfuse_dashboard_filter.md`](examples/langfuse_dashboard_filter.md).

Without `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` in your environment the SDK keeps working — attributes are attached to the local OTel span and the Langfuse exporter is a no-op. Langfuse's "no public_key" warnings are silenced by default; pass `install_processor(silence_langfuse_auth_warnings=False)` to re-enable them.

## Three tiers, on purpose

```
Tier 1  heuristic    keyword / structural rules, deterministic, cheap
Tier 2  LLM-assisted  Ollama local + position-swap consensus
                      confidence = 1 − 2·avg_disagreement
                      (Judge Reliability Harness, arXiv 2603.05399)
Tier 3  human queue   Langfuse Score API, ScoreSource=ANNOTATION
                      always wins over Tier 1 + Tier 2
```

LLM-as-judge is known to be unreliable on subtle judgements (production frontier models score around 50% on bias-stress tests; position bias alone causes ~40% GPT-4 inconsistency, see arXiv 2605.06939). `tetrad-lens` treats Tier 2 as *suggestive* and routes low-confidence spans to Tier 3 instead of pretending the LLM got it right.

## Adapters

| Host          | Adapter                                                                                              | v0.x status |
|---------------|------------------------------------------------------------------------------------------------------|-------------|
| Cline         | [`python/src/tetrad_lens/adapters/cline_mcp.py`](python/src/tetrad_lens/adapters/cline_mcp.py)      | shipped     |
| Claude Code   | [`skills/tetrad-lens/SKILL.md`](skills/tetrad-lens/SKILL.md) + the same MCP server                  | shipped     |
| Aider         | —                                                                                                    | v0.2 (waiting on plugin API) |
| OpenHands     | —                                                                                                    | v0.2        |

## Schema

JSON Schema 2020-12 lives at [`schema/tetrad-v1.json`](schema/tetrad-v1.json). It is the cross-language contract — Pydantic models in `python/src/tetrad_lens/schema.py` mirror it and the `TestJsonSchemaParity` test enforces required-key parity.

`tetrad.figure_ground` is exposed in the schema but is **DERIVED, read-only** — producers do not set it, consumers compute it. See [`docs/figure_ground_critique_response.md`](docs/figure_ground_critique_response.md) for why.

## Roadmap

See [`docs/roadmap.md`](docs/roadmap.md). Highlights: PyPI Trusted-Publisher (v0.1.1), TypeScript SDK parity (v0.1.x; note the Vercel OpenTelemetry integration is **not** API-compatible with Langfuse v4's exporter), optional Hot/Cold and Acoustic Space axes, OpenTelemetry OTEP submission once a two-language prototype is ready.

## Co-maintainer wanted

Solo maintainer burnout has a 60% rate in 2026 across small-to-mid OSS projects. This project carries a 4-week co-maintainer-recruitment KPI from day one; if it is not met, the README will say so honestly and v0.2 may move to archive. See [`.github/ISSUE_TEMPLATE/co-maintainer-wanted.md`](.github/ISSUE_TEMPLATE/co-maintainer-wanted.md).

## Acknowledgements

- **Marshall McLuhan** and **Eric McLuhan**, *Laws of Media: The New Science* (University of Toronto Press, 1988) — the tetrad.
- **Douglas C. Engelbart**, "Augmenting Human Intellect" (SRI International, 1962) — the H-LAM/T framework. The A/B/C levels are the Bootstrap Institute's 1990s extension on top of that paper.
- **Alexander R. Galloway**, *Protocol: How Control Exists after Decentralization* (MIT Press, 2004) — the framing that "the schema is the artifact."
- The Langfuse and OpenTelemetry communities for the surface this project hooks into.

## License

[MIT](LICENSE).
