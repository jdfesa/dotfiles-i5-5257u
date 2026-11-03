# Agent instructions — MacBookPro12,1

## Platform and priorities

- Plataforma objetivo: Debian 13 amd64, i5-5257U (2C/4T), Iris 6100/i915,
  BCM43602/brcmfmac y 8 GB de RAM. La estabilidad y la mantenibilidad tienen
  prioridad sobre los efectos visuales.
- Sway es la sesión principal; Zsh es el intérprete de la cuenta. Conservar
  PulseAudio, NetworkManager, UPower y las políticas de logind. No forzar el
  renderizado por software ni prometer mejoras de autonomía sin mediciones comparables.
- XFCE es únicamente un perfil opcional de recuperación: config/xfce/,
  scripts/xfce/ y docs/xfce-recovery.md. No añadirlo a la lista de paquetes
  ni al manifiesto del entorno principal.

## Repository layout

- README.md es un índice breve del hardware, el alcance y la navegación.
  La documentación temática pertenece a docs/, con títulos y nombres de archivos
  en inglés y prosa en español.
- Mantener en inglés la ayuda de línea de comandos y los textos de las interfaces.
- Los documentos de la raíz son README.md, LICENSE, CHANGELOG.md, TODO.md
  y AGENTS.md. Los README de componentes deben ser índices breves, sin duplicar
  procedimientos.
- config/<component>/ contiene las fuentes; scripts/, los auxiliares de ejecución;
  tools/, las herramientas de mantenimiento; tests/, las pruebas de regresión;
  licenses/, los avisos de terceros.
- La copia de trabajo canónica del portátil es /home/jd/dotfiles-i5-5257u,
  incluida la u final. Las configuraciones de usuario se enlazan por archivo
  según el manifiesto seleccionado. No eliminar esa copia mientras existan
  enlaces que apunten a ella.
- Mantener los paquetes descargados y el estado generado por las aplicaciones
  fuera de las fuentes gestionadas. Los archivos de sistema se instalan como
  archivos normales gestionados por paquetes o propiedad de root, no como
  enlaces simbólicos al directorio personal.
- Usar procedimientos técnicos impersonales y resultados medidos. No reproducir
  diálogos, historiales personales de configuración de cuentas ni cronologías
  temporales de implementación.
- Conservar MIT para el código y la documentación originales, y los avisos
  de licencia de proveedores y fuentes tipográficas.

## Language and naming

- Redactar en español el cuerpo de la documentación, incluidos el contenido
  actual y las nuevas aportaciones de TODO.md y AGENTS.md. Usar contenido
  íntegramente en inglés solo en los archivos indicados explícitamente.
- El README.md principal de la raíz es una excepción explícita: todo su contenido,
  incluido el cuerpo, se redacta en inglés.
- Mantener en inglés los títulos y subtítulos, así como los nombres de archivos,
  scripts y directorios.
- Usar etiquetas de navegación y textos de enlaces a documentos en inglés,
  según el título o el nombre real del destino. Si la etiqueta es un nombre
  de archivo, respetar su escritura exacta, incluidas las mayúsculas y la extensión.
  Los destinos deben coincidir con las rutas reales, también en sistemas que
  distinguen mayúsculas de minúsculas.
- Usar kebab-case (minúsculas y guion medio -) para los nombres propios de
  archivos, scripts y directorios que contengan varias palabras; por ejemplo,
  restore-guide.md, open-networks.sh y window-tools/. No usar espacios,
  guiones bajos ni camelCase en esos nombres.
- Respetar los nombres convencionales README.md, AGENTS.md, TODO.md,
  CHANGELOG.md y LICENSE, y los nombres exigidos por aplicaciones o herramientas.
  Los documentos convencionales de la raíz conservan las mayúsculas indicadas;
  no convertir esos nombres a kebab-case.
- Conservar sin traducir comandos, rutas, identificadores, nombres propios
  y valores técnicos requeridos por el software. Esta convención no implica
  renombrados masivos de archivos existentes.

## Working machine and synchronization

- La única copia de trabajo principal es `/home/jd/dotfiles-i5-5257u` en el
  portátil remoto. Conectarse por SSH para editar las fuentes, ejecutar las
  pruebas y validar los cambios en la máquina donde tendrán efecto.
- Crear, aplicar y comprobar los enlaces simbólicos como `jd` en ese mismo
  portátil, utilizando los manifiestos del checkout canónico. Los destinos
  del home apuntan a sus fuentes, nunca a la máquina de control ni a respaldos.
- Conservar las configuraciones vigentes del portátil como base del trabajo.
  No sustituir ajustes existentes por copias locales antiguas para limpiar
  el estado de Git o hacer pasar una prueba.
- GitHub es la fuente pública versionada. Antes de empezar, revisar el estado
  del checkout remoto y ejecutar `git pull --ff-only` cuando sea seguro.
  Si hay cambios pendientes que impidan el pull, compararlos y reconciliarlos
  sin descartarlos ni ocultarlos automáticamente.
