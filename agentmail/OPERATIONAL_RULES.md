<!-- Defines AgentMail fleet operating rules; overseers and seats follow these alongside SPEC.md and the seat template. -->
# AgentMail — Operational Rules

**1.1 update:** [SPEC.md](SPEC.md) and [UPGRADE.md](UPGRADE.md) take precedence
over historical operating advice below. Use `--body-file` or quoted heredocs
for safe Markdown transfer. Research/requirements/implementation are distinct
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

Never edit or delete a sent message. A correction is a **new appended message** (SPEC §3.2). The read acknowledgement is the `new/ → cur/` move; that git-visible transition is the protocol ack and is sufficient — an extra "landed" note is optional etiquette, not a second required protocol.

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

## 9. Launch children in a per-project tmux session, and always `--terminal tmux`

Use a tmux session named for the project, such as circle, and preserve any existing session and work.
Use agentmail-run-backed roster seats through agentmail-launch with --terminal tmux --apply.
For Codex children omit --skip-permissions: the current launcher rejects it and retains the Codex sandbox.
Claude-only bypass arguments are not portable; apply them only under the existing authorization and safeguards.
The supervisor has a separate interactive approval profile and must pass the host-control checks in [SUPERVISOR_BOOTSTRAP.md](SUPERVISOR_BOOTSTRAP.md).
A tmux route does not bypass an OS or runtime denial.
Before replacement, identify the current seat runner and watcher and stop only the exact owned instances through an approved mechanism.
Start the watcher first and explicitly submit the boot prompt if it was not executed.
Execute an attachment script to open the required Terminal.app window; do not type a command into a startup-sensitive shell.
Verify the target project, client/pane mapping and task acknowledgement before reporting the seat running.

## 10. A child must be able to READ the org root, or it stalls unattended

A child's working directory is its own project sub-repo, but it must read the shared mail spool (`.agent-mail/`) and the `agentmail/bin` helpers, which live in the **org root above** that sub-repo. If the host enforces a working-directory read block — Claude Code's `permissions.blockReadsOutsideWorkingDirectories: true` — the child stops on a permission prompt for **every** mail read, and unattended (`--skip-permissions`) it **stalls**, because: that block is a separate gate that `--skip-permissions` does **not** override; it fires even on dynamically-built shell paths (`cd X && ls`) that are actually inside the org; and a per-project settings file **cannot** relax a global one — only the host's global settings count. An unattended fleet therefore needs that block **OFF** in the host's global config. Know the trade-off: **no** single setting gives all three of *read-anywhere-in-the-org*, *block-the-parent-directory*, and *never-prompt* — pick two. An unattended fleet needs the block off, and the parent-directory boundary then rests on instruction (tell seats not to read outside the org), not on the sandbox.

**Settled, after paying for it twice: never turn that block ON while the fleet is running.** Its enforcement mechanism *is a permission prompt to the human*, so switching it on to "protect the boundary" guarantees the thing the supervision model most forbids — a child interrupting the operator (rule 12). Permission-bypass does not override it, and disabling the interactive-question tool does not cover it; they are different mechanisms. Worse, the supervisor **cannot** clear the resulting dialog — answering another agent's permission prompt is itself refused — so a stalled child can only be freed by the operator or by a relaunch that discards its in-context work. **Control the boundary by removing the reason to cross it, not by walling it:** (a) relocate every tool the agents need to *inside* the org root (a browser-automation binary cached in the user's home is the usual culprit — point its browsers-path at an in-org directory), (b) instruct the boundary in the seat's boot prompt and grant `--add-dir <org root>` only, and (c) **audit instead of gating** — session transcripts record every tool call, so grep them for home-directory paths periodically. Auditing costs the operator nothing and answers the question the wall was supposed to answer; in the incident that produced this rule, an audit disproved the suspected violation outright (the prompts the operator saw came from the browser binary launching, not from any agent reading personal files).

## 11. Every spawned agent is a mail seat — it escalates by mail, never prompts the human

