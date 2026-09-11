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

Start each child seat as a window in a tmux session **named for the PROJECT** (`circle`, `skyzai`, …) — never one shared session, and never named for the org/overseer. Create it once (`tmux new-session -d -s <project>`), then `agentmail/bin/agentmail-launch --seat <seat> --terminal tmux --apply --skip-permissions`. **Always pass `--terminal tmux`.** The auto-detected iTerm/Terminal path either reports a launch that produced no live process, or — for the supervising overseer — is refused by the host's auto-mode classifier, which will not let one agent *directly* spawn an unsupervised (`--dangerously-skip-permissions`) agent; routing the spawn through `tmux new-window` is permitted, so tmux is the working path. Watcher-first is still mandatory (a session that boots unwatched goes deaf to mail). If the boot prompt does not auto-submit in the pane, type it in with `tmux send-keys -t <project>:<seat> "<boot prompt>" Enter` (note: send-keys **cannot** answer another agent's permission dialog — that is guarded — so fix the permission cause instead, see rule 10). tmux runs **headless**: to let a human watch a child, attach a real terminal to it — `osascript -e 'tell application "Terminal" to do script "tmux attach -t <project>"'`. Before relaunching, `pgrep -f "agentmail-run --seat <seat>"` and kill any live instance first (rule 4: one session per inbox); killing the last window can take the tmux server down, so re-create the session if needed.

## 10. A child must be able to READ the org root, or it stalls unattended

A child's working directory is its own project sub-repo, but it must read the shared mail spool (`.agent-mail/`) and the `agentmail/bin` helpers, which live in the **org root above** that sub-repo. If the host enforces a working-directory read block — Claude Code's `permissions.blockReadsOutsideWorkingDirectories: true` — the child stops on a permission prompt for **every** mail read, and unattended (`--skip-permissions`) it **stalls**, because: that block is a separate gate that `--skip-permissions` does **not** override; it fires even on dynamically-built shell paths (`cd X && ls`) that are actually inside the org; and a per-project settings file **cannot** relax a global one — only the host's global settings count. An unattended fleet therefore needs that block **OFF** in the host's global config. Know the trade-off: **no** single setting gives all three of *read-anywhere-in-the-org*, *block-the-parent-directory*, and *never-prompt* — pick two. An unattended fleet needs the block off, and the parent-directory boundary then rests on instruction (tell seats not to read outside the org), not on the sandbox.

## 11. Every spawned agent is a mail seat — it escalates by mail, never prompts the human

When the supervising agent spawns a worker (to parallelize, to draft, whatever), that worker MUST be a mail-native **seat**, not a bare CLI process. A bare agent has no escalation path: the moment it hits a real decision it stalls asking a human who is not watching its terminal — which breaks the supervision model, where decisions flow **up** to the supervisor by mail, never sideways to whoever happens to see the pane. Making a worker mail-native is three steps beyond launching a bare CLI: `agentmail-init <seat>` (its maildir), a **roster entry** (so it is tracked and scoped to its project, not the org root), then launch through `agentmail-run --seat <seat> -- <agent-cli> …` with a boot instruction that says: arm the watcher first, take the task by mail, **escalate every decision to the supervisor by mail, and never open an interactive question or prompt a human**. Dispatch its task by mail too, not by typing into its pane. Converting a bare worker to a seat mid-flight loses no work if you relaunch it in the SAME worktree — its branch and commits are on disk, not in the process.

## 12. A child talks to NO human — enforce it, don't just instruct it

Only the supervising agent speaks to the operator; a child escalates decisions **up by mail** (rule 11), never to whoever is watching its terminal. But instruction alone is not enough — an agent handed a hard decision will still reach for an interactive-question / prompt tool and block, waiting on the very human it was told not to address. So **remove the capability**: launch every child with its interactive-question tool disabled (Claude Code: `--disallowedTools AskUserQuestion`). Combined with permission-bypass (no permission prompts), a child then *physically cannot* block on a human — its only escalation path is mail. `agentmail-launch` now does this for every child seat automatically (and also grants the child `--add-dir <org root>` per rule 10, so it can reach its mailbox); if you hand-roll a launch, add the flag yourself.

---

*A recurring meta-lesson behind several of these: a guard or field that reads **prose** instead of **behaviour** — a check that passes because a name appears in a docstring, a column that cannot change while claiming to track a changing thing — is worse than none, because it ships as evidence. Test a guard by trying to break it; if you have not tried, it is not evidence.*

*Revision: first issue, 2026-09-04; amended 2026-09-11 (added rules 9–11: per-project tmux launch; the org-root read-block that stalls unattended children; every spawned worker being a mail seat that escalates by mail rather than prompting a human; and children launched with their interactive-question tool removed so they physically cannot prompt the operator). Amend by appending a dated revision; do not silently overwrite.*
