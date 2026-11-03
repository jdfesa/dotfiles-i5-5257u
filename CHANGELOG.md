# Changelog

## 2026-11-03

### Added

- Fuente Propo Regular de 2,45 MiB enlazada por archivo para iconos de barra,
  con versión, integridad y avisos conservados.
- Indicador de batería con nivel, estado de carga y porcentaje UPower permanente,
  usando glifos ya gestionados y el mismo tick de la barra.
- Grupo de métricas contraíble con chevrón, redibujado inmediato desde memoria
  y controles esenciales siempre visibles, sin nuevos procesos ni sondeo.
- Calendario GTK3 bajo demanda al pulsar la fecha, con navegación mensual,
  ventana única y configuración enlazada por manifiesto.
- Licencia MIT para el código y la documentación originales.
- Guía de restauración ordenada y perfiles declarativos de paquetes Debian.
- Pruebas del manifiesto completo sobre un hogar temporal, idempotencia y reversión.
- Comprobaciones de estructura, enlaces y exclusiones, con análisis opcional del historial Git.
- Cobertura de exclusión de árboles temporales en la publicación y las transferencias.

### Changed

- Perfil de Zed con modo Vim, mapa base Zed, tema Ayu Dark e iconos predeterminados;
  permisos de la fuente alineados con el modo 0644 del manifiesto.
- CPU y RAM muestran iconos diferenciados y porcentajes sin leyendas; clima usa
  los pictogramas de referencia sin alterar caché, unidades ni actualización.
- Documentación temática y procedimientos de restauración centralizados en docs/;
  README principal reducido a hardware, alcance y navegación.
- Paquetes, fuentes y manifiesto de recuperación XFCE aislados del perfil principal.
- Selección explícita de manifiesto mediante --manifest para perfiles independientes.
- Guías Git, GitHub CLI y RTK independientes de la configuración de cuentas.

### Fixed

- Control de retroiluminación del teclado en Sway mediante F5/F6 y UPower,
  con pasos del 10 %, apagado completo y llamadas acotadas, sin drivers externos,
  permisos nuevos ni procesos residentes adicionales.
- Icono de volumen unificado con la tipografía proporcional y separación reducida
  junto a Wi-Fi, sin modificar el indicador de red.
- Las lecturas malformadas del porcentaje UPower se tratan como no disponibles,
  sin interrumpir la barra.
- Autostart de brillo del perfil de recuperación dirigido al helper gestionado,
  sin depender de una ubicación obsoleta del checkout.

## 2026-11-02

### Added

- Sesión Sway/Wayland para MacBookPro12,1 con configuración modular por manifiesto.
- Kitty, Zsh, Starship, Fuzzel, notificaciones, bloqueo y gestión de inactividad.
- Barra nativa, fuentes, actualización acotada de clima/APT y carga UPower.
- Panel Wi-Fi compartido bajo demanda y menú de energía centrado con confirmación.
- Configuración de Zed estable y asociaciones web XDG de Helium.
- Despliegue con detección de conflictos, respaldos, reversión y pruebas de regresión.

### Changed

- Sway como sesión autenticada preferida; Zsh y Kitty como opciones predeterminadas.
- Super+Shift+B resuelve el navegador XDG; Super+Shift+Enter queda sin asignar.
- Zed disponible desde el lanzador, sin atajo de editor asignado.

### Fixed

- Cancelación del panel Wi-Fi sin falsos errores; fallos reales visibles.
- Estado del cliente Wi-Fi independiente del código de salida de Kitty.
- Comandos personalizados del prompt acotados y ejecutados mediante shell POSIX.
- Fallos de notificaciones sin interrupción de la barra.

## 2026-08-07

- Base de hardware, helper de brillo y referencias iniciales de dependencias.