When the supervising agent spawns a worker (to parallelize, to draft, whatever), that worker MUST be a mail-native **seat**, not a bare CLI process. A bare agent has no escalation path: the moment it hits a real decision it stalls asking a human who is not watching its terminal — which breaks the supervision model, where decisions flow **up** to the supervisor by mail, never sideways to whoever happens to see the pane. Making a worker mail-native is three steps beyond launching a bare CLI: `agentmail-init <seat>` (its maildir), a **roster entry** (so it is tracked and scoped to its project, not the org root), then launch through `agentmail-run --seat <seat> -- <agent-cli> …` with a boot instruction that says: arm the watcher first, take the task by mail, **escalate every decision to the supervisor by mail, and never open an interactive question or prompt a human**. Dispatch its task by mail too, not by typing into its pane. Converting a bare worker to a seat mid-flight loses no work if you relaunch it in the SAME worktree — its branch and commits are on disk, not in the process.

## 12. A child talks to NO human — enforce it, don't just instruct it

Only the supervising agent speaks to the operator; a child escalates decisions **up by mail** (rule 11), never to whoever is watching its terminal. But instruction alone is not enough — an agent handed a hard decision will still reach for an interactive-question / prompt tool and block, waiting on the very human it was told not to address. So **remove the capability**: launch every child with its interactive-question tool disabled (Claude Code: `--disallowedTools AskUserQuestion`). Combined with permission-bypass (no permission prompts), a child then *physically cannot* block on a human — its only escalation path is mail. `agentmail-launch` now does this for every child seat automatically (and also grants the child `--add-dir <org root>` per rule 10, so it can reach its mailbox); if you hand-roll a launch, add the flag yourself.

## 13. The operator must be able to SEE the fleet — a detached session is not "running"

A headless tmux session satisfies `tmux ls` and satisfies nothing the operator asked for. **Launching a fleet is not finished until a real terminal window is attached to it and the panes are watchable.** The check that matters is `tmux list-clients -t <project>`; empty output means invisible, no matter what `tmux ls` reports. Reporting "the fleet is up" off `tmux ls` alone is the recurring failure this file ends on — a check whose subject is not the thing at risk.

**Attach by EXECUTING a script, never by having AppleScript type a command.** `osascript -e 'tell application "Terminal" to do script "<cmd>"'` *types* the command into a newly-spawned interactive shell, so **anything the shell prints at startup that reads a keypress will swallow the first character** of that command. The symptom is a parade of unrelated-looking errors from what is one bug: `tmux attach` → `zsh: command not found: mux`; `/Users/x/y.command` → `no such file or directory: Users/x/y.command`; `exec /opt/...` → `command not found: xec`. In the incident that produced this rule the thief was oh-my-zsh's auto-update prompt (`[oh-my-zsh] Would you like to update? [Y/n]`), and six launch attempts were misread as six different failures before anyone compared them and noticed **exactly one character** was missing from each.

**Latest operator requirement, 2026-09-12: separate visible Terminal.app windows for children.**
This supersedes the earlier single-window/panes-only instruction.
Keep the project-named tmux organization, but verify each attached terminal actually displays its assigned seat.
Multiple clients on one session may follow the same window selection; client count alone does not prove distinct seats are visible.
Do not substitute hidden tabs, detached sessions or internal managed subagents.
The main belongs in Ramesh's current terminal, currently iTerm2.

**Send the boot prompt explicitly; do not trust it to auto-submit.** Passing the boot instruction as a CLI argument to the agent binary does not reliably execute it — seats sit at an empty prompt looking hung when in fact nothing was ever submitted, and the operator reasonably reports them as "stuck". After launch, `tmux send-keys -t <pane> -l "<boot>"`, pause, then send `Enter`. Confirm by reading the pane: an interrupt hint ("esc to interrupt") means it is working; a bare prompt means it is not.

Two fixes, apply both:
- **Root cause:** silence the startup prompt (`zstyle ":omz:update" mode disabled`, `DISABLE_AUTO_UPDATE=true`, `DISABLE_UPDATE_PROMPT=true`). These must be placed **BEFORE** `source $ZSH/oh-my-zsh.sh` — appended after it they are read too late and do nothing, which is its own half-hour of confusion. Verify with `zsh -i -c 'echo OK'`: nothing but your own output may appear.
- **Mechanism:** ship a `.command` file (`chmod +x`, `open -a Terminal <file>`). It is **executed** rather than typed, so no keystroke can be eaten by anything — it is robust even on a machine whose shell startup you do not control, which is the reason to keep using it after the prompt is fixed. Have it build the session (holder window first, per rule 9), launch each seat, then `exec tmux attach` so the window the operator is looking at *is* the session.

## 14. Recycling ONE seat must not kill its neighbours

