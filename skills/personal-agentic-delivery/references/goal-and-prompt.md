# Goal and prompt for personal roadmap delivery

Use the following as the reusable starting objective. Replace the repository path or roadmap name only when needed.

Respetar siempre las instrucciones del host/repositorio, sus gates reales y la configuración vigente de TDD/RDD. Este objetivo no activa SDD ni revisiones, y no autoriza operaciones remotas por sí solo.

## Goal

Continuar el roadmap canónico del proyecto de forma autónoma hasta completar todos los elementos accionables. Trabaja siguiendo la skill personal-agentic-delivery, agrupando en una misma PR los cambios relacionados por concepto para reducir tiempo, tokens y overhead, sin mezclar funcionalidades independientes.

Antes de tocar código, recupera el estado de la rama, cambios sin commitear, PRs abiertas, issues y dependencias. Si existe trabajo a medias, consérvalo y retómalo en una rama adecuada; no lo dupliques ni sobrescribas cambios del usuario.

Selecciona el siguiente issue por dependencias, prioridad, valor y estado real, no por número. Si falta trabajo necesario, crea la issue con contexto, criterios de aceptación, dependencias y el encabezado exacto `## Decision record — CODEX`. Actualiza el padre directo del roadmap.

Implementa cada unidad de concepto en una PR coherente. Puedes incluir contrato, persistencia, wiring, tests y refactors locales necesarios en la misma PR. Mantén commits lineales y revisables. Separa seguridad, migraciones, integraciones externas y cambios arquitectónicos cuando necesiten rollback o decisión independiente.

Valida primero de forma focalizada y después con los checks relevantes del repositorio. Si un fallo es tuyo, arréglalo. Si el mismo fallo externo se repite dos veces, documenta la evidencia y la decisión bajo `## Decision record — CODEX`, y continúa si tests, typecheck, build y seguridad están correctos. No esperes indefinidamente a revisiones opcionales, agentes agotados, runners sin minutos o despliegues limitados por cuota.

Publica o fusiona sólo si el usuario ya autorizó esa operación y destino y los gates del repositorio lo permiten. Si falta autorización, entrega el cambio local o la PR y detente en ese límite. Después de una fusión autorizada, verifica el commit, cierra la issue, sincroniza el roadmap y continúa con el siguiente issue dentro del alcance autorizado.

## Prompt corto

Usa `$personal-agentic-delivery` y continúa el roadmap del proyecto de forma autónoma. Retoma primero cualquier trabajo a medias, agrupa cambios relacionados por concepto en PRs revisables con commits lineales, documenta toda decisión con `## Decision record — CODEX`, gestiona CI según la política indicada y sigue con el siguiente issue hasta agotar el backlog accionable dentro del alcance autorizado, sin publicar ni fusionar sin autorización.

## Autorización remota opcional (añadir sólo si se desea)

Autorizo en `<owner/repo>` la creación/actualización de issues, el push de ramas de trabajo y la creación y fusión de PRs del roadmap acordado, respetando los gates reales. No incluye releases, despliegues ni cambios destructivos. No pidas aprobación por cada PR dentro de este alcance; consulta antes de ampliarlo.
