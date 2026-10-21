<!-- Defines AgentMail fleet operating rules; overseers and seats follow these alongside SPEC.md and the seat template. -->
# AgentMail — Operational Rules

**1.1 update:** [SPEC.md](SPEC.md) and [UPGRADE.md](UPGRADE.md) take precedence
over historical operating advice below. Use `--body-file` or quoted heredocs
for safe Markdown transfer.
The 2026-10-21 amendments below supersede older site-specific launch, model and integration advice.
Use the portable [onboarding guide](../ONBOARDING.md) for a fresh machine; resolve all workspace paths from `IAC_ROOT`.
Research/requirements/implementation are distinct
intents, and ownership is domain-specific; see [HANDOFFS.md](HANDOFFS.md).

*Rules learned from running AgentMail networks in production, including cross-developer git federation. These are system-level and apply to any deployment. They complement the protocol in `SPEC.md` and the federation model in `FEDERATION.md` — this file is the "what bit us and how not to repeat it" layer.*

---

## 1. Timestamp every message, and record send-time in git

Every message carries a `sent:` UTC timestamp in its frontmatter and filename.
Read that field for send time; Git commit time records synchronization and
may cover multiple messages. Do not forge commit dates to imply delivery or
causal order. UUIDs identify messages; `in_reply_to` identifies causal replies.

## 2. Never put shell substitution in a message body

Compose message bodies in a **quoted heredoc** to a file (`<<'EOF'` — the quoted delimiter disables all expansion), then send with `-m "$(cat file)"`. **Never** place backtick characters or `$(...)` directly in a `-m` or `--subject` argument: the shell command-substitutes them before the tool sees the argument, and the message is corrupted — in one real incident a `ps` listing was executed and dumped into a message body. Because messages are immutable (rule 3), a corrupted send costs a separate correction message.

## 3. Messages are immutable

Never edit or delete a sent message. A correction is a **new appended message** (SPEC §3.2). The read acknowledgement is the `new/ → cur/` move; that git-visible transition is the protocol ack and is sufficient.
An extra landed note is optional etiquette, not a second required protocol.

Never blind-drain an inbox: no `mail-read >/dev/null`, blanket `mv new/* cur/`, or acknowledgement based on an earlier listing.
Inspect every current `new/` message in the same shell command as `mail-read`, keep its output visible, and read any arrivals it prints after that inspection.
DONE, verdict, question and blocker bodies must be handled in full, not just by subject.
If a seat appears finished without a seen reply, inspect `cur/` as well as `new/` before assuming it is still working.

## 4. One monitor per seat

Exactly **one** watcher/bridge process may run per seat. Check for and **stop any existing instance before arming a new one**. Two monitors on the same working tree, each pulling/committing/pushing on its own timer, cause real divergence and hung git processes — a genuine incident, not a hypothetical.

## 5. Stay passive on a repo that also holds product code

If a mail channel is embedded in a repository that also contains product code, the watcher must be **passive**: detect and notify only. No auto-committing or auto-pushing daemon. All commits and pushes happen inside a foreground turn where they are visible and serialized against other git work.

## 6. Explicit pathspec, always

Commit only the mail path (`git add <maildir>`), **never `git add -A`**. On a shared/product repo, `-A` sweeps in-progress code into a mail commit. Explicit pathspec keeps mail commits to mail.

## 7. No `mail-sync` daemon on a product repo

`mail-sync` does `git add -A` on its whole tree every cycle — correct for a dedicated mail repo, wrong for a repo that also holds product code (it would auto-commit unfinished code). For a channel embedded in a product repo, sync by **explicit-pathspec commits + normal push/pull**, not the daemon.

## 8. MAIL-BEFORE-PUSH

Before pushing, pull — and treat the pull as delivering **mail, not just code**. Drain and **read your newly-arrived inbox** as part of that pull, and reconcile it against what you are about to push. If a message holds, redirects, or contradicts your intended change, **do not push** — surface and resolve it first. A pull that updated the code also delivered instructions you have not seen; never push on top of unread mail. (General discipline for every seat, on any repo: drain your inbox before pushing.)

## 9. Launch tracked seats with `--terminal tmux` and verify the viewed fleet window

Preserve existing sessions and work; project-named launch sessions may be used to organize creation.
At the reference site, join the resulting seat panes into the one viewed `fleet:1` window named `seats`, with its holder pane (rule 30).
Use agentmail-run-backed roster seats through agentmail-launch with --terminal tmux --apply.
For Codex children omit --skip-permissions: the current launcher rejects it and retains the Codex sandbox.
Claude-only bypass arguments are not portable; apply them only under the existing authorization and safeguards.
The supervisor has a separate interactive approval profile and must pass the host-control checks in [SUPERVISOR_BOOTSTRAP.md](SUPERVISOR_BOOTSTRAP.md).
A tmux route does not bypass an OS or runtime denial.
Before replacement, identify the current seat runner and watcher and stop only the exact owned instances through an approved mechanism.
Start one supported persistent watcher first and explicitly submit the boot prompt if it was not executed.
Codex without a persistent notification tool checks mail at startup and after every step; the overseer nudges it when new mail arrives.
Always pass the actual mail root with `-d`; a worktree cwd is not the mail root.
Execute an attachment script to open the required Terminal.app window; do not type a command into a startup-sensitive shell.
Verify the target project, client/pane mapping and task acknowledgement before reporting the seat running.

## 10. Grant the approved mail/tool paths before unattended work

A worker's project cwd is separate from the shared mail spool and helpers in the workspace root.
A directory read block can prompt even when another permission-bypass flag is present; a successful read does not prove an edit is permitted.
Grant only the approved paths in the reviewed launch profile and prove the needed read/write behavior before dispatch.
Do not change global read-block settings while a fleet is running or disable a safeguard to clear a stall.
If policy denies the required access, preserve state and report the blocker; neither Markdown nor --add-dir overrides an enforced denial.
Where approved, place required tools inside the permitted workspace to avoid unnecessary boundary crossings, and audit scoped session evidence rather than scanning personal folders.

## 11. Every spawned agent is a mail seat — it escalates by mail, never prompts the human

When the supervising agent spawns a worker (to parallelize, to draft, whatever), that worker MUST be a mail-native **seat**, not a bare CLI process. A bare agent has no escalation path: the moment it hits a real decision it stalls asking a human who is not watching its terminal — which breaks the supervision model, where decisions flow **up** to the supervisor by mail, never sideways to whoever happens to see the pane. Making a worker mail-native is three steps beyond launching a bare CLI: `agentmail-init <seat>` (its maildir), a **roster entry** (so it is tracked and scoped to its project, not the org root), then launch through `agentmail-run --seat <seat> -- <agent-cli> …` with a boot instruction that says: arm the watcher first, take the task by mail, **escalate every decision to the supervisor by mail, and never open an interactive question or prompt a human**. Dispatch its task by mail too, not by typing into its pane. Converting a bare worker to a seat mid-flight loses no work if you relaunch it in the SAME worktree — its branch and commits are on disk, not in the process.

