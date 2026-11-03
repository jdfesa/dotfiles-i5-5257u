# Keyboard backlight

## Driver and control

El MacBookPro12,1 dispone de retroiluminación controlada por `applesmc`,
incluido en el kernel de Debian 13. En el equipo se verificó
`smc::kbd_backlight`, con rango 0–255, y encendido físico mediante UPower.
No requiere un controlador externo, un kernel alternativo ni un servicio nuevo.

UPower expone `GetBrightness`, `GetMaxBrightness` y `SetBrightness` en
`org.freedesktop.UPower.KbdBacklight`. `mbp-sway-tools` utiliza esa interfaz
del servicio existente como `jd`, con llamadas acotadas a 2 s y un bloqueo
por usuario para serializar pulsaciones. Solo se ejecuta al usar el atajo.

El paquete Debian de `brightnessctl` permite escribir LED mediante el grupo
`input`; la cuenta no pertenece a ese grupo. No añadirla, no usar sudo
en los atajos y no ampliar permisos de sysfs. El brillo de pantalla conserva
su control independiente con `brightnessctl -d intel_backlight`.

## Keyboard shortcuts

- F5 reduce y F6 aumenta el brillo del teclado; según el modo Fn, usar Fn+F5/F6.
- Los eventos son `XF86KbdBrightnessDown` y `XF86KbdBrightnessUp`.
- Cada pulsación ajusta aproximadamente el 10 % del máximo, redondeado hacia
  arriba; los extremos se limitan a 0 y al máximo. El nivel 0 apaga el teclado.
- No se fija un nivel al iniciar ni al recargar Sway y no se añade ajuste
  automático por luz ambiente ni sondeo periódico.

La ayuda y la tabla completa están en [Keyboard shortcuts](keybindings.md).

## Verification and recovery

Consultar sin modificar el nivel:

```sh
busctl --system --timeout=2s call org.freedesktop.UPower \
  /org/freedesktop/UPower/KbdBacklight \
  org.freedesktop.UPower.KbdBacklight GetBrightness
```

Verificación física realizada en la sesión Sway del equipo: F5/F6 actúan
directamente, sin Fn, y permiten subir, bajar y apagar la iluminación.
Una lectura aceptada por D-Bus no sustituye observar la iluminación física.
Repetir la comprobación después de un nuevo login y, al validar suspensión,
después de reanudar. No se presupone persistencia entre reinicios.

Los enlaces existentes de `mbp-sway-tools` y la configuración siguen apuntando
al checkout canónico; no se requiere otro manifiesto ni enlaces nuevos.
Los respaldos de fuentes se conservan fuera del checkout. Ante un fallo,
restaurar solo los archivos afectados y validar antes de recargar; no cambiar
controladores ni permisos para ocultar el error.

## References

- [UPower keyboard backlight interface](https://upower.freedesktop.org/docs/KbdBacklight.html).
- [brightnessctl Debian manual](https://manpages.debian.org/trixie/brightnessctl/brightnessctl.1.en.html).
