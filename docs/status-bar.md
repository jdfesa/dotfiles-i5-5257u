# Status bar

## Appearance and blocks

Swaybar superior, opaca, Catppuccin Mocha; **JetBrainsMono Nerd Font Mono
Regular 10**, sin forzar Bold. Usa el protocolo i3bar compatible con Swaybar
y fuentes de iconos específicas por bloque. Solo escritorios
existentes; fecha en inglés, hora local 24 h y temperatura en °C.

### Icon typography

Los pictogramas de clima, métricas y audio usan **JetBrainsMono Nerd Font Propo
Regular 12**, para conservar su proporción sin comprimirlos a una celda.
El texto mantiene Mono 10; batería y Wi-Fi conservan sus fuentes específicas.
La procedencia, tamaño, licencia y hash del TTF se detallan en [Fonts](fonts.md).

CPU muestra un chip amarillo y el porcentaje; RAM, un módulo de memoria rosa
y el porcentaje, sin las leyendas redundantes. El clima usa iconos sólidos de
sol, luna y nube de Font Awesome; niebla y lluvia de Weather Icons; nieve y
tormenta de Material Design. Se conservan °C, el marcador `~` de caché y `--°C` sin datos.
Solo cambia la presentación de la muestra: no hay gráficos animados,
consultas nuevas ni cambios en los temporizadores de clima o en el tick de 10 s.

El volumen usa la misma fuente a 12 en sus estados normal, silencio y sin audio.
Su área mínima es de 24 píxeles lógicos y el espacio posterior es de 4, para
mantenerlo próximo a Wi-Fi. El icono Wi-Fi conserva BGH Status Icons 12, su área
mínima de 28 y su separación posterior de 12; no cambia su acción de clic.

| Bloque | Dato / acción |
|---|---|
| Clima | Icono y temperatura de Orán; sin geolocalización ni nombre de ciudad |
| ↑ / ↓ | Tráfico Wi-Fi por delta de contadores; K=KiB/s, M=MiB/s |
| RAM / CPU | MemAvailable y uso agregado |
| Temperatura | Sensor coretemp/x86_pkg_temp detectado al iniciar |
| Disco | Espacio libre de `/`; G=GiB |
| Paquetes | Candidatos de metadata local APT; click / Super+U |
| Audio | Icono de volumen/mute; click / Super+A abre alsamixer |
| Wi-Fi | Solo icono de calidad, calidad de señal; click / Super+N |
| Batería | Icono según estado y nivel, más porcentaje real de UPower; siempre visible |
| US / ES | Distribución real del teclado; clic izquierdo alterna US / español de España |
| Reloj | Fecha en inglés y hora local; clic izquierdo abre el calendario |

La interfaz inalámbrica se detecta desde sysfs (en este equipo `wlp3s0`), se configura según el hardware detectado. Los clicks ejecutan acciones fijas por
`swaymsg`; no se interpolan nombres de redes ni eventos como comandos de shell.

## Battery indicator

