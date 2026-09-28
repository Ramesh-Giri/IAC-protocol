# Supervisor bootstrap and handoff

Updated 2026-09-12 at Ramesh's request after a supervisor could send mail but could not manage visible terminal agents.
This is the startup procedure referenced by AGENTS.md, not a grant of operating-system permissions.
Existing Layer-3, cloud, key and repository-ownership rules remain in force.

## Permission profiles

The supervisor and unattended children have different responsibilities and must have separate launch profiles.
The supervisor needs an operator-approved host-control path for its own agent processes, project tmux sessions and dedicated terminal windows.
Children remain confined to their assigned work and escalate by AgentMail without prompting a human.

The failed supervisor session had workspace-write restrictions and approval policy never.
It could create internal Codex subagents and read/write shared mail, but tmux returned Operation not permitted and process enumeration returned Cannot get process list.
These internal subagents did not meet Ramesh's visible Terminal.app requirement.
Changing Markdown or adding a writable directory does not remove a process, socket or application-control restriction.
The incoming session must inspect its actual effective permissions; command-line intent alone is not proof.

## Operator launch of the next main agent

Run this from Ramesh's current iTerm2 terminal, outside the outgoing agent's restricted execution tool.
This is an interactive supervisor launch with approvals available, not an unattended child profile.
The flags were checked against the installed codex --help on 2026-09-12.

```sh
cd /Users/darkness/Work/Aureus
codex --sandbox workspace-write --ask-for-approval on-request --model gpt-6-astra 'You are overseer-ramesh, the incoming main agent. Read conversation-context/NEW_MAIN_AGENT_PROMPT.md in full and follow it. Complete the supervisor capability checks before claiming takeover or launching the visible Circle fleet.'
```

This command enables requests for approval; it does not itself grant host control or override managed policy.
The incoming agent must use its supported approval path for required host operations and verify the results.
If managed policy still forbids those operations or effective approval remains never, report that mismatch immediately and do not declare the handoff complete.
Do not attempt to bypass an enforced denial through a child, alternate socket, application or helper.
Do not use the existing overseer-astra.command unchanged: it still selects never.
Do not use fleet-start.command unchanged: it kills the project session and passes a flag rejected for Codex children.
The executable launchers have not been repaired as part of this documentation update.

## Required checks before accepting the seat

Record raw results, identities and timestamps for each check in conversation-context/CURRENT_STATE.md.
A failure is a failed capability check, not evidence that no process or window exists.

1. Read the handoff and inspect the effective runtime, sandbox, approval policy and available host-control tools.
Identify the incoming main session separately from subprocesses, the outgoing main, watchers and children.
2. Verify process enumeration and control through an approved mechanism.
Use a disposable process created for the check; terminate only that identified process and verify it exited.
Do not test control by killing an unidentified agent.
3. Inspect the intended project tmux session and its clients through the approved mechanism.
Verify ability to create, inspect and clean up a disposable test session if needed; never reset an existing project session to test access.
4. Verify the ability to open and identify a dedicated terminal window, attach a tmux client and close that same test window without affecting another seat.
An empty client list fails visibility; a client entry alone does not prove which seat the operator can see.
Record the terminal window/client/pane mapping and displayed seat identity.
5. Reconcile the overseer watcher lease with the outgoing owner before starting exactly one replacement watcher.
Send a unique probe and observe actual watcher detection plus a correlated mail reply.
Do not consume the same inbox concurrently with the outgoing main.
6. Before any child is called running, verify one seat runner, one watcher, a visible Terminal.app window showing that seat, and its acknowledgement of a uniquely identified task.
Verify the model from the running seat, not just the roster.

## Visible child launch contract

Ramesh's latest requirement is separate visible Terminal.app windows for children, using tmux sessions named for the project.
The main agent stays in Ramesh's own terminal application, currently iTerm2.
Internal managed subagents, detached tmux sessions and hidden tabs do not satisfy this requirement.
Do not silently substitute them when terminal control fails.
Use executed attachment scripts rather than typing commands into an interactive shell with possible startup prompts.
If multiple clients share a tmux session, verify each continues showing its assigned seat; synchronized window selection can otherwise show the same seat twice.

Use runtime-specific arguments and validate the command before opening a terminal.
For a Codex child, the current agentmail-launch accepts --terminal tmux --apply without --skip-permissions.
Its Codex command retains workspace-write and never; that child profile must not be copied onto the supervisor.
Claude-only bypass flags require the existing authorization and safeguards; they are not portable to Codex.
Preserve live sessions, worktrees and mailbox leases when replacing one seat.
Verify the intended project target rather than assuming tmux new-window selected the correct session.

## Handoff completion

Preserve outgoing state first, prove incoming capabilities, then transfer inbox and watcher ownership in a controlled sequence.
After the new seat can receive mail, the incoming main is responsible for ending the exact outgoing main session and closing its dedicated window if it has one.
Record the session/process identity and window identity before acting, and verify their termination separately from the watcher.
Never close a shared window or infer that an agent exited because it went quiet.
If the current main has no identifiable dedicated terminal window, record what is known and leave that check unresolved rather than inventing an identity.

Track delivery, acknowledgement, active work, verified implementation and deployment as distinct states.
No acknowledgement means a queued task; no patch and test evidence means no verified implementation.
Do not stop an incoming agent from preparing useful authorized work solely because a later production decision will require Ramesh.
