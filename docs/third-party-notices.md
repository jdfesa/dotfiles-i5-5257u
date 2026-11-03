# Third-party notices

`tools/link-user-config.py`, `scripts/power-action.sh`, el flujo de `power-menu`,
los helpers `status-*`/`update-*`, parte de sus tests, los atajos y la paleta se
adaptan del proyecto `dotfiles-i3-2310m` de jd. Su aviso MIT se conserva en
[`licenses/i3-reference-MIT.txt`](../licenses/i3-reference-MIT.txt).

JetBrains Mono Nerd Font, variantes Mono y Propo, conserva [OFL](../config/fonts/OFL.txt)
y [Icon set notices](../config/fonts/UPSTREAM.md). Los tres TTF se redistribuyen
sin modificar; hashes y tag en [Fonts](fonts.md).
La fuente Wi-Fi `status-icons.ttf` es material original MIT de la referencia;
se conserva su nombre de familia interno `BGH Status Icons` por compatibilidad.

El tema de `config/kitty/theme.conf` adapta los datos de color originales de jd
en `mydotfiles/shared/kitty/active-theme.conf`, sin scripts ni sesiones asociadas.
`config/starship/starship.toml` adapta el perfil de jd en
`mydotfiles/shared/starship/starship.toml`; conserva el diseño activo y acota
los comandos Git para Debian.

Los programas instalados conservan sus licencias de distribución; los avisos de
paquetes Debian están en `/usr/share/doc/<paquete>/copyright`.
