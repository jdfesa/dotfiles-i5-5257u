# Sway setup

## Scope and dependencies

Sesión principal Wayland de Debian 13 amd64 para MacBookPro12,1.
Sway utiliza i915/Mesa en Iris 6100, PulseAudio, NetworkManager, UPower y logind.
LightDM proporciona el login; el perfil no cambia políticas PAM ni tapa/inhibidores.
[Minimal login screen](minimal-login-screen.md) describe el aspecto opcional
sin modificar el bloqueo de Sway ni la selección de sesión.

[Restore guide](restore-guide.md) instala la lista completa
`config/packages/debian.txt`, prepara overrides y aplica enlaces.
[Dependencies](dependencies.md) registra versiones y origen de los paquetes.
Fuente: [Sway Debian](https://packages.debian.org/trixie/sway) y
[Sway configuration manual](https://manpages.debian.org/trixie/sway/sway.5.en.html).

## Configuration

`config/sway/config` y la ayuda de atajos se enlazan a `~/.config/sway/`.
El manifiesto también enlaza el override local preparado desde la plantilla.

- Fondo sólido, bordes sencillos y [Status bar](status-bar.md) Mocha opaca.
- Pantalla eDP-1 2560×1600, escala 2: espacio lógico 1280×800.
- XWayland bajo demanda para aplicaciones X11.
- Brillo al 40 % solo al iniciar sesión; cambios posteriores no se sobrescriben
  con reload. brightness-udev y el grupo video proporcionan acceso al backlight.
- [Keyboard backlight](keyboard-backlight.md): F5/F6 mediante UPower existente,
  sin nuevos servicios ni permisos sobre el grupo input.
- Distribuciones US predeterminada y ES de España; selector manual global junto
  a la fecha, integrado en la [Status bar](status-bar.md), sin sondeo adicional.
- Atajos Omarchy adaptados en [Keyboard shortcuts](keybindings.md).
- [Trackpad gestures](trackpad-gestures.md): cambio de escritorio con tres dedos
  mediante Sway y libinput, sin procesos ni paquetes adicionales.
- El include Debian `/etc/sway/config.d/*` integra el entorno D-Bus/systemd.
- `mbp-sway-session` arranca una sola instancia de mako, swayidle y agente Polkit.
- Inactividad: bloqueo a los 5 min, aviso al minuto previo y pantalla apagada a
  los 10 min. Bloqueo antes de suspensión; no hay timeout de suspensión automática.

Kitty/Zsh, Fuzzel, panel Wi-Fi y Power menu se describen por componente.
Los cambios de timeouts requieren un nuevo inicio normal del helper; reload no
lo duplica ni reinicia una sesión. Para la alternativa independiente, consultar
[Recovery profile](xfce-recovery.md).

## Preferred session

Después de ingresar en Sway, guardar la selección autenticada:

```sh
busctl --system call org.freedesktop.Accounts \
  "/org/freedesktop/Accounts/User$(id -u)" \
  org.freedesktop.Accounts.User SetXSession s sway
```

Sway debe existir en `/usr/share/wayland-sessions/sway.desktop`, administrado por
APT. El binario y archivos de sistema son propiedad root; el perfil del home
se gestiona como jd mediante [Deployment](deployment.md).

## Verification

```sh
sway --validate --config ~/.config/sway/config
echo "$XDG_SESSION_TYPE"
swaymsg -t get_version
swaymsg -t get_outputs
eglinfo -B
```

Sin sesión gráfica, el backend temporal permite validar sintaxis:

```sh
WLR_BACKENDS=headless WLR_RENDERER=pixman sway --validate --config ~/.config/sway/config
```

No es una prueba de aceleración ni un ajuste persistente.

Plataforma de referencia verificada: Sway 1.10.1, sesión Type=wayland/Active=yes,
EGL Intel Iris 6100 (BDW GT3), OpenGL 4.6/ES 3.2 y eDP-1 59,972 Hz/escala 2.
Revalidar terminal/lanzador, bloqueo, escala, audio y brillo después de restaurar.
Autonomía, tapa/suspensión y screen sharing tienen sus comprobaciones separadas.

## Updates and recovery

Revisar/simular cambios APT antes de aplicar y repetir parser/tests.
`swaymsg reload` actualiza configuración sin cerrar ventanas; no equivale al
restart de i3. Para retirar, salir normalmente, conservar un acceso de reparación
y revisar `apt-get -s remove sway swayidle swaylock` antes de desinstalar.
No eliminar dependencias compartidas mediante autoremove a ciegas.
[Deployment and rollback](deployment.md), [XFCE recovery](xfce-recovery.md).