`tmux kill-pane` on a window that holds other live seats **destroys the window when the last pane goes**, taking working agents with it. In the incident that produced this rule the supervisor killed a reviewer seconds after dispatching it a review — the mail survived (it is a file), the agent's in-context work did not. The `keep` holder window (rule 9) guards the SERVER, not a shared window; panes need their own discipline.

To recycle one seat: `pkill -f "agentmail-run --seat <seat>"`, relaunch it, then `tmux join-pane` it back into the shared window. **Never `kill-pane`** while another seat shares that window. Afterwards verify BOTH seats, not the one you touched — count monitors per seat (`pgrep -f "agentmail-run --seat <seat>" | wc -l`, exactly 1 each, rule 4) and read each pane's own banner for the model it is really running. A supervisor that changes one seat and reports success without re-checking the others will ship a fleet in a state it never inspected; the operator finds it before you do.

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

Ramesh, 2026-09-14: several seats shared one repository and every session showed the same name ("skyzai_app"), so nobody could tell the agents apart.
Claude Code labels a session by its working directory unless it is given a name.
Launch every Claude seat with `claude --name <seat-id>`; `agentmail-launch` now does this automatically.
Also title the tmux pane with the seat id (`tmux select-pane -T <seat-id>` with `pane-border-status top`), so the grid shows who is who.
When reporting to the operator, refer to agents by seat id, never by repository or app name.
A second, related lesson from the same launch: a repository's own CLAUDE.md may name a single seat ("Your seat: skyzai-ramesh"); a worker seat started in that repository will reasonably doubt its identity.
Give it verifiable evidence (its roster entry, its own `agentmail-run --seat` process arguments, its queued task mail), never an unverifiable assertion, and add a line to that CLAUDE.md saying roster worker seats are valid.

## 19. Two budgets, one fleet: smart runtime switching and cross-runtime spawning

Ramesh, 2026-09-14: Claude and Codex are both installed and have SEPARATE budgets; the fleet must not drain one while the other idles, and either runtime's main must be able to spawn the other runtime's agents.
Standing procedure for whichever agent holds the overseer seat (Claude or Codex):

