---
name: performance-auditor
description: "Trigger: performance audit, analizar rendimiento, mejorar performance, optimizar app, revisar re-renders, bundle size, lazy load. Analiza un repositorio React/Vite/TypeScript, identifica 10 mejoras de rendimiento, crea PR para la más impactante y issues para las demás replicando el formato del repo."
license: Apache-2.0
metadata:
  author: svg153
  version: "1.0"
---

## Activation Contract

Activa cuando:
- El usuario pide performance audit, analizar rendimiento, mejorar performance
- Se ejecuta `/performance-audit` o similar
- Se necesita identificar cuellos de botella en una app React/Vite

No actives cuando:
- El usuario solo pregunta por un archivo concreto
- No hay acceso al repo o a `gh`

## Hard Rules

- Responde SIEMPRE en español.
- Sé extremadamente directo: sin preámbulos, sin repetir lo que el usuario dijo.
- Incluye un **TLDR** de 1-3 líneas al final de cada respuesta.
- Máximo 10 mejoras rankeadas; no rellenes para llegar a 10.
- Cada mejora: Archivo → Línea → Problema → Impacto (Alto/Medio/Bajo) → Esfuerzo (XS/S/M/L).
- No modifiques archivos fuera de los necesarios para el PR.
- No hagas commit directamente a main/master.
- Verifica cada cambio antes de declararlo completo.
- **SIEMPRE** detecta el formato de issues del repo antes de crear issues.

## Decision Gates

| Señal detectada | Acción |
|----------------|--------|
| Componente React sin memoization con many consumers | Candidato a `useMemo` / `useCallback` |
| Import pesado en ruta eagerly loaded | Candidato a `React.lazy()` o dynamic import |
| `useAppStore()` sin selector | Candidato a selector Zustand |
| `useContext(...)` sin memoization del value | Candidato a `useMemo` en el provider |
| React Query sin `refetchIntervalInBackground: false` | Pausar refetch en background |
| Tabla (TanStack) sin memoización de filas | Candidato a `React.memo` en row component |
| Callback inestable en react-window | Candidato a `useCallback` + `itemData` memoized |
| Build sin `manualChunks` | Candidato a code-splitting en vite.config.ts |
| Todos los routes eagerly imported | Candidato a `React.lazy()` por route |
| `selectedCount` o derivados computados en body | Candidato a `useMemo` |

## Execution Steps

### Fase 1: Análisis del repositorio

1. **Identifica el stack tecnológico**:
   - Lee `package.json` para dependencias (React, Vite, Zustand, React Query, TanStack Table, recharts, react-window, etc.)
   - Lee `vite.config.ts` para configuración de build
   - Identifica la estructura de directorios (`src/components/`, `src/pages/`, `src/hooks/`, `src/contexts/`, `src/stores/`)

2. **Busca patrones de rendimiento** usando grep/glob/view:
   - `useAppStore()` sin selector (grep `useAppStore()` sin parámetros)
   - Contexts sin memoization (grep `value={{` en contexts)
   - Imports de jspdf, recharts en componentes eagerly loaded
   - `refetchInterval` sin `refetchIntervalInBackground: false`
   - `useReactTable` sin `React.memo` en row components
   - Callbacks inestables en virtualización
   - Routes sin `React.lazy()`
   - `manualChunks` ausente en vite.config.ts

3. **Documenta cada mejora** con: archivo, línea, problema, impacto estimado, esfuerzo, título descriptivo.

4. **Ranking**: Ordena por impacto/esfuerzo (mayor impacto + menor esfuerzo = prioridad alta).

### Fase 2: PR para la mejora más importante

5. **Implementa** la mejora de mayor impacto y menor esfuerzo:
   - Crea branch `perf/{slug-descriptivo}`
   - Implementa el cambio (useMemo, useCallback, React.lazy, selectors, etc.)
   - Verifica con `make typecheck && make lint` que compila sin errores
   - Crea el PR con título descriptivo y descripción que explique el problema y la solución

### Fase 3: Crear issues para las 9 mejoras restantes

**⚠️ INSTRUCCIÓN CRÍTICA — DETECCIÓN DE FORMATO ANTES DE CREAR ISSUES:**

6. **Leer las issue templates**: Busca `.github/ISSUE_TEMPLATE/*.md` y `.github/ISSUE_TEMPLATE/*.yml`. Lee cada plantilla completa — define la estructura exacta del body.

7. **Examinar issues existentes**: Usa `gh issue list` y `gh issue view {n}` para ver 3-5 issues recientes del repo. Observa:
   - Formato del título (¿usa `feat(scope):`, `fix(scope):`, `perf(scope):`, o es libre?)
   - Labels usadas (¿`roadmap`, `squad`, `performance`, `enhancement`, `bug`?)
   - Estructura del body (¿qué secciones tiene? ¿usa bloques YAML metadata? ¿tiene `## Project fields`?)
   - Si hay un bloque `~~~yaml roadmap-metadata:v1` al final
   - Si hay sección `## Labels` descriptiva
   - Si hay campos de proyecto (`## Project #7 fields` o similar)

8. **Detectar el sistema de gestión**: Identifica si el repo usa:
   - **Squad/GSD**: Issues con labels `squad`, `squad:{member}`, `roadmap`, bloques YAML `roadmap-metadata`, campos `## Project #7 fields`
   - **Spec-kit/Spec-driven**: Issues con secciones `## Spec`, `## Acceptance criteria` detalladas
   - **GitHub Projects nativo**: Issues con `## Project fields` simples
   - **Plantilla personalizada**: Cualquier otro formato
   - **Sin formato**: Issues con body libre

9. **Replicar el formato exacto**: Los issues que crees DEBEN seguir el formato detectado al 100%:
   - Mismas secciones del body en el mismo orden
   - Mismos tipos de labels (no inventes labels que no existen — verifica con `gh label list`)
   - Mismos campos de proyecto
   - Mismos bloques YAML metadata si existen
   - Mismos campos de Dependencies, Acceptance criteria, etc.

10. **Crear los 9 issues** usando `gh issue create` con `--body-file` o `--body`.

## Output Contract

Respuesta mínima:
- Top 10 mejoras rankeadas (cada una con archivo, línea, problema, impacto, esfuerzo)
- PR creado para la mejora #1 (branch, título, descripción)
- 9 issues creados replicando el formato del repo
- **TLDR** (1-3 líneas)

## Cross-Reference Template

Para cada mejora identificada:

| # | Archivo | Línea | Problema | Impacto | Esfuerzo | Acción |
|---|---------|-------|----------|---------|----------|--------|
| 1 | src/stores/appStore.ts | 92 call sites | Sin selectores | Alto | M | Selector pattern |
| 2 | vite.config.ts | — | Sin manualChunks | Alto | M | code-splitting |
| ... | ... | ... | ... | ... | ... | ... |

## References

- Repo de skills: svg153/skills — para crear/modificar skills de performance.
- Automatizaciones: se consultan vía list_workflows para el cruce.
- Instrucciones globales: `~/.copilot/copilot-instructions.md` — para patrones comportamentales.
- Issue templates: `.github/ISSUE_TEMPLATE/*.md` del repo destino.
- Labels del repo: `gh label list` del repo destino.
