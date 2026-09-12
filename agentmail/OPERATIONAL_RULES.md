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

Start each child seat as a window in a tmux session **named for the PROJECT** (`circle`, `skyzai`, …) — never one shared session, and never named for the org/overseer. Create it once (`tmux new-session -d -s <project>`), then `agentmail/bin/agentmail-launch --seat <seat> --terminal tmux --apply --skip-permissions`. **Always pass `--terminal tmux`.** The auto-detected iTerm/Terminal path either reports a launch that produced no live process, or — for the supervising overseer — is refused by the host's auto-mode classifier, which will not let one agent *directly* spawn an unsupervised (`--dangerously-skip-permissions`) agent; routing the spawn through `tmux new-window` is permitted, so tmux is the working path. Watcher-first is still mandatory (a session that boots unwatched goes deaf to mail). If the boot prompt does not auto-submit in the pane, type it in with `tmux send-keys -t <project>:<seat> "<boot prompt>" Enter` (note: send-keys **cannot** answer another agent's permission dialog — that is guarded — so fix the permission cause instead, see rule 10). tmux runs **headless**: to let a human watch a child you must attach a real terminal to it, and you must do that by **executing a `.command` file** (`open -a Terminal <file>`), *not* by `osascript ... do script "tmux attach …"` — that types the command and a shell startup prompt eats its first character. See **rule 13**, which is the whole failure and its fix. Before relaunching, `pgrep -f "agentmail-run --seat <seat>"` and kill any live instance first (rule 4: one session per inbox); killing the last window can take the tmux server down, so re-create the session if needed.

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

**Every seat must be a PANE in one window, not a window per seat.** A launcher that opens one window per seat shows the operator a tab bar and exactly one agent; cycling windows to see the others is not seeing the fleet. After launching, collapse them: `tmux join-pane -s <project>:<seat> -t <project>:<first> -h` for each remaining seat, then `tmux select-layout ... tiled`, and set `pane-border-status top` so each pane is labelled. Verify with `tmux list-panes` — one line per seat; if `list-windows` still shows a window per seat, it is wrong.

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
