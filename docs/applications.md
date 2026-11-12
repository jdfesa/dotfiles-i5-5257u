# Applications and launchers

## Installed programs

Inventario de programas instalados y gestionados por el perfil principal,
incluidos sus accesos y ajustes. Al incorporar otro programa, añadir aquí
su uso y enlace a la guía correspondiente; no duplicar versiones ni listar
bibliotecas transitivas.

| Programa | Uso | Configuración pública / destino |
|---|---|---|
| Fuzzel | Super+Espacio/D; buscar aplicaciones por nombre, Enter abre, Esc cancela | `config/fuzzel/fuzzel.ini` → `~/.config/fuzzel/fuzzel.ini` |
| Kitty / Zsh | Super+Enter; terminal de login predeterminada y paneles auxiliares | `config/kitty/`, `config/zsh/` → destinos del manifiesto |
| Foot | Respaldo disponible en Fuzzel | `config/foot/foot.ini` → `~/.config/foot/foot.ini` |
| Starship | Prompt de nuevas Zsh, tanto en Kitty como en Foot | `config/starship/starship.toml` → `~/.config/starship.toml`; init en `config/zsh/zshrc` |
| Helium | Fuzzel; navegador XDG actual de Super+Shift+B | `config/helium/mimeapps.list` → `~/.config/mimeapps.list`; entrada de escritorio del paquete APT |
| Zed | Fuzzel o `zed`; sin atajo asignado | `config/zed/` → settings y entrada .desktop por manifiesto; binario oficial fuera del repo |
| Yazi | `yazi` en Kitty; vista previa PDF en el panel derecho | `config/yazi/yazi.toml` → `~/.config/yazi/yazi.toml` |
| Zathura | Enter sobre un PDF en Yazi; páginas oscuras, sin cambiar el lector XDG | `config/zathura/zathurarc` → `~/.config/zathura/zathurarc` |
| Wi-Fi networks | Super+N, icono de barra o búsqueda en Fuzzel | `scripts/open-networks.sh`, `config/network/mbp-networks.desktop` → binario/enlace .desktop del usuario |
| Power menu | Buscar Power menu/apagar en Fuzzel o Super+Shift+P | `config/power/mbp-power-menu.desktop`, `scripts/power-menu` y `scripts/power-action.sh` → destinos del manifiesto |
| wmenu | Ayuda a demanda | Helpers públicos; no sustituye el catálogo de aplicaciones de Fuzzel |

Versiones, origen e integridad se mantienen en [Dependencies](dependencies.md).
Cada fuente se agrupa por componente y se despliega con enlaces por archivo
mediante `config/manifest.json`. No copiar configuraciones independientes al home.
Instalación/rutas/verificación/recuperación: [Helium](helium-setup.md),
[Zed](zed-setup.md) y [Yazi and Zathura setup](yazi-setup.md). El navegador se
resuelve por XDG, no se fija su ejecutable en el atajo. Helium y Zed conservan
sus entradas de búsqueda en Fuzzel.

## Fuzzel installation and recovery

Fuzzel es nativo Wayland, similar al modo drun de Rofi, sin daemon residente.
Fuente: [Debian package](https://packages.debian.org/trixie/fuzzel),
[Fuzzel configuration manual](https://manpages.debian.org/trixie/fuzzel/fuzzel.ini.5.en.html).
Instalación 2026-11-02, amd64, versión registrada en el inventario; integridad
por metadata firmada y hashes de APT. Reutiliza las bibliotecas ya instaladas.

```sh
apt-get -s --no-install-recommends --no-remove install fuzzel
sudo apt-get --no-install-recommends --no-remove install fuzzel
```

El binario del sistema lo administra APT. El perfil propio usa los colores y
fuente de la barra; `terminal=kitty -e` ejecuta las aplicaciones TUI directamente,
sin convertirlas en shells de login.
Se buscan nombre, nombre genérico, filename y keywords, incluidas las palabras
españolas del menú de energía. Detalles y cancelación: [Power menu](power-menu.md).
La terminal normal sigue iniciando Zsh de login.

Validar con `fuzzel --check-config`, `desktop-file-validate` sobre la entrada
administrada y una apertura/cancelación desde la sesión Sway. Recargar Sway para
actualizar atajos sin cerrar aplicaciones. Los tests no eligen programas/redes.

Comprobar Super+Espacio y el lanzamiento de aplicaciones tras restaurar.
Super+Enter abre Kitty y dentro se ejecuta Zsh.

Actualización manual por APT. Antes de retirar Fuzzel, restaurar un lanzador
alternativo y el frontend previo del menú de energía desde backups revisados;
después revertir sus enlaces y simular `apt-get -s remove fuzzel`. No eliminar
wmenu: aún se usa en la ayuda.

## Network use

[Wi-Fi setup](wifi-setup.md) describe escaneo, conexión, editor avanzado,
permisos y recuperación mediante NetworkManager.

## Terminal and prompt

[Kitty setup](kitty-setup.md) registra instalación oficial, perfil propio,
verificación nativa y recuperación. [Starship setup](starship-setup.md) registra el prompt adaptado,
fuentes verificadas, mediciones y recuperación sin reemplazar la shell.
