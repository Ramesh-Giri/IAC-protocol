# Change report: IAC onboarding review fixes

Repo `.`, branch `public-review-snapshot`, range `81a4104..6c9e729`.
1 commits, 0 merges, 21 files, +1977 / -1166 lines.

Part 1 is written by the authoring agent. Part 2 is generated from git by `agentmail/bin/change-report` and is the ground truth: if they disagree, Part 2 wins and the disagreement is a review finding.

# Part 1: Narrative (authoring agent)

## What and why
The onboarding review found that inspecting an existing checkout could refresh its Git index and that a manual setup record without a note could crash the CLI.
The corrected bootstrap disables optional Git locks and validates manual notes before processing any project.
The public research artifacts now replace private identities and dispatch content with neutral identifiers and topic summaries.
This report describes the full preserved, uncommitted onboarding candidate using a disposable comparison repository; the workspace itself remains uncommitted.

## Flow (step by step)
1. A developer runs the bootstrap CLI with a local manifest.
2. Manifest validation requires a nonempty string setup_note for every bootstrap:false record, returning the existing structured error on invalid input.
3. All Git subprocesses inherit GIT_OPTIONAL_LOCKS=0, including inspection commands during dry-run.
4. Existing preservation and clone/update behavior continues through the same shared Git helper.
5. Public research joins use consistent neutral seat IDs; historical scores and labels are preserved.
6. Reviewers use agentmail/PUBLIC_EXPOSURE_FOLLOWUP.md to assign remaining operational/generated-evidence cleanup separately.

## How it is implemented
bin/iac-bootstrap changes only the shared Git environment and conditional manifest validation.
bin/test_iac_bootstrap.py adds an actual Git checkout with a deliberately stale tracked-file timestamp, then compares index bytes and nanosecond mtime after invoking the CLI with --dry-run.
A second CLI regression rejects missing, empty, whitespace-only, numeric, list and object notes with exit 2 and no traceback, and checks a valid manual note.
The research dataset keeps record order, dates, runtime/model assignments, standing flags and kind labels while replacing identity fields and private prose.
The four saved signal runs keep truth labels and probabilities and join to the same sanitized descriptions.
The design explains that evaluating summaries creates a new experiment and cannot reproduce private-text historical scores.
Operational scripts, behavior-bearing policy data, fixtures and generated historical output remain unchanged; the location-only follow-up lists their outstanding identity matches.
The pre-existing onboarding documentation and local-only inventory remain preserved.

## How it was verified
Both new CLI regressions failed before the bootstrap fix: index refresh and raw KeyError respectively.
The focused bootstrap preservation checks passed through the shared test lane after the fix.
The focused team setup checks passed 4/4 through the shared test lane.
A data integrity check verified all 236 dataset records and 920 signal result rows retain their historical labels, scores, ordering and joins.
The full tracked/nonignored privacy scan found no identity matches in the three corrected research artifacts.
It recorded 49 remaining operational/generated-evidence locations and five intentional legal/public-source locations.
git diff --check passed.
No app build, full suite, live repository access, cloud command, deployment, desktop application or fleet launch was performed.

## Deploy / release impact
No deployment is required.
The original worktree is left uncommitted for overseer review and integration.
The full public-safety gate remains open for the separately owned locations in the follow-up inventory.
Legal attribution and the toolkit's public source links are retained.

# Part 2: Facts (generated from git)

## Sensitive areas touched

- **Auth / identity / keys** (1): `agentmail/research/modelpick/signals_results.json`

## Commits

- `6c9e729` 2026-10-22 01:04 Review snapshot: Preserved onboarding candidate and focused review corrections

## Source files (6)

### `.gitignore` (modified, +16/-0)

### `agentmail/research/modelpick/dataset.json` (modified, +840/-840)

### `agentmail/research/modelpick/signals_results.json` (modified, +1/-1)

### `agentmail/templates/iac-local.env.example` (added, +11/-0)

### `bin/iac-bootstrap` (added, +146/-0)
- Added: `class Parser`, `error()`, `git()`, `load_projects()`, `main()`, `remote_key()`, `update_project()`

### `projects.example.json` (added, +35/-0)

## Test files (1)

### `bin/test_iac_bootstrap.py` (added, +158/-0)
- Added: `check()`, `check_dry_run_index()`, `check_manual_manifest()`, `clean_git()`, `fixture_git()`, `held_git()`

## Docs and context files (14)

### `ONBOARDING.md` (added, +129/-0)

### `README.md` (modified, +4/-0)

### `agentmail/ONBOARDING_GAP_REPORT.md` (added, +79/-0)

### `agentmail/ONBOARDING_NARRATIVE.md` (added, +46/-0)

### `agentmail/OPERATIONAL_RULES.md` (modified, +204/-63)

### `agentmail/ORCHESTRATION.md` (modified, +24/-13)

### `agentmail/OVERSEER_HANDOFF.md` (modified, +53/-119)

### `agentmail/PUBLIC_EXPOSURE_FOLLOWUP.md` (added, +87/-0)

### `agentmail/SUPERVISOR_BOOTSTRAP.md` (modified, +66/-70)

### `agentmail/TOKEN_EFFICIENCY.md` (modified, +7/-2)

### `agentmail/research/modelpick/DESIGN.md` (modified, +25/-12)

### `agentmail/templates/SEAT_AGENTS.md` (modified, +17/-4)

### `agentmail/templates/design-standard-material.md` (modified, +24/-42)

### `bin/README.md` (added, +5/-0)
