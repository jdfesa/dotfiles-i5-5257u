# XFCE recovery

## Optional profile

XFCE es una alternativa de recuperación, no el entorno de trabajo principal.
Su lista de paquetes y manifiesto están separados del perfil Sway:

- `config/xfce/packages-debian.txt`.
- `config/xfce/manifest.json`.
- `scripts/xfce/set-local-brightness.sh`.
- `config/xfce/mbp2015-brightness.desktop`.

La restauración principal no instala este conjunto ni aplica estos enlaces.

## Installation and configuration

Con Debian y el login LightDM ya preparados según [Restore guide](restore-guide.md):

```sh
xargs -a config/xfce/packages-debian.txt -- apt-get -s --no-install-recommends --no-remove install
xargs -a config/xfce/packages-debian.txt -- sudo apt-get --no-install-recommends --no-remove install
python3 tools/link-user-config.py --manifest config/xfce/manifest.json
python3 tools/link-user-config.py --manifest config/xfce/manifest.json --apply \
  --backup-dir "$HOME/.local/state/dotfiles-i5-5257u/link-backups/xfce-$(date +%Y%m%d-%H%M%S)"
```

Un archivo existente diferente es un conflicto: respaldarlo y reconciliarlo
antes de aplicar. No reemplazar configuraciones completas del escritorio.
Elegir XFCE desde LightDM solo cuando se necesite la sesión alternativa.

## Brightness helper

El autostart OnlyShowIn=XFCE llama `~/.local/bin/mbp-xfce-brightness`, enlazado
al script de este checkout. Espera 5 s y ajusta el backlight al 40 % mediante
el helper de xfce4-power-manager y PolicyKit. Actúa solo en DISPLAY=:0 o :0.0;
una sesión remota o sin pantalla local no cambia el brillo.

Puede desactivarse desde Session and Startup o revirtiendo el journal opcional.
No habilitar xfce4-power-manager dentro de Sway: la gestión de inactividad y
brillo del perfil principal es independiente.

## Recovery

Si falla el inicio de Sway, entrar a una TTY con Ctrl+Alt+F3 (posiblemente Fn),
iniciar sesión, revisar el parser y el journal del despliegue afectado.
Si esta alternativa está instalada, elegirla desde LightDM para reparar fuentes
y enlaces. Volver a Sway tras validar; no cambiar la sesión preferida como parte
del despliegue del perfil opcional.
