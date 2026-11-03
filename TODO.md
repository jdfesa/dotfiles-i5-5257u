# TODO

## Restoration

- [ ] Probar la guía completa de restauración en una instalación limpia de Debian 13;
      las pruebas con un directorio personal temporal no cubren el instalador del
      sistema, el gestor de acceso ni PAM.

## Hardware validation

- [ ] Verificar la compatibilidad de los gestos multitáctiles del trackpad con
      libinput/Sway, incluida la configuración disponible y las limitaciones del modelo.
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
- [ ] Reconciliar el perfil de Zed modificado en el portátil con la copia local,
      preservando sus opciones y revisando los permisos de la fuente gestionada.

## Optional workflow improvements

- [ ] Evaluar archivos pequeños incluidos desde Sway para atajos, apariencia y reglas
      de ventanas, sin cambiar las asignaciones de teclas ni el contrato de enlaces
      por archivo del manifiesto.
- [ ] Evaluar un selector de ventanas bajo demanda mediante Sway IPC y Fuzzel,
      con identificadores de contenedor validados y sin otro proceso residente.
- [ ] Evaluar marcadores por categorías mediante Fuzzel y el navegador XDG
      predeterminado, con selecciones inequívocas y URL HTTP/HTTPS validadas.
