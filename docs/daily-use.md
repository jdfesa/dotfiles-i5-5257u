# Daily use

## Session and applications

Sway es la sesión principal. Super+Enter abre Kitty/Zsh; Super+Espacio o D abre
Fuzzel. Super+Shift+B resuelve el navegador XDG predeterminado. Helium y Zed
se encuentran en Fuzzel; Zed no tiene un atajo asignado.
[Keyboard shortcuts](keybindings.md), [Applications and launchers](applications.md).

Super+N o el icono Wi-Fi abre [Wi-Fi panel](wifi-setup.md). Super+Shift+P abre
[Power menu](power-menu.md). Guardar el trabajo antes de confirmar una acción.

## Status bar

El chevrón expande o contrae tráfico, RAM, CPU, temperatura y disco. Clima,
paquetes, audio, Wi-Fi, batería y fecha permanecen visibles. El clic en la fecha
abre un calendario mensual: flechas o Page Up/Page Down para navegar,
Home/Today para volver al día actual y Escape para cerrar.

La batería muestra porcentaje y estado: rayo al cargar, verificación con carga
completa, pausa en estados pendientes e interrogación si el estado es desconocido.
Una lectura ausente muestra `--%`, no un cero inventado. La actualización usa
el tick compartido de 10 s. [Status bar](status-bar.md) detalla colores y controles.

## Lock and display

Bloqueo tras 5 min de inactividad y pantalla apagada tras 10 min. Para desbloquear,
introducir la contraseña de sesión y Enter; no hay eco de caracteres. Los mensajes
verifying/wrong corresponden a la autenticación de swaylock.

F1/F2 controlan brillo; según el teclado puede ser necesario Fn.
Las teclas de volumen utilizan PulseAudio. Super+Shift+C recarga configuración
sin cerrar aplicaciones ni reiniciar Sway.

## Battery inspection

```sh
upower -i /org/freedesktop/UPower/devices/DisplayDevice | grep -E '^[[:space:]]*(state|percentage):'
# Diagnóstico opcional de ciclos del dispositivo físico:
if [ -r /sys/class/power_supply/BAT0/cycle_count ]; then
    cat /sys/class/power_supply/BAT0/cycle_count
fi
```

Usar percentage para carga actual, no BAT0/capacity.
[Hardware and compatibility](initial-state.md), [Power and performance](optimizations.md).
Para una sesión alternativa, seguir [XFCE recovery](xfce-recovery.md).
