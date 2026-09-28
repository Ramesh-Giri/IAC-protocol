# IAC picks the model from declared runtimes - design and measurement (modelpick-0927-x2q5)

Seat: research-modelpick-0927-ramesh.
Date: 2026-09-27.
Status: design and measurement only. Nothing in `agentmail-launch`, `roster.json`, fleet tooling or
any product repo was changed. No GCP, no Cloud Run call, no gcloud, no SSH.
Laya inference ran locally on CPU from the cached checkpoint
(`~/.cache/huggingface/hub/models--convaiinnovations--laya`), in a throwaway venv outside the repo.
Work done in a treehouse worktree, never a hand-rolled `git worktree add`.

This task supersedes nothing in `layaroute-0926-f9k3`
(`agentmail/research/layaroute/DESIGN.md`, branch `research/layaroute-0926`, commit `a8a9ba9`) - it
asks a different question (match task against a declared catalogue, not imitate the overseer's past
picks) and its own verdict was NO-GO on the question it asked. I read it in full. Its measurements
still bind and I re-checked the two load-bearing ones on today's roster before relying on them (see
"Still true today", below). I did not re-run its full pipeline; I ran new experiments that this task
specifically asks for: signal-level Laya framings (not just kind), and local catalogue verification
(not web search).

## Verdict

**Build the architecture Ramesh described, with Laya inside it exactly where the overseer's brief
placed it: a kind-plus-signal reader, never a model-namer.** Do not train it - there is nothing to
train it ON. Do not let it gate the hard rule - it is not accurate or stable enough, measured two
different ways now. Build the catalogue and the deterministic matcher first; they are useful with
zero Laya calls and one of them already catches a live bug. Add Laya later, in shadow mode, if the
outcome log says it earns its keep.

This is not "the whole thing is impossible." Steps 2-5 of the overseer's hypothesis (catalogue,
matcher, hard-rule filter, headroom, logging) are buildable now, mostly from data that already
exists on this machine. Step 1 (Laya reading the task) is buildable too, just not as a trained model
and not as a safety gate.

## Part 1: is "pass the catalogue to Laya to train" viable? (asked to confirm or refute)

**Refuted, same as the overseer suspected.** Confirmed here rather than taken on faith:

