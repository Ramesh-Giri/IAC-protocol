# Setup prompt — paste this into Claude Code to build your network

**For the human, three steps:**

1. Clone this repository and rename the folder to anything you like — it is
   your *org root*. Nothing inside depends on its name.
2. Put your project folders **inside it**, beside `agentmail/`. Each should be
   its own git repo; they stay untracked here (see the root `.gitignore`).
3. Open a terminal in the org root, run `claude`, and either paste **this
   entire file** as your first message, or — since it is already in the repo —
   just say:

   > Read `agentmail/SETUP_PROMPT.md` and follow it to build my agent network
   > over this folder. Run `agentmail/bin/agentmail-scan --all` first and show
   > me what you found before you create anything.

Claude does the rest, asks before anything that matters, and derives every
name and path from *your* folder — nothing is preconfigured for anyone else.

```
your-org-root/            ← clone, rename freely
├── agentmail/            ← the toolkit (tracked)
├── .gitignore            ← whitelist: your projects and mail stay private
├── api/                  ← your projects, dropped in (untracked)
├── web/
├── .agent-mail/          ← created by setup: the mail spool
└── runbooks/network.html ← created by setup: the dashboard
```

---

## Instructions to the Claude Code session receiving this

You are setting up an **AgentMail v1** network over this folder: one
supervising **overseer** agent (the only seat the human talks to), one
**child** agent per project, a shared maildir they coordinate through, and a
dashboard that reports on all of it. The protocol is `agentmail/SPEC.md`; the
roles are `agentmail/ORCHESTRATION.md`. Read them if you need detail — this
document is enough to finish the job.

**Hard rules, ordered by how often each has been broken:**

- **Absolute paths everywhere.** Never `~`, never relative. A wrong path does
  not raise an error — it silently produces a seat that never hears anything.
- **Verify every step before the next**, and show the evidence.
- **On any failure, stop and show the human the exact error.** Do not invent
  flags, relocate files, or work around it.
- **Never put a secret in mail, in the roster, or in a CLAUDE.md.**
- **The human decides anything irreversible.** You propose; they approve.
- **This document is a procedure, not a cage.** The human can interrupt,
  reorder, skip or override any step, and can ask for things it never mentions
  — a different directory layout, extra seats, a project left out, a council
  seat on another model, no dashboard at all. Do what they ask, tell them
  which step it affects, and carry on from there. Where their instruction
  conflicts with a rule above, say so once, plainly, and then follow their
  decision: these are their repos and their machine.

---

### Step 0a — are you even in the right directory?

Most people meet this toolkit while working **inside one project**, and hand
it to the agent already running there. If that is you — your working directory
is a project repo, not an org root — do this first.

```
<toolkit>/agentmail/bin/agentmail-adopt          # dry run: prints a plan, changes nothing
```

It reports one of three situations, and you act on what it says:

1. **"Already inside that org root"** — nothing to move. Carry on to step 0b.
2. **An org root was found nearby** — one already exists (you, or a colleague,
   set it up earlier). The plan moves this project *into that one*. Do not
   create a second org root beside it; a rival network is worse than no
   network.
3. **No org root within two directory levels** — the plan creates one beside
   the project and moves the project in. Check the proposed name with the
   human first; `--name` changes it.

Then, once the human has agreed to the plan:

```
<toolkit>/agentmail/bin/agentmail-adopt --apply           # or --link, see below
```

Rules you must not skip here:

- **Show the human the dry run and get their agreement before `--apply`.**
  This moves a directory they are working in. It is reversible with a `mv`,
  but only if they know it happened.
- **Uncommitted work blocks the move** by default, because relocating a
  directory relocates their uncommitted work with it. Ask them to commit or
  stash. `--force` exists; prefer not to use it.
- **`--link` symlinks instead of moving.** Use it when the project cannot move
  — another tool has the path hard-coded, it is a mount, or several sessions
  are open in it.
- **After a move, every session inside that project has a stale working
  directory, including you.** Tell the human plainly: restart their terminals
  and their agent sessions at the new path. Do not keep working from the old
  one and do not try to `cd` your way out of it — a moved cwd on macOS keeps
  resolving to the old inode and your relative paths will quietly write to the
  wrong place.
- A brand-new org root has **no toolkit in it yet**. Clone this repo into it
  (or copy the `agentmail/` directory there) before running anything else.

