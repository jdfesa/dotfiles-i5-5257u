# Lid power policy

## Portable mode

Este perfil opcional usa la suspensión normal de logind. Con la tapa cerrada
y sin dock ni pantallas externas adicionales, arma una alarma única de
**20 minutos desde el inicio de la suspensión**. Abrir la tapa cancela esa
alarma; un cierre posterior empieza un plazo nuevo al volver a suspender.
No hay apagado por inactividad con la tapa abierta.

El despertador usa el tiempo transcurrido durante la suspensión, no la hora
civil. Tras vencer espera 3 s para procesar los eventos de reanudación, comprueba
que hubo suspensión real y que tanto ACPI como logind indican que la tapa
sigue cerrada. Si no puede verificarlo, no pide el apagado. Al conectar un dock
o pantallas adicionales, se conserva la política de logind de ignorar la tapa.
Si otro evento despierta el portátil antes del plazo sin abrir la tapa, la
alarma original sigue armada; el auxiliar no provoca otra suspensión.

El apagado, si se habilita, **cierra la sesión y se puede perder trabajo sin
guardar**. No se envía SIGKILL a las aplicaciones ni se inicia un apagado
forzado: logind puede retrasar o impedir el apagado si hay inhibidores.
El perfil configura también la suspensión por tapa para respetar inhibidores.
El menú manual conserva su confirmación; el bloqueo previo de Sway sigue a
cargo de swayidle.

El perfil selecciona `s2idle` solo para la suspensión elegible con tapa
cerrada y restaura el modo anterior tras reanudar. Con tapa abierta, sin
el perfil armado o con un dock, conserva el modo original. Si no puede
seleccionar `s2idle`, no arma el apagado. No combinarlo con overrides
`MemorySleepMode=` ni `SuspendState=` que reemplacen el modo de esta suspensión.
No se modifica el swap ni la hibernación, que guarda y restaura la sesión.

### Hardware validation

En el MacBookPro12,1, el ensayo con alarma interna de 60 s y la tapa cerrada
durante aproximadamente 90 s confirmó que `s2idle` reanudó al cabo de 61 s;
el auxiliar registró la solicitud simulada antes de abrir la tapa. Con
`deep`/S3, el equipo no despertó al cumplirse el plazo en el ensayo equivalente;
sí se comprobó la cancelación al abrir antes de tiempo y el bloqueo de sesión.

El plazo operativo de **1200 s** usa el mismo mecanismo de alarma. Se infiere
que funcionará con ese intervalo, pero no se validó físicamente a 20 minutos
ni se ejecutó un apagado real durante las pruebas. No se midió el consumo
comparativo de los modos.

## Install in trial mode

Usar la consola local, con trabajo guardado y espacio para recuperar el
equipo. Debian 13 ya proporciona Python 3.13, PyGObject, systemd/logind 257 y
el controlador RTC; no se añade ningún paquete. No se inicia un daemon al
arrancar: el auxiliar se ejecuta solo al comenzar la suspensión y sale al
cancelarse o al vencer el plazo. Si otro gestor controla la tapa o falla el
auxiliar, no hay apagado por este perfil.

Desde la raíz del checkout, revisar los cinco destinos antes de copiar. El
bloque rechaza archivos preexistentes, incluso enlaces rotos; para actualizar
una instalación anterior, hacer un respaldo externo y comparar los archivos.
Los archivos de sistema deben ser copias normales de root, no enlaces al
repositorio.

```sh
(
    set -eu
    helper=/usr/local/libexec/mbp-lid-poweroff.py
    unit=/etc/systemd/system/mbp-lid-poweroff.service
    hook=/etc/systemd/system/systemd-suspend.service.d/60-mbp-lid-poweroff.conf
    lid=/etc/systemd/logind.conf.d/60-mbp-lid-poweroff.conf
    settings=/etc/default/mbp-lid-poweroff
    src=config/power/lid-poweroff

    for path in "$helper" "$unit" "$hook" "$lid" "$settings"; do
        if sudo test -e "$path" || sudo test -L "$path"; then
            printf 'Existing destination: %s\n' "$path" >&2
            exit 1
        fi
    done
    sudo mkdir -p /usr/local/libexec /etc/systemd/system/systemd-suspend.service.d /etc/systemd/logind.conf.d
    sudo install -o root -g root -m 0644 scripts/lid-poweroff.py "$helper"
    sudo install -o root -g root -m 0644 "$src/mbp-lid-poweroff.service" "$unit"
    sudo install -o root -g root -m 0644 "$src/suspend-hook.conf" "$hook"
    sudo install -o root -g root -m 0644 "$src/lid-switch.conf" "$lid"
    sudo install -o root -g root -m 0644 "$src/settings.conf" "$settings"

    sudo systemd-analyze verify --man=no "$unit" systemd-suspend.service
    sudo systemctl daemon-reload
)
```

