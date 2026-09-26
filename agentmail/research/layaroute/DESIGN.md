# Laya picks the model for a task - design and measurement (layaroute-0926-f9k3)

Seat: research-layaroute-0926-ramesh.
Date: 2026-09-26.
Status: design and measurement only.
Nothing in `agentmail-launch`, `roster.json`, fleet tooling or any product repo was changed.
No GCP, no Cloud Run call.
Laya inference ran locally on CPU from the cached checkpoint (`~/.cache/huggingface/hub/models--convaiinnovations--laya`), in a throwaway venv outside the repo.

## Verdict

**Do not build a Laya router.**
Build the decision log and a deterministic hard-rule guard instead, and run Laya in shadow mode only if Ramesh still wants the evidence.

The reasons, in order of weight:

1. The model choice in the roster is barely a function of task kind, so no kind classifier can do much.
   Give the router a PERFECT kind classifier (my own labels) and the best fixed policy, scored leave-one-out: 81.3% against 79.1% for "always Sonnet".
   The gain is +2.2 points with a 95% bootstrap interval of [-2.6, +7.0].
   That is not distinguishable from zero at n=230.
2. What the roster records is mostly the budget regime of the day, not the task.
   Codex share by day: 2026-09-14 7 of 24, 2026-09-17 19 of 46, then 1 of 69 seats from 2026-09-22 onward.
   Opus share: 7 of 24 on 09-14, 3 of 12 on 09-21, zero since 09-22.
   Since 2026-09-22 the overseer has chosen Sonnet 68 times in 69 seats, so today's behaviour already IS the constant.
3. Laya as measured does not beat the constant.
   End to end (Laya kind -> best policy -> predicted model class, policy fitted leave-one-out): 79.1% on the 4-way wording, identical to always-Sonnet, and between 71.3% and 79.1% on the 9-way wording depending on option order.
4. Laya's recall on the one class that must never be wrong is too low to be a safety mechanism: it flags 56% of security-flavoured seats.
   A router that relies on it for the hard rule is a broken router.
5. The router would run about 18 times a day (230 seats over 13 days, peak 46).
   A CPU service kept warm for that (`min-instances=1`) is a poor trade against a table lookup.

This is the "worse than a constant, say so plainly" case.
It is not a statement that Laya is a bad classifier: it is a real classifier on this task (see the numbers below).
It is a statement that the target, "which model did the overseer pick", carries almost no signal that task text can supply.

## What is true today

Ramesh's premise ("you are doing it based on the project") is not what the data shows.
It is per SEAT, and by the one-seat-one-task rule (OPERATIONAL_RULES rule 21) a seat IS a task, so it is effectively per task, chosen by hand.
Predicting the model from the project alone scores exactly the constant, 79.1%, because every project's majority is Sonnet.
Only 6 long-lived project seats (circle, skyzai, connect-sdk, reality_futures, apu, aia) are genuinely per project, and they are not routed tasks.

Population used: 230 routable task seats.
Excluded: overseer, the Codex council seat, this seat, and the 6 standing project seats.

| model class | seats | share |
|---|---|---|
| Sonnet 5 (claude-code) | 182 | 79.1% |
| Codex (terra 27+2 subagent, spark 2, sol 2) | 33 | 14.3% |
| Opus 5 | 15 | 6.5% |

The roster has no token or cost data, so cost per task cannot be measured from it.
That gap is itself a finding (see Logging).

## The choice set, from the 230 real seats

I labelled every seat by task kind from its description text alone (never from the model).
The labels are my judgement: regex-assisted, then every regex misfire fixed by hand (`label_kinds.py`, `OVERRIDE`).
Because they were regex-assisted, the kind labels are keyword-solvable by construction.
Read every agreement number below as "agrees with the author's labelling", not as correctness.

