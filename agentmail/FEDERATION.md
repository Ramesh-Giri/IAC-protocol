# Federation — one mail network across machines and developers

AgentMail's core protocol (SPEC.md) assumes a shared directory. Federation
extends the same network across machines — developer A's agents talking to
developer B's agents — **using git as the transport**, with zero changes to
the message format, the maildir semantics, or any agent's behavior.

## 1. The model

**The entire `.agent-mail/` directory is one private git repository, cloned
on every participating machine.**

```
        alice's machine                      bob's machine
  ┌────────────────────────┐            ┌────────────────────────┐
  │ overseer (parent)      │            │ overseer (parent)      │
  │ api · bot · …          │            │ web · docs · …         │
  │        │ local fs      │            │        │ local fs      │
  │   .agent-mail/  ◀──────┼── git ─────┼──▶ .agent-mail/        │
  │   (clone)  ▲           │  (private  │    (clone)  ▲          │
  │            │           │   remote)  │             │          │
  │        mail-sync       │            │        mail-sync       │
  └────────────────────────┘            └────────────────────────┘
```

- Same-machine delivery stays instant (plain filesystem, no git involved).
- Cross-machine delivery arrives on the next sync cycle.
- Every agent keeps using `mail-send` / `mail-read` / `mail-watch`
  unchanged — an agent cannot even tell whether a peer is local or remote.
- When a pull drops files into an inbox's `new/`, the **existing local
  watcher fires**. The sync daemon doesn't notify anyone; the maildir does.

## 2. Why this cannot conflict

Git merges break on concurrent edits to the same file. The protocol makes
that structurally impossible:

| Property (from SPEC.md) | Consequence for git |
|---|---|
| Message filenames are unique (timestamp + sender + slug + collision suffix) | Two machines never create the same path |
| Message files are immutable after delivery | No edit/edit conflicts, ever |
| Only the inbox **owner** moves `new/ → cur/` | A file's move happens on exactly one machine |
| Only the inbox owner archives its threads | `archive/` writes don't race |

The one rule federation adds: **an agent's inbox is written-into by anyone
but reorganized only on its home machine.** (`roster.json` gets the same
treatment: only the parent designated `roster_owner` edits it.)

`tmp/` is never committed (it's in `.gitignore`) — half-composed mail stays
local by construction.

## 3. The sync daemon — `mail-sync`

One small loop per machine (run it under the overseer session's monitor, or
as a launchd/systemd service):

```
every INTERVAL (default 30 s):
  1. commit any local changes   (new outbound mail, our own new→cur moves)
  2. pull --rebase              (receive remote mail)
  3. push                       (publish ours; on race, pull --rebase again and retry)
```

Design points:

- **Commit-before-pull** so a rebase never touches uncommitted files.
- **Rebase, not merge** — history stays linear; with conflict-free paths
  (§2) a rebase is always clean.
- Push races (both sides pushing in the same window) resolve by one extra
  pull-rebase-push cycle; the daemon retries automatically.
- Interval is a latency/noise trade-off. 30 s feels live in practice;
  federation is for coordination, not chat. (A push-triggered webhook can
  replace polling later without changing anything else.)
- The daemon is dumb on purpose: it moves files, it never reads mail,
  it has no protocol knowledge. All intelligence stays in agents.

## 4. The roster in a federated network

In the common case, **every developer runs the full set of project agents**
against their own clones — the seat space is a matrix (project × site), and
seat ids are namespaced accordingly: `<project>-<site>`.

```json
{
  "version": 1,
  "roster_owner": "overseer-alice",
  "sites": {
    "alice": { "sync": "git", "machine": "alice-mbp" },
    "bob":   { "sync": "git", "machine": "bob-studio" }
  },
  "agents": {
    "overseer-alice": { "role": "parent",  "site": "alice", "project": null,
                        "model": "claude-fable-5" },
    "overseer-bob":   { "role": "parent",  "site": "bob",   "project": null,
                        "model": "claude-fable-5" },
    "backend-alice":  { "role": "child",   "site": "alice", "project": "backend",
                        "model": "claude-opus-4-8" },
    "backend-bob":    { "role": "child",   "site": "bob",   "project": "backend",
                        "model": "claude-opus-4-8" },
    "app-alice":      { "role": "child",   "site": "alice", "project": "app",
                        "model": "claude-sonnet-5" },
    "app-bob":        { "role": "child",   "site": "bob",   "project": "app",
                        "model": "claude-sonnet-5" },
    "codex-alice":    { "role": "council", "site": "alice", "project": null,
                        "model": "gpt-codex" }
  }
}
```

Three channel types follow from the matrix:

- **Supervision is site-local.** Each overseer supervises only its own
  site's children; permission Layer-3 escalates to *that* human. A parent
  never commands another site's child — it asks that site's parent.
- **Same-project, cross-site peers** (`backend-alice` ⇄ `backend-bob`) are
  the busiest channel: two agents on the *same codebase*, different clones,
  coordinating like two human devs on one repo — branch intent ("I'm on the
  payments router, hold off"), migration numbering, contract heads-ups,
  merge sequencing. Facts flow freely here; anything that *changes what
  ships* still goes up through both overseers as a proposal.
- **Overseer ⇄ overseer** carries cross-site commitments: integration
  contracts, priorities, release coordination — then each tasks its own
  children.

"Tell every backend agent" = fan-out to `backend-*` (the sender resolves
recipients from the roster's `project` field).

## 5. Trust and privacy

- The mail repo is **private infrastructure** — a private remote, access =
  membership in the network. Everyone in it can read all mail (by design:
  auditability); do not federate with parties who shouldn't see the traffic.
- The no-secrets rule (SPEC §5) stops being etiquette and becomes critical:
  the transport is now a hosted git remote.
- Message authenticity is by convention (`from:` is unforged only because
  participants are trusted). If that ever stops being acceptable, signed
  commits per machine give attribution for free; per-message signatures can
  be layered later without format changes.

## 6. Adding a developer (the whole point)

```bash
git clone <private-mail-remote> ~/work/.agent-mail
cd ~/work/.agent-mail
../agentmail/bin/agentmail-init overseer-newdev their-project     # new maildirs
# add agents to roster.json (ask the roster owner)
mail-sync &                                                        # daemon up
```

Four steps, no coordination downtime for anyone else — the next sync cycle,
the new inboxes exist everywhere and anyone can mail them.
