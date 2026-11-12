# Yazi and Zathura setup

## Daily use

- Ejecutar `yazi` en Kitty. Al seleccionar un PDF, la vista previa se renderiza
  en el panel derecho con Poppler, sin abrir el lector. El panel ocupa la mitad
  del ancho; la miniatura conserva la proporción de la página y se limita a
  1040 × 1480 píxeles para la pantalla integrada a escala 2.
- Pulsar Enter sobre el PDF para abrirlo en Zathura. Las páginas se muestran
  con fondo oscuro y texto claro; Ctrl+R alterna los colores originales. Si
  el Kitty enfocado está en pantalla completa en Sway, se sale de ese modo
  para no ocultar Zathura. Super+F vuelve a activar la pantalla completa.
- Para enviar Zathura a otro escritorio, enfocar su ventana y pulsar
  Super+Shift+número. Super+número cambia a ese escritorio; 0 corresponde
  al escritorio 10. Véase [Keyboard shortcuts](keybindings.md).
- La regla solo se aplica dentro de Yazi; no cambia el lector PDF predeterminado
  del escritorio. La vista previa conserva los colores originales. Si una
  miniatura sigue pequeña tras cambiar el tamaño, salir de Yazi, ejecutar
  `ya cache clear` y volver a abrirlo.

## Installation

En Debian 13 amd64, Yazi `26.9.1-1` se instala desde el paquete oficial del
proveedor, no desde un repositorio APT adicional. Los paquetes Debian son
`file`, `poppler-utils`, `zathura` y `zathura-pdf-poppler`. No hacen falta
las dependencias recomendadas para otros formatos. Ambos programas se ejecutan
bajo demanda. En el equipo de referencia, APT calculó 1,3 MB adicionales para
Zathura y su plugin, reutilizando Poppler y GTK ya instalados; el tamaño en
disco no mide la autonomía.

En un directorio temporal fuera del checkout:

```sh
asset=yazi-x86_64-unknown-linux-gnu.deb
rtk proxy curl --fail --location --output "$asset" \
  "https://github.com/sxyazi/yazi/releases/download/v26.9.1/$asset"
printf '%s  %s\n' 331d6247c0a0fd549f14cd599a928a529b8b22eded1bb1f61a518376c7621b45 "$asset" | rtk proxy sha256sum -c - &&
  rtk proxy apt-get -s --no-install-recommends --no-remove install "./$asset" file poppler-utils zathura zathura-pdf-poppler
```

Tras comprobar el hash publicado y revisar la simulación:

```sh
rtk proxy sudo apt-get --no-install-recommends --no-remove install "./$asset" file poppler-utils zathura zathura-pdf-poppler
```

El paquete instala los binarios como archivos administrados por dpkg. Se
actualiza manualmente con otro paquete oficial y su nueva suma verificada.
Consultar [Yazi release](https://github.com/sxyazi/yazi/releases/tag/v26.9.1)
y [Yazi installation](https://yazi-rs.github.io/docs/installation/).

## Verification and recovery

Aplicar el manifiesto principal como usuario tras simular los enlaces, con
respaldo externo y registro, según [Configuration deployment](deployment.md).
Comprobar `yazi --version`, `zathura --version` (debe listar el plugin PDF)
y `pdftoppm -v`. En la sesión Sway, abrir Yazi en Kitty, seleccionar un PDF
de prueba, comprobar su vista previa y abrirlo con Enter. Pulsar Ctrl+R dos
veces para verificar ambos esquemas sin cambiar el archivo.

Para revertir los enlaces, usar su registro de despliegue. Para retirar los
programas, revisar primero `apt-get -s remove yazi zathura zathura-pdf-poppler`.
No retirar Poppler ni `file` si los usan otras aplicaciones.
