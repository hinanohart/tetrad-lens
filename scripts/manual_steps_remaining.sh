#!/usr/bin/env bash
# manual_steps_remaining.sh
# ---------------------------------------------------------------------------
# The hard-limit list. Everything in this file requires a *human* — either
# because it is a third-party web UI, a personal opt-in, or a judgment call
# that an autonomous agent should not make unsupervised.
#
# Generated: 2026-05-17 (after v0.1.1 ships)
# Repo:      https://github.com/hinanohart/tetrad-lens
#
# Run this with --help to see the full menu. Each step is idempotent: re-run
# is safe, and the script tells you what it found instead of doing anything
# destructive.
# ---------------------------------------------------------------------------

set -euo pipefail

REPO_SLUG="hinanohart/tetrad-lens"
PKG_NAME="tetrad-lens"

usage() {
  cat <<'USAGE'
tetrad-lens — manual steps that the autonomous pipeline cannot complete.

Usage:
  ./scripts/manual_steps_remaining.sh           # show all pending items
  ./scripts/manual_steps_remaining.sh --pypi    # open PyPI Trusted-Publisher docs
  ./scripts/manual_steps_remaining.sh --review  # review pending Dependabot PRs
  ./scripts/manual_steps_remaining.sh --help    # this message

Items covered:
  1. PyPI Trusted Publisher activation  (one-time, PyPI web UI)
  2. (optional) GitHub Environment "pypi" protection rules
  3. Co-maintainer recruitment           (Issue #5 — human opt-in)
  4. Dependabot PR review                (PRs #1, #3 — judgment call)
USAGE
}

print_step_pypi() {
  cat <<EOF

╭─ Step 1 ── PyPI Trusted Publisher activation ─ (REQUIRED for v0.1.x → PyPI) ─╮
│                                                                              │
│ Until this is done, every GitHub Release fires .github/workflows/publish.yml │
│ and the publish step fails at the OIDC handshake. Failure is loud and safe   │
│ (no token to leak), but the package will not appear on PyPI.                 │
│                                                                              │
│ One-time setup (you must have a PyPI account):                               │
│                                                                              │
│   1. https://pypi.org/manage/account/publishing/                             │
│   2. "Add a new pending publisher" and fill in:                              │
│        PyPI Project Name :  ${PKG_NAME}                                       │
│        Owner             :  hinanohart                                       │
│        Repository name   :  tetrad-lens                                      │
│        Workflow name     :  publish.yml                                      │
│        Environment name  :  pypi                                             │
│   3. Save. The next GitHub Release event publishes automatically.            │
│                                                                              │
│ Why this is manual: PyPI requires a logged-in human to authorize the trust   │
│ relationship; OIDC publishers cannot be bootstrapped via API.                │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
EOF
}

print_step_environment() {
  cat <<EOF

╭─ Step 2 ── (optional) Tighten GitHub Environment "pypi" ────────────────────╮
│                                                                              │
│ GitHub auto-creates the environment the first time publish.yml runs, but    │
│ it has zero protection rules. Recommended:                                  │
│                                                                              │
│   Settings → Environments → pypi → "Add deployment protection rule"          │
│     - Required reviewers   : 1 (a maintainer)                                │
│     - Wait timer           : 0–5 min                                         │
│     - Deployment branches  : selected → main only                            │
│                                                                              │
│ This makes PyPI publish a *gated* action: even after the OIDC trust is set, │
│ a release will pause until a maintainer clicks Approve. Skip if you trust   │
│ tagging end-to-end.                                                          │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
EOF
}

print_step_comaintainer() {
  cat <<EOF

╭─ Step 3 ── Co-maintainer recruitment (Issue #5) ────────────────────────────╮
│                                                                              │
│ Open issue: https://github.com/${REPO_SLUG}/issues/5                          │
│ Label     : "co-maintainer wanted (pinned)"                                  │
│                                                                              │
│ This is a *human opt-in*: another person has to volunteer and accept commit │
│ access. Cannot be automated. Suggested cadence:                              │
│                                                                              │
│   - Promote the issue on McLuhan / LangSec / OTel SIG channels.              │
│   - When a candidate appears, review their last 3 OSS PRs and offer triage  │
│     access first, write access after a small contribution lands.             │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
EOF
}

print_step_dependabot() {
  cat <<EOF

╭─ Step 4 ── Dependabot PRs awaiting human review ────────────────────────────╮
│                                                                              │
│ These are major-version bumps for GitHub Actions. The CI passes against     │
│ both, but a human should at minimum read the release notes:                 │
│                                                                              │
│   PR #1  actions/checkout              4 → 6                                 │
│          https://github.com/${REPO_SLUG}/pull/1                              │
│                                                                              │
│   PR #3  googleapis/release-please-action  4 → 5                             │
│          https://github.com/${REPO_SLUG}/pull/3                              │
│                                                                              │
│ Decision matrix:                                                             │
│   - Both green in CI?               yes → merge                              │
│   - Release notes mention breaking? read once, then merge                    │
│   - Hesitant?                       close the PR with comment "deferred"     │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
EOF
}

show_status() {
  echo
  echo "===== Current status (live from GitHub) ====="
  if ! command -v gh >/dev/null 2>&1; then
    echo "gh CLI not installed — install from https://cli.github.com/ to see live status."
    return
  fi
  echo
  echo "Latest releases:"
  gh release list --limit 3 --repo "${REPO_SLUG}" 2>/dev/null \
    | awk '{printf "  %s  (%s)\n", $1, $4}' || echo "  (release list unavailable)"
  echo
  echo "Open PRs:"
  gh pr list --state open --repo "${REPO_SLUG}" 2>/dev/null \
    | awk -F'\t' '{printf "  #%s  %s\n", $1, $2}' || echo "  (PR list unavailable)"
  echo
  echo "Open issues:"
  gh issue list --state open --repo "${REPO_SLUG}" 2>/dev/null \
    | awk -F'\t' '{printf "  #%s  %s\n", $1, $3}' || echo "  (issue list unavailable)"
  echo
}

main() {
  case "${1:-all}" in
    -h|--help) usage; exit 0 ;;
    --pypi)
      print_step_pypi
      command -v xdg-open >/dev/null && xdg-open "https://pypi.org/manage/account/publishing/" 2>/dev/null || true
      ;;
    --review)
      print_step_dependabot
      ;;
    all|"")
      print_step_pypi
      print_step_environment
      print_step_comaintainer
      print_step_dependabot
      show_status
      ;;
    *)
      echo "unknown option: $1" >&2
      usage
      exit 2
      ;;
  esac
}

main "$@"
