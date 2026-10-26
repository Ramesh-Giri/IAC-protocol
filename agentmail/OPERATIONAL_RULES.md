<!-- Defines generic fleet operating rules; deployments add private site policy in local/. -->
# AgentMail operational rules

[SPEC.md](SPEC.md), [UPGRADE.md](UPGRADE.md) and [HANDOFFS.md](HANDOFFS.md) define protocol behavior and domain-specific authority.
Use the [onboarding guide](../ONBOARDING.md) for workspace setup.
Site-specific additions, original operating history, model restrictions and machine settings live in ignored `local/`, not in the public toolkit.
Read the site's local instructions and roster before acting.
The preserved original rules are in `local/site-originals/agentmail/OPERATIONAL_RULES.md` when that overlay is present.
These rules describe coordination policy; they do not provide operating-system enforcement.

## 1. Timestamp every message and preserve causal replies

Use the UTC `sent:` field and filename for send time.
Git commit time records synchronization, which can cover several messages.
Do not forge timestamps to imply delivery order.
UUIDs identify messages; `in_reply_to` identifies causal replies.

## 2. Transfer message bodies without shell expansion

Write Markdown with a quoted heredoc and send it using `--body-file`.
Do not interpolate backticks, shell substitutions or untrusted text into shell command strings.
Use argument arrays where available.

## 3. Messages are immutable and must be read before acknowledgement

Corrections are new appended messages.
The `new/` to `cur/` transition acknowledges reading; it does not establish approval or completion.
Never suppress `mail-read` output, bulk-move unread messages or acknowledge from an earlier listing.
Inspect every message printed by the current read, including arrivals after an earlier inspection.
Read verdicts, questions, blockers and DONE bodies in full.
Check `cur/` as well as `new/` before assuming an apparently finished seat has not replied.

## 4. One consumer per seat

Verify watcher or bridge ownership before starting a replacement.
Stop only the identified prior consumer and confirm it exited.
Duplicate consumers can race on acknowledgement and Git synchronization.

## 5. Keep embedded mail transport passive

A watcher in a repository that also holds product code detects and notifies only.
Do not run an auto-committing or auto-pushing daemon there.
Serialize Git effects in visible foreground work.

## 6. Use explicit pathspecs

Stage only the intended mail or task paths.
Never sweep unrelated work into a mail commit with a repository-wide add.

## 7. Reserve mail-sync for dedicated mail repositories

`mail-sync` stages its whole tree.
Embedded channels use explicit-pathspec commits and authorized foreground synchronization instead.

## 8. Read delivered mail before pushing

An authorized pull can deliver instructions as well as code.
Read current mail and reconcile holds, redirects and decisions before pushing.
Preserve local work and stop on unexpected divergence.

## 9. Launch roster seats through supported controls

Use `agentmail-run` through `agentmail-launch` with the actual mail root passed using `-d`.
Preserve existing sessions, panes and work.
Use the site's approved visible layout and runtime-specific permission profile.
Codex workers retain their sandbox; Claude-only bypass arguments are not portable.
Verify current runner/watcher ownership before replacing either.
Arm a supported persistent notification tool first and renew it when required.
Without that tool, check mail at startup and after every step; the overseer provides arrival nudges.
A tmux route does not override an OS or runtime denial.
Verify seat identity, pane mapping and task acknowledgement before reporting a successful launch.

## 10. Grant only approved tool and workspace paths

A seat's project cwd can differ from its mail spool, helpers and leased checkout.
Prove required reads and writes within the approved launch profile.
A successful read does not prove writes are allowed.
Do not disable global safeguards to clear a stall.
An instruction file or directory flag cannot override enforced policy.
Preserve state and report denied capabilities through mail.

## 11. Delegated workers are mail-native seats

Before launch, create the maildir, register a scoped roster entry and establish an escalation route.
Dispatch the actual task through mail rather than typing a private brief into a pane.
A worker escalates decisions to its supervising owner and does not prompt an unattended human.
Internal forks do not automatically become registered or authorized seats.

## 12. Separate decision questions from permission controls

Disable a worker's interactive decision-question tool where supported and verify actual behavior.
That does not remove OS or runtime permission prompts.
Workers report remaining prompts through mail and never approve another session's trust grant.
Only the designated human-facing supervisor asks the human for decisions.

## 13. Verify the operator's actual view

