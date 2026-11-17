# imagen-a-slide

Convierte imágenes de diapositivas (PNG, JPG, WEBP, PDF o PPTX "planos" exportados como imagen) en diapositivas **editables** con el mismo diseño, en dos salidas que comparten todo el proceso:

- **pptx** (por defecto): PowerPoint con texto, formas, tablas, gráficos y logos como objetos nativos. Las fotos pasan a un fondo limpio, sin texto, con los elementos encima.
- **html**: **un único archivo `.html`** autocontenido (visor, datos e imágenes dentro, sin red). Se envía y se abre en cualquier navegador. Teclas: flechas, F pantalla completa, N notas, E editar textos, P imprimir/PDF.

## Requisitos
- Windows con **PowerPoint de escritorio** para la salida pptx (y Excel, solo para gráficos nativos). La salida html solo usa Edge para la captura de control.
- Claude Code: CLI, app de escritorio (pestaña Code) o VS Code.
- Opcional: Podman o Python con numpy/opencv/scikit-image, para la comparación numérica (`compare.ps1`). Sin ellos, ese paso se salta.
- No envía nada a servicios externos. El OCR es el que trae Windows.

## Qué incluye
| Componente | Qué hace |
|---|---|
| Skill `imagen-a-slide` | Procedimiento completo: clasificar (native/hybrid), medir con OCR, construir, comparar, corregir y aprender |
| `scripts/build_from_spec.ps1` | Motor pptx: spec JSON → `.pptx` + PNG de control |
| `scripts/build_html.ps1` + `html/` | Motor html: la misma spec → un solo `.html` + PNG de control |
| `scripts/ocr.ps1` | OCR local: caja de cada línea y tamaño de letra calculado por anchura, con imagen de control |
| `scripts/clean_bg.ps1` / `crop.ps1` | Fondo limpio sin textos; recorte de piezas (fotos, logos) como imagen movible |
| `scripts/prepare_pptx.ps1` / `prepare_pdf.ps1` | PPTX de imágenes o PDF → una PNG por diapositiva + notas |
| `scripts/compare.ps1` | Comparación numérica fuente vs render por elemento (desplazamiento, tamaño de letra, desbordes) |
| `scripts/bench.ps1` | Banco de pruebas: `-SelfTest` de regresión sin datos reales |
| `assets/logos/` | Solo un logo ficticio de ejemplo (`ejemplo_cliente.svg`); añade los logos reales solo en tu copia local |
| Agente `slide-spec-writer` (Sonnet) | Escribe y construye la spec de una diapositiva; uno por diapositiva, en paralelo |
| Agente `slide-qa` (Haiku) | QA visual de solo lectura: compara el render con el original |

## Uso
Pásale a Claude una o varias imágenes y pide, por ejemplo, *"hazme un pptx editable de esta diapositiva"* o *"hazme un HTML de esta diapositiva para enviarlo"*. También: `/imagen-a-slide:imagen-a-slide html <imagen>` (salida `pptx`, `html` o `ambos`).

## Seguridad con tu PowerPoint
PowerPoint solo admite una instancia: los scripts se conectan a la tuya. Nunca cierran PowerPoint ni Excel; solo cierran lo que abren ellos e informan de cuántas presentaciones tenías abiertas antes y después. Si la spec tiene gráficos, PowerPoint necesita una ventana (se abre minimizada) y puede quedar abierto al terminar: ciérralo tú.

## Mejora continua
`skills/imagen-a-slide/LEARNINGS.md` recoge qué falló en cada uso y cómo se arregló. Si mejoras algo, sube la `version` de `.claude-plugin/plugin.json` para que tus compañeros reciban la actualización.
