# XAMPP and Composer setup

## Scope

Perfil opcional de desarrollo local para una instalación existente de
XAMPP en `/opt/lampp`. Su manifiesto enlaza `xampp`, `php` y `composer` en `~/.local/bin`.
No modifica el perfil Sway, el PHP del sistema, la configuración de Apache ni
`sudoers`. No habilita unidades ni inicia servicios al iniciar sesión.

XAMPP se instala manualmente fuera del repositorio. Elegir el instalador de
Linux en el [archivo oficial](https://sourceforge.net/projects/xampp/files/XAMPP%20Linux/),
comprobar su suma y seguir [XAMPP FAQs for Linux](https://www.apachefriends.org/faq_linux.html).
Este perfil no descarga ni fija ninguna versión de XAMPP. Usarlo solo para
desarrollo local y no exponer sus servicios a la red.

## PHP compatibility

Como referencia, XAMPP 8.2.12 para Linux incluye PHP 8.2.12: satisface el
mínimo de Laravel 12, pero [Laravel 13](https://laravel.com/docs/13.x/releases)
requiere PHP 8.3 o posterior. Antes de elegir una herramienta, comprobar
`php --version` y el requisito de PHP del proyecto. Debian 13 ofrece
[PHP 8.4 CLI](https://packages.debian.org/trixie/php8.4-cli) como alternativa
independiente de XAMPP y sin necesidad de iniciar Apache. Si ambos están
instalados, `/usr/bin/php8.4` evita el lanzador de XAMPP que tiene precedencia
en `~/.local/bin`. No usar el lanzador de Composer de XAMPP con el PHP de Debian.

## Requirements

Con Python 3 y el linker de [Configuration deployment](../deployment.md),
comprobar primero los paquetes Debian del perfil opcional:

```sh
xargs -a config/xampp/packages-debian.txt -- apt-get -s --no-install-recommends --no-remove install
xargs -a config/xampp/packages-debian.txt -- sudo apt-get --no-install-recommends --no-remove install
```

Instalar solo si la simulación es aceptable. XAMPP usa `net-tools` para consultas
de red; el lanzador usa `sudo` y, para el panel, `xauth` y `xhost` (este último en
`x11-xserver-utils`). Composer usa `curl` y los certificados CA de Debian.

## Composer and launchers

Desde la raíz de los dotfiles, como el usuario de la sesión y sin `sudo`,
instalar Composer 2 solo si falta `composer.phar` o si se desea actualizar.
El [procedimiento oficial de Composer](https://getcomposer.org/doc/faqs/how-to-install-composer-programmatically.md)
permite comparar el SHA-384 publicado antes de ejecutar el instalador
descargado por HTTPS. El script deja únicamente el PHAR en
`~/.local/share/composer/composer.phar`; no copia lanzadores ni guarda el artefacto
en Git. Antes de actualizar, conservar una copia externa del PHAR si se
necesita volver a la versión anterior.

```sh
sh tools/install-composer.sh
```

La instalación observada de Composer 2.11.2 coincide con el SHA-256 publicado
en [Composer downloads](https://getcomposer.org/download/):
`dd158c0afd41d15fac89e1b4e47b5d42911fe316c3687cd5edac98319b25d028`.

Con `~/.local/bin` en `PATH`, simular y aplicar únicamente el manifiesto adicional.
No reemplazar un lanzador distinto de forma automática. Si hay un conflicto,
respaldar y revisar el archivo existente antes de apartarlo manualmente.

```sh
python3 tools/link-user-config.py --manifest config/xampp/manifest.json
python3 tools/link-user-config.py --manifest config/xampp/manifest.json --apply \
  --backup-dir "$HOME/.local/state/dotfiles-i5-5257u/link-backups/xampp-$(date +%Y%m%d-%H%M%S)"
php --version
composer --version
xampp --help
```

`php` y `composer` usan el mismo intérprete de `/opt/lampp/bin/php`. No ejecutar
Composer con `sudo`. Los proyectos, dependencias, bases de datos, credenciales y
perfiles de Composer permanecen fuera de los dotfiles.

## On-demand use

Ejecutar `xampp status` para comprobar los servicios y `xampp startmysql` o
`xampp startapache` solo si se necesitan. El comando `xampp` sin argumentos
conserva la acción `start`, que inicia todos los servicios de XAMPP. Un proyecto
Laravel con SQLite y el servidor de Artisan no requiere Apache ni MariaDB.

Desde una terminal de Sway con XWayland activo, `xampp gui` abre el administrador
del proveedor. No anteponer `sudo`: el script lo invoca únicamente para el
administrador o las acciones de XAMPP. Para el panel, utiliza una autorización
X11 coincidente o concede acceso temporal solo al usuario local root; intenta
retirar únicamente el permiso añadido al cerrar o ante un fallo o señal
capturable. Si la retirada falla, seguir el aviso desde la misma sesión
gráfica. No se desactiva el control de acceso X11.

## Verification and rollback

Las pruebas simulan `sudo`, X11 y las descargas, sin arrancar servicios ni
instalar el PHAR real. Las pruebas de Composer requieren el PHP de XAMPP
instalado y se omiten si no existe. Probar el panel en la sesión gráfica por
separado; un chequeo por SSH no valida XWayland.

Para revertir los enlaces, pasar la ruta impresa del journal a
`python3 tools/link-user-config.py --rollback`. La reversión no
desinstala XAMPP, no borra el PHAR ni toca los datos de los proyectos.
