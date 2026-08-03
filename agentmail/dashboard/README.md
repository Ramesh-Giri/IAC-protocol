# netdash — the AgentMail network dashboard

Renders a `network-snapshot` document as **one self-contained HTML instrument
panel**: no server, no CDN, no webfont, no network call at view time. Open the
file, mail it, commit it — it works offline and on someone else's laptop.

```sh
agentmail/bin/network-dashboard                    # -> runbooks/network.html
agentmail/bin/network-dashboard --json saved.json  # render a saved snapshot
agentmail/bin/network-dashboard -o /tmp/net.html --hours 12 --quiet
python3 -m netdash --help                          # same CLI, as a module
```

## The one commitment

**The page never asserts more than the filesystem proved at snapshot time.**
Where the system is unobservable it prints a labelled hole instead of a
reassuring default. Everything below is a consequence of that sentence.

- **Three independent slots per seat** — `SESSION` (is a process attributed to
  it), `MAILBOX` (is it listening and current), `WORK` (is it producing) — and
  the composite word is always printed next to the slots that produced it, so a
  wrong composite is self-refuting.
- **Two independent axes** — liveness (colour) × occupancy (shape). A seat can
  be interrupted on a human ruling while its process is dead. *Never started*
  is not *down*; *lost* is not *stopped* — and since nothing here writes an exit
  record, those two are printed together and timestamped rather than guessed
  apart.
- **No borrowed thresholds.** A seat is late by *its own* rhythm: the longest
  gap between its own recent events. Fewer than three events, or a silence
  longer than the whole window it was observed in, and the page refuses to
  judge instead of inventing a deadline.
- **Work is a window delta, never a cumulative counter.** Totals prove a seat
  once existed; deltas prove it did something recently.
- **Everything decays by field class** (see below) — a page left open overnight
  shows hollow glyphs by morning, not last night's confident lamps.
- **Disagreements are never resolved silently.** When two signals conflict, both
  are printed and the conflict is flagged. A wedged session usually looks
  exactly like this.

### Freshness classes

| class | meaning | rendering |
|---|---|---|
| `durable` | a fact about a moment (a message was delivered, a commit exists) | never decays; its age ticks live from its own timestamp |
| `monotone` | can only grow while the page sits open (unread counts, unread age) | rendered as a lower bound — "at least N" |
| `volatile` | process liveness, dirty trees, ahead/behind, composite state | full strength for 5 min, dimmed to 15 min, then forced to the unknown glyph |

### Visibility registers

`REVEALED` observed live here · `FOGGED` last known, stamped "as of T", drawn
dimmer and dashed · `SHROUDED` never observed at all — an outline and the
reason, never a state. Losing sight of something makes it **unknown**, never
**down**. Carrying a last-known value forward as if it were fresh is the
cardinal sin of this panel.

### Seats on another machine

A federated roster contains seats that live on someone else's laptop. Every
local probe — the process table, the watcher, the working directory, CPU, git
— is **silent** about those, and reading that silence as a fault is the one
thing this page must never do. So a remote seat gets:

- liveness `remote`, in its own **REMOTE — FOGGED** bucket, ranked below idle;
- composite `Remote`, never `Dark` and never `Unknown`;
- no CPU probe, no repository checks, no signal disagreements, **no alerts**;
- and no "no watcher, therefore deaf" — its watcher runs on its own machine.

What *is* still observable is its mail, because the spool is synced: a remote
seat with a genuinely old queue still raises the alarm, since queue depth is a
fact about files that arrived here. Fogged does not mean blind.

## Nothing about any particular site is written into this code

Every name — the human, the site, seat ids, projects, the seat-id suffix
stripped from cramped labels, the repository root, the path to the mail
helpers — is discovered at runtime from `roster.json` and from the filesystem.
Clone this tree onto another machine with another roster and the page renders
*that* site. Where the roster names nobody, the page says so rather than
inventing a name. There is no configuration file to edit.

## Layout

```
agentmail/bin/network-dashboard     thin entry point (adds ../dashboard to sys.path)
agentmail/dashboard/
  README.md                         this file
  netdash/
    thresholds.py   every number the page judges by, each with its reason
    util.py         escaping, durations, and the four freshness wrappers
    probes.py       what this tool observes for itself (see below)
    state.py        the state machines — no HTML in this file
    glyphs.py       inline SVG: shape first, colour as a redundant channel
    identity.py     who this network belongs to, read from the roster
    model.py        one pass -> seats, buckets, debts, wait-for graph, alerts
    panels.py       the nine panels, in reading order
    page.py         assembles one self-contained file
    cli.py          argument parsing, atomic write
    static/         dashboard.css, dashboard.js (real files, inlined at build)
  tests/            python3 -m unittest discover -s tests
```

