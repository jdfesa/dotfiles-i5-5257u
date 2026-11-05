# Configuration deployment

## Sources and manifests

El checkout canónico es `/home/jd/dotfiles-i5-5257u`. Los destinos del home
apuntan a archivos de esa copia; conservarla mientras existan enlaces activos.

- `config/manifest.json`: perfil principal Sway y aplicaciones.
- `config/xfce/manifest.json`: perfil de recuperación opcional, independiente.
- Cada entrada declara source, destino relativo al home, modo y método symlink.
  Modos: 420=0644, 493=0755 y 384=0600.
- Paquetes/binarios se administran por separado; no se enlazan archivos del
  sistema a un checkout modificable del usuario.

Para una instalación nueva, seguir [Restore guide](restore-guide.md).

## Local overrides

Sway incluye `~/.config/sway/local.conf`. Su fuente se prepara una vez:

```sh
cd ~/dotfiles-i5-5257u
install -d -m 700 private private/sway
# Solo si el destino todavía no existe:
if [ ! -e private/sway/local.conf ] && [ ! -L private/sway/local.conf ]; then
  install -m 600 config/sway/local.conf.example private/sway/local.conf
fi
```

El manifiesto enlaza también el módulo público `trackpad-gestures.conf`, incluido
antes del override local. Los ajustes de toque y desplazamiento siguen en
`local.conf`; consultar [Trackpad gestures](trackpad-gestures.md).

La plantilla contiene pantalla eDP-1, escala 2 y touchpad. Las distribuciones
US predeterminada y ES de España se declaran en la configuración pública de Sway;
el botón junto a la fecha las alterna. Revisar los valores del dispositivo antes
de aplicar; no repetir install sobre un ajuste existente.

## Plan and apply

Ejecutar como jd, sin sudo:

```sh
python3 tools/link-user-config.py
python3 tools/link-user-config.py --apply \
  --backup-dir "$HOME/.local/state/dotfiles-i5-5257u/link-backups/restore-$(date +%Y%m%d-%H%M%S)"
```

El plan no escribe archivos. Detiene el proceso ante contenido diferente,
enlaces inesperados, padres enlazados o fuentes con dueño/modo incorrectos.
Puede sustituir una copia regular idéntica después de respaldarla. No hay opción
force: mover o reconciliar explícitamente un conflicto antes de repetir el plan.
El directorio de backup debe ser nuevo y estar fuera del checkout y de `.config`.

Una segunda ejecución debe informar unchanged. El journal se genera solo cuando
hay cambios y conserva el conjunto exacto de enlaces aplicado.

## Rollback

```sh
python3 tools/link-user-config.py --rollback /ruta/al/journal.json
```

La reversión verifica identidad de enlaces, hashes de backups y cambios posteriores.
Un destino modificado detiene el rollback. No revierte paquetes ni binarios.
El journal puede contener varios componentes: revisar sus entries antes de usarlo.

## Updating the checkout

Actualizar las fuentes por Git y repetir tests, plan y parsers antes de recargar
Sway. Un cambio de contenido se refleja mediante los enlaces existentes; nuevos
archivos requieren actualizar el manifiesto y aplicar su plan.

```sh
git pull --ff-only
python3 -m unittest discover -s tests -v
python3 tools/link-user-config.py
sway --validate --config ~/.config/sway/config
swaymsg reload
```

La recarga no reinicia la sesión. Un proceso que lee configuración solo al
arrancar puede requerir su reinicio normal; guardar el trabajo antes de hacerlo.

## SSH synchronization

`tools/sync-to-host.py` permite desplegar una copia de trabajo revisada a otro
checkout del equipo. Requiere Git, Python 3, SSH y rsync en ambos extremos.
El destino se define en `private/local/ssh-target`, formato usuario@host, modo 0600.

```sh
python3 tools/sync-to-host.py
python3 tools/sync-to-host.py --apply
```

La lista de fuentes procede de Git e incluye archivos nuevos no ignorados.
El override local admitido es `private/sway/local.conf`. El transporte conserva
backup de sustituciones bajo `~/.local/state/dotfiles-i5-5257u/sync-backups/`
y verifica SHA256, dueño y modo tras aplicar. No elimina archivos: reconciliar
renombres y retiradas de forma explícita. Un backup no reemplaza una fusión de
cambios divergentes.
