#!/bin/zsh
# Attach to the configured fleet window; no sessions or panes are created.
# Site-specific defaults live in ignored .iac-local.env and local/.
set -eu
IAC_ROOT="${IAC_ROOT:-${0:A:h:h:h}}"
[[ ! -f "$IAC_ROOT/.iac-local.env" ]] || source "$IAC_ROOT/.iac-local.env"
if [[ "${1:-}" == --help || "${1:-}" == -h ]]; then
  print 'Usage: fleet-watch.command [session:window] (default: IAC_FLEET_WINDOW or fleet:seats)'
  exit 0
fi
if (( $# > 1 )) || [[ "${1:-}" == -* ]]; then
  print -u2 'Usage: fleet-watch.command [session:window]'
  exit 2
fi
exec tmux attach-session -t "${1:-${IAC_FLEET_WINDOW:-fleet:seats}}"
