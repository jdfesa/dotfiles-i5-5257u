# RTK y optimización de tokens en Codex

Fecha de instalación y configuración: 2026-08-07.

## Propósito y alcance

RTK es un proxy de comandos que filtra y resume salidas antes de que lleguen al
contexto del modelo. Se instaló para reducir ruido en comandos habituales de
desarrollo, como `git status`, pruebas, compilaciones y búsquedas.

Esta configuración tiene dos partes independientes:

1. RTK reduce la salida de comandos que Codex ejecuta con el prefijo `rtk`.
2. Codex usa por defecto razonamiento medio, resumen conciso y baja verbosidad.

La integración de Codex se basa en instrucciones globales. No intercepta por sí
sola todos los comandos del sistema y comienza a aplicarse en sesiones nuevas de
Codex. La reducción informada por RTK es una estimación basada en el volumen de
salida; no equivale necesariamente al mismo porcentaje de ahorro facturado.

## Fuentes y artefacto instalado

- Proyecto oficial: `https://github.com/rtk-ai/rtk`
- Release: `https://github.com/rtk-ai/rtk/releases/tag/v0.45.0`
- Versión: 0.45.0.
- Plataforma: Linux x86-64 sobre Debian 13 `trixie`.
- Archivo: `rtk-x86_64-unknown-linux-musl.tar.gz`.
- Checksums: `checksums.txt` de la misma release.
- SHA-256 oficial del archivo:
  `c4c036fbf181fc55ef329786c8c17e0d427972b053b825944d968a6aafef1ba4`.
- SHA-256 del binario instalado:
  `99e0cff729d52297a23eb832f809d9773ba7c32de818dfe76b2cdd900a951535`.

Se eligió el binario estático `musl` para instalarlo bajo el usuario `jd`, sin
agregar un repositorio APT ni modificar rutas del sistema.

## Dependencias

Para reproducir la instalación sin GitHub CLI:

```bash
sudo apt install curl tar coreutils
```

Si GitHub CLI ya está instalado y autenticado, también puede descargar los
artefactos con `gh`. En esta máquina todas las dependencias ya estaban presentes;
no se instalaron ni eliminaron paquetes de Debian.

## Instalación reproducible

No se usó `curl | sh`. Los artefactos se descargaron en una carpeta temporal, el
archivo se verificó con el checksum oficial y recién entonces se instaló el
binario:

```bash
rtk_version=0.45.0
rtk_archive=rtk-x86_64-unknown-linux-musl.tar.gz
rtk_tmp_dir="$(mktemp -d /tmp/mbp2015-rtk.XXXXXX)"

gh release download "v${rtk_version}" \
  --repo rtk-ai/rtk \
  --pattern "$rtk_archive" \
  --pattern checksums.txt \
  --dir "$rtk_tmp_dir"

(
  cd "$rtk_tmp_dir"
  grep "  ${rtk_archive}$" checksums.txt | sha256sum --check --strict
)

tar -tzf "$rtk_tmp_dir/$rtk_archive"
tar -xzf "$rtk_tmp_dir/$rtk_archive" -C "$rtk_tmp_dir"
mkdir -p ~/.local/bin
install -m 0755 "$rtk_tmp_dir/rtk" ~/.local/bin/rtk
```

Alternativa de descarga sin `gh`:

```bash
curl -fsSL \
  -o "$rtk_tmp_dir/$rtk_archive" \
  "https://github.com/rtk-ai/rtk/releases/download/v${rtk_version}/${rtk_archive}"

curl -fsSL \
  -o "$rtk_tmp_dir/checksums.txt" \
  "https://github.com/rtk-ai/rtk/releases/download/v${rtk_version}/checksums.txt"
```

La ubicación final es `~/.local/bin/rtk`, propiedad de `jd`, modo `0755` y
tamaño de 10.326.432 bytes. `~/.local/bin` ya estaba incluido en el `PATH` desde
`.profile` y `.bashrc`.

## Telemetría y configuración local

La telemetría se dejó explícitamente desactivada:

```bash
rtk telemetry disable
rtk telemetry status
```

El estado verificado fue `consent: no`, `enabled: no` y sin hash de dispositivo.
RTK guarda su configuración en `~/.config/rtk/config.toml`. Se conservaron el
historial local de 90 días y la copia de la salida completa solo para comandos
fallidos. Se desactivaron colores y emoji para evitar contenido decorativo:

```toml
[tracking]
enabled = true
history_days = 90

[display]
colors = false
emoji = false
max_width = 120

[tee]
enabled = true
mode = "failures"
max_files = 20
max_file_size = 1048576

[telemetry]
enabled = false
consent_given = false
```

El directorio `~/.config/rtk` quedó en modo `0700` y el archivo en `0600`. Las
métricas permanecen en `~/.local/share/rtk/history.db`, también bajo el usuario
local; desactivar telemetría no desactiva estas métricas.

## Integración global con Codex

Primero se revisaron los cambios sin escribir archivos:

```bash
RTK_TELEMETRY_DISABLED=1 \
  rtk -v init -g --codex --ultra-compact --dry-run
```

En RTK las opciones globales, como `-v`, deben colocarse antes del subcomando.
Después del ensayo se aplicó la integración oficial:

```bash
RTK_TELEMETRY_DISABLED=1 rtk init -g --codex --ultra-compact
rtk init -g --codex --show
```

El inicializador creó dos archivos, ambos propiedad de `jd` y modo `0600`:

- `~/.codex/RTK.md`: instrucciones breves para anteponer `rtk` a los comandos;
- `~/.codex/AGENTS.md`: referencia global `@/home/jd/.codex/RTK.md`.

Codex carga `AGENTS.md` al iniciar una sesión, por lo que debe reiniciarse para
garantizar que una sesión anterior incorpore la integración. La opción
`--ultra-compact` solo afecta esa ejecución de RTK; para forzarla en un comando
manual debe escribirse antes del subcomando:

```bash
rtk --ultra-compact git status
```

No se instaló un hook de shell para Codex. Si un comando requiere la salida
íntegra, puede omitirse RTK o usarse el paso directo con seguimiento:

```bash
rtk proxy git status
```

## Configuración de consumo de Codex

Antes del cambio, `~/.codex/config.toml` usaba
`model_reasoning_effort = "high"`. Se establecieron valores predeterminados más
económicos:

```toml
model = "gpt-5.6-sol"
model_reasoning_effort = "medium"
model_reasoning_summary = "concise"
model_verbosity = "low"
```

`medium` conserva razonamiento para desarrollo general con menor consumo que
`high`; `concise` reduce el detalle del resumen de razonamiento y `low` reduce la
extensión de las respuestas. Para una tarea compleja puede aumentarse el esfuerzo
solo durante esa ejecución, sin modificar el archivo:

```bash
codex -c 'model_reasoning_effort="high"'
```

La sintaxis completa se validó sin iniciar una conversación facturable:

```bash
codex --strict-config --version
```

Referencias oficiales de OpenAI:

- `https://learn.chatgpt.com/docs/config-file/config-reference`
- `https://learn.chatgpt.com/docs/agent-configuration/agents-md`
- `https://developers.openai.com/api/docs/guides/latest-model`

La guía de modelos recomienda instrucciones breves, no repetir reglas y exponer
solo las herramientas relevantes. Por eso la integración global conserva una
única referencia y un archivo de instrucciones pequeño, en lugar de duplicar el
mismo texto en cada repositorio.

## Verificación y primera medición

Comandos de comprobación:

```bash
command -v rtk
rtk --version
rtk telemetry status
rtk init -g --codex --show
rtk git status
rtk gain
rtk gain --history
```

Resultado inicial sobre este repositorio:

- versión verificada: `rtk 0.45.0`;
- cuatro comandos registrados;
- 494 tokens estimados de entrada y 480 de salida;
- 14 tokens estimados ahorrados, un 2,8% en la muestra completa;
- `rtk git status` redujo un 52% en una ejecución;
- un `git log --stat` ya compacto casi no tuvo reducción.

La muestra es pequeña y no representa compilaciones o pruebas con salidas largas,
donde el beneficio debería ser mayor. `rtk gain` permite medirlo con el uso real.
En RTK 0.45.0, `rtk session` informa sesiones de Claude Code y no sirve como
medición específica de sesiones de Codex.

## Uso recomendado

RTK es más útil cuando la salida es extensa o repetitiva:

```bash
rtk git status
rtk git diff
rtk rg 'patron' .
rtk pytest -q
rtk npm run build
rtk gain --history
```

Debe comprobarse la salida sin filtrar cuando falte contexto, se diagnostique un
caso límite o la exactitud sea más importante que el ahorro. Ante un fallo, RTK
conserva la salida completa bajo `~/.local/share/rtk/tee/`, hasta 20 archivos de
1 MiB según la configuración actual. Estos registros deben revisarse antes de
copiarlos a documentación o Git porque pueden contener rutas o datos del proyecto.

## Actualización

1. Consultar la release estable más reciente del repositorio oficial.
2. Repetir la descarga con el archivo y `checksums.txt` de esa misma release.
3. Verificar el checksum antes de reemplazar `~/.local/bin/rtk`.
4. Ejecutar `rtk --version`, `rtk telemetry status` y
   `rtk init -g --codex --show`.
5. Revisar si el inicializador cambió sus instrucciones o archivos.
6. Actualizar versión, fecha, checksums y resultados en este documento.

## Limpieza de temporales

Después de verificar la instalación, debe validarse y eliminarse únicamente la
carpeta temporal creada para RTK:

```bash
case "$rtk_tmp_dir" in
  /tmp/mbp2015-rtk.*) rm -rf -- "$rtk_tmp_dir" ;;
  *) echo "Ruta temporal inesperada; no se elimina" >&2 ;;
esac
```

La carpeta temporal usada el 2026-08-07 se eliminó después de registrar los
checksums. Solo permanecieron el binario, la configuración, las métricas locales y
los dos archivos de integración con Codex.

## Reversión y desinstalación

Retirar primero la integración de Codex:

```bash
rtk init -g --codex --uninstall
```

Verificar que el comando quite la referencia de RTK sin borrar otras instrucciones
que puedan existir en `~/.codex/AGENTS.md`. Para volver al esfuerzo anterior de
Codex, editar `~/.codex/config.toml`:

```toml
model_reasoning_effort = "high"
```

También pueden eliminarse `model_reasoning_summary` y `model_verbosity` para
recuperar los valores predeterminados. Tras revisar las rutas exactas, retirar los
archivos locales de RTK:

```bash
rm -- ~/.local/bin/rtk
rm -- ~/.config/rtk/config.toml
rm -- ~/.local/share/rtk/history.db
```

Los directorios vacíos pueden conservarse. Los registros de fallos bajo `tee/`
deben inspeccionarse antes de decidir si se eliminan.