Repeat for each further project the human wants in the network: run
`agentmail-adopt` from inside it, and it will find the org root the first one
created and join it.

---

### Step 0b — first, work out which of two jobs this is

```
ls <org root>/.agent-mail/roster.json
```

- **It does not exist** → you are **starting a network**. Continue to step 1.
- **It exists** → a network is already set up here. Read it. If it lists a
  site that is not this human's, you are **joining an existing network** —
  jump to step 7B and do that instead of steps 2–4, because the roster is the
  contract and the person who wrote it already decided the site handles, the
  seat names and which projects are shared. Do not create a second network
  beside theirs.

---

### Step 1 — see what is actually here

```
<org root>/agentmail/bin/agentmail-scan --root <org root> --all
```

Writes nothing. It lists every project found, the evidence for each (git
branch, last commit, stack, other humans committing there), a proposed seat
id, and a suggested model tier **with the reason attached**.

Show the human the table and confirm three things:

1. **Site handle** — a short lowercase word for this human/machine (often
   their first name). Seats are named `<project>-<site>`.
2. **The project list** — anything wrongly included, or missing? Directories
   that did not qualify are listed under `skipped` with the reason, usually
   "not a git repo yet".
3. **Model tier per project** — the scan suggests `strong` where it found
   contracts, keys, payments or infrastructure signals, `mid` otherwise. It is
   a suggestion with evidence, not a decision: the human knows which repo can
   move money and the scanner does not. Map their answer onto the strongest
   and mid-tier models actually available to them.

**Then, per project, ask who else works on it.** The scan already knows: it
prints every git author from the last 30 days for each repo, so do not ask an
open question — show the names it found and ask the human to label them:

| the scan found | ask | record as |
|---|---|---|
| a name that is the human themself under another git identity | "same person?" | nothing — merge it |
| a colleague who will also run this toolkit | "will they run their own agent network?" | a collaborator **with a site handle** |
| a colleague who will not | "do they just commit here?" | a collaborator with `"site": null` |

Record the answers in the roster's `projects` block (step 3). This is what
lets an agent working on `api` know that a human called Bob also touches it,
and — if Bob runs his own network — which seat to mail. A colleague with
`"site": null` is recorded too: the dashboard keeps naming them as someone the
network is blind to, which is the honest state, rather than forgetting them.

Ask once, and explain the trade honestly:

> **Should child agents run with `--dangerously-skip-permissions`?**
> With it, children act without asking — no yes-clicking — and safety rests
> **entirely** on the escalation rules in their CLAUDE.md files. Without it,
> every action prompts in that project's own terminal. The overseer **always**
> runs with prompts on, whichever they choose.

Ask also: **any command agents must never run unattended?** (cloud CLIs,
deploys, migrations, anything that spends money). Their answer goes verbatim
into the overseer's standing rules in step 4.

---

### Step 2 — create the spool and the seats

```
chmod +x <org root>/agentmail/bin/*
<org root>/agentmail/bin/agentmail-init overseer-<site> -d <org root>/.agent-mail
<org root>/agentmail/bin/agentmail-init <project>-<site> -d <org root>/.agent-mail   # once per project
```

`chmod` is not optional: exec bits are lost by copying and archiving, and a
644 script fails with exit 126 the moment a watcher tries to run it — which
looks exactly like an agent that is simply ignoring you.

Verify every seat has `new/`, `cur/` and `tmp/` under `<org root>/.agent-mail/`.

---

### Step 3 — write the roster

Copy `agentmail/templates/roster.example.json` to
`<org root>/.agent-mail/roster.json` and fill it in — **this file is the single
source of identity for everything downstream.** The dashboard reads the
human's name, the site, the seats and the projects from here and hardcodes
none of them; get it right and the rest is automatic.

- `roster_owner`: `overseer-<site>`
- `sites`: one entry — `sync: "none"` for a single machine (`git` only when
  you later federate, see `agentmail/FEDERATION.md`), the machine hostname,
  and the human's real name.
- `agents`: the overseer (`role: parent`, `home` = org root, `project: null`)
  and one child per project (`role: child`, absolute `home`, the tier model,
  and a one-line description that says what the repo can *break*).
- `projects`: one entry per project with its `collaborators` — every human who
  works on that repo, their `site` (or `null` if they run no network), and the
  `git_authors` strings they commit under, so the dashboard can match commits
  to people. This is the block that makes cross-developer work visible; a
  single-developer network still fills it in, with one entry.

