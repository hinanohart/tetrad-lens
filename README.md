# tetrad-lens

> A McLuhan-tetrad-shaped attribute schema and three-tier tagger for AI agent traces, on top of Langfuse and OpenTelemetry.

[![CI](https://github.com/hinanohart/tetrad-lens/actions/workflows/ci.yml/badge.svg)](https://github.com/hinanohart/tetrad-lens/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/tetrad-lens.svg)](https://pypi.org/project/tetrad-lens/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Schema](https://img.shields.io/badge/schema-tetrad--v1-7c3aed.svg)](schema/tetrad-v1.json)

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

```bash
pip install "tetrad-lens"             # core
pip install "tetrad-lens[mcp]"        # + Cline / Claude Code MCP adapter
pip install "tetrad-lens[ollama]"     # + LLM-assisted tagger
```

## Quickstart

```python
from tetrad_lens import observe
from tetrad_lens.heuristic import tag_heuristically
from tetrad_lens.sdk import tag_current_span

@observe(name="my-step")
def do_thing(plan: str) -> str:
    span_data = tag_heuristically(plan)   # Tier 1 (deterministic)
    tag_current_span(span_data)            # attaches tetrad.* attributes
    return run(plan)
```

Then open Langfuse and filter on `attribute["tetrad.reverse"] >= 0.5` for high second-order-risk spans. More filter recipes are in [`examples/langfuse_dashboard_filter.md`](examples/langfuse_dashboard_filter.md).

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

See [`docs/roadmap.md`](docs/roadmap.md). Highlights: TypeScript SDK parity, optional Hot/Cold and Acoustic Space axes, OpenTelemetry OTEP submission once two-language prototype is ready.

## Co-maintainer wanted

Solo maintainer burnout has a 60% rate in 2026 across small-to-mid OSS projects. This project carries a 4-week co-maintainer-recruitment KPI from day one; if it is not met, the README will say so honestly and v0.2 may move to archive. See [`.github/ISSUE_TEMPLATE/co-maintainer-wanted.md`](.github/ISSUE_TEMPLATE/co-maintainer-wanted.md).

## Acknowledgements

- **Marshall McLuhan** and **Eric McLuhan**, *Laws of Media: The New Science* (University of Toronto Press, 1988) — the tetrad.
- **Douglas C. Engelbart**, "Augmenting Human Intellect" (SRI International, 1962) — the H-LAM/T framework. The A/B/C levels are the Bootstrap Institute's 1990s extension on top of that paper.
- **Alexander R. Galloway**, *Protocol: How Control Exists after Decentralization* (MIT Press, 2004) — the framing that "the schema is the artifact."
- The Langfuse and OpenTelemetry communities for the surface this project hooks into.

## License

[Apache-2.0](LICENSE).
