---
name: cost-optimizer-lite
description: "Trigger: cost-tips, chronicle cost, optimizar costos, ahorrar tokens, gasto tokens. Versión ligera de cost-optimizer para el workflow Cost tips: analiza gasto de sesiones, cruza con workflows/skills activos, rankea máximo 3 recomendaciones con triaje de ubicación. No duplica las reglas que el prompt del workflow ya define."
license: Apache-2.0
metadata:
  author: svg153
  version: "1.0"
---

## Activation Contract

Activa cuando:
- El workflow "Cost tips" ejecuta `/chronicle cost-tips` (semanal, lunes 9:00)
- El usuario pide cost-tips manualmente

No actives cuando:
- Solo preguntan el precio de un modelo
- No hay datos de uso disponibles

## Relación con cost-optimizer

El prompt del workflow "Cost tips" ya es la especificación tipificada de la salida
(idioma, tono, máximo 3 recomendaciones, secciones obligatorias, TLDR, señales proxy,
regla de /model). **No repitas esas reglas aquí.** Esta skill aporta solo lo que el
prompt no contiene: decision gates, triaje de ubicación, presupuesto de datos y fases.

La versión completa (`skills/cost-optimizer/SKILL.md`) se mantiene para uso manual
interactivo cuando se quiera el contrato de salida ampliado.

## Presupuesto de datos

Basado en la ejecución del 2026-09-28 (15+ llamadas de recolección, listing de 21KB,
6 consultas SQL con 1 error). Límites duros por ejecución:

- **1** `list_workflows` (suficiente: toda la config de automatizaciones).
- **Máx 5** consultas `session_store_sql`: agregados con `GROUP BY` (modelo, sesión),
  una sola ventana temporal (7 días), `LIMIT` siempre. Si una consulta falla por
  columna, corrige la columna; no replanifiques el resto.
- **Directorios GitHub**: solo `fields=["name","path"]`. Nunca listing completo
  (la ejecución 2026-09-28 devolvió 21KB y se traspasó a fichero temporal).
- **SKILL.md**: solo de skills con overlap real de costos (las que invoca un workflow
  activo). No descargues skills no relacionadas.
- Si `session_usage.cost = 0` en toda la BD, di "señal proxy" y continúa; no busques
  fuentes alternativas de facturación.

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

## Triage de Ubicación

Cada recomendación DEBE incluir dónde se implementa el fix:

| Tipo de señal | Criterio | Ubicación destino |
|---|---|---|
| Patrón comportamental universal | Regla de pocas líneas "si ves X, haz Y" | `~/.copilot/copilot-instructions.md` |
| Configuración de automatización | Frecuencia, modelo, prompt de un workflow | `save_workflow` (modificar workflow) |
| Patrón con activación/gates/output | Necesita trigger, fases y output contract | `svg153/skills/skills/<nueva>/SKILL.md` |
| Convención de repo concreto | Norma específica de un proyecto | `<repo>/.github/copilot-instructions.md` |
| Entorno cloud agent | Dependencias, runners, firewalls | `<repo>/.github/workflows/copilot-setup-steps.yml` |

**Regla de oro**: no todo es skill. Regla de una línea → instrucción. Workflow mal
configurado → `save_workflow`. Skill nueva solo si hay trigger, gates y output contract.

## Execution Steps

### Fase 1: Datos (bajo presupuesto)
1. `list_workflows` + máx 5 agregados SQL (sesión, modelo, 7 días).
2. Clasifica la evidencia: exacta, proxy o mixta.
3. Identifica las señales de mayor impacto con los Decision Gates.

### Fase 2: Cruce con skills y automatizaciones
4. Para cada workflow activo: gasto por ejecución, eficiencia del prompt, modelo,
   frecuencia. (Una sola pasada de `list_workflows` ya lo cubre.)
5. Lee SKILL.md solo de las skills que invoca un workflow activo o tengan overlap
   de costos. Evalúa: triggers, hard rules, overlap que cause trabajo duplicado.

### Fase 3: Respuesta
6. Máx 3 recomendaciones rankeadas: Contexto → Problema (evidencia numérica) →
   **Ubicación** → Acción (comando concreto) → Impacto.
7. Tabla de cruce con el Cross-Reference Template de cost-optimizer (Componente,
   Tipo, Gasto estimado, Problema, Propuesta, Ubicación del fix).
8. "Datos de tus sesiones" (5-8 bullets con bold-label).
9. "Limitaciones del perfil" solo si hay limitación material.
10. **TLDR** de 1-3 líneas.

## Output Contract

- Recomendaciones rankeadas (máx 3) con Ubicación explícita
- Cruce con skills y automatizaciones (tabla)
- Datos de tus sesiones (bullets)
- Limitaciones (solo si aplica)
- **TLDR** (1-3 líneas)

## References

- Versión completa: `skills/cost-optimizer/SKILL.md`
- Workflow disparador: "Cost tips" (Automations view, lunes 9:00, host local)
- Repo de skills: svg153/skills
- Instrucciones globales: `~/.copilot/copilot-instructions.md`
