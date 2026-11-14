#!/bin/sh
# Operate only an explicitly selected, protected and non-autoconnecting AP.
set -eu

fail() {
    printf '%s\n' "$*" >&2
    exit 1
}

usage() {
    printf '%s\n' "Usage: mbp-wifi-hotspot status|start|stop PROFILE_UUID"
}

if [ "$#" -eq 1 ] && [ "$1" = "--help" ]; then usage; exit 0; fi
if [ "$#" -ne 2 ]; then usage >&2; exit 2; fi
action=$1
profile=$2
case "$action" in
    status|start|stop) ;;
    *) usage >&2; exit 2 ;;
esac
if [ "${#profile}" -ne 36 ]; then fail "Expected a NetworkManager profile UUID."; fi
printf '%s\n' "$profile" | grep -Eq '^[a-fA-F0-9]{8}(-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}$' ||
    fail "Expected a NetworkManager profile UUID."

if [ "$action" != status ]; then
    if [ -n "${SSH_CONNECTION:-}${SSH_CLIENT:-}${SSH_TTY:-}" ] || ! [ -t 0 ]; then
        fail "Change the hotspot only from a local interactive terminal."
    fi
fi

field() {
    LC_ALL=C nmcli --wait 5 --escape no --get-values "$1" connection show uuid "$profile"
}
[ "$(field connection.type)" = 802-11-wireless ] &&
    [ "$(field 802-11-wireless.mode)" = ap ] ||
    fail "The selected profile is not a Wi-Fi access point."

active() {
    list=$(LC_ALL=C nmcli --wait 5 --get-values UUID connection show --active) ||
        fail "Could not read active NetworkManager connections."
    printf '%s\n' "$list" | grep -Fxiq -- "$profile"
}
require_safe_start() {
    [ "$(field connection.autoconnect)" = no ] &&
        [ "$(field ipv4.method)" = shared ] ||
        fail "The profile must use IPv4 sharing and have autoconnect disabled."
    case "$(field 802-11-wireless-security.key-mgmt)" in
        wpa-psk|sae) ;;
        *) fail "The profile must use WPA Personal security." ;;
    esac
}

case "$action" in
    status)
        if active; then printf '%s\n' "Hotspot is active."; else printf '%s\n' "Hotspot is inactive."; fi
        ;;
    start)
        require_safe_start
        if active; then printf '%s\n' "Hotspot is already active."; exit 0; fi
        printf '%s' "Starting the hotspot can disconnect Wi-Fi. Continue [y/N]? " >&2
        IFS= read -r answer || exit 1
        case "$answer" in y|Y) ;; *) exit 0 ;; esac
        exec nmcli --wait 30 connection up uuid "$profile"
        ;;
    stop)
        if ! active; then printf '%s\n' "Hotspot is already inactive."; exit 0; fi
        exec nmcli --wait 30 connection down uuid "$profile"
        ;;
esac
