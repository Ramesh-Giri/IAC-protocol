# AgentMail

**File-based IPC and orchestration for multi-agent AI coding sessions.**

> **Zero-to-running in one paste:** give your Claude Code session
> [SETUP_PROMPT.md](SETUP_PROMPT.md) and it interviews you and builds the
> whole network — seats, roster, identity files, self-test, launch commands.

AgentMail lets multiple AI coding agents (Claude Code sessions or similar),
each owning a different repository, coordinate like processes on an operating
system: durable message passing, live wake-ups, and a supervisor hierarchy —
with nothing but a shared directory. No broker, no daemon, no database.

```
                        ┌──────────┐
              user ───▶ │  PARENT   │  top-tier model, runs WITH permission
                        │  agent    │  prompts — the only agent the user talks to
                        └─────┬────┘
              task / approve / report   (AgentMail messages)
        ┌─────────────┬───────┴──────┬─────────────┐
        ▼             ▼              ▼             ▼
   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │ child A │   │ child B │   │ child C │   │ child D │
   │ repo A  │   │ repo B  │   │ repo C  │   │ repo D  │
   └─────────┘   └─────────┘   └─────────┘   └─────────┘
     autonomous mode, guarded by deny-rules + escalation hooks;
     model tier assigned per project/task by the parent
```

## The mental model: actors with a supervision tree

Several classic coordination architectures were evaluated for this problem
(the full comparison is in [DESIGN.md](DESIGN.md)). The one that fits is the
**actor model with supervision trees** — the architecture Erlang/OTP has run
telecom switches on for 30+ years:

| Actor model (Erlang/OTP) | AgentMail |
|---|---|
| Actor: isolated state, no shared memory | An agent session, owning one repository |
| Per-actor mailbox, async message passing | The agent's maildir (`new/` + `cur/`) |
| Supervisor process | The **parent agent** — top-tier model, user-facing, permission-prompted |
| Worker processes | **Child agents** — autonomous, unprivileged, one per repo |
| "Let it crash" + supervisor restarts | Sessions die freely; mailboxes and in-flight tasks survive; the parent re-dispatches |
| Selective receive | Reading `new/` oldest-first, acting per message `type` |

Why it fits: actors assume **no shared state** (each agent owns its repo —
enforced), **asynchrony** (agents are rarely alive at the same moment), and
**failure as a first-class event** (sessions end constantly; supervision
handles it). Secondary influences: the *microkernel* idea that the trusted
core should be minimal (here: a directory and one atomic `rename()` — too
small to fail interestingly), and the *blackboard* idea that shared,
inspectable artifacts beat opaque channels.

## Why files?

Every classic IPC mechanism was considered. Pipes and sockets need both ends
alive at once — agent sessions start and die constantly. Brokers (Redis,
NATS) add an infrastructure dependency and hide messages inside a service.
A shared directory, used with **Maildir semantics**, gives you:

- **Durability** — messages survive any agent, machine, or session crash.
- **Atomicity** — `rename()` within a filesystem is atomic; a reader never
  sees a half-written message, and concurrent senders can't corrupt anything.
- **Auditability** — every message is a human-readable Markdown file; the
  whole conversation history is `grep`-able and can live in git.
- **Zero infrastructure** — works on a laptop, a shared VM, or a synced
  folder. If you can `mv` a file, you can run AgentMail.

## Layout

```
.agent-mail/
├── roster.json              # who exists, their repo, model tier, capabilities
├── <agent>/                 # one maildir per agent
│   ├── tmp/                 # senders compose here (invisible to readers)
│   ├── new/                 # unread mail — the ONLY thing watchers watch
│   └── cur/                 # read mail (moving new/ → cur/ IS the ack)
├── archive/                 # resolved threads, one file per topic
└── bin/                     # mail-send, mail-check, mail-read, mail-watch
```

## Quickstart

```bash
# one-time setup
./bin/agentmail-init api web bot

# send (composes in tmp/, atomically renames into new/ — never edit in place)
echo "The payments API contract changed, see PR #30." | \
  ./bin/mail-send --from api --to web \
    --subject "Contract change: /api/payments/submit" --ack

# check your inbox (lists new/, full messages, does not ack)
./bin/mail-check web

# read + ack (prints messages, moves them new/ → cur/)
./bin/mail-read web

# live wake-ups (one line per arriving message; safe to restart any time —
# it can never replay history, because read mail isn't in new/)
./bin/mail-watch web
```

## The documents

- **[SPEC.md](SPEC.md)** — the wire protocol: message format, filename
  scheme, atomicity rules, ack semantics, threading, archival. Implement
  this in any language in ~50 lines.
- **[ORCHESTRATION.md](ORCHESTRATION.md)** — the supervisor pattern: parent
  and child roles, per-project model allocation, the permission/escalation
  model that lets children run autonomously *safely*, the peer-mail policy,
  and the task lifecycle message types.
- **[OVERSEER.md](OVERSEER.md)** — running the parent in practice: setup,
  the one-line launch, the handoff-by-mail pattern, the task board, what
  only the human decides, and human etiquette for the tree.
- **[COUNCIL.md](COUNCIL.md)** — cross-model deliberation: setting up
  bridged council seats (Codex, Gemini, …), the convening commands, and the
  standing policy for when a council is (and isn't) convened.
- **[FEDERATION.md](FEDERATION.md)** — one mail network across machines and
  developers, using git as the transport.
- **[DESIGN.md](DESIGN.md)** — why the actor model won over client–server,
  microkernel, brokers, blackboards, and tuple spaces.

## Vendor-neutral by construction

The protocol's only requirements are *reading and writing files*. Any
CLI-based agent can hold a seat in the network — Claude Code, Codex,
Gemini CLI, aider, a cron job, or a human with a text editor. There is no
SDK and nothing to integrate: if it can run `mv`, it can speak AgentMail.
The roster's `model` field is descriptive ("what runs this seat"), not a
protocol concept. The one caveat: the *orchestration* layer's guardrails
(permission hooks, deny-rules, model overrides) are configured per-runtime —
the mail is universal, the leash is vendor-specific.

## Federation across machines

Multiple developers, each with their own supervision tree, form **one mail
network** by making `.agent-mail/` a shared private git repository — see
[FEDERATION.md](FEDERATION.md). Maildir's unique immutable filenames make
git sync conflict-free by construction; a dumb `mail-sync` daemon
(pull–rebase–push on an interval) is the entire transport, and arriving
mail triggers the same local watchers as same-machine mail. Cross-site
etiquette: technical facts flow agent-to-agent; commitments flow
overseer-to-overseer.

## Design lineage

The mailbox layout is [qmail's Maildir](https://cr.yp.to/proto/maildir.html)
(1995), which solved exactly this problem — concurrent lock-free delivery to
a spool — for Unix mail. AgentMail adds a message schema, ack semantics
suited to LLM agents, and the orchestration layer on top.

## License

MIT.
