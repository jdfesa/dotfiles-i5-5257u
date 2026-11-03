#!/bin/sh
# Adapted from i3-2310m; see licenses/i3-reference-MIT.txt.
# Launched in Kitty after confirmation; logind authorizes the active local session.
set -eu
export LANG=en_US.UTF-8 LANGUAGE=en_US:en LC_ALL=en_US.UTF-8

dry_run=0
if [ "$#" -eq 2 ] && [ "$1" = --dry-run ]; then
    dry_run=1
    shift
fi
[ "$#" -eq 1 ] || { printf '%s\n' 'Usage: power-action.sh [--dry-run] suspend|reboot|poweroff' >&2; exit 2; }
case $1 in
    suspend) action=$1; capability=CanSuspend ;;
    reboot) action=$1; capability=CanReboot ;;
    poweroff) action=$1; capability=CanPowerOff ;;
    *) exit 2 ;;
esac
[ -t 0 ] || { printf '%s\n' 'A terminal is required for authorization.' >&2; exit 2; }

failure() {
    printf '\n%s\n' "$1" 'No forced action was attempted. Press Enter to close.' >&2
    read -r ignored || true
    exit 1
}

printf 'Requested action: %s\n' "$action"
# systemd v257 made root respect normal block inhibitors in auto mode.
# Older versions must not silently lose that protection when restored elsewhere.
version=$(systemctl --version | sed -n '1s/^systemd \([0-9][0-9]*\)\( .*\)\{0,1\}$/\1/p')
case $version in
    ''|*[!0-9]*) failure 'Cannot verify the systemd version; action cancelled.' ;;
esac
[ "$version" -ge 257 ] || failure 'systemd 257 or newer is required; action cancelled.'
# Fail closed rather than prompting or silently falling back to sudo. Check
# before locking: SSH/inactive sessions or additional authorization requirements
# must not leave a hidden prompt behind a locked screen.
permission=$(busctl --system call org.freedesktop.login1 /org/freedesktop/login1 \
    org.freedesktop.login1.Manager "$capability") || failure 'Cannot check session authorization; action cancelled.'
[ "$permission" = 's "yes"' ] || failure 'Action is unavailable, inhibited, or not authorized for this session.'
if [ "$action" = suspend ] && [ "$dry_run" -eq 0 ]; then
    swaylock -f || failure 'Screen lock failed; suspend cancelled.'
fi
# Keep the existing v257+ inhibitor semantics, now as the real user (no sudo).
# Never retry with --force/-i, check-inhibitors=no, or a privileged fallback.
# --no-ask-password also refuses authentication if policy changes after preflight.
if [ "$dry_run" -eq 1 ]; then
    systemctl --dry-run --no-ask-password --check-inhibitors=auto "$action" || failure 'The requested action failed or was inhibited.'
else
    systemctl --no-ask-password --check-inhibitors=auto "$action" || failure 'The requested action failed or was inhibited.'
fi
