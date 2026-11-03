# Git workflow

## Identity and defaults

La identidad es una configuración de la cuenta que utiliza Git. Ajustarla antes
de crear commits, con los valores apropiados para esa cuenta:

```sh
git config --global user.name "Your Name"
git config --global user.email "you@example.org"
git config --global user.useConfigOnly true
git config --global init.defaultBranch main
git config --global core.autocrlf input
git config --global fetch.prune true
git config --global pull.ff only
git config --global push.default simple
```

El proyecto utiliza LF, mensajes Conventional Commits en inglés y revisión de
cambios por archivo. `pull.ff=only` evita merges implícitos al actualizar la copia.

## Change validation

```sh
git status --short
python3 -m unittest discover -s tests -v
python3 tools/check-repository.py --history
git diff --check
git diff --cached --stat
git diff --cached
```

La última revisión debe realizarse sobre el conjunto exacto preparado para el
commit. La validación de archivos de trabajo no implica que ya estén publicados.
Actualizar CHANGELOG y las guías afectadas junto a los cambios funcionales.

## Commit organization

Separar funcionalidades o módulos coherentes y añadir sus pruebas y documentación.
Los cambios compartidos del manifiesto deben declarar solo fuentes incluidas
en ese commit o en sus antecesores. Ejemplos de Conventional Commits en inglés:

```text
feat(sway): configure the hardware-specific Wayland session
fix(status): align volume icon spacing
docs(restore): document the installation sequence
```

Antes de publicar, actualizar las referencias y revisar el intervalo saliente:

```sh
git fetch origin
git log --oneline origin/main..HEAD
git diff --stat origin/main..HEAD
git ls-files -ci --exclude-standard
python3 tools/check-repository.py --history
git push origin HEAD:main
```

La lista de archivos versionados que coinciden con exclusiones debe estar vacía.
Los patrones estáticos son comprobaciones acotadas, no una garantía universal;
complementan la revisión del índice y de los objetos del intervalo saliente.
CHANGELOG conserva cambios técnicos; TODO contiene trabajo pendiente.

## Local configuration recovery

Revertir solo la clave necesaria, por ejemplo `git config --global --unset
pull.ff`. No reemplazar una configuración global completa para retirar un ajuste.
