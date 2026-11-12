# Wi-Fi driver recovery

## Symptoms and diagnosis

En la BCM43602 del MacBookPro12,1, brcmfmac dejó de responder después de reanudar
una suspensión profunda con el núcleo `6.12.115+deb13.1-amd64`. La radio seguía
`enabled`, sin bloqueo físico ni lógico, pero no aparecía ninguna red.
El registro mostró `brcmf_msgbuf_query_dcmd: Timeout on response for query command`,
`Failed to reserve space in commonring` y errores de escaneo `-5`/`-12`.

La causa inmediata fue el bloqueo del controlador/firmware tras la reanudación;
no se ha determinado el defecto exacto que lo desencadena. Una lista vacía,
incluso si nmcli termina con éxito, no basta por sí sola para diagnosticarlo.
Consultar el registro antes de cambiar perfiles o contraseñas:

```sh
rtk proxy pkexec /usr/bin/journalctl -k -b --no-pager --grep='brcmf|PM: suspend' -n 100
rtk proxy nmcli radio all
rtk proxy nmcli device wifi list ifname wlp3s0 --rescan yes
```

## Controller reset

Ejecutar desde una terminal local con la autorización normal del sistema:

```sh
rtk proxy pkexec /usr/bin/bash -c '
set -eu
/usr/sbin/modprobe -r brcmfmac_wcc brcmfmac
/usr/sbin/modprobe brcmfmac
'
```

`brcmfmac_wcc` mantiene una referencia a brcmfmac: intentar retirar solo
`brcmfmac` devuelve `Module brcmfmac is in use`. No forzar la descarga.
El reset interrumpe el Wi-Fi y NetworkManager puede reconectar una red guardada;
no ejecutarlo mediante SSH si esa sesión depende del Wi-Fi. No reinicia
NetworkManager ni requiere apagar la conexión USB del teléfono.

## Verification

```sh
rtk proxy nmcli -f DEVICE,TYPE,STATE,CONNECTION device status
rtk proxy nmcli device wifi list ifname wlp3s0 --rescan yes
rtk proxy curl --interface wlp3s0 --connect-timeout 5 --max-time 12 \
    --silent --show-error --output /dev/null --write-out 'Wi-Fi HTTPS status: %{http_code}\n' \
    https://deb.debian.org/debian/
```

La recuperación comprobada volvió a detectar redes, reconectó un perfil guardado
y obtuvo HTTP 200 por Wi-Fi, manteniendo activo el enlace USB. **Super+N** abre
el [Wi-Fi panel](../wifi-setup.md) para elegir otra red.

Es una recuperación puntual, no una corrección permanente validada para la
suspensión. No se instalaron servicios, reinicios automáticos ni cambios de
ahorro de energía.