- Measure, do not guess: run `agentmail/bin/fleet-usage` (reads Claude /usage and Codex /status, no model calls) at session start, before launching any seat, at least every 2 hours while seats run, and immediately when any seat reports a limit warning. Record the numbers and reset times in conversation-context/CURRENT_STATE.md. A "could not read" result is a failed check, not zero budget.
- Pick the runtime per seat by (1) task fit, then (2) budget: prefer the pool that has unused budget and resets soonest (unused budget is lost at reset), while (3) keeping floors: do not push a pool below about 15% unless it resets within 24 hours, and always keep enough Claude or Codex for the overseer seat itself.
- Separate Codex pools: the Codex account shows a main weekly limit and a separate GPT-5.3-Codex-Spark limit; route small, mechanical work (lint fixes, docs, test scaffolding, simple renames) to Spark before spending the main pool.
- Task fit: Codex seats suit well-scoped code-only authoring, read-only reviews, cross-runtime second opinions, test writing and mechanical edits. Claude seats suit work that needs host tools (tmux, emulators and local sockets, flutter test on the host, GUI/Gatekeeper prompts), long house-pattern Flutter UI work, and security-critical authoring. Right-size models inside each runtime (Codex: spark, luna, terra, astra; Claude: haiku, sonnet, opus), never default to the largest.
- Codex sandbox realities: `workspace-write` blocks writes outside the cwd and `--add-dir` paths. A git worktree's metadata lives in the main repository's `.git`, so a Codex seat that must COMMIT in a worktree needs that `.git` added; local sockets (databases, emulators) may be denied. Read-only review seats have neither problem.
- Cross-runtime review: when possible the reviewer runs on the other runtime than the author (independent model family, and it spreads spend).
- Main handover across runtimes: when the overseer's own runtime approaches its floor, prepare the handoff and propose moving the overseer seat to the other runtime (SUPERVISOR_BOOTSTRAP.md), rather than stalling the fleet.
- Seats report any quota or limit warning to the overseer by mail at once; the overseer rebalances by closing and relaunching work on the other runtime (rule 18 naming, close-when-done policy).
- STRICT frugality (Ramesh, 2026-09-14, "follow that strictly"): run the fewest concurrent seats that meet the deadline. A seat is ended as soon as its specific unit is done, and is NOT kept idle waiting for a verdict or a possible follow-up; follow-ups go to a fresh seat, preferably on the runtime with more headroom. Idle Claude seats still spend tokens every time a mail or monitor event wakes them with their full context.
- Lean on the lower-cost option in both directions: while one pool is low, push suitable work to the other so both last longer; when that pool recovers, rebalance back. Expensive models (Opus, GPT-6-Astra) only for work that needs them (security-critical authoring, hard reviews); reviews and mechanical follow-ups default to the cheaper runtime and model.
- The overseer seat itself is usually the largest single consumer: keep its turns lean, delegate reading-heavy checks to a cheap seat, and avoid re-reading large outputs.
- Closing a finished seat (Ramesh, 2026-09-14): the seat's DONE mail must already be a complete handoff (branch, SHA, tests, done/not done, gotchas, next steps). The overseer then closes it directly: TERM the exact `agentmail-run --seat <seat>` runner (rule 14), verify the runner, agent and watcher are gone, and retile the grid. Do not type `/exit` into the agent's pane and do not require a READY-TO-CLOSE round-trip.
- Mail frugality (Ramesh, 2026-09-14, "follow strictly"): every mail costs tokens for the writer, the reader, and each woken agent's full context. Task mails point at a spec or handoff file instead of repeating it; decisions go out as one batched mail; facts flow peer-to-peer between seats; seats mail only at milestones (ACK, blocker, DONE); the overseer reads subjects first and opens bodies only when needed; research and bulk reading go to a cheap seat (e.g. Codex Spark with `--search`).
- Frugal reading has one exception: verdicts, blockers, questions and DONE mails are always opened in full the moment they arrive. On 2026-09-14 a Codex BLOCK and a seat's report were drained by subject only, and two seats sat idle for ten minutes waiting on the overseer. When a seat looks idle, check the overseer's own unread and skimmed mail first.
- Codex seats do not wake on new mail (observed 2026-09-14: a Codex reviewer sat idle with 4 unread task mails while Claude seats woke through their Monitor watcher). After mailing a Codex seat that is idle, nudge its pane once ("run mail-read <seat> and act on it") and confirm it shows Working; tell Codex seats to run mail-check before stopping after each unit.
- Token-efficiency reasoning, adopted practices and rejected options: [TOKEN_EFFICIENCY.md](TOKEN_EFFICIENCY.md).
- No automatic closing (Ramesh, 2026-09-14): only the main agent (overseer) closes seats, after checking the handoff. Seats never close themselves and no script closes seats. The overseer runs `agentmail/bin/fleet-guard` as a persistent Monitor; it is ALERT-ONLY (IDLE, CODEX-UNREAD, OVERSEER-UNREAD, GONE lines) so a finished or waiting seat cannot be forgotten. On each alert the overseer acts the same turn: assign work, nudge, or close the seat itself.
- A blocked seat looks busy (Ramesh, 2026-09-14: "one is blocked and you didn't know"): a seat's `flutter test` hung on a macOS Gatekeeper dialog ("flutter_tester is an app downloaded from the internet") while its pane still showed a spinner, so an idle-only check missed it. fleet-guard now also alerts STUCK (screen unchanged for 8 minutes while "working"), PROMPT (question or permission prompt text in a pane) and MACOS-DIALOG (CoreServicesUIAgent up). Root cause removed the same day: `xattr -dr com.apple.quarantine /opt/homebrew/share/flutter/bin/cache`. Re-run it after any Flutter upgrade or cache re-download, before seats run flutter test.
- Before closing a seat, record evidence that it is finished, not busy: its DONE/verdict mail is in, the bottom status line of its pane is past tense ("Worked for", "done") with an empty input, no "esc to interrupt"/"Working (" in the last lines, and no child command running. Report that evidence to the operator when closing. fleet-guard reads only the bottom status lines, because old "Working (" lines stay visible higher up in a Codex transcript.
- Closing the LAST seat in the shared grid window destroys that window and the operator's Terminal view jumps to another window (2026-09-14). Before closing the last pane, first launch or join the next seat into the grid, or re-create circle:circle-agents immediately afterwards and `tmux select-window` it; then re-verify `tmux list-clients` shows the grid window.

## 20. A watcher that expires is a seat that is deaf, and an alarm that matches the wrong name is no alarm

Two failures on 2026-09-16, found while one security-audit seat sat blocked for many minutes and nothing raised an alert. Ramesh noticed it by looking at the screen.

