# Power menu

## Entry points and reference

Abrir **Super+Espacio**, buscar **Power menu** o **apagar** y pulsar Enter.
También funciona **Super+Shift+P**. Ambos accesos usan el mismo
`~/.local/bin/mbp-power-menu`; no hay comandos de apagado directos en Fuzzel.
Para que la búsqueda española funcione, Fuzzel incluye `keywords` entre sus
campos de búsqueda. La interfaz continúa en inglés.

El flujo adapta `scripts/power-menu`, `scripts/power-action.sh` y la entrada
`.desktop` del proyecto i3-2310m. Conserva acciones, orden y confirmaciones,
con herramientas propias de Sway: Fuzzel, swaylock, swaymsg y Kitty.
Fuzzel descubre la aplicación; el menú y las confirmaciones usan su modo dmenu
centrado, con los mismos colores/fuente del lanzador y sin daemon adicional.
Se mantiene el orden de opciones, sin caché dmenu ni ejecución de texto libre.
No se instala Rofi ni se importan comandos i3/X11.

## Actions and safety

| Acción | Comportamiento |
|---|---|
| Power off | Confirmación; apagado mediante logind/systemctl |
| Reboot | Confirmación; reinicio mediante logind/systemctl |
| Suspend | Confirmación y autorización; bloquear antes de suspender |
| Log out | Confirmación; salir únicamente de la sesión Sway actual |
| Lock | Bloqueo swaylock inmediato |
| Cancel / Escape | Cancelar sin acción |

Antes de confirmar, guardar el trabajo. `No` o Escape en la confirmación
cancelan. Las selecciones se comparan con una lista fija; texto arbitrario no
se interpreta como shell. El helper rechaza contextos que no sean Wayland/Sway.

Apagado, reinicio y suspensión abren una Kitty para autorización/errores. El
helper exige terminal, systemd >=257 y capacidad logind exactamente `yes`;
`challenge`, `no`, fallo de consulta o bloqueo no provocan fallback sudo.
Se mantienen `--check-inhibitors=auto` y `--no-ask-password`, sin force ni
ignorar inhibidores. Un fallo de bloqueo impide suspender. Los errores quedan
visibles en la terminal hasta Enter; no se afirma éxito por el exit de Kitty.

## Sources and deployment

No se añaden paquetes. Se reutilizan Sway, Kitty, Fuzzel, swaylock y systemd
del [Dependencies](dependencies.md). Fuentes públicas y destinos:

| Fuente | Destino |
|---|---|
| `scripts/power-menu` | `~/.local/bin/mbp-power-menu` |
| `scripts/power-action.sh` | `~/.local/bin/mbp-power-action` |
| `config/power/mbp-power-menu.desktop` | `~/.local/share/applications/mbp-power-menu.desktop` |

El archivo de escritorio usa modo 0644 y los scripts 0755, propietario jd;
enlaces por manifiesto desde `/home/jd/dotfiles-i5-5257u`.
[Deployment](deployment.md) describe simulación, conflictos, backups y rollback.
Es una entrada estándar, no una regla privilegiada ni autostart.
Referencias: [Desktop Entry](https://specifications.freedesktop.org/desktop-entry/latest/recognized-keys.html),
[Fuzzel fields](https://manpages.debian.org/trixie/fuzzel/fuzzel.ini.5.en.html#fields).
MIT de la adaptación conservado en [notices](third-party-notices.md).

## Verification and recovery

```sh
desktop-file-validate ~/.local/share/applications/mbp-power-menu.desktop
fuzzel --check-config
~/.local/bin/mbp-power-menu --dry-run 'Power off'
python3 -m unittest discover -s tests -v
```

El dry-run del menú no abre UI ni llama logind/systemctl. Los tests simulan
todos los comandos de energía, autorizaciones e inhibidores; comprueban
cancelación, confirmaciones, bloqueo antes de suspensión y ausencia de
escalación. No equivalen a apagar/reiniciar/suspender realmente el MacBook.
La prueba física segura es abrir desde Fuzzel y cerrar con Escape.

Para retirar solo el acceso de Fuzzel, revisar su entrada del manifiesto y
verificar el enlace .desktop antes de quitarlo. Un rollback por journal revierte
todas las entradas de esa invocación, no solo el menú. Conservar los helpers y
el atajo si todavía se utilizan; Fuzzel, Kitty y swaylock son compartidos con
otros componentes. El menú no genera caché dmenu ni estado persistente propio.
