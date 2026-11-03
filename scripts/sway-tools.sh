#!/bin/sh
# On-demand tools only. Adapted interaction conventions from i3-2310m.
set -eu
case ${1:-} in
    networks)
        exec "$HOME/.local/bin/mbp-open-networks" ;;
    audio)
        exec kitty --class=mbp-mixer --title='Audio mixer' alsamixer ;;
    calendar)
        exec "$HOME/.local/bin/mbp-calendar" ;;
    updates)
        exec kitty --class=mbp-updates --title='APT updates (cached metadata)' \
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
    *) printf '%s\n' 'Usage: mbp-sway-tools networks|audio|calendar|updates|browser|help|screenshot' >&2; exit 2 ;;
esac