- El repositorio de GitHub conserva el respaldo versionado de las fuentes
  públicas para recuperarlas si se pierde la copia del portátil. Solo quedan
  respaldados allí los cambios incluidos en commits y publicados mediante
  push; los archivos privados ignorados requieren un respaldo privado separado.
- Crear las ramas y realizar los commits, push y pull requests desde el
  repositorio del portátil, cuando estén autorizados. La copia de esta máquina
  de control es secundaria: consultarla y actualizarla mediante pull después
  de publicar solo cuando sea necesario; en caso contrario, omitir ese pull.
  No usarla como origen de cambios o despliegues.
- No crear clones, worktrees ni directorios paralelos con configuraciones
  antiguas como alternativa al checkout principal. Los respaldos necesarios
  permanecen fuera de las fuentes y no se utilizan como copias de trabajo;
  retirar los árboles temporales cuando termine su verificación.
- Transferir directamente por SSH solo los archivos privados necesarios y
  revisados; nunca publicarlos en Git. Estar ignorado por `.gitignore` no
  convierte cachés, descargas o estado de aplicaciones en archivos desplegables.

## Workflow

1. Inspeccionar por SSH las fuentes y los destinos reales del portátil;
   preservar las modificaciones y actualizar primero las fuentes de su checkout
   canónico. Mantener los pendientes en TODO.md en la raíz. Trabajar una
   prioridad por vez.
2. Declarar las dependencias directas de Debian en config/packages/debian.txt;
   las dependencias opcionales de recuperación van por separado. Preferir
   paquetes y artefactos oficiales estables. Revisar las sumas de verificación,
   las simulaciones de paquetes y los comandos antes de instalar.
3. Ejecutar las pruebas, las comprobaciones previas a publicación, los validadores
   de sintaxis y la simulación de enlaces. Aplicar los enlaces de usuario como jd,
   con un nuevo directorio externo de respaldo y un registro de reversión.
4. Validar el comportamiento de la sesión real por separado de las pruebas de
   sintaxis y de directorio personal temporal. No afirmar que se probó una
   restauración sobre un sistema limpio si no se realizó.
5. Actualizar las guías de dependencias y temas, y CHANGELOG. No realizar commit,
   push, reescrituras del historial ni cambios de visibilidad remota sin
   autorización explícita. Antes de publicar, revisar nuevamente .gitignore,
   el índice exacto y el historial que se enviará.

## Runtime contracts

- Omarchy es la referencia de atajos, no una distribución para importar.
  Super+Enter abre Kitty; Super+Space/D, Fuzzel; Super+N, redes;
  Super+Shift+B, el navegador XDG predeterminado. No fijar Helium en ese atajo.
  Zed permanece accesible solo desde el lanzador hasta acordar un atajo para
  el editor; Super+Shift+Enter queda sin asignar.
- Mantener sincronizados config/sway/keybindings-help.txt y docs/keybindings.md.
- Conservar la barra superior opaca Mocha y JetBrainsMono Nerd Font Mono Regular 10.
  Kitty permanece opaco, sin desenfoque, animación del cursor ni control remoto;
  Foot es la alternativa de respaldo.
- Aplicar JetBrainsMono Nerd Font Propo Regular 12 solo a iconos de clima,
  métricas y audio para conservar su proporción; no cambiar el texto Mono 10, la terminal,
  la batería Mono 12 ni el Wi-Fi BGH 12 al ajustar esos pictogramas.
- Starship usa comandos personalizados POSIX con ejecución acotada y una
  alternativa nativa de Zsh. No importar complementos de shell ajenos; las nuevas
  fuentes tipográficas necesitan sus archivos, licencia y sumas de verificación.
- Los accesos a redes comparten mbp-open-networks. Preservar el protocolo explícito
  de resultado del cliente: Kitty no propaga el estado de salida del proceso hijo.
  HUP/TERM son cancelaciones normales; los fallos ordinarios del cliente deben
  seguir tratándose como errores.
- Las acciones de energía conservan la confirmación, la autorización de sesión
  activa, los inhibidores normales y el bloqueo previo a suspender. No forzar
  acciones ignorando un inhibidor ni añadir reglas amplias de privilegios.
  Coordinar los cambios de energía, sesión y conexión.
- Mantener el ciclo compartido de 10 s de la barra, el nivel de carga de UPower,
  la lista fija de acciones permitidas por clic y las tareas puntuales acotadas
  de clima/APT. No actualizar ni instalar paquetes automáticamente desde los widgets.
- La batería debe permanecer visible con la barra contraída: icono según el
  estado real de carga, descarga o carga completa, y porcentaje de UPower.
  No sustituir el nivel de carga por la salud, la capacidad de diseño o los ciclos.
- La contracción afecta solo a la vista: el chevrón redibuja la muestra en memoria
  sin ejecutar procesos ni volver a consultar sensores, contadores o UPower.
  Mantener el tick compartido y los controles esenciales; no prometer ahorro de
  batería por ocultar métricas.

## Tooling

- Los comandos de administración comienzan con rtk; usar rtk proxy para obtener
  la salida completa.
- Aplicar la persistencia de Engram sin incluir registros de sesión en las guías
  del proyecto.
- Ejecutar python3 tools/check-repository.py --history antes de revisar una publicación.
