# IAC / AgentMail protocol

Version 1.1 · file-based transport for trusted collaborators.

The key words MUST, MUST NOT, SHOULD and MAY express protocol requirements.
This version supersedes the 1.0 draft's exactly-once, replay-proof and
conflict-free claims. The transport is not an operating-system sandbox.

## 1. Layout and identity

```
.agent-mail/
├── roster.json               # shared seats, sites, projects and delegation
├── local.json                # optional LOCAL site/home overrides; never commit
├── .locks/                   # LOCAL process locks; never commit
├── <seat>/
│   ├── tmp/                  # LOCAL composition and bridge retry receipts
│   ├── new/                  # delivered, not acknowledged
│   └── cur/                  # acknowledged; not necessarily completed
└── archive/                  # optional human-managed history
```

Seat IDs MUST match `[a-z0-9][a-z0-9_-]*` and appear in `roster.agents`.
Both sender and recipient MUST be registered. Maildir subdirectories MUST
share a filesystem supporting hard links and advisory file locks.
The bundled implementation supports Python 3.9+ on macOS/Linux.
Install the whole `agentmail/` directory: `bin/` imports `lib/iac.py`.

An inbox MUST be consumed only on its home site. Locks prevent cooperating
processes on ONE machine from racing; they are not distributed leases.
A seat is a stable identity, not a model or a temporary process.
Use distinct seats/worktrees for concurrent workers on the same project.

## 2. Delivery and acknowledgement

Each send gets a UUID and a filename:
`<UTC timestamp>-<sender>-<subject slug>--<UUID>.md`.

The sender writes the complete file in the recipient's `tmp/`, flushes it,
then atomically links it into `new/` without overwriting existing files.
It removes the temporary link afterward. Delivered files MUST be immutable.
The filename timestamp is useful for sorting, not identity or causal order.

Reading with `mail-check` does not acknowledge. `mail-read` prints and
flushes output before linking the unchanged message into `cur/` and
removing the `new/` link. A conflicting existing `cur/` file is an error,
never an overwrite. A crash between these steps can leave two links or
cause a repeated read. Consumers MUST tolerate retries.

**Acknowledged does not mean acted on, approved, or completed.** An agent
that acknowledges before working MUST recover its outstanding work from
`cur/`, correlated replies and its own task records after a restart.

The implementation coordinates send/read/sync via a transport lock and
consumer processes via a per-seat lock. This protects cooperating helpers,
not arbitrary shell writes. Hardware/filesystem failure and remote sync
are not covered by an unconditional no-loss guarantee.

## 3. Message envelope

Messages are UTF-8 Markdown with flat YAML-style frontmatter. New string
values are JSON-quoted (valid YAML strings); legacy unquoted values remain
readable. Duplicate keys and multi-line header values are rejected.
No YAML tags or executable expressions are evaluated.

```yaml
---
id: "9d432512-8031-4776-8017-dff6c55b50d3"
from: "api-alice"
to: "web-bob"
subject: "Review the revised API contract"
type: "handoff"
sent: "2026-09-05T09:00:00Z"
thread: "api-contract-v2"
expects_reply: "true"
ack: "requested"
project: "api"
intent: "research"
authority: "technical"
---

What changed, why it matters, what you are asking the recipient to do.
```

Required new headers: `id`, `from`, `to`, `subject`, `type`, `sent`.
Optional headers:

| Field | Meaning |
| --- | --- |
| `thread` | Human-readable conversation grouping; not a task identity |
| `in_reply_to` | Exact request ID (legacy filename when no ID exists) |
| `expects_reply` | Explicit true/false; overrides type-based defaults |
| `ack` | Legacy compatibility: requested/none; not proof of completion |
| `project` | Key in `roster.projects` |
| `intent` | research, requirements, proposal, implementation, review, decision |
| `authority` | product, technical, joint: domain concerned, NOT granted permission |
| `supersedes` | Exact earlier message ID replaced by this message |
| `references` | JSON-encoded string containing a list of pinned artifact references |

