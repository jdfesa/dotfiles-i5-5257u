# Optimizaciones y prioridades

Fecha del diagnóstico: 2026-08-07.

## Aplicadas

### Indicador de batería y control de brillo

Se activó en la barra superior el complemento nativo del Gestor de energía de
XFCE. Reutiliza `upower` y `xfce4-power-manager`, que ya estaban instalados, por lo
que no fue necesario instalar paquetes adicionales.

### Brillo inicial local

Se programó un nivel inicial del 40% exclusivamente para el escritorio local. La
sesión actual era XRDP (`DISPLAY=:10`) y la pantalla física estaba en LightDM, por
lo que no se alteró desde la sesión remota.

## Diagnóstico del almacenamiento externo

- SSD: Kingston SV300S37A240G de 240 GB.
- Enlace: USB 3.0 SuperSpeed, 5 Gb/s.
- Protocolo: UAS, que permite una cola de E/S mejor que `usb-storage`.
- Sistema raíz: ext4, 211 GB, 4% ocupado.
- Planificador actual: `mq-deadline`.
- El puente USB anuncia el SSD como rotacional (`rotational=1`).
- El puente no anuncia descarte/TRIM (`discard_max_bytes=0`).
- `fstrim.timer` está habilitado semanalmente, pero el puente no expone soporte de
  descarte para este disco.

### Recomendación prioritaria

No cambiar aún el planificador ni crear reglas udev sin medir primero. El enlace
UAS ya es correcto. Conviene ejecutar en una próxima etapa:

- prueba reproducible de lectura/escritura que no destruya datos;
- lectura SMART del SSD mediante el puente USB;
- verificación explícita de `fstrim`;
- prueba del comportamiento con `rotational=0` antes de persistir una regla.

El sistema completo reside en un SSD externo antiguo: una copia de seguridad es
más prioritaria que una mejora marginal de rendimiento.

## Energía y temperatura

- CPU: controlador `intel_cpufreq`, gobernador `schedutil`, rango 500–3100 MHz.
- No están activos `power-profiles-daemon` ni TLP.
- CPU observada: 55–57 °C.
- Batería observada: 36,2 °C.
- No se instalará TLP ni se cambiarán límites de CPU sin medir primero consumo,
  suspensión, Wi-Fi y rendimiento de compilación. XFCE seguirá administrando
  pantalla, suspensión e indicadores.

## Batería

- Carga real observada por UPower: 99,8%.
- Salud: 62,9% de la capacidad de diseño.
- Ciclos: 1.407.

La prioridad operativa es avisar con suficiente anticipación y guardar el trabajo,
no intentar recalibrar por software una batería físicamente degradada.