## 12. Children escalate by mail, with decision-question tools disabled where supported

Only the supervisor speaks to the human; children send questions and blockers upward through mail.
For Claude children the launcher disables AskUserQuestion; verify the equivalent capability and real behavior for each other runtime.
This removes a decision-question tool, not every runtime or operating-system permission prompt.
Keep safeguards intact and report any remaining prompt by mail rather than approving another session's trust/permission grant.
The supported watcher/polling fallback in rule 9 and the startup checks in rule 34 still apply.

## 13. The operator must be able to SEE the fleet — a detached session is not "running"

A headless tmux session satisfies `tmux ls` and satisfies nothing the operator asked for. **Launching a fleet is not finished until a real terminal window is attached to it and the panes are watchable.** The check that matters is `tmux list-clients -t <project>`; empty output means invisible, no matter what `tmux ls` reports. Reporting "the fleet is up" off `tmux ls` alone is the recurring failure this file ends on — a check whose subject is not the thing at risk.

**Attach by EXECUTING a script, never by having AppleScript type a command.** `osascript -e 'tell application "Terminal" to do script "<cmd>"'` *types* the command into a newly-spawned interactive shell, so **anything the shell prints at startup that reads a keypress will swallow the first character** of that command. The symptom is a parade of unrelated-looking errors from what is one bug: `tmux attach` → `zsh: command not found: mux`; `/absolute/example.command` → `no such file or directory: absolute/example.command`; `exec /opt/...` → `command not found: xec`. In the incident that produced this rule the thief was oh-my-zsh's auto-update prompt (`[oh-my-zsh] Would you like to update? [Y/n]`), and six launch attempts were misread as six different failures before anyone compared them and noticed **exactly one character** was missing from each.

**Current operator requirement, 2026-10-20: one viewed Terminal.app fleet window, all seats visible as panes (rule 30).**
This supersedes the September separate-window advice.
The holder and seats share `fleet:1`, named `seats`; verify which window the attached client actually displays.
Do not create one window per seat or infer visibility from client count alone.
Do not substitute hidden tabs, detached sessions or internal managed subagents.
The main belongs in the operator's own terminal application.

**Send the boot prompt explicitly; do not trust it to auto-submit.** Passing the boot instruction as a CLI argument to the agent binary does not reliably execute it — seats sit at an empty prompt looking hung when in fact nothing was ever submitted, and the operator reasonably reports them as "stuck". After launch, `tmux send-keys -t <pane> -l "<boot>"`, pause, then send `Enter`. Confirm by reading the pane: an interrupt hint ("esc to interrupt") means it is working; a bare prompt means it is not.

Two fixes, apply both:
- **Root cause:** silence the startup prompt (`zstyle ":omz:update" mode disabled`, `DISABLE_AUTO_UPDATE=true`, `DISABLE_UPDATE_PROMPT=true`). These must be placed **BEFORE** `source $ZSH/oh-my-zsh.sh` — appended after it they are read too late and do nothing, which is its own half-hour of confusion. Verify with `zsh -i -c 'echo OK'`: nothing but your own output may appear.
- **Mechanism:** ship a `.command` file (`chmod +x`, `open -a Terminal <file>`). It is **executed** rather than typed, so no keystroke can be eaten by anything — it is robust even on a machine whose shell startup you do not control, which is the reason to keep using it after the prompt is fixed. Have it build the session (holder window first, per rule 9), launch each seat, then `exec tmux attach` so the window the operator is looking at *is* the session.

## 14. Recycling one seat must preserve its neighbours

Capture a seat's pane ID at creation and verify its title, runner and work state before acting.
Preserve its patch/handoff before restarting; close a finished seat only after reading its DONE/verdict in full.
Stop only the exact owned runner, its child tools and watcher, then verify those processes exited.
If the old pane remains, remove only that captured pane after checking its identity; never select a target by list position or shifting window index.
Do not kill a shared window/session, the holder pane or a runtime service used by the human or another seat.
Keep the permanent holder with the seat panes so closing the last worker does not destroy the viewed fleet window.
After replacement, verify the affected seat and its neighbours, one consumer per seat, the actual running models and the displayed client window.
Return a lease only after the integration/preservation checks in rules 21/32.

## 15. Verify the SUBJECT, and read raw output before believing your own summary

This file's closing lesson applies to the SUPERVISOR as hard as to the code it reviews, and is the rule most often broken by whoever is enforcing it. Two failure shapes, both of which ship as evidence:

**(a) A check whose subject is not the thing at risk.** Renaming a plugin directory to disable it, when the loader reads the manifest inside and not the directory name. Appending a config setting *after* the line that consumes it. Reporting a fleet "running" from `tmux ls` when the operator needs `tmux list-clients`. Confirming one seat's model and reporting the fleet correct. Before claiming anything is done, ask: **what would this check report if the thing had failed?** If the answer is "the same", it is not a check.

**(b) Trusting a pass/fail label over the output beneath it.** A capability probe that reported every model id `REJECTED` had actually died on `Not inside a trusted directory` and never reached a model — the label was read, the error was not. Worse, that false result was then used to tell the operator his instruction was impossible; he disproved it from his own screen. **When a finding concludes the user's request cannot be done, suspect the finding before the request.**

Two corollaries earned the same day:
- **Several failures that look different may be one bug.** `command not found: mux`, `no such file: Users/x`, `command not found: xec` were chased as three problems; exactly one character was missing from each, and the cause was a startup prompt eating a keystroke (rule 13). Compare failures to each other before theorising about any one of them.
- **Never ask the operator to look something up that a command can answer.** Enumerate the capability, read the cache, parse the config. Asking a human to open an interactive picker and describe it is not a capability check, and it spends the one resource the supervisor exists to conserve.

## 16. An agent must be able to say WHERE it is running — and must not be talked out of a verified finding

Asked which terminal it was on, a supervisor answered with the *fleet's* terminal, then with "no terminal attached", then with the wrong application twice. All four answers were produced confidently, and the operator had to correct each one. An agent that cannot locate itself will answer questions about the operator's screen with facts about some other process — and will report a fleet as "running" that nobody can see (rule 13).

**The checks that work** (`agentmail/bin/whereami` implements them):
- **Environment variables prove nothing.** A background job has no `TERM_PROGRAM` and no `TMUX`; their absence is not evidence of anything.
- **Walk the process tree to the session process.** Reading the tty of your own spawned subprocess reports `??` because it is detached — that is not your session's tty.
- **A genuine window has a `login` session leader on its tty.** No login leader means a daemon-allocated PTY: a background job, invisible to the operator.
- **`login` does not identify the application.** Terminal.app and iTerm2 both spawn it. Resolve the login process's **parent** — `iTermServer` means iTerm2, `Terminal` means Terminal.app. Inferring the app from the leader alone is a check whose subject is not the thing asked about (rule 15).
- **`System Events … background only is false` under-reports**; it omitted a running iTerm2. Scan `ps` for terminal emulators rather than trusting that listing.
- **Name which process you are describing.** "The operator's client", "this session", and "the fleet's windows" are three different answers to one question.

