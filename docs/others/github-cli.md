# Instalación y uso de GitHub CLI

Fecha de instalación: 2026-08-07.

## Propósito

GitHub CLI (`gh`) se instaló para autenticar Git por HTTPS mediante el flujo web
de dispositivo, sin copiar un token en la terminal ni guardarlo en el repositorio.

## Fuente y artefacto

- Proyecto oficial: `https://github.com/cli/cli`
- Release: `https://github.com/cli/cli/releases/tag/v2.97.0`
- Versión: 2.97.0, publicada el 2026-07-31.
- Plataforma: Linux x86-64/AMD64.
- Archivo: `gh_2.97.0_linux_amd64.tar.gz`.
- Checksums: `gh_2.97.0_checksums.txt`.
- SHA-256 verificado:
  `a2c9b8497e1f85b1ad0dfcb78b5a622e098801b8e461e459e88e1ee12f018112`.

## Dependencias

```bash
sudo apt install curl tar coreutils
```

`coreutils` proporciona `sha256sum` e `install`. En esta máquina las dependencias
ya estaban presentes; no se instalaron paquetes del sistema.

## Instalación reproducible sin privilegios root

No se usó `curl | sh`. Se descargó el archivo, se verificó y recién después se
instaló el binario bajo el usuario `jd`:

```bash
gh_version=2.97.0
gh_archive="gh_${gh_version}_linux_amd64.tar.gz"
gh_tmp_dir="$(mktemp -d /tmp/gh-install.XXXXXX)"

curl -fsSL \
  -o "$gh_tmp_dir/$gh_archive" \
  "https://github.com/cli/cli/releases/download/v${gh_version}/${gh_archive}"

curl -fsSL \
  -o "$gh_tmp_dir/checksums.txt" \
  "https://github.com/cli/cli/releases/download/v${gh_version}/gh_${gh_version}_checksums.txt"

(
  cd "$gh_tmp_dir"
  grep "  ${gh_archive}$" checksums.txt | sha256sum --check --strict
)

tar -xzf "$gh_tmp_dir/$gh_archive" -C "$gh_tmp_dir"
mkdir -p ~/.local/bin
install -m 0755 \
  "$gh_tmp_dir/gh_${gh_version}_linux_amd64/bin/gh" \
  ~/.local/bin/gh
```

La ubicación final es `~/.local/bin/gh`, propiedad de `jd`, modo `0755`. Debian
añade normalmente `~/.local/bin` al `PATH` al iniciar sesión. Para la sesión actual:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Verificación

```bash
command -v gh
gh --version
```

Resultado esperado para esta instalación:

```text
/home/jd/.local/bin/gh
gh version 2.97.0 (2026-07-31)
```

## Autenticación por dispositivo

```bash
gh auth login --hostname github.com --git-protocol https --web
```

1. Responder `Yes` cuando pregunte si debe autenticar Git.
2. Copiar el código temporal mostrado.
3. Abrir `https://github.com/login/device` en Helium.
4. Iniciar sesión como `jdfesa`, ingresar el código y autorizar GitHub CLI.
5. Esperar el mensaje `Authentication complete` en la terminal.

El código de un solo uso no se documenta. Si el comando se ejecuta por SSH y
intenta abrir un navegador de texto, puede abrirse manualmente la URL anterior en
Helium; el proceso de `gh` debe permanecer esperando la autorización.

Comprobar la cuenta sin revelar el token:

```bash
gh auth status
git config --global --get-regexp '^credential\..*\.helper$'
```

En esta máquina `gh` guardó la credencial en el keyring y añadió helpers para
`github.com` y `gist.github.com`. Nunca debe usarse `gh auth status --show-token`
en salidas que se vayan a guardar o publicar.

## Actualización

1. Consultar la release estable más reciente en el repositorio oficial.
2. Cambiar `gh_version` en el procedimiento de instalación.
3. Descargar también el nuevo archivo de checksums.
4. Verificar el archivo antes de reemplazar el binario.
5. Ejecutar `gh --version` y `gh auth status`.
6. Registrar versión, URL, checksum y fecha en este documento.

## Limpieza de temporales

Después de verificar la instalación, validar que la ruta sea la temporal creada y
eliminarla:

```bash
case "$gh_tmp_dir" in
  /tmp/gh-install.*) rm -rf -- "$gh_tmp_dir" ;;
  *) echo "Ruta temporal inesperada; no se elimina" >&2 ;;
esac
```

La descarga temporal usada el 2026-08-07 fue eliminada después de registrar el
checksum. Solo quedó el binario instalado.

## Cierre de sesión y desinstalación

Revocar primero la credencial local:

```bash
gh auth logout --hostname github.com
```

Retirar los helpers generados por GitHub CLI si ya no se utilizará:

```bash
git config --global --unset-all credential.https://github.com.helper
git config --global --unset-all credential.https://gist.github.com.helper
```

Finalmente, eliminar exclusivamente el binario instalado:

```bash
rm -- ~/.local/bin/gh
```
