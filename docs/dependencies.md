# Dependencies and installation inventory

## Managed packages

Instalación verificada: **2026-11-02**, Debian 13/trixie, amd64 (paquetes de
recursos `all` cuando corresponde). Fuentes oficiales Debian:
`https://deb.debian.org/debian/` y
`http://security.debian.org/debian-security`, suites trixie/trixie-security.
APT verifica firmas Debian de metadata y hashes de los `.deb`; sin scripts de
instalación descargados a una shell. Los programas del proveedor se detallan aparte.

La lista declarativa de dependencias directas para una instalación nueva es
[`config/packages/debian.txt`](../config/packages/debian.txt). Incluye sesión,
audio, red, portales, firmware y herramientas de validación. Las bibliotecas
transitivas las resuelve APT. Los paquetes del entorno alternativo están en
[`config/xfce/packages-debian.txt`](../config/xfce/packages-debian.txt).

Las versiones siguientes son referencia de compatibilidad, no pins de APT.

| Paquete | Versión verificada | Uso |
|---|---|---|
| [sway](https://packages.debian.org/trixie/sway) | `1.10.1-2` | Compositor Wayland |
| [swayidle](https://packages.debian.org/trixie/swayidle) | `1.8.0-1` | Inactividad y bloqueo previo a suspensión |
| [swaylock](https://packages.debian.org/trixie/swaylock) | `1.8.2-1` | Bloqueo PAM |
| [kitty](https://packages.debian.org/trixie/kitty) | `0.41.1-2+deb13u2` | Terminal predeterminada / Zsh |
| [foot](https://packages.debian.org/trixie/foot) | `1.21.0-2` | Terminal Wayland de respaldo |
| [wmenu](https://packages.debian.org/trixie/wmenu) | `0.1.9-2` | Menú de ayuda a demanda |
| [fuzzel](https://packages.debian.org/trixie/fuzzel) | `1.12.0+ds-1` | Lanzador Wayland de aplicaciones .desktop |
| [mako-notifier](https://packages.debian.org/trixie/mako-notifier) | `1.10.0-1` | Notificaciones |
| [brightnessctl](https://packages.debian.org/trixie/brightnessctl) | `0.5.1-3.1` | Brillo de pantalla; teclado mediante UPower |
| [brightness-udev](https://packages.debian.org/trixie/brightness-udev) | `0.5.1-3.1` | Permisos estándar de backlight |
| [systemd](https://packages.debian.org/trixie/systemd) | `257.13-1~deb13u1` | busctl para llamadas D-Bus acotadas |
| [upower](https://packages.debian.org/trixie/upower) | `1.90.9-1` | Batería y control nativo del brillo de teclado |
| [xwayland](https://packages.debian.org/trixie/xwayland) | `2:24.1.6-1` | Compatibilidad X11 bajo Wayland |
| [wl-clipboard](https://packages.debian.org/trixie/wl-clipboard) | `2.2.1-2` | Portapapeles |
| [grim](https://packages.debian.org/trixie/grim) | `1.4.0+ds-2+b1` | Capturas |
| [slurp](https://packages.debian.org/trixie/slurp) | `1.5.0-1` | Selección de área |
| [rsync](https://packages.debian.org/trixie/rsync) | `3.5.0+ds1-0+deb13u1` | Transporte de fuentes por SSH |
| [wayland-utils](https://packages.debian.org/trixie/wayland-utils) | `1.2.0-2` | Diagnóstico Wayland |
| [mesa-utils](https://packages.debian.org/trixie/mesa-utils) | `9.0.0-2+b2` | Diagnóstico EGL/OpenGL |
| [vulkan-tools](https://packages.debian.org/trixie/vulkan-tools) | `1.4.304.0+dfsg1-1` | Verificación Vulkan físico previa a Zed |
| [zsh](https://packages.debian.org/trixie/zsh) | `5.9-8+b24` | Shell predeterminada |
| [starship](https://packages.debian.org/trixie/starship) | `1.22.1-5` | Prompt de Zsh adaptado de mydotfiles |
| [i3status](https://packages.debian.org/trixie/i3status) | `2.15-2` | Backend de Swaybar |
| [python3-gi](https://packages.debian.org/trixie/python3-gi) | `3.50.0-4+b1` | Calendario GTK bajo demanda |
| [gir1.2-gtk-3.0](https://packages.debian.org/trixie/gir1.2-gtk-3.0) | `3.24.49-3` | Widget Gtk.Calendar nativo Wayland |

## Transitive packages

Dependencias añadidas por APT, sin demonios propios seleccionados manualmente:

| Paquete | Versión |
|---|---|
| `swaybg` | `1.2.1-1` |
| `libfcft4t64` | `3.3.1-1` |
| `libliftoff0` | `0.5.0-1.1` |
| `libseat1` | `0.9.1-1` |
| `libutf8proc3` | `2.9.0-1+b2` |
| `libwlroots-0.18` | `0.18.2-3` |
| `libxcb-composite0` | `1.17.0-2+b1` |
| `libxcb-errors0` | `1.0.1-4` |
| `libxcb-ewmh2` | `0.4.2-1` |
| `libxcb-res0` | `1.17.0-2+b1` |
| `mesa-utils-bin` | `9.0.0-2+b2` |
| `zsh-common` | `5.9-8` |
| `libconfuse-common` | `3.3-4` |
| `libconfuse2` | `3.3-4` |
| `kitty-shell-integration` | `0.41.1-2+deb13u2` |

Para [Trackpad gestures](trackpad-gestures.md) se usa `bcm5974`, incluido en el
kernel de Debian, y `libinput10` (`1.28.1-1+deb13u1` en el equipo de referencia),
dependencia transitiva del compositor. El perfil no añade paquetes ni servicios.

## Platform services

Mesa 25.0.7/i915 y firmware-brcm80211 20250410-2 soportan Iris 6100 y BCM43602.
LightDM/AccountsService, D-Bus, polkitd/mate-polkit, UPower y PulseAudio forman la
sesión principal. GTK, NetworkManager y los portales proporcionan integración
de aplicaciones. Se declaran explícitamente en la lista de restauración.
[Minimal login screen](minimal-login-screen.md) reutiliza LightDM GTK Greeter
con Adwaita y DejaVu Sans, sin paquetes adicionales.

Versiones observadas: network-manager 1.52.1-1, nm-connection-editor 1.36.0-3+b1,
fonts-dejavu-core 2.37-8 y fonts-symbola 2.60-2. El [perfil opcional](xfce-recovery.md)
no forma parte de la instalación principal.

## Vendor applications

Programas del proveedor, gestionados separadamente de la lista Debian:

| Programa | Versión verificada | Origen / gestión |
|---|---|---|
| Helium | `helium-bin 0.15.2.1-1`, Chromium `151.0.7922.75` | APT del proveedor `https://pkg.helium.computer/deb`, stable/main; paquete helium-bin |
| Zed | `1.26.2`, commit `c4273271092b0287f7d181f616bd5171e0a2f70c` | Tarball oficial x86_64, hash publicado verificado; app de usuario, actualización manual |

[Helium](helium-setup.md) detalla asociaciones/configuración y actualización
pendiente; [Zed](zed-setup.md) registra URL, SHA256, instalación reproducible,
requisitos Vulkan, configuración, verificación y recuperación.

## Fonts and script assets

JetBrains Mono Nerd Font Mono Regular/Bold, base 2.304 / Nerd Fonts v3.5.1,
y fuente Wi-Fi de referencia: archivos públicos del proyecto i3, con hashes
SHA256 comprobados y atribuciones conservadas. Propo Regular se obtiene del tag
oficial Nerd Fonts v3.5.1 para los iconos de clima y métricas. Procedencia,
integridad y avisos en [Fonts](fonts.md) y [Third-party notices](third-party-notices.md).
No se instala una colección completa ni un daemon de fuentes.

## Installation, validation and updates

- [Sway](sway-setup.md): comandos, dependencias previas, rutas, permisos y reversión.
- [Zsh](zsh-setup.md): instalación, cambio de shell y recuperación de Bash.
- [Kitty](kitty-setup.md): perfil, terminal predeterminada y recuperación.
- [Starship](starship-setup.md): prompt, timeouts, fuentes y recuperación nativa.
- [Status bar](status-bar.md): i3status, fuentes, timers y comprobación de datos.
- [Despliegue](deployment.md): SSH, enlaces, hashes y backups.

```sh
sudo apt-get update
apt-get -s --no-install-recommends --no-remove install PAQUETES_REVISADOS
sudo apt-get --no-install-recommends --no-remove install PAQUETES_REVISADOS
# Inventario de un paquete; no descarga ni modifica nada:
dpkg-query -W -f='${Package} ${Version} ${Architecture} ${db:Status-Status}\n' sway
```

Revisar los cambios y actualizar este inventario al aplicar actualizaciones.
No hay actualización automática de paquetes. Desinstalar solo tras simular la
retirada y recuperar shell/sesión alternativa; nunca `autoremove` a ciegas.
Descargas administradas por APT; los bundles temporales de despliegue se limpian
tras verificar. Los caches generados por helpers viven fuera del checkout.
