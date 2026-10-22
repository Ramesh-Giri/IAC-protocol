# Change report: iac-public-content

Repo `.`, branch `docs/iac-onboarding-1021`, range `866f637..working tree`.
0 commits, 0 merges, 49 files, +1162 / -5134 lines.

Part 1 is written by the authoring agent. Part 2 is generated from git by `agentmail/bin/change-report` and is the ground truth: if they disagree, Part 2 wins and the disagreement is a review finding.

# Part 1: Narrative (authoring agent)

## What and why

The public toolkit contained site identity, machine settings, copied task descriptions and roster-derived research history.
The candidate moves private originals into an ignored overlay and leaves generic protocol/tooling guidance in tracked files.
No publication, Git-history rewrite or live fleet operation is part of this change.
The working-tree facts include the launcher trust repair and the review fix round for its outer resend path, supervisor approval profile, remaining public model pins and private activation requirements.

## Flow (step by step)

1. The workspace owner retains private instructions, original scripts, historical research and policy under ignored local/.
2. Fleet helpers resolve workspace/mail/main-seat settings from explicit arguments, approved local settings and the roster.
3. The deterministic model guard reads the private model policy while public tests use synthetic tasks and model IDs.
4. Generic protocol and context guidance remains public; raw datasets, generated study output and obsolete prototypes are removed from the public payload.
5. The report helper describes tracked and nonignored uncommitted changes without changing the index or creating commits.
6. Reviewers inspect this candidate and carry its private overlay before switching local fleet tooling to a new checkout.

## How it is implemented

local/preservation-manifest.json records hashes of original copies before tracked edits or removals.
The ignored instruction entrypoints and model-policy.json retain site additions and restrictions.
model_guard._load_policy validates explicit model restrictions, the review exception, score floor and host runtime; malformed policy becomes an advisory error rather than blocking launcher import.
resolve preserves candidate order and continues to separate the guard's opinion from the roster's actual selection.
Fleet command wrappers use local roots and roster seats, avoid destructive session resets and preserve normal runtime safeguards.
fleet-start captures source pane IDs and joins only requested seats into the configured visible window.
The launcher now routes literal boot resends through the guarded submission loop.
Each key requires a successful nonempty capture; only anchored known idle composer suffixes or an exact-cwd folder dialog authorize input, and only the current status line proves activity.
All other nonempty screens get one Escape and one warning naming the seat and last three captured lines, then stop.
The small per-runtime allowlist requires a ruled Claude composer or a Codex composer followed by the exact shortcuts footer; unsupported footer variants and partial renders stop safely.
After typing, Enter additionally requires the exact pending boot text in that same known composer.
Hook trust remains human-only.
Folder selection and confirmation use separate captures; swallowed Enter is retried without retyping the boot prompt.
Parent Codex seats retain on-request approvals and configured GUI plugins; workers retain workspace-write/never and GUI-plugin disable flags.
A synthetic roster fixture compares the complete generated parent and worker argv and the wrapper's offline dry-run command.
Federation examples now use roster-style model placeholders.
The private migration runbook preserves root entrypoints, the original 60-path overlay and 47 hashes, supplies reconciled active site instructions and explicit policy/environment activation, and checks root-reference reachability.
An archived brand template missing from the review's described copy set was recovered from local Git history with a separate preservation hash.
The model guard emits a loud warning if no implicit policy file exists.
Generic operational rules retain the lessons while moving dated incidents, current pins, product cases and site rules out of tracked guidance.
The context skeletons retain exactly the six promised files, with end-user testing and domain vocabulary folded into the relevant documents.
Equivalent SVG ellipses avoid shape-name collisions with the identifier scan while preserving the existing geometry.
change-report --working-tree generates facts from read-only Git diffs and public untracked files; a regression checks index bytes and nanosecond mtime remain unchanged.
project-map closes text reads so its existing checks no longer emit resource warnings.

## How it was verified

