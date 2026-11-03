# Restore guide

## Target and prerequisites

Destino: Debian 13 amd64 en MacBookPro12,1, cuenta `jd` con sudo y conectividad
funcional. Sway es el perfil principal. El entorno alternativo se instala solo
siguiendo [XFCE recovery](xfce-recovery.md); no es requisito de estos pasos.

Esta guía empieza después de instalar Debian. El instalador administra discos,
usuarios y arranque; los dotfiles no particionan ni reemplazan ese proceso.
Confirmar `VERSION_ID=13`, arquitectura amd64 y los componentes APT `main` y
`non-free-firmware`. La BCM43602 utiliza brcmfmac/firmware-brcm80211.

## 1. Clone into the account home

```sh
sudo apt-get update
sudo apt-get --no-install-recommends --no-remove install git python3 ca-certificates
cd /home/jd
(umask 022; git clone https://github.com/jdfesa/dotfiles-i5-5257u.git)
cd /home/jd/dotfiles-i5-5257u
```

Conservar este nombre y ubicación: las entradas de aplicaciones utilizan rutas
explícitas de esta máquina. El checkout debe contener los manifiestos y fuentes
que se van a restaurar. No ejecutar el enlazador como root.

## 2. Install the Sway package profile

`config/packages/debian.txt` es la lista completa de dependencias directas,
incluidos componentes de sesión, red, audio, fuentes y portales que una
instalación de escritorio puede traer de antemano.

```sh
xargs -a config/packages/debian.txt -- apt-get -s --no-install-recommends --no-remove install
# Revisar el plan completo antes de continuar:
xargs -a config/packages/debian.txt -- sudo apt-get --no-install-recommends --no-remove install
```

Las dependencias transitivas las resuelve APT. No sustituir esta lista por el
número de paquetes añadido en otra instalación. `xserver-xorg` y el greeter
permiten el login LightDM; la sesión seleccionada sigue siendo Sway/Wayland.
No instalar otro servidor de audio encima de PulseAudio durante esta restauración.

Revisar locales y grupo de backlight:

```sh
locale -a
# Si falta en_US.UTF-8, generarlo mediante:
sudo dpkg-reconfigure locales
id -nG jd
# Si falta video, añadirlo y volver a iniciar sesión:
sudo usermod -aG video jd
```

## 3. Install vendor applications

- [Helium](helium-setup.md): configurar su repositorio firmado e instalar
  helium-bin antes de aplicar las asociaciones de navegador.
- [Zed](zed-setup.md): comprobar Vulkan físico, descargar la release oficial
  revisada, verificar su digest e instalar la app y CLI.

Estos pasos no se ejecutan por clonar ni por iniciar una terminal. Las versiones
observadas y las políticas de actualización están en [Dependencies](dependencies.md).
Las herramientas de [Development utilities](others/README.md) son independientes.

## 4. Prepare and review the device override

```sh
install -d -m 700 private private/sway
# Solo en una copia nueva donde local.conf no exista:
if [ ! -e private/sway/local.conf ] && [ ! -L private/sway/local.conf ]; then
  install -m 600 config/sway/local.conf.example private/sway/local.conf
fi
```

Revisar eDP-1, 2560×1600/escala 2 y touchpad. Sway declara US predeterminado y
ES de España, alternables desde el botón junto a la fecha. La plantilla es
suficiente para esta pantalla; `private/sway/local.conf` es su override editable.
No repetir install sobre cambios existentes.

## 5. Apply user configuration

```sh
python3 -m unittest discover -s tests -v
python3 tools/link-user-config.py
python3 tools/link-user-config.py --apply \
  --backup-dir "$HOME/.local/state/dotfiles-i5-5257u/link-backups/restore-$(date +%Y%m%d-%H%M%S)"
python3 tools/link-user-config.py
fc-cache "$HOME/.local/share/fonts"
```

La última ejecución debe mostrar unchanged. Ante Conflict, preservar y reconciliar
el archivo indicado; no hay force. Conservar la ruta de journal para rollback.
El perfil principal no aplica el manifiesto opcional de recuperación.

Antes del siguiente login:

```sh
sudo chsh -s /usr/bin/zsh jd
sudo update-alternatives --set x-terminal-emulator /usr/bin/kitty
sudo systemctl enable NetworkManager.service lightdm.service
WLR_BACKENDS=headless WLR_RENDERER=pixman sway --validate --config ~/.config/sway/config
```

La validación headless es solo sintáctica y no configura un renderer permanente.

## 6. Log into Sway and activate user units

Cerrar la sesión normalmente e ingresar eligiendo Sway en LightDM. Esto también
aplica el shell y los grupos de la cuenta. Dentro de la nueva sesión:

```sh
systemctl --user daemon-reload
systemctl --user enable --now mbp-weather-refresh.timer mbp-packages-refresh.timer
systemctl --user start mbp-weather-refresh.service mbp-packages-refresh.service
busctl --system call org.freedesktop.Accounts \
  "/org/freedesktop/Accounts/User$(id -u)" \
  org.freedesktop.Accounts.User SetXSession s sway
```

La última llamada guarda Sway como sesión preferida. Mantener login autenticado;
no es necesario cambiar PAM ni habilitar autologin.

## 7. Acceptance checks

```sh
echo "$XDG_SESSION_TYPE"                  # wayland
swaymsg -t get_version
eglinfo -B                               # Iris 6100, no llvmpipe
vulkaninfo --summary                     # API de la GPU física
fuzzel --check-config
xdg-settings get default-web-browser     # helium.desktop
systemctl --user list-timers 'mbp-*'
~/.local/bin/mbp-open-networks --check
```

Comprobar Super+Enter, Super+Espacio/D, Super+Shift+B, Super+N, Power menu,
barra, escala, fuentes, brillo y volumen. Abrir Zed desde Fuzzel; no tiene un
atajo asignado. Guardar trabajo y coordinar ensayos de energía/red antes de
suspender, apagar o cambiar de conexión.

## Recovery and coverage

[Deployment](deployment.md) describe rollback por journal y conflictos.
[XFCE recovery](xfce-recovery.md) describe la sesión alternativa opcional.
Las pruebas automatizadas cubren el manifiesto completo sobre un hogar temporal,
idempotencia, rollback y separación de perfiles. No sustituyen una restauración
completa del sistema operativo en hardware; esa validación permanece en TODO.md.
