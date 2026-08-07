#!/bin/sh

set -eu

brightness_helper=/usr/sbin/xfpm-power-backlight-helper
target_brightness=555

# No se debe intentar controlar la pantalla física desde una sesión XRDP/SSH.
case "${DISPLAY:-}" in
  :0|:0.0) ;;
  *) exit 0 ;;
esac

# Da tiempo a que la sesión local y PolicyKit queden activos después del login.
sleep 5

if [ ! -x "$brightness_helper" ]; then
  echo "No se encontró el ayudante de brillo de XFCE: $brightness_helper" >&2
  exit 1
fi

exec pkexec --disable-internal-agent \
  "$brightness_helper" --set-brightness "$target_brightness"

