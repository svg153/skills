# Aprendizajes (se amplía en cada uso)

Formato: fecha · quién (modelo) · qué falló o se descubrió · cómo se arregló · ¿convertido en regla?

Los casos reales se citan por tipo de diapositiva (A: 7 tarjetas de texto; B: nativa compleja con cajas de cifras; C: portada con foto; D: separador con ilustración 3D), nunca por su contenido.

## Coste medido por tarea (para decidir si delegar)
| Tarea | Modelo | Tokens del subagente | Tiempo | Resultado |
|---|---|---|---|---|
| Spec + build, 7 tarjetas (A) | Sonnet | ~57k | ~80 s | Igual o mejor que Opus |
| Spec + build, nativa compleja (B) | Sonnet | ~67k | ~100 s | Fiel; 3 builds |
| Spec + `clean_bg` + build, híbrida (C) | Sonnet | ~67k | ~90 s | Fiel; 2 limpiezas, 2 builds |
| Spec + `clean_bg` + build, híbrida (D) | Sonnet | ~58k | ~65 s | **Más fiel que el redibujo de Opus** |
| QA visual de un render | Haiku | ~37-40k | 13-26 s | Útil, sin falsos positivos; encontró un fallo del motor |

## 2026-11-13 · sesión inicial (Opus, sin delegar) — 4 diapositivas de prueba
- Llamar a `Quit()` en PowerPoint cerró las presentaciones del usuario: COM se engancha a su única instancia. → El motor ya no cierra PowerPoint. **Regla 0**
- Logos escritos a mano ≠ logos reales. → Se usan los SVG oficiales (p. ej. de Wikimedia Commons), guardados en `assets/logos`. **Regla §1**
- Portada con foto recortada y difuminada → costura vertical visible. → Placa de fondo limpia con `clean_bg`. **Regla §1**
- Configuración regional en español: `-f` escribía comas decimales en el SVG. → El motor usa la cultura invariante.
- Codificación: un `.ps1` en UTF-8 sin BOM rompe los acentos en PowerShell 5.1. → Los scripts son ASCII y los textos van en el JSON, que se lee en UTF-8.
- `WordWrap` desactivado con texto centrado → el texto se centra respecto al borde izquierdo. → El motor activa el ajuste si `align` no es left.
- El anclaje vertical se pierde si no se fija `Top`/`Height` después. → Lo hace el motor.
- En PowerShell, `@(@(a,b,c,d))` con un único elemento se aplana. → `clean_bg` recibe las cajas como texto.
- En los reemplazos con regex de .NET, `$_` del texto de sustitución es "toda la entrada" y corrompió un archivo. → No uses regex para reescribir código.

## 2026-11-13 · piloto Sonnet — diapositiva A
- Sonnet calibró el tamaño de letra comparando anchos: título 27 pt (Opus había puesto 34) y tarjetas 13,2 pt (Opus 11,5). → **El OCR ahora da `pt_regular`/`pt_bold` calculados por anchura** con WPF. Coinciden con la calibración de Sonnet (±0,5 pt) sin necesidad de construir.

## 2026-11-13 · v1.0 unificada (fusión con una skill anterior basada en contenedor)
- La skill anterior (contenedor Podman con Python, Node y LibreOffice) no funcionaba en el equipo de pruebas: no había Podman. Se incorporaron sus ideas:
  - tablas, gráficos, viñetas, flechas, formas variadas, grupos, notas y dudas;
  - native/hybrid, tema y rejilla comunes, punto de control con el usuario;
  - OCR = geometría y modelo = texto;
  - prohibir capturas a pantalla completa.
- Gráficos: guardar `ChartData` en una variable y luego llamar a `Activate()` devuelve `Workbook` nulo. → Hay que leer `$sh.Chart.ChartData.Workbook` de nuevo tras activar, con reintentos.
- Una función de PowerShell devuelve al flujo de salida cualquier valor de COM no capturado (un array con booleanos). → Pipe a `Out-Null` y usar `$pres.Slides(j)`.
- `$true -eq 'number'` es verdadero en PowerShell, así que las viñetas salían numeradas. → Comprobar `-is [string]`.
- En algunos equipos, una política de administración puede **bloquear los marketplaces de plugins que no estén en una lista aprobada**. → Publicar mediante un marketplace aprobado o instalar la skill como skill personal.

