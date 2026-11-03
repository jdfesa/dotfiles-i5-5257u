#!/bin/sh

set -eu

brightness_helper=/usr/sbin/xfpm-power-backlight-helper
target_brightness=555

# The local recovery display is the only eligible target.
case "${DISPLAY:-}" in
  :0|:0.0) ;;
  *) exit 0 ;;
esac

# Allow the local session and its PolicyKit agent to initialize.
sleep 5

if [ ! -x "$brightness_helper" ]; then
  printf 'Brightness helper not found: %s\n' "$brightness_helper" >&2
  exit 1
fi

exec pkexec --disable-internal-agent \
  "$brightness_helper" --set-brightness "$target_brightness"