**Cleaning up windows needs the same care.** Closing "idle" terminal windows by AppleScript's `busy` property will close a window running `tmux attach` — that is not "busy", yet it is the operator's only view of the fleet. Closing it re-creates the exact invisibility of rule 13 while reporting a successful tidy-up. Before closing any window, ask what it HOSTS, not whether it looks idle; afterwards re-verify `tmux list-clients` is non-empty and re-attach if it is not.

**Placement follows from this.** The supervising seat opens in **the terminal the operator is actually using**; child seats go in the *other* terminal app (the fleet's tmux session), which the operator only watches. Opening the main agent in the children's window makes the operator hunt for the one seat they talk to, and an overseer launched as a background job is worse still — invisible, and unable to be driven at all. Detect the operator's terminal before launching (this rule's checks), then target it: `open -a <that app> <launcher>.command`.

**And the harder half.** The first answer above was *correct about the host app*, and the supervisor abandoned it when the operator pushed back — then argued its way to a wrong one. **Being talked off a verified finding is worse than the original error**, because the evidence was already in hand. When contradicted: re-examine and re-run the check. If the evidence still holds, say so plainly and show it; if it does not, say precisely what changed. The operator is usually right about their own machine — but the route to their answer is fresh evidence, never deference. Never claim something is proven when it is inferred; label an inference as one.

---

*A recurring meta-lesson behind several of these: a guard or field that reads **prose** instead of **behaviour** — a check that passes because a name appears in a docstring, a column that cannot change while claiming to track a changing thing — is worse than none, because it ships as evidence. Test a guard by trying to break it; if you have not tried, it is not evidence.*

*Revision: first issue, 2026-09-04; amended 2026-09-12 (rule 13: the operator must SEE the fleet — attach a real terminal by EXECUTING a .command file, never by AppleScript-typing a command into a shell, because a startup prompt eats the first keystroke); amended 2026-09-11 (added rules 9–11: per-project tmux launch; the org-root read-block that stalls unattended children; every spawned worker being a mail seat that escalates by mail rather than prompting a human; and children launched with their interactive-question tool removed so they physically cannot prompt the operator). Amend by appending a dated revision; do not silently overwrite.*

## 17. Prove supervisor capabilities before completing a handoff

Follow [SUPERVISOR_BOOTSTRAP.md](SUPERVISOR_BOOTSTRAP.md).
Keep supervisor and child permission profiles separate and validate runtime-specific launch arguments before use.
Verify actual process control, tmux access, terminal attachment and closure, and unique mail/watch round trips through approved controls.
Do not infer capabilities from requested flags, writable filesystem paths or internal subagent availability.
If effective policy denies an operation and provides no approval route, report the exact blocker and prepare durable context rather than bypassing it.
Only mark the visible fleet running after seat identity, terminal mapping, watcher ownership and task acknowledgement are verified.
Transfer watcher/inbox ownership without duplicate consumers, then terminate the identified outgoing main and its dedicated window after preserving its state.
Watcher exit is not main-session exit.

## 18. Name every seat after its SEAT, not its repository

Operator feedback, 2026-09-14: several seats shared one repository and every session showed the same name ("app"), so nobody could tell the agents apart.
Claude Code labels a session by its working directory unless it is given a name.
Launch every Claude seat with `claude --name <seat-id>`; `agentmail-launch` now does this automatically.
Also title the tmux pane with the seat id (`tmux select-pane -T <seat-id>` with `pane-border-status top`), so the grid shows who is who.
When reporting to the operator, refer to agents by seat id, never by repository or app name.
A second, related lesson from the same launch: a repository's own CLAUDE.md may name a single seat ("Your seat: app-owner"); a worker seat started in that repository will reasonably doubt its identity.
Give it verifiable evidence (its roster entry, its own `agentmail-run --seat` process arguments, its queued task mail), never an unverifiable assertion, and add a line to that CLAUDE.md saying roster worker seats are valid.

## 19. Two budgets, one fleet: smart runtime switching and cross-runtime spawning

Operator feedback, 2026-09-14: Claude and Codex are both installed and have SEPARATE budgets; the fleet must not drain one while the other idles, and either runtime's main must be able to spawn the other runtime's agents.
Standing procedure for whichever agent holds the overseer seat (Claude or Codex):

**2026-10-20 routing update at the reference site:** new authoring and review seats default to Codex `gpt-6.1-sol`; Claude is reserved for required host tools or a demonstrated Codex blocker.
A fresh Codex reviewer may review Codex work.
Sonnet is the minimum Claude seat tier; older Haiku, Spark and cheapest-model examples below are historical, not current routing instructions.
Keep measuring both budgets; if `/status` cannot render, inspect the newest session rate-limit record and report the time window/reset and any prepaid-credit use, without copying credentials.
A missing-runtime label needs a PATH/installed-binary check before declaring the runtime absent.

- Measure, do not guess: run `agentmail/bin/fleet-usage` (reads Claude /usage and Codex /status, no model calls) at session start, before launching any seat, at least every 2 hours while seats run, and immediately when any seat reports a limit warning. Record the numbers and reset times in conversation-context/CURRENT_STATE.md. A "could not read" result is a failed check, not zero budget.
- Pick the runtime per seat by (1) task fit, then (2) budget: prefer the pool that has unused budget and resets soonest (unused budget is lost at reset), while (3) keeping floors: do not push a pool below about 15% unless it resets within 24 hours, and always keep enough Claude or Codex for the overseer seat itself.
- Separate Codex pools: the Codex account shows a main weekly limit and a separate GPT-5.3-Codex-Spark limit; route small, mechanical work (lint fixes, docs, test scaffolding, simple renames) to Spark before spending the main pool.
- Task fit: Codex seats suit well-scoped code-only authoring, read-only reviews, cross-runtime second opinions, test writing and mechanical edits. Claude seats suit work that needs host tools (tmux, emulators and local sockets, flutter test on the host, GUI/Gatekeeper prompts), long house-pattern Flutter UI work, and security-critical authoring. Right-size models inside each runtime (Codex: spark, luna, terra, astra; Claude: haiku, sonnet, opus), never default to the largest.
- Codex sandbox realities: author/reviewer seats in this fleet cannot `git add`, commit or merge, even when a requested directory grant appears to cover the worktree metadata.
  Pre-lease their treehouse checkout, accept uncommitted patches and route Git writes to the host-capable integrator (rule 31).
  Do not retry blocked Git writes or assume `--add-dir` overrides an enforced denial; local sockets may also be denied.
