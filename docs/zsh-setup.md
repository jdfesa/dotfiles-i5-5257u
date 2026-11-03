# Zsh setup

## Installation and defaults

Shell de login/interactivo de jd: `/usr/bin/zsh`. Kitty solicita explícitamente
Zsh como login shell, de modo que las terminales nuevas no heredan el Bash de
una sesión gráfica iniciada antes del cambio. Las terminales ya abiertas no se
cierran ni se convierten automáticamente.

Fuente: [Debian package](https://packages.debian.org/trixie/zsh).
Versiones, arquitectura y fecha en [Dependencies](dependencies.md).
Integridad: firmas del índice APT y hashes de paquetes del repositorio Debian.
Se reutilizan las bibliotecas del sistema; no hay frameworks, plugins externos,
bootstrap por Internet ni servicios residentes.

```sh
apt-get -s --no-install-recommends --no-remove install zsh
sudo apt-get --no-install-recommends --no-remove install zsh
sudo chsh -s /usr/bin/zsh jd
```

Los archivos del paquete son root-owned, bajo `/usr/bin` y `/etc/zsh`.
`config/zsh/zprofile` y `zshrc` se enlazan a `~/.zprofile` y `~/.zshrc` según
`config/manifest.json`, con conflictos/backups gestionados por la herramienta.

## Configuration

- PATH sin duplicados, con `~/.local/bin` y `~/bin`.
- Completion nativo, edición Emacs y [Starship](starship-setup.md) basado en el
  perfil modular, con prompt simple de recuperación y caché privada.
- Historial privado: `${XDG_STATE_HOME:-~/.local/state}/zsh/history`, modo 0600,
  directorio 0700; cache de completion bajo `~/.cache/zsh`.
- Comandos precedidos de espacio se omiten del historial.
- No se carga `.bashrc` ni se cambia el intérprete de scripts POSIX/Python.

## Verification and recovery

```sh
getent passwd jd | cut -d: -f1,7
zsh -n ~/.zshrc ~/.zprofile
zsh -lic 'print -r -- $ZSH_VERSION; whence -p python3'
# Parser del perfil de terminal: ver kitty-setup.md
```

La carga interactiva crea solamente historial/cache privados. Para recuperar
Bash como shell de la cuenta, usar `chsh -s /bin/bash` autenticado y revertir
los enlaces con el journal correspondiente. Antes de quitar Zsh por APT,
recuperar también los ajustes `shell` de Kitty y del respaldo Foot; no dejar una cuenta apuntando a un
binario eliminado. Las actualizaciones son manuales mediante APT.
