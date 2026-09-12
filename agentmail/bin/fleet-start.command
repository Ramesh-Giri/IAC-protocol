#!/bin/zsh
# Start a project's agent fleet in a VISIBLE Terminal window, ALL SEATS ON SCREEN
# AT ONCE as split panes -- never as windows/tabs you have to cycle through.
# Ramesh, 2026-09-12: "there are 3 seats in terminal but in a tab bar.. dint i
# tell u to show them separately". Seeing one seat at a time is not seeing them.
#
# Why a .command file: AppleScript `do script` TYPES the command into a shell and
# any zsh startup prompt eats the first keystroke ("tmux" -> "mux"). A .command
# file is EXECUTED, so nothing can be swallowed.
set -e
PROJECT="${1:-circle}"
ROOT="/Users/darkness/Work/Aureus"
TMUX=/opt/homebrew/bin/tmux
SEATS=(circle-ramesh circle-review-ramesh)
cd "$ROOT"

$TMUX kill-session -t "$PROJECT" 2>/dev/null || true
# `keep` holder window: closing an agent pane must not take the server down.
$TMUX new-session -d -s "$PROJECT" -n keep

for SEAT in $SEATS; do
  echo "launching $SEAT ..."
  "$ROOT/agentmail/bin/agentmail-launch" --seat "$SEAT" \
      --terminal tmux --apply --skip-permissions || echo "  FAILED: $SEAT"
  sleep 2
done

# Collapse every seat window into ONE window of side-by-side panes.
FIRST="${SEATS[1]}"
for SEAT in ${SEATS[@]:1}; do
  $TMUX join-pane -s "$PROJECT:$SEAT" -t "$PROJECT:$FIRST" -h 2>/dev/null || true
done
$TMUX select-layout -t "$PROJECT:$FIRST" tiled 2>/dev/null || true
$TMUX rename-window -t "$PROJECT:$FIRST" agents 2>/dev/null || true
$TMUX set -t "$PROJECT" pane-border-status top 2>/dev/null || true
$TMUX set -t "$PROJECT" pane-border-format " #{pane_index}: #{pane_title} " 2>/dev/null || true

# The boot prompt does not always auto-submit in the pane; send it explicitly.
i=1
for SEAT in $SEATS; do
  BOOT="You are IAC seat ${SEAT}, role child. Mail root: $ROOT/.agent-mail. Helpers: $ROOT/agentmail/bin. Read roster.json for your project authority and delegation. Reply using --in-reply-to with the incoming message ID. Escalate every decision to overseer-ramesh BY MAIL; never prompt a human. Arm your mail watcher (persistent) FIRST, then check your mail and get oriented."
  $TMUX send-keys -t "$PROJECT:agents.$i" -l "$BOOT" 2>/dev/null || true
  sleep 1
  $TMUX send-keys -t "$PROJECT:agents.$i" Enter 2>/dev/null || true
  i=$((i+1))
done

echo
echo "Ctrl-b o = next pane · Ctrl-b z = zoom one pane full-screen (again to unzoom) · Ctrl-b d = detach"
sleep 2
exec $TMUX attach -t "$PROJECT"
