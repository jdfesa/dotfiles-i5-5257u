# Trackpad gestures

## Hardware and support

Debian 13 detecta el trackpad integrado ISO del MacBookPro12,1 (`05ac:0273`)
con el controlador `bcm5974` del kernel. En la sesión Wayland de referencia,
Sway 1.10.1 y libinput 1.28.1 lo exponen como `1452:627:bcm5974`.
No se necesitan controladores externos, permisos sobre el grupo `input`,
ni demonios de gestos.

La sesión ya usa toque para hacer clic, clic secundario con dos dedos
(`clickfinger`), desplazamiento natural con dos dedos y desactivación temporal
al escribir. El módulo de gestos no cambia estos ajustes ni la aceleración.

Fuentes: [Linux bcm5974 driver](https://github.com/torvalds/linux/blob/v6.12/drivers/input/mouse/bcm5974.c),
[libinput gestures](https://wayland.freedesktop.org/libinput/doc/1.28.1/gestures.html)
y [Sway configuration manual](https://manpages.debian.org/trixie/sway/sway.5.en.html).

## Workspace swipes

| Gesto | Acción |
|---|---|
| Tres dedos hacia la izquierda | Siguiente escritorio de la pantalla actual |
| Tres dedos hacia la derecha | Escritorio anterior de la pantalla actual |

El cambio se realiza al terminar el gesto, entre escritorios existentes;
no crea escritorios ni mueve ventanas. Solo se asignan deslizamientos
horizontales de tres dedos para el trackpad comprobado. No se asigna el
cambio de escritorio con cuatro dedos, con un deslizamiento vertical ni con
una pinza. El zoom con pinza depende de la aplicación. Otro trackpad no
hereda el gesto; tampoco se replica la animación de macOS.

## Configuration and restore

El módulo [`trackpad-gestures.conf`](../config/sway/trackpad-gestures.conf)
limita `bindgesture` al identificador del dispositivo. `swipe:3` exige tres
dedos; `--exact` exige que coincida la dirección sin otras direcciones.

```text
bindgesture --exact --input-device=1452:627:bcm5974 swipe:3:left workspace next_on_output
bindgesture --exact --input-device=1452:627:bcm5974 swipe:3:right workspace prev_on_output
```

Tras reinstalar, recuperar una revisión de los dotfiles que incluya el módulo
y aplicar el manifiesto principal como `jd` según [Restore guide](restore-guide.md).
El manifiesto crea el enlace `~/.config/sway/trackpad-gestures.conf`; Sway lo
incluye antes de `local.conf`. No copiar el módulo al override ni instalar
un servicio adicional.

Desde la sesión de Sway, comprobar el enlace, validar y recargar:

```sh
readlink -f ~/.config/sway/trackpad-gestures.conf
sway --validate --config ~/.config/sway/config
swaymsg reload
```

El enlace debe resolver a `config/sway/trackpad-gestures.conf` dentro del
checkout canónico. Ante conflictos, consultar
[Configuration deployment](deployment.md).

## Verification

Desde la sesión de Sway:

```sh
swaymsg -t get_inputs
swaymsg -t get_workspaces
```

1. Confirmar que el identificador aparece como `touchpad`.
2. Mantener una ventana en cada uno de tres escritorios de la misma pantalla
   (por ejemplo, 1, 2 y 3) y situarse en el del medio. Con el puntero fuera
   de la barra, deslizar tres dedos a la izquierda y comprobar que se enfoca
   el 3. Volver al 2 y deslizar a la derecha para comprobar que se enfoca el 1.
3. Comprobar que un deslizamiento horizontal con cuatro dedos o vertical con
   tres no cambia de escritorio, que el desplazamiento de dos dedos y los clics
   siguen funcionando y que la pinza funciona en una aplicación Wayland que la admita.

La detección del dispositivo y el parser de Sway no prueban el gesto físico.
Si no hay cambio, revisar primero el identificador, que existan otros
escritorios en la pantalla enfocada y que el puntero no esté sobre Swaybar.

## Disable the swipes

Para mantener los demás ajustes y desactivar solo los dos gestos, añadir
a `private/sway/local.conf`:

```text
unbindgesture --exact --input-device=1452:627:bcm5974 swipe:3:left
unbindgesture --exact --input-device=1452:627:bcm5974 swipe:3:right
```

Validar con `sway --validate --config ~/.config/sway/config` y aplicar con
`swaymsg reload`. Quitar las dos líneas y recargar para recuperarlos.