- Cross-runtime review: when possible the reviewer runs on the other runtime than the author (independent model family, and it spreads spend).
- Main handover across runtimes: when the overseer's own runtime approaches its floor, prepare the handoff and propose moving the overseer seat to the other runtime (SUPERVISOR_BOOTSTRAP.md), rather than stalling the fleet.
- Seats report any quota or limit warning to the overseer by mail at once; the overseer rebalances by closing and relaunching work on the other runtime (rule 18 naming, close-when-done policy).
- STRICT frugality (the operator, 2026-09-14, "follow that strictly"): run the fewest concurrent seats that meet the deadline. A seat is ended as soon as its specific unit is done, and is NOT kept idle waiting for a verdict or a possible follow-up; follow-ups go to a fresh seat, preferably on the runtime with more headroom. Idle Claude seats still spend tokens every time a mail or monitor event wakes them with their full context.
- Lean on the lower-cost option in both directions: while one pool is low, push suitable work to the other so both last longer; when that pool recovers, rebalance back. Expensive models (Opus, GPT-6-Astra) only for work that needs them (security-critical authoring, hard reviews); reviews and mechanical follow-ups default to the cheaper runtime and model.
- The overseer seat itself is usually the largest single consumer: keep its turns lean, delegate reading-heavy checks to a cheap seat, and avoid re-reading large outputs.
- Closing a finished seat (the operator, 2026-09-14): the seat's DONE mail must already be a complete handoff (branch, SHA, tests, done/not done, gotchas, next steps). The overseer then closes it directly: TERM the exact `agentmail-run --seat <seat>` runner (rule 14), verify the runner, agent and watcher are gone, and retile the grid. Do not type `/exit` into the agent's pane and do not require a READY-TO-CLOSE round-trip.
- Mail frugality (the operator, 2026-09-14, "follow strictly"): every mail costs tokens for the writer, the reader, and each woken agent's full context. Task mails point at a spec or handoff file instead of repeating it; decisions go out as one batched mail; facts flow peer-to-peer between seats; seats mail only at milestones (ACK, blocker, DONE); the overseer reads subjects first and opens bodies only when needed; research and bulk reading go to a cheap seat (e.g. Codex Spark with `--search`).
- Frugal reading has one exception: verdicts, blockers, questions and DONE mails are always opened in full the moment they arrive. On 2026-09-14 a Codex BLOCK and a seat's report were drained by subject only, and two seats sat idle for ten minutes waiting on the overseer. When a seat looks idle, check the overseer's own unread and skimmed mail first.
- Codex seats do not wake on new mail (observed 2026-09-14: a Codex reviewer sat idle with 4 unread task mails while Claude seats woke through their Monitor watcher). After mailing a Codex seat that is idle, nudge its pane once ("run mail-read <seat> and act on it") and confirm it shows Working; tell Codex seats to run mail-check before stopping after each unit.
- Token-efficiency reasoning, adopted practices and rejected options: [TOKEN_EFFICIENCY.md](TOKEN_EFFICIENCY.md).
- No automatic closing (the operator, 2026-09-14): only the main agent (overseer) closes seats, after checking the handoff. Seats never close themselves and no script closes seats. The overseer runs `agentmail/bin/fleet-guard` as a persistent Monitor; it is ALERT-ONLY (IDLE, CODEX-UNREAD, OVERSEER-UNREAD, GONE lines) so a finished or waiting seat cannot be forgotten. On each alert the overseer acts the same turn: assign work, nudge, or close the seat itself.
- A blocked seat looks busy (the operator, 2026-09-14: "one is blocked and you didn't know"): a seat's `flutter test` hung on a macOS Gatekeeper dialog ("flutter_tester is an app downloaded from the internet") while its pane still showed a spinner, so an idle-only check missed it. fleet-guard now also alerts STUCK (screen unchanged for 8 minutes while "working"), PROMPT (question or permission prompt text in a pane) and MACOS-DIALOG (CoreServicesUIAgent up). Root cause removed the same day: `xattr -dr com.apple.quarantine $FLUTTER_ROOT/bin/cache`. Re-run it after any Flutter upgrade or cache re-download, before seats run flutter test.
- Before closing a seat, record evidence that it is finished, not busy: its DONE/verdict mail is in, the bottom status line of its pane is past tense ("Worked for", "done") with an empty input, no "esc to interrupt"/"Working (" in the last lines, and no child command running. Report that evidence to the operator when closing. fleet-guard reads only the bottom status lines, because old "Working (" lines stay visible higher up in a Codex transcript.
- Closing the LAST seat in the shared grid window destroys that window and the operator's Terminal view jumps to another window (2026-09-14). Before closing the last pane, first launch or join the next seat into the grid, or re-create circle:circle-agents immediately afterwards and `tmux select-window` it; then re-verify `tmux list-clients` shows the grid window.

## 20. A watcher that expires is a seat that is deaf, and an alarm that matches the wrong name is no alarm

Two failures on 2026-09-16, found while one security-audit seat sat blocked for many minutes and nothing raised an alert. the operator noticed it by looking at the screen.

**Seat watchers expire.** A Claude seat arms its mail watcher as a Monitor, and a Monitor has a hard 30-minute lifetime. When it expires the seat is told once and must re-arm it. The audit seat did not, so it never saw the overseer's STOP mail, finished its turn, and asked "tell me whether to continue" in its own pane, where nobody reads.
For runtimes with a persistent notification tool, every boot instruction says to re-arm the watcher when it expires for the whole run.
Without that tool, use the startup/step polling and overseer nudge in rule 9.
Never end a turn with a question in the pane. The overseer applies the same rule to its own watcher and fleet-guard.
When a seat seems to ignore mail, check its unread count first (`ls .agent-mail/<seat>/new | wc -l`); a non-zero count on an idle seat means its watcher died. A one-line pane nudge telling it to run `mail-read` is the recovery.

**fleet-guard was blind to almost every seat.** Claude Code retitles its pane with a status glyph (`✳ <seat>`, or a spinner while working). fleet-guard matched the raw pane title against the maildir name, found no directory called `✳ app-...`, and silently skipped the seat, so IDLE, STUCK and PROMPT never fired for it. Seats whose title the overseer had set by hand still matched, which made the guard look healthy. Fixed the same day: the title is stripped of any leading non-alphanumeric prefix before matching, and the prompt patterns now include Claude Code's selection dialogs ("enter to select", "model switch", "safeguards flagged") - a lesson first written down on 2026-09-15 and never implemented.
Verified against the live panes: before the fix the audit seat was not watched; after it, it is. This is rule 15 again - a check that reports the same thing whether or not the subject failed is not a check. Test a guard by making it see a known-bad pane.

**Opus 5 on security work, again.** A full security audit on Opus 5 was stopped by the "Model switch" safeguard dialog, exactly as a security-testing seat was on 2026-09-15, and despite the handoff saying to use Sonnet. Security audits, pen tests and exploit reproduction run on Sonnet. The overseer does not answer that dialog: its first option changes a global setting for every session, which is the operator's decision. Dismiss it with Esc (no switch, no setting change), have the seat persist its state to disk by mail, then move the work to a Sonnet seat that resumes from that state.

**EnterWorktree prompts a human.** A verifier seat called Claude Code's built-in EnterWorktree tool, which asks for approval to relocate the session's permission root to a model-supplied path. Nobody answers a seat's pane, so it blocked. The repaired fleet-guard raised PROMPT within seconds - the first time it caught a stall before the operator did. The overseer declined it (Esc; it does not approve permission grants on another agent's behalf). Seats use `treehouse get --lease`, then read the worktree by absolute path and run commands as `cd <worktree> && ...` inside one Bash call; they never call EnterWorktree. Say so in every task that involves a worktree.

