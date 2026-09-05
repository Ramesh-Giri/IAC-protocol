# Federation — one mail network across machines and developers

For the agent-led **solo → team → share your fork** workflow, start with
[TEAM_SETUP.md](TEAM_SETUP.md). New setups keep local `.agent-mail/` separate
from private shared `.team-mail/`, with an optional `iac-team.json` connection
descriptor in the fork. The examples below describe the original single
shared-spool model using `.agent-mail/`; the same transport works at
`.team-mail/` with explicit `-d` arguments. Preserve existing deployments.
Two roots do not bridge automatically: one main session reviews and relays
approved handoffs. Run sync only on the chosen shared root.

For 1.1 rollout and recovery, read [UPGRADE.md](UPGRADE.md). Automated sync
requires a **dedicated mail-only Git repository**, not a directory nested
inside a product repository. Keep the toolkit outside that repository.
Each machine sets its ignored `local.json.site` and optional local `homes`;
the shared roster owner does not identify the current machine.

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

## 2. Why ordinary conflicts are uncommon, not impossible

Git merges break on concurrent edits to the same file. The protocol makes
ordinary message collisions unlikely:

| Property (from SPEC.md) | Consequence for git |
|---|---|
| Message filenames include a UUID | Independent sends do not normally collide |
| Message files are immutable after delivery | Cooperating senders avoid edit/edit conflicts |
| Only the inbox **owner** moves `new/ → cur/` | A file's move happens on exactly one machine |
| Only the inbox owner archives its threads | `archive/` writes don't race |

The one rule federation adds: **an agent's inbox is written-into by anyone
but reorganized only on its home machine.** (`roster.json` gets the same
treatment: only the parent designated `roster_owner` edits it.)

`tmp/` is never committed (it's in `.gitignore`) — half-composed mail stays
local by construction.

Roster edits, archiving, divergent history or consuming the same inbox on
multiple sites can still conflict. Local locks are not distributed leases.
On an unresolved Git operation, sync stops making changes until a person
resolves it. It never force-pushes, deletes conflicts, or rewrites branches
to manufacture success. A successful local send does not prove remote delivery.

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
- **Rebase, not merge** — history stays linear when reconciliation succeeds;
  conflicts require explicit resolution.
- Push races (both sides pushing in the same window) resolve by one extra
  pull-rebase-push cycle; the daemon retries automatically.
- Interval is a latency/noise trade-off. 30 s feels live in practice;
  federation is for coordination, not chat. (A push-triggered webhook can
  replace polling later without changing anything else.)
- The loop validates a mail-only payload and excludes machine-local state.
  It does not execute message contents. Git commands have bounded timeouts.

## 4. The roster in a federated network

Each developer clones **only the projects they choose to work on** and runs
only their selected local seats. One or two projects are enough. The shared
roster may describe more projects and seats without installing their code or
starting them locally. Seat IDs are namespaced as `<project>-<site>`;
the project-by-site mapping need not have every possible combination.

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

### A fresh shared channel is a valid starting point

You do not need to import old correspondence to start collaborating. For a
new team channel, use one **private, mail-only repository**, cloned into each
workspace's `.team-mail/` when preserving separate local mail. Start with the
approved roster, empty maildirs, and a short current-context handoff.
Old personal mail can stay private and
local; copy selected historical material only after an explicit review.

An ordinary local folder is sufficient for agents on one machine, but does
not synchronize to another developer's computer. Independent fresh folders
on two computers are two disconnected networks, not a shared channel.

Keep project code in its own repositories, and machine paths/credentials out
of shared mail. The mail repository holds the roster plus messages and
optional approved archives; it needs no application source. Creating or
publishing that private repository still requires the team's authorization.
If existing mail must be retained, back it up and agree on a migration path;
do not reset, clear or overwrite the current spool to obtain a fresh channel.

### Agent-led onboarding

Use the agent-led [setup procedure](SETUP_PROMPT.md), not a fresh network
template. The new developer asks their agent to clone and set up IAC. It asks
for the workspace name/location before cloning, or preserves the name of an
existing manual clone. Next it collects the selected project URLs or local
paths and checks `iac-team.json` for the private team-mail URL before asking
for missing information. It clones only that selected code and
joins the shared mail repository.

The inviter grants access and arranges roster-owner-approved registration:
one site, a main seat, selected project seats and their delegation. If an
unregistered developer has no valid sender seat, the agent reports exactly
what the inviter must register; it cannot bootstrap membership by pretending
to be another seat. A registered main can request further seats by mail.
Unapproved roster edits must not be left for automatic sync to publish.

The setup agent verifies the shared identities, writes ignored `local.json`
for this machine's site/homes, adapts local instructions, tests mail and
starts only authorized selected sessions plus one mail sync loop. It proves
a correlated cross-machine reply before reporting team communication ready.
Missing access, registration or an offline remote site is reported explicitly.

Cloning the public toolkit does not grant team access or download project
repositories. Mail synchronization transports messages and roster changes,
not project code. Each selected project retains its own remote and ordinary
branch/review/push workflow.
