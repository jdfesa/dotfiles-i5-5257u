# Wi-Fi panel

## Entry points

- **Super+N**, click izquierdo en el icono Wi-Fi o **Wi-Fi networks** en Fuzzel:
  todos abren `~/.local/bin/mbp-open-networks`.
- Se pide un escaneo nuevo una vez al abrir. La lista marca la conexión activa;
  usar flechas/Tab/Enter para elegir y Escape/Back para salir.
- Seleccionar otra red puede interrumpir SSH: no hacerlo como prueba remota sin
  coordinación. No se desconecta ni cambia de red automáticamente al abrir.
- Un segundo acceso enfoca el panel existente. Para pedir otro escaneo manual,
  cerrar el panel y volver a abrirlo. No se añaden servicios de sondeo.
- Super+W cierra el panel como cancelación normal, sin aviso de fallo. El cliente
  TUI maneja HUP/TERM por cierre de ventana; una salida no cero sin esa señal
  sigue tratándose como error. No se ignoran indiscriminadamente los errores.

El helper no recorta la lista a redes conocidas ni a la red conectada: muestra
lo que NetworkManager ofrece a nmtui. Si un escaneo encuentra solo un AP, no
se inventan redes adicionales; revisar radio, alcance y controlador si se
esperaban otras. Un fallo de escaneo muestra aviso y deja disponible la caché.

## Components and configuration

Se reutilizan NetworkManager/nmcli/nmtui y nm-connection-editor ya instalados;
versiones en [Dependencies](dependencies.md). Fuentes oficiales:
[nmtui](https://networkmanager.dev/docs/api/latest/nmtui.html),
[nmcli Debian](https://manpages.debian.org/trixie/network-manager/nmcli.1.en.html).
No se instala otro gestor de red, agente de secretos persistente o regla Polkit.

`scripts/open-networks.sh` se enlaza como `mbp-open-networks`, y la entrada de
`config/network/` se enlaza a `~/.local/share/applications/`. Modos y destinos
exactos están en el manifiesto. El helper requiere sesión Wayland y runtime
del usuario, mantiene un lock mientras el panel vive y usa comandos fijos.
NetworkManager administra los perfiles y solicita los datos de conexión.

El panel usa `kitty --class=mbp-networks ... sh -c COMANDO`, que reemplaza la
shell de login por el cliente. No usar el alias nmtui-connect como login shell:
un argv0 con prefijo `-` impide su dispatch. Kitty no propaga errores del hijo;
un resultado privado por apertura en XDG_RUNTIME_DIR conserva el estado nmtui.
El trap EXIT lo escribe (HUP/TERM cancelan con 0), el helper lo verifica y borra
al terminar. Un resultado ausente también informa fallo. El resultado contiene únicamente el código de salida.

## Advanced and institute networks

```sh
~/.local/bin/mbp-open-networks --edit
```

Abre el editor gráfico ya existente para crear/modificar perfiles, incluidas
redes ocultas o configuraciones que la TUI no exponga. Para WPA-Enterprise/802.1X
se necesitan los datos oficiales del instituto (EAP, dominio/servidor y CA);
no deshabilitar la verificación de certificados para lograr conexión. Un portal
cautivo puede necesitar completar el acceso en el navegador después de conectar.

El funcionamiento con una red empresarial requiere comprobar sus parámetros
y autenticación; abrir la lista no valida una conexión diferente.

## Read-only checks and recovery

```sh
~/.local/bin/mbp-open-networks --check     # Sin escaneo ni ventana
nmcli -f DEVICE,TYPE,STATE device status
nmcli radio wifi
```

En una TTY puede usarse directamente `nmtui connect`. Si la radio está apagada,
activarla deliberadamente con `nmcli radio wifi on` desde la sesión local; un
bloqueo físico requiere revisar el dispositivo. No hay fallback sudo ni bypass
de permisos. SSH y la sesión local pueden tener autorizaciones diferentes.

Validar apertura/foco/cancelación sin activar otra red, sintaxis con `sh -n` y
regresiones con comandos simulados. La reversión restaura los archivos públicos
desde backup y sus enlaces; no borrar ni modificar perfiles de NetworkManager.

Comprobar Super+N, click de barra, escaneo y cancelación después de restaurar.
Las pruebas de transición/autenticación se realizan de forma separada.