**Prompt detection reads the bottom of the pane only.** The first version scanned the whole screen and raised PROMPT when an agent was editing code containing "approve this". A real dialog always renders just above the status line, so fleet-guard now checks the last 16 non-empty lines. Tested against the two real dialogs from 2026-09-16 (Opus model-switch, EnterWorktree) and the false-positive diff: both dialogs still caught, the diff ignored.

**A thinking seat is not an idle seat.** During a long "still thinking" phase Claude Code hides the "esc to interrupt" hint but keeps a present-tense spinner line ("✻ Choreographing… (5m 34s"), so fleet-guard called a busy reviewer IDLE. It now also treats a word ending in "…" followed by an elapsed-time bracket as working; a finished turn reads "Churned for 17s" and is still idle. Tested against both spinner styles and a finished turn.

*Revision: rule 20 added 2026-09-16.*

- 2026-09-17: two workers told "no sub-agents" spawned forks anyway and sat idle waiting on them. `agentmail-launch` now also disallows the `Agent` tool for every non-overseer seat; a seat that genuinely needs sub-agents (e.g. the security-audit skill) sets `"allow_subagents": true` in roster.json.

## 21. One task per seat, and the task id is the test

Operator feedback, 2026-09-21: "why are u asing the same subagent to do things? that might cause context problems i guess. please dont do that.. one task to one agent only. make sure of that."

