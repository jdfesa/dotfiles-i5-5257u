# Wi-Fi hotspot

## Prepare an optional profile

Este lanzador gestiona un punto de acceso creado en NetworkManager. No restaura
unidades de systemd, servicios independientes de DNS o reglas de cortafuegos
heredadas. No altera perfiles de Wi-Fi cliente. En una instalación migrada,
verificar que no se esté ejecutando otro hotspot antes de usar este.

1. Usar la consola local o una conexión de administración independiente: el
   modo AP puede desconectar la única interfaz Wi-Fi de su red habitual.
2. Simular los requisitos con python3 tools/restore-profile.py hotspot packages.
   Instalar con --apply solo tras revisar el plan; no se instala un servicio
   independiente de dnsmasq.
3. En nm-connection-editor crear un perfil Wi-Fi en modo Hotspot con IPv4
   compartido, WPA Personal y conexión automática desactivada. Elegir una
   clave fuerte. No mostrar ni guardar secreto, SSID ni UUID en Git. Se necesita
   una interfaz con capacidad AP y, para compartir Internet, otro enlace con
   salida. En el portátil se detectó capacidad AP; no se probó compartir tráfico.

## Operate on demand

Aplicar los enlaces de hotspot según [Optional restore profiles](../optional-profiles.md#plan-and-apply).
Obtener el UUID con nmcli -f NAME,UUID,TYPE connection show, seleccionar el
perfil de hotspot y asignar el UUID a la variable PROFILE_UUID:

```sh
mbp-wifi-hotspot status "$PROFILE_UUID"
mbp-wifi-hotspot start "$PROFILE_UUID"
mbp-wifi-hotspot stop "$PROFILE_UUID"
```

`start` exige confirmación. Tanto `start` como `stop` requieren terminal local,
sin sesiones SSH. No se cambian permisos de NetworkManager ni se requieren
reglas sudoers. Si la autorización local o el controlador impiden arrancar,
no forzar el cambio. Al terminar, detener el AP y verificar la reconexión a
la red habitual. Para quitar la integración, revertir los enlaces; el perfil
de red se administra por separado.