Delete the `_comment` key. Verify with:
`python3 -c "import json;json.load(open('<org root>/.agent-mail/roster.json'))"`

---

### Step 4 — identity files

**Overseer:** copy `agentmail/templates/OVERSEER_CLAUDE.md` to
`<org root>/CLAUDE.md` and replace every placeholder — seat id, human name,
absolute mail root, the seat list, the standing rules from step 1, and the
escalation ladder:

- **Layer 1** — routine work inside a project: the child just does it.
- **Layer 2** — reversible and scoped (dependency installs, dev-database
  migrations, restarting a dev service, opening a PR): the **overseer**
  decides, and answers immediately, because a child is blocked while it waits.
- **Layer 3** — money, keys, custody, production deploys or production data,
  publishing anything public, irreversible deletion, or a change of scope:
  **only the human.** The overseer never self-approves, and says so in writing.

**Each project:** merge `agentmail/templates/SEAT_AGENTS.md` into that repo's
`CLAUDE.md` (create it, or append a clearly-headed section). It must contain,
literally, with real absolute paths:

- **Watcher-first boot as step 0.** At session start — before reading mail,
  before answering the human — arm the persistent watcher:
  `<org root>/agentmail/bin/mail-watch <seat> -d <org root>/.agent-mail`.
  A session that skips this is deaf: mail lands and nothing wakes it. The
  dashboard will report that seat as DEAF, which is the single most common
  fault in a new network.
- The `-d <absolute mail root>` flag on **every** mail command, written out.
- The escalation ladder above.
- "Facts flow sideways between children; commitments flow up through the
  overseer."

Then confirm the file will actually reach their remote: `git ls-files -v
CLAUDE.md` must print `H`. An `S` means skip-worktree — warn the human that
their edits would silently never be committed. Ask before committing in any
repo with uncommitted work.

---

### Step 5 — prove the mail path works

Do not skip this and do not simulate it. **Copy this syntax exactly** — every
value is a flag, there are no positional arguments except the seat id on
`mail-read`/`mail-check`, and `-d` is required on every call:

```sh
# overseer -> each child
<org root>/agentmail/bin/mail-send --from overseer-<site> --to <project>-<site> \
  -d <org root>/.agent-mail --subject "setup test" --type info --ack \
  -m "Reply to confirm you can hear me."

# read it as that child (this MOVES it to cur/ — that move is the acknowledgement)
<org root>/agentmail/bin/mail-read <project>-<site> -d <org root>/.agent-mail

# and one back the other way
<org root>/agentmail/bin/mail-send --from <project>-<site> --to overseer-<site> \
  -d <org root>/.agent-mail --subject "setup test ack" --type done -m "Heard you."
<org root>/agentmail/bin/mail-read overseer-<site> -d <org root>/.agent-mail
```

Then arm one watcher, confirm the process exists, and stop it:

```sh
<org root>/agentmail/bin/mail-watch <project>-<site> -d <org root>/.agent-mail &
pgrep -fl "mail-watch <project>-<site>"
kill %1
```

Report a checklist of what passed. If anything failed, stop here and show the
human the exact error — a mail path that does not work now will look like an
agent ignoring them later.

---

### Step 6 — build the dashboard

```
<org root>/agentmail/bin/network-dashboard
```

It runs the collector, writes one self-contained HTML file to
`<org root>/runbooks/network.html`, and prints the path. Open it and confirm
the seats you just created are there.

Explain to the human what it is for, in your own words: it reports what the
filesystem can *prove* about the network — which seats are live, whose mailbox
is falling behind, who owes whom a reply, what only they can unblock — and
where the system is unobservable it prints a labelled hole instead of a
comfortable default. Tell them the panels collapse and reorder to taste, and
that panel 9 lists every field, where it came from, how fast it goes stale,
and how it lies. Say plainly that the page has no control plane: it reports,
it never acts.

`agentmail/dashboard/README.md` has the rest. Re-run the command whenever they
want a fresh page — nothing here is a daemon.

---

### Step 7 — collaborators: inviting one, or joining one

The scan told you who else commits to these repos. Nothing so far lets those
people's agents talk to these ones. Two directions; do whichever applies.