El indicador usa `State` y `Percentage` del dispositivo agregado `DisplayDevice`
de [UPower](https://upower.freedesktop.org/docs/Device.html), no la salud,
la capacidad de diseño ni los ciclos. El porcentaje se redondea para mostrarlo
sin decimales; no se modifica el dato de origen ni se fuerza a 100 %.

| UPower state | Presentation |
|---|---|
| `discharging` / `empty` | Batería con relleno por tramos de 10 % y porcentaje |
| `charging` | Batería con rayo y relleno según nivel; porcentaje visible incluso a 100 % |
| `fully-charged` | Batería con marca de verificación; conserva el porcentaje informado |
| `pending-charge` / `pending-discharge` | Batería con pausa; no afirma carga activa |
| Estado desconocido | Icono de batería con interrogación y porcentaje, si está disponible |
| Lectura ausente, inválida o error de UPower | Icono desconocido y `--%`; nunca inventa `0%` |

En descarga, el icono es verde por encima de 40 %, naranja por encima de 20 %
y hasta 40 %, y rojo hasta 20 %; en este último tramo también se resalta el
porcentaje. Los estados de carga activa y completa usan verde; los pendientes,
amarillo. Los avisos al bajar de 20/10 % mientras descarga se conservan, sin
nuevos avisos por redibujar o contraer la barra. Estar al 100 % no se interpreta
por sí solo como carga completa: se respeta el estado informado por UPower.

Los iconos Material Design ya están en la fuente gestionada Nerd Font; su
relleno diferencia niveles sin depender solo del color. El icono usa tamaño
12 y el porcentaje conserva el texto de la barra a 10. No se instala otra
fuente ni se cambia la tipografía de la terminal.

El formateo es puro: reutiliza la consulta de UPower del tick compartido de 10 s,
con timeout de 5 s. No consulta sensores, red o archivos, ni crea procesos
adicionales. El cambio aparece en el siguiente tick que recibe el nuevo estado
de UPower. Si el backend omite el bloque de batería, el adaptador lo repone
con los datos disponibles o con `--%`.

## Collapsible metrics

La barra inicia en modo compacto. El chevrón situado antes de los paquetes
permite ocultar o mostrar el grupo secundario: tráfico Wi-Fi, RAM, CPU,
temperatura y espacio de disco. Clima, paquetes, audio, Wi-Fi, batería con su
porcentaje, selector US/ES y fecha permanecen visibles. Un bloque marcado explícitamente
como urgente por el productor tampoco se oculta.

- `›`: grupo contraído; clic izquierdo para expandir.
- `‹`: grupo expandido; clic izquierdo para contraer.
- La preferencia vive en memoria y vuelve al modo compacto al recargar la barra.

El clic redibuja inmediatamente la última muestra formateada: no ejecuta un
comando, no relee contadores ni vuelve a consultar UPower. El mismo adaptador
conserva el muestreo compartido cada 10 s incluso con las métricas ocultas,
para mantener coherentes las tasas de tráfico al expandir. No hay demonios,
temporizadores, animaciones ni archivos de estado adicionales. La contracción
reduce ocupación visual; no se presenta como una mejora medida de autonomía.

## Keyboard layout selector

El botón de texto **US** / **ES**, inmediatamente a la izquierda de la fecha,
alterna con un clic izquierdo entre inglés de Estados Unidos (`us`) y español
de España (`es`, no `latam`). Permanece visible con las métricas contraídas.
La selección es manual y global para los teclados conectados; no detecta
automáticamente si el teclado físico es externo o integrado.

Verificado en la sesión Sway del equipo: el clic alterna la distribución y
su etiqueta junto a la fecha; los cambios externos también llegan por eventos.
La comprobación tras un nuevo login y la conexión/desconexión del teclado
externo se mantienen por separado en TODO.md.

La configuración pública declara `input type:keyboard` con `xkb_layout us,es`
después del include local, para superar el antiguo override genérico US.
US es la primera distribución y la predeterminada al iniciar una sesión nueva.
El clic cambia un índice fijo 0/1 mediante Sway IPC y confirma el resultado;
no interpreta texto del evento ni identificadores de dispositivos como comandos.

El adaptador existente recibe eventos `input` por un socket Unix de Sway y
actualiza solo este control sobre la muestra guardada en memoria. No hay
otro proceso residente, temporizador, archivo de estado ni consulta periódica
de distribución. El tick de sensores sigue siendo de 10 s; un clic o evento
de distribución no vuelve a consultar batería, tráfico o sensores.

El texto refleja el estado informado por Sway, no una suposición. Si faltan
datos, la configuración no corresponde a US/ES o los teclados divergen, muestra
`--`. Si todos admiten US/ES pero tienen índices distintos, el siguiente clic
los unifica en US. Los cambios externos y conexiones/desconexiones actualizan
el indicador por eventos. Si se pierde el socket de eventos, recargar la barra
para restablecer la suscripción; no se inventa una distribución.

Referencia: [Sway input manual](https://manpages.debian.org/trixie/sway/sway-input.5.en.html)
y [Sway IPC manual](https://manpages.debian.org/trixie/sway/sway-ipc.7.en.html).

## Calendar

El clic izquierdo sobre la fecha abre `mbp-calendar`: una ventana flotante
centrada, nativa de Wayland y con el tema Mocha. Permite consultar meses y años;
no es una agenda, no sincroniza cuentas ni modifica la fecha del sistema.

- Flechas del calendario: cambiar el mes o el año.
- `Page Up` / `Page Down`: mes anterior / siguiente.
- `Today` o `Home`: volver a la fecha actual; el día actual aparece marcado.
- `Close`, `Escape` o el atajo habitual `Super+W`: cerrar la ventana.
- Otro clic en la fecha presenta la ventana existente, sin duplicarla.

Se utiliza [Gtk.Calendar](https://docs.gtk.org/gtk3/class.Calendar.html)
mediante `python3-gi` y `gir1.2-gtk-3.0`, declarados en la lista de paquetes.
La instancia única se gestiona con Gtk.Application, sin servidor propio,
sondeo, temporizador, red, autostart ni terminal adicional. El proceso existe
solo mientras la ventana está abierta y termina al cerrar la última ventana.
No cambia el ciclo de actualización de la barra.

El manifiesto enlaza `scripts/calendar-popup.py` a `~/.local/bin/mbp-calendar`
y `config/calendar/calendar.css` a `~/.config/calendar/calendar.css`.
La regla de Sway se limita al identificador `local.mbp.Calendar`; el clic
solo acepta el bloque `tztime` / instancia `local` y ejecuta una acción fija.

### Resource profile

En el i5-5257U, una muestra de 5 s con la ventana abierta en reposo registró
52,4 MiB de RSS y 27,4 MiB de PSS (memoria proporcional, descontando la parte
compartida con otros procesos), sin incremento de tiempo de CPU en ese intervalo.
El cierre de la ventana terminó el proceso; una segunda apertura presentó la
misma ventana sin crear otra instancia residente. Son observaciones puntuales,
no una garantía de consumo constante ni una medición de autonomía de la batería.

## Dependencies and installation

Fuente: [i3status Debian](https://packages.debian.org/trixie/i3status),
[i3bar protocol](https://i3wm.org/docs/i3bar-protocol.html). Versiones e integridad en
[Dependencies](dependencies.md); fuentes y SHA256 en
[Fonts](fonts.md).

```sh
apt-get -s --no-install-recommends --no-remove install i3status python3-gi gir1.2-gtk-3.0
sudo apt-get --no-install-recommends --no-remove install i3status python3-gi gir1.2-gtk-3.0
# Aplicar manifiesto como jd antes de iniciar los timers:
fc-cache "$HOME/.local/share/fonts"
systemctl --user daemon-reload
systemctl --user enable --now mbp-weather-refresh.timer mbp-packages-refresh.timer
systemctl --user start mbp-weather-refresh.service mbp-packages-refresh.service
```

El manifiesto enlaza archivos públicos de fuentes, configuración y unidades
`systemd --user`; no son enlaces de archivos del sistema. Los TTF coinciden con
los hashes de la referencia y preservan licencia/procedencia. Sin recompilación,
colección completa de fuentes ni descargas durante el inicio de la sesión.

La muestra nativa detecta `wlp3s0`, muestra carga UPower real y resuelve ambas
familias de fuentes. La vista compacta conserva los controles esenciales y
la expandida añade las métricas secundarias. Revalidar apariencia y clics
después de restaurar.

## Scheduling and private state

- i3status obtiene datos cada **10 s**. El adaptador residente espera eventos con
  selectores, aplica formato, lee contadores en ese tick y consulta carga UPower.
- Clima: [Open-Meteo HTTPS](https://open-meteo.com/en/docs), centro público de
  Orán definido en `config/status/weather.json`, cada **30 min** mediante oneshot.
  Timeout 20 s / servicio 30 s; cache de hasta 3 h se marca `~` al fallar,
  vencida/ausente muestra `--°C`. Sin GPS o geolocalización por IP.
- Paquetes: cada **6 h**, `apt-get --simulate upgrade` con índices existentes,
  sin sudo, descargas, actualización de índices ni instalación automática.
- Caches: `~/.cache/mbp-sway/`, fuera del repo. Unidades con umask 0077,
  `NoNewPrivileges=yes`, `Nice=10`. No hay clientes Python de clima residentes.
- Avisos de batería al bajar de 20/10 % mientras descarga, suplementarios a UPower.
- Respetar SIGSTOP/SIGCONT del grupo de procesos de Swaybar; no señales USR
  personalizadas ni polling adicional para los clicks.

## Verification and recovery

```sh
~/.local/bin/mbp-status-adapter --run-once
upower -i /org/freedesktop/UPower/devices/DisplayDevice | grep -E '^[[:space:]]*(state|percentage):'
python3 -m unittest discover -s tests -p test_battery.py -v
fc-match 'JetBrainsMono Nerd Font Mono'
fc-match 'BGH Status Icons'
systemctl --user list-timers 'mbp-*'
python3 -m unittest discover -s tests -v
```

Tras un cambio de configuración, `swaymsg reload` debe renovar la barra; verificar
que no queden dos adaptadores. La lectura `--run-once` es diagnóstica y no lanza
avisos. Revalidar clicks/fontes/fullscreen con la sesión local; un parser no
prueba la apariencia exacta o la autonomía.

Para retirar tareas, deshabilitar primero los dos timers y detener servicios
oneshot, luego revertir los enlaces de ese despliegue. Mantener las fuentes si
las usan otros programas. No borrar journals hasta verificar recuperación.
