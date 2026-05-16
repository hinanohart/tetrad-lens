# Contributing to tetrad-lens

Thank you for considering a contribution. This document covers the workflow, scope boundaries, and review expectations.

## Project scope (v0.x)

`tetrad-lens` is a **Langfuse / OpenTelemetry plugin** that adds a McLuhan-tetrad-shaped attribute schema and a three-tier auto-tagger to AI agent traces. It is **not** a standalone observability platform, **not** an LLM judge framework, and **not** an agent OS.

In scope:
- Schema additions on top of OpenTelemetry GenAI / OpenInference attributes
- Tagging logic (heuristic, LLM-assisted, human-review queue)
- Adapters for Cline (MCP) and Claude Code (skill + MCP)

Out of scope for v0.x (may move to v0.2+):
- Self-running tagging pipelines (D-case AIOS-style)
- Custom UI on top of Langfuse (we use the standard chart + Score filter)
- Adapters for Aider / OpenHands (revisit once their plugin APIs stabilise)

## Banned language

PR titles, commit messages, README, and source comments are linted against these terms:

- `自走`
- `完全`
- `永続`
- `fully automated`
- `fully autonomous`

These overclaims invite the same failure mode the project tries to measure. Use precise wording instead: "checkpoint-resume pipeline", "three-tier tagger", "human-review queue".

## Conventional commits

This repo uses `release-please` (googleapis/release-please-action v4). Commit messages must follow [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/):

- `feat:` — new feature (minor bump)
- `fix:` — bug fix (patch bump)
- `feat!:` or `BREAKING CHANGE:` footer — major bump
- `chore:`, `docs:`, `refactor:`, `test:`, `ci:` — no release

## Local dev

```bash
cd python
pip install -e ".[dev]"
pytest -q
ruff check src tests
mypy src
```

## Three-tier tagger ground rules

When proposing changes to the auto-tagger, please:

1. **Heuristic tier** PRs include test cases showing keyword/structural rules are deterministic.
2. **LLM-assisted tier** PRs include Judge Reliability Harness measurements (arXiv 2603.05399) and position-swap consensus numbers. Single-model scores are not enough.
3. **Human-review queue** PRs preserve `ScoreSource=ANNOTATION` override semantics — human scores must always win.

## PII masking

PII masking defaults to ON. PRs that disable masking by default will not be merged. Opt-out is per-trace and must be explicit.

## Co-maintainer recruitment

Solo maintainer burnout statistics (60% in 2026) drive a 4-week recruitment KPI. If you have used `tetrad-lens` in production and want to help, please comment on the pinned "Co-maintainer wanted" issue.

## Code of conduct

By participating you agree to the [Contributor Covenant 2.1](CODE_OF_CONDUCT.md).
