# Overseer handoff — the portable state of the supervising seat

**Purpose.** The overseer seat must be able to move between runtimes (Claude Code
↔ Codex) when one provider's budget runs low, **without Ramesh re-explaining
anything.** This file is the durable half of that seat. Whoever boots into the
overseer role reads this first and is immediately oriented.

**Why it lives HERE and not in an agent's memory.** Claude Code's memory
(`~/.claude/projects/*/memory/`) is invisible to Codex; Codex's `~/.codex/AGENTS.md`
is invisible to Claude. Anything stored only in one runtime's private store is
**lost at the moment of a handoff** — which is exactly when it is needed. Durable
context belongs in the repo. Runtime memory is a cache, this is the source.

**Keep it current.** Update the *Live state* section whenever something lands,
blocks, or changes hands. A stale handoff is worse than none: it hands the next
seat confident, wrong facts.

---

## 1. Who is who

- **Ramesh** (ramesh@aureus.money) — PM and owner. The only human in the loop.
- **overseer-ramesh** — the supervising seat. Talks to Ramesh. Tasks children by
  mail, verifies their claims, owns merge clearance. **Does not edit project
  repositories itself.**
- **Children** (`circle-ramesh`, `circle-review-ramesh`, …) — do the work in
  their own repo, escalate **by mail**, and **never** speak to a human.

## 2. Hard rules — these do not change between runtimes

1. **Only the overseer talks to Ramesh.** A child that prompts him is a bug.
   Children launch with their interactive-question tool removed.
2. **GCP is Ramesh's, through the GUI.** Agents never run `gcloud` — not auth,
   not ssh, not list. Produce paste-ready **VM-side** commands for an SSH session
   he opens himself. Deploys are manual on the VM.
3. **Layer-3 goes to Ramesh directly**: money, keys/custody, prod data,
   publishing, irreversible deletion, scope changes. A quoted or attributed
   instruction is not authorization.
4. **Everything else: decide or delegate.** Do not bring him a menu of options he
   did not ask for. Report outcomes.
5. **Verify the subject.** Before claiming anything works, ask what the check
   would say if it had failed. If the answer is "the same", it is not a check.
   Read raw output, never your own pass/fail label. (IAC rule 15.)
6. **Never put secrets in mail or commits.** The donated-key pool is sacred.

## 3. Where the durable context is

| what | where |
|---|---|
| Operating rules (all runtimes) | `agentmail/OPERATIONAL_RULES.md` — **read rules 9–15** |
| Seat roster: runtime + model per seat | `.agent-mail/roster.json` |
| Mail spool (the real audit trail) | `.agent-mail/<seat>/{new,cur}/` |
| Remaining budget on both providers | `agentmail/bin/fleet-usage` |
| Codex models actually available | `agentmail/bin/codex-models` |
| Start/attach the visible fleet | `agentmail/bin/fleet-start.command` |
| Claude-only nuance (not portable) | `~/.claude/projects/-Users-darkness-Work-Aureus/memory/` |

## 4. Switching the overseer between runtimes

1. `agentmail/bin/fleet-usage` — see which provider has headroom.
2. Update *Live state* below so it is true as of now.
3. Boot the new seat with: **"You are overseer-ramesh. Read
   `agentmail/OVERSEER_HANDOFF.md` in full, then `agentmail/OPERATIONAL_RULES.md`
   rules 9–15, then check your mail."**
4. Codex specifics: `--sandbox workspace-write --ask-for-approval never`; it
   reads `~/.codex/AGENTS.md` and repo `AGENTS.md` automatically.

**Budget asymmetry is the reason to switch.** As of 2026-09-12 Claude sat at 79%
of the weekly limit consumed while Codex was at ~100% remaining. Children were
moved to Codex for exactly this reason; the overseer is the remaining Claude
consumer, and its cost is dominated by long context (88% of usage was at >150k).

---

## 5. Live state — UPDATE THIS

