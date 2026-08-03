# Running an Overseer — setup and operations

The overseer concept is defined in ORCHESTRATION.md §1. This page is the
practical guide: standing one up, launching it, feeding it state, and how
the human works with it day to day.

## 1. One-time setup

```bash
# 1. Pick its home: your org root — a directory that is NOT any project repo.
#    The overseer owns coordination, never code; its home enforces that.
cd ~/work/<org>

# 2. Give it identity: copy templates/OVERSEER_CLAUDE.md to ./CLAUDE.md and
#    fill in: seat id, human name, mail root, helper-script path, the seat
#    list, your standing rules (e.g. "no autonomous cloud commands"), and
#    the Layer-2/Layer-3 permission boundaries you want enforced.

# 3. Give it a seat:
agentmail/bin/agentmail-init overseer-<site>     # + add to roster.json,
                                                 #   role: parent
```

## 2. Launching (and relaunching)

```bash
cd ~/work/<org>
claude          # or your runtime of choice — the CLAUDE.md does the rest
```

First prompt — one line is enough:

> **"You're my overseer — check your mail and get oriented."**

Everything else it needs is on disk: its CLAUDE.md says *who it is*, its
inbox says *what's going on*. This is deliberate — an overseer session that
dies is relaunched with the same one-liner and loses nothing, because state
lives in the mailboxes and the task board, never in the session.

On boot it should (per its CLAUDE.md): drain `mail-read overseer-<site>`,
arm `mail-watch overseer-<site>` persistently, read `overseer-tasks.md`,
start any bridges that aren't running (COUNCIL.md), and report status.

## 3. Feeding it state — the handoff pattern

The overseer learns the world **by mail, not by prompt**. Whenever context
must reach it — first boot, a child finishing a big phase, a human decision
made out-of-band — send it a `type: info` handoff message:

```bash
agentmail/bin/mail-send --from <any-seat> --to overseer-<site> \
  --subject "HANDOFF — <topic>" --type info --thread overseer-bootstrap <<'EOF'
<network state · open items with owners · pending human decisions ·
 standing rules worth repeating>
EOF
```

Why mail instead of pasting into its prompt: the handoff becomes part of
the permanent record, survives session death, and reads identically whether
the overseer is booting for the first time or the fifth.

## 4. Its working memory — the task board

`overseer-tasks.md` in its home directory, one line per open item:

```
- api-<site> | receipts follow-up: redline web response shape | waiting | their mail pending
- ALL          | migration acks                                    | 1/4     | v0 archives when done
- <human>      | decide: publish repo name/org                     | waiting |
```

The board is the overseer's own file — children never edit it; they report
by mail and the overseer updates the board. Relaunch = read board + inbox,
fully re-oriented.

## 5. What only the human decides

The overseer will surface these; volunteering them at launch saves a
round-trip:

1. **Bridges on?** — permission to start council bridges (they invoke CLIs).
2. **Model pins** — approve the per-repo tier table (roster + settings).
3. **Anything Layer-3** — money, keys, prod, publishing, irreversible
   deletion, scope changes. It must never self-approve these; a "standing
   yes" from you belongs written into its CLAUDE.md, not assumed.

## 6. Human etiquette — making the tree work

- **Route work through the overseer.** Telling a child directly bypasses
  the task trail; do it only for deliberately hands-on sessions — and
  expect the overseer's board to lag until the child reports by mail.
  Duplicate instructions through both channels is how agents collide.
- **Talk outcomes, not mechanics.** "Get receipts working in the app" is a
  better prompt than a task decomposition — decomposition is its job.
- **Ask for the audit trail when curious** — "show me the council thread",
  "who approved that migration" — it greps the mailboxes; that's what
  they're for.
- **Relaunch freely.** The overseer is stateless by design; killing it
  costs nothing but the current turn.

## 7. Failure modes

| Symptom | Fix |
|---|---|
| Overseer editing repo files | Its CLAUDE.md must forbid it; if it persists, the task should have been dispatched — remind it, and check the task board isn't stale |
| Children idle, board full | Overseer died or watcher dropped — relaunch with the one-liner |
| Human bypassed the tree and agents collided | Reconcile by mail: child reports state, overseer re-baselines the board |
| Two overseer sessions running | Both drain the same inbox — the ack-move race is safe (SPEC §8), but kill one; supervision wants a single mind |
