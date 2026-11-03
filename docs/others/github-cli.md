# GitHub CLI

Herramienta opcional para issues, releases y pull requests. No es necesaria
para clonar por HTTPS este repositorio ni para ejecutar el perfil Sway.

## Debian installation

Fuente: [Debian gh package](https://packages.debian.org/trixie/gh).

```sh
apt-get -s --no-install-recommends --no-remove install gh
sudo apt-get --no-install-recommends --no-remove install gh
gh --version
gh help
```

APT administra el binario y sus actualizaciones. Para retirar, simular
`apt-get -s remove gh` y revisar la operación antes de aplicarla.
Las opciones de cuentas y autenticación están en la
[GitHub CLI manual](https://cli.github.com/manual/).
