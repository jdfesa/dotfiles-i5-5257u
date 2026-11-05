# Keyboard shortcuts

`Super` es la tecla **Command** del Mac (`Mod4`). La base preferida es Omarchy,
usando el mapa mantenido del equipo i3 de referencia y adaptando las acciones a
Wayland. No se importa X11 de la referencia ni la distribución Omarchy completa.
Fuentes: `config/sway/config`, `config/sway/trackpad-gestures.conf` y ayuda visible
`config/sway/keybindings-help.txt`.

| Atajo | Acción |
|---|---|
| Super+Enter | Kitty |
| Super+Espacio o D | Fuzzel; busca aplicaciones .desktop, incluida Wi-Fi networks |
| Super+Shift+B | Navegador predeterminado XDG; actualmente Helium |
| Super+N | Panel Wi-Fi: escaneo a demanda y nmtui connect en terminal flotante |
| Super+A | Mezclador alsamixer |
| Super+U | APT: lista desde metadata local, sin actualizar/instalar |
| Super+K | Ayuda filtrable de atajos; Esc cierra |
| Super+Shift+P | Menú de energía, confirmaciones; Esc/No cancela |
| Super+W, Q o Shift+Q | Cerrar ventana |
| Super+flechas | Foco |
| Super+Shift+flechas | Mover ventana |
| Super+1…9, 0 | Escritorios 1…10 |
| Deslizamiento de tres dedos | [Trackpad gestures](trackpad-gestures.md): izquierda, siguiente; derecha, anterior en la misma pantalla |
| Super+Shift+número | Enviar ventana, sin seguirla |
| Super+B / V | División horizontal / vertical |
| Super+J o E | Alternar división |
| Super+L | División / pestañas / apilado |
| Super+Ctrl+W / S | Pestañas / apilado |
| Super+F | Pantalla completa |
| Super+T o Shift+Espacio | Flotante / mosaico |
| Super+Tab | Foco entre capa flotante y mosaico |
| Super+S / Alt+S | Mostrar scratchpad / enviar ventana al scratchpad |
| Super+R | Tamaño: flechas o H/J/K/L; Enter/Esc sale |
| Super+Ctrl+L | Bloquear con swaylock |
| Super+Shift+C o R | Recargar Sway; R **no reinicia** el compositor |
| Super+Shift+E | Cerrar sesión; Y confirma, N/Esc cancela |
| Botón US / ES junto a la fecha | Clic izquierdo alterna inglés US / español de España |
| F1 / F2, posiblemente con Fn | Brillo de pantalla -/+5 % |
| F5 / F6, posiblemente con Fn | Brillo de teclado -/+10 % mediante UPower; permite apagarlo |
| Teclas de volumen/silencio | PulseAudio existente |
| Super+Shift+S o Print | Selección de captura al portapapeles; sin copia persistente |
| Ctrl+Shift+C / V | Copiar/pegar en Kitty |

[Keyboard backlight](keyboard-backlight.md) describe el controlador nativo y la verificación de F5/F6.

Helium también permanece en Fuzzel. Zed se abre desde Fuzzel o con `zed`, sin
atajo asignado hasta acordarlo. Super+Shift+Enter queda libre: no es alias del
navegador ni se reasigna automáticamente al editor.

La [Status bar](status-bar.md) reproduce el diseño de referencia con tick de 10 s,
clicks de red/audio/paquetes y cachés de clima/actualizaciones. La batería se
obtiene de UPower; no de `BAT0/capacity`, que aquí representa salud.

El bloqueo tras 5 minutos usa la contraseña normal de jd, sin eco de caracteres.
Enter vacío puede mostrar «wrong»; «verifying» es la comprobación PAM normal.
