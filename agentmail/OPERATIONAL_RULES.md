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

---

*A recurring meta-lesson behind several of these: a guard or field that reads **prose** instead of **behaviour** — a check that passes because a name appears in a docstring, a column that cannot change while claiming to track a changing thing — is worse than none, because it ships as evidence. Test a guard by trying to break it; if you have not tried, it is not evidence.*

*Revision: first issue, 2026-09-04. Amend by appending a dated revision; do not silently overwrite.*
