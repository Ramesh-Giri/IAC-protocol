# Onboarding and operating-rule gap report

Compared the starting toolkit docs with the assigned private operational memory, current handoffs, task board and owner-supplied inventory.
This public report records reusable lessons only; project-specific evidence and inventory remain in ignored local files.
The original task's documentation-only boundary was expanded to allow the manifest and bootstrap, then narrowed for public/private separation.
Nothing in this report authorizes product implementation, cloud execution or publication.

## Missing or incomplete lessons

| Lesson | Starting coverage | Canonical change |
| --- | --- | --- |
| Never tell a worker to discard/reset local changes; provide a fresh lease | Treehouse guidance existed, but rule 22 recovery still said to revert stray edits | Rule 22 preserves the patch; new rule 32 names the brief wording and fresh-lease approach |
| Never blind-drain an inbox, including the listing/read race | Rule 19 required full verdicts but did not prohibit suppressed acknowledgement reads | Rule 3 requires current-message inspection in the acknowledgement command and visible output; seat template mirrors it |
| Cancelled/superseded CI cannot count as green | General evidence rules existed; exact final-SHA job conclusions were absent | New rule 33; orchestration and token guide link the final pushed candidate |
| Batch reviewed integration instead of waiting for CI after each merge | Rule 31 established an integrator, but not the batching sequence | Rule 31 and rule 29 now put combined validation/push with integration; token guide records the batching lesson |
| Sandboxed Codex seats cannot add/commit/merge; preserve prerequisite WIP first | Rule 19 implied a metadata-directory grant would enable commits; rule 31 only partly covered blocked authors | Rules 19/31 state the observed author/reviewer boundary, verified integrator capability and prerequisite WIP-commit-then-merge path |
| Hook/folder startup wording varies; typed prompts can remain unsent | Rules 13/30 covered submission and one hook-review phrase | New rule 34 covers variants, human trust, actual Working/ACK, captured pane IDs and the known launcher defect |
| Roster description defaults must match authority | Protocol covered delegation; no explicit description/default consistency check | Rule 34 checks author/reviewer/integrator description alongside role/home/delegation |
| Fixed fixture clocks and real-clock subprocesses diverge over time | No clock-boundary guidance | New rule 35 requires consistent clock injection or captured-instant fixtures, including actual subprocess paths |
| Text/regex checkers can be bypassed; check actual compiled exports/behavior | Rule 15 already named proxy evidence, but not this concrete acceptance method | Rule 35 adds runtime/export checks and excludes live side effects during inspection |
| A force-update policy must be published before enforcing builds reach devices | Device maps existed, but deployment/config prerequisites were not in release rules | New rule 36 adds published policy, matching server dependencies, sequential versions and packaged-code verification |
| Production follows the actual owner's repository/branch and author-access policy | No production-source/author-access lesson | New rule 37; local inventory records actual owner/fork/branches rather than exposing them publicly |
| Federated mail needs fetch/integration before quoting its state | Protocol/federation explained Git transport; rule 8 covered mail-before-push | New rule 38 covers stale local snapshots, owner-scoped fetch/integration and receipt/reading distinctions |
| Minimal function deploys require the changed import closure | No affected-function-closure guidance | Rule 36 requires shared-import consumers and deploy ordering, with an explicit pending-helper caveat |
| Human cloud boundary includes read-only discovery and equivalent routes | Historical handoff covered command-line GCP; narrower wording could imply alternate routes | Rule 39 explicitly covers discovery/auth/SSH/SDK/API/CI substitutes and complete human instructions |
| Shared status/type/kind codecs prevent casing bugs | Project-specific standard was private, absent from generic worker guidance | Rule 35 and seat template require one enum/codec and wire conversion boundary |
| Close/recycle must preserve leases and exact process identity | Rules 14/21/30 covered most closure behavior; rule 21 lacked preservation criteria | Rule 21 checks preserved/integrated work; rule 34 captures pane IDs; bootstrap warns against killing shared services |
| A clone lacks global tools, live handoffs and a reusable project inventory | Tool catalog covered global installs; no portable workspace entry point or clone manifest | New onboarding, ignored local inventory/config, safe example manifest, bootstrap and offline self-check |

