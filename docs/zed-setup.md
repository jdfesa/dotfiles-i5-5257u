# Zed setup

## Hardware gate and installed release

Instalación verificada el **2026-11-02**, versión estable oficial **1.26.2**,
Linux **x86_64**, commit `c4273271092b0287f7d181f616bd5171e0a2f70c`.
[Release](https://github.com/zed-industries/zed/releases/tag/v1.26.2),
[Manual Linux installation](https://zed.dev/docs/linux#downloading-manually),
[Linux requirements](https://zed.dev/docs/installation#linux).

Zed requiere Vulkan 1.3. La comprobación utiliza `vulkan-tools`
1.4.304.0+dfsg1-1 de APT Debian; no requiere sustituir los controladores de Mesa:

```sh
apt-get -s --no-install-recommends --no-remove install vulkan-tools
sudo apt-get --no-install-recommends --no-remove install vulkan-tools
vulkaninfo --summary
```

La **GPU física integrada Iris 6100 (BDW GT3)** informa API **1.3.305**,
conformidad 1.3.0.0, Mesa 25.0.7-2+deb13u1. No confundirla con la versión del
loader 1.4.309 ni con el dispositivo CPU llvmpipe, también enumerado.
glibc 2.41 supera el mínimo x86_64 2.31; CPU AVX2 presente. No se aplicó una
variable de software rendering ni se sustituyó Mesa para ocultar incompatibilidad.

Los portales FileChooser/OpenURI y Secret Service forman parte de la integración
de sesión. Compartir pantalla es otra función y conserva su pendiente propio;
abrir el editor no lo verifica.

## Artifact and reproducible installation

Se utilizó el mismo tarball precompilado que distribuye el instalador oficial,
pero sin ejecutar un instalador descargado ni canalizar curl a una shell.

- URL: `https://github.com/zed-industries/zed/releases/download/v1.26.2/zed-linux-x86_64.tar.gz`
- Tamaño observado: 90.563.772 bytes.
- SHA256 publicado por la API oficial de assets GitHub y comprobado localmente:
  `4d7b972019f25bd0a8cc6f4c56c81ab7ad9205f3461d00ac79259b34a03856d2`.
- HTTPS y digest del mismo proveedor verifican integridad; no son una firma
  independiente del proveedor. No se presenta el hash como tal.

Procedimiento de instalación inicial como jd; se detiene si ya existe una app
o un enlace CLI, en lugar de destruirlos:

```sh
python3 - <<'PY'
import hashlib, os, pathlib, shutil, tarfile, tempfile, urllib.request
home = pathlib.Path.home()
local = home / '.local'
local.mkdir(exist_ok=True)
for target in (local / 'zed.app', local / 'bin/zed'):
    assert not target.exists() and not target.is_symlink(), target
url = 'https://github.com/zed-industries/zed/releases/download/v1.26.2/zed-linux-x86_64.tar.gz'
expected = '4d7b972019f25bd0a8cc6f4c56c81ab7ad9205f3461d00ac79259b34a03856d2'
with tempfile.TemporaryDirectory(prefix='.zed-stage-', dir=local) as directory:
    stage = pathlib.Path(directory)
    archive = stage / 'zed.tar.gz'
    with urllib.request.urlopen(url, timeout=90) as source, archive.open('wb') as dest:
        shutil.copyfileobj(source, dest)
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == expected
    with tarfile.open(archive, 'r:gz') as bundle:
        for member in bundle.getmembers():
            path = pathlib.PurePosixPath(member.name)
            assert not path.is_absolute() and '..' not in path.parts
            assert path.parts[0] == 'zed.app'
        bundle.extractall(stage, filter='data')
    assert (stage / 'zed.app/libexec/zed-editor').is_file()
    os.rename(stage / 'zed.app', local / 'zed.app')
(local / 'bin').mkdir(exist_ok=True)
(local / 'bin/zed').symlink_to(local / 'zed.app/bin/zed')
PY
```

El staging y el archivo descargado se eliminan al terminar. Un recibo de versión/URL/hash puede conservarse, modo 0600, bajo
`~/.local/state/dotfiles-i5-5257u/installations/zed-1.26.2.json`.
La aplicación se instala separadamente de las fuentes de configuración.

## Centralized configuration

| Fuente / material | Destino y gestión |
|---|---|
| App oficial, archivos de licencia incluidos | `~/.local/zed.app/`, propietario jd, fuera del checkout |
| CLI de la app | `~/.local/bin/zed` → `~/.local/zed.app/bin/zed`; enlace de instalación, no fuente de configuración |
| `config/zed/settings.json` | `~/.config/zed/settings.json`, enlace por manifiesto, 0644 |
| `config/zed/dev.zed.Zed.desktop` | `~/.local/share/applications/dev.zed.Zed.desktop`, enlace por manifiesto, 0644 |
| Icono | Archivo del bundle oficial, no una copia adicional en el repo |
| Estado de ejecución | Directorio de datos de Zed, independiente de settings.json |

Aplicar enlaces con dry-run y backup según [Deployment](deployment.md).
Cada journal conserva todos los enlaces modificados por su invocación; revisar
sus entries antes de revertir.
La configuración usa la Nerd Font existente, terminal Zsh de login, modo Vim
activado y mapa base Zed. El tema seleccionado es Ayu Dark con modo oscuro;
One Light queda como variante clara y los iconos usan Zed (Default).
La fuente pública mantiene el modo 0644 declarado en el manifiesto. Solo se
versionan preferencias: credenciales, material de cuenta y estado de sesión
permanecen fuera de las fuentes públicas.
La base deja desactivadas telemetría, AI, autoactualización y
auto-instalación de la extensión HTML predeterminada; no se añadieron plugins.
AI/extensiones/lenguajes pueden habilitarse después de revisar la necesidad.
Los LSP y runtimes del instituto aún requieren selección y pruebas propias.

**Zed permanece en Fuzzel, sin atajo asignado.** El enlace de escritorio registra un editor; no asocia inode/directory.
Super+Shift+B es exclusivamente el navegador XDG; Super+Shift+Enter no se
reutiliza automáticamente para el editor.

## Verification

```sh
~/.local/bin/zed --version
ldd ~/.local/zed.app/libexec/zed-editor | grep 'not found'  # Debe estar vacío
desktop-file-validate ~/.local/share/applications/dev.zed.Zed.desktop
python3 -m unittest discover -s tests -v
```

Compatibilidad de referencia: archivo TXT con `--foreground --user-data-dir
DIR_TEMPORAL`, protocolo `xdg_shell` sin XWayland, Iris 6100 e
`is_software_emulated: false`, sin errores de configuración ni bibliotecas faltantes.
Para repetir la prueba, usar un directorio temporal independiente, cerrar esa
instancia y retirar sus datos al terminar. Comprobar también la apertura desde
Fuzzel. Esto no sustituye una carga real de proyecto, una medición de batería
ni la verificación de cada lenguaje/LSP.

## Updates and recovery

Actualización manual, no APT ni updater de fondo: elegir la nueva release
estable, revisar requisitos y digest oficial, cerrar Zed guardando el trabajo,
respaldar/mover la app anterior fuera del checkout y repetir la instalación
con URL/hash revisados. No ejecutar el procedimiento inicial sobre un destino
existente ni eliminar datos de usuario para actualizar el programa.
Conservar `settings.json`/desktop enlazados, verificar CLI/librerías/renderizado
y actualizar el inventario. Si falla, recuperar la app y el enlace CLI anteriores.

Para retirar solo Zed, revisar sus dos entradas en el manifiesto y verificar la
identidad de los enlaces antes de quitarlos. Un rollback por journal afecta a
todas sus entries; no está limitado automáticamente al editor. Después retirar
únicamente la app y el enlace CLI identificados, conservando ajustes/estado si
se requiere recuperación. Reconciliar el manifiesto antes del próximo despliegue
para que no recree enlaces retirados. No usar autoremove para esta app manual.
