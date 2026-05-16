# Roadmap

## v0.1.x (shipped)

- Schema v1 + JSON Schema 2020-12 + i18n (en, ja)
- Python SDK: `@observe`, `install_processor`, `tag_current_span`, `tetrad_context`
- Three-tier tagger: heuristic + LLM (Ollama + position-swap) + human-review queue
- Adapters: Cline (MCP), Claude Code (skill + MCP)
- CI: ban-words lint, slopsquatting guard, dependency review, release-please

## v0.1.x (queued)

- PyPI Trusted Publisher (`.github/workflows/publish.yml` scaffold ships in v0.1.0; activating it needs PyPI-side OIDC setup)
- TypeScript SDK parity (`@observe` wrapper around Langfuse TS v4 + LangfuseSpanProcessor). **Caveat**: the Vercel OpenTelemetry integration is not API-compatible with Langfuse v4's exporter; the TS adapter will document this explicitly rather than try to paper over it.
- Implement the dual-emit toggle that `OTEL_SEMCONV_STABILITY_OPT_IN=tetrad/dup` currently advertises (env var is read but the second-namespace emit is not yet wired)
- More heuristics + per-language keyword bundles
- Custom Langfuse dashboard JSON for the four axes (not a custom UI — a saved chart config)

## v0.2 (post co-maintainer onboarding)

- Adapters for Aider and OpenHands once their plugin APIs stabilise
- "Reading-list" mode: cluster spans by tetrad signature for retro reviews
- Optional Hot/Cold (Understanding Media, 1964) axis
- Optional Acoustic Space axis (Through the Vanishing Point, 1968)

## v0.3+

- OTEP submission to OpenTelemetry SIG (two-language prototype required first)
- Federated Conventions publication
- LangChain / LlamaIndex callback handlers

## Out-of-scope (deliberate)

- A self-running agentic tagging pipeline — would re-introduce the AIOS-shape failure mode the R14 critic round flagged
- A custom dashboard UI replacing Langfuse — we want to be additive, not competitive
- Authoritative LLM-as-judge — the human-review queue is the last word, by design
