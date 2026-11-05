# TODO

## Restoration

- [ ] Probar la guía completa de restauración en una instalación limpia de Debian 13;
      las pruebas con un directorio personal temporal no cubren el instalador del
      sistema, el gestor de acceso ni PAM.

## Hardware validation

- [ ] Revalidar el selector US/ES tras un nuevo login de Sway y al conectar o
      desconectar el teclado externo.
- [ ] Comprobar en el trackpad el toque, el clic secundario, el desplazamiento con
      dos dedos y el zoom con pinza en una aplicación Wayland compatible.
      Véase [Trackpad gestures](docs/trackpad-gestures.md).
- [ ] Medir el consumo con el mismo brillo y cargas de trabajo representativas.
- [ ] Verificar la tapa, la suspensión y reanudación, el comportamiento con batería
      baja y el ahorro de energía de la pantalla.
- [ ] Validar el aviso previo al bloqueo y repetir F5/F6 de retroiluminación tras
      iniciar una nueva sesión autenticada de Sway.
- [ ] Validar las acciones pendientes de audio y paquetes de la barra, y las teclas
      de brillo y volumen.
- [ ] Probar la autenticación Wi-Fi del instituto y los portales cautivos cuando
      corresponda.
- [ ] Integrar la compartición de pantalla del navegador con PipeWire/portal-wlr
      si se requiere.

## Development environment

- [ ] Acordar un atajo para el editor; Zed permanece accesible solo desde el lanzador.
- [ ] Seleccionar los entornos de ejecución, servidores LSP y extensiones para los
      lenguajes del instituto, y probar proyectos reales.
- [ ] Revisar la actualización de Helium del proveedor y coordinar el reinicio
      del navegador.
- [ ] Revisar las actualizaciones generales de mantenimiento de Debian.

## Optional workflow improvements

- [ ] Evaluar archivos pequeños incluidos desde Sway para atajos, apariencia y reglas
      de ventanas, sin cambiar las asignaciones de teclas ni el contrato de enlaces
      por archivo del manifiesto.
- [ ] Evaluar un selector de ventanas bajo demanda mediante Sway IPC y Fuzzel,
      con identificadores de contenedor validados y sin otro proceso residente.
- [ ] Integrar la vista de miniaturas del escritorio actual con `woverview --current`
      y un deslizamiento de tres dedos hacia arriba cuando la sesión principal tenga
      Sway 1.12 o posterior desde una fuente compatible con Debian estable. Validar el
      gesto en la sesión principal; la captura por ventana se comprobó en una sesión
      aislada con Sway 1.12. No habilitar esta integración en Sway 1.10.1.
- [ ] Evaluar marcadores por categorías mediante Fuzzel y el navegador XDG
      predeterminado, con selecciones inequívocas y URL HTTP/HTTPS validadas.