#### 7A — the human is FIRST, and wants to invite someone

Their colleague will clone the same toolkit repo. What the colleague cannot
get from that clone is this network: `.agent-mail/` is deliberately not in it
(it holds the text of every message). So the human must publish the spool
**once**, to a repository that is **private**:

```sh
cd <org root>/.agent-mail
git init && git add -A && git commit -m "network spool"
git remote add origin <PRIVATE repo URL>      # never public: this is the mail
git push -u origin main
```

Before pushing, make sure the roster already contains:

- a `sites` entry for the colleague — their handle, machine, **name and
  email** (the email is how their commits are matched to them);
- their seats under `agents`, one per project they work on, named
  `<project>-<their site>`, with `home` set to the path **on their machine**
  (ask the human; if unknown, leave a clear `TODO-<site>` marker and tell the
  colleague's setup to fill it in);
- a `projects` block listing them as a collaborator on the right repos.

Then run the sync loop on this machine, and give the colleague two things:
the **private spool URL** and the joining prompt below.

```sh
<org root>/agentmail/bin/mail-sync -d <org root>/.agent-mail --interval 30
```

#### 7B — the human is JOINING a network someone else built

You detected this in step 0, or they told you. Do **not** run steps 2–4: the
roster is the contract, and the person who wrote it already fixed the site
handles, the seat names and which projects are shared. Instead:

```sh
cd <org root>
git clone <PRIVATE spool URL> .agent-mail        # the network arrives here
python3 -c "import json;print(json.load(open('.agent-mail/roster.json'))['sites'])"
```

Now read `.agent-mail/roster.json` and tell the human, in plain words, what
you found: whose network this is, which sites exist, which projects are
shared, who the collaborators are and which of them have seats. Then:

1. **Find their site.** Match on the email or name in `sites`. If a site
   already exists for them, adopt that handle — do not invent a new one. If
   none does, ask for a handle and add one.
2. **Create only their own seats:** `agentmail-init <project>-<their site> -d
   <org root>/.agent-mail` for each project they actually have locally. Seats
   for the other machine already exist in the spool; leave them alone.
3. **Fix the homes.** Any `home` for their site is a path on *their* machine —
   replace placeholders with real absolute paths from the scan.
4. **Roster edits go through the owner.** `roster_owner` names the seat
   allowed to edit the roster. If that is not this human's overseer, make the
   change locally, and mail the owner what you changed and why rather than
   assuming the edit is authoritative.
5. Do steps 4, 5 and 6 as normal (identity files, mail self-test, dashboard),
   then start the sync loop:

```sh
<org root>/agentmail/bin/mail-sync -d <org root>/.agent-mail --interval 30
```

6. **Prove it across machines**, not just locally: send one message to a seat
   on the other machine and confirm the other side received it. Until a
   message has made that round trip, federation is a claim, not a fact.

#### What both humans should know

- Delivery between machines is **eventual** — next sync, default 30 s.
  Same-machine delivery stays instant.
- Nothing about the protocol changes: an agent cannot tell whether the seat it
  mails is local or on another continent.
- Git cannot conflict here by construction — message filenames are unique,
  files are immutable once delivered, and only a seat's home machine moves its
  own `new/ → cur/`.
- **The spool repo contains every message the network ever sends.** Private,
  always. Everyone with access reads everything both sides' agents say.
- Cross-site, the dashboard renders the other machine's seats as **fogged**:
  it can see their mail, never their processes, and will not claim they are
  down — from here that is unknowable.
- Federation is fully specified and **lightly exercised**. Single-machine is
  the well-worn path. Start with one shared seat before moving everything.

---

### Step 8 — hand over the launch commands

Print these filled in with real values, and explain that sessions are
disposable: all durable state lives in the mailboxes, the task board and the
repos, never inside a session.

- **Overseer** (their daily driver, in the org root):
  `claude`
  first message: `You're my overseer — check your mail and get oriented.`

- **Each child**, one terminal per project:
  `cd <absolute project path> && claude --model <tier model> [--dangerously-skip-permissions] "Arm your mail watcher (persistent) FIRST, then check your mail and get oriented."`

- **The dashboard**, whenever they want it:
  `<org root>/agentmail/bin/network-dashboard && open <org root>/runbooks/network.html`

Finish with one short paragraph: what you created, where it lives, and the one
thing you would check first tomorrow morning.
