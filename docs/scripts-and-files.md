# Scripts y archivos auxiliares

Este documento inventaría toda automatización creada para el equipo. Cada futuro
script `.sh` o `.py` debe añadirse aquí con su propósito, requisitos, efectos,
verificación y reversión.

## `scripts/set-local-brightness.sh`

### Propósito

Ajustar el brillo inicial de la pantalla integrada al 40% al entrar en una sesión
XFCE local. El rango detectado es 0–1388 y el valor configurado es 555.

### Comportamiento y seguridad

- Solo actúa cuando `DISPLAY` es `:0` o `:0.0`.
- En XRDP, SSH sin escritorio u otra pantalla termina correctamente sin cambiar
  hardware.
- Espera cinco segundos para que la sesión local y PolicyKit estén activos.
- Usa `/usr/sbin/xfpm-power-backlight-helper`, provisto por XFCE.
- Usa PolicyKit sin agente interno. La política instalada permite la acción sin
  contraseña únicamente a un usuario local activo.
- No modifica archivos del sistema ni necesita una regla personalizada de `sudo`.

### Requisitos

- Paquete `xfce4-power-manager`.
- `pkexec` y PolicyKit activos.
- Interfaz de brillo reconocida por el kernel.

### Ejecución

XFCE lo ejecuta mediante:

```text
~/.config/autostart/mbp2015-brightness.desktop
```

No debe probarse desde XRDP esperando que cambie la pantalla física: por diseño no
hace nada allí.

### Verificación

En una sesión local, después de iniciar XFCE:

```bash
cat /sys/class/backlight/intel_backlight/brightness
```

El resultado inicial esperado es `555`. El usuario puede cambiarlo después desde
el icono del Gestor de energía o con las teclas de brillo.

### Reversión

Desactivar **Brillo inicial MBP 2015** en **Sesión e inicio > Inicio automático de
aplicaciones**. También puede retirarse la entrada de autoinicio; el script por sí
solo nunca se ejecuta automáticamente.

## `~/.config/autostart/mbp2015-brightness.desktop`

Entrada estándar de autoinicio de XFCE. No contiene lógica de optimización: llama
al script anterior. Su copia reproducible está versionada en
`config/autostart/mbp2015-brightness.desktop`; XFCE utiliza la copia desplegada en
`~/.config/autostart`.

Para restaurarla en este equipo:

```bash
cp config/autostart/mbp2015-brightness.desktop \
  ~/.config/autostart/mbp2015-brightness.desktop
```

## Política para automatizaciones futuras

Antes de incorporar otro script se documentará:

1. Problema medido que resuelve.
2. Parámetros y valores predeterminados.
3. Dependencias y privilegios.
4. Archivos o estado que modifica.
5. Procedimiento de prueba.
6. Procedimiento de reversión.
