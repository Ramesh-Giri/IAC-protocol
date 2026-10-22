# Token efficiency for the overseer + seats fleet

This checklist describes reusable coordination practices.
Private adoption history and original research notes live in ignored `local/`.
See the [research checklist](research/token-efficiency-20260914.md) for evaluation questions.
Binding rules live in OPERATIONAL_RULES.md rules 18-19 and 31-39; this file is the reasoning and the checklist.
Use the approved roster and verified local catalog for current runtime/model choices.

## Where the tokens actually go
- The overseer's own long context, re-read on every turn (cached reads are cheaper, never free); by far the largest consumer on a busy day.
- Each woken seat re-reading its whole context when a mail or monitor event arrives, even if it only acknowledges.
- Writing and reading mail bodies (paid by both writer and reader).
- Tool output pasted into context or mail (test logs, diffs, file dumps).
- The operator's own short messages are negligible; asking the operator to abbreviate saves almost nothing.

## Adopted practices
1. Fresh sessions over giant sessions: close a seat when its unit is done and give follow-ups to a fresh seat; hand the overseer seat to a fresh session (compact handoff file) after a large block of work instead of carrying the whole day.
2. Fixed handoff envelope, artifacts not prose: task, decisions, constraints, acceptance, state (branch + SHA + raw test counts), next action; mails point at spec/handoff files instead of repeating them.
3. Mail discipline: one batched decisions mail; facts peer-to-peer; seats mail at ACK, blocker and DONE only; overseer reads subjects first but opens verdicts, blockers, questions and DONE mails in full immediately.
4. Keep durable instructions stable and short (AGENTS.md, CLAUDE.md, context/ files) so they are read once per session and caching stays effective; do not churn them mid-session.
5. Tool output hygiene: send counts and paths, not logs; grep or tail before reading; never paste repeated command output into mail.
6. Measure: run agentmail/bin/fleet-usage per rule 19 and route work to the runtime and model tier with headroom according to task fit and site policy.
7. Idle seats: Claude seats wake on mail through their Monitor watcher (costly with big context); Codex seats do not wake and need one pane nudge; close idle finished seats instead of keeping them warm.
8. Batch cleared merges into one combined local validation and one push, rather than repeating a full CI wait after every merge.
   Check required completed jobs on the final pushed SHA; cancelled or superseded jobs do not count as green.
9. Inspect new messages in the same command as an acknowledgement read; never suppress inbox output to stop watcher replay.
   A fast acknowledgement that hides a verdict creates more idle-seat cost than it saves.

## Changes that need evidence first

Cache configuration depends on the runtime or API integration and must follow its current official documentation.
Compression and routing changes need a representative pilot that checks retained constraints, correctness and actual cost.
Adding an orchestration framework requires evidence of a useful capability beyond the existing protocol helpers.
Do not publish private per-seat measurements as generic guidance.
