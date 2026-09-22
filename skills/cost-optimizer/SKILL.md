---
name: cost-optimizer
description: "Trigger: cost-tips, chronicle cost, optimizar costos, ahorrar tokens, revisar costos, gasto tokens. Analiza uso de tokens, cruza con skills/automatizaciones activas, detecta ineficiencias y propone mejoras o skills nuevas."
license: Apache-2.0
metadata:
  author: svg153
  version: "2.0"
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

## Decision Gates

| Señal detectada | Acción |
|----------------|--------|
| Sesión mezcla tareas no relacionadas | Recomienda `/new` entre tareas |
| Muchas llamadas a herramientas (proxy) | Recomienda acotar el working set |
| Mensajes grandes pegados | Recomienda recortar antes de pegar |
| Crecimiento de contexto tardío | Recomienda `/compact` o nueva sesión |
| Modelo caro en tarea mecánica | Recomienda `/model` solo con evidencia |
| Patrón repetido en múltiples sesiones | Evalúa crear skill o automatización |
| Skill/automatización causa gasto repetido | Propón modificar la skill o crear nueva de mejora |

## Execution Steps

### Fase 1: Análisis de costos
1. Recibe el precomputed cost profile (no consultes historial directamente).
2. Clasifica la precisión de la evidencia: exacta, proxy, o mixta.
3. Identifica las 3 señales de mayor impacto usando la tabla de Decision Gates.

### Fase 2: Cruce con skills y automatizaciones activas
4. Lista las automatizaciones activas (workflows) y sus configuraciones.
5. Para cada automatización, evalúa:
   - ¿Cuánto gasta en tokens por ejecución?
   - ¿Su prompt es eficiente o redundante?
   - ¿Usa el modelo correcto para su tarea?
   - ¿Se ejecuta con la frecuencia adecuada?
6. Consulta las skills instaladas en el repo svg153/skills.
7. Para cada skill relevante, evalúa:
   - ¿Su description es clara y triggera correctamente?
   - ¿Sus Hard Rules son suficientemente específicas?
   - ¿Hay overlap con otras skills que cause trabajo duplicado?
   - ¿Puede reemplazar pasos manuales del usuario?

### Fase 3: Diagnóstico y propuestas
8. Clasifica los hallazgos en:
   - **Optimizar skill existente**: la skill tiene un patrón ineficiente detectable en el perfil de costos.
   - **Crear skill de mejora**: hay un patrón repetido sin skill que lo resuelva.
   - **Modificar automatización**: el prompt o frecuencia de un workflow causa gasto innecesario.
   - **Proceso de mejora**: proponer una skill nueva que prevenga que el mismo problema se repita.
9. Para cada propuesta, di: qué skill/automatización, en qué repo, qué cambio concreto.

### Fase 4: Respuesta
10. Redacta recomendaciones rankeadas (máx 3) con la forma: Contexto → Problema → Acción → Impacto.
11. Redacta "Cruce con skills y automatizaciones" con la tabla de diagnóstico.
12. Redacta "Datos de tus sesiones" con bullets bold-label.
13. Redacta "Limitaciones del perfil" solo si hay limitación material.
14. Añade **TLDR** final de 1-3 líneas.

## Output Contract

Respuesta mínima:
- Recomendaciones rankeadas (máx 3)
- Cruce con skills y automatizaciones (tabla de diagnóstico)
- Datos de tus sesiones (5-8 bullets)
- Limitaciones (solo si aplica)
- **TLDR** (1-3 líneas)

## Cross-Reference Template

Para cada automatización/skill evaluada:

| Componente | Tipo | Gasto estimado | Problema detectado | Propuesta |
|-----------|------|---------------|-------------------|-----------|
| Cost tips | workflow | X tokens/ejecución | ... | ... |
| skill-xyz | skill | triggera frecuente | ... | ... |

Si no hay problemas: "Todas las automatizaciones y skills evaluadas son eficientes."

## References

- Perfil de costos precomputado: se recibe como input, no se consulta.
- Repo de skills: svg153/skills — para crear/modificar skills de optimización.
- Automatizaciones: se consultan vía list_workflows para el cruce.
