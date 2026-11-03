# Scripts and tools

## Main session helpers

Los helpers se ejecutan como jd. Rutas y modos se declaran en `config/manifest.json`.
[Restore guide](restore-guide.md) y [Configuration deployment](deployment.md) describen la preparación.

| Fuente | Contrato | Dependencias / verificación |
|---|---|---|
| scripts/sway-session.sh | Instancia única por sesión; ciclo de vida mako/swayidle/Polkit | Sway, flock, mate-polkit; parser y sesión local |
| scripts/sway-tools.sh | Despacho fijo de herramientas y teclado keyboard-brightness-up/down a demanda | Kitty, XDG/GTK, alsamixer, APT, wmenu, grim/slurp/wl-copy, UPower/busctl y flock; tests con comandos simulados |
| scripts/open-networks.sh | --check solo lectura; --edit editor; panel a demanda | NetworkManager/nmcli/nmtui, Kitty, flock; tests de estado/cancelación del cliente |
| scripts/power-menu | Fuzzel dmenu con acciones fijas; --dry-run no ejecuta acciones | Fuzzel, swaymsg/swaylock, Kitty; confirmaciones simuladas |
| scripts/power-action.sh | suspend/reboot/poweroff, --dry-run opcional; autorización/inhibidores | systemd >=257, busctl, terminal, swaylock; política simulada y tests PTY |
| scripts/status-bar.sh | Inicia i3status, detecta sensor/audio una vez | i3status, pactl, fontconfig; parser de shell |
| scripts/status-adapter.py | Adaptador JSON/clics, selector US/ES por Sway IPC y vista contraíble; diagnóstico --run-once | Python 3, UPower; tests de protocolo, redibujado sin muestreo y allowlist |
| scripts/calendar-popup.py | Calendario de consulta, instancia única y salida al cerrar | Python 3, PyGObject, GTK3; fechas/activación simuladas y validación Wayland |
| scripts/sway-status.py | --once solo lectura; parseo de batería y umbrales | Python 3, UPower; ejemplos de batería |
| scripts/update-weather.py | Oneshot HTTPS acotado y caché validada | Python 3; tests sin red de respuestas/timeout |
| scripts/update-packages.py | Simulación APT con caché, sin instalación | Python 3, apt-get; comandos/errores simulados |

Las cuatro unidades config/status/systemd programan los dos helpers de actualización.
La [Status bar](status-bar.md) define tick, caché y manejo de fallos.
Las guías de [Wi-Fi panel](wifi-setup.md) y [Power menu](power-menu.md) describen sus interfaces.

## Maintenance tools

| Fuente | Parámetros / efectos | Verificación |
|---|---|---|
| tools/link-user-config.py | dry-run; --manifest PATH; --apply --backup-dir DIR; --rollback JOURNAL | Conflictos, hogar completo, idempotencia y rollback |
| tools/sync-to-host.py | dry-run; --apply; --target; --ssh-control | Lista de fuentes, transporte y SHA256/dueño/modo |
| tools/check-repository.py | Árbol de trabajo; --history añade blobs Git | Estructura, enlaces, reglas ignore y patrones de prueba |

## Recovery profile

`scripts/xfce/set-local-brightness.sh` y su autostart pertenecen solo al
[XFCE recovery](xfce-recovery.md), con manifiesto independiente.
No se despliegan ni inician desde el perfil Sway.

## Regression suites

Ejecutar `python3 -m unittest discover -s tests -v`. Las pruebas usan hogares y
repositorios temporales, comandos simulados y respuestas de ejemplo. Los ensayos
de hardware/sesión son pasos de aceptación separados de la validación sintáctica.

| Suite | Cobertura |
|---|---|
| tests/test_restoration.py | Manifiestos completos, hogar nuevo, rollback y perfil opcional |
| tests/test_repository.py | Árbol publicable, enlaces, patrones y revisión de symlinks |
| tests/test_deployment.py | Conflictos, backups, lista de transporte y batería |
| tests/test_desktop_apps.py / test_terminal_profile.py | Defaults XDG, settings de aplicaciones y entrypoints |
| tests/test_network_panel.py / test_power_menu.py | UI simulada, cancelación y guardas de acciones |
| tests/test_shell.py / test_starship.py | Inicialización, fallback, glifos y timeouts |
| tests/test_status_adapter.py / test_packages.py / test_weather.py | Protocolo de barra y cachés/errores |
| tests/test_battery.py | Estados/niveles, porcentaje, cobertura de glifos y fallos de lectura UPower |
| tests/test_status_icons.py | Fuente proporcional, hash/enlace, glifos, valores sin leyendas y caché de clima |
| tests/test_calendar.py | Cambio de mes/año, límites, ventana única y rechazo fuera de Wayland |
| tests/test_keyboard_backlight.py | UPower simulado, pasos/límites, apagado completo, errores, entradas inválidas y concurrencia acotada |
| tests/test_keyboard_layout.py | Índices US/ES, eventos IPC, framing parcial, errores, clics fijos y redibujado sin sondeo |
