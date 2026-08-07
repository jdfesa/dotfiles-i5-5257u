# Registro de cambios

## 2026-08-07

- Se relevó el hardware del `MacBookPro12,1` y el estado de Debian 13/XFCE.
- Se creó `~/github/mbp2015` con las carpetas `docs` y `scripts`.
- Se añadió `power-manager-plugin` como elemento 19 del panel superior de XFCE.
- Se recargó el panel de la sesión XRDP para aplicar su configuración.
- Se añadió la entrada de autoinicio
  `~/.config/autostart/mbp2015-brightness.desktop`.
- Se creó y documentó `scripts/set-local-brightness.sh` para aplicar 40% de brillo
  únicamente en la sesión gráfica local.
- No se instalaron ni eliminaron paquetes.
- No se modificaron archivos bajo `/etc`, `/usr` ni `/sys`.
- Git no fue inicializado.
- Se configuró Git globalmente con `José Sandoval` y el correo privado de GitHub
  `92765822+jdfesa@users.noreply.github.com`.
- Se establecieron valores globales básicos para `main`, finales de línea, limpieza
  de referencias y comportamiento seguro de `pull`/`push`.
- Durante la configuración inicial de identidad no se autenticó GitHub ni se
  clonaron dotfiles.
- Se añadió una copia reproducible de la entrada de autoinicio de XFCE bajo
  `config/autostart`.
- Se preparó `mbp2015` para Git con rama `main`, remoto GitHub, `.gitignore`,
  `.gitattributes` y commits siguiendo Conventional Commits en inglés.
- Se instaló GitHub CLI 2.97.0 bajo `~/.local/bin`, verificando el checksum oficial.
- Se autorizó la cuenta `jdfesa` mediante el flujo web de dispositivo y se configuró
  HTTPS como protocolo de GitHub.
