# Security policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |
| < 0.1   | No        |

## Reporting a vulnerability

Please **do not open a public issue** for security findings.

Instead, open a [GitHub security advisory](https://github.com/hinanohart/tetrad-lens/security/advisories/new) (preferred) or contact a CODEOWNER listed in `.github/CODEOWNERS`.

We aim to acknowledge reports within 5 business days and to publish a fix or mitigation within 30 days for high-severity issues.

## Dependency hygiene

- Python: lockfile via `pyproject.toml` + `uv.lock` (when installed)
- Slopsquatting defence: CI checks every imported package against PyPI metadata before install (see `.github/workflows/ci.yml`)
- GitHub Dependency Review runs on every PR

## LLM-as-judge reliability

The Tier 2 LLM-assisted tagger is documented as **non-authoritative** by design. Human-review queue scores (`ScoreSource=ANNOTATION`) always override LLM scores. Do not rely on Tier 2 tags for safety-critical decisions without Tier 3 confirmation.
