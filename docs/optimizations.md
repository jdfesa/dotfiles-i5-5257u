# Power and performance

## Baseline

Sway utiliza fondo sólido, barra opaca y escala entera 2. Kitty desactiva blur,
transparencia y animación de cursor. El perfil no instala un gestor de energía
adicional ni modifica límites de CPU. logind conserva las políticas de tapa e
inhibidores; swayidle bloquea antes de suspensión y administra inactividad.

CPU de referencia: intel_cpufreq con schedutil, rango observado 500–3100 MHz.
Cambiar TLP, perfiles de energía o límites exige medir primero batería, suspensión,
Wi-Fi y compilación. Menor memoria residente no demuestra por sí sola mayor autonomía.

## Background work

- Barra sobre tick i3status de 10 s; sin sondeo adicional para clicks.
- Clima mediante oneshot cada 30 min, con caché y timeout.
- Conteo APT con metadata local cada 6 h, sin instalar paquetes.
- Wi-Fi, lanzador y menú de energía se ejecutan a demanda.
- Starship limita comandos custom a 500 ms; la latencia total depende del proyecto.

## Storage

El SSD externo de referencia negocia USB 3/UAS. El puente informa rotational=1
y no expone descarte (discard_max_bytes=0); habilitar un timer fstrim no demuestra
soporte real de TRIM. Mantener mq-deadline hasta comparar cargas equivalentes.
Verificar SMART, enlace y comportamiento de descarte antes de cambiar reglas udev.

## Measurement procedure

Comparar brillo, conectividad, carga de batería, temperatura y trabajo equivalente.
Registrar consumo en reposo y durante compilación/navegación, así como duración
de una carga y recuperación de suspensión. No atribuir diferencias al compositor
si también cambiaron brillo, navegador, carga o estado de batería.

La batería de referencia conserva aproximadamente 62,9 % de su capacidad de
fábrica. La configuración no puede recuperar desgaste físico. Los ensayos de
autonomía y suspensión pendientes figuran en [TODO](../TODO.md).
