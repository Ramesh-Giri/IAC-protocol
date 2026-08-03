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

### Step 7 (only if they work with other people) — connect a collaborator

Ask: **does anyone else commit to these repos?** The scan already told you —
it lists every git author from the last 30 days per project. If there are
others, they are invisible to this network: their agents cannot be mailed,
and yours cannot be mailed by them. The dashboard reports them as
`SHROUDED — no seat, no maildir`.

Two honest options; give the human both and let them choose.

**A. Stay single-site (fine, and the default).** Their collaborator's agents
simply are not part of this network. The dashboard keeps naming them under
"humans in these repos with no seat", which is the point: you can see the gap
rather than forget it exists.

**B. Federate.** The collaborator clones the same toolkit repo on their own
machine and runs this same setup with **their own site handle**. Then the two
machines share one `.agent-mail/` **as its own private git repository**:

```sh
# once, on the first machine — the spool becomes its own repo
cd <org root>/.agent-mail
git init && git add -A && git commit -m "network spool"
git remote add origin <private repo URL>     # PRIVATE. This carries every message.
git push -u origin main

# on each machine afterwards, including the collaborator's
cd <their org root> && git clone <private repo URL> .agent-mail

# then, on every machine, one sync loop per machine
<org root>/agentmail/bin/mail-sync -d <org root>/.agent-mail --interval 30
```

Read `agentmail/FEDERATION.md` before doing this and tell the human what it
says plainly:

- Delivery between machines is **eventual**, not instant — it arrives on the
  next sync (default 30 s). Same-machine delivery stays immediate.
- Nothing about the protocol changes. An agent cannot tell whether the seat it
  is mailing is local or on another continent.
- Git cannot conflict here **by construction**: message filenames are unique,
  message files are immutable once delivered, and only a seat's home machine
  moves its own `new/ → cur/`.
- The roster must list **both sites** and all their seats, and only the
  `roster_owner` edits it.
- **That private repo contains the full text of every message the network
  ever sends.** It must not be public, and everyone with access to it can read
  everything both sides' agents say.
- Cross-site, the dashboard shows the other machine's seats as **fogged**: it
  can see their mail, never their processes. It will not claim they are down,
  because from here that is unknowable.

The honest caveat, and say it out loud: federation is fully specified and only
lightly exercised. Single-machine is the well-worn path. If they try it,
suggest starting with one shared seat before moving the whole network.

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