## Contradictions reconciled

- September separate-terminal-window instructions conflicted with rule 30's one viewed fleet window.
  Rules 9/13, orchestration and supervisor bootstrap now point to the same displayed-window requirement.
- Older instructions had the overseer commit, merge, build and regenerate maps despite rule 31's delegation requirement.
  Rules 27-31, orchestration and the worker template now assign integration legwork to the host-capable integration/build seat.
- The integrator exception incorrectly cited rule 11 instead of one-task rule 21.
  Rule 31 now cites rule 21.
- Historical model-cost examples could be mistaken for current pins.
  Rule 19 identifies the later routing update and local-catalog/budget checks; orchestration uses approved roster selection rather than old tier examples.
- The handoff and supervisor docs embedded one machine's identity and stale live state.
  They are now portable contracts; machine/team state belongs in ignored local files.
- The Material template embedded a private brand repository/pin and font assumptions.
  It now requires the project's owner-approved private adoption record, licensed exported assets and literal requested component semantics.

## Already covered; retained rather than duplicated

Protocol 1.1 and HANDOFFS already distinguish product/technical authority, research from implementation, correlated replies, immutable messages and acknowledged versus completed work.
Rules 2/4-8 cover shell-safe mail, single consumers, passive product-repo transport and explicit pathspecs.
Rules 11/12/18/20-26 cover mail-native workers, upward escalation, naming, watcher expiry, one task per seat, granted directories, runtime handoff, bounded searches, device maps and PR sweeps.
Rules 27-30 already define change reports, first-touch file documentation, project maps, shared warm test lanes, machine limits and fleet visibility.
The global-tooling template already covers treehouse rather than hand-rolled worktrees and bounded autonomous runs.
Product UI, payment, booking, identity, backup and accepted-risk decisions remain in the private handoff and each project's canonical requirements/ADRs.
They are not global IAC policy and were not used as authorization to modify product code.

## Script follow-ups outside this change

| Existing file | Observed issue | Required follow-up |
| --- | --- | --- |
| `agentmail/bin/agentmail-launch` | Hook-review branch sends a trust keystroke on one wording variant | Remove automatic trust, handle supported dismiss/continue paths, recognize wording variants and verify Working/ACK |
| `agentmail/bin/fleet-start.command` | Hardcoded site root/seats, destructive session reset, blanket worker permission flag | Replace with portable local settings and non-destructive runtime-specific launch/attachment |
| `agentmail/bin/overseer-astra.command` | Hardcoded site root/seat and restrictive main approval profile | Use portable local configuration and verify effective supervisor capabilities |
| `agentmail/bin/overseer-codex.command` | Hardcoded site root/seat and local handoff assumptions | Read portable local settings and current handoff explicitly |
| `agentmail/bin/fleet-guard` | Hardcoded mail-root default and fallback main-seat identity | Derive main identity from approved local configuration/roster rather than a person's seat name |

These scripts are unchanged; documentation does not fix their behavior or make them portable.
The current launch helper must be reviewed before use where its automatic-trust branch could run.
Existing model-guard code/tests also contain historical product/seat examples; this task does not change enforcement code or its fixtures.
The private helper for computing affected function closures was pending in the supplied handoff; no implementation or availability is claimed here.

## Verification and remaining owner inputs

The bootstrap has an offline assert-based self-check for dry-run behavior and preservation of existing work, with Git/network effects simulated.
Final delivery mail records the checks actually run and their results.
No real project cloning, cloud call, deployment, dependency installation, device operation or Git commit/push is part of verification.
Real repository access and served production mappings therefore remain unproven by this change.

The workspace owner must supply the ignored real inventory/private handoff, approve domain-specific delegation and arrange project/team-mail access.
Any unknown deployment owners, package destinations or production branches remain explicit local handoff items; the public example never invents them.
No new product decision is requested by the generic documentation changes.
