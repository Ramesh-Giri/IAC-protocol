# Design Rationale — choosing the coordination architecture

The problem: N AI coding agents, each owning one repository, possibly on
different machines, **rarely alive at the same time**, need to exchange
tasks, questions, and permission requests — supervised by one user-facing
parent agent. Which classical architecture fits?

## Requirements the winner must satisfy

- **R1 Asynchrony.** Sender and receiver are almost never running
  simultaneously. Anything requiring a live rendezvous is out.
- **R2 Durability.** An agent session dying (context exhaustion, crash,
  laptop lid) must lose zero messages.
- **R3 Auditability.** The user must be able to read every message with
  `cat`, and history must be archivable in git.
- **R4 Zero infrastructure.** No daemon that can be down, no service to
  operate, no cloud dependency.
- **R5 Supervision.** A privileged parent assigns work, gates dangerous
  actions, and reports to the user; children are autonomous but unprivileged.
- **R6 Concurrency safety.** Simultaneous sends/reads must not corrupt.

## The candidates

### Client–server (RPC)
Children call a parent server (or each other) and get responses.
**Fails R1/R4**: both ends must be alive at call time, and someone must run
the server. Request/response is still a *useful conversation shape* — we
keep it as `question`→answer and `escalation`→`approve|deny` message pairs —
but as an *architecture* it assumes liveness we don't have.

### Microkernel OS
A minimal trusted core doing only IPC; everything risky in unprivileged
user-space servers. The *philosophy* survives here — our "kernel" is a
directory plus atomic `rename()`, deliberately too small to fail — but the
analogy breaks on mechanics: microkernel IPC is synchronous port-based
rendezvous between *live* processes (R1 again), and there's no notion of a
supervising process hierarchy (R5).

### Message broker / pub-sub (Redis Streams, NATS, MQTT)
Durable queues, acks, consumer groups — semantically a great match.
**Fails R3/R4**: messages live inside a service, unreadable without tooling,
and the broker is a new single point of failure that someone must operate.
(For agents already sharing a production Redis, this also couples dev
coordination to prod infrastructure — a bad trade.)

### Blackboard
All agents read/write one shared knowledge structure and react
opportunistically. Great for *shared world-state*, wrong for *directed
communication*: no addressing, no ack semantics, and every agent must scan
everything (the failure mode our v0 single-file inboxes actually exhibited).
Its legacy here: artifacts are shared and inspectable, not hidden in
channels.

### Tuple spaces (Linda)
Elegant associative decoupling in space and time — satisfies R1/R2 — but
pattern-matched anonymous tuples defeat R3 (auditability of *who told whom
what*) and supervision needs explicit addressing anyway.

### Actor model + supervision trees (Erlang/OTP) — **chosen**
Isolated actors, no shared memory, each with a private mailbox; all
communication is async message passing; supervisors own workers' lifecycles
and restart policy ("let it crash").

| Requirement | How actors satisfy it |
|---|---|
| R1 | Mailboxes decouple send-time from read-time completely |
| R2 | The mailbox, not the actor, is the durable unit — an actor death loses nothing queued |
| R3 | Mailbox = directory of Markdown files (our implementation choice) |
| R4 | Filesystem is the only runtime |
| R5 | Supervision trees are *native* to the model — exactly the parent/child hierarchy |
| R6 | One-file-per-message + atomic rename; no shared mutable state exists |

The mapping is unusually literal: agents already ARE isolated
(separate repos, separate contexts, no shared memory), already fail
routinely, and already need a supervisor. We implement actor mailboxes with
**Maildir** (qmail, 1995) because it is the battle-proven way to build a
lock-free, crash-safe, concurrent mailbox out of nothing but directories.

## What we deliberately do NOT build

- **Synchronous calls** — nothing blocks awaiting a reply; agents poll their
  inbox at turn start and may run watchers for wake-ups. A "call" is two
  correlated async messages (`thread` field).
- **Delivery infrastructure** — no retries, no dedup service, no ordering
  guarantees beyond filename sort. The filesystem either renamed the file or
  it didn't.
- **Cross-machine transport** — out of scope for the protocol. If agents
  span machines, sync `.agent-mail/` with any file-sync tool (Syncthing,
  rsync, a shared mount); Maildir's design survives sync conflicts by
  construction (unique filenames, immutable files).

## Failure modes, v0 vs v1

| Failure | v0 (single append-file + `tail -F`) | v1 (Maildir actors) |
|---|---|---|
| File rewritten in place | Watcher replays entire history | Impossible — messages are immutable files |
| Watcher restart | Re-announces everything ever sent | Sees only `new/`; replay structurally impossible |
| Two agents send at once | Interleaved/corrupted appends | Two independent files; safe |
| Reader crashes mid-read | Read-marker ambiguity | File still in `new/`; re-read next turn |
| Inbox growth | One 400 KB file, unreadable in one pass | Read mail moves to `cur/`, archived per-thread |
