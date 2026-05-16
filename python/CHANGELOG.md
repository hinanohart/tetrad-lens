# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Future releases are managed by `release-please` based on Conventional Commits.

## [0.2.0](https://github.com/hinanohart/tetrad-lens/compare/v0.1.0...v0.2.0) (2026-05-16)


### Features

* initial release scaffold (v0.1.0) ([f9cd250](https://github.com/hinanohart/tetrad-lens/commit/f9cd25059af6a3bdd85d4cb411775c5998e83b1d))


### Bug Fixes

* **release-please:** move CHANGELOG into python/ and drop ../ path ([8e7369b](https://github.com/hinanohart/tetrad-lens/commit/8e7369b41190cafd10fd569150852dc802e5621f))

## [0.1.0] - 2026-05-17

### Added

- Tetrad schema v1 (`schema/tetrad-v1.json`) with OpenTelemetry attribute mapping
  - `tetrad.enhance`, `tetrad.obsolesce`, `tetrad.retrieve`, `tetrad.reverse` ∈ [0,1] + rationale
  - `tetrad.figure_ground` DERIVED, read-only
  - `engelbart.level` ∈ {a,b,c} (Bootstrap Institute 1990s ABC extension; original Engelbart 1962 SRI report)
  - `tetrad.schema_version` (semver)
- Python SDK (`python/src/tetrad_lens/`):
  - `@observe` wrap on Langfuse decorator
  - `LangfuseSpanProcessor` integration
  - Cline MCP adapter (`adapters/cline_mcp.py`)
  - Claude Code skill + MCP adapter (`adapters/claude_code_skill.py`)
  - Dual-emit via `OTEL_SEMCONV_STABILITY_OPT_IN` (openinference-semantic-conventions + OTel GenAI)
  - PII masking default ON
- Three-tier auto-tagger:
  - Tier 1 heuristic (keyword / structural rules)
  - Tier 2 LLM-assisted (Ollama local + position-swap consensus + Judge Reliability Harness integration)
  - Tier 3 human review queue (Langfuse Score API + ScoreSource=ANNOTATION override)
- Case studies: Cline session + Claude Code session
- CI: pytest + ban-word lint + dependency review + lockfile guard
- License: Apache-2.0