A seat receives exactly ONE task id in its lifetime.
When that unit is finished, the seat is closed (rule 19's close-when-done), and any further work goes to a freshly launched seat.
Sending a second task id to a live seat is the violation, and it stays a violation when the seat is idle, when the new work is adjacent to the old, and when relaunching feels wasteful.

**Why this is not merely tidiness.** A seat that has already completed one task carries that task's entire context forward: every file it read, every wrong turn it took, every assumption it formed.
That context is re-sent on every wake, so it is a standing token cost, and worse it is a correctness risk, because the seat reasons about task B through task A's assumptions and does not know it is doing so.
A fresh seat reads the new task cold, which is the whole point of dispatching by mail with a self-contained brief.

**What is the same task and is allowed.** A correction ("you got this wrong, redo it"), an unblock ("I built it for you, continue"), a boundary reminder, or a continuation ("now run the AFTER") of the task the seat already holds.
The test is mechanical: if the work needs a NEW task id, it needs a NEW seat. If it is still the same task id, mail the seat.

**The incident.** On 2026-09-21 the overseer broke this twice in one session.
`app-security-task-owner` was given `resume-secfix-0921-x9r4` and then, once it reported DONE, `run-secfix-0921-t3m8`.
`app-device-task-owner` was given `device-0921-r8v2` and then `redfix-0921-m2k9`.
Both times the second task was sent because the seat was already alive and warm and relaunching looked like overhead.
That is precisely the reasoning this rule exists to override, and the operator caught it from the outside while the overseer did not notice it from the inside.

Before returning a treehouse lease, the integrator verifies that all edits and unpushed commits are integrated or durably preserved.
Closing a runner does not return its lease.
Do not force-return dirty or unpreserved work; mail the blocker and lease identity.

*Revision: rule 21 added 2026-09-21; lease preservation clarified 2026-10-21.*

## 22. Grant the worktree directory, or the seat prompts the human it must never reach

Found 2026-09-23. A Level 3 seat, launched with `--dangerously-skip-permissions` and `--disallowedTools AskUserQuestion`, still put a permission dialog on the operator's screen: *"Do you want to make this edit to firebase.json?"*, in a treehouse worktree under `~/.treehouse`.

**Directory access is a separate gate.** `--dangerously-skip-permissions` does not cover it and neither does removing the interactive-question tool, exactly as rule 10's read-block is a separate gate. The seat had no mechanism left except a prompt, and the only thing that can answer one is whoever is looking at the pane. That is the rule 12 stall arriving through a door rule 12 does not watch.

**Why it hid all day.** READS outside the granted directories are fine while `blockReadsOutsideWorkingDirectories` is false. Only the first WRITE trips it. So read-only research seats and seats working in the main checkout were unaffected, and the failure surfaced only when an implementation seat first edited a file inside its own leased worktree.

**The contradiction it exposed.** The standing rule is that seats take isolated treehouse worktrees rather than sharing a checkout ([[treehouse-not-raw-worktree]]). But `agentmail-launch` granted `--add-dir` for the org root and the mail root only, and treehouse worktrees live under `~/.treehouse`, OUTSIDE both. Every seat sent to a worktree was one edit away from prompting the operator.

**Fixed at the launcher**, not per seat: `agentmail-launch` now adds `--add-dir <TREEHOUSE_ROOT or ~/.treehouse>` for every Claude child when that directory exists, with the reasoning in a comment so it is not tidied away later.

**The recovery, when a seat is found blocked on a prompt.**
Do not approve permission grants on another agent's behalf (rule 20).
Dismiss without granting trust where supported, preserve the patch and handoff, and stop only the exact owned runner.
Fix the cause and relaunch the same task in a fresh pre-granted lease; never discard edits to free the old lease (rule 32).
Restarting the same seat for the same task ID is not a rule 21 violation.

**The check that would have caught it:** launch one seat and have it EDIT a file in its worktree before trusting the fleet. A seat that reads successfully proves nothing about whether it can write.

*Revision: rule 22 added 2026-09-23.*

## 23. When the overseer's runtime runs out, hand the seat to the other runtime at once

Operator feedback, 2026-10-07: "claude stopped saying it hit the limit, but I HAVE CODEX fully functional, u were supposed to track that and start codex main agent with necessary prompt".
On 2026-10-07 the Claude overseer hit its usage limit mid-build with four work packages in flight.
It wrote a handoff and stopped; the Claude seats stalled with it, and nothing moved for over two hours while the Codex budget sat at 99% unused.
That is the waste rule 19 exists to prevent, applied to the overseer seat itself.

- Track your own runtime. Run `agentmail/bin/fleet-usage` at session start, before each dispatch batch and at least hourly during long runs. At 80% of the 5-hour session window or 90% of the weekly limit, prepare the handover; do not wait for the hard stop.
- On the first usage-limit warning (or at the threshold), in this order: write `conversation-context/NEXT_MAIN_AGENT_HANDOFF_<date>.md` (what is merged, every in-flight seat with branch/SHA/brief path, the next action for each, open decisions, deploy-day items); then start the Codex overseer using a reviewed local handoff launcher (the bundled `overseer-codex.command` is a legacy site example, not a portable launcher) in a visible terminal the operator watches (rule 13); it runs with on-request approvals so the operator can approve the host operations (tmux, ps, git) a supervisor needs - never "never" for the overseer; then tell the operator in one line that the seat moved to Codex and where.
- The incoming Codex overseer reads that handoff, re-arms its mail check, relaunches stalled Claude seats' tasks on Codex where they fit (rule 19 task fit; Flutter-on-host work may have to wait for the Claude reset), and keeps the fleet moving.
- The reverse holds too: a Codex overseer near its limit hands back to Claude the same way.
- Only one overseer acts at a time. The outgoing overseer stops dispatching once the handoff is written; if it is still alive after its limit resets, it reads the newer handoff and asks the operator which seat continues before acting.

## 24. Never scan the whole disk or home folder

No `find /`, `find ~`, `find /absolute/home/...`, `grep -r` or `du` over `/` or `~`, by the overseer or any seat (Claude or Codex). On macOS a whole-disk walk triggers one privacy dialog per protected folder (Photos, Contacts, Documents, Downloads, ...) on the operator's screen. Search only the repo, your treehouse worktree, or `.agent-mail/attachments/<topic>/`. Seats write every artifact (screenshots, logs) under `.agent-mail/attachments/<topic>/` and quote the absolute path in DONE. Claude sessions are also hard-blocked by deny rules in `~/.claude/settings.json`.

*Revision: rule 24 added 2026-10-09.*

## 25. Every agent that drives a device keeps the shared screen map

Operator feedback, 2026-10-12: whenever an agent accesses the phone, it records the screens, elements, taps and navigation it sees into a shared map, so the next agent navigates from the map instead of rediscovering it.
The maps live in `$IAC_ROOT/device-maps/` (one file per app, e.g. `app.md`); the file's header defines the format.
Read the map before navigating. Record each screen you actually see, where each tap led, and any trap that broke a run.
The map grows only by normal use: never tap around just to fill it.
The overseer puts this rule in every brief that touches a device.

*Revision: rule 25 added 2026-10-12.*

## 26. Sweep open PRs and new branches every session

Operator feedback, 2026-10-13: open PRs from other sessions held findings the fleet never saw.
Outside AI sessions had opened 14 PRs on a product repo with real findings, and nobody in the fleet looked at them for months.
At every session start, alongside the mail drain, the overseer runs `gh pr list --state open` and checks new remote branches on every active repo.
New PRs are triaged the same day into merge, rework or close, and every closure carries a comment saying why.
A real finding inside a PR that is closed becomes a fresh fix task against current code; closing the PR never closes the finding.
Template: `.agent-mail/attachments/<topic>/BRIEF.md` and its TRIAGE.md.

*Revision: rule 26 added 2026-10-13.*

## 27. Every merged change ships a change report the human can read without the diff

Operator feedback, 2026-10-19: he designs the architecture but no longer writes the code, and after a night of agent work he could not tell what was written, which flows changed, which files and functions were touched, or how a fix was implemented.
The knowledge existed only scattered across DONE mails and reviews.

Every unit of work that changes code ends with a change report, and nothing merges without one.

- **The author writes Part 1 (narrative).** Generate the skeleton with `agentmail/bin/change-report <base> HEAD --repo <worktree> --task <task-id> --out <file>`, then fill every `TODO(author)` section: what and why, the flow step by step (entry point first, real function names), how it is implemented (design choice, what was rejected, known limits), how it was verified (failing test first, suites with counts, what was NOT checked), and deploy/release impact. Codex seats that cannot write the repo deliver it as `attachments/<batch>/<KEY>_CHANGE_REPORT.md` next to their patches and link it in DONE.
- **Part 2 (facts) is generated from git, never hand-written.** Commits, every file changed, functions and classes added/changed/removed, test cases, dependency diffs and sensitive areas (server, rules, payments, keys, config). It is the ground truth: if Part 1 disagrees with it, that is a review finding.
- **The reviewer checks the report against the diff**, not just the code: a flow step that does not exist, an unlisted sensitive area or a missing deploy step is CHANGES-REQUIRED.
- **The overseer withholds merge clearance** while `change-report --check <file>` reports any `TODO(author)`. On merge the integrator regenerates Part 2 for the exact merged range (`<merge>^1..<merge>`), keeps the author's Part 1, and commits the result in the product repo as `docs/changes/<YYYY-MM-DD>-<task-id>.md` in the same merge, so the record travels with the code.
- **Daily digest.** After a batch or an overnight run, a designated documentation/integration seat writes `docs/changes/<YYYY-MM-DD>-DIGEST.md`: one paragraph per merged task in plain language linking its report, plus what is held, what needs the human, and the deploy impact in one list.
- **Test-case ledger.** Any change to user-visible behaviour also updates the product's sheet in `$IAC_ROOT/AUREUS_TEST_CASES.xlsx` (plain-language case, expected result, honest status: PENDING until deployed and seen working).

The overseer puts this rule in every brief that changes code.

*Revision: rule 27 added 2026-10-19.*

## 28. Document a file the first time you touch it, and keep the project map current

Operator feedback, 2026-10-19: every file an agent touches should be documented properly the first time, and a graph should show which file links to what, in a tree, updated as agents touch files rather than all at once, so that in the end he has a detailed map of the entire project.

- **First touch documents the file.** When an agent edits a source file that has no header doc comment, it adds one at the top in the same change. Keep it short and true to the code:
  - line 1: one sentence, what this file is for (this line is what the map shows);
  - then: the main classes/functions and what they do; what it depends on (other project files, services, storage, network); who uses it; side effects (writes data, calls the server, sends money, touches keys or hardware).
  - Dart: `///` lines at the very top, followed by `library;`. TS/JS: a leading `/** ... */`. Python: the module docstring.
  Tooling lines (ignore_for_file, eslint, licence banners) are not documentation.
- **Later touches keep it true.** If a change alters what the header says, the header changes in the same commit. A stale header is a review finding.
- **Folders.** A new folder gets a `README.md` whose first line says what the folder holds.
- **Never document in bulk.** Coverage grows only through real work on a file. Do not open files just to add headers.
- **The map.** `agentmail/bin/project-map --repo <repo>` writes `docs/map/PROJECT_MAP.md` (folder tree, each file's purpose or `undocumented`, the files it links to, how many use it, coverage per folder) and `docs/map/graph.json`. The integrator regenerates and commits it on every merge, next to the rule-27 change report.
- **Agent graph.** Where a repo has `graphify-out/`, agents also run `graphify update .` after code changes so `graphify query/path/explain` stay current.
- **Reviewers check it.** A touched file left without a header, or with a header that no longer matches the code, is CHANGES-REQUIRED.

The overseer puts this rule in every brief that changes code.

*Revision: rule 28 added 2026-10-19.*

## 29. Seats submit focused tests to shared warm lanes; integration owns builds and full validation

Operator feedback, 2026-10-19: cold Flutter compilation and duplicated Node installs in 7-8 seat worktrees exhausted a 16 GB Mac and caused stale-dependency failures.
`agentmail/bin/testlane` keeps a bounded pool of dedicated warm checkouts so seats share compilation and dependency caches.

- **Seats submit focused tests with `testlane run`.**
  Use `testlane run --queue <shared-queue> --repo-dir <seat-worktree> --base <review-base> -- <argv...>` with the smallest explicit test-file list that proves the change.
  The client snapshots tracked changes and nonignored untracked files, including binary files, without writing the seat's index or object store.
  `npm test`, `npm run build` and `npx tsc -p <config>` use `functions/`; other commands default to the repository root, with `--cwd functions` available for Node tests.
  A queue wait expiry leaves the submitted job intact; inspect `testlane status --queue <shared-queue>` before submitting again.
- **The designated host-capable integration/build seat starts and stops the runner outside author/reviewer sandboxes.**
  Start `testlane runner --repo <product-repo> --lanes 4 --queue <shared-queue>` from a trusted environment with Flutter, Node, npm, Python 3 and git installed.
  Grant seats write access to the queue, then publish its absolute path in task briefs.
  The runner creates and owns only `<shared-queue>/lanes/<n>` detached git worktrees; it never leases or changes treehouse pools.
  SIGTERM/SIGINT stop intake and drain active jobs; restarting the same queue resumes its pool.
  A surviving worker retains its lane lock across a runner crash; a dead worker's job is retried once after the lane is free.
  `testlane status --queue <shared-queue>` shows queue depth, running jobs and quarantined lanes.
- **Warm caches survive each reset.**
  The runner preserves `node_modules/`, `.dart_tool/`, `build/`, `functions/lib*` and `.test-build/`, cleans other generated files, and reinstalls only the dependency group whose manifest/lock hash changed or whose cache is missing.
  Initial warmup runs `flutter pub get` and `npm ci` in `functions/`.
  Full logs and immutable per-job results live under the queue.
- **The runner accepts only an explicit command allowlist.**
  Supported forms are `flutter test --no-pub <paths...>` (concurrency 1), `flutter analyze <paths...>`, `python3 tool/analyzer_gate.py`, `npm test`, `npm run build`, `npx tsc -p <config>` and `node --test <files...>`.
  Paths must stay inside the lane and may not traverse symlinks; shell strings, arbitrary flags, app builds and dependency-install jobs are rejected and logged.
  TypeScript uses the lane's installed compiler directly, so npx cannot install a missing package.
  Both runner-managed TypeScript paths first resolve JSONC and inherited configs with `tsc --showConfig`, then pin `rootDir` to `functions/` and all emission paths with runner-owned CLI flags.
  A config named `tsconfig.test.json` emits under `functions/.test-build/`; other explicit TypeScript configs emit under `functions/lib/`, preserving paths relative to `functions/`.
  Declarations and incremental build-info files stay in that same output directory, and `noEmitOnError` prevents emission from invalid source roots.
  Output directories and their existing contents must resolve inside that fixed directory, without symlinks, special files or regular files with multiple hard links.
  Configured `outFile`, `generateTrace` and `generateCpuProfile` outputs are unsupported and rejected before compilation, including values inherited through `extends`.
  Other command forms also reject caller-supplied output-path flags.
  Focused Node targets under `functions/.test-build/` are compiled with `tsconfig.test.json` in the same job and lane, sharing the test timeout.
  Those generated targets may be absent in the seat; the runner removes the requested cached output files first and requires the current patch to emit them again.
  Test-config compiles also discard their fixed incremental build-info file so TypeScript cannot skip recreating a deleted generated target.
  This controls command submission and runner-managed compiler output paths; it is not a host filesystem sandbox.
  Test code, npm scripts and dependency manifests still require review and trust because they and installation hooks execute with the runner user's host permissions, including access beyond their lane.
- **Seats never build apps** (apk/ipa/web or Gradle) **and never run the full analyzer gate or full suites.**
  A designated host-capable integration/build seat builds the app and runs combined validation once per cleared batch (rule 31).
  When lanes are busy, a brief may permit delivery with unrun checks stated honestly.
  Existing `heavy.sh` remains unchanged during migration; the overseer explicitly announces the switch to the shared queue.
- **Cap concurrent seats at about 5 on this Mac.**
  The overseer checks swap and load before launching, and cleans up only its identified orphaned build processes.
  Queue additional seats and use remote review capacity when available.
- Every brief that touches code carries this rule and the shared queue path.

*Revision: rule 29 added 2026-10-19; updated 2026-10-19 for task testlane-1019 with shared warm runner/client lanes.*

## 30. The operator must SEE every seat: one viewed window, no strays, no orphans

On 2026-10-20 the operator asked "where are all the subagents? why can't I see them?" for a whole session of four seats.
The only Terminal.app client was attached to `fleet:1` (the holder window) while every seat was split into a separate `fleet:2 seats` window that nobody was looking at.
That window also held a forgotten `sleep 86400` pane, and two `mail-watch` processes from seats closed three and four days earlier were still running.
The overseer had not armed `fleet-guard`, so nothing reported any of it.

- **One window.** The holder pane and every seat pane live in the SAME window, the one the Terminal client is showing (`fleet:seats`, index 1). Never create a second seats window; if one exists, `join-pane` the holder into it and `move-window` it to index 1.
- **Verify the viewer, not the session.** After every launch or close, `tmux list-clients` must show a Terminal.app client on the seats window (trace the client pid up to Terminal.app, per "Know where you are running"). A session marked "attached" proves nothing about which window is on screen.
- **No placeholder panes.** Never keep a window alive with a `sleep` pane; the holder pane exists for that. Any pane in the seats window that is not a seat or `fleet-holder` is a defect.
- **Closing a seat kills three things:** the `agentmail-run --seat <seat>` process, its pane, and any `mail-watch <seat>` process; then `treehouse return` the lease (rule 21).
- **Arm `fleet-guard --window fleet:seats` as a persistent Monitor at session start**, next to the inbox watcher. It now also emits `HIDDEN` (no viewer, or the viewer shows another window), `STRAY-PANE`, `ORPHAN-WATCH`, and `PROMPT` for the Codex "Hooks need review" dialog. Act on every line.

## 31. The overseer does no legwork: a standing integrator seat merges, the overseer stays free to talk

Operator feedback, 2026-10-20 (4th time): "why are u performing tasks on ur own? dind i ask u to allocate to subagents and stay free for me".
The overseer's whole job is to talk to the operator, decide, write briefs, launch and close seats, and read verdicts.
It does not commit, merge, resolve conflicts, run tests, refresh fixtures or hashes, regenerate the project map, import workbook rows, push, or edit any project file - not even "just this once".
All of that goes to a standing integrator seat per active repo (Codex by default), launched at session start and kept for integration only.
The integrator receives `merge` mail (branch, verdict mail id, worktree lease) and does: commit a sandbox-blocked author worktree, merge to the integration branch, resolve conflicts keeping every side's intent, run the focused post-merge checks named in the verdict, refresh pinned hashes, regenerate the project map (rule 28), import PENDING workbook rows, push, return the lease, and mail MERGED with SHAs and test counts.
The integrator is the one seat exempt from rule 21's one-task-per-seat closure; it is closed when its repo's merge queue is empty at session end.
The overseer may run a check of a few seconds only when the answer decides a dispatch or a safety call.
If the overseer catches itself running a second legwork command in a row, it stops and writes a brief instead.


Batch cleared merges rather than waiting for a separate CI cycle after each merge.
The integrator performs one combined local validation and one push, then checks CI on the final pushed SHA (rule 33).
If an uncommitted prerequisite is needed in another author branch, the integrator first records it as a WIP commit, then merges that commit into the dependent branch and records the dependency in the handoff.
A WIP commit preserves work; it is not review clearance or production release authority.
Never ask a sandboxed author to stash, discard or force-checkout work to unblock integration.
The integrator must have verified Git-write capability; assigning the role to a blocked Codex sandbox does not provide it.

## 32. Never brief a seat to discard work

A clean base means a fresh treehouse lease, not reset/checkout of an occupied worktree.
Never use brief wording such as drop the old changes, reset to development or clean the worktree.
It can provoke destructive Git attempts, repeated classifier denials and a human prompt.
Preserve the old lease; have the authorized lease owner acquire a fresh one at the named base, then copy only the required local build inputs without mailing their values.
Every such brief says: never discard; mail the overseer instead.

## 33. Cancelled or superseded CI is not green

A release claim names the exact final pushed SHA and every required job's completed conclusion.
Cancelled, superseded, queued, missing, timed-out or failed jobs do not count as successful validation.
A skip is acceptable only when the job's documented path/platform condition explains it and required coverage still ran.
After another push cancels a run, follow the replacement run on the new SHA; never combine green jobs from different candidates.
Read raw job output and keep unrun checks explicit.

## 34. Startup prompts and roster descriptions are part of the launch contract

Changed plugins can show Hooks need review, N hooks need review, or Modified since last trusted / review required; a new repository can show Trust this folder.
The supervisor inspects the actual dialog before sending a boot prompt and verifies Working plus a task ACK afterwards.
Hook or directory trust is a human action, never a worker's or a launcher's automatic keystroke.
Use a supported continue-without-trusting/dismiss path when available; otherwise preserve state and report the blocker by mail.
Do not disable safeguards or grant blanket trust to clear a startup stall.
The current launcher has a known automatic-trust branch; its repair is pending, and these docs do not claim it is safe to run unchanged.
When nudging, submit text and Enter separately (or use the verified seat-nudge helper) and confirm activity; typed text in an idle composer is not work.
Capture pane IDs at creation, then verify the seat title before targeting them; never select the last pane by list position.
Roster description defaults must match authority: an author is not READ-ONLY, a reviewer is not an implementer, and an integrator is scoped to integration.
Check role, home, project, delegation and description together before launch; changing prose does not grant permissions.

## 35. Check runtime behavior and control clocks across process boundaries

Text/regex checkers can be bypassed by equivalent syntax, comments or renamed bindings.
Use ground-truth checks for the claim: for example load compiled exports in an isolated local test to verify actual callable registration/metadata, rather than grepping export source text.
Never import deployment code with live credentials or production side effects just to inspect it.
A source scan may supplement runtime evidence; it cannot replace it.
Use one shared enum/codec per status/type/kind concept, with conversion at the wire boundary; string-case differences must not silently choose different behavior.

A fixed Date.UTC fixture becomes a time-bomb when a spawned process still uses the real clock.
Pass the same injected clock/reference instant across the boundary, or derive fixtures from a captured current instant with appropriate margins.
Prove expiry/TTL and boundary behavior on both sides, including in the actual subprocess path.
A fake clock installed only in the parent is not evidence that the child shares it.

## 36. Release prerequisites must precede device builds and installation

Do not run partial/baseline acceptance on the owner's phone.
First finish and review the planned batch, compare the candidate's server/rules/index/config changes with the recorded deployed base, and have the human deploy dependencies.
For clients with force-update enforcement, the owner must publish a valid Remote Config policy before any build containing enforcement reaches a device; a saved draft or local defaults are not publication.
Check supported/minimum versions against the real build being installed; do not invent an inflated version to bypass the gate.
Use the next real version/build number and verify new code inside the packaged APK, not merely in compilation output or cached intermediates.
Release mode/flavor/signature must match the requested artifact; Android-only scope does not silently become an iOS blocker.
Read and update the device screen map during normal use (rule 25).

Deployment packets use the changed-function import closure from the actual deployed base to the reviewed candidate: changed handlers plus exported functions affected through shared imports.
Explain additions/removals, dependencies, indexes/rules/config and ordering; never infer the deploy list from directly edited handler filenames alone.
At the 2026-10-21 handoff, tool/changed_functions.py was pending; verify it exists and is reviewed before relying on it, otherwise document a manual closure review.
This is packet preparation only: agents never execute cloud commands, including discovery/authentication, SDK/API equivalents or CI wrappers.

## 37. Verify the production owner, source repository and served deployment

GitHub merge success is not Vercel deployment success.
Production follows the owner's configured source repository and branch, not an upstream fork or a lookalike local clone.
A production site can follow an owner fork from main while a related repository uses master or development.
Record the real source and branch in ignored local inventory, and verify them with the deployment owner.
Vercel can refuse commits authored by contributors who lack project/team access even when they have GitHub access.
Request legitimate access or an owner merge/deploy; never spoof the author or claim a merge is live.
Verify the deployment's source SHA and the actual served page/asset after the authorized release.

## 38. Fetch federated mail before reporting remote state

A local project coordination-mail directory is a Git snapshot, not a live inbox.
Before quoting remote unread counts or saying there is no new mail, its authorized repository owner fetches and integrates the intended remote branch, preserving local work and stopping on divergence.
Workers do not enter another repo to do this; ask its owner through mail.
Read the resulting messages in full; only the owning site consumes that inbox.
A visible new/ to cur/ receipt on a federated channel is distinct from local reading, approval and completed work.

## 39. Human-only steps get complete instructions; agent work stays with agents

At the reference site, the operator alone operates GCP, deployments, Remote Config publication, secret provisioning and store submission.
No agent may execute even read-only GCP status/auth/SSH or use an SDK, API, Terraform, CI trigger or remote wrapper as a substitute.
This prohibition survives a general proceed/deploy request and is not an approval-escalation path.
Draft TYPE-THIS commands only, with the actual execution location, complete directory, expected output, stop conditions and rerun behavior.
For a cloud VM, start inside the console-opened SSH session; omit the connection/transport wrapper from copied runbooks.
Never refer to steps in a previous message or use unresolved placeholders in a block handed to the human to execute.
Integration/build seats do ordinary Git, tests, builds and local checks within their authority; do not invent human prerequisites without checking the evidence first.
Never bypass security hooks with no-verify, and never brief a worker to weaken security checks to prove a test.
If a proof is blocked, preserve evidence and request an approved testing method rather than retrying until a prompt appears.

*Revision: 2026-10-21, rules 3/9/13/19/21/22/27-31 reconciled and rules 32-39 added from operational memory and the onboarding task.*

*Revision: 2026-10-22, public documentation generalized; real team inventory and owner identities remain in ignored local handoffs.*
