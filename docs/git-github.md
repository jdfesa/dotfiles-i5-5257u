# Configuración de Git y GitHub

Fecha de configuración: 2026-08-07.

## Alcance

Git se configuró globalmente para el usuario `jd`. El proyecto `mbp2015` se
mantiene separado de `mydotfiles`: no se clonaron, movieron ni versionaron los
dotfiles de otras máquinas.

## Identidad

La identidad se obtuvo del perfil público de GitHub `jdfesa`:

```text
Nombre: José Sandoval
Correo: 92765822+jdfesa@users.noreply.github.com
```

El correo usa el formato privado moderno de GitHub `ID+usuario@users.noreply.github.com`.
No se configuró ningún correo personal.

## Configuración global aplicada

Archivo resultante: `~/.gitconfig`.

```ini
[user]
    name = José Sandoval
    email = 92765822+jdfesa@users.noreply.github.com
    useConfigOnly = true

[init]
    defaultBranch = main

[core]
    autocrlf = input

[fetch]
    prune = true

[pull]
    ff = only

[push]
    default = simple
    autoSetupRemote = true
```

### Motivo de cada valor

- `user.useConfigOnly=true`: evita que Git invente una identidad basada en el
  usuario y hostname del equipo.
- `init.defaultBranch=main`: usa `main` en repositorios nuevos.
- `core.autocrlf=input`: conserva finales de línea LF en el repositorio bajo Linux.
- `fetch.prune=true`: retira referencias remotas que ya fueron eliminadas.
- `pull.ff=only`: evita merges automáticos inesperados al ejecutar `git pull`.
- `push.default=simple`: publica únicamente la rama actual hacia su rama asociada.
- `push.autoSetupRemote=true`: configura automáticamente el upstream en el primer
  `push` de una rama nueva.

## Verificación

```bash
git config --global --list --show-origin
git var GIT_AUTHOR_IDENT
git var GIT_COMMITTER_IDENT
```

La identidad efectiva verificada fue:

```text
José Sandoval <92765822+jdfesa@users.noreply.github.com>
```

## Pendiente para una etapa posterior

- Reordenar y versionar los dotfiles de esta máquina.

## Autenticación de GitHub

GitHub CLI 2.97.0 se instaló para `jd` en:

```text
~/.local/bin/gh
```

El binario se descargó desde la publicación oficial y se verificó con el checksum
SHA-256 publicado por GitHub. La cuenta `jdfesa` se autorizó mediante el flujo web
de dispositivo y GitHub CLI configuró HTTPS como protocolo para Git.

El token no forma parte del repositorio. El estado puede comprobarse sin mostrarlo:

```bash
gh auth status
```

## Repositorio `mbp2015`

```text
Rama principal: main
Remoto: https://github.com/jdfesa/mbp2015.git
Convención de commits: Conventional Commits, mensajes en inglés
```

Este repositorio contiene únicamente la documentación y automatización específica
de este MacBook Pro. Los dotfiles generales se gestionarán por separado.

Estar conectado a GitHub en Helium no transfiere automáticamente credenciales a
Git en la terminal; por eso la terminal se autorizó explícitamente mediante
GitHub CLI.
