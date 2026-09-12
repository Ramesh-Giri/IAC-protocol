#!/bin/zsh
# Attach a VISIBLE Terminal window to a project's agent fleet.
# Executed directly by Terminal (open -a Terminal), so no keystrokes are typed
# into a shell -- the oh-my-zsh update prompt used to swallow the first
# character of an AppleScript-typed command ("tmux" -> "mux", 2026-09-12).
SESSION="${1:-circle}"
exec /opt/homebrew/bin/tmux attach -t "$SESSION"