## 2026-11-13 · pruebas en paralelo (3 × Sonnet + 3 × Haiku)
- 3 builds simultáneos contra el mismo PowerPoint del usuario: sin errores de "ocupado" y siempre con `antes` y `despues` iguales. **El paralelo funciona.**
- **Híbrido > redibujo** también para ilustraciones con volumen o sombras: la diapositiva D con la ilustración original limpia queda mucho más fiel que el SVG redibujado por Opus. → **Regla §1 cambiada**
- `clean_bg`: con el borde izquierdo de la caja a 8 px del texto quedaron restos, porque el borde se funde 12 px con el original. → **Margen ≥ 25 px a los lados**, ~20 px arriba y abajo, y una caja por bloque. **Regla en la tabla de scripts**
- OCR, desviaciones del tamaño por anchura:
  - Líneas con etiqueta en negrita y texto normal: empezar un 3-4 % por debajo (13 pt desbordaba y 12,5 encajaba).
  - Títulos grandes en negrita: unos 5 % menos.
  - Etiquetas con letras espaciadas: el OCR sobreestima; usar la altura de mayúscula y luego `charSpacing`.
  - Texto < 9 pt en cajas pequeñas: el OCR junta líneas y lee mal; medir leyendo la imagen.
  → **Regla §2**
- El OCR ahorró ~70 % del trabajo de medir (20 de 30 líneas en la diapositiva B).
- **Haiku QA encontró un fallo del motor**: el degradado de una palabra salía casi liso porque PowerPoint lo extiende sobre todo el cuadro de texto. → El motor fija ahora los puntos del degradado en los límites de la palabra (`BoundLeft`/`BoundWidth`).
- Haiku QA también detectó un guion corto en lugar de uno largo y el peso semibold frente a bold de un título (se usa `"font": "Segoe UI Semibold"`). Ningún falso positivo en las 3 revisiones.

## 2026-11-16 · comparación numérica opcional (Opus)
- Con Podman (WSL2) disponible, se añade `compare.ps1` + `compare.py`, en un contenedor mínimo (Python, OpenCV, scikit-image; sin LibreOffice, porque el render lo hace PowerPoint). Si no hay Podman, usa un Python local; si tampoco lo hay, el paso se salta.
- Por elemento mide SSIM, `dx/dy` (búsqueda por plantilla, ±40 px) y, en textos, la relación de anchura de la tinta → tamaño de letra sugerido.
- Prueba sintética: título desplazado +20 px → `dx=+20` exacto; cuerpo a 110 % → anchura ×1,12 y sugiere 16 → 14 pt; los elementos idénticos no dan avisos.
- Git Bash reescribe las rutas tipo `/w/...` al pasarlas a `podman run`. → Lanza siempre Podman desde PowerShell (`compare.ps1`).

## 2026-11-16 · validación de la comparación con renders reales de PowerPoint (Opus)
- Prueba: `ejemplo_tarjetas.json` construido como "fuente", una copia idéntica y otra con tres fallos conocidos (título +25 px, Texto 1 de tamaño ×1,1, logo +20 px).
  - Idéntica: SSIM 1,000 y **0 avisos**: el render de PowerPoint es determinista, sin falsos avisos.
  - Con fallos: **los tres detectados con su valor exacto** (`dx=+25`, tamaño sugerido, `dy=+20`).
