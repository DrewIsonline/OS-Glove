#!/usr/bin/env bash
# Install Ubuntu Glove as a per-user GNOME utility from a reviewed source tree.
set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
STATE_DIR="$DATA_HOME/ubuntu-glove"
APP_DIR="$STATE_DIR/app"
BIN_DIR="$HOME/.local/bin"
USER_UNIT_DIR="$CONFIG_HOME/systemd/user"
WRAPPER="$BIN_DIR/ubuntu-glove"
SERVICE="$USER_UNIT_DIR/ubuntu-glove.service"
ACTION="install"
INSTALL_DEPS=0

usage() {
  cat <<'EOF'
Usage: scripts/install_stack.sh [--enable|--disable|--deps-only] [--install-deps]

  --enable       Validate and install/update Ubuntu Glove for this desktop user.
  --disable      Stop and disable this user's Ubuntu Glove service.
  --install-deps Install required Ubuntu GNOME packages through apt (uses sudo).
  --deps-only    Install packages only (safe to run from SSH or headless setup).

This installer intentionally has no system-wide mode. The user overlay must run
from the logged-in Ubuntu GNOME desktop user session.
EOF
}

while (($#)); do
  case $1 in
    --enable) ACTION="install" ;;
    --disable) ACTION="disable" ;;
    --install-deps) INSTALL_DEPS=1 ;;
    --deps-only) ACTION="deps-only"; INSTALL_DEPS=1 ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

require_runtime() {
  command -v systemctl >/dev/null || { echo "systemctl is required." >&2; exit 1; }
  command -v python3 >/dev/null || { echo "python3 is required." >&2; exit 1; }
  [[ ${EUID:-$(id -u)} -ne 0 ]] || { echo "Do not run this installer as root." >&2; exit 1; }
}

require_graphical_session() {
  if [[ -z ${DISPLAY:-} && -z ${WAYLAND_DISPLAY:-} ]]; then
    echo "No graphical display is available. Run this from a terminal inside the logged-in Ubuntu GNOME desktop session, not SSH." >&2
    exit 1
  fi
}

install_dependencies() {
  local core_packages=(
    python3
    python3-gi
    python3-gi-cairo
    python3-pyatspi
    at-spi2-core
    gir1.2-gtk-4.0
    gir1.2-adw-1
    gir1.2-ayatanaappindicator3-0.1
    gnome-screenshot
  )
  sudo apt-get update
  sudo apt-get install -y "${core_packages[@]}"

  # Optional: GTK4 Layer Shell is available in newer Ubuntu releases (24.10+) or Debian.
  # The app automatically falls back to standard undecorated GTK4 windows if absent.
  if apt-cache show gir1.2-gtk4layershell-1.0 >/dev/null 2>&1; then
    sudo apt-get install -y gir1.2-gtk4layershell-1.0 || true
  fi
}

validate_source() {
  python3 "$PROJECT_DIR/main.py" --check-data
}

write_user_launcher() {
  mkdir -p "$BIN_DIR"
  cat >"$WRAPPER" <<EOF
#!/usr/bin/env bash
exec /usr/bin/python3 "$APP_DIR/main.py" "\$@"
EOF
  chmod 0755 "$WRAPPER"
}

write_user_service() {
  mkdir -p "$USER_UNIT_DIR"
  cat >"$SERVICE" <<EOF
[Unit]
Description=Ubuntu Glove desktop overlay
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR
ExecStart=$WRAPPER
Restart=on-failure
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=graphical-session.target
EOF
}

install_user() {
  require_graphical_session
  validate_source
  mkdir -p "$STATE_DIR"
  chmod 0700 "$STATE_DIR"
  if [[ -L $APP_DIR ]]; then
    echo "Refusing to replace symlinked application directory: $APP_DIR" >&2
    exit 1
  fi
  local staging previous
  staging="$(mktemp -d "$STATE_DIR/.app-staging.XXXXXX")"
  previous="$STATE_DIR/.app-previous"
  trap 'rm -rf -- "$staging"' RETURN
  tar --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='debian' --exclude='tests' -C "$PROJECT_DIR" -cf - . | tar -C "$staging" -xf -
  python3 "$staging/main.py" --check-data
  rm -rf -- "$previous"
  if [[ -d $APP_DIR ]]; then
    mv "$APP_DIR" "$previous"
  fi
  mv "$staging" "$APP_DIR"
  trap - RETURN
  rm -rf -- "$previous"
  write_user_launcher
  write_user_service
  systemctl --user daemon-reload
  systemctl --user enable --now ubuntu-glove.service
  printf '\nInstalled Ubuntu Glove for %s. Local notes remain at: %s/context_notes.db\nOptional Bash support:\n  source "%s/scripts/bashrc_hook.sh"\n\n' "$USER" "$STATE_DIR" "$APP_DIR"
}

disable_user() {
  systemctl --user disable --now ubuntu-glove.service 2>/dev/null || true
  printf 'Ubuntu Glove is disabled for this user. Your notes and configuration were retained.\n'
}

require_runtime
if (( INSTALL_DEPS )); then
  install_dependencies
fi
if [[ $ACTION == disable ]]; then
  disable_user
elif [[ $ACTION == deps-only ]]; then
  printf 'Dependencies installed successfully. To enable the desktop service, log into GNOME and run:\n  bash %s/scripts/install_stack.sh --enable\n' "$PROJECT_DIR"
else
  install_user
fi