The full agentmail suite passed 90 tests, including the existing context-file consistency fix and new exact parent/worker wrapper command coverage.
The bootstrap preservation checks passed.
The dashboard suite passed 54 tests and the model-guard suite passed 21 tests.
The portable configuration checks use fake executables and temporary rosters; they open no terminal and access no live fleet.
The launcher startup-trust self-check passed through submission, boot resend and spawn, including both wrapped dialog examples, pending-approval menus, unknown menus, partial renders, real composer structures, exact-cwd folder dialogs, failed captures with nonempty stdout, stale interrupt text and swallowed Enter.
The allowlist repair first reproduced text or Enter sent to all three supplied dialog cases with zero warnings using mocked subprocess and sleep calls.
Replacing the anchored Codex allowlist with a permissive bare-glyph match makes the self-check fail.
The required agentmail suite passed 90 tests after the allowlist repair; launcher self-check and git diff --check also passed.
Before the fix, offline reproduction recorded literal boot text sent into a hook menu and after a failed capture, and stale interrupt text suppressed the needed resend.
In-memory mutations removing hook detection, raw folder equality, empty/failed capture guards or restoring an outer literal bypass were all detected.
All seven migration Python blocks passed in a disposable fixture; Git ignore replies were mocked there, with real candidate ignore/hash checks performed separately.
Shell syntax and CLI help probes passed.
The final tracked-content identifier scan returned empty output after the permitted public URL and license exceptions.
The expanded private scan includes nonignored new public files and concrete model-ID shapes while exempting exact runtime/plugin identifiers and synthetic test IDs.
Command: `python3 local/public-scan.py`.
Output: empty (exit 0).
Preservation hashes and git check-ignore prove that original copies exist and remain private.
A local scan of available Git history found no obvious credential signatures; this is not an exhaustive credential audit.
The private history inventory records prior published locations without quoting values.
No real terminal launch, cloud operation, deployment, commit, push or history rewrite was performed.

## Deploy / release impact

No product deployment is required.
The candidate remains uncommitted for review and integration.
Before switching a fleet to this checkout, its authorized integrator must follow ignored local/MIGRATION.md, activate the private rules from retained root entrypoints, source the site environment and verify the explicit model policy.
Historical exposure remains in previously published Git objects; only the repository owner decides on history remediation.

# Part 2: Facts (generated from git)

## Sensitive areas touched

- **Payments / money** (2): `agentmail/bin/codex-models`, `agentmail/bin/overseer-codex.command`
- **Auth / identity / keys** (2): `agentmail/research/modelpick/eval_signals.py`, `agentmail/research/modelpick/signals_results.json`

## Commits


## Source files (26)

### `.gitignore` (modified, +4/-1)

### `agentmail/bin/agentmail-launch` (modified, +247/-115)
- Added: `_self_check_startup_trust()`, `_startup_folder_matches()`, `_startup_idle_matches()`, `check()`, `run()`
- Changed: `_print_full_roster_guard_audit()`, `_resend_boot_if_idle()`, `_submit_until_working()`, `build_command()`, `spawn()`

### `agentmail/bin/catalog-check` (modified, +3/-4)

### `agentmail/bin/change-report` (modified, +33/-17)
- Changed: `build()`, `content()`, `dep_lines()`

### `agentmail/bin/codex-models` (modified, +3/-3)

### `agentmail/bin/fleet-guard` (modified, +29/-25)
- Changed: `hygiene()`, `runner_alive()`, `unread()`

### `agentmail/bin/fleet-start.command` (modified, +59/-50)

### `agentmail/bin/fleet-usage` (modified, +3/-3)
- Changed: `probe()`

### `agentmail/bin/fleet-watch.command` (modified, +14/-6)

### `agentmail/bin/overseer-astra.command` (modified, +14/-8)

### `agentmail/bin/overseer-codex.command` (modified, +15/-13)

### `agentmail/bin/project-map` (modified, +7/-8)
- Changed: `build()`, `folder_readme()`

### `agentmail/bin/seat-nudge` (modified, +1/-1)

### `agentmail/bin/whereami` (modified, +5/-7)
- Changed: `_is_real_window()`

### `agentmail/dashboard/netdash/glyphs.py` (modified, +3/-3)
- Changed: `g_mailbox()`, `g_occ()`

### `agentmail/dashboard/netdash/panels.py` (modified, +3/-3)
- Changed: `render_waitgraph()`, `row()`

### `agentmail/dashboard/netdash/static/dashboard.css` (modified, +5/-4)

### `agentmail/lib/model_guard.py` (modified, +59/-77)
- Added: `_load_policy()`
- Changed: `_security_locked()`, `resolve()`

### `agentmail/lib/security_lock_patterns.txt` (modified, +6/-29)

### `agentmail/research/modelpick/catalogue_check.py` (deleted, +0/-66)
- Removed: `load_claude_ids()`, `load_codex_ids()`, `main()`

