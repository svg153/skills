---
name: cost-optimizer
description: "Trigger: cost-tips, chronicle cost, optimizar costos, ahorrar tokens, revisar costos, gasto tokens. Analiza uso de tokens y sesiones para dar consejos directos de ahorro en español con TLDR."
license: Apache-2.0
metadata:
  author: svg153
  version: "1.0"
---

## Activation Contract

Activa cuando:
- El usuario pide cost-tips, optimizar costos, revisar gasto de tokens
- Se ejecuta `/chronicle cost-tips` o similar
- Se necesita evaluar si una skill o automatización puede reducir costos

No actives cuando:
- El usuario solo pregunta precio de un modelo
- No hay datos de uso disponibles

## Hard Rules

- Responde SIEMPRE en español.
- Sé extremadamente directo: sin preámbulos, sin repetir lo que el usuario dijo.
- Incluye un **TLDR** de 1-3 líneas al final de cada respuesta.
- Máximo 3 recomendaciones rankeadas; no rellenes para llegar a 3.
- Cada recomendación: Contexto (1 oración) → Problema (1 oración con evidencia) → Acción (1 oración con comando concreto) → Impacto (Alto/Medio/Bajo).
- No inventes precisión: di "señal proxy" cuando no hay datos exactos de uso.
- No recomiendes `/model` a un modelo más barato a menos que la mezcla de modelos lo justifique con evidencia.
- Evalúa si crear o modificar una skill/automatización resolvería el problema de raíz.

## Decision Gates

| Señal detectada | Acción |
|----------------|--------|
| Sesión mezcla tareas no relacionadas | Recomienda `/new` entre tareas |
| Muchas llamadas a herramientas (proxy) | Recomienda acotar el working set |
| Mensajes grandes pegados | Recomienda recortar antes de pegar |
| Crecimiento de contexto tardío | Recomienda `/compact` o nueva sesión |
| Modelo caro en tarea mecánica | Recomienda `/model` solo con evidencia |
| Patrón repetido en múltiples sesiones | Evalúa crear skill o automatización |

## Execution Steps

1. Recibe el precomputed cost profile (no consultes historial directamente).
2. Clasifica la precisión de la evidencia: exacta, proxy, o mixta.
3. Identifica las 3 señales de mayor impacto usando la tabla de Decision Gates.
4. Redacta recomendaciones rankeadas con la forma: Contexto → Problema → Acción → Impacto.
5. Redacta "Datos de tus sesiones" con bullets bold-label.
6. Redacta "Limitaciones del perfil" solo si hay limitación material.
7. Añade **TLDR** final de 1-3 líneas.
8. Evalúa: ¿una skill o automatización evitaría este problema? Si sí, propón la acción concreta.

## Output Contract

Respuesta mínima:
- Recomendaciones rankeadas (máx 3)
- Datos de tus sesiones (5-8 bullets)
- Limitaciones (solo si aplica)
- **TLDR** (1-3 líneas)
- Evaluación de skill/automatización (si aplica)

## References

- Perfil de costos precomputado: se recibe como input, no se consulta.
- Repo de skills: svg153/skills — para crear/modificar skills de optimización.
