# Inter-Agent Communication

**A file-based protocol, supervision model and dashboard for running several
AI coding agents — one per repository — as one accountable network.**

IAC also removes the human copy/paste relay between developers' agents:
share research and Markdown, review it in context, agree on product and
technical decisions, then hand scoped work to the appropriate project seats.
Start with [research handoffs](agentmail/HANDOFFS.md).

**IAC 1.1:** safer delivery, bounded bridge retries, seat locks, explicit reply
IDs, local-site configuration, and Claude/Codex launch support. Existing users:
read [the upgrade checklist](agentmail/UPGRADE.md) before replacing live helpers.

## Get started: let your agent do the setup

You choose the workspace name and projects. Your agent handles cloning,
local configuration, agent identities, mail setup and verification.
**No project repository is included or cloned by default.** One or two
projects are enough; add more later.

### Ask your agent to clone and set up IAC

Give your existing coding agent this prompt:

> Clone and set up IAC from https://github.com/Ramesh-Giri/IAC-protocol.
> Read its README and follow agentmail/SETUP_PROMPT.md. Ask me where to put
> the workspace and what to name it before cloning. Then ask which project
> repository URLs I want to set up and whether I am joining an existing team.
> Clone only the projects I select and handle the setup and checks for me.

The agent asks for a parent directory and workspace name, then clones into
that exact destination. `team-workspace`, `my-hub`, and `my-projects` are
only examples, not mandatory names. It must not choose one silently.

### Already cloned IAC yourself?

Keep the directory name you chose. Open your coding agent there and say:

> Set up IAC in this folder. Read agentmail/SETUP_PROMPT.md, ask me for the
> project URLs I want, and handle the setup. Keep this workspace name.

You may clone projects manually before setup, or give their URLs to the
agent and let it clone them. Existing folders are inspected and reused
with your agreement—not overwritten, moved or recloned automatically.

### What the agent does next

1. **Confirms your workspace.** Preserves a manual clone's name; asks for
   name/location before an agent-managed clone. Never overwrites a destination.
2. **Asks what you want locally.** Collects only your selected project URLs
   or existing local paths. It does not clone every project in a team roster.
3. **Asks whether you are joining a team.** For a team, requests the private
   mail-repository URL and your identity/site; otherwise sets up local mail.
   Missing access is reported, never bypassed.
4. **Clones and inspects the selected projects.** Maps them to the team's
   project IDs, follows their development instructions, and requests only
   missing credentials or choices. Does not deploy, push or implement features.
5. **Configures your seats and mail.** Preserves the shared roster, writes
   machine-local paths to ignored `local.json`, and adapts agent instructions
   without publishing your local identity into project code.
6. **Verifies and starts what you authorize.** Tests mail locally, starts
   selected sessions and sync when permitted, and proves a cross-site reply
   for a team join. It reports any missing registration, login or remote reply.

A clone does not execute setup by itself. These are instructions for the
agent handling your **setup request**, not a Git hook or background installer.

### For agents reading this README

When the user requests IAC onboarding, follow
[agentmail/SETUP_PROMPT.md](agentmail/SETUP_PROMPT.md) end to end. Before an
agent-managed clone, ask for workspace name/location if not supplied.
After a manual clone, keep its existing name. Ask for selected project URLs
and join-versus-create intent; then perform the authorized work rather than
returning a checklist of commands for the human to run.

Do not trigger onboarding during a code review, toolkit upgrade or clone-only
request. Do not launch agents when prohibited. Missing credentials, remote
seat approval or a remote reply are real dependencies—not permission to
invent configuration or claim completion.

### Joining your existing team: Sam's example

Sam can give his agent the first prompt above and say, "I'm joining an existing
team." The agent asks for the private mail-repository URL and which project
URLs Sam wants. If he selects only the API project, it clones only that project and
configures his main seat plus his API seat. Web, tooling and other team projects
may remain visible in the roster without being cloned or launched locally.

The team provides access and either pre-registers Sam's site/seats or arranges
roster-owner approval. Sam's agent handles the local work; it does not grant
itself team membership or change product/technical decision ownership.

There are three separate repositories:

| Repository | What cloning it provides |
| --- | --- |
| Public IAC toolkit | Tools, templates and this setup procedure |
| Private team mail | Shared roster and correspondence; no project source by default |
| Each selected project | That project's source, history and development instructions |

The public IAC clone deliberately contains **neither project repositories
nor private team mail**. Mail sync does not clone projects or push their code.
Everyone with access to a shared mail repository can read its correspondence.
Never put credentials in it.

### Already working inside a project?

Tell the agent that project's path. It can configure an external local home
without moving it. If you want to move or link an existing project into a
workspace, `agentmail-adopt` can show a dry-run plan; relocation requires your
explicit agreement. It is not a prerequisite for URL-based onboarding.

If you rename a configured workspace later, update your ignored
`local.json.homes` and local instruction paths, then restart affected
sessions/watchers. Do not replace another developer's paths in the shared
roster or move an active project without checking its working state.

**Requirements:** Python 3.9+, Git, macOS or Linux, and an installed,
authenticated coding-agent CLI. The setup agent checks prerequisites and
helps with missing ones under your machine's permission rules. A human must
complete account sign-in or grant missing repository access.

---

## What you get

**Model tiers per project, and one command to start them.** The roster assigns
a model to each repo — the strongest for anything touching money, keys or
production; a faster one for app and tooling work — and `agentmail-launch`
opens one named terminal per seat with that model, the right working directory,
and the watcher-first boot prompt. Dry run by default, so you can see exactly
which project gets which model, and which sessions can act unattended, on one
screen. The overseer always prompts; the launcher refuses to do otherwise.

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
whom a reply, whether outstanding replies form a possible wait cycle, and
which humans are committing to your repos with no seat in the network at all.
Values decay as you watch: a page left open overnight shows hollow glyphs by
morning, not last night's confident lamps. See
[`agentmail/dashboard/README.md`](agentmail/dashboard/README.md).

---

## Documentation

| File | What it covers |
|---|---|
| [`agentmail/SETUP_PROMPT.md`](agentmail/SETUP_PROMPT.md) | agent-led onboarding: chosen name, selected project URLs, team join and verification |
| [`agentmail/README.md`](agentmail/README.md) | the mental model: actors, supervision, why files |
| [`agentmail/SPEC.md`](agentmail/SPEC.md) | the wire protocol — maildir layout, headers, delivery rules |
| [`agentmail/HANDOFFS.md`](agentmail/HANDOFFS.md) | research/Markdown handoffs and product versus technical authority |
| [`agentmail/UPGRADE.md`](agentmail/UPGRADE.md) | 1.1 rollout, compatibility and recovery |
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
| `agentmail/bin/agentmail-adopt` | move a project you're inside into an org root — dry run by default |
| `agentmail/bin/agentmail-scan` | find projects here and propose a roster — read-only |
| `agentmail/bin/agentmail-launch` | start every seat in a named terminal with its assigned model — dry run by default |
| `agentmail/bin/agentmail-run` | bind one interactive CLI to a seat and hold its local session lock |
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