**Seat watchers expire.** A Claude seat arms its mail watcher as a Monitor, and a Monitor has a hard 30-minute lifetime. When it expires the seat is told once and must re-arm it. The audit seat did not, so it never saw the overseer's STOP mail, finished its turn, and asked "tell me whether to continue" in its own pane, where nobody reads.
Every seat's boot instruction and task mail must say: re-arm the watcher every time it expires, for the whole run, and never end a turn with a question in the pane. The overseer applies the same rule to its own watcher and fleet-guard.
When a seat seems to ignore mail, check its unread count first (`ls .agent-mail/<seat>/new | wc -l`); a non-zero count on an idle seat means its watcher died. A one-line pane nudge telling it to run `mail-read` is the recovery.

**fleet-guard was blind to almost every seat.** Claude Code retitles its pane with a status glyph (`✳ <seat>`, or a spinner while working). fleet-guard matched the raw pane title against the maildir name, found no directory called `✳ skyzai-...`, and silently skipped the seat, so IDLE, STUCK and PROMPT never fired for it. Seats whose title the overseer had set by hand still matched, which made the guard look healthy. Fixed the same day: the title is stripped of any leading non-alphanumeric prefix before matching, and the prompt patterns now include Claude Code's selection dialogs ("enter to select", "model switch", "safeguards flagged") - a lesson first written down on 2026-09-15 and never implemented.
Verified against the live panes: before the fix the audit seat was not watched; after it, it is. This is rule 15 again - a check that reports the same thing whether or not the subject failed is not a check. Test a guard by making it see a known-bad pane.

**Opus 5 on security work, again.** A full security audit on Opus 5 was stopped by the "Model switch" safeguard dialog, exactly as a security-testing seat was on 2026-09-15, and despite the handoff saying to use Sonnet. Security audits, pen tests and exploit reproduction run on Sonnet. The overseer does not answer that dialog: its first option changes a global setting for every session, which is the operator's decision. Dismiss it with Esc (no switch, no setting change), have the seat persist its state to disk by mail, then move the work to a Sonnet seat that resumes from that state.

**EnterWorktree prompts a human.** A verifier seat called Claude Code's built-in EnterWorktree tool, which asks for approval to relocate the session's permission root to a model-supplied path. Nobody answers a seat's pane, so it blocked. The repaired fleet-guard raised PROMPT within seconds - the first time it caught a stall before the operator did. The overseer declined it (Esc; it does not approve permission grants on another agent's behalf). Seats use `treehouse get --lease`, then read the worktree by absolute path and run commands as `cd <worktree> && ...` inside one Bash call; they never call EnterWorktree. Say so in every task that involves a worktree.

**Prompt detection reads the bottom of the pane only.** The first version scanned the whole screen and raised PROMPT when an agent was editing code containing "approve this". A real dialog always renders just above the status line, so fleet-guard now checks the last 16 non-empty lines. Tested against the two real dialogs from 2026-09-16 (Opus model-switch, EnterWorktree) and the false-positive diff: both dialogs still caught, the diff ignored.

**A thinking seat is not an idle seat.** During a long "still thinking" phase Claude Code hides the "esc to interrupt" hint but keeps a present-tense spinner line ("✻ Choreographing… (5m 34s"), so fleet-guard called a busy reviewer IDLE. It now also treats a word ending in "…" followed by an elapsed-time bracket as working; a finished turn reads "Churned for 17s" and is still idle. Tested against both spinner styles and a finished turn.

*Revision: rule 20 added 2026-09-16.*

- 2026-09-17: two workers told "no sub-agents" spawned forks anyway and sat idle waiting on them. `agentmail-launch` now also disallows the `Agent` tool for every non-overseer seat; a seat that genuinely needs sub-agents (e.g. the security-audit skill) sets `"allow_subagents": true` in roster.json.

## 21. One task per seat, and the task id is the test

Ramesh, 2026-09-21: "why are u asing the same subagent to do things? that might cause context problems i guess. please dont do that.. one task to one agent only. make sure of that."

