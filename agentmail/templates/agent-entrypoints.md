# Agent entrypoints — one canonical instruction set for every agent

Goal: whichever agent you open — Claude, Codex, Cursor, Copilot, Gemini, … — reads
its own native config, lands on the **same** instructions, and behaves identically,
including auto-reading `conversation-context/` to resume a session. Set this up per
site so a fresh agent of any kind can take over with no extra prompting.

## The pattern

1. **Canonical file — `AGENTS.md`** at the org root holds the full instructions (the
   overseer/role doc; see `OVERSEER_CLAUDE.md`). `AGENTS.md` is the cross-agent
   standard many tools load, so it is the single source of truth.

2. **Thin pointers** — every other agent config is one line pointing at `AGENTS.md`,
   never a copy of the body (copies drift):
   - `CLAUDE.md` — Claude Code
   - `.cursorrules` and `.cursor/rules/agents.md` — Cursor
   - `.github/copilot-instructions.md` — GitHub Copilot
   - `GEMINI.md` — Gemini CLI

   Each contains, verbatim, something like:
   > Read `AGENTS.md` in the project root — the single canonical instruction set for
   > every agent on this site, shared with Claude/Codex/Cursor/etc. Follow it in
   > full, including reading `conversation-context/` at session start.

3. **Session-start rule (put it inside `AGENTS.md`)** — "Before acting, if
   `conversation-context/` exists at the org root, read it in order (README →
   SESSION_SUMMARY → CURRENT_STATE → NEXT_STEPS)." This is what makes *any* agent
   auto-resume a session rather than starting cold.

## Project level: keep the entrypoint lean, point into project-context/

A project repo's auto-loaded agent file (`AGENTS.md` / `CLAUDE.md`) should stay
LEAN: the boot/operating directives that must load every session (e.g. arm the mail
watcher first, escalation rules, deploy-is-manual), the handful of most-used
commands, and POINTERS into `project-context/` for everything else. Put the verbose
durable knowledge - architecture, repo layout, terminology (`glossary.md`), how key
components work, end-to-end testing (`e2e-testing.md`), conventions - in
`project-context/` and reference it ("for architecture read
`project-context/architecture-context.md`"). Do NOT duplicate that knowledge in the
always-loaded file: it bloats every session's context and drifts.

And keep ONE canonical source (per "The pattern" above) - never two separate files
with overlapping content that can disagree. A common mistake is a big `CLAUDE.md`
plus a separate `AGENTS.md` quick-ref that drift apart; symlink or point them at one
canonical file instead.

## Why pointers, not copies
One source of truth can't fall out of sync. If you duplicate the instructions into
each config, they drift and agents diverge. Keep the pointers to one line.

## Notes
- These entrypoint files live at the org root and are often gitignored per site
  (they hold site-specific paths/roster). This template documents the *convention*
  so each site or clone can wire it up the same way.
- Runtime permissions are configured separately, per agent/runtime — the entrypoint
  files carry instructions, not permission settings.