- Los `picture`/`svg` sin `h` se saltaban y el logo movido pasaba inadvertido. → La altura se estima a partir de la tinta de la fuente.
- Un contenedor (tarjeta) salía con SSIM bajo solo porque su texto estaba mal. → Ya no da aviso; aparece como "afectado por <hijo>".
- `-Spec` tiene que ser la spec del render, no la de la fuente: el tamaño sugerido se calcula a partir de su `size`.
- Se lanzó el ejemplo con las rutas `C:\ruta\...` de la documentación. → `compare.ps1` comprueba ahora los archivos con un mensaje claro, y tiene `-Demo` para probarlo sin archivos.

## 2026-11-16 · comparación con originales reales (Opus)
- En un deck de prueba, cada original plano iba seguido de su reconstrucción. Se compararon 4 originales con 13 reconstrucciones guardadas (Opus v1/v2/v3 y Sonnet), sin spec.
- Con originales rasterizados, **el SSIM de todo texto sale bajo** (0,4-0,7) aunque esté bien, por el suavizado y la fuente. El umbral 0,80 marcaba de 10 a 15 zonas por diapositiva. → Textos y zonas solo avisan por SSIM < 0,45; se miden con la caja de tinta (anchura, altura y dx/dy). Bajan a 1-12 avisos, todos con un motivo concreto.
- El SSIM global y el número de avisos **ordenan las versiones igual que la revisión a ojo**: Sonnet > Opus en las 4 (p. ej. diapositiva A: Opus con 11-12 avisos, Sonnet con 3).
- Diapositiva A (Opus): todos los textos salen con anchura ×0,87. Es exactamente 11,5 / 13,2 pt, el error de tamaño que se descubrió a mano. **La comparación lo detecta sola y sin spec.**
- Las zonas muy grandes (ilustración + fondo) dan `dx/dy` poco fiables: hay que mirarlas en la hoja.
- Añadido: modo sin spec (zonas automáticas a partir del mapa de diferencias).

## 2026-11-16 · diapositiva A reconstruida con el bucle build + compare (Opus, sin delegar)
- Hybrid: placa `clean_bg` con 3 cajas (cabecera, logos, bloque de tarjetas) + 7 tarjetas nativas agrupadas (forma, icono SVG, separador y texto). 1 limpieza y 2 builds.
- **Resultado** (comparación sin spec, mismo método para todas): Opus v1 0,735 / 11 avisos · Opus v2 0,737 / 10 · Sonnet v3 0,772 / 3 · **nueva 0,806 / 3**. Con spec quedan 2 avisos aceptables (un icono redibujado y un logo oficial frente al raster).
- Tamaños del OCR sin tocar: cuerpo 13,2, título 27 y etiqueta 11,5. Acertaron a la primera; `compare` lo confirmó (anchura 0,97-1,01).
- Build 1: `compare` detectó que **un texto desbordaba su tarjeta 28 px** (sugirió 12,5) y que los iconos dibujaban ~45 px frente a 60-72 en el original. → Con un viewBox 24 y trazo, el dibujo ocupa ~3/4 de la caja: **pon el `w` del icono ≈ ancho del icono en la fuente × 1,3**.
- Mejoras de `compare.py` que salieron de esta diapositiva (cada una comprobada con la regresión idéntica/con fallos/demo):
  - Margen de tinta pequeño en vertical (6 px): con 30 px atrapaba la línea vecina y daba "título ×0,55" y "dy=−50" falsos.
  - Solo cuentan los trazos cuyo centro cae dentro de la caja (en vertical), y se excluyen formas, líneas e imágenes ajenas, como el subrayado del título.
  - Nuevo aviso **DESBORDA su caja N px** (prioridad 1); antes solo veía una anchura del 4 %.
  - Tarjetas: se mide su contorno, no el contenido. Líneas y formas finas: solo cuenta dx/dy, nunca el SSIM. Iconos e imágenes: SSIM < 0,45.
  - La plantilla solo recoloca la medida si coincide ≥ 0,8 (con 0,52 dio un "dx=+41" falso).
- `examples/ejemplo_tarjetas.json` llevaba los tamaños erróneos de Opus (título 34, tarjeta 11,5). → Corregido a 27 y 13,2, porque `slide-spec-writer` copia ese ejemplo.

