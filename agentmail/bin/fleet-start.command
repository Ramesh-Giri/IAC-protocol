#!/bin/zsh
# Start a project's agent fleet in a VISIBLE Terminal window and stay attached.
#
# Why a .command file: AppleScript `do script` TYPES the command into a shell,
# and any zsh startup prompt eats the first keystroke ("tmux"->"mux"). A
# .command file is EXECUTED, so nothing can be swallowed. 2026-09-12.
set -e
PROJECT="${1:-circle}"
ROOT="/Users/darkness/Work/Aureus"
TMUX=/opt/homebrew/bin/tmux
cd "$ROOT"

$TMUX kill-session -t "$PROJECT" 2>/dev/null || true
# `keep` holder window: closing an agent window can otherwise kill the server.
$TMUX new-session -d -s "$PROJECT" -n keep

for SEAT in circle-ramesh circle-review-ramesh; do
  echo "launching $SEAT ..."
  "$ROOT/agentmail/bin/agentmail-launch" --seat "$SEAT" \
      --terminal tmux --apply --skip-permissions || echo "  FAILED: $SEAT"
done

echo
echo "windows:"; $TMUX list-windows -t "$PROJECT"
echo
echo "Attaching. Ctrl-b n = next agent, Ctrl-b w = pick from list, Ctrl-b d = detach."
sleep 2
exec $TMUX attach -t "$PROJECT"
