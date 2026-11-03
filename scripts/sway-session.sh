#!/bin/sh
# Start only once per Sway session, never during config validation or reload.
set -eu
[ "${XDG_SESSION_TYPE:-}" = wayland ] && [ -n "${SWAYSOCK:-}" ] || exit 0
exec 9>"${XDG_RUNTIME_DIR:?}/mbp-sway-session.lock"
flock -n 9 || exit 0

# Debian's config.d imports WAYLAND_DISPLAY/SWAYSOCK into D-Bus/systemd.
# Keep the existing PulseAudio server; do not start the XFCE power manager.
mako &
notify_pid=$!
swayidle -w -C "${XDG_CONFIG_HOME:-$HOME/.config}/swayidle/config" &
idle_pid=$!
/usr/libexec/polkit-mate-authentication-agent-1 &
polkit_pid=$!
cleanup() {
    kill "$idle_pid" "$notify_pid" "$polkit_pid" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 0' HUP INT TERM
# IPC closes at compositor exit; this also cleans up the session children.
swaymsg -m -t subscribe '["shutdown"]' >/dev/null 2>&1 || true
