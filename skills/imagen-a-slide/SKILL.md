---
name: imagen-a-slide
description: Reconstruye diapositivas que vienen como imagen (PNG/JPG/WEBP, capturas, PDF o PPTX "planos" exportados como imágenes) con el mismo diseño y EDITABLES, en dos salidas que comparten el proceso - un PowerPoint con texto, formas, tablas y gráficos nativos (pptx, por defecto; Windows con PowerPoint de escritorio) y/o una presentación HTML en UN SOLO ARCHIVO autocontenido para enviar (html). Argumento opcional pptx | html | ambos. Úsala cuando el usuario pase una o varias imágenes de diapositiva y pida "hazme un pptx de esta imagen", "hazme un HTML / una presentación web de esta imagen", "lo mismo con esta", "rehacer esta slide", "convertir esta imagen en diapositiva", limpiar el fondo de una portada o poner logos oficiales. No la uses para crear decks desde cero sin imagen de referencia, ni para editar un pptx que ya es editable (para eso, la skill pptx).
license: "MIT"
compatibility: "Windows con PowerShell 5.1. Salida pptx: PowerPoint de escritorio (y Excel solo para gráficos nativos). Salida html: Microsoft Edge solo para el PNG de control. Opcional: Podman o Python con numpy, opencv y scikit-image para la comparación numérica."
metadata:
  author: "svg153"
  version: "2.1"
---

# Imagen de diapositiva → PPTX editable y/o HTML de un solo archivo

## Activation Contract

Úsala cuando el usuario aporte una o varias **imágenes de diapositivas ya diseñadas** (PNG/JPG/WEBP, capturas, un PDF exportado o un PPTX cuyas diapositivas son solo imágenes) y quiera recuperarlas **editables con el mismo diseño**, como PowerPoint (`pptx`, por defecto), como un HTML de un solo archivo (`html`) o ambos (`ambos`). El argumento opcional es `[pptx|html|ambos] <imagen(es)>`. También cubre limpiar el fondo de una portada para poner encima los textos editables y sustituir logos dibujados por los oficiales.

No la uses para crear una presentación nueva sin imagen de referencia, para editar un `.pptx` que ya es editable, para extraer el sistema de diseño de un deck existente (eso es `deck-design-system`) ni fuera de Windows cuando se pida `pptx`.

Datos de cliente (logos, paleta, rejilla): nunca dentro de esta skill. Van en un perfil local (§1, «Perfiles de cliente»).

Objetivo: una diapositiva que se pueda **editar como si se hubiera hecho a mano**. Nunca pegues la diapositiva entera como imagen y lo llames editable.

El flujo separa **pensar** (modelo principal) de **ejecutar** (motores fijos + modelos pequeños). Nadie escribe código de PowerPoint ni HTML: se escribe una **spec JSON** (`reference/spec.md`), común a las dos salidas, y un motor la convierte:

| Salida (`$ARGUMENTS`) | Motor | Resultado |
|---|---|---|
| `pptx` (por defecto) | `build_from_spec.ps1` | `.pptx` por diapositiva + PNG de control |
| `html` | `build_html.ps1` | **un único `.html`** (visor, spec e imágenes dentro; se envía y se abre en cualquier navegador sin red) + PNG de control |
| `ambos` | los dos, con la misma spec | `.pptx` + `.html` |

Si el usuario no dice la salida, es `pptx`. "Presentación web", "HTML", "para mandar por correo y abrir en el navegador" = `html`. Los pasos 0-4 son idénticos; solo cambia el motor del build y la entrega.

Todo es local: PowerShell 5.1 + PowerPoint (y Excel solo para gráficos nativos del pptx); el HTML solo necesita Edge para el PNG de control. No hace falta Node, Python ni contenedores (solo el paso opcional `compare.ps1` usa Podman o Python). **No subas imágenes ni textos del cliente a servicios externos.** La única descarga permitida son logos públicos (§2).

Ejecuta siempre los scripts así (las rutas con espacios, entre comillas):
`powershell -NoProfile -ExecutionPolicy Bypass -File "${CLAUDE_SKILL_DIR}/scripts/<script>.ps1" <args>`