### `agentmail/research/modelpick/catalogue_check_output.txt` (deleted, +0/-9)

### `agentmail/research/modelpick/dataset.json` (deleted, +0/-3070)

### `agentmail/research/modelpick/decisions_demo.jsonl` (deleted, +0/-5)

### `agentmail/research/modelpick/eval_signals.py` (deleted, +0/-29)

### `agentmail/research/modelpick/phase2_demo.py` (deleted, +0/-71)

### `agentmail/research/modelpick/signals_results.json` (deleted, +0/-1)

## Test files (4)

### `agentmail/dashboard/tests/test_model.py` (modified, +1/-1)
- Changed: `test_tags_are_balanced()`

### `agentmail/lib/test_model_guard.py` (modified, +98/-147)
- Added: `class LocalPolicyTests`, `setUp()`, `test_audit_lock_kinds_always_remove_restricted_models()`, `test_document_rules_trigger_conservative_lock()`, `test_policy_is_explicit_and_validated()`, `test_review_and_audit_both_lock_with_configured_policy()`
- Changed: `in()`, `test_allowlist_drops_unverified_ids_deterministically()`, `test_always_tier_text_locks_regardless_of_kind()`, `test_bias_towards_over_locking_is_intentional_do_not_narrow()`, `test_brief_hash_never_leaks_the_text_itself()`, `test_flavour_tier_locks_by_default_for_every_kind_including_review()`, `test_laya_floor_locks_even_with_benign_kind_and_text()`, `test_locks_fired_is_structured_not_prose()`, `test_log_schema_has_every_field_the_overseer_specified()`, `test_missing_catalogue_for_a_runtime_drops_its_candidates_not_passes_them()`, `test_no_verified_ids_arg_skips_allowlist_explicitly()`, `test_non_security_briefs_do_not_lock()`, `test_one_line_toggle_is_the_only_thing_that_would_reopen_review()`, `test_patterns_file_missing_fails_loud_not_silent()`, `test_pinned_seat_bypasses_everything()`
- Removed: `test_audit_lock_kinds_always_remove_opus_and_fable()`, `test_real_kyb_brief_locks_on_the_word_rules_documented_tension()`, `test_review_and_audit_both_lock_per_the_ruling()`

### `agentmail/tests/test_change_report.py` (modified, +25/-0)
- Added: `test_working_tree_report_preserves_index_and_includes_new_files()`

### `agentmail/tests/test_local_configuration.py` (added, +132/-0)
- Added: `class LocalConfigurationTests`, `test_codex_supervisor_and_worker_profiles_match_wrapper_dry_run()`, `test_fleet_start_preserves_sessions_and_uses_captured_panes()`, `test_guard_reads_explicit_policy_and_reports_invalid_policy()`

## Docs and context files (19)

### `agentmail/FEDERATION.md` (modified, +7/-7)

### `agentmail/ONBOARDING_GAP_REPORT.md` (modified, +27/-71)

### `agentmail/ONBOARDING_NARRATIVE.md` (modified, +2/-1)

### `agentmail/OPERATIONAL_RULES.md` (modified, +257/-460)

### `agentmail/OVERSEER_HANDOFF.md` (modified, +3/-1)

### `agentmail/PROJECT_CONTEXT.md` (modified, +3/-0)

### `agentmail/PUBLIC_EXPOSURE_FOLLOWUP.md` (modified, +13/-191)

### `agentmail/SUPERVISOR_BOOTSTRAP.md` (modified, +9/-5)

### `agentmail/TOKEN_EFFICIENCY.md` (modified, +11/-9)

### `agentmail/examples/web/context/ui-context.md` (modified, +1/-1)

### `agentmail/research/README.md` (added, +5/-0)

### `agentmail/research/modelpick/DESIGN.md` (modified, +23/-363)

### `agentmail/research/modelpick/README.md` (added, +5/-0)

### `agentmail/research/token-efficiency-20260914.md` (modified, +16/-115)

### `agentmail/templates/project-context/architecture-context.md` (modified, +5/-0)

### `agentmail/templates/project-context/code-standards.md` (modified, +6/-0)

### `agentmail/templates/project-context/e2e-testing.md` (deleted, +0/-17)

### `agentmail/templates/project-context/glossary.md` (deleted, +0/-9)

### `docs/changes/iac-onboarding-review-fixes.md` (deleted, +0/-108)
