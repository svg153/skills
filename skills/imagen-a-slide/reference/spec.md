# Spec JSON (común a `build_from_spec.ps1` → pptx y `build_html.ps1` → html)

Salida `html`: la spec es la misma; `output` y `png` se ignoran (los nombres los da `-Out`).
En el HTML, 1 px CSS = 1 pt, y el texto sigue la semántica de PowerPoint (sin margen por defecto, ajuste de línea solo con `wrap` o alineado no a la izquierda).
Limitaciones del visor HTML (aceptables; avisa al usuario si la diapositiva las usa):
- `donut`, `can`, `cube` y `cloud` salen como rectángulo.
- `chart` `scatter` no está soportado.
- El borde discontinuo de una forma rectangular sale siempre como `dashed`.

## Unidades y convenciones
- Coordenadas en **px de la imagen fuente** (`sourceWidth`, por defecto 2000). El motor las convierte a una diapositiva 16:9 de 960×540 pt (×0,48 si la fuente mide 2000 px).
- Tamaños de letra en **pt**. Colores hex de 6 dígitos sin `#`.
- `elements` va en **orden de capas**: el primero queda al fondo.
- Textos en UTF-8 (tildes, `≈`, `€` sin problema). `\n` = salto de línea dentro del párrafo.
- Rutas relativas a la carpeta del JSON. `@logos/<archivo>.svg` = logo buscado primero en el perfil de cliente (si lo hay) y después en `assets/logos` de la skill.

## Documento
```json
{ "sourceWidth": 2000,
  "output": "Nombre.pptx",           // si existe y está abierto -> Nombre_v2.pptx
  "png": "Nombre.png",               // solo con 1 diapositiva; con varias: Nombre_s1.png, Nombre_s2.png…
  "theme": { "font": "Segoe UI", "headFont": "Segoe UI", "text": "374151", "bg": "FFFFFF" },
  "background": { "color": "FFFFFF" },   // o { "image": "fondo_limpio.png" }
  "profile": "C:/ruta/perfil.json",      // opcional: perfil de cliente (logos + tema); también IMAGEN_A_SLIDE_PROFILE
  "elements": [ … ],
  "notes": "notas del orador", "doubts": [ "texto ilegible en…" ] }
```
Para varias diapositivas en un mismo archivo: `"slides": [ { "background", "elements", "notes", "doubts" }, … ]`.

## Campos comunes
`name` (nombre en el panel de selección; ponlo siempre), `group` (los elementos con el mismo valor se agrupan), `rotate` (grados), `alt` (texto alternativo para imágenes), `confidence` (0-1; < 0,7 va a las dudas).

## Tipos de elemento
### `text`
`x y w h`, `text` **o** `paragraphs:[{text, size, bold, italic, color, align, bullet: true|"number", level}]`, `size`, `color`, `bold`, `italic`, `font`, `role` (`title`/`subtitle` usan `theme.headFont`), `align` left|center|right|justify, `anchor` top|middle|bottom, `lineSpacing` (pt exacto), `spaceAfter` (pt), `charSpacing` (pt), `wrap`, `fill`, `margin`,
`runs:[{match, all, bold, italic, underline, color, size, gradient:[c1,c2]}]` (formatea la primera aparición de `match`, o todas si `all: true`).
- Si `wrap` es false (por defecto) y el texto está alineado a la izquierda, los saltos son los tuyos (`\n`) y no se reorganiza.
- Con `align` center o right, el ajuste de línea se activa solo.
- Viñetas: `bullet: true`. Nunca escribas `•` en el texto.

### `shape` (y su alias `rect`)
`shape`: rect, roundRect, ellipse, triangle, rtTriangle, diamond, parallelogram, trapezoid, hexagon, octagon, plus, regularPentagon, homePlate/pentagon, chevron, rightArrow, leftArrow, upArrow, downArrow, leftRightArrow, star5, donut, can, cube, cloud, flowChartProcess, flowChartDecision, flowChartTerminator.
Campos: `x y w h`, `fill` (null = sin relleno), `fillTransparency` 0-1, `line` ("HEX" o `{color, width, dash}`), `lineWidth`, `radius` 0-0.5 (roundRect), `shadow` true.
Texto dentro de la forma: los mismos campos que `text`, puestos en la propia forma.
`rect` con `radius > 0` = roundRect.

### `line`
`x1 y1 x2 y2`, `color`, `width` (pt), `dash` solid|dash|dot|squareDot|dashDot|longDash, `beginArrow`/`endArrow` none|triangle|arrow|stealth|diamond|oval.

### `picture` / `svg`
`picture`: `path` (png/jpg/svg). `svg`: `svg` con el marcado completo en línea, para iconos.
Para una pieza recortada de la fuente (foto en una tarjeta, logo sin SVG oficial): `crop.ps1 -Box "x0,y0,x1,y1" [-Transparent]` imprime la línea `picture` con `x y w h` ya puestos; añade `name` y `alt`.
`x y w [h]`: sin `h` mantiene la proporción.
Iconos: trazo, viewBox `0 0 24 24`, `stroke-width` 1.7 y el color del tema. Nada de `<use>`, filtros ni `<text>`; los degradados lineales y radiales sí funcionan.
Tamaño de icono: el dibujo ocupa unos 3/4 del viewBox, así que pon `w` ≈ ancho del icono en la fuente × 1,3 y céntralo en el centro del icono original (no en su esquina).
El motor avisa si una imagen cubre más del 80 % de la diapositiva: solo se acepta como fondo limpio.

### `table`
`x y w h`, `rows` (array de filas; cada celda es un texto o `{text, bold, color, fill, align, size}`), `colW` (px), `size`, `color`, `fill`, `align`, `header: {fill, color, bold}` (primera fila), `border: {color, width}`.

### `chart` (nativo, necesita Excel)
`chartType`: bar | line | pie | doughnut | area | scatter. `dir` col|bar, `stacked`, `markers`.
`series:[{name, labels:[…], values:[…]}]`, `title`, `colors:[…]` (por serie; en pie/doughnut, por porción), `showValue`, `valueFormat` ("0", "0.0%"…), `showLegend`, `estimated` (true si has medido barras a ojo: va a las dudas).

## Recetas probadas
- **Tarjeta con icono**:
  - `shape` roundRect con fill F3F4F6, radius 0.14 y shadow.
  - `svg` de ~75 px centrado en vertical.
  - `line` vertical, a 8 px del borde de la tarjeta por arriba y por abajo.
  - `text` con la misma caja que la tarjeta, `anchor: middle` y la etiqueta en negrita en `runs`.
- **Caja centrada** con varias líneas de distinto tamaño: `text` con `align: center` y `paragraphs`, cada uno con su `size`.
- **Palabra en degradado** (p. ej. «degradado»): `runs:[{match:"degradado", gradient:["14B8A6","2563EB"]}]`.
- **Etiqueta espaciada** («S E C C I Ó N»): escribe el texto normal y añade `charSpacing` 4-5.
- **Ejemplos completos y probados**: `examples/ejemplo_tarjetas.json` (tarjetas y logos) y `examples/ejemplo_completo.json` (diagrama, tabla, viñetas, gráficos y dos diapositivas).
