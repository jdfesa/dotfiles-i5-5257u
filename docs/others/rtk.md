# RTK command proxy

RTK filtra salidas extensas de comandos de desarrollo. Es opcional y no forma
parte de las dependencias de sesión. [Project and releases](https://github.com/rtk-ai/rtk).

## Installation reference

Artefacto de referencia: v0.45.0, Linux x86_64 musl,
`rtk-x86_64-unknown-linux-musl.tar.gz`.
SHA256: `c4c036fbf181fc55ef329786c8c17e0d427972b053b825944d968a6aafef1ba4`.

Descargar el archivo y `checksums.txt` de la misma release, verificar el digest,
inspeccionar el tarball y copiar el binario a `~/.local/bin/rtk`, modo 0755.
Para versiones nuevas, revisar requisitos y hashes de esa release antes de
sustituir el binario. No ejecutar un instalador remoto mediante una tubería.

## Usage

```sh
rtk --version
rtk git status
rtk git diff
rtk gain
rtk proxy git status
```

`proxy` conserva la salida original cuando el filtrado dificulta un diagnóstico.
Las métricas de reducción son estimaciones de volumen, no un benchmark del
hardware ni garantía de ahorro de recursos. Para retirar, identificar el binario
instalado y revisar cualquier integración opcional antes de eliminarlo.
