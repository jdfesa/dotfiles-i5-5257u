#!/bin/sh
# On-demand tools only. Adapted interaction conventions from i3-2310m.
set -eu

# UPower owns the LED: no raw sysfs writes, sudo or input-group membership.
read_keyboard_level() {
    response=$(busctl --system --timeout=2s call org.freedesktop.UPower \
        /org/freedesktop/UPower/KbdBacklight \
        org.freedesktop.UPower.KbdBacklight "$1") || return 1
    case $response in
        "i "*) level=${response#i } ;;
        *) return 1 ;;
    esac
    case $level in ''|*[!0-9]*) return 1 ;; esac
    case $level in 0|[1-9]*) ;; *) return 1 ;; esac
    [ "${#level}" -le 10 ] && [ "$level" -le 2147483647 ] || return 1
    printf '%s\n' "$level"
}

case ${1:-} in
    keyboard-brightness-up|keyboard-brightness-down)
        [ "$#" -eq 1 ] || { printf '%s\n' 'Keyboard brightness takes no extra arguments.' >&2; exit 2; }
        umask 077
        exec 9>"${XDG_RUNTIME_DIR:?}/mbp-keyboard-backlight.lock"
        flock -w 1 9 || { printf '%s\n' 'Keyboard backlight is busy.' >&2; exit 1; }
        maximum=$(read_keyboard_level GetMaxBrightness) &&
        current=$(read_keyboard_level GetBrightness) || {
            printf '%s\n' 'Could not read keyboard backlight from UPower.' >&2; exit 1;
        }
        [ "$maximum" -gt 0 ] && [ "$current" -le "$maximum" ] || {
            printf '%s\n' 'Invalid keyboard backlight range.' >&2; exit 1;
        }
        step=$(( (maximum + 9) / 10 ))
        case $1 in
            keyboard-brightness-up) target=$((current + step)) ;;
            keyboard-brightness-down) target=$((current - step)) ;;
        esac
        [ "$target" -ge 0 ] || target=0
        [ "$target" -le "$maximum" ] || target=$maximum
        [ "$target" -ne "$current" ] || exit 0
        exec busctl --system --timeout=2s call org.freedesktop.UPower \
            /org/freedesktop/UPower/KbdBacklight \
            org.freedesktop.UPower.KbdBacklight SetBrightness i "$target" ;;
    networks)
        exec "$HOME/.local/bin/mbp-open-networks" ;;
    audio)
        exec kitty --class=mbp-mixer --title='Audio mixer' --override=tab_bar_min_tabs=2 alsamixer ;;
    calendar)
        exec "$HOME/.local/bin/mbp-calendar" ;;
    updates)
        exec kitty --class=mbp-updates --title='APT updates (cached metadata)' --override=tab_bar_min_tabs=2 \
            sh -c 'apt list --upgradable; printf "\nRead-only; no refresh or installation. Press Enter to close.\n"; read -r ignored' ;;
    browser)
        # Resolve the configured XDG default; do not pin a browser executable.
        browser=$(xdg-settings get default-web-browser)
        [ -n "$browser" ] || { printf '%s\n' 'No default web browser is configured.' >&2; exit 1; }
        exec gtk-launch -- "$browser" ;;
    help)
        wmenu -i -l 20 -p Shortcuts < "${XDG_CONFIG_HOME:-$HOME/.config}/sway/keybindings-help.txt" >/dev/null || true ;;
    screenshot)
        # No persistent screenshots or fixed filenames containing private pixels.
        geometry=$(slurp) || exit 0
        [ -n "$geometry" ] || exit 0
        # A private temporary file avoids a failed producer leaving wl-copy alive.
        shot=$(mktemp "${XDG_RUNTIME_DIR:?}/mbp-shot.XXXXXX")
        trap 'rm -f "$shot"' EXIT
        grim -g "$geometry" "$shot"
        wl-copy --type image/png < "$shot" ;;
    *) printf '%s\n' 'Usage: mbp-sway-tools networks|audio|calendar|updates|browser|help|screenshot|keyboard-brightness-up|keyboard-brightness-down' >&2; exit 2 ;;
esac
