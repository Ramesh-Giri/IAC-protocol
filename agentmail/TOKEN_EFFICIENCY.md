# Token efficiency for the overseer + seats fleet

Adopted 2026-09-14 at Ramesh's direction ("store the information you have collected and add it to IAC").
Source research: [research/token-efficiency-20260914.md](research/token-efficiency-20260914.md) (Codex Spark seat with live web search; its "verified from source" items were spot-reviewed by the overseer, its blog claims were not adopted).
Binding rules live in OPERATIONAL_RULES.md rules 18-19; this file is the reasoning and the checklist.

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
6. Measure: run agentmail/bin/fleet-usage per rule 19 and route work to the runtime and model tier with headroom (Codex Spark or small models for mechanical and research work; Opus or GPT-6-Astra only for hard reasoning or security-critical authoring).
7. Idle seats: Claude seats wake on mail through their Monitor watcher (costly with big context); Codex seats do not wake and need one pane nudge; close idle finished seats instead of keeping them warm.

## Evaluated but not adopted
- Explicit Anthropic cache breakpoints and prewarming: applies to direct API integrations, not to Claude Code or Codex CLI seats, which manage caching themselves.
- The research's model routing example named outdated models (gpt-4o-mini, o3); use the live lineup (agentmail/bin/codex-models and the model-lineup memory).
- Prompt-compression middleware (leanctx, LLMLingua): claimed 40-60% or larger savings are unverified for CLI agents and risk losing constraints; revisit only with a measured pilot.
- Adopting AutoGen or CrewAI: high integration cost for no measured gain over AgentMail.