`mail-send` accepts `--body-file` or stdin for Markdown; neither is executed.
Repeat `--ref shared-repository@FULL_COMMIT:path/to/file.md` for artifacts.
Full commits are 40- or 64-character hexadecimal IDs. Repository identifiers
must be agreed, accessible shared repositories, not sender-only local paths.
The helper validates format; it does not fetch or verify the referenced
artifact. The receiving agent MUST verify repository, commit and path before
relying on it. It MUST report inaccessible references, not invent contents.

## 4. Requests, replies and handoffs

Request types `task`, `question`, `proposal`, `escalation`, `handoff`
and `review` expect a reply by default. Other types, including `info`,
`ack`, `progress`, `blocked`, `done`, `report`, `answer` and
`verdict`, do not. `--request-reply` (alias `--ack`) or `--no-reply`
sets this explicitly.

Reply to the sender with `--in-reply-to REQUEST_ID`, the same thread,
and `--no-reply` unless deliberately opening a new request.
An acknowledgement or progress report does not close an outstanding task.
Request IDs distinguish two tasks on the same thread in the same second.

A handoff SHOULD say: summary, evidence/artifacts, requested action,
constraints and what would constitute a useful response. Research handoffs
normally request assessment, not implementation. See [HANDOFFS.md](HANDOFFS.md).

Supersession is explicit context, not automatic cancellation: the receiver
must reconcile it against work already started and reply with its status.

## 5. Bridge reliability

`mail-bridge SEAT --once -- COMMAND...` invokes a headless command only for
messages that expect a reply. Notifications are acknowledged without invoking
the command. The command receives a prompt on stdin; stdout MUST be only
its final response. Nonzero exit, timeout or empty output is a failure.
Partial stdout from a failed command MUST NOT be sent as an answer.

Failures remain in `new/`. Local receipts in `tmp/bridge-state/` track
bounded attempts (default 3) and backoff; default command timeout is 300s.
After exhaustion, fix the cause and use `--once --retry-failed`.
A successful response is saved before sending; recovery reuses it and a
stable reply UUID, then acknowledges the request. This prevents duplicate
mail in the covered crash window. It does NOT ensure exactly-once model
execution or task side effects: a crash before saving the response may
rerun the command. Tasks MUST be idempotent or check prior effects.

Bridge and interactive runner share a per-seat session lock. Consumers have
a separate lock. Notifications do not trigger reply loops. The bridge's
prompt is advisory: the command's actual sandbox/permissions MUST be set by
the operator. Council commands MUST be configured read-only.

## 6. Federation

`mail-sync` is only for a dedicated mail Git repository whose top-level
directory is the mail root. Embedded product channels require manual,
explicitly scoped Git commits; the helper refuses them before staging.

It whitelists roster, ignore rules, message files and maildir placeholders;
rejects unrelated payload and tracked local state; serializes local transport
while committing, pulling with rebase and pushing. Git subprocesses time out.
An unresolved merge/rebase blocks further automatic work; no force push,
conflict deletion, credential prompting or branch guessing is performed.
Configure the intended upstream before syncing an existing remote.

UUID paths reduce collisions, but roster edits, misuse, shared archiving,
branch divergence and multiple consumers can still conflict. An offline site
has a local copy, not proof of delivery to another developer.
See [FEDERATION.md](FEDERATION.md) and [UPGRADE.md](UPGRADE.md).

## 7. Trust and authority

The roster describes product/technical decision owners and explicit
delegation. It is a shared agreement, not authentication or access control.
`AGENTMAIL_SEAT` binds cooperating sends to the launched seat; a process
with filesystem access can bypass it. Restrict Git membership and operating
system/CLI permissions to the intended collaborators.

Receiving mail, a Markdown attachment, a senior-sounding sender, or an
`authority` header MUST NOT grant new permissions. Research is evidence;
requirements carry product intent; technical implementation requires the
technical owner's delegation. Cross-domain changes require agreement in
both affected domains. Routine work inside existing delegation needs no
new approval ritual.

Never mail secrets. Do not add automatic execution of attached scripts or
instructions. Validate completion using code/test evidence, not a `done`
label. The dashboard's reply ledger is bounded by visible mail history;
a reply cycle is a possible wait cycle, not proof of deadlock.
