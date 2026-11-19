# Ubuntu Glove Bash integration. Source this file from ~/.bashrc; do not execute it directly.
# It updates READLINE_LINE only after a user chooses a curated command in the GTK palette.

if [[ $- == *i* ]]; then
  ubuntu_glove_palette() {
    local selected
    selected="$(ubuntu-glove --command-palette --print-command)" || return 0
    if [[ -n $selected ]]; then
      READLINE_LINE="$selected"
      READLINE_POINT=${#READLINE_LINE}
    fi
  }

  ubuntu_glove_prompt_hint() {
    local exit_status=$?
    local last_command
    (( exit_status == 0 )) && return 0
    last_command="$(HISTTIMEFORMAT= builtin history 1 2>/dev/null | sed -E 's/^[[:space:]]*[0-9]+[[:space:]]*//')"
    case $exit_status in
      127)
        printf '\nUbuntu Glove: command not found. Check spelling, install its package, or press Ctrl+Space for curated commands.\n' >&2
        ;;
      126)
        printf '\nUbuntu Glove: permission denied. Review ownership and executable permissions before using chmod or sudo.\n' >&2
        ;;
      1)
        if [[ $last_command == apt\ * || $last_command == apt-get\ * ]]; then
          printf '\nUbuntu Glove: package action failed. Run `sudo apt update` first, then review the exact package error.\n' >&2
        else
          printf '\nUbuntu Glove: command exited with status 1. Review its output before retrying.\n' >&2
        fi
        ;;
      *)
        printf '\nUbuntu Glove: command exited with status %s. Review the command output before applying a fix.\n' "$exit_status" >&2
        ;;
    esac
    return 0
  }

  # Ctrl+Space sends Ctrl-@ to Readline. This intentionally has no global desktop shortcut.
  bind -x '"\C-@":ubuntu_glove_palette'

  if [[ ${PROMPT_COMMAND-} != *ubuntu_glove_prompt_hint* ]]; then
    if [[ -n ${PROMPT_COMMAND-} ]]; then
      PROMPT_COMMAND="ubuntu_glove_prompt_hint; ${PROMPT_COMMAND}"
    else
      PROMPT_COMMAND="ubuntu_glove_prompt_hint"
    fi
  fi
fi