Revisar `systemd-analyze cat-config systemd/logind.conf` para detectar
overrides posteriores. En Debian 13, comprobar
`systemctl show -P CanReload systemd-logind.service` y, si devuelve `yes`,
aplicar el cambio con `sudo systemctl reload systemd-logind.service`, con la
tapa abierta. Si no admite recarga, aplicar en el próximo reinicio local
planificado; no reiniciar logind desde una sesión gráfica o SSH.
No usar `systemctl enable` para el auxiliar.

## Verify and enable poweroff

1. Con tapa abierta, editar `sudoedit /etc/default/mbp-lid-poweroff`.
   Para la prueba, dejar `MBP_LID_MODE=dry-run` y fijar
   `MBP_LID_SECONDS=60`. Esperar al menos 30 s tras arrancar o reanudar
   para que logind detecte las pantallas.
2. Cerrar la tapa, abrir antes del plazo y comprobar que se reanuda con
   bloqueo. Consultar `sudo journalctl -b -u mbp-lid-poweroff.service`:
   debe indicar cancelación, no una solicitud de apagar.
3. Repetir con la tapa cerrada más de 60 s. Antes de abrirla, desde otro
   equipo en la misma red, comprobar si volvió a estar accesible y revisar
   el journal. En modo de prueba debe aparecer
   `Dry run: lid stayed closed; would request a normal poweroff.`.
   El journal de `systemd-suspend.service` debe registrar la selección de
   `s2idle`; al reabrir, `cat /sys/power/mem_sleep` debe volver a mostrar el
   modo habitual entre corchetes.
   Si no se observó reanudación hasta abrir la tapa, no habilitar el apagado:
   no está confirmado el despertar con la tapa cerrada. Probar tanto con
   batería como con alimentación si se usará en ambas condiciones.
4. Solo tras confirmar ambos casos, usar `MBP_LID_SECONDS=1200` y
   `MBP_LID_MODE=poweroff`. Hacer la primera prueba de apagado con la
   sesión guardada y acceso físico. Verificar luego que no se apagó al
   suspender manualmente con la tapa abierta. El plazo se puede cambiar en
   segundos (30–86400); los cambios se leen en la próxima suspensión.

Para revisar una prueba tras encender de nuevo, usar
`sudo journalctl -b -1 -u mbp-lid-poweroff.service` si el journal persiste.
Si el firmware no despierta de suspensión, no usar esta política como
garantía de apagado. Un bloqueo de apagado o una lectura no disponible se
tratan como cancelación, no se reintenta forzando.

## Desktop mode and rollback

Con la tapa **abierta**, desarmar el perfil apartando primero
`/etc/default/mbp-lid-poweroff` a un respaldo externo de root y ejecutar
`sudo systemctl stop mbp-lid-poweroff.service`. Sin el archivo de
configuración, la unidad no se inicia en nuevas suspensiones. No se puede
cancelar un apagado que logind ya aceptó.

Para retirar por completo el perfil, respaldar y apartar únicamente estos
archivos, ejecutar `sudo systemctl daemon-reload` y recargar logind si lo
admite, como en la instalación. En caso contrario, la política previa vuelve
con el próximo reinicio local:

- `/usr/local/libexec/mbp-lid-poweroff.py`
- `/etc/systemd/system/mbp-lid-poweroff.service`
- `/etc/systemd/system/systemd-suspend.service.d/60-mbp-lid-poweroff.conf`
- `/etc/systemd/logind.conf.d/60-mbp-lid-poweroff.conf`

Para usar un monitor externo de forma permanente con la tapa cerrada,
mantener el auxiliar desarmado y guardar un drop-in local aparte en
`/etc/systemd/logind.conf.d/90-mbp-desktop-lid.conf`. Confirmar que esa ruta
no existe antes de crearla, conservarla como archivo de root y aplicar en el
próximo reinicio local:

```ini
[Login]
HandleLidSwitch=ignore
HandleLidSwitchExternalPower=ignore
HandleLidSwitchDocked=ignore
```

Comprobar pantalla y teclado externos antes de cerrar la tapa. Para volver
al modo portátil, retirar el override de escritorio, reinstalar el perfil
o restaurar sus archivos desde el respaldo y repetir la prueba en modo
`dry-run` antes de habilitar el apagado.

## References

- [logind.conf(5)](https://manpages.debian.org/trixie/systemd/logind.conf.5.en.html)
- [systemd-suspend.service(8)](https://manpages.debian.org/trixie/systemd/systemd-suspend.service.8.en.html)
- [timerfd_create(2)](https://manpages.debian.org/trixie/manpages-dev/timerfd_create.2.en.html)
- [org.freedesktop.login1](https://www.freedesktop.org/software/systemd/man/latest/org.freedesktop.login1.html)
