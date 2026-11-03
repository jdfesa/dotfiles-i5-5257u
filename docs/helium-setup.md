# Helium setup

## Package and compatibility reference

Helium se distribuye como `helium-bin`, amd64. Versión de referencia verificada
el 2026-11-02: 0.15.2.1-1, Chromium 151.0.7922.75.
El repositorio del proveedor es `https://pkg.helium.computer/deb`, stable/main,
publicado en su [Official download guide](https://helium.surf/download).

Las instalaciones y actualizaciones utilizan metadata firmada de APT. La versión
de referencia no es un pin: revisar periódicamente el candidato disponible y
coordinar el reinicio del navegador al actualizar.

## New Debian installation

Configurar el repositorio publicado por el proveedor. La lista Debian principal
incluye curl, ca-certificates y gnupg. Este bloque es para una instalación nueva;
si ya existen archivos de repositorio o clave, revisarlos antes de reemplazarlos.

```sh
(
    set -eu
    test ! -e /usr/share/keyrings/helium.gpg
    test ! -e /etc/apt/sources.list.d/helium.list
    stage=$(mktemp -d /tmp/helium-repo.XXXXXX)
    trap 'rm -rf -- "$stage"' EXIT
    curl --fail --location --proto '=https' -o "$stage/key.asc" \
      https://raw.githubusercontent.com/imputnet/helium-linux/main/pubkey.asc
    gpg --show-keys --with-fingerprint "$stage/key.asc"
    gpg --batch --dearmor --output "$stage/helium.gpg" "$stage/key.asc"
    sudo install -m 644 "$stage/helium.gpg" /usr/share/keyrings/helium.gpg
    printf '%s\n' 'deb [signed-by=/usr/share/keyrings/helium.gpg] https://pkg.helium.computer/deb stable main' \
      | sudo tee /etc/apt/sources.list.d/helium.list >/dev/null
    sudo apt-get update
    apt-get -s --no-install-recommends --no-remove install helium-bin
    sudo apt-get --no-install-recommends --no-remove install helium-bin
)
```

Revisar el origen de la clave y el plan APT. El paquete mantiene su entrada
Helium en el catálogo de aplicaciones; aplicar después el manifiesto de enlaces.

## Managed configuration and launchers

| Material | Ubicación / gestión |
|---|---|
| Paquete y bibliotecas | APT; `/usr/bin/helium` → `/opt/helium/helium-wrapper` |
| Entrada de aplicaciones | `/usr/share/applications/helium.desktop`, administrada por APT |
| Asociaciones públicas | `config/helium/mimeapps.list` → `~/.config/mimeapps.list`, enlace 0644 de jd |

La entrada de Helium sigue disponible en **Fuzzel**. No hace falta duplicar el
archivo de escritorio del paquete: así conserva sus actualizaciones normales.
Las asociaciones enlazadas fijan solo HTTP, HTTPS, HTML y XHTML; no PDF, imágenes
ni el editor de texto. Un destino existente diferente debe reconciliarse antes
de aplicar el manifiesto; no sustituir asociaciones ajenas al perfil.

**Super+Shift+B abre el navegador predeterminado XDG**. El helper consulta
`xdg-settings get default-web-browser` y usa `gtk-launch` con el ID de escritorio
como un único argumento, sin evaluación de shell ni binario fijado. Actualmente el resultado
es Helium; si cambia la asociación, el mismo atajo respeta el nuevo navegador.
Super+Shift+Enter no está asignado. Zed no tiene un atajo de editor.

Helium seleccionó Wayland nativo automáticamente en la prueba; no se fijan
opciones de backend en el atajo. El wrapper instalado tampoco lee un archivo
`helium-flags.conf`, por lo que no se crea una configuración sin efecto.
No se usan flags `--no-sandbox`, renderizado por software ni bypass de seguridad.

## Verification

```sh
helium --version
xdg-settings get default-web-browser            # helium.desktop
xdg-mime query default x-scheme-handler/http    # helium.desktop
xdg-mime query default x-scheme-handler/https   # helium.desktop
xdg-mime query default text/html                # helium.desktop
xdg-mime query default application/xhtml+xml   # helium.desktop
```

Compatibilidad de referencia: ventana `about:blank` con perfil temporal,
protocolo `xdg_shell`, sin XWayland ni necesidad de `--ozone-platform`.
Revalidar asociaciones y apertura desde Fuzzel después de restaurar o actualizar.
Los tests comprueban que el helper siga otro navegador XDG y rechace la ausencia
de predeterminado sin interpretar texto como shell.

## Updates and recovery

Para una instalación nueva, seguir el repositorio firmado del proveedor y
revisar sus claves/dependencias antes de usar APT. Con el paquete ya instalado:

```sh
apt-cache policy helium-bin
apt-get -s --only-upgrade --no-install-recommends --no-remove install helium-bin
# Después de revisar cambios y coordinar guardar/cerrar el navegador:
sudo apt-get --only-upgrade --no-install-recommends --no-remove install helium-bin
```

No fijar indefinidamente una versión antigua. Registrar la nueva versión y
repetir apertura/asociaciones después de actualizar. No hay updater adicional.

Para cambiar de navegador, editar la fuente de las cuatro asociaciones,
sincronizar y verificar XDG. El rollback se realiza mediante el journal generado
al aplicar el manifiesto: revisar su lista de entries, porque una misma invocación
puede incluir componentes distintos. Antes de retirar Helium, elegir otro
navegador instalado; revertir preferencias no requiere borrar el perfil.

Referencia de las asociaciones:
[MIME Applications](https://specifications.freedesktop.org/mime-apps/latest/default.html).