| Script | Para qué |
|---|---|
| `build_from_spec.ps1 -Spec x.json` | spec → `.pptx` + `.png` por diapositiva (+ `_dudas.md` si hay dudas) |
| `ocr.ps1 -Src img [-Out x.ocr.json]` | OCR local de Windows: caja de cada línea (numerada, `n`) y tamaño de letra calculado **por anchura** (`pt_regular`/`pt_bold`). Escribe además `x.ocr.png`, la imagen con cada línea recuadrada y numerada: azul = texto, rojo = sin tamaño (iconos, símbolos). Lo que no aparece recuadrado (casi todos los iconos) se mide leyendo la imagen. `-NoOverlay` para omitirla |
| `crop.ps1 -Src img -Out pieza.png -Box "x0,y0,x1,y1" [-Transparent]` | Recorta una región de la fuente como `picture` movible: una foto o captura dentro de una tarjeta, un logo sin SVG oficial o un icono complejo que no compensa redibujar. `-Transparent` quita un fondo **liso** (sin halo). Imprime la línea de spec lista para pegar. No es para sacar una foto de un degradado (para eso, `clean_bg`) |
| `clean_bg.ps1 -Src img -Out fondo.png -Boxes "x0,y0,x1,y1;…"` | Borra textos y logos de una imagen y continúa el degradado (placa de fondo). Cuenta: **una caja por bloque**, con ≥ 25 px de margen a izquierda y derecha (los bordes se funden 12 px con el original) y ~20 px arriba y abajo (tildes y descendentes). Mira siempre el PNG resultante |
| `prepare_pptx.ps1 -Src plano.pptx -OutDir pages` | PPTX de imágenes → `pages/sN.png` + `manifest.json` con las notas |
| `prepare_pdf.ps1 -Src deck.pdf -OutDir pages [-Pages "1,3-5"]` | PDF (diapositivas exportadas o escaneadas) → `pages/sN.png` + `manifest.json`, con el lector de PDF de Windows. Avisa si una página no es 16:9 |
| `build_html.ps1 -Spec a.json[,b.json] -Out deck.html` | Salida `html`. La MISMA spec → **un único `.html`** autocontenido: el visor `html/deck.js` y `deck.css`, la spec y las imágenes en base64, sin red ni dependencias. Teclas: flechas para navegar, F pantalla completa, N notas, E editar textos, P imprimir/PDF. Escribe `<stem>_html.png` con Edge sin ventana (perfil temporal) para pasarlo a `compare.ps1`. Gráficos en SVG propio, sin Excel. Fuente: Segoe UI (en Mac sale la del sistema) |
| `bench.ps1 -SelfTest` / `bench.ps1 -Dir <banco>` | **Banco de pruebas.** `-SelfTest`: regresión con el ejemplo de la skill (copia idéntica = 0 avisos; copia con 3 fallos = exactamente esos 3), sin datos de cliente. `-Dir`: casos reales (`original.png` + `spec.json`, que se reconstruye, o + `render.png`, que solo se compara), con `history.csv` y el cambio respecto a la ejecución anterior. **Ejecútalo después de cambiar un script, una regla o un ejemplo.** El banco va fuera de la skill: tiene diapositivas de cliente |
| `package_plugin.ps1 -OutDir <carpeta> [-Author …] [-Version …]` | Genera el plugin publicable (`imagen-a-slide.zip` + entrada de marketplace) con esta skill y los dos agentes. Solo incluye los logos permitidos y **falla** si encuentra un término de la lista de cliente (`forbid.txt`, junto al banco), el nombre de usuario o una ruta local. Úsalo solo cuando el usuario pida publicar |
| `compare.ps1 -Src fuente.png -Render Nombre.png -Spec Nombre.json [-Slide N]` | **Opcional.** Comparación numérica por elemento: SSIM, desplazamiento `dx/dy` en px de la fuente y, en textos, relación de anchura con el tamaño de letra sugerido. Escribe `Nombre.compare.md` y la hoja `Nombre.compare.png` (fuente, render y diferencias). Usa el contenedor Podman `imagen-a-slide-compare` (se construye solo la primera vez) o un Python local con numpy, opencv y scikit-image. Si no hay ninguno de los dos, sáltate este paso. `compare.ps1 -Demo` es una autoprueba que no necesita archivos. Pasa como `-Spec` la spec con la que se construyó el render: el tamaño sugerido se calcula a partir de su `size`. **Sin `-Spec`**, detecta solas las zonas que difieren (sirve para revisar reconstrucciones antiguas o de otra herramienta) |

## 0. Reglas de seguridad (obligatorias)
- PowerPoint tiene **una sola instancia**: COM se engancha al PowerPoint del usuario, que puede estar editando otra presentación. **Nunca** `Quit()` ni `Stop-Process POWERPNT`/`EXCEL`, y nunca código COM propio fuera de los scripts. Los scripts solo cierran lo que abren e imprimen `presentaciones abiertas antes=N despues=N`. Si los dos números no coinciden, para y avisa.
- Por defecto, **un archivo por diapositiva**, porque el usuario suele copiarlas a mano a su presentación general. Si el destino está abierto, el motor guarda `_v2`, `_v3`…
- Corrige siempre en la spec y reconstruye. No edites el `.pptx` ni el `.html` a mano.
- Si la spec tiene `chart`, PowerPoint necesita ventana: el motor abre la presentación minimizada. Si PowerPoint no estaba abierto, al terminar queda una ventana de PowerPoint vacía y algún Excel en segundo plano. Avisa al usuario de que puede cerrarlos él; tú no los cierres.
- `build_html.ps1` no toca PowerPoint: con salida `html` no hay riesgo COM. Usa Edge sin ventana con un perfil temporal, nunca el del usuario.