## 2026-11-16 · piezas recuperadas de la idea original (Opus)
Revisada la skill frente al plan de la skill anterior: todo lo probado seguía en su sitio. Faltaban 4 piezas; se han añadido sin dependencias nuevas (PowerShell, WinRT/WPF y C# compilado al vuelo, solo ASCII):
- `prepare_pdf.ps1`: PDF → PNG por página con `Windows.Data.Pdf`. Prueba: PDF de 2 páginas generado a mano; las páginas salen idénticas a sus imágenes (SSIM 0,999) y `-Pages` funciona. `RenderToStreamAsync` es una `IAsyncAction` y necesita la sobrecarga `AsTask(IAsyncAction)`, no la de `IAsyncOperation`.
- `crop.ps1`: recorte con fondo liso transparente. La alpha se calcula por distancia a la mediana del borde y se des-mezcla el color de fondo en los píxeles del borde, así que no queda halo (comprobado sobre azul marino y cian).
- `ocr.ps1` escribe `x.ocr.png` con las líneas numeradas (`n` en el JSON). En la diapositiva A deja ver que el OCR **no detecta casi ningún icono**: hay que medirlos a mano.
- `bench.ps1`: `-SelfTest` (9 comprobaciones con el ejemplo de la skill; todas PASS) y `-Dir` para un banco real. **El banco real va siempre fuera de la skill**, porque contiene imágenes reales. Dos ejecuciones seguidas dan cambio 0: el proceso es determinista.
- PowerShell 5.1: `New-Object Windows.Rect($a, $b, $c.Width + 6, ...)` parte `+ 6` en otro argumento. → Calcula las expresiones antes, en variables.
- PowerShell 5.1: `"... $spec: ..."` es un error de sintaxis (se lee como unidad `spec:`). → Usa `${spec}:`.
- `Export-Csv` con la configuración regional española escribe "0,91". → `history.csv` usa siempre la cultura invariante.

## 2026-11-16 · prueba de salida HTML con la misma spec (Opus)
- `build_html.ps1` + `html/deck.js`/`deck.css`: la spec se interpreta igual que en `build_from_spec.ps1` (margen 0, ajuste de línea solo con `wrap` o alineación ≠ izquierda, interlineado exacto, `radius` relativo al lado corto, sombra azul al 90 % de transparencia). Lienzo de 960×540, donde 1 px CSS = 1 pt.
- Diapositiva A en HTML: un solo archivo de **146 KB** (el fondo PNG pasa a JPEG q88). Frente al original da **SSIM 0,797 con 2 avisos**; el PPTX da 0,806 con los mismos 2. **HTML frente a PPTX: 0 avisos.** Los iconos SVG salen algo mayores en el navegador que en PowerPoint.
- `ejemplo_completo.json` (formas, flechas, tabla, viñetas, barras y anillo, 2 diapositivas) se ve bien en HTML. Los gráficos son SVG propio y no necesitan Excel.
- Las capturas de Edge sin ventana usan `--user-data-dir` temporal (nunca el perfil del usuario) y `--virtual-time-budget`. `Start-Process` no entrecomilla los argumentos: hay que hacerlo a mano si hay espacios.
- Sin probar todavía: la navegación con teclado, la edición (E) y la impresión (P) en un navegador real.

## 2026-11-16 - Renombrada a imagen-a-slide (Opus 5.5)
- La skill pasa de `imagen-a-pptx` a `imagen-a-slide`: el proceso (clasificar, OCR, fondo limpio, recortes, spec, comparar, banco) es común y la salida se elige con el argumento `pptx` (por defecto) | `html` | `ambos`. `build_html.ps1` deja de ser experimental.
- Validación tras el cambio: `bench.ps1 -SelfTest` 9/9 PASS; `bench.ps1 -Dir` con cambio 0 en los 4 casos; la diapositiva A en HTML con los mismos 2 avisos que en PPTX.

## 2026-11-16 · Gráficos nativos: AddChart2 E_FAIL (Opus 5.5)
- Síntoma: tras una actualización de Office (build 16.0.20527), todo gráfico fallaba con E_FAIL. Fallaba también con `AddChart`, sin `NewLayout`, e incluso con 1 serie de 2 valores.
- Causa: la presentación se creaba sin ventana (`Presentations.Add(0)`), y esta versión ya no inserta gráficos así. Arreglo: si la spec tiene `chart`, el motor abre la presentación con ventana, minimizada. Sin gráficos, sigue sin ventana.
- Segundo fallo, silencioso: con Excel en frío, el primer gráfico se quedó con los datos de ejemplo de Excel (Category 1, Series 1, 4,3…) sin dar error. Arreglo: el motor relee los valores de la serie 1 y reintenta hasta 3 veces; si siguen sin coincidir, falla con un mensaje claro.
- Efecto secundario aceptado: si PowerPoint no estaba abierto antes, al terminar queda una ventana de PowerPoint vacía y procesos de Excel incrustados (modo automatización). No se cierran, por la regla de seguridad: los cierra el usuario.
- Además, la carpeta temporal `spec_*` ahora se borra también cuando el build falla, y en ese caso también se imprime la línea antes/después.
- Control (misma sesión, mismo Office): una copia del motor forzada a crear la presentación sin ventana falla 2 de 2 veces; con ventana funciona. No hay documentación ni issue público de Microsoft sobre ello. Otros proyectos públicos de automatización de PowerPoint ven gráficos con Excel inestables (se pierden datos, Excel se cuelga, se abre un Excel por gráfico); su salida es crear el gráfico sin Excel, a partir de un pptx con el gráfico ya hecho o pegando el paquete de gráfico desde el portapapeles. Alternativa futura si la ventana molesta: generar el XML del gráfico (OpenXML) sin Excel.

## 2026-11-16 · Skill neutralizada para publicar (Opus 5.5)
- Antes de publicar se quitaron de la propia skill todos los datos reales: nombres de cliente y de empresas concretas, sus logos, cifras, títulos y textos de las diapositivas reales, rutas y nombres de usuario. Los ejemplos usan `@logos/ejemplo_cliente.svg` y textos y cifras genéricos. Los casos reales se citan como A-D.
- `package_plugin.ps1` prepara el paquete en `%TEMP%`, porque una carpeta de salida profunda supera el límite de 260 caracteres de Windows. Solo copia los logos permitidos, cambia las rutas absolutas de los agentes por `${CLAUDE_PLUGIN_ROOT}` y falla si encuentra términos de `forbid.txt` (guárdalo fuera de la skill), el nombre de usuario o rutas `C:\Users\…`.

## 2026-11-17 · Perfiles de cliente y composición de skills (Opus 5.5)
- Mantener dos copias (una "con cliente" y otra "limpia para publicar") hace que diverjan. → Una sola skill genérica, sin datos de cliente, y una **skill local por cliente** que la invoca y le pasa un `perfil.json` (logos + tema). La genérica no sabe nada del cliente.
- Motores: `"profile"` en la spec, o la variable `IMAGEN_A_SLIDE_PROFILE`. `@logos/x` se busca primero en el perfil y después en la skill. El tema del perfil rellena lo que la spec no fija. Sin perfil, un logo que no existe falla con un mensaje claro.
- Validación: autoprueba 9/9; spec de prueba con perfil en PPTX y HTML idénticos; error claro sin perfil; banco real con **cambio 0** en los 4 casos tras la migración.
- `package_plugin.ps1`: el escáner buscaba subcadenas, así que una sigla corta del cliente saltaba dentro de una palabra normal del código. → Ahora el término tiene que empezar palabra (puede ser un prefijo). Control positivo: un archivo sembrado con dos términos se bloquea.
- Al escribir el comentario de esa misma corrección se colaron dos términos reales del cliente como ejemplo, y el escáner los paró. → **Nunca uses datos reales como ejemplo en la skill genérica**, ni siquiera en comentarios; ejecuta el escáner después de cada cambio.
