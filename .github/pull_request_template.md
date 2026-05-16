## Summary

<!-- 1-3 bullets describing the change -->

## Type of change

- [ ] `feat:` new feature
- [ ] `fix:` bug fix
- [ ] `docs:` documentation only
- [ ] `chore:` housekeeping / dependencies / CI
- [ ] `refactor:` internal change with no user-visible effect

## Layer touched

- [ ] Layer 1 schema (`schema/`) — **breaking-change risk**, please bump `tetrad.schema_version`
- [ ] Layer 2 SDK (`python/src/tetrad_lens/sdk.py` / `adapters/`)
- [ ] Layer 3 tagger (`heuristic.py` / `llm_tagger.py` / `review_queue.py`)
- [ ] CI / release / docs

## Checklist

- [ ] Commit follows Conventional Commits
- [ ] PR title and body free of banned words (`自走` / `完全` / `永続` / `fully automated` / `fully autonomous`)
- [ ] Tests added or updated
- [ ] Docs updated if user-facing behavior changed
- [ ] PII masking default-ON behavior preserved
