# Configuración global y flujo de Git

Fecha de configuración: 2026-08-07.

## Estado previo

Git 2.47.3 ya estaba instalado en Debian. No existía configuración global, helper
de credenciales ni clave SSH de cliente. Los únicos archivos encontrados en
`~/.ssh` correspondían al acceso entrante por SSH y no se reutilizaron para GitHub.

## Identidad

Se utilizó la identidad pública de GitHub y su correo privado moderno:

```text
Nombre: José Sandoval
Usuario: jdfesa
Correo: 92765822+jdfesa@users.noreply.github.com
```

No se configuró ningún correo personal.

## Configuración desde cero

Si Git no está instalado en Debian:

```bash
sudo apt update
sudo apt install git
```

Aplicar la configuración global:

```bash
git config --global user.name "José Sandoval"
git config --global user.email \
  "92765822+jdfesa@users.noreply.github.com"
git config --global user.useConfigOnly true
git config --global init.defaultBranch main
git config --global core.autocrlf input
git config --global fetch.prune true
git config --global pull.ff only
git config --global push.default simple
git config --global push.autoSetupRemote true
```

### Motivo de los valores

- `user.useConfigOnly=true`: impide que Git invente una identidad basada en el
  usuario y hostname.
- `init.defaultBranch=main`: usa `main` en repositorios nuevos.
- `core.autocrlf=input`: conserva LF en el repositorio bajo Linux.
- `fetch.prune=true`: elimina referencias remotas obsoletas.
- `pull.ff=only`: evita merges automáticos inesperados al hacer `pull`.
- `push.default=simple`: publica la rama actual hacia su upstream.
- `push.autoSetupRemote=true`: crea el upstream durante el primer `push`.

## Verificación

```bash
git --version
git config --global --list --show-origin
git var GIT_AUTHOR_IDENT
git var GIT_COMMITTER_IDENT
```

Autor y committer deben mostrar:

```text
José Sandoval <92765822+jdfesa@users.noreply.github.com>
```

## Inicialización y publicación de `mbp2015`

El remoto se comprobó vacío antes de crear el historial. Después se ejecutó:

```bash
cd ~/github/mbp2015
git init --initial-branch=main
git remote add origin https://github.com/jdfesa/mbp2015.git
```

Los commits usan Conventional Commits y mensajes en inglés:

```text
chore: initialize repository
feat(power): add local brightness automation
docs: document hardware setup and optimizations
```

Publicación y comprobación básica:

```bash
git push --set-upstream origin main
git status --short --branch
git ls-remote origin refs/heads/main
```

El repositorio general de dotfiles no fue clonado, movido ni modificado durante
este trabajo.

## Reversión de la configuración global

Cada valor puede retirarse explícitamente, por ejemplo:

```bash
git config --global --unset user.name
git config --global --unset user.email
git config --global --unset user.useConfigOnly
```

No se debe borrar `~/.gitconfig` completo sin revisar antes si contiene otros
ajustes incorporados posteriormente.
