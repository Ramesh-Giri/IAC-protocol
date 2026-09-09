# Conversation Context (template)

A per-session handoff folder so a fresh agent (Claude, Codex, etc.) can resume
**exactly** where a previous session stopped, without the operator re-explaining.
This is the session-level companion to `project-context/` (which describes a
*project*; this describes a *conversation/session in flight*).

## How to use it

Copy this folder to a working location (e.g. your org root as
`conversation-context/`) at the start of, or during, a substantial session, and
keep it current as work progresses. Fill in the four files. When you need to hand
off — closing a window, switching agents, or running low on context — the folder
*is* the handoff.

## The four files

- `SESSION_SUMMARY.md` — what was done this session and why (narrative + decisions).
- `CURRENT_STATE.md` — what's live/running now, what's parked, every file changed.
- `NEXT_STEPS.md` — the ordered pickup list, with exact commands where possible.
- `README.md` — this file: how to use it + the continuation prompt below.

## Continuation prompt (paste to a fresh agent)

> Read `<path>/conversation-context/` (README → SESSION_SUMMARY → CURRENT_STATE →
> NEXT_STEPS), then continue where the last session left off. Give me a one-screen
> status first, then proceed with the top NEXT step.

## Notes

- Keep it **living**, not a one-time snapshot — stale handoffs mislead.
- It complements, not duplicates, durable memory and any tool/onboarding docs;
  link to those rather than copying them.
- A fresh Claude in an org root also auto-loads `CLAUDE.md` + memory; a fresh
  Codex/other won't, so state the agent's role here and point at `CLAUDE.md`.
