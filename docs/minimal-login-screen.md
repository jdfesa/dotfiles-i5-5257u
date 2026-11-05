# Minimal login screen

## Scope

Perfil visual opcional para LightDM GTK Greeter en Debian 13. El inicio
de sesión y el bloqueo son distintos: LightDM presenta el acceso de arranque;
`swaylock` sigue bloqueando la sesión Wayland. No se cambia PAM, autologin,
la lista de usuarios ni la sesión seleccionada por AccountsService.

El perfil utiliza un fondo Mocha estático, un formulario centrado sin avatar
y DejaVu Sans a 192 DPI para eDP-1 de 2560×1600. Mantiene reloj, distribución
de teclado, selección de sesión, accesibilidad y energía. La hoja GTK hereda
Adwaita oscuro y se selecciona solo en el greeter; no afecta a las aplicaciones
de la sesión. No requiere paquetes adicionales.

## Install

Los archivos de sistema son copias normales propiedad de root. No se enlazan
desde el manifiesto de usuario. Si alguno de los destinos ya existe, revisar
su contenido y respaldarlo fuera del checkout antes de sustituirlo.

```sh
cd ~/dotfiles-i5-5257u
greeter_dir=/etc/lightdm/lightdm-gtk-greeter.conf.d
theme_dir=/usr/local/share/themes/mbp-minimal/gtk-3.0

(
    set -eu
    test ! -L "$greeter_dir" && test ! -L "$theme_dir" || exit 1
    for path in "$greeter_dir/90-mbp-minimal.conf" "$theme_dir/gtk.css"; do
        if [ -e "$path" ] || [ -L "$path" ]; then
            printf 'Existing destination: %s\n' "$path" >&2
            exit 1
        fi
    done
    [ -d "$greeter_dir" ] || sudo install -d -o root -g root -m 0755 "$greeter_dir"
    [ -d "$theme_dir" ] || sudo install -d -o root -g root -m 0755 "$theme_dir"
    sudo install -o root -g root -m 0644 \
        config/lightdm/mbp-minimal/gtk-3.0/gtk.css "$theme_dir/gtk.css"
    sudo install -o root -g root -m 0644 \
        config/lightdm/90-mbp-minimal.conf "$greeter_dir/90-mbp-minimal.conf"
)
```

El greeter lee los fragmentos por nombre y finalmente
`/etc/lightdm/lightdm-gtk-greeter.conf`. Revisar si ese archivo ya declara
claves activas de apariencia; no sobrescribir valores ajenos automáticamente.

## Local greeting

`~~` identifica texto literal en la lista de indicadores. Desde la raíz del
checkout, crear el fragmento local la primera vez. Sustituir solo `Name` por el
nombre que se quiera mostrar. Si el archivo ya existe, editarlo en lugar de
volver a crearlo.

```sh
(
    set -euC
    umask 077
    install -d -m 0700 private/lightdm
    cat > private/lightdm/99-greeting.conf <<'EOF'
[greeter]
indicators=~spacer;~~welcome, Name!;~spacer;~clock;~layout;~session;~a11y;~power
EOF
)
```

Si el destino no existe, instalar una copia legible por el greeter:

```sh
(
    set -eu
    destination="$greeter_dir/99-greeting.conf"
    if [ -e "$destination" ] || [ -L "$destination" ]; then
        printf 'Existing destination: %s\n' "$destination" >&2
        exit 1
    fi
    sudo install -o root -g root -m 0644 private/lightdm/99-greeting.conf "$destination"
)
```

El saludo no cambia el nombre de cuenta ni las credenciales. Mantener su
fuente privada fuera de Git y respaldarla aparte si se necesita restaurarla.

## Verification and rollback

Antes de cerrar la sesión, comprobar que las copias del sistema coincidan
con las fuentes. Tener los archivos en el repositorio o generar una captura
aislada no cambia el login del equipo.

```sh
cmp config/lightdm/90-mbp-minimal.conf "$greeter_dir/90-mbp-minimal.conf"
cmp config/lightdm/mbp-minimal/gtk-3.0/gtk.css "$theme_dir/gtk.css"
# Only if a local greeting was installed:
cmp private/lightdm/99-greeting.conf "$greeter_dir/99-greeting.conf"
```

Para validar el equipo, guardar el trabajo y cerrar sesión normalmente.
No reiniciar LightDM desde la sesión activa. Comprobar el saludo, la
legibilidad de los campos, los controles de teclado y accesibilidad, y que
la sesión elegida siga siendo Sway. Con pantallas externas, comprobar también
la escala y la posición del formulario.

En MacBookPro12,1 con Debian 13, LightDM 1.32.0 y GTK Greeter 2.0.9 se
comprobó que al cerrar sesión aparece el perfil con el saludo local y
que se puede volver a una sesión Sway en Wayland. No se realizó una
restauración desde una instalación limpia.

Para volver a la apariencia anterior, retirar solo los archivos instalados
por este perfil. Si se reemplazó algún archivo existente, restaurar su respaldo
en lugar de eliminarlo:

```sh
sudo rm -f -- /etc/lightdm/lightdm-gtk-greeter.conf.d/99-greeting.conf \
    /etc/lightdm/lightdm-gtk-greeter.conf.d/90-mbp-minimal.conf \
    /usr/local/share/themes/mbp-minimal/gtk-3.0/gtk.css
```

El cambio se verá cuando LightDM vuelva a presentar su pantalla de acceso.
[LightDM GTK Greeter configuration](https://github.com/Xubuntu/lightdm-gtk-greeter/blob/lightdm-gtk-greeter-2.0.9/data/lightdm-gtk-greeter.conf).
