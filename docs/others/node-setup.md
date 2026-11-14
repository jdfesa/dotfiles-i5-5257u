# Node.js setup

Instalación opcional por usuario para Linux amd64; no reemplaza el Node de APT
ni inicia procesos de fondo. En el portátil se observó Node 22.20.0 con npm
10.9.3: no se fija esa versión para nuevas instalaciones.

## Install and verify

1. Elegir una versión LTS compatible con el proyecto en
   [Node.js downloads](https://nodejs.org/en/download).
2. Simular e instalar los requisitos si faltan:

```sh
python3 tools/restore-profile.py node packages
# Instalar requisitos solo si faltan y el plan es aceptable:
python3 tools/restore-profile.py node packages --apply
```

3. Verificar el manifiesto firmado según
   [Verifying binaries](https://github.com/nodejs/node#verifying-binaries).
   Definir `VERSION` con prefijo `v` y `SHA256` con el digest del archivo
   `linux-x64.tar.xz` (no el del código fuente). Ejecutar el plan y aplicar:

```sh
python3 tools/install-node.py "$VERSION" "$SHA256"
python3 tools/install-node.py "$VERSION" "$SHA256" --apply
node --version
npm --version
```

El instalador comprueba el SHA-256 antes de extraer. Instala en
~/.local/share/nodejs y enlaza node, npm y npx en ~/.local/bin; no sobrescribe
versiones ni enlaces, incluso si están rotos. Para actualizar, respaldar y
apartar los enlaces existentes tras verificar sus destinos. Puede revertirse
retirando los tres enlaces de la nueva versión y restaurando los anteriores.
Conservar los binarios y datos de npm fuera de Git.