A seat receives exactly ONE task id in its lifetime.
When that unit is finished, the seat is closed (rule 19's close-when-done), and any further work goes to a freshly launched seat.
Sending a second task id to a live seat is the violation, and it stays a violation when the seat is idle, when the new work is adjacent to the old, and when relaunching feels wasteful.

**Why this is not merely tidiness.** A seat that has already completed one task carries that task's entire context forward: every file it read, every wrong turn it took, every assumption it formed.
That context is re-sent on every wake, so it is a standing token cost, and worse it is a correctness risk, because the seat reasons about task B through task A's assumptions and does not know it is doing so.
A fresh seat reads the new task cold, which is the whole point of dispatching by mail with a self-contained brief.

**What is the same task and is allowed.** A correction ("you got this wrong, redo it"), an unblock ("I built it for you, continue"), a boundary reminder, or a continuation ("now run the AFTER") of the task the seat already holds.
The test is mechanical: if the work needs a NEW task id, it needs a NEW seat. If it is still the same task id, mail the seat.

**The incident.** On 2026-09-21 the overseer broke this twice in one session.
`skyzai-security-fix-0919-ramesh` was given `resume-secfix-0921-x9r4` and then, once it reported DONE, `run-secfix-0921-t3m8`.
`skyzai-apu-device-0921-ramesh` was given `device-0921-r8v2` and then `redfix-0921-m2k9`.
Both times the second task was sent because the seat was already alive and warm and relaunching looked like overhead.
That is precisely the reasoning this rule exists to override, and Ramesh caught it from the outside while the overseer did not notice it from the inside.

*Revision: rule 21 added 2026-09-21.*

## 22. Grant the worktree directory, or the seat prompts the human it must never reach

Found 2026-09-23. A Level 3 seat, launched with `--dangerously-skip-permissions` and `--disallowedTools AskUserQuestion`, still put a permission dialog on Ramesh's screen: *"Do you want to make this edit to firebase.json?"*, in a treehouse worktree under `~/.treehouse`.

**Directory access is a separate gate.** `--dangerously-skip-permissions` does not cover it and neither does removing the interactive-question tool, exactly as rule 10's read-block is a separate gate. The seat had no mechanism left except a prompt, and the only thing that can answer one is whoever is looking at the pane. That is the rule 12 stall arriving through a door rule 12 does not watch.

**Why it hid all day.** READS outside the granted directories are fine while `blockReadsOutsideWorkingDirectories` is false. Only the first WRITE trips it. So read-only research seats and seats working in the main checkout were unaffected, and the failure surfaced only when an implementation seat first edited a file inside its own leased worktree.

**The contradiction it exposed.** The standing rule is that seats take isolated treehouse worktrees rather than sharing a checkout ([[treehouse-not-raw-worktree]]). But `agentmail-launch` granted `--add-dir` for the org root and the mail root only, and treehouse worktrees live under `~/.treehouse`, OUTSIDE both. Every seat sent to a worktree was one edit away from prompting the operator.

**Fixed at the launcher**, not per seat: `agentmail-launch` now adds `--add-dir <TREEHOUSE_ROOT or ~/.treehouse>` for every Claude child when that directory exists, with the reasoning in a comment so it is not tidied away later.

**The recovery, when a seat is found blocked on a prompt.** Do NOT answer it; the overseer does not approve permission grants on another agent's behalf (rule 20). Press Esc, terminate the exact runner, revert any stray edit, return the worktree to the pool, fix the cause, then relaunch and re-send the task mail. Restarting the same seat for the same task id is not a rule 21 violation.

**The check that would have caught it:** launch one seat and have it EDIT a file in its worktree before trusting the fleet. A seat that reads successfully proves nothing about whether it can write.

*Revision: rule 22 added 2026-09-23.*

## 23. When the overseer's runtime runs out, hand the seat to the other runtime at once

Ramesh, 2026-10-07: "claude stopped saying it hit the limit, but I HAVE CODEX fully functional, u were supposed to track that and start codex main agent with necessary prompt".
On 2026-10-07 the Claude overseer hit its usage limit mid-build with four work packages in flight.
It wrote a handoff and stopped; the Claude seats stalled with it, and nothing moved for over two hours while the Codex budget sat at 99% unused.
That is the waste rule 19 exists to prevent, applied to the overseer seat itself.

- Track your own runtime. Run `agentmail/bin/fleet-usage` at session start, before each dispatch batch and at least hourly during long runs. At 80% of the 5-hour session window or 90% of the weekly limit, prepare the handover; do not wait for the hard stop.
- On the first usage-limit warning (or at the threshold), in this order: write `conversation-context/NEXT_MAIN_AGENT_HANDOFF_<date>.md` (what is merged, every in-flight seat with branch/SHA/brief path, the next action for each, open decisions, deploy-day items); then start the Codex overseer by EXECUTING `agentmail/bin/overseer-codex.command` in a visible terminal Ramesh watches (rule 13); it runs with on-request approvals so Ramesh can approve the host operations (tmux, ps, git) a supervisor needs - never "never" for the overseer; then tell Ramesh in one line that the seat moved to Codex and where.
- The incoming Codex overseer reads that handoff, re-arms its mail check, relaunches stalled Claude seats' tasks on Codex where they fit (rule 19 task fit; Flutter-on-host work may have to wait for the Claude reset), and keeps the fleet moving.
- The reverse holds too: a Codex overseer near its limit hands back to Claude the same way.
- Only one overseer acts at a time. The outgoing overseer stops dispatching once the handoff is written; if it is still alive after its limit resets, it reads the newer handoff and asks Ramesh which seat continues before acting.

## 24. Never scan the whole disk or home folder

No `find /`, `find ~`, `find /Users/...`, `grep -r` or `du` over `/` or `~`, by the overseer or any seat (Claude or Codex). On macOS a whole-disk walk triggers one privacy dialog per protected folder (Photos, Contacts, Documents, Downloads, ...) on Ramesh's screen. Search only the repo, your treehouse worktree, or `.agent-mail/attachments/<topic>/`. Seats write every artifact (screenshots, logs) under `.agent-mail/attachments/<topic>/` and quote the absolute path in DONE. Claude sessions are also hard-blocked by deny rules in `~/.claude/settings.json`.

*Revision: rule 24 added 2026-10-09.*

## 25. Every agent that drives a device keeps the shared screen map

Ramesh, 2026-10-12: whenever an agent accesses the phone, it records the screens, elements, taps and navigation it sees into a shared map, so the next agent navigates from the map instead of rediscovering it.
The maps live in `/Users/darkness/Work/Aureus/device-maps/` (one file per app, e.g. `skyzai-app.md`); the file's header defines the format.
Read the map before navigating. Record each screen you actually see, where each tap led, and any trap that broke a run.
The map grows only by normal use: never tap around just to fill it.
The overseer puts this rule in every brief that touches a device.

*Revision: rule 25 added 2026-10-12.*

## 26. Sweep open PRs and new branches every session

Ramesh, 2026-10-13: open PRs from other sessions held findings the fleet never saw.
Outside AI sessions had opened 14 PRs on a product repo with real findings, and nobody in the fleet looked at them for months.
At every session start, alongside the mail drain, the overseer runs `gh pr list --state open` and checks new remote branches on every active repo.
New PRs are triaged the same day into merge, rework or close, and every closure carries a comment saying why.
A real finding inside a PR that is closed becomes a fresh fix task against current code; closing the PR never closes the finding.
Template: `.agent-mail/attachments/prtriage-1013/BRIEF.md` and its TRIAGE.md.

*Revision: rule 26 added 2026-10-13.*

## 27. Every merged change ships a change report the human can read without the diff

Ramesh, 2026-10-19: he designs the architecture but no longer writes the code, and after a night of agent work he could not tell what was written, which flows changed, which files and functions were touched, or how a fix was implemented.
The knowledge existed only scattered across DONE mails and reviews.

Every unit of work that changes code ends with a change report, and nothing merges without one.

- **The author writes Part 1 (narrative).** Generate the skeleton with `agentmail/bin/change-report <base> HEAD --repo <worktree> --task <task-id> --out <file>`, then fill every `TODO(author)` section: what and why, the flow step by step (entry point first, real function names), how it is implemented (design choice, what was rejected, known limits), how it was verified (failing test first, suites with counts, what was NOT checked), and deploy/release impact. Codex seats that cannot write the repo deliver it as `attachments/<batch>/<KEY>_CHANGE_REPORT.md` next to their patches and link it in DONE.
- **Part 2 (facts) is generated from git, never hand-written.** Commits, every file changed, functions and classes added/changed/removed, test cases, dependency diffs and sensitive areas (server, rules, payments, keys, config). It is the ground truth: if Part 1 disagrees with it, that is a review finding.
- **The reviewer checks the report against the diff**, not just the code: a flow step that does not exist, an unlisted sensitive area or a missing deploy step is CHANGES-REQUIRED.
- **The overseer refuses to merge** while `change-report --check <file>` reports any `TODO(author)`. On merge it regenerates Part 2 for the exact merged range (`<merge>^1..<merge>`), keeps the author's Part 1, and commits the result in the product repo as `docs/changes/<YYYY-MM-DD>-<task-id>.md` in the same merge, so the record travels with the code.
- **Daily digest.** After a batch or an overnight run, the overseer writes `docs/changes/<YYYY-MM-DD>-DIGEST.md`: one paragraph per merged task in plain language linking its report, plus what is held, what needs the human, and the deploy impact in one list.
- **Test-case ledger.** Any change to user-visible behaviour also updates the product's sheet in `/Users/darkness/Work/Aureus/AUREUS_TEST_CASES.xlsx` (plain-language case, expected result, honest status: PENDING until deployed and seen working).

The overseer puts this rule in every brief that changes code.

*Revision: rule 27 added 2026-10-19.*

## 28. Document a file the first time you touch it, and keep the project map current

Ramesh, 2026-10-19: every file an agent touches should be documented properly the first time, and a graph should show which file links to what, in a tree, updated as agents touch files rather than all at once, so that in the end he has a detailed map of the entire project.

- **First touch documents the file.** When an agent edits a source file that has no header doc comment, it adds one at the top in the same change. Keep it short and true to the code:
  - line 1: one sentence, what this file is for (this line is what the map shows);
  - then: the main classes/functions and what they do; what it depends on (other project files, services, storage, network); who uses it; side effects (writes data, calls the server, sends money, touches keys or hardware).
  - Dart: `///` lines at the very top, followed by `library;`. TS/JS: a leading `/** ... */`. Python: the module docstring.
  Tooling lines (ignore_for_file, eslint, licence banners) are not documentation.
- **Later touches keep it true.** If a change alters what the header says, the header changes in the same commit. A stale header is a review finding.
- **Folders.** A new folder gets a `README.md` whose first line says what the folder holds.
- **Never document in bulk.** Coverage grows only through real work on a file. Do not open files just to add headers.
- **The map.** `agentmail/bin/project-map --repo <repo>` writes `docs/map/PROJECT_MAP.md` (folder tree, each file's purpose or `undocumented`, the files it links to, how many use it, coverage per folder) and `docs/map/graph.json`. The overseer regenerates and commits it on every merge, next to the rule-27 change report.
- **Agent graph.** Where a repo has `graphify-out/`, agents also run `graphify update .` after code changes so `graphify query/path/explain` stay current.
- **Reviewers check it.** A touched file left without a header, or with a header that no longer matches the code, is CHANGES-REQUIRED.

The overseer puts this rule in every brief that changes code.

*Revision: rule 28 added 2026-10-19.*

## 29. Seats submit focused tests to shared warm lanes; the overseer owns builds and full validation

Ramesh, 2026-10-19: cold Flutter compilation and duplicated Node installs in 7-8 seat worktrees exhausted a 16 GB Mac and caused stale-dependency failures.
`agentmail/bin/testlane` keeps a bounded pool of dedicated warm checkouts so seats share compilation and dependency caches.

- **Seats submit focused tests with `testlane run`.**
  Use `testlane run --queue <shared-queue> --repo-dir <seat-worktree> --base <review-base> -- <argv...>` with the smallest explicit test-file list that proves the change.
  The client snapshots tracked changes and nonignored untracked files, including binary files, without writing the seat's index or object store.
  `npm test`, `npm run build` and `npx tsc -p <config>` use `functions/`; other commands default to the repository root, with `--cwd functions` available for Node tests.
  A queue wait expiry leaves the submitted job intact; inspect `testlane status --queue <shared-queue>` before submitting again.
- **The overseer starts and stops the runner outside seat sandboxes.**
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
  Focused Node targets under `functions/.test-build/` are compiled with `tsconfig.test.json` in the same job and lane, sharing the test timeout.
  Those generated targets may be absent in the seat; the runner removes the requested cached output files first and requires the current patch to emit them again.
  This controls command submission; test code and dependency manifests still require review and trust because they and installation hooks execute on the runner host.
- **Seats never build apps** (apk/ipa/web or Gradle) **and never run the full analyzer gate or full suites.**
  The overseer builds the app and runs full validation once per merge.
  When lanes are busy, a brief may permit delivery with unrun checks stated honestly.
  Existing `heavy.sh` remains unchanged during migration; the overseer explicitly announces the switch to the shared queue.
- **Cap concurrent seats at about 5 on this Mac.**
  The overseer checks swap and load before launching, and cleans up only its identified orphaned build processes.
  Queue additional seats and use remote review capacity when available.
- Every brief that touches code carries this rule and the shared queue path.

*Revision: rule 29 added 2026-10-19; updated 2026-10-19 for task testlane-1019 with shared warm runner/client lanes.*