## 1. Clasificar (modelo principal; no delegar)
Pregunta solo si no está claro qué prima: **editabilidad** (por defecto), **fidelidad visual** o **plantilla corporativa**. Para cada diapositiva decide:

| Contenido | Estrategia |
|---|---|
| Texto, tarjetas, diagramas (cajas y flechas), tablas, gráficos | **native**: todo como elementos; tablas y gráficos SIEMPRE nativos |
| Foto, **cualquier ilustración con sombras, volumen o degradados** (calendarios 3D, portapapeles, nubes con brillo), fondos artísticos | **hybrid**: placa de fondo limpia con `clean_bg` (sin textos ni logos de empresa) como `background.image`, y todo lo demás encima. Es más fiel y más barato que redibujar. **Nunca** recortes la foto con un difuminado: deja una costura vertical |
| Ilustración plana y simple, o que el usuario quiera poder editar por piezas | **native** con elementos `svg` |

- **Logos de empresa** (la tuya, tus clientes…): siempre como elemento, con su SVG oficial. La skill solo trae `@logos/ejemplo_cliente.svg`, un logo ficticio de ejemplo. Los logos reales van en un **perfil de cliente** (ver el punto siguiente), nunca dentro de esta skill.
- **Perfiles de cliente**: los datos de un cliente (logos, paleta, rejilla, reglas de confidencialidad) viven fuera de esta skill, en una skill local propia (p. ej. `imagen-a-slide-<cliente>`) con un `perfil.json`:
  - formato: `{ "name": "...", "logos": "assets/logos", "theme": { "font", "headFont", "text", "bg" } }`;
  - la spec lo referencia con `"profile": "<ruta>/perfil.json"`, o se usa la variable de entorno `IMAGEN_A_SLIDE_PROFILE`;
  - los motores buscan `@logos/<archivo>` primero en los logos del perfil y después en `assets/logos` de esta skill, y el tema del perfil rellena lo que la spec no fije;
  - la skill del cliente invoca a esta y le añade sus datos (composición). Esta skill no sabe nada del cliente.
- Para un logo que aún no tengas, descarga el SVG de `https://commons.wikimedia.org/wiki/Special:FilePath/<Archivo>.svg` (User-Agent genérico, sin datos del usuario), quítale DOCTYPE y metadatos y deja solo viewBox + paths.
- Los logos integrados en la propia ilustración (p. ej. iconos de producto dibujados dentro de la foto o la ilustración) se quedan en el fondo. Los que van en una caja o tarjeta propia se ponen como elemento.
- **Tema y rejilla comunes** cuando hay varias diapositivas: fija una vez la fuente (Segoe UI por defecto; nunca Aptos), los colores y la posición y tamaño del título. Pásalo igual a todas las specs, para que el título no baile entre diapositivas del mismo tipo.

## 2. Medir (OCR = geometría; el modelo = texto y significado)
1. `ocr.ps1` sobre cada imagen. Usa sus `x,y,w,h` para las cajas de texto, y `pt_bold`/`pt_regular` como punto de partida del tamaño de letra:
   - Línea toda en negrita: `pt_bold`, unos 5 % menos en títulos grandes (> 30 pt).
   - Línea normal: `pt_regular`.
   - Mezcla de etiqueta en negrita y texto normal: empieza un 3-4 % por debajo de `pt_regular`, o desbordará.
   - Etiquetas con letras espaciadas: el OCR sobreestima; calcula el tamaño por la altura de mayúscula (px × 0,48 / 0,7) y ajusta `charSpacing` hasta igualar el ancho.
   - Texto pequeño (< 9 pt) dentro de cajas chicas: el OCR junta o confunde líneas; mídelo leyendo la imagen.

   Redondea a 0,5 pt y recalibra tras el primer build comparando anchos.
2. El texto del OCR pierde tildes y eñes (`soluciÃ©n`, `gesti6n`): **el texto final siempre se lee de la imagen**. Une las líneas de un mismo párrafo en un solo `text`, con `\n` donde la imagen salta de línea.
3. Los elementos que no son texto (tarjetas, iconos, líneas, logos) se miden leyendo la imagen. Mira `x.ocr.png` para ver qué detectó el OCR y qué no.
   - Fotos, capturas o logos sin SVG oficial que van **sueltos** (en una tarjeta, no fundidos con el fondo): `crop.ps1` y elemento `picture`.
