# Kitty setup

## Installation and integration

Terminal principal de Sway con Zsh de login. Versión de referencia: Kitty
0.41.1-2+deb13u2, Debian 13 amd64. [Debian package](https://packages.debian.org/trixie/kitty),
[CLI](https://manpages.debian.org/trixie/kitty/kitty.1.en.html) y
[Configuration](https://manpages.debian.org/trixie/kitty/kitty.conf.5.en.html).

```sh
apt-get -s --no-install-recommends --no-remove install kitty
sudo apt-get --no-install-recommends --no-remove install kitty
sudo update-alternatives --set x-terminal-emulator /usr/bin/kitty
```

APT administra binarios, shell integration y terminfo. Los archivos
`config/kitty/kitty.conf` y `theme.conf` se enlazan individualmente a
`~/.config/kitty/`, modo 0644. Aplicar el manifiesto según
[Deployment](deployment.md), sin duplicar configuraciones en el home.

Super+Enter abre Kitty; Fuzzel usa `kitty -e` para programas Terminal=true.
Los paneles usan `--class=mbp-*`, que define su app_id y conserva las reglas
flotantes de Sway. Un comando explícito sustituye la shell de login.

## Work tabs

La barra nativa de Kitty aparece arriba, incluso con una sola pestaña. El
diseño Powerline usa el naranja del tema para distinguir la pestaña activa.
La etiqueta muestra solo el nombre de la carpeta activa, no la ruta completa
ni el escritorio de Sway. Cambiar de carpeta en Zsh actualiza la etiqueta.

- Ctrl+Shift+T abre una pestaña en la carpeta actual.
- Ctrl+Shift+Izquierda/Derecha alterna las pestañas de la misma ventana.
- Los paneles auxiliares y las aplicaciones TUI lanzadas por Fuzzel no muestran
  la barra mientras tengan una sola pestaña.

No se importan sesiones, tmux ni extensiones. Para comprobar el cambio sin
cerrar trabajo abierto, iniciar otra ventana con Super+Enter.

## Rendering policy

- JetBrainsMono Nerd Font Mono 10 y paleta separada en theme.conf.
- Fondo opaco, blur/trail/blink desactivados y scrollback de 10.000 líneas.
- Control remoto desactivado; no se necesita daemon ni socket de control.
- Cierre Super+W sin confirmación extra; guardar trabajo antes de cerrar.
- Display auto: Wayland en Sway y compatibilidad con otra sesión gráfica.

La configuración evita efectos adicionales, pero eso no cuantifica ahorro de
batería. [Fonts](fonts.md), [Starship](starship-setup.md) y
[Power and performance](optimizations.md).

## Verification

```sh
kitty +runpy 'from pathlib import Path; from kitty.config import load_config; bad=[]; load_config(str(Path.home()/".config/kitty/kitty.conf"), accumulate_bad_lines=bad); assert not bad, bad; print("Kitty config: OK")'
fuzzel --check-config
update-alternatives --query x-terminal-emulator
```

La prueba de referencia identificó una ventana xdg_shell sin XWayland y Zsh
como hijo. Verificar esas condiciones nuevamente tras cambios de versión.
Kitty 0.41.1 devuelve 0 incluso con hijo exit7: el panel Wi-Fi comprueba su
resultado de cliente por separado y distingue cierre HUP/TERM de error ordinario.
[Wi-Fi panel](wifi-setup.md).

## Updates and recovery

Actualizar manualmente por APT y repetir parser/apertura. Foot permanece como
terminal alternativa dentro de Wayland; una TTY sirve para reparar fuentes,
pero no ejecuta Foot directamente sin sesión gráfica.
Para recuperar selección automática de terminal Debian:

```sh
sudo update-alternatives --auto x-terminal-emulator
```

Antes de retirar Kitty, adaptar los entrypoints de Sway/Fuzzel/paneles y revisar
el plan de enlaces. Simular `apt-get -s remove kitty kitty-shell-integration`;
no retirar terminfo o bibliotecas compartidas a ciegas. Usar el journal del
despliegue correspondiente para rollback, verificando sus entries.