A detached session or an attached client showing another window does not establish visibility.
Check the displayed window, pane identities and owning terminal client.
If the approved layout uses one grid, keep the holder and all seats in that viewed window.
Execute an attachment script rather than typing a command into a startup-sensitive interactive shell.
A shell startup prompt can consume keystrokes.
Submit a boot prompt only after inspecting startup state, then confirm activity and a task ACK.
Do not infer submission from text sitting in a composer.

## 14. Recycle one seat without disturbing its neighbours

Capture stable pane IDs and verify title, runner and work state before acting.
Preserve patches and handoffs, and read the complete DONE or verdict first.
Stop only the owned runner, child tools and watcher, then verify their exit.
Do not kill shared windows, sessions, holder panes or services used by other seats.
Verify the replaced seat and its neighbours afterwards.
Return a lease only after preservation and integration checks.

## 15. Check the thing actually at risk

Ask what a check would report if the claimed behavior failed.
If the result would be unchanged, the check is inadequate.
Read raw output before trusting a pass/fail summary.
Several different-looking failures can share one cause; compare their evidence before inventing separate explanations.
Do not ask the human to look up a fact an authorized local check can answer.

## 16. Know where the agent is running

Use `agentmail/bin/whereami` when runtime or terminal identity matters.
Distinguish the job host, allocated PTY and operator-facing client.
Do not report another process's terminal as the current agent's own surface.
Environment variables alone do not prove ancestry or a visible window.

## 17. Prove supervisor capabilities before handoff

Follow [SUPERVISOR_BOOTSTRAP.md](SUPERVISOR_BOOTSTRAP.md).
Verify actual process control, tmux access, terminal mapping and unique mail/watch round trips through approved controls.
Requested flags, writable paths and internal subagents do not prove effective host capabilities.
Transfer inbox and watcher ownership explicitly, preserving state before ending the identified outgoing main.
Watcher exit does not prove main-session exit.

## 18. Name sessions after seats

Use the roster seat ID for runtime names, pane titles and reports.
Several seats may share a repository, so repository names do not establish agent identity.
Resolve instruction conflicts using the roster, runner arguments and task mail rather than an unsupported assertion.

## 19. Measure runtime fit and budget

Verify installed binaries and current model availability rather than guessing from old examples.
Measure each runtime's independent quota and reset window using approved local tools.
An unreadable usage result is unknown, not zero budget.
Choose among approved runtime/model candidates by task fit, measured headroom and the site's reserve policy.
Model pins, minimum tiers and budget floors belong in the ignored site overlay and roster.
The optional deterministic guard reads `local/model-policy.json` or `IAC_MODEL_POLICY`; public defaults contain no site model restrictions.
The guard is advisory in the launcher and never grants permission or substitutes the roster model.
Prepare durable context before moving a task across runtimes.
Accept uncommitted work from sandboxed authors and route denied Git writes to an authorized integrator.
Do not retry denied operations or assume a directory grant overrides the sandbox.
Close finished seats after complete handoff evidence; do not keep idle seats for speculative follow-ups.
Batch useful mail and link artifacts, while always reading decisions, verdicts, questions, blockers and DONE bodies in full.
Nudge an idle polling-only runtime after mail delivery and verify it resumes work.
See [TOKEN_EFFICIENCY.md](TOKEN_EFFICIENCY.md).

## 20. Keep watchers and alerts effective

Re-arm expiring notification tools for the whole run, or declare polling honestly.
Check unread mail when a seat appears to ignore instructions.
Normalize status glyphs before matching pane titles to seat IDs.
Inspect live status lines rather than old transcript output when detecting prompts or activity.
An unchanged spinner can indicate a blocked command; thinking animation alone does not establish progress.
Test alerts with known blocked, idle and working states.
Do not approve model, hook, directory or OS trust changes on another session's behalf.
Use approved leased workspaces rather than interactive relocation tools that require unattended human input.
Subagent permission is explicit in the roster and task, never inferred from a skill or tool's availability.

## 21. One task per author or reviewer seat

A seat receives one task ID for its lifetime.
Corrections, unblocks and continuations of that same task may use the existing seat.
A new task ID requires a fresh seat, except for the scoped standing integrator in rule 31.
Before returning a lease, verify all edits and unpushed commits are integrated or durably preserved.
Closing a runner does not return its lease.
Never force-return dirty or unpreserved work.

## 22. Verify write access to the actual leased worktree

