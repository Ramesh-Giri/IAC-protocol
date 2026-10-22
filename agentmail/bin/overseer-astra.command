#!/bin/zsh
# Launch the configured main seat through the reviewed roster launcher.
# Site-specific identity, model pins and handoffs live in ignored local/ and the roster.
set -eu
IAC_ROOT="${IAC_ROOT:-${0:A:h:h:h}}"
[[ ! -f "$IAC_ROOT/.iac-local.env" ]] || source "$IAC_ROOT/.iac-local.env"
if [[ "${1:-}" == --help || "${1:-}" == -h ]]; then
  print 'Usage: overseer-astra.command [agentmail-launch options]'
  print 'Requires IAC_MAIN_SEAT; the approved roster controls runtime, model and permissions.'
  exit 0
fi
: "${IAC_MAIN_SEAT:?Set IAC_MAIN_SEAT in .iac-local.env or the environment}"
exec "$IAC_ROOT/agentmail/bin/agentmail-launch" \
  -d "${AGENTMAIL_DIR:-$IAC_ROOT/.agent-mail}" \
  --seat "$IAC_MAIN_SEAT" --overseer "$@"