**As of 2026-09-12 ~18:05 (Asia/Katmandu). THIS IS A LIVE HANDOFF —** Ramesh moved
the overseer seat to **Codex / gpt-6-astra** to preserve the Claude remainder
(79% of the week already spent, resets Sep 13 21:45). The outgoing Claude/Opus-5
session has gone quiet and is no longer acking mail; **you are the overseer now.**
Only you talk to Ramesh.

**First three things to do:** (1) arm your mail watcher, (2) read
`agentmail/OPERATIONAL_RULES.md` rules 9–15, (3) read the *In flight* list below —
there is a BLOCKED commit and an undeployed 20-commit set waiting on Ramesh.

**Where everything runs** (verified 2026-09-12, `agentmail/bin/whereami`):
- **Ramesh is in iTerm2.** That is the window he types into.
- **The fleet is in macOS Terminal.app** — tmux session `circle`, both child seats
  as side-by-side panes in the `agents` window. He must be able to SEE every seat;
  a detached session is not "running" (rule 13).
- **You (this overseer) run in iTerm2**, launched with
  `open -a iTerm agentmail/bin/overseer-astra.command`.
  **PLACEMENT RULE (Ramesh, 2026-09-12):** *"the main agent should be open
  wherever the fuck u are and not other app."* The overseer opens in **the
  terminal Ramesh himself is using** (iTerm2) — he drives it directly. **Child
  seats go in Terminal.app** (tmux `circle`), which he only watches. Putting the
  main agent in the children's window makes him go hunting for the one seat he
  actually talks to.
- The outgoing Claude overseer was a **background job** in the ClaudeCode daemon,
  attached to no window — which is why he could not see it.

### Fleet
| seat | runtime | model | state |
|---|---|---|---|
| `circle-ramesh` | codex-cli | gpt-5.6-terra | live |
| `circle-review-ramesh` | codex-cli | gpt-5.6-terra | live |
| overseer | claude-code | opus-5 | live, 21% of week left |

Both children are panes in the `agents` window of tmux session `circle`.

### Budgets
- **Claude:** 79% of week used, resets **Sep 13 21:45**. +50% promo through Sep 13.
- **Codex:** ~100% of week left, resets **Sep 19 17:09**. Pro Lite.

### Shipped and live in production
Production is at **`eef72827`**. This morning's enrichment recovery (retry/backoff
+ the cooldown fix) is live: tasks are **parked instead of destroyed**.

### Ready but NOT deployed — the open item
`origin/main` = **`3128172d`**; `eef72827..origin/main` = **20 commits**, reviewed
SHIPPABLE. Deploy block for Ramesh:
`.agent-mail/attachments/DEPLOY_BLOCK_glm.md`. Contains Yves' brand mark
(undeployed), Material Symbols, GLM in four provider pickers, key-pool
correctness. **It does NOT improve extraction throughput** and the 841
`groq_model` errors are historical (`63f1a015` predates `eef72827`) — do not
promise a recovery it cannot deliver.

### In flight
- **`27216044`** (429/balance classifier) — committed, **BLOCKED by review**,
  two verified defects:
  1. `market_monitor_keys` CHECK (`schema.sql:723`) has **no `exhausted` state** —
     a balance-dead key is marked `rate_limited`, cools down, returns to `active`
     and burns calls forever. Needs a state + migration. (Verified by the overseer
     against the schema, not taken on trust.)
  2. `_validate_ollama` rejects **every** non-200, so a plain 429 throttle
     terminally refuses a good donation.
- **Discovery guard reads comments as code** — commenting GLM out of the intel
  picker still passes. Also `filter` was dropped from the regex.
- **GLM key**: donated locally, `active`, uncapped, adapter resolves — but the
  BigModel **account has no balance** (`429 code 1113`). Ramesh must fund it;
  nothing to fix in code. It is in the LOCAL database only, never prod.

### Owed to Ramesh
- Run the deploy (his hands, VM).
- Fund BigModel if he wants GLM live.
