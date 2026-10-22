#!/bin/zsh
# Launch explicitly named roster seats and join their captured panes into one fleet window.
# Depends on tmux, Python and agentmail-launch; creates only its holder and requested seats.
# Site-specific settings live in ignored .iac-local.env and local/.
set -eu
IAC_ROOT="${IAC_ROOT:-${0:A:h:h:h}}"
[[ ! -f "$IAC_ROOT/.iac-local.env" ]] || source "$IAC_ROOT/.iac-local.env"
if [[ "${1:-}" == --help || "${1:-}" == -h ]]; then
  print 'Usage: fleet-start.command <seat> [seat ...]'
  print 'Settings: IAC_ROOT, AGENTMAIL_DIR, IAC_FLEET_SESSION (default fleet).'
  print 'Launches with normal runtime permissions; preserves existing sessions and panes.'
  exit 0
fi
if (( $# == 0 )); then
  print -u2 'Pass the approved roster seat IDs explicitly; see fleet-start.command --help.'
  exit 2
fi
MAIL_ROOT="${AGENTMAIL_DIR:-$IAC_ROOT/.agent-mail}"
SESSION="${IAC_FLEET_SESSION:-fleet}"
# Resolve the complete launch plan before creating any session or pane.
PLAN="$(python3 - "$MAIL_ROOT" "$SESSION" "$@" <<'PYPLAN'
import json, re, sys
from pathlib import Path
root, session, *seats = sys.argv[1:]
valid = lambda value: isinstance(value, str) and re.fullmatch(r"[a-z0-9][a-z0-9_-]*", value)
try:
    roster = json.loads((Path(root) / "roster.json").read_text())["agents"]
    if not valid(session) or len(set(seats)) != len(seats):
        raise ValueError("invalid session or duplicate seat")
    for seat in seats:
        if not valid(seat) or seat not in roster:
            raise ValueError("unknown or invalid requested seat")
        project = roster[seat].get("project")
        if not valid(project):
            raise ValueError("invalid roster project")
        print(f"{seat}|{project}")
except (OSError, KeyError, ValueError) as exc:
    sys.exit(f"fleet-start: {exc}")
PYPLAN
)"
LAUNCH_ARGS=()
for SEAT in "$@"; do LAUNCH_ARGS+=(--seat "$SEAT"); done
# Launcher preflight verifies local ownership, home paths and runtime safeguards.
"$IAC_ROOT/agentmail/bin/agentmail-launch" -d "$MAIL_ROOT" "${LAUNCH_ARGS[@]}" --terminal tmux
if ! tmux has-session -t "=$SESSION" 2>/dev/null; then
  HOLDER="$(tmux new-session -d -s "$SESSION" -n seats -P -F '#{pane_id}')"
  tmux select-pane -t "$HOLDER" -T fleet-holder
elif ! tmux display-message -p -t "${SESSION}:seats" '#{window_id}' >/dev/null 2>&1; then
  print -u2 "Existing session $SESSION has no seats window; preserve it and configure the viewed window first."
  exit 1
fi
"$IAC_ROOT/agentmail/bin/agentmail-launch" -d "$MAIL_ROOT" "${LAUNCH_ARGS[@]}" --terminal tmux --apply
while IFS='|' read -r SEAT PROJECT; do
  PANE="$(tmux display-message -p -t "${PROJECT}:${SEAT}" '#{pane_id}')"
  tmux join-pane -s "$PANE" -t "${SESSION}:seats" -h
  tmux select-layout -t "${SESSION}:seats" tiled >/dev/null
done <<< "$PLAN"
tmux set-option -t "$SESSION" pane-border-status top
tmux set-option -t "$SESSION" pane-border-format ' #{pane_index}: #{pane_title} '
exec tmux attach-session -t "${SESSION}:seats"
