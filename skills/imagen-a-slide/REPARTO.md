# Reparto de tareas entre modelos

Delegar compensa cuando la tarea **genera mucha salida mecánica** (specs y coordenadas), **se puede comprobar de forma objetiva** (render y comparación) y **hay varias en paralelo**. No compensa cuando preparar el encargo cuesta más que hacer la tarea: el subagente tiene que leer la skill y la imagen, unos 15-20k tokens de arranque.

| Tarea | Quién | ¿En paralelo? | Por qué |
|---|---|---|---|
| Clasificar native/hybrid, tema, rejilla, qué es logo | Opus (principal) | – | Es criterio de diseño; un error aquí lo arrastra todo |
| OCR, limpieza de fondo, build | Script (cualquiera lo lanza) | Sí | Es determinista |
| Spec JSON: medir, transcribir, maquetar | **Sonnet** `slide-spec-writer` | Sí, 1 por diapositiva | Mecánico y largo; el OCR le da la geometría y los tamaños |
| Iconos SVG sencillos | Sonnet, dentro de la spec | – | Formas simples; un error se ve enseguida en el render |
| Ilustración SVG compleja | Opus o subagente Opus | Sí | Los modelos pequeños componen peor |
| Cajas para `clean_bg` | Sonnet propone, Opus mira el PNG | Sí | Fácil de verificar |
| QA visual fuente vs render | **Haiku** `slide-qa` | Sí, 1 por render | Comparar y listar es barato; Haiku solo informa, no decide |
| Corrección final y entrega | Opus | – | Juicio de calidad |
| LEARNINGS / reglas nuevas | Opus | – | Destilar reglas a partir de los fallos |

## Cuándo NO delegar
- Una diapositiva corta o un retoque (mover 10 px, cambiar un color): se edita la spec y se reconstruye.
- Lo que dependa del contexto de la conversación y no se pueda escribir en el brief.

## Plantilla de brief para `slide-spec-writer`
```
Skill: <ruta absoluta de la carpeta de la skill (${CLAUDE_SKILL_DIR})>
Imagen fuente: <ruta>           OCR: <ruta .ocr.json> (si ya lo has lanzado)
Salida: <carpeta>\<Nombre>.json  (output <Nombre>.pptx, png <Nombre>.png)
Formato final: pptx | html | ambos  (con html, construye y compara con build_html.ps1 -Spec <json> -Out <Nombre>.html -> <Nombre>_html.png; el HTML de todo el deck lo monta el modelo principal al final)
Estrategia: native | hybrid (fondo: <ruta del fondo limpio>)
NO incluir (ya está en el fondo): <lista>
Logos: @logos/<archivo>.svg (los que haya en assets/logos de tu copia) en <posición aproximada>
Tema/rejilla: Segoe UI; título <x,y,size>; colores <…>
Notas: <datos dudosos, textos ilegibles, qué va en cursiva…>
```

## Plantilla de brief para `slide-qa`
```
Fuente: <ruta imagen original>
Render: <ruta png>
Elementos que deben faltar a propósito: <p. ej. "la ilustración es una aproximación redibujada">
```
