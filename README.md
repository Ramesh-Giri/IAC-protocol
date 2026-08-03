# Inter-Agent Communication

**A file-based protocol, supervision model and dashboard for running several
AI coding agents — one per repository — as one accountable network.**

Clone this folder, rename it to whatever you want, drop your projects inside,
and paste one file into Claude Code. It reads *your* folder, proposes a
network, asks you what it cannot know, and builds it.

```
your-org-root/            ← this repo, renamed to anything
├── agentmail/            ← the toolkit
├── api/                  ← your projects, dropped in (never tracked here)
├── web/
├── .agent-mail/          ← the mail spool, created by setup
└── runbooks/network.html ← the dashboard, regenerated on demand
```

No broker, no daemon, no database, no service to run. Agents coordinate
through a shared directory; everything durable is a file you can read with
`cat`.

---

## Quick start

```sh
git clone https://github.com/Ramesh-Giri/IAC-protocol my-org && cd my-org
# drop your project folders in, beside agentmail/
claude
```

Then type this as your **first prompt**:

> **Read `agentmail/SETUP_PROMPT.md` and follow it to build my agent network
> over this folder. Run `agentmail/bin/agentmail-scan --all` first and show me
> what you found before you create anything.**

That is the whole setup. The scan is read-only; from there Claude proposes a
roster from *your* folders, asks you the handful of things it cannot know
(site name, model tier per repo, whether children run unattended), then
creates the seats, writes the roster and identity files, proves the mail path
end to end, builds the dashboard, and prints the commands to launch each
agent.

Prefer to see it first? `agentmail/bin/agentmail-scan --all` writes nothing and
tells you what a network over this folder would look like.

**Requirements:** Python 3.9+ and git. macOS or Linux. Claude Code (or any
agent runtime that can run a shell command and watch a file).

---

## What you get

**A supervision tree.** One overseer — the only agent you talk to — and one
child per repository. Facts flow sideways between children; commitments flow
up through the overseer; anything irreversible flows to you.

**Durable message passing.** A maildir per seat: `new/` is unread, moving a
file to `cur/` is the acknowledgement, and that is the whole delivery
guarantee. Sessions are disposable — kill one mid-task and its mail is still
there when it comes back.

**An escalation ladder that is written down.** Layer 1 the agent does; Layer 2
(reversible, scoped) the overseer approves; Layer 3 — money, keys, production,
publishing, irreversible deletion — only you, and the overseer is forbidden
from self-approving.

**A dashboard that refuses to reassure you.** It reports what the filesystem
can prove and prints a labelled hole everywhere else. It will tell you which
seat has gone deaf, whose queue is growing faster than it drains, who owes
whom a reply, whether two agents are deadlocked waiting on each other, and
which humans are committing to your repos with no seat in the network at all.
Values decay as you watch: a page left open overnight shows hollow glyphs by
morning, not last night's confident lamps. See
[`agentmail/dashboard/README.md`](agentmail/dashboard/README.md).

---

## Documentation

| File | What it covers |
|---|---|
| [`agentmail/SETUP_PROMPT.md`](agentmail/SETUP_PROMPT.md) | **paste this into Claude Code** — the whole build, start to finish |
| [`agentmail/README.md`](agentmail/README.md) | the mental model: actors, supervision, why files |
| [`agentmail/SPEC.md`](agentmail/SPEC.md) | the wire protocol — maildir layout, headers, delivery rules |
| [`agentmail/ORCHESTRATION.md`](agentmail/ORCHESTRATION.md) | roles, escalation ladder, model tiers |
| [`agentmail/COUNCIL.md`](agentmail/COUNCIL.md) | advisory seats from other model families |
| [`agentmail/FEDERATION.md`](agentmail/FEDERATION.md) | more than one machine |
| [`agentmail/dashboard/README.md`](agentmail/dashboard/README.md) | what the dashboard promises, and what it cannot show |
| [`agentmail/DESIGN.md`](agentmail/DESIGN.md) | why it is files and not a broker |

Licensed under the [MIT License](LICENSE). Tests run on Linux and macOS,
Python 3.9 and 3.12 — see [`.github/workflows/tests.yml`](.github/workflows/tests.yml).

## Tools

| Command | Does |
|---|---|
| `agentmail/bin/agentmail-scan` | find projects here and propose a roster — read-only |
| `agentmail/bin/agentmail-init` | create a seat's maildir |
| `agentmail/bin/mail-send` | send a message |
| `agentmail/bin/mail-read` | read a seat's mail and mark it acknowledged |
| `agentmail/bin/mail-check` | count what is waiting |
| `agentmail/bin/mail-watch` | wake a session when mail arrives |
| `agentmail/bin/mail-bridge` | run a non-Claude runtime as a seat |
| `agentmail/bin/mail-sync` | replicate the spool between machines |
| `agentmail/bin/network-snapshot` | one JSON document describing the live network |
| `agentmail/bin/network-dashboard` | render that as one self-contained HTML page |

---

## What this repo does and does not carry

The root `.gitignore` is a **whitelist**: everything is ignored, and only the
toolkit is re-admitted. That is deliberate — a blocklist leaks the first
project folder someone forgets to add.

Tracked: `agentmail/`, this README, the `.gitignore`.

Never tracked: your project folders (each is its own repo with its own
remote), `.agent-mail/` (the live spool — it holds the actual bodies of every
message your agents have exchanged), your root `CLAUDE.md` (your name, your
machine, your paths, your rules), `runbooks/` (generated dashboards render
your network's contents), and `overseer-tasks.md` (your task board).

A cloner does not need your mail. They need the shape, and
`agentmail/bin/agentmail-init` builds it in one command.

---

## Safety, honestly

Child agents can be run with `--dangerously-skip-permissions`, and the setup
asks you to choose. With it they act without prompting, and **the only thing
standing between an agent and your production systems is the escalation ladder
written in its `CLAUDE.md`** — a text file, enforced by the model's compliance
with it, not by the operating system. That is a real trust boundary and it is
softer than a sandbox.

If that is not a trade you want to make, answer "no" at setup: every action
then prompts in that project's terminal. The overseer always prompts.

Nothing in this toolkit sends anything anywhere. It has no telemetry, no
network calls, and no cloud dependency: all state is files on your disk, and
the dashboard is generated locally and opened from disk. Your `.agent-mail/`
spool holds the plain text of everything your agents say to each other — the
root `.gitignore` keeps it out of git, and you should keep it out of anywhere
else you would not paste an internal chat log.

## Status and provenance

This came out of running a real five-project network daily, and most of its
rules are scar tissue: the watcher-first boot rule exists because sessions
went silently deaf; absolute paths are mandatory because a relative one fails
without an error; the dashboard alarms on a *growing* queue rather than a deep
one because absolute depth said nothing useful. Where a design choice has a
reason, the file that implements it states the reason.

Expect rough edges in anything federated — the multi-machine path is specified
and only lightly exercised.
