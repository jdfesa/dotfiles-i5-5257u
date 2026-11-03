#!/bin/sh
# Locate the CPU package sensor once at bar startup, not on every refresh.
set -eu
cache="$HOME/.cache/mbp-sway"
mkdir -p -m 700 "$cache"
sensor=""
for device in /sys/class/hwmon/hwmon*; do
    [ -r "$device/name" ] || continue
    IFS= read -r name < "$device/name" || continue
    if [ "$name" = coretemp ] && [ -r "$device/temp1_input" ]; then
        sensor="$device/temp1_input"
        break
    fi
done
if [ -z "$sensor" ]; then
    for zone in /sys/class/thermal/thermal_zone*; do
        [ -r "$zone/type" ] || continue
        IFS= read -r name < "$zone/type" || continue
        if [ "$name" = x86_pkg_temp ] && [ -r "$zone/temp" ]; then
            sensor="$zone/temp"
            break
        fi
    done
fi
if [ -n "$sensor" ]; then
    ln -sfn "$sensor" "$cache/cpu-temperature"
else
    # An unreadable path produces an honest unavailable indicator, not 0°C.
    rm -f "$cache/cpu-temperature"
fi
if [ ! -f "$cache/weather.txt" ] ||
   [ -n "$(find "$cache/weather.txt" -mmin +180 -print)" ]; then
    printf '☁ --°C\n' > "$cache/weather.txt"
fi
# Avoid repeated ALSA error logs while the external adapter is unplugged.
# Device presence is checked at startup only; reload i3 after connecting it.
config="$HOME/.config/status/i3status.conf"
if ! grep -q '\[.*\]' /proc/asound/cards 2>/dev/null; then
    awk '$0 != "order += \"volume master\""' "$config" > "$cache/i3status-no-audio.conf"
    config="$cache/i3status-no-audio.conf"
fi
# Replace this startup shell with native i3status; the click adapter is separate.
exec i3status -c "$config" "$@"