4. Lo que no puedas leer con seguridad va a `doubts` de la diapositiva o a `confidence < 0.7`, y acaba en `_dudas.md`.

## 3. Repartir el trabajo (ver `REPARTO.md`)
- **1 diapositiva sencilla**: hazla tú.
- **≥2 diapositivas, o 1 larga**: un subagente `slide-spec-writer` (Sonnet) **por diapositiva, en paralelo**. Su brief (plantilla en REPARTO.md) incluye la imagen, la salida, la decisión del paso 1, el tema y la rejilla, y la ruta de esta skill: `${CLAUDE_SKILL_DIR}`.
- Las instrucciones de los dos subagentes están en `agents/slide-spec-writer.md` y `agents/slide-qa.md`. Si tu cliente no los tiene instalados como agentes, lanza un subagente genérico con `model: sonnet` (o `haiku` para el QA) y dile que siga ese archivo, con `Skill: ${CLAUDE_SKILL_DIR}` en el brief.
- **Ilustraciones SVG complejas**: tú o un subagente Opus.
- **QA**: `slide-qa` (Haiku) por render. Tú decides qué se corrige.
- **Punto de control**: con un deck de varias diapositivas, enseña al usuario la primera ya revisada antes de lanzar el resto. Así un error de tema no se repite en todo el deck.

## 4. Construir, comparar, corregir (máx. 3 vueltas)
Build → `compare.ps1` (si está disponible) → mira el PNG junto a la imagen fuente (o `slide-qa`) → corrige la spec → build.
- Salida `html`: el build es `build_html.ps1 -Spec x.json -Out x.html` y el render es `x_html.png` (o `x_html_sN.png`). Con `ambos`, itera con un solo motor (el pptx) y genera el otro al final; compara también el render HTML con `compare.ps1` (HTML vs PPTX suele dar 0 avisos: la spec se respeta igual en los dos).
- `compare.md` da cifras objetivas: aplica directamente los `dx/dy` (resta el desplazamiento a `x/y`) y el `size` sugerido. Que sean > 15 px o > 5 % de anchura es un fallo real.
- Pasa `compare.md` a `slide-qa` para que se centre en lo que las cifras no ven: texto erróneo, negritas o elementos que faltan.
- En los textos, el SSIM siempre sale bajo frente a una imagen rasterizada (otro suavizado, otra fuente), así que solo avisa por debajo de 0,45. Lo que cuenta son `dx/dy` y la anchura, medidos con la caja de tinta.
- Una **anchura igual en todos los textos** (p. ej. todos ×0,87) indica un tamaño de letra mal calibrado en toda la diapositiva: multiplica todos los `size` por 1/anchura.
- Las zonas enormes (ilustraciones o fondo) con `dx/dy` grandes pueden venir del fondo. Compruébalas en la hoja antes de mover nada.

Prioridad:
1. Texto cortado o desbordado.
2. Texto erróneo, saltos de línea o negritas en otro sitio.
3. Elementos solapados o pegados al borde.
4. Elementos que faltan o sobran, y texto duplicado (en el fondo y nativo).
5. Posición con más de 15 px de diferencia.
6. Colores y tamaños.

Para tras 3 vueltas o cuando solo queden diferencias de fuente inevitables.

## 5. Entrega
- `pptx`: `.pptx` (uno por diapositiva, salvo que pidan deck) y `_dudas.md` si existe.
- `html`: **un solo `.html` con todas las diapositivas** (pasa todas las specs a `build_html.ps1`, en orden) y `_dudas.md` si existe. Dile al usuario las teclas (flechas, F pantalla completa, N notas, E editar textos, P imprimir/PDF), que lo editado con E no se guarda al recargar y que fuera de Windows la fuente Segoe UI se sustituye por la del sistema.
- Resumen breve: estrategia de cada diapositiva y limitaciones (fuentes sustituidas, ilustraciones redibujadas).
- Si hay que encajarlo en una plantilla corporativa, después usa la skill `pptx`.

## 6. Aprender (obligatorio)
Anota en `LEARNINGS.md`, con fecha y modelo, qué falló y cómo se arregló, sobre todo lo que fallaron los modelos pequeños. Si un fallo se repite dos veces, conviértelo en regla aquí, en `reference/spec.md` o en el agente correspondiente. Así la skill mejora en cada uso.

Después de cambiar un script, una regla o un ejemplo, ejecuta `bench.ps1 -SelfTest` (y `bench.ps1 -Dir` si hay banco). Si un caso empeora, revierte o corrige antes de dar el cambio por bueno. Cuando una reconstrucción quede bien, añádela al banco: `original.png` + `spec.json` + sus recursos, en una carpeta nueva.