Laya's `system_one` call answers a typed question about a piece of TEXT - a `choice` question returns
one of a fixed set of labels with probabilities, nothing else (see the `laya.system_one` calls in
`eval_signals.py` below and in the prior seat's `eval_laya.py`). It has no code path that accepts
"here is a table of models and their properties" as an input to be memorized, and no code path that
outputs a model id - the catalogue isn't shaped like something you feed to `system_one` at all, let
alone train on.

Training any classifier - Laya included - needs labelled examples: (task text -> correct answer)
pairs. A capability catalogue is a table of (model -> what it's good at). Those are different axes.
To turn a catalogue into training pairs you need to already have a task-to-model policy to generate
the labels, and if you have that policy, you don't need to train anything - you have the matcher.
The only way to manufacture (task -> model) pairs without a policy already in hand is to ask an LLM
to imitate one, and then Laya's "training" is distillation of that LLM's prompt-following, at extra
cost and extra latency, with no way to tell whether it learned the LLM's judgement or its biases.

So: Laya reads the TASK (kind, plus any requirement signal it's assigned). Everything about models -
names, capability claims, price, entitlement - lives in the catalogue and the matcher, never inside
Laya. This was already the overseer's stated design; I'm confirming it holds, not proposing it.

## Part 2: discovery - what a catalogue can honestly claim

The brief's worry is specific: "main agent searches internet" produces a snapshot of vendor
marketing and contested benchmarks, decaying the moment it's written down, with no way to tell two
disagreeing sources apart. I checked what's verifiable WITHOUT a web search, on this machine, today.

### What is real, local, dated, and already sitting on disk

**Codex**: `~/.codex/models_cache.json`. One row per model the ChatGPT account can actually invoke via
this Codex CLI, each with `slug`, `display_name`, `context_window`, `supported_reasoning_levels`
(the exact effort strings the CLI accepts), `visibility` (`list`/`hide`), and a `priority` (the
CLI's own default ordering). The whole file carries `fetched_at` and `client_version`.
`agentmail/bin/codex-models` already reads it; nothing invents an id here, the CLI wrote it.

**Claude Code**: `~/.claude/cache/model-catalog/*.json`, one file per (org, surface) queried this
session. Each carries `fetchedAt` / `staleAt` (a ~58-minute TTL on the file I read) and a `catalog`
with one row per model this account and this CLI version can select: `id`, `name`, `description`
(one line, still marketing but first-party and short), `section` (`main` vs `overflow` - overflow
models need explicit selection, which is a real signal about what's the account's default lane),
`capabilities` (tool support flags), `thinking` (whether/how it takes an effort level), and
`min_claude_code_version` (excludes ids the installed CLI can't run). Nothing today reads this file
programmatically - `codex-models` has no Claude sibling. That's a one-file gap, not a hard problem:
`catalogue_check.py` in this folder reads both caches side by side to show the shape.

**What neither cache has**: price, or any real judgement of "good at X". I grepped both files for
`price`/`cost` - absent from both (see `catalogue_check_output.txt` and the grep in this seat's
transcript). `agentmail/bin/model-lineup-and-task-sizing` memory carries pricing and "use for" text,
web-search-sourced, dated, and re-verified against executed calls (its own file records two of its
own past mistakes: unexecuted ids marked "(approx)", and a test that died before reaching the model
but got read as a rejection). That is exactly the provenance discipline the brief is asking for, and
it already exists - it just isn't machine-readable. Two claim classes, two different trust levels:

| claim | source | how it's dated | disagreement handling |
|---|---|---|---|
| "this model id exists and I can call it" | local cache file (`models_cache.json`, Claude catalog) | file's own `fetched_at`/`staleAt`, refreshed by the CLI itself | none needed - it's the CLI's own account state, there's only one source |
| "this model costs $X per token" | curated memory file, web-search sourced | a `modified:` date on the memory file, re-verified periodically | last-verified-date wins; a memory file with no re-verification date is untrusted after some staleness window (propose 30 days) |
| "this model is good at X" | curated memory file / task-mail conventions (`smart-runtime-switching`, `model-lineup-and-task-sizing`) | same as above | same as above, PLUS: a claim with no source at all (no memory file, no executed test) must never enter the catalogue - "good at X" without provenance is exactly the vendor-copy risk the brief flagged |

**A capability catalogue entry, concretely, is therefore two tiers glued together**: a `verified`
tier (id, context window, effort levels, entitlement - refreshed automatically, minutes old, zero
human judgement) and a `claimed` tier (price, "good at", relative ranking - a human- or web-sourced
field with a `source` string and a `date`, refreshed on a cadence, never auto-trusted past its
staleness window). The matcher may use a `claimed` field to break ties or choose a candidate ORDER;
it may never use a `claimed` field to decide whether a candidate is allowed to be recommended at all
- only the `verified` tier gates that. This is the same last-veto-wins shape the brief asks for the
hard rules, applied one layer down to catalogue trust.

### A model that is not installed or not entitled must never be recommended

Checked, not assumed: I cross-referenced today's roster (241 seats) against both caches
(`catalogue_check.py`, run 2026-09-27T05:51Z, output in `catalogue_check_output.txt`). Result: **two
live roster seats are pinned to `gpt-5.3-codex-spark`, a model id absent from today's
`models_cache.json`** (`research-token-efficiency-ramesh`, `skyzai-tasks-plan-codex-ramesh`). That id
was verified-working on 2026-09-12 per `model-lineup-and-task-sizing` memory; nine days later it is
gone from the account's own list, and two roster entries still point at it today. **Nobody would
have noticed until a launch failed** - the roster carries no mechanism that would have caught this on
its own, and it sat live for nine days. This is the decay the brief warned about, caught with zero
web search and zero Laya calls, using exactly the mechanism this design proposes: **match the
roster's model field against the local cache, on every launch, not once; anything absent is a
finding, not a launch.** I am not fixing these two seats - that is fleet tooling and out of scope for
a design task - but I am reporting it, per the task's own "review, don't fix, mail it instead" rule;
see the mail I'm sending with this design. This is the strongest argument in this whole document for
building phase 1 (catalogue verification) before anything else: it is the cheapest possible piece,
and it just caught a real, live, silent failure mode that nothing else in the fleet would have.

The general rule this generalizes to: **the matcher's LAST step before returning a candidate is "is
this id a key in today's cache for this runtime?" - if not, drop it, no matter how good the `claimed`
tier says it is.** No invented ids can survive that check because the check is a set-membership test
against a file the vendor's own CLI wrote minutes ago.

## Part 3: architecture (what I'd build, and where Laya sits)

Same shape the overseer proposed; I'm reporting where I'd change or harden it based on what I
measured.

```
task text + brief
      |
      v
[1. Laya] -> kind + probabilities (choice question, no model names, ever)
      |
      v
[2. catalogue] -- verified tier (local cache, minutes old) + claimed tier (dated, sourced)
      |
      v
[3. matcher] -- kind + blast-radius flag + host-tool flag + author-runtime -> ORDERED candidates
      |
      v
[4. hard-rule filter] -- deterministic, regex + policy table, can ONLY remove candidates, runs LAST
      |
      v
[5. headroom selector] -- picks first permitted candidate whose pool clears the floor
      |
      v
{runtime, model, effort, reasons[]}  (or: fall back to roster value / stated default)
      |
      v
[6. log] -- one JSONL line, always, whichever path decided
```

1. **Laya reads the task, emits kind + requirement signals.** Measured below: this is real but
   noisy and framing-sensitive. Use it as one INPUT to the matcher with a confidence floor, never as
   the sole decision, and never let its output name or rank models directly (it structurally can't -
   see Part 1).
2. **Catalogue**, two tiers as above.
3. **Matcher**: a lookup table (kind, blast-radius, host-tool-flag, author-runtime) -> ordered
   candidate list of catalogue entries, same as the prior seat's proposal. This is the piece with the
   least measurement risk - it's a table, testable exhaustively, and it's where a human's judgement
   (Ramesh's) is supposed to live, encoded rather than re-derived every time.
4. **Hard-rule filter, last, veto-only.** Unchanged from the prior seat's design; still correct;
   re-justified below with fresh evidence that it is not enforced anywhere today.
5. **Headroom**: reads a CACHED `fleet-usage` snapshot, never calls it in the launch path (that probe
   drives a throwaway tmux session and takes about a minute - unacceptable in a launch's hot path).
   Unchanged from prior design.
6. **Log**: unchanged from prior design; still the single highest-value, lowest-risk thing to build,
   because it's what turns "did this work" from opinion into a queryable table.

## Part 4: Laya, measured - kind AND direct signals, challenging the hypothesis rather than reusing it

The prior seat measured Laya as a 4-way/9-way KIND classifier. This task asks specifically for
"kind plus requirement signals" (Laya emits SIGNALS, the matcher decides). I tested whether asking
Laya more directly for the two signals a matcher actually needs - "is this security work" and "is
this read-only" - does better than routing through a kind label first. It should, if anything: a
direct binary question has less to get wrong than a 4-or-9-way pick.

> **Read this before anyone proposes a Laya probability threshold again.** The readonly signal's
> recall swings from 0.600 to 0.877 - 28 points - purely from listing "yes" before "no" instead of
> after, nothing else changed. That rules out Laya as a gate on its own, independent of whatever the
> recall number happens to be on any given day: a threshold calibrated against today's wording is not
> a threshold against tomorrow's, and the wording WILL change every time the model lineup does. This
> is a stronger objection than "the recall is too low" - low recall can look like it might improve
> with a better prompt; an instability driven by string order cannot be prompted away.

**Method.** Two `choice` questions, each yes/no, wording fixed before running (no tuning - the same
discipline the prior seat used, and the same discipline the LAYA_TODO_DETECTOR_STATE incident argues
for): "Does this task involve security testing, a security audit, penetration testing, exploit work,
or a security fix?" and "Is this task read-only, meaning it must not change any code (a review, a
plan, research or a measurement)?". Each run twice, option order forward and reversed (order is a
known bias lever for Laya's choice head - the prior seat found a 5-point swing on kind; I wanted to
know if a binary question is more stable). Ground truth: the prior seat's kind labels, same known
limitation (regex-assisted, hand-reviewed, one labeller - see its "Limits" section, which applies
here too). n=230 routable seats, description text only, local CPU, no network. Code and raw results:
`eval_signals.py`, `signals_results.json`.

| signal | order | n | positives | accuracy | recall | precision |
|---|---|---|---|---|---|---|
| security | fwd | 230 | 34 | 0.561 | 0.706 | 0.209 |
| security | rev | 230 | 34 | 0.583 | 0.529 | 0.184 |
| readonly | fwd | 230 | 65 | 0.609 | 0.600 | 0.379 |
| readonly | rev | 230 | 65 | 0.313 | 0.877 | 0.275 |

Two findings, both against using this for the hard rule:

1. **Recall on security tops out at 0.706** (24 of 34 caught), worse than looking impressive but
   still means roughly 1 in 3 security-flavoured seats gets missed by Laya alone, on the more
   favourable of the two option orders. That is not a fixable-by-better-wording problem I can rule
   out from here, but it's consistent with the prior seat's 0.56 on the 4-way kind question - two
   different phrasings, both well under a bar you could hang a hard rule on.
2. **The readonly signal moves 28 recall points (0.600 -> 0.877) and 30 accuracy points
   (0.609 -> 0.313) on option order alone**, with nothing else changed. An instability that large,
   from a variable that has nothing to do with the task, means the raw probability cannot be
   compared to a fixed threshold across any change to the question - which is exactly what "the
   lineup changes, the wording will need to change with it" guarantees will happen over the life of
   this system. A signal whose meaning drifts when you reorder two strings is not a signal you can
   calibrate once and trust.

This is a genuine attempt to make the overseer's "kind plus requirement signals" framing work better
than the prior seat's kind-only test, run fresh rather than assumed. It does not clear the bar
either. Verdict on Laya's role is unchanged: real signal, useful as ONE weighted input with a
confidence floor into the matcher's ranking, structurally excluded from the hard-rule gate, which
must stay regex-and-table, deterministic, last, unit-tested exhaustively - unchanged from the prior
design.

## Still true today, re-checked rather than assumed

- **The hard rule is still unenforced.** `skyzai-sec-audit-ramesh` (description: "Full Cloudflare
  security-audit skill run, backend + rules, report only") is `claude-opus-5` in today's
  `roster.json`, checked 2026-09-27. This is the same live violation the prior seat found on
  2026-09-26; it has not been fixed in the day between. A deterministic filter that runs on every
  launch would have caught it both times; a Laya gate at the measured recall would have had roughly
  a 30-44% chance of missing it depending on phrasing.
- **A dead model id is live in the roster right now** (previous section) - new evidence this task's
  scrutiny of "discovery" surfaced that the prior task didn't need to look for.

## Enforcement design for the hard rules (unchanged from the prior seat, re-justified)

1. One pure function, `resolve(task, pool_state, author_runtime) -> {runtime, model, effort,
   reasons[]}`, lives in launcher-side code, never inside a Laya client.
2. Short-circuits first: pinned seats (overseer, council), an explicit per-task `model:` override on
   the task mail (still the documented mechanism - `ORCHESTRATION.md` section 3, line 90, checked
   against today's file).
3. Router proposes: Laya supplies kind + signals + probabilities, nothing else. It cannot emit a
   model name even if compromised or miscalibrated, because its output type doesn't include one.
4. Matcher maps (kind, blast-radius, host-tool flag, author runtime) to an ordered candidate list
   from the catalogue's `verified` tier.
5. Hard-constraint filter runs LAST, reads task text with deterministic patterns (the regex is the
   PRIMARY signal, per the prior seat's finding that over-locking is nearly free - re-affirmed
   here: at the loosest Laya lock threshold, a false lock just sends a seat to Sonnet, which is where
   79% of seats already go), and may additionally lock on Laya P(security) crossing a low floor
   (tightens only, per Part 4's numbers, never loosens).
6. Allowlist check: candidate id must be a key in TODAY's cache read (Part 2's mechanism) - not
   "was verified once", every launch, because Part 2 found a nine-day-old id already dead.
7. Exhaustive unit test over the full finite domain (kind x flags x pool state x author runtime x
   Laya kind), asserting no security-locked path ever resolves to Opus or Fable, and pinned seats
   never reach the router at all.

## Headroom - unchanged, still where the real signal lives

The prior seat's finding stands and nothing here contradicts it: date-as-budget-proxy beat the
kind classifier (84.3% vs 79.1%/81.3%), meaning headroom, not task kind, is the strongest single
predictor of what actually got picked historically. The selector reads a snapshot `fleet-usage`
writes periodically (never called from the launch path - it drives a throwaway tmux probe and takes
about a minute), applies the 15%-unless-resets-within-24h floor and the overseer reserve, and picks
the first ALREADY-PERMITTED candidate above its floor. A stale (>2h) or unreadable snapshot is
UNKNOWN, which keeps the default candidate - a failed read is a failed check, not a zero.

## Failure path

Unchanged: timeout (1.5s in-process; local CPU measured 0.19-0.36s per call in both this seat's and
the prior seat's runs, so this is generous headroom) or low confidence or any exception on the Laya
call resolves straight to `unknown` kind, which the matcher treats as "use the roster value or the
stated Sonnet default." The hard-constraint filter still runs on that fallback path - a router
outage cannot un-gate a security seat. A router outage cannot block a launch, full stop: worst case
is the launch you'd have made with no router at all.

## Logging

Unchanged from the prior design (task id, kind + probabilities + Laya latency/error, catalogue
snapshot ids for both tiers with their fetch/verify dates, headroom snapshot, final decision,
`decided_by`, brief hash never brief text). Restating why this is the first thing worth shipping
regardless of any Laya verdict: it is what would let a future measurement be honest instead of
regex-labelled-by-one-person-after-the-fact, which is the single biggest limitation of both this
study and the prior one.

## What I would build FIRST

Not the same answer as the prior seat, because this task's own scrutiny surfaced a cheaper, lower-
risk, already-proven-useful first step:

1. **Catalogue verification** (`catalogue_check.py`, this folder) - read-only, no policy risk, no
   Laya, no design debate, and it already found a live bug (two seats on a dead Codex id) in the time
   it took to write and run it. Turn it into a small script the overseer runs periodically (or
   folds into `rollcall`), same shape as `codex-models` but covering the allowlist check across both
   runtimes and flagging roster/cache mismatches. This is smaller than the prior seat's "decision
   log" proposal and has zero design risk.
2. **The decision log + deterministic hard-rule guard** (prior seat's proposal, unchanged, still
   correct) - would have caught the still-live Opus/security-audit seat both times it was checked.
3. **Laya in shadow mode**, 3-4 weeks, only if Ramesh still wants the evidence after (1) and (2) are
   running - unchanged from the prior recommendation, because nothing measured here moves that
   verdict.

## Recommendation

1. **Ramesh's target ("the right model chosen per task, from the models I said I have") is
   achievable, and the architecture in his own brief is the right shape** - Laya reads the task,
   never the models; a catalogue holds the models with dated, sourced claims; a matcher joins them; a
   deterministic filter has final say. Build that.
2. **"Train Laya on the catalogue" does not work, confirmed**: there is no (task -> model) label to
   train on without already having the policy you'd be training it to replace. Not a Laya limitation
   specifically - it's true of any classifier fed a capability table instead of labelled examples.
3. **Discovery should be local-cache-first, not internet-first.** Both runtimes already write a
   dated, authoritative, machine-readable list of what THIS account can actually call
   (`~/.codex/models_cache.json`, `~/.claude/cache/model-catalog/*.json`). Web search and curated
   memory are still needed for price and "good at X", but those claims must carry a source and a
   date and must never gate whether a model is offered - only the local cache does that. Two live
   findings surfaced by that check right now: a dead Codex model id on two roster seats, and the
   Opus-on-security-audit rule violation persisting from the prior study to today. Both are reported
   to the overseer separately, not fixed here.
4. **Laya is not accurate or stable enough to gate the hard rule**, tested two ways now (kind
   classification, and direct binary signal framing) - security recall never clears ~0.7, and a
   binary signal's own recall swings 28 points on option order alone. Keep it strictly downstream of
   a deterministic veto.
5. **Build catalogue verification first** - smallest, safest, and it already found a bug. Then the
   decision log and hard-rule guard. Laya joins later, in shadow mode, if the logged outcomes justify
   it.

## Limits of this study

- Ground truth for the signal-level test is the prior seat's kind labels (regex-assisted, one
  labeller) - same limitation as before, inherited rather than re-derived.
- n=230, one Laya checkpoint (`convaiinnovations/laya`, stock, no fine-tuning), two wordings, two
  option orders, fixed in advance - same design discipline as the prior study, same caveat that a
  third wording could move the number again.
- The Claude Code model-catalog cache is per-(org, surface)-queried-this-session; I read the newest
  file present, but a fresh install or a long-idle account might have none cached at all -
  `catalogue_check.py` handles that as "empty," which the design treats as UNKNOWN, not "no models
  exist."
- Codex sub-tiers, Haiku, and reasoning-effort sizing were out of scope here as they were in the
  prior study; the log this design proposes is what would finally collect the data to analyse them.
- I did not build or run the matcher/policy table itself - out of scope per the task
  ("design only", "do not build the picker until GO").

## Files

`eval_signals.py` (the two-signal experiment), `signals_results.json` (raw per-seat probabilities),
`catalogue_check.py` (the throwaway research prototype of the roster-vs-cache cross-reference,
kept as the record of what was measured for this design), `catalogue_check_output.txt` (its output
as run 2026-09-27T05:51Z), `dataset.json` (copied from the prior seat's `layaroute` branch, commit
`a8a9ba9`, unchanged - same 230-seat, hand-reviewed dataset, so the two studies are directly
comparable).
Re-run: `pip install laya==0.3.20` in a throwaway venv (`HF_HUB_OFFLINE=1`), then
`python3 eval_signals.py`; `python3 catalogue_check.py` needs no install, reads only local cache
files and `roster.json`.

**Phase 1, post-GO**: the prototype above was promoted into a real tool at
`agentmail/bin/catalog-check` (matches the `codex-models` style: no-args-first, `--help`, `-d
MAIL_ROOT` like every other `agentmail/bin` script). It is read-only - reports mismatches, edits
nothing - and returns a non-zero exit on any mismatch or unreadable catalogue, so it can be folded
into `rollcall` or a periodic check. Run it: `agentmail/bin/catalog-check -d
/Users/darkness/Work/Aureus/.agent-mail`.
