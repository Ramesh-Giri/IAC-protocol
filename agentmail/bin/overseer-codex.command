#!/bin/zsh
# Hand the OVERSEER seat to Codex when the Claude overseer runs out of budget (rule 23).
# Executed, not typed (rule 13). Opens in the Terminal window it is executed in.
# The overseer is INTERACTIVE: on-request approvals, so Ramesh can approve tmux/ps/git host
# operations it needs (SUPERVISOR_BOOTSTRAP.md). "never" silently denies them; that broke the
# first Codex takeover on 2026-10-07. Children keep "never"; the overseer must not.
cd /Users/darkness/Work/Aureus
HANDOFF="$(ls -t conversation-context/NEXT_MAIN_AGENT_HANDOFF_*.md 2>/dev/null | head -1)"
exec "$(command -v codex)" \
  --sandbox workspace-write --ask-for-approval on-request \
  --add-dir /Users/darkness/Work/Aureus/.agent-mail \
  --add-dir "$HOME/.treehouse" \
  --model gpt-6.1-sol \
  "You are overseer-ramesh, the supervising seat of the IAC network, taking over from a Claude overseer that hit its usage limit (OPERATIONAL_RULES rule 23). FIRST read AGENTS.md and ${HANDOFF} in full: it lists what is merged, every in-flight seat with branch, SHA and brief path, and the next action for each. THEN read agentmail/OPERATIONAL_RULES.md rules 9-23 and overseer-tasks.md. Check your mail with agentmail/bin/mail-read overseer-ramesh (read every DONE/verdict in full; never drain blind). Keep the fleet moving: relaunch stalled Claude seats' tasks on Codex where the task fits, close finished seats, launch reviews and fixes exactly as the handoff describes. You are the ONLY agent that talks to Ramesh; children escalate by mail. Never run gcloud or any GCP command - hand Ramesh paste-ready TYPE-THIS commands. Layer-3 (money, keys, prod data, deploys, publishing, irreversible deletion) goes to Ramesh. Report outcomes, not menus."
