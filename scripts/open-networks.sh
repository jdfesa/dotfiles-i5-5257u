#!/bin/sh
# One on-demand NetworkManager panel, shared by the bar, keyboard and launcher.
# Passwords and SSIDs stay in NetworkManager/UI, never in arguments or logs here.
set -eu
export LC_ALL=C.UTF-8

usage() {
    printf '%s\n' 'Usage: mbp-open-networks [--check|--edit|--help]'
}

case $# in
    0) mode=connect ;;
    1) case $1 in
        --check) mode=check ;;
        --edit) mode=edit ;;
        --help) usage; exit 0 ;;
        *) usage >&2; exit 2 ;;
       esac ;;
    *) usage >&2; exit 2 ;;
esac

notice() {
    printf '%s\n' "$1" >&2
    if [ -n "${WAYLAND_DISPLAY:-}" ] && command -v notify-send >/dev/null 2>&1; then
        timeout 3 notify-send -a 'Wi-Fi networks' "$1" >/dev/null 2>&1 || true
    fi
}

for tool in kitty flock nmtui nmcli; do
    command -v "$tool" >/dev/null 2>&1 || {
        notice "Required command is missing: $tool"
        exit 127
    }
done
running=$(nmcli --wait 5 --terse --fields RUNNING general 2>/dev/null) || running=
if [ "$running" != running ]; then
    notice 'NetworkManager is not available. Check its service before reconnecting.'
    exit 1
fi

if [ "$mode" = check ]; then
    printf '%s\n' 'NetworkManager: running'
    printf 'Wi-Fi radio: '
    nmcli --wait 5 --terse --fields WIFI general
    exit 0
fi

[ -n "${WAYLAND_DISPLAY:-}" ] && [ -n "${XDG_RUNTIME_DIR:-}" ] || {
    notice 'Open this panel from Sway. From a TTY, run: nmtui connect'
    exit 1
}
umask 077
if [ "$mode" = edit ]; then
    command -v nm-connection-editor >/dev/null 2>&1 || {
        notice 'The advanced NetworkManager connection editor is not installed.'
        exit 127
    }
    exec nm-connection-editor
fi

# Lock lifetime follows the panel. A second click focuses it instead of spawning.
exec 9>"$XDG_RUNTIME_DIR/mbp-networks.lock"
if ! flock -n 9; then
    if [ -n "${SWAYSOCK:-}" ] && command -v swaymsg >/dev/null 2>&1; then
        swaymsg '[app_id="^mbp-networks$"] focus' >/dev/null 2>&1 || true
    fi
    exit 0
fi

# One fresh scan per opening, no timer/polling and no automatic activation.
# A successful list request can still be empty when the driver cannot scan.
# Use BSSID so hidden SSIDs are not mistaken for an absence of access points.
if ! access_points=$(nmcli --wait 10 --terse --fields BSSID device wifi list --rescan yes 2>/dev/null); then
    notice 'Fresh Wi-Fi scan unavailable; showing NetworkManager cached networks.'
elif [ -z "$access_points" ]; then
    radio=$(nmcli --wait 5 --terse --fields WIFI general 2>/dev/null) || radio=unknown
    case $radio in
        disabled)
            notice 'Wi-Fi radio is off. To enable it deliberately, run: nmcli radio wifi on'
            ;;
        *)
            notice 'No Wi-Fi access points were returned. Check range and radio; if networks disappeared after suspend, see docs/wifi/driver-recovery.md for driver recovery.'
            ;;
    esac
fi

# The explicit command replaces Kitty's default login Zsh. Do not invoke nmtui
# as a login-shell multicall alias: a leading '-' breaks its dispatch.
# Kitty does not propagate the child's exit status. Keep a private per-opening
# result, not UI output, so real nmtui errors remain visible. The client writes
# on exit, including a clean cancellation when the WM sends HUP/TERM.
panel_state=$(mktemp -d "$XDG_RUNTIME_DIR/mbp-networks.XXXXXX")
trap 'rm -f "$panel_state/status"; rmdir "$panel_state"' 0
tui_command='
trap '\''code=$?; printf "%s\n" "$code" > "$1"'\'' 0
trap "exit 0" HUP TERM
nmtui connect
'
if kitty --class=mbp-networks --title='Wi-Fi networks' --override=tab_bar_min_tabs=2 \
    sh -c "$tui_command" mbp-networks "$panel_state/status"; then
    if [ -r "$panel_state/status" ] && [ "$(cat "$panel_state/status")" = 0 ]; then
        exit 0
    fi
fi
notice 'The Wi-Fi panel failed. Run nmtui connect in a terminal to inspect the error.'
exit 1