Read access, permission-bypass arguments and removal of a decision-question tool do not prove directory write access.
Use only reviewed, task-scoped directory grants.
Do not change global access settings or retry a denial through another tool.
Preserve work and mail the exact blocker instead of reverting unrelated edits.

## 23. Transfer runtime ownership deliberately

Before a runtime limit strands a task, save the approved goal, branch/base, worktree, patch, checks, blockers and next action.
A replacement uses the same durable task evidence and reconciles current mail before repeating effects.
Keep one active consumer for each seat during transfer.
Follow rule 17 for a supervisor takeover.

## 24. Bound searches and tool output

Search explicit relevant paths and file types first, using structural or text search before broad dumps.
Do not recursively scan unrelated personal folders or private transcripts to answer a scoped project question.
Read enough context to verify a conclusion, and keep large artifacts out of repeated mail bodies.

## 25. Preserve end-user verification context

For device or visual testing, record the current screen, navigation path, candidate version and observed result in the project's private test record.
Distinguish a proposed test, a local check and observed behavior on the intended target.
Do not call stale screenshots or cached binaries evidence for a new candidate.

## 26. Triage review findings before closing branches

For every finding, record the affected behavior, current source evidence, owner, disposition and verification needed.
Closing or superseding a PR does not close a still-present defect.
If necessary, create a fresh scoped fix task against current code and link the preserved evidence.

## 27. Every merged code change ships a readable report

The author writes what changed and why, the runtime flow, implementation choices, verification and release impact.
Generate the report skeleton with `agentmail/bin/change-report` and fill every `TODO(author)`.
Part 2 is generated from Git and must agree with the narrative.
Reviewers compare the report with the actual diff.
The integrator regenerates facts for the exact merged range and includes `docs/changes/<task-id>.md` with the change.
If author Git writes are denied, preserve the report with the patch and link it in DONE mail.
Update the project's configured test ledger for user-visible changes, using honest pending versus observed-working states.
Private ledger paths and product cases belong in the local overlay.

## 28. Document touched files and maintain the project map

On first touch, add a concise header explaining purpose, important entry points, dependencies, consumers and material side effects.
Keep existing headers accurate when behavior changes.
New folders receive a purpose-first README.
Do not open unrelated files just to document them in bulk.
The integrator runs `agentmail/bin/project-map --repo <repo>` for merged changes and commits the map beside the change report.
Refresh any project-specific graph index only where the project uses one.

## 29. Share expensive test capacity

Workers submit focused checks to the configured `testlane` queue when required by project policy.
An authorized integration/build seat owns the runner and full combined validation.
Use explicit accepted command forms and bounded concurrency.
A queue wait expiry does not cancel the submitted job; inspect status before resubmitting.
The client snapshots intended changes without modifying the author's index or object store.
Runner-managed output paths must stay inside their designated lane without symlink escapes.
Warm caches survive job resets, and dependency installs occur only when required.
The runner command allowlist is not a filesystem sandbox: test code and install hooks execute with host permissions and require trust.
Machine limits, queue paths, heavy-build restrictions and host-specific setup belong in local policy.

## 30. Maintain the approved visible fleet layout

For a one-grid layout, holder and seats share the window the operator actually sees.
Verify the client view after every launch or closure.
Do not use placeholder sleep panes or hidden windows to claim visibility.
An alert-only `fleet-guard` reports hidden views, stray panes, orphan watchers and prompts; the supervisor handles each finding.
Closing a seat preserves work and removes only its identified runner, pane and watcher.

## 31. A standing integrator owns integration

The overseer communicates, decides and dispatches; it does not quietly absorb author or integration work.
A scoped, host-capable integrator preserves blocked-author work, integrates cleared changes, resolves conflicts, runs combined checks, generates reports/maps and performs authorized pushes.
Assigning the role does not grant denied Git or host capability.
Batch cleared merges for combined validation and follow CI on the final pushed SHA.
Preserve an uncommitted prerequisite before importing it into dependent work.
A WIP preservation commit is not review clearance or release authorization.
The integrator's queue is the exception to rule 21's single-task author/reviewer lifecycle.

## 32. Never brief a seat to discard work

A clean base means a fresh approved lease, not resetting an occupied worktree.
Preserve the old lease and all edits.
Copy only required authorized local inputs into a fresh checkout, without exposing their values in mail.
If preservation is blocked, report it rather than discarding state.

## 33. Cancelled or superseded CI is not green

