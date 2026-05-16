# Architecture (v0.1)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Layer 0  Distribution                                                │
│   GitHub (Apache-2.0) — shipped                                      │
│   PyPI — workflow scaffold in .github/workflows/publish.yml, needs   │
│          PyPI-side Trusted Publisher setup (v0.1.1)                  │
│   Claude Code skill — manual install via cp (per-project .mcp.json   │
│          or ~/.claude.json); marketplace submission not pursued      │
│          in v0.1                                                     │
│   Releases via release-please (googleapis/release-please-action@v4) │
└──────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Layer 1  Schema  (the cross-language contract)                       │
│   schema/tetrad-v1.json — JSON Schema 2020-12                        │
│   tetrad.{enhance,obsolesce,retrieve,reverse} ∈ [0,1] + rationale    │
│   tetrad.figure_ground  DERIVED, read-only                           │
│   tetrad.tier ∈ {heuristic, llm, annotation}                         │
│   tetrad.confidence ∈ [0,1]   (required when tier=llm)               │
│   engelbart.level ∈ {a,b,c}   (Bootstrap Institute 1990s extension)  │
│   tetrad.schema_version       (semver, producers MUST set)           │
└──────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Layer 2  SDK  (Python; TypeScript queued for v0.1.x — note Vercel   │
│           OTel exporter is NOT API-compatible with Langfuse v4)      │
│   @observe       wraps Langfuse @observe; preserves sync/async       │
│                  signature; ensures PII masking is wired in          │
│   install_processor()  sets client._mask on the Langfuse v4 client   │
│                        (assigning client.mask is silent no-op in v4) │
│                        and silences "no public_key" warnings         │
│   tag_current_span(span_data)   attaches tetrad attributes to the    │
│                        active OTel span AND pushes them into OTel    │
│                        baggage so child spans inherit                │
│   tetrad_context(name)  context-manager fallback for ad-hoc use      │
│   adapters/                                                          │
│     cline_mcp.py            MCP server exposing tetrad_tag tool      │
│     claude_code_skill.py    paired with skills/tetrad-lens/SKILL.md  │
│   Dual-emit toggle: OTEL_SEMCONV_STABILITY_OPT_IN=tetrad/dup  —      │
│        env var is RESERVED for v0.1.x dual-emit; not implemented yet │
│   PII masking: default ON, opt-out per trace; pattern set covers     │
│        email/phone/secret-prefix/bearer/SSN/JWT/IPv4/Luhn-valid CC   │
└──────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Layer 3  Three-tier tagger                                           │
│   ① heuristic.py      keyword / structural rules, deterministic      │
│   ② llm_tagger.py     Ollama local + position-swap consensus +       │
│                       confidence = 1 - 2·avg_disagreement            │
│                       (Judge Reliability Harness, arXiv 2603.05399)  │
│   ③ review_queue.py   Langfuse Score API (ScoreSource=ANNOTATION)    │
│                       ANNOTATION always wins                         │
└──────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Layer 5  Observation surface                                         │
│   Langfuse standard chart + Score filter on tetrad_v1.{...}          │
│   No custom UI in v0.1 (deferred to v0.2+, intentionally)            │
└──────────────────────────────────────────────────────────────────────┘
```

## Why Layer 4 is missing

The original design considered a Layer 4 ("self-running tagging pipeline"). It was removed before v0.1 ship because:

1. It re-introduces the AIOS-shaped failure mode the R14 critic round flagged (case D in the design log).
2. Observability tools that run their own agents inherit those agents' failure modes (reward hacking, slopsquatting).
3. The MVP is more useful as a *measurement* surface than as another *agent*.

If you want a pipeline, build it on top of the SDK and tagger — the schema is the contract, not the runtime.

## Risk register

| Risk | Mitigation in v0.1 |
|------|---------------------|
| LLM-as-judge unreliable (arXiv 2603.05399) | Tier 2 confidence drops with position-swap disagreement; low-confidence spans flow to Tier 3 |
| Schema drift between Python and JSON | `test_schema.py::TestJsonSchemaParity` |
| Banned overclaims in docs / PRs | `.github/workflows/ci.yml::ban-words` |
| Slopsquatting | CI step queries PyPI for every direct dep before install |
| Solo maintainer burnout (60% in 2026) | Co-maintainer recruitment KPI in CONTRIBUTING.md + pinned issue |
| McLuhan attribution | LICENSE Apache-2.0 + CITATION.cff + README "Acknowledgements" |
| Figure / ground critique (Tetrad without Figure/Ground) | `docs/figure_ground_critique_response.md` |

## Build-time invariants enforced by CI

- No `otel.*` attribute (reserved by OTel SIG)
- No `google-github-actions/release-please-action` (archived; use `googleapis/release-please-action@v4`)
- No banned overclaim terms in source, README, or PR
- Direct dependencies must resolve on PyPI
- Schema file ≥ 1000 bytes (Environment Hardening, blocks tamper-truncation)
- `pip-audit` runs on every PR; high-severity CVEs in transitive deps fail the build

## Informational hard caps for derived agentic pipelines

These bounds are **not** enforced by `tetrad-lens` itself (the project does
not run a self-driving pipeline; see "Why Layer 4 is missing"), but the
original R14 second-round design recorded them as guardrails for any
downstream pipeline a user might build on top:

| Bound       | Recommended cap        | Rationale                                    |
|-------------|------------------------|----------------------------------------------|
| Turn count  | ≤ 200 per sub-session  | futility-loop defense                        |
| Token spend | ≤ 5 M per full run     | budget cap before human review               |
| Dollar cost | ≤ \$200 per full run   | corollary of the token cap at 2026 prices   |

Downstream pipelines that exceed these should pause and ask for confirmation.
