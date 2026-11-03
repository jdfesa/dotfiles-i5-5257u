# Starship setup

## Installation and configuration

Prompt Zsh Catppuccin Mocha con directorio, rama/estado Git, worktree e indicadores
de lenguajes. Versión de referencia Debian 13 amd64: 1.22.1-5.
[Debian package](https://packages.debian.org/trixie/starship),
[Zsh integration](https://starship.rs/guide/#step-2-set-up-your-shell-to-use-starship),
[Configuration](https://starship.rs/config/).

```sh
apt-get -s --no-install-recommends --no-remove install starship
sudo apt-get --no-install-recommends --no-remove install starship
```

`config/starship/starship.toml` se enlaza a `~/.config/starship.toml`, 0644;
`config/zsh/zshrc` inicializa Starship al final de shells interactivas.
El prompt derecho usa $all. El motor de prompt y la cobertura de [Fonts](fonts.md)
son requisitos independientes.

## Runtime contracts

- scan_timeout=100 y command_timeout=500 ms; custom Git no elude esos límites.
- Shell custom POSIX sh explícita y consultas Git locales. ls-remote --get-url
  resuelve la URL configurada sin fetch; solo se imprime un indicador.
- El indicador worktree compara git-dir y common-dir.
- Fallback nativo si falta binario/configuración, MBP_SIMPLE_PROMPT=1, TERM=dumb
  o terminal NetBeans incompatible.
- Cache bajo `${XDG_CACHE_HOME:-~/.cache}/starship`, directorio 0700.

Los timeouts limitan cada comando, no toda la composición del prompt.

## Verification and measurements

```sh
zsh -n ~/.zshrc ~/.zprofile
starship print-config >/dev/null
python3 -m unittest discover -s tests -v
```

Los tests cubren prompt fuera/dentro de Git, URLs de prueba, linked worktrees,
comandos lentos y fallback. La validación nativa de referencia usa Kitty/Wayland,
Zsh de login y 52 símbolos con cobertura de fuentes.

Medición 2026-11-02, HOME aislado, 120 columnas, izquierda+derecha consecutivos,
11 muestras calientes por contexto:

| Contexto | Mediana | Máximo caliente |
|---|---:|---:|
| Vacío | 5,9 ms | 6,2 ms |
| Git pequeño | 14,0 ms | 16,2 ms |
| Proyecto Python | 6,9 ms | 7,4 ms |
| Checkout dotfiles | 13,9 ms | 15,8 ms |

Primera muestra vacía: 69 ms. No extrapolar a repositorios grandes ni a consumo
energético. Repetir con proyectos representativos antes de ampliar módulos.

## Updates and recovery

Actualizar por APT y repetir parser/apertura. Para una nueva shell con prompt
nativo, sin tocar enlaces:

```sh
MBP_SIMPLE_PROMPT=1 zsh -l
```

Para retirarlo permanentemente, adaptar el bloque de inicialización Zsh y revisar
el journal antes de revertir enlaces. Simular `apt-get -s remove starship` y
preservar los otros componentes de shell/historial.
