# Fonts

## Managed assets

`config/fonts/` contiene JetBrainsMono Nerd Font Mono Regular/Bold y Propo
Regular, base JetBrains Mono 2.304 / Nerd Fonts v3.5.1, y la fuente de iconos de estado.
Los TTF se enlazan individualmente a `~/.local/share/fonts/` por manifiesto.

- [Nerd Fonts v3.5.1 source](https://github.com/ryanoasis/nerd-fonts/tree/v3.5.1/patched-fonts/JetBrainsMono/Ligatures).
- [JetBrains Mono OFL](../config/fonts/OFL.txt).
- [Icon set notices](../config/fonts/UPSTREAM.md).
- `status-icons.ttf`: fuente MIT; su familia interna BGH Status Icons se
  conserva por compatibilidad con el formato de barra.

| Archivo | SHA256 |
|---|---|
| JetBrainsMonoNerdFontMono-Regular.ttf | `f2a5ea6cfab397445ffab00c0370927b66d61e560a05db5db271b42006381c1a` |
| JetBrainsMonoNerdFontMono-Bold.ttf | `bfcf9a917276ffc058867d87cbc8a5b2f1ab0f4b710e9170dc02763ccb80bd4b` |
| jetbrains-mono-nerd-font-propo-regular.ttf | `8a2803de76ad18ed82f465dfd17130032c34c031b263179d3047a547c7caa460` |

### Proportional status icons

La variante **JetBrainsMono Nerd Font Propo Regular** evita comprimir los
pictogramas anchos dentro de una celda monoespaciada. Se aplica a tamaño 12
solo a los iconos de clima, métricas y audio, sin cambiar el texto Mono 10, la terminal,
la fuente Wi-Fi ni la batería ya validada.

- [Official font asset](https://raw.githubusercontent.com/ryanoasis/nerd-fonts/v3.5.1/patched-fonts/JetBrainsMono/Ligatures/JetBrainsMonoNerdFontPropo-Regular.ttf).
- Tamaño: 2 571 412 bytes, aproximadamente 2,45 MiB en disco.
- Git blob SHA1 verificado: `333bfac1567a074e6471c7d14f62c78a7f8d84ee`.
- Archivo sin modificar; se conserva con nombre kebab-case en el repositorio.
- OFL y avisos de iconos coinciden byte por byte con los del tag oficial v3.5.1
  ya conservados en `config/fonts/OFL.txt` y `config/fonts/UPSTREAM.md`.

El manifiesto enlaza el TTF individualmente a `~/.local/share/fonts/`.
Tras aplicarlo, ejecutar `fc-cache "$HOME/.local/share/fonts"` y comprobar
`fc-match 'JetBrainsMono Nerd Font Propo'`. No se instala la colección completa
ni se inicia ningún proceso por añadir esta fuente.

## Runtime coverage

El texto de Kitty y de la barra usa JetBrainsMono Nerd Font Mono, tamaño 10. Starship utiliza
52 símbolos Unicode configurados; los glifos Nerd Font están cubiertos por los
TTF gestionados. Los signos estándar adicionales resuelven mediante DejaVu Sans
Mono y Symbola de Debian. El icono Git U+F1D3 evita el código obsoleto U+F7A1.

El indicador de batería usa 25 glifos ya presentes en el mismo TTF: once niveles,
once niveles con rayo, batería desconocida, verificación y pausa. El icono se
renderiza a 12 y el porcentaje conserva tamaño 10. La cobertura se comprueba
con `fc-query` en `tests/test_battery.py`; no requiere otra fuente ni un cambio
de tipografía global. Los códigos se contrastan con
[Nerd Fonts v3.5.1 glyph names](https://raw.githubusercontent.com/ryanoasis/nerd-fonts/v3.5.1/glyphnames.json).

```sh
fc-cache "$HOME/.local/share/fonts"
fc-match 'JetBrainsMono Nerd Font Mono'
fc-match 'BGH Status Icons'
fc-match 'JetBrainsMono Nerd Font Propo'
```

Una nueva fuente requiere archivo redistribuible, licencia, versión/origen,
hash y enlace explícito. Actualizar los tests de cobertura al cambiar assets.
