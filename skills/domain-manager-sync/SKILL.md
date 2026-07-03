---
name: skill-sync
description: 'Auto-sync all skills from svg153/skills GitHub repo. Maintains symlinks from /hermes-home/skills/ to the canonical repo. Before any task, verify symlinks are current by pulling latest from repo. Trigger: any skill management, skill updates, or when unsure if a skill is up to date.'
license: MIT
metadata:
  author: svg153
  version: "1.0"
---

# Skill Sync — Sincronización Genérica de Skills

Mantiene todas las skills del repositorio `svg153/skills` sincronizadas con la carpeta de Hermes.

## Arquitectura

```
svg153/skills (GitHub)  ←  CANONICAL (única fuente de verdad)
        ↑
        │  symlink
        ↓
/hermes-home/skills/   ←  Hermes lee desde aquí
```

- **Repositorio**: `github.com/svg153/skills` → `skills/<nombre>/`
- **Symlinks**: `/hermes-home/skills/<nombre>` → `/root/workspace/svg153-skills/skills/<nombre>`
- **Seguridad**: `.gitignore` excluye `*.env`, `*.key`, `hosts.yml`
- **SKILL.md es público**: solo instrucciones, sin credenciales

## Procedimiento de Sincronización

Antes de cualquier tarea que use skills del repositorio:

```bash
cd /root/workspace/svg153-skills && git pull origin main
```

Verificar que los symlinks están intactos:

```bash
# Listar todos los symlinks
ls -la /hermes-home/skills/ | grep "^l"

# Verificar que cada skill del repo tiene su symlink
for skill in $(ls /root/workspace/svg153-skills/skills/); do
    if [ ! -L "/hermes-home/skills/$skill" ]; then
        echo "MISSING: $skill"
    fi
done
```

## Añadir una Nueva Skill al Repo

1. Crear carpeta: `skills/<nombre-skill>/`
2. Crear `SKILL.md` con frontmatter (name, description, license, metadata)
3. Añadir scripts/activos en `scripts/` si los hay
4. Commit y push:
   ```bash
   cd /root/workspace/svg153-skills
   git add skills/<nombre-skill>/
   git commit -m "feat: add <name> skill"
   git push origin main
   ```
5. Crear symlink:
   ```bash
   ln -sf /root/workspace/svg153-skills/skills/<nombre-skill> /hermes-home/skills/<nombre-skill>
   ```

## Actualizar una Skill Existente

1. Editar `SKILL.md` y/o `scripts/` en el repo
2. Commit y push
3. Hermes lee automáticamente el nuevo contenido (symlink + skill_view)

## Eliminar una Skill

1. Eliminar carpeta del repo
2. Commit y push
3. Eliminar symlink: `rm /hermes-home/skills/<nombre>`

## Seguridad

- **NUNCA** hardcodear API keys en SKILL.md o scripts
- **NUNCA** commit de credenciales (`.gitignore` excluye `*.env`, `*.key`, `hosts.yml`)
- **SKILL.md es público** — solo instrucciones no sensibles
- Usar `***` como placeholder para credenciales
- Referencias a GitHub Secrets: `${{ secrets.VAR }}`

## Skills Actuales en el Repo

```
branch-pr, chained-pr, cognitive-doc-design, comment-writer,
domain-manager, gentle-ai-ecosystem, go-testing, issue-creation,
judgment-day, sdd-apply, sdd-archive, sdd-design, sdd-explore,
sdd-init, sdd-onboard, sdd-propose, sdd-spec, sdd-tasks,
sdd-verify, skill-creator, skill-improver, skill-publish,
skill-registry, work-unit-commits
```

## Estructura del Repo

```
svg153-skills/
├── .gitignore          # Excluye: *.env, *.key, hosts.yml, __pycache__
├── CONTRIBUTING.md
├── README.md
├── skills/
│   ├── <skill-name>/
│   │   ├── SKILL.md    # Instrucciones públicas (sin secretos)
│   │   └── scripts/    # Scripts auxiliares (sin secretos)
│   └── ...
└── scripts/
    ├── check-updates.sh
    └── migrate-skills.sh
```
