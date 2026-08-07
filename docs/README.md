# Organización y política de documentación

Este repositorio debe permitir reproducir la preparación del equipo desde cero,
con o sin asistencia. Ninguna descarga, instalación, configuración o práctica
operativa se considera terminada hasta quedar documentada.

## Organización

Los documentos ubicados directamente en `docs/` corresponden exclusivamente al
MacBook Pro 2015 con Debian: hardware, controladores, energía, batería, pantalla,
almacenamiento, rendimiento y automatizaciones específicas del equipo.

La carpeta [`docs/others`](others/README.md) contiene temas auxiliares que no son
optimizaciones propias del hardware o de Debian, por ejemplo:

- Git y convenciones de commits;
- GitHub CLI y autenticación;
- publicación de repositorios;
- futuras herramientas generales de desarrollo.

## Idioma y nombres de archivos

- El contenido de la documentación se escribe en español.
- Los nombres de documentos y directorios se escriben siempre en inglés.
- Se usa ASCII, sin acentos, eñes ni otros caracteres especiales.
- Para nombres compuestos se usa `lowercase-kebab-case.md`.
- Se conservan nombres convencionales como `README.md` cuando corresponde.

Ejemplos válidos:

```text
initial-state.md
daily-use.md
scripts-and-files.md
others/github-cli.md
```

## Información obligatoria para cada descarga o instalación

1. Propósito y motivo de la herramienta.
2. Fuente oficial y URL exacta.
3. Versión y fecha de instalación.
4. Arquitectura o variante descargada.
5. Dependencias previas.
6. Método de integridad: checksum, firma o mecanismo equivalente.
7. Comandos reproducibles, sin canalizar descargas directamente a una shell.
8. Ubicación final y permisos relevantes.
9. Configuración adicional realizada.
10. Verificación funcional.
11. Procedimiento de actualización y desinstalación/reversión.
12. Limpieza de archivos temporales.

## Información obligatoria para scripts

Todo `.sh` o `.py` debe figurar en
[`scripts-and-files.md`](scripts-and-files.md) con propósito, parámetros,
dependencias, privilegios, efectos, prueba y reversión.

## Seguridad documental

Nunca se guardarán en Git:

- contraseñas, tokens o cookies;
- códigos de dispositivo de un solo uso;
- claves privadas;
- archivos `.env` reales;
- salidas que revelen credenciales.

Se pueden documentar nombres de usuario, correos `noreply`, rutas, checksums y
comandos que no contengan secretos.

## Cierre de cada cambio

Antes de publicar se debe:

1. actualizar la guía correspondiente y `changelog.md`;
2. validar scripts y archivos de configuración;
3. revisar que no existan secretos ni temporales;
4. usar Conventional Commits en inglés;
5. verificar que el SHA remoto coincida con el local.
