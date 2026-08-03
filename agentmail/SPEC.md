# AgentMail Protocol Specification

**Version 1.0-draft** · Status: pre-release

The key words MUST, MUST NOT, SHOULD, MAY are used as in RFC 2119.

## 1. Overview

AgentMail is a durable message-passing protocol between AI agents using a
shared directory as the transport ("the kernel"). It guarantees:

1. **Atomic delivery** — a reader never observes a partial message.
2. **Exactly-once read semantics** — a message is unread or read, never
   ambiguous, with no counters or markers to maintain.
3. **Replay-proof watching** — a live watcher can be started, killed, and
   restarted at any moment and can never re-announce old mail.
4. **Crash survival** — no state is lost when any agent, watcher, or the
   whole machine dies.

All four follow from one rule: **a message is one immutable file, and its
lifecycle is expressed only by which directory it is in.**

## 2. Directory layout

```
.agent-mail/
├── roster.json
├── <agent-id>/
│   ├── tmp/        # compose area — readers MUST ignore this directory
│   ├── new/        # delivered, unread
│   └── cur/        # read (acknowledged)
├── archive/
└── bin/
```

- `<agent-id>` MUST match `[a-z0-9_-]+` and appear in `roster.json`.
- All three subdirectories MUST be on the same filesystem (rename atomicity).
- The layout is per-agent **inbox only**. There are no outboxes; sending is
  writing into the recipient's maildir.

## 3. Message lifecycle

### 3.1 Send

1. Sender composes the complete message file in the **recipient's** `tmp/`
   under a unique name (§4).
2. Sender atomically moves it: `rename(tmp/NAME, new/NAME)`.

The sender MUST NOT write directly into `new/`, MUST NOT modify any file
after the rename, and MUST NOT edit or delete another agent's mail. A
crashed send leaves at worst a stale file in `tmp/`, which is invisible to
readers; files in `tmp/` older than 24h MAY be garbage-collected by anyone.

### 3.2 Read + acknowledge

A recipient reads a message from `new/` and acknowledges it by atomically
moving it to `cur/`, unchanged. The move IS the ack — there are no read
markers, and message files are never edited. An agent that wants to note
*what it did* about a message records that in its reply or its own logs,
never inside the received file.

Recipients SHOULD drain `new/` (oldest first — filenames sort
chronologically) at the start of every working turn, in addition to any
live watcher.

### 3.3 Reply

A reply is a normal send in the opposite direction carrying the same
`thread` value (§5). Reply-to-sender, not reply-into-your-own-inbox.

### 3.4 Archive

When a thread is resolved (both sides consider it closed), either party MAY
concatenate the thread's messages from `cur/` into
`archive/<YYYY-MM-DD>-<topic>.md` and delete the originals from `cur/`.
Archival is a courtesy for humans; it has no protocol meaning.

## 4. Filename scheme

```
<utc-timestamp>-<from>-<slug>.md
2026-08-01T05-12-33Z-api-payments-contract-change.md
```

- Timestamp: UTC, ISO 8601 with `:` replaced by `-` (filesystem-safe),
  second precision. If two messages from the same sender would collide,
  the sender MUST suffix `-2`, `-3`, ….
- `<from>`: sender's agent-id.
- `<slug>`: lowercase kebab-case summary, ≤40 chars.

Filenames MUST sort chronologically with plain byte ordering (they do, given
the timestamp prefix). The filename is metadata for humans and sorting; the
authoritative header is inside the file.

## 5. Message format

A message is UTF-8 Markdown with a YAML frontmatter header:

```markdown
---
from: api
to: web
subject: Contract change — /api/payments/submit gains order_id
type: info            # see §6
thread: payments-receipts     # optional; groups a conversation
ack: requested        # requested | none      (etiquette, not enforced)
sent: 2026-08-01T05:12:33Z
---

Body in Markdown. Institutional tone. As short as clarity allows.
```

Required fields: `from`, `to`, `subject`, `sent`. Everything else is
optional; unknown fields MUST be ignored (forward compatibility).

Rules:

- One recipient per message file. "Broadcast" = the sender delivers one
  copy per recipient. (Fan-out is the sender's cost, keeping reads trivial.)
- **No secrets, ever** — no API keys, private keys, tokens, or PII. Public
  artifacts (a public address, a public key, a PR URL) are fine. Assume the
  directory will someday be synced, backed up, or committed.
- Bodies SHOULD stay under ~4 KB. Anything larger belongs in a repo file,
  gist, or PR that the message links to.

## 6. Message types

`type` lets automation route without parsing prose. The core set:

| type | Direction | Meaning |
|---|---|---|
| `info` | any | FYI; no action required |
| `question` | any | Blocking question; answer expected |
| `task` | parent → child | Work assignment (see ORCHESTRATION.md §4) |
| `ack` | child → parent | Task accepted, ETA optional |
| `progress` | child → parent | Milestone / status update |
| `blocked` | child → parent | Cannot proceed; states exactly what is needed |
| `done` | child → parent | Task complete; includes verification evidence |
| `escalation` | child → parent | Permission request for a guarded action (§5 of ORCHESTRATION.md) |
| `approve` / `deny` | parent → child | Ruling on an escalation, quoting the request |
| `proposal` | convener → council seat | Question put to a council (ORCHESTRATION.md §7) |
| `verdict` | council seat → convener | Position + reasoning + confidence + strongest counter-argument |

Implementations MAY add types; unknown types MUST be treated as `info`.

## 7. Watching (live wake-ups)

A watcher monitors **only `new/`** for file-creation events (`inotifywait`
on Linux, `fswatch` on macOS, or a 5–15 s `ls` poll as fallback) and emits
one event per new file.

Because read mail lives in `cur/`, a watcher restarted after any downtime
sees only genuinely-unread messages — replay is structurally impossible.
Watchers MUST NOT be pointed at `cur/`, `tmp/`, or a whole inbox file (the
v0 design's `tail -F` replay bug is exactly what this layout eliminates).

## 8. Concurrency and conflict rules

- Multiple simultaneous senders to one inbox: safe — each writes its own
  file; `rename()` serializes at the filesystem.
- Multiple readers of one inbox (two sessions of the same agent): the
  `new/ → cur/` rename succeeds for exactly one; the loser treats the
  `ENOENT` as "already read elsewhere" and moves on.
- Clock skew between machines affects only sort order, never correctness.

## 9. The roster

`roster.json` is the service directory — the only shared configuration:

```json
{
  "version": 1,
  "agents": {
    "api":  { "role": "child",  "repo": "api-server",
                 "model": "claude-opus-4-8", "description": "Backend + platform" },
    "web":  { "role": "child",  "repo": "web-app",
                 "model": "claude-sonnet-5", "description": "Mobile app + Connect" },
    "parent":  { "role": "parent", "repo": null,
                 "model": "claude-fable-5", "description": "Supervisor; user-facing" }
  }
}
```

Only the parent SHOULD edit the roster (adding agents, changing model
assignments). Children read it to resolve recipients.

## 10. Compatibility note (v0 migration)

The predecessor protocol (single append-only `<agent>-inbox.md` per agent,
`<!-- read: … -->` markers, `tail -F` watchers) is deprecated. During
migration, agents SHOULD read both systems but send only AgentMail v1.
Known v0 failure modes this spec removes: full-file rewrites replaying
history into watchers, marker corruption, interleaved concurrent appends,
unbounded file growth, and watchers announcing all history on start.