Name the exact final pushed SHA and required jobs' completed conclusions.
Queued, missing, cancelled, superseded, timed-out or failed jobs do not establish successful validation.
Document legitimate conditional skips and the coverage that still ran.
Follow replacement runs after another push; do not combine results from different candidates.

## 34. Startup prompts and roster descriptions are launch contracts

Inspect actual hook, folder and runtime trust dialogs before submitting work.
Only the human grants new trust.
Use a documented continue-without-trusting path where available; otherwise preserve state and report the blocker.
Do not disable safeguards or grant blanket trust to clear a stall.
Submit text and Enter separately when the runtime requires it, and confirm activity plus task acknowledgement.
Check role, home, project, delegation and description together.
A description change does not grant authority.

## 35. Check runtime behavior and clocks across process boundaries

Source-text checks supplement actual behavior checks; they cannot prove callable registration or runtime metadata alone.
Do not import deployment code with live credentials or side effects for inspection.
Use a shared enum/codec for each status/type/kind concept and convert at the boundary.
Pass a consistent injected reference clock into subprocesses or derive fixtures from one captured instant.
Prove expiry and boundary behavior through the actual process path.
A fake clock in the parent does not prove the child shares it.

## 36. Verify release prerequisites before device delivery

Finish and review the approved batch before acceptance on the intended target device.
Compare server, rules and configuration dependencies against the recorded deployed base.
A saved configuration draft does not establish publication.
Use real sequential version/build values and inspect code inside the actual packaged artifact.
Match the requested platform, mode, flavor and signature.
A deployment packet includes changed handlers and exported functions affected through shared imports, with ordering and configuration dependencies.
Verify a helper's existence and review status before relying on it; otherwise document the manual dependency review.
Respect the site's human-only execution boundaries throughout packet preparation.

## 37. Verify the production source and served result

Repository merge success does not establish deployment success.
Record source repository, branch, owner and deployment mapping in ignored inventory.
Use legitimate contributor access; never spoof authorship to pass a deployment check.
After an authorized release, verify source SHA and the actual served page or asset.

## 38. Fetch federated mail before reporting remote state

A local coordination-mail clone is a snapshot, not a live remote inbox.
Its authorized owner integrates the intended remote branch while preserving work and stopping on divergence.
Workers request this through the owner rather than entering another repository without authority.
Read delivered bodies in full, and consume only the owning site's inbox.
A federated read receipt is distinct from approval and completed work.

## 39. Human-only boundaries remain human-only

Read the local overlay for platforms and actions reserved to the human.
A general proceed/deploy instruction does not override a specific prohibition.
Do not substitute a read-only command, SDK/API, CI trigger, remote wrapper or delegated agent for a forbidden operation.
For a human-run step, draft complete TYPE-THIS instructions with location, expected output, stop conditions and rerun behavior.
Do not request credentials or weaken checks to prove a test.
Ordinary authorized Git, build and verification work stays with its designated agent owner.

## 40. Keep one operator requests ledger

Every main agent, on any runtime, keeps one ledger per operator at `<project-context-dir>/OPERATOR_REQUESTS.md`, reused across runtime changes.
Add a row the moment the operator asks for a task, research or a decision, before dispatching it.
Keep Open/waiting, Parked and Done tables with R- / P- / D- ids, date, request, status (`OPEN | WAITING-OPERATOR | DONE | PARKED`) and result path or next step.
Seat DONE mails state the result path on their first body line; move the row to Done with that path before replying to the operator.
Show `OPEN` and `WAITING-OPERATOR` items at session start, at handover (rule 23 handoffs link the ledger) and whenever the operator asks for status.

## 41. Check public web and mail security regularly

Every web project lists its public hosts, production paths and mail domains in the site's ignored `local/websec.local.json` inventory.
Run `agentmail/bin/websec-check` at main-agent session start, weekly, and before reporting a web deploy or release complete.
Every FAIL becomes a tracked task with an owner and evidence; a failed or incomplete check cannot support a completion claim.
Record accepted edge exceptions with a reason and expiry date, and review WARN results explicitly.
Each web repository also asserts its security headers through a contract test in CI against a deployed preview, including error paths; an external periodic check alone is insufficient.
Contact mailboxes displayed in products must exist and accept mail; DNS records alone do not prove delivery.
Follow [WEBSEC.md](WEBSEC.md) for the inventory format, check coverage and preview CI example.

Revision: public rules generalized; original site-specific rules are preserved in the ignored local overlay.
