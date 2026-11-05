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
| Cuatro dedos hacia la izquierda | Siguiente escritorio de la pantalla actual |
| Cuatro dedos hacia la derecha | Escritorio anterior de la pantalla actual |

El cambio se realiza al terminar el gesto, entre escritorios existentes;
no crea escritorios ni mueve ventanas. Solo se asignan deslizamientos
horizontales de cuatro dedos y solo para el identificador comprobado.
Otro trackpad, incluso una variante con otro identificador, no hereda el gesto.
No se asignan pinzas ni gestos verticales: el zoom con pinza depende de la
aplicación. No se replica Mission Control, Force Click ni la animación de macOS.

El manifiesto enlaza `config/sway/trackpad-gestures.conf` y Sway lo incluye
antes de `local.conf`. Aplicar los enlaces y recargar según
[Configuration deployment](deployment.md); no copiar el módulo al override.

## Verification

Desde la sesión de Sway:

```sh
swaymsg -t get_inputs
swaymsg -t get_workspaces
```

1. Confirmar que el identificador aparece como `touchpad`.
2. Mantener una ventana en cada uno de tres escritorios de la misma pantalla
   (por ejemplo, 1, 2 y 3) y situarse en el del medio. Con el puntero fuera
   de la barra, deslizar cuatro dedos a la izquierda y comprobar que se enfoca
   el 3. Volver al 2 y deslizar a la derecha para comprobar que se enfoca el 1.
3. Comprobar que un deslizamiento vertical o de tres dedos no cambia de
   escritorio, que el desplazamiento de dos dedos y los clics siguen funcionando
   y que la pinza aún funciona en una aplicación Wayland que la admita.

En el equipo de referencia se verificó físicamente el cambio del escritorio 2
al 3 hacia la izquierda y del 2 al 1 hacia la derecha con cuatro dedos. Con tres
no se cambió de escritorio, tal como se espera con este perfil.

La detección del dispositivo y el parser de Sway no prueban el gesto físico.
Si no hay cambio, revisar primero el identificador, que existan otros
escritorios en la pantalla enfocada y que el puntero no esté sobre Swaybar.

## Disable the swipes

Para mantener los demás ajustes y desactivar solo los dos gestos, añadir
a `private/sway/local.conf`:

```text
unbindgesture --exact --input-device=1452:627:bcm5974 swipe:4:left
unbindgesture --exact --input-device=1452:627:bcm5974 swipe:4:right
```

Validar con `sway --validate --config ~/.config/sway/config` y aplicar con
`swaymsg reload`. Quitar las dos líneas y recargar para recuperarlos.