| kind | seats | share | Sonnet | Opus | Codex |
|---|---|---|---|---|---|
| feature | 64 | 27.8% | 53 | 7 | 4 |
| review (read-only, incl. re-review) | 38 | 16.5% | 13 | 7 | 18 |
| ui | 30 | 13.0% | 30 | 0 | 0 |
| security_fix (hardening implementation) | 22 | 9.6% | 22 | 0 | 0 |
| fix_findings (fix a reviewer's BLOCK) | 19 | 8.3% | 13 | 0 | 6 |
| integrate (merge, land, release) | 16 | 7.0% | 16 | 0 | 0 |
| plan_research (no code) | 15 | 6.5% | 13 | 0 | 2 |
| bugfix / live incident | 14 | 6.1% | 13 | 0 | 1 |
| security_audit (audit, pen test, security review) | 12 | 5.2% | 9 | 1 | 2 |

No kind swallows 80% and none is empty, so nine is a usable set.
But only review and feature ever leave Sonnet in any quantity.
Five of the nine kinds (ui, security_fix, integrate, bugfix, and largely plan_research and fix_findings) map to Sonnet 100% or nearly so.
A router only earns its keep on the distinctions that change the answer, and there are three: review, security, and blast radius.
So the choice set a policy actually needs is the 4-way one: **review / security / plan_research / build**.
Blast radius (wallet, escrow, key vault, crypto, prod data) is not a task kind.
It is a property of the project and the diff, and it belongs in a policy input, not in Laya's choice set.

Recommendation on question 1: classify KIND, not model.
Laya cannot name a model (its output is a label plus probabilities), the lineup changes every few weeks, and the policy table stays readable and diffable.
Routing straight to a model would also weld the checkpoint to a lineup that is stale within a month.

## Measured: Laya zero-shot on the roster

Method.
One typed `choice` question, the fixed wording `What kind of work does this task brief describe?`, criteria written once before running and not tuned (the todo-detector work showed that ~60 tuned combinations inflate a number).
Two wordings (9-way, 4-way), two option orders (forward, reversed, because order is a known bias lever for the choice head), two inputs (description only, n=230; description plus first 700 chars of the attached brief, n=131 because only 131 seats have a readable attachment).
Local CPU inference, 0.19 s per seat on descriptions, 0.36 s with briefs.
Checkpoint: stock English `convaiinnovations/laya`, no fine-tuning.
Data and per-seat probabilities: `dataset.json`, `laya_zeroshot_results.json`.

Kind accuracy against the author's labels:

| input | choice set | order | n | Laya | majority class |
|---|---|---|---|---|---|
| description | 9-way | fwd | 230 | 54.8% | 27.8% |
| description | 9-way | rev | 230 | 49.6% | 27.8% |
| description | 4-way | fwd | 230 | 77.0% | 62.2% |
| description | 4-way | rev | 230 | 75.2% | 62.2% |
| desc + brief | 9-way | fwd | 131 | 61.8% | 23.7% |
| desc + brief | 4-way | fwd | 131 | 74.0% | 48.9% |

Laya is well above chance on kind, so it is a real classifier here, in line with the todo detector.
Two cautions: the 9-way result moves 5 points on option order alone, and adding the brief did not help on the 4-way set.

Per kind, 4-way, description, forward order:

| kind | n | recall | precision |
|---|---|---|---|
| build | 143 | 0.80 | 0.86 |
| review | 38 | 1.00 | 0.69 |
| security | 34 | 0.56 | 0.63 |
| plan_research | 15 | 0.40 | 0.46 |

Per kind, 9-way: review recall 0.97, integrate 0.81, ui 0.60, security_fix 0.59, bugfix 0.57, security_audit 0.50, feature 0.41, plan_research 0.20, fix_findings 0.11.
Laya confuses fix_findings with bugfix (13 of 19), which is a genuine ambiguity in the words, not a Laya defect.

Confidence is informative: accuracy on the covered subset rises with the top probability (4-way: 0.881 at floor 0.5 covering 55%, 0.957 at 0.7 covering 20%).

End to end, the number that decides "worth shipping".
For each seat, take Laya's kind, look up the best policy for that kind fitted on the OTHER seats, and compare the predicted model class with the one actually chosen.

| input | choice set, order | always-Sonnet | perfect classifier | Laya |
|---|---|---|---|---|
| description (n=230) | 4-way, fwd | 79.1% | 81.3% | 79.1% |
| description (n=230) | 4-way, rev | 79.1% | 81.3% | 79.1% |
| description (n=230) | 9-way, fwd | 79.1% | 81.3% | 79.1% |
| description (n=230) | 9-way, rev | 79.1% | 81.3% | 71.3% |
| desc + brief (n=131) | 4-way | 74.8% | 64.9% | 74.8% |

Laya never beats the constant.
The 64.9% "perfect" figure on the brief subset is not a bug: with 131 seats the fitted policy flips review to Codex (the Sep 17 regime) and the leave-one-out score drops below the constant.
That instability is the point, the signal is too thin to fit.

What would help is knowing the day: kind plus date gives 84.3% (+5.2 points, 95% interval [0.0, +10.4]).
Date is a stand-in for the Claude and Codex budget state that day.
So the honest reading is that the only variable with any pull on the label is headroom, which is not a property of the task.

## Hard rules: how the policy makes them impossible to override

Rules found (overseer memory `model-lineup-and-task-sizing`, `smart-runtime-switching`, `fleet-authority-and-escalation`, `ORCHESTRATION.md` section 3, `OPERATIONAL_RULES.md` rules 12, 19, 21):

1. Security audits, pen tests and exploit reproduction go to Sonnet, never Opus 5.
   The safeguard "Model switch" dialog blocked seats on 2026-09-15 and 2026-09-16.
   The roster itself holds the violation: `skyzai-sec-audit-ramesh` is `claude-opus-5`, the only Opus seat among the 12 audit-kind seats.
2. The overseer seat is not routed, and neither is the council seat (`codex-ramesh`, advisory, read-only, mail-bridge).
3. Fable 5.1 is support-only, spawned by the overseer under Ramesh's two conditions.
   The router must never emit it.
4. Only executed-and-verified Codex IDs are valid.
   `gpt-5-codex`, `gpt-5.1-*` and `gpt-5.3-codex` are rejected by the account, and memory says Spark is unusable, yet two roster seats are on Spark.
   The allowlist is `agentmail/bin/codex-models` (reads `~/.codex/models_cache.json`) plus a checked-in Claude list.
5. Host-tool work (tmux, emulators, `flutter test` on the host, GUI prompts) must be a Claude seat.
   A task-text classifier cannot see this, so it is a capability flag on the task mail, not a Laya output.
6. Reviewer on the other runtime than the author, where possible.
   This is relational: it needs the AUTHOR seat's runtime as a policy input, which no classifier over the reviewer's own brief can supply.
7. Budget floors: about 15% per pool unless it resets within 24 hours, and an overseer reserve.
8. Expensive models (Opus, GPT-6 Astra, and Sol) only for work that needs them; never the default.
9. One task per seat (rule 21).
   A running session cannot swap its model, so routing happens once, at launch, per task id.
10. Seats never open a prompt (rules 12, 22).
    Routing must never produce a launch that can end in an interactive dialog; the Opus security dialog is exactly that.

Conflict to decide.
The overseer memory says "Opus is fine for code REVIEW" and to use Opus for security-critical diffs, while rule 1 says audits go to Sonnet.
Four Opus review seats ran on 2026-09-15 and 09-16 (`skyzai-final-review*` explicitly covered security and UI, plus `skyzai-notes-review` and `skyzai-nest-review`) and the memory records no block for them, so the boundary is fuzzy and the dialog fired on audit and reproduction content.
My recommendation is the conservative side: any security-flavoured text locks OUT Opus and Fable, whatever the kind.
The cost is small, because the locked fallback is Sonnet, which is the default anyway (measured below: over-locking costs almost nothing).

Enforcement design, so Laya's output cannot override a rule rather than merely usually not doing so:

1. One pure function, `resolve(task, pool_state, author_runtime) -> {runtime, model, effort, reasons[]}`, lives in launcher-side code, not in the Laya client.
2. Short-circuits first, before any router call: pinned seats (overseer, council) and an explicit per-task override (`model:` on the task mail, ORCHESTRATION section 3).
3. Then the router proposes: Laya supplies a KIND and probabilities, nothing else.
   Laya has no way to name a model, so it structurally cannot emit Opus for anything.
4. Then the policy table maps kind (plus blast-radius flag, host-tool flag, author runtime) to an ORDERED candidate list.
5. Then the hard-constraint filter runs LAST, on the final candidate, and it is the only thing that can veto.
   Its predicates read the task text (brief and attachment) with deterministic patterns, and read Laya's kind only to add locks:
   a security-flavoured pattern, OR Laya P(security) >= 0.3, OR an unreadable or missing brief, locks out Opus and Fable.
   Laya can therefore tighten and never loosen.
6. Then the allowlist check: model ID must be in the verified list, else fall back to the roster value.
7. An exhaustive unit test enumerates every (kind, flags, pool state, author runtime, Laya kind) combination, which is a small finite domain, and asserts that no security-locked path resolves to Opus or Fable, and that pinned seats never reach the router.
   A test over the whole domain is a real check: it would fail if a table row were wrong, which a spot check would not.

Measured cost of over-locking, since the filter is deliberately conservative.
At P(security) >= 0.5, 0 of 196 non-security seats would be locked but only 11 of 34 security seats are caught.
At >= 0.3, 22 of 34 caught and 20 of 196 non-security seats locked.
At >= 0.2, 33 of 34 caught and 65 of 196 locked.
A false lock sends a seat to Sonnet, which is 79% of seats already, so recall matters and precision barely does.
Set the Laya lock at 0.2 if Laya is used at all, and treat the regex as the primary.
The regex hard rule is a design proposal here, not something I can score fairly: my kind labels came from similar patterns, so any score on this roster would be circular.
Shadow mode is how it gets scored honestly.

## Budget and headroom: beside the policy, not in it

The table maps kind to an ordered candidate list, for example review: Codex terra, then Sonnet.
A separate headroom selector then picks the first candidate whose pool is above its floor.
It is a second stage for three reasons.
Kinds change over months and budgets over hours, so folding them together forces a policy edit every time a reset passes.
The data says budget is what actually moved the label (Codex 19 of 46 on one day and 1 of 69 since 09-22), so it must be inspectable on its own.
And a failure in the budget read must not corrupt the kind decision.

Rules for the selector:

1. Inputs are a cached snapshot from `fleet-usage`, written by the overseer's periodic check (start, before launches, every ~2h).
   The launch path must NOT call `fleet-usage` itself: it drives throwaway tmux sessions and takes about a minute.
2. Score a pool by remaining percentage divided by hours to reset (use it or lose it), subject to the 15% floor unless it resets within 24 hours, and the overseer reserve.
3. A snapshot older than 2 hours, or "could not read", means UNKNOWN, and UNKNOWN keeps the default candidate.
   Per rule 19, a failed read is a failed check, not zero budget, and not full budget either.
4. Review anti-affinity: prefer the runtime that did not author the reviewed diff.
5. Only the choice among ALREADY-PERMITTED candidates happens here.
   Headroom can never re-admit a model the hard-constraint filter removed.

## Failure path: degrade to today, decided in one place

Fallback is decided in `resolve()`, never inside the Laya client.
The client is only allowed to return `(kind, probs, latency)` or raise.

- Timeout: 1.5 s in-process (local CPU measured 0.2 to 0.35 s), 3 s if a remote service is used.
  No retry: a launch is not worth two waits.
- Confidence floor: top probability >= 0.5 on the 4-way choice.
  Measured accuracy on the covered subset is 88% at that floor, covering 55% of seats.
  Below the floor, kind is `unknown`.
- `unknown`, any exception, service down, empty brief, or unverified model ID all resolve to today's behaviour: the roster value, or the stated default Sonnet 5.
  The hard-constraint filter still runs on the fallback.
- The reason chain is printed by `agentmail-launch --terminal print`, so the dry run shows why a model was chosen, the same way it shows the command today.
- A router outage cannot block a launch, because the worst case is the launch you would have made anyway.

## Logging from day one

This is the part worth building regardless of Laya, and it is what today's process is missing.
One append-only JSONL line per routing decision (decided by the router, by an overseer override, or by the roster):

- timestamp, task id, seat id, project, kind labels (author or Laya) with probabilities and checkpoint version, Laya latency or error code
- roster value, policy candidates, hard-constraint locks that fired, headroom snapshot id with each pool's percentage and reset time, final runtime, model, effort, `decided_by`
- sha256 of the brief, never its text

Outcome signals to join afterwards, all obtainable from the existing mail spool and guards:

- rework: a BLOCK verdict on the seat's branch, or a fix/re-review chain (19 fix_findings seats already exist, the chain is visible in mail)
- stall: fleet-guard IDLE, STUCK and GONE alerts
- classifier or dialog block: fleet-guard PROMPT with "model switch" or "safeguards flagged"
- overseer override: a roster diff after the router ran
- cost: session transcript token totals per seat, which do not exist anywhere today (a gap to close first)
- time to DONE

Tune only on cells with at least 30 outcomes per (kind, model), and keep a held-out fortnight, so the policy is tuned on evidence and not on opinion, which is exactly what happened here.

## Recommendation

1. Do not build the Laya router, on today's evidence.
   It cannot beat "always Sonnet", it fails the hard-rule test alone, and its only real signal is the budget state, which is not Laya's to give.
2. Build the routing-decision log and the deterministic guard first.
   They are useful with no Laya at all: they would have caught the Opus security audit, and they turn the overseer's unrecorded judgement into data.
3. If Ramesh still wants Laya in the loop, run it in SHADOW MODE for 3 to 4 weeks: it records its kind next to the overseer's choice and changes nothing.
   Decide GO or NO on the outcome-labelled log, using the criterion "does a Laya-informed policy have a lower rework, stall or cost than what the overseer chose, on at least 30 seats per cell".
   Inference for shadow mode can be the local CPU checkpoint (no Cloud Run), which is a Ramesh decision.
4. The one place Laya might add value over patterns is a security-flavoured brief that contains none of the words a pattern lists.
   Nothing in this roster can test that fairly.
   Shadow mode can.
5. A different, larger lever than model choice is reasoning effort (Codex takes low to ultra, and `~/.codex/config.toml` pins high globally).
   The roster does not record it, so I could not measure it.
   The log should.

## Limits of this study

- The ground truth is the overseer's unvalidated judgement combined with the day's budget, not correctness.
- Kind labels are mine and keyword-derived.
- n=230, one checkpoint, one wording per choice set, fixed in advance; the 9-way result moves 5 points on option order.
- Descriptions are short summaries the overseer wrote, not the briefs a live router would see, and only 131 seats have a readable attachment; using the brief did not help.
- Codex sub-tiers (terra, sol, spark) and Haiku were not analysed: Haiku was never used, so a Haiku lane for mechanical work has no data at all.
- All results are on the stock checkpoint; nothing was fine-tuned.
- A single labeller: no inter-rater check.

## Files

`label_kinds.py`, `build_dataset.py`, `dataset.json` (230 seats plus 6 standing), `ceiling.py`, `uncertainty.py`, `eval_laya.py`, `laya_zeroshot_results.json`, `score_laya.py`, `confidence.py`, `results.txt` (all output).
Re-run: `python3 build_dataset.py && python3 ceiling.py && python3 uncertainty.py`; `eval_laya.py` needs `pip install laya==0.3.20` in a venv and the cached checkpoint (`HF_HUB_OFFLINE=1`).