Imports only ever point downwards:
`thresholds → util → probes → state → glyphs → identity → model → panels →
page → cli`.

## What this tool probes for itself

`network-snapshot` answers "what does the mail network look like". It does not
stat `FETCH_HEAD`, it does not sample CPU, and SPEC §2 tells it to ignore
`tmp/`. Those three gaps are where the interesting failures live, so netdash
probes them at page-build time — and every such value carries **its own**
clock, never the snapshot's:

- **last fetch** — `stat <repo>/.git/FETCH_HEAD`. A fresh snapshot does not make
  a four-day-old fetch fresh, so ahead/behind is printed beside the age of the
  fetch it was measured against.
- **CPU now** — two `ps` samples 1.5 s apart. Cumulative CPU cannot tell a
  wedged process from a looping one; a delta can. This is what "spinning" means.
- **mailbox depth history** — the filenames in `<seat>/new/`, which carry SPEC §4
  timestamps. A lower bound on past depth (anything already read left no trace),
  which is why the alarm is on the derivative, not the count.
- **dead letters** — a listing of `<seat>/tmp/`, names and mtimes only, never
  contents. A delivery that died half-written is invisible to every other tool
  in this network; that is exactly why it is counted here.

## Reading it

Panels **collapse when you click their title** and **reorder when you drag the
⠿ handle** (or focus it and press alt with the arrow keys). Your arrangement is
remembered in this browser. On a first visit only the three panels a human is
answerable for are open — waiting, seats, alerts — and the six evidence panels
start shut, which is the difference between a 2,800px page and a 12,600px one.

All of that is **view state only**: theme, order, what is open, column sorting
and the pair-matrix filter. Not one control touches a seat, a maildir, a
repository or a process. There is deliberately no button that sends mail, kills
a session or edits the board — a page that reports on a system should not also
be able to disturb it. Every action it suggests is a command you run yourself.

## Panels

| # | panel | what it answers |
|---|---|---|
| 1 | Waiting on *(the human)* | what only a person can unblock |
| 2 | Seats ranked by who needs *(them)* | who needs attention, in that order — idle collapses |
| 3 | Alerts | derived anomalies and signal disagreements; empty most days |
| 4 | The supervision tree | who reports to whom, fixed roster order |
| 5 | Work per seat | in-flight, last outbound, cadence, session, mailbox, repo |
| 6 | Mail | reply-debt ledger, wait-for graph, dead letters, pair matrix, river |
| 7 | Federation | what is revealed, fogged, and shrouded |
| 8 | History | commits and settled items — all durable, never decays |
| 9 | Provenance | every field → its source → its freshness → how it lies |

## Deliberately absent

Health scores and "N/M healthy" traffic lights · token or cost as a headline
(progress-blind: high usage, zero errors, all green, while an agent loops) ·
volume leaderboards · trend arrows · inbox-zero as an achievement · any
threshold not derived from observed cadence · any control that would imply this
page can act on the network. Every action on the page is selectable text that a
human runs.

The page also states plainly what it *cannot* show: whether a live process is
thinking or wedged, what the human said (prompts are not mail and leave no
file), any other site's seats, archived or off-roster mail, whether a task was
done well, and per-item age on the board.

## Tests

```sh
cd agentmail/dashboard && python3 -m unittest discover -s tests -q
```

41 tests, standard library only. They cover the derivations a human would act
on: the cadence refusals, the mailbox deaf rules, the three liveness states,
occupancy (including "on-cadence is not working" and "spinning needs burn *and*
silence"), the depth derivative, composite precedence, roster-derived identity,
both debt kinds, cycle detection, triage ordering, and the page contract —
balanced tags, self-containment, and "a page is always produced".

## Related tools

- `agentmail/bin/network-snapshot` — the collector. One JSON document
  describing the live network; the dashboard is a rendering of it, and
  `--json` lets you render a saved one.
- `agentmail/bin/agentmail-launch` — starts the seats this page then observes.
  The roster is intent, the running argv is reality, and the dashboard flags
  the two when they disagree.

## Requirements

Python 3.9+, standard library only. `git`, `ps` and `lsof` are used through
`network-snapshot`; when one of them fails the page reports it rather than
guessing around it.
