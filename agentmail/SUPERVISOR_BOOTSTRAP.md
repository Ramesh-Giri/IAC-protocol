# Supervisor bootstrap and handoff

This procedure verifies actual host capabilities before a supervisor accepts a handoff.
It grants no operating-system permissions and never overrides cloud, key or repository ownership boundaries.
See [ONBOARDING.md](../ONBOARDING.md) for portable local settings and [OPERATIONAL_RULES.md](OPERATIONAL_RULES.md) for the fleet rules.

## Permission profiles

The supervisor and unattended children have different responsibilities and separate launch profiles.
The supervisor needs an operator-approved host-control path for its owned agent processes, tmux sessions and dedicated terminal windows.
Children remain within delegated work and escalate by mail without prompting a human.
A workspace-write/never profile may allow mail but block process enumeration or tmux; a writable directory does not prove host control.
Internal managed subagents do not satisfy a request for a visible terminal fleet.
Respect an enforced denial; preserve context and report the precise blocker instead of bypassing it through a helper.

## Launch the incoming main

The human launches the incoming supervisor from their own terminal, outside a restricted outgoing worker's tool.
Set `IAC_ROOT` and `IAC_MAIN_SEAT` using the local settings described in onboarding.
Select an installed, approved model explicitly; this example uses the reference Codex workhorse:

```sh
cd "$IAC_ROOT"
codex --sandbox workspace-write --ask-for-approval on-request --model gpt-6.1-sol \
  "You are $IAC_MAIN_SEAT, the incoming supervisor. Read the local main instructions and latest conversation-context handoff. Complete agentmail/SUPERVISOR_BOOTSTRAP.md capability checks before accepting inbox ownership or claiming a visible fleet is running."
```

On-request enables a supported approval path; it does not grant host control or override managed policy.
If effective policy remains restrictive, report that mismatch and keep takeover explicitly incomplete.
Do not execute the legacy `overseer-astra.command`, `overseer-codex.command` or `fleet-start.command` unchanged: they contain site-specific assumptions, and some select incompatible permissions or destructively reset a session.
A documentation update is not a launcher repair.

## Required checks

Record raw results, identities and timestamps in the ignored local handoff.
A failed capability check is not evidence that no process/window exists.

1. Read the durable state and inspect effective runtime, sandbox, approval policy and host-control tools.
   Identify the incoming main separately from subprocesses, the outgoing main, watchers and children.
2. Verify enumeration and control of a disposable process created for the check.
   Stop only that process and verify exit; never test by killing an unidentified agent or shared app-server.
3. Inspect existing tmux sessions and their clients without resetting them.
   Verify creation, inspection and cleanup of a disposable test session if needed.
4. Verify an actual terminal client showing the intended fleet window and named seat panes.
   In the reference layout, the holder and all seats share the viewed `fleet:1` window named `seats`; the main stays in the human's own terminal.
   An attached session alone does not identify the window being displayed.
5. Reconcile watcher/inbox ownership with the outgoing main before arming one supported replacement watcher.
   Prove a unique probe notification and correlated reply; do not race another consumer.
   Without a persistent notification tool, declare that limitation and use startup/step mail reads plus overseer nudges for worker seats.
6. Before calling a child running, verify its runner, actual model, pane identity, visible location and ACK for the specific task.
   A launcher success line, spinner elsewhere or text in an idle composer is insufficient.
7. For an author, verify an edit is possible in its pre-leased worktree.
   For an integrator, verify Git-write capability within its approved profile; a sandboxed author's inability to commit is expected and not fixed by renaming its role.

## Child launch contract

Use mail-native registered seats and runtime-specific arguments, preserving existing sessions, leases and work.
For the reference macOS layout, project launch sessions may organize creation, but join seat panes into the one viewed fleet window per rule 30.
Do not substitute detached sessions or hidden tabs for the required view.
Execute reviewed attachment scripts when opening terminal clients; shell startup prompts can consume a typed command's first character.
Capture pane IDs at creation and verify the seat title before targeting them.

Inspect an `agentmail-launch --terminal tmux` dry-run before any authorized `--apply`.
Codex workers omit `--skip-permissions`; Claude-specific bypass arguments are not portable and require existing authorization and safeguards.
Keep the supervisor's interactive profile separate from unattended workers.
The current launcher has a known branch that sends a trust key when hook-review wording appears; do not run that branch or describe it as safe automation.
Changed-hook or new-folder trust is a human action; use a supported dismiss/continue-without-trusting path, or report the block.
Never disable safeguards to clear a prompt.
Submit boot/nudge text and Enter separately, then confirm Working and the task ACK.

## Handoff completion

Preserve outgoing state first, prove incoming capabilities, then transfer watcher/inbox ownership without duplicate consumers.
The incoming main ends only the identified outgoing main session and its dedicated window after state transfer is verified.
Do not close a shared fleet window, the terminal app or a shared runtime service.
Verify main-process exit independently from watcher exit.
If there is no identifiable dedicated window, record that uncertainty rather than inventing an identity.

Track queued, acknowledged, active, verified, merged and deployed as distinct states.
The overseer decides and dispatches; integration/build/documentation seats do repository legwork under their own delegation.
A later production decision does not prevent useful authorized preparation, and a general proceed instruction does not override human-only cloud execution.
