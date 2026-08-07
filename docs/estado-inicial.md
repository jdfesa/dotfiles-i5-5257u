# Estado inicial y cambios

Fecha del relevamiento: 2026-08-07.

## Equipo

- Modelo: Apple MacBook Pro 13-inch Early 2015 (`MacBookPro12,1`).
- Procesador: Intel Core i5-5257U, 2 núcleos y 4 hilos, 2.7 GHz.
- Gráficos: Intel Iris Graphics 6100, controlador `i915`.
- Memoria: 7.7 GiB utilizables.
- Sistema: Debian 13 (trixie), kernel 6.12, escritorio XFCE.
- Disco del sistema: Kingston SV300S37A240G de 240 GB conectado por USB 3.
- Disco interno: Apple SSD de 256 GB con APFS, no montado.
- Pantalla interna: eDP, controlada por `intel_backlight`.

## Batería

- Fabricante/controlador: SMP `bq20z451`.
- Ciclos registrados: 1.407.
- Capacidad máxima actual: 4.123.000 µAh.
- Capacidad de diseño: 6.559.000 µAh.
- Salud estimada: 62,9% de la capacidad original.
- Temperatura observada: 36,3 °C.

La batería está bastante degradada. No conviene confiar únicamente en el tiempo
restante estimado: guardar el trabajo con frecuencia y conectar el cargador antes
de llegar al nivel crítico.

## Cambios aplicados

- Se creó `~/github/mbp2015/docs`.
- Se añadió el complemento nativo **Gestor de energía** al panel superior de XFCE.
  El complemento ya estaba instalado; muestra el estado de la batería y ofrece
  un control deslizante para el brillo.
- Se configuró un brillo inicial del 40% para las sesiones XFCE locales mediante
  `scripts/set-local-brightness.sh`. El ajuste se aplica cinco segundos después
  de entrar al escritorio y puede cambiarse luego desde el panel o el teclado.

## Estado del brillo al iniciar el trabajo

- Interfaz: `/sys/class/backlight/intel_backlight`.
- Rango: 0–1388.
- Valor configurado inicialmente: 1041 (aproximadamente 75%).
- Valor elegido para las próximas sesiones locales: 555 (aproximadamente 40%).

La pantalla local estaba en el inicio de sesión de LightDM durante el trabajo y
la sesión XFCE activa era remota (`DISPLAY=:10`). Por eso el valor físico no se
forzó desde SSH; se aplicará en el siguiente inicio de sesión local.
