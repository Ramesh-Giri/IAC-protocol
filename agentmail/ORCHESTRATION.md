# Orchestration — the supervision tree

How to run a fleet of AI coding agents so that **the user talks to exactly
one agent** and everything else happens autonomously, safely, out of sight.

## 1. Roles

### The parent (supervisor)
- Runs on the **strongest available model** (e.g. `claude-fable-5`) — it does
  the thinking that is expensive to get wrong: decomposition, allocation,
  review, and judgment calls.
- Runs in **normal permission mode** — the user sees and approves its
  actions. It is the single human-facing surface.
- Owns the roster: which agents exist, which repo and model each gets.
- Decomposes user requests into tasks, dispatches them as `task` messages,
  tracks progress, verifies `done` claims, and reports upward in the user's
  language, not the children's.
- Rules on `escalation` requests (§5): approves routine ones itself,
  forwards the consequential ones to the user.

### Children (workers)
- One per repository. A child NEVER edits outside its repo — repo ownership
  is the isolation boundary, like actor state.
- Run **autonomously** (no interactive permission prompts — e.g. Claude
  Code's `--dangerously-skip-permissions` or `--permission-mode
  bypassPermissions`), which is only acceptable because of the guardrails
  in §5. Autonomy without guardrails is negligence.
- Model tier assigned by the parent (§3) via the roster or per-task.
- Report by mail: `ack` on pickup, `progress` at milestones, `blocked` with
  a precise need, `done` with verification evidence (test output, commit
  hash, deployed URL).

## 2. Topology

```
user ⇄ parent               (conversation; permission prompts)
parent ⇄ child              (task / ack / progress / blocked / done / escalation / approve)
child ⇄ child               (peer mail: spec questions, integration hand-offs)
child ⇄ user                (NEVER — everything user-facing goes through the parent)
```

### Peer mail policy: facts flow sideways, commitments flow up

Children talk to each other directly — routing every spec question through
the parent makes it a bottleneck and corrupts technical detail in relay
(telephone-game). But the two channels carry different things:

- **Peer (child ⇄ child), allowed and encouraged:** questions and facts —
  API details, bug reports, test vectors, integration mechanics. Anything
  whose answer is checkable against code.
- **Up the tree, required:** anything that *changes what ships* — interface
  or contract changes, scope, deadlines, spend. Children may discuss these
  sideways, but the outcome arrives at the parent as a **proposal**, never
  a done deal two workers agreed between themselves.

Why this is safe without the parent reading every thread: all peer mail is
durable files the parent can inspect at any time (visibility does not
require being in the loop), and children MUST surface material peer
outcomes in their next `progress` report. The parent audits; it does not
chaperone.

## 3. Model allocation

The parent assigns models per project — and may override per task. The
principle: **pay for judgment, not for typing.**

| Tier | Example model | Assign to |
|---|---|---|
| Frontier | `claude-fable-5` | The parent itself; rare "hard problem" tasks explicitly delegated with a model override |
| Strong | `claude-opus-4-8` | Children owning complex, high-blast-radius repos (payments, contracts, infra) |
| Balanced | `claude-sonnet-5` | Children doing routine feature work in well-tested codebases |
| Fast | `claude-haiku-4-5` | Mechanical bulk work: renames, codemods, doc formatting, test scaffolds |

Rules of thumb:
- Allocation lives in `roster.json` (`model` field); a `task` message MAY
  carry `model: <id>` to override for that task alone.
- Upgrade a child's tier when its `done` reports keep failing the parent's
  verification; downgrade when a repo's work is consistently mechanical.
- The parent SHOULD note allocation changes to the user — it's the user's
  spend.

## 4. Task lifecycle

```
user request
  → parent decomposes into tasks
  → task message per child          (spec, acceptance criteria, model hint)
  → child: ack                      (accepted, optional ETA)
  → child: progress | blocked       (blocked states EXACTLY what is needed)
  → child: done                     (with evidence)
  → parent verifies                 (runs/reads the evidence — never trusts claims)
  → parent reports to user
```

A `task` message MUST contain: objective, acceptance criteria the child can
self-check, boundaries (what NOT to touch), and where to report. Underspec'd
tasks come back as `question` — that's the protocol working, not overhead.

The parent tracks open tasks (its own todo list or `parent/state.md`) and
nags: a child silent past its ETA gets a `question`; a dead session's task
gets re-dispatched — mailboxes survive, so nothing is lost ("let it crash").

## 5. The permission model — autonomy with a spine

Children skip interactive prompts, so safety moves into three layers:

### Layer 1 — hard deny-rules (mechanical, no judgment)
Configured in each child's settings (e.g. Claude Code `settings.json`
permission `deny` rules + hooks). Non-negotiable floor, including at least:

- cloud/infra CLIs: `gcloud`, `aws`, `az`, `kubectl`, `terraform`
- `git push --force`, tag deletion, history rewrites on shared branches
- deletion outside the repo working tree; `rm -rf` on absolute paths
- package publishing (`npm publish`, `pip upload`), app-store submissions
- anything touching wallets, private keys, payment execution, or `.env`
  secret values

A denied action is not a dead end — it's an **escalation trigger**.

### Layer 2 — escalation to the parent (routine judgment)
When a child needs a guarded action, it sends `escalation` with: the exact
command/change, why, blast radius, and rollback plan. The parent MAY
approve on its own authority things that are **reversible and scoped**:
installing a dependency, a schema migration on a dev database, restarting a
dev service, opening a PR.

### Layer 3 — escalation to the user (consequential judgment)
The parent MUST forward to the human, never self-approve:

- anything moving money or touching key custody
- production deploys / prod data changes
- publishing anything public (repos, packages, posts, releases)
- deleting data that cannot be regenerated
- scope changes to what the user actually asked for

The parent's value is exactly here: the user stops being interrupted for
Layer-2 noise and is *only* interrupted for Layer-3 decisions, with the
parent's recommendation attached.

### Audit trail
Every escalation and ruling is mail — durable files. "Who approved the
migration and why" is answerable with `grep`, forever.

## 6. Spawning children

Two patterns, both compatible with the protocol:

- **Persistent sessions** — a long-lived interactive session per repo
  (a terminal tab per project). The human starts them; the parent reaches
  them purely by mail + their inbox watchers.
- **On-demand headless** — the parent (or a cron/hook) launches
  `claude -p "<bootstrap prompt>" --permission-mode bypassPermissions` in
  the target repo when a `task` lands, pointing it at its inbox. Dies when
  done; the mailbox carries anything that arrived meanwhile.

Bootstrap prompt for a child, minimally: agent-id, repo path, "drain your
inbox first", the deny-rules reminder, and "report only by mail".

## 7. The council pattern — cross-model deliberation

For consequential decisions, the overseer MAY convene a **council**:
advisory seats on *deliberately different models/vendors* (e.g. a Claude
overseer consulting Codex and Gemini seats). Different models have
uncorrelated blind spots; a reviewer that shares the proposer's failure
modes is a weak reviewer. A cross-vendor council is monoculture insurance.

Pure convention on existing primitives — no new protocol:

```
convener → each seat:  type: proposal   thread: council-<topic>
                       (question, context links, deadline, quorum rule)
each seat → convener:  type: verdict    same thread
                       (position, reasoning, confidence, best attack)
convener:              synthesizes → decides or escalates to the human
                       with verdicts attached → posts ruling to thread
```

Rules that keep a council healthy:

- **Advises, never decides.** Authority stays on the supervision path
  (overseer → human); a council must not diffuse responsibility.
- **Convene sparingly** — high-blast-radius designs, genuine uncertainty,
  and reviews *of the overseer's own plans* (the one case where an
  independent-vendor reviewer is the only unbiased one available).
- **Quorum is per-question**, declared in the proposal: unanimity for
  security-critical, majority-with-recorded-dissent for the rest.
- **Dissent is preserved** — the thread is the audit trail; a verdict that
  lost the vote is still on file when reality later votes differently.

Council seats are ordinary roster seats (`role: council` as documentation);
any seat can also be mailed ad hoc without convening the full ritual.

## 8. Anti-patterns

- **The parent doing the children's work.** If the parent is editing a
  child's repo, the tree has collapsed; fix the child (better model, better
  task spec) instead.
- **Self-approval loops.** A child asking *itself* whether something is
  safe, or a parent rubber-stamping Layer-3 items "to keep velocity".
- **Chatty status pings.** `progress` at milestones, not heartbeats — every
  message costs attention (and tokens) at the far end.
- **Secrets in mail.** Once in the directory, assume synced and archived.
- **Trusting `done`.** The parent verifies evidence. A child claiming green
  tests is a claim; the parent reading the test output is a fact.
