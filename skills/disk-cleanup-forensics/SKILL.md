---
name: disk-cleanup-forensics
description: "Trigger: análisis de disco; dónde se fue el espacio; disco lleno / disk full; liberar espacio / reclaim; qué has borrado; crecimiento inexplicado del disco; forense VSS / instantáneas; VHDX de WSL/Docker; caches de dev tools regenerables. Metodología forense 100% read-only para localizar dónde crece el disco en una máquina dev (Windows + WSL + Docker + VHDX + VSS) y proponer limpieza segura por fases sin borrar nada hasta aprobación explícita."
license: "Apache-2.0"
metadata:
  author: "svg153"
  version: "1.0"
---

## Activation Contract

Activa cuando:
- El usuario pregunta dónde se fue el espacio / disco lleno / qué ha crecido
- Pide análisis de disco, limpieza o reclaim (incluso frases tipo "¿qué has borrado?")
- Hay sospecha de crecimiento inexplicado de una unidad
- Se menciona reclaimit, VHDX, VSS, pagefile o caches de dev tools

## Regla de oro (hard rule)

**FASE 0 = 100% READ-ONLY.** Nada de `Remove-Item`, `del`, `rm`, prune, purge, vacuum ni instalar herramientas. Los comandos de análisis JAMÁS escriben. Solo se borra con lista explícita confirmada por el usuario, elemento a elemento. Si el usuario pregunta "¿qué has borrado?", verificar primero que en toda la sesión no hubo ninguna escritura — re-mide todo y busca al responsable real en el log de eventos.

## Fase 0a — Medición Windows (read-only)

```powershell
# 1. Baseline de la unidad
Get-Volume -DriveLetter C | Select-Object @{n='FreeGB';e={[math]::Round($_.SizeRemaining/1GB,1)}}, @{n='TotalGB';e={[math]::Round($_.Size/1GB,1)}}

# 2. Archivos de sistema en raíz (pagefile/hiberfil/swapfile — Get-ChildItem NO los ve sin -Force)
Get-ChildItem C:\ -File -Force | Select-Object Name, @{n='GB';e={[math]::Round($_.Length/1GB,2)}}

# 3. Mapa top-level (robocopy /L = SOLO LISTA, cero escritura; mucho más rápido que Measure-Object recursivo)
function Get-DirSize([string]$path) {
  $out = & robocopy $path 'C:\__rcnull__' /L /S /BYTES /NFL /NDL /NJH /NP /R:0 /W:0 /XJ 2>$null
  ($out | Where-Object { $_ -match '^\s*Bytes\s*:' } | Select-Object -First 1) -match 'Bytes\s*:\s*(\d+)' | Out-Null
  [long]$Matches[1]
}
Get-ChildItem C:\ -Directory -Force | ForEach-Object { "{0,-30} {1,10:N1} GB" -f $_.Name, ((Get-DirSize $_.FullName)/1GB) }

# 4. Drill-down siempre top-down: cada nivel ordenado desc, y siguiente nivel de las 3-5 mayores
```

Trucos de medición:
- `robocopy /L /BYTES` es el caballo de batalla: lista sin copiar, multihilo, y la línea `Bytes:` del summary es el tamaño total de la ruta.
- `-Force` en Get-ChildItem SIEMPRE (muestra dotfolders y system files).
- Comparar SIEMPRE contra la medición anterior con tabla Δ — el crecimiento es el hallazgo, no el tamaño absoluto.
- Si el mapa suma ±2% de la unidad y aún faltan GB, hay capa invisible: VSS (System Volume Information), MFT, alternate streams.

## Fase 0b — Where disk ACTUALLY grows (top offenders, evidence-backed)

En orden de impacto típico en una máquina dev Windows de alto uso:

| # | Culprit | Tamaño típico | Cómo se verifica |
|---|---|---|---|
| 1 | **VHDX de WSL/Docker** (`%LocalAppData%\wsl\*\ext4.vhdx`, `%LocalAppData%\Docker\wsl\disk\docker_data.vhdx`) | 100-400 GB cada uno | Tamaño del fichero; el VHDX no encoge aunque borres dentro → recuperar = compactar (Optimize-VHD) tras `wsl --shutdown`, NO borrando ficheros |
| 2 | **Agent/CLI session-state** (`.copilot\session-state\<id>\`, codex, claude) | 1-20 GB por sesión larga | Drill-down de cada `<id>`; artifacts de workflows crecen sin límite |
| 3 | **Agent worktrees + clones de sesiones** (`.copilot\repos\<repo>-issue*`, `.copilot\copilot-worktrees`, `.codex\worktrees`) | +5-15 GB/mes si no se purgan | Los duplicados `<repo>-<pr/issue/prefijo>` son descendientes de sesiones cerradas |
| 4 | **pagefile.sys** | puede alcanzar el tamaño de la RAM completa | Windows lo auto-agranda con presión de memoria (WSL). Fix: tamaño manual fijo + reboot |
| 5 | **VSS / restore points** (System Volume Information) | 10-30 GB, invisible a du | SOLO con admin: `vssadmin list shadowstorage /for=C:` |
| 6 | **Docker build cache** | decenas de GB, cientos de entradas caducadas | `docker system df -v` |
| 7 | **Caches dev regenerables**: npm `_cacache`+`_npx`, uv, pip, ms-playwright, puppeteer, go pkg/mod, pnpm store, trivy, trunk, pre-commit | 0,5 a >10 GB c/u | Drill-down de `~/.cache` y dotfolders en WSL; `%LocalAppData%\npm-cache`, `%LocalAppData%\pnpm*`, `%LocalAppData%\uv`, `%LocalAppData%\ms-playwright` en Windows |
| 8 | **Caches de apps Electron**: `User Data\Cache` de apps de vídeo/edición, VS Code `CachedExtensionVSIXs` + `workspaceStorage`, Chrome `Service Worker` + `Code Cache` | 1-3 GB c/u | Drill-down por app |
| 9 | **Servidores remotos VS Code por versión** (`.vscode-server`, `.vscode-server-insiders`, `vscode-remote-wsl`) | decenas de GB de versiones viejas | Se re-descargan solas al conectar |

## Fase 0c — Forense VSS (cuando "desaparecen" GB o "aparecen" sin causa)

```powershell
# Los GB que nadie borró suelen ser instantáneas VSS. Solo el log de eventos lo prueba:
Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=(Get-Date).AddHours(-72)} -EA SilentlyContinue |
  Where-Object ProviderName -eq 'volsnap' |
  Select-Object TimeCreated, Id, Message
# ID 33: borrada la más antigua (límite) · ID 24: sin espacio para crecer · ID 35: TODAS anuladas
```
- volsnap ID 35 libera de golpe 10-30 GB sin que nadie toque nada → explica saltos inexplicables de espacio libre (típico durante horas sin uso aparente).
- Consecuencia tras ID 35: cero restore points; con el disco al límite Windows los purgará en cuantos se regeneren. Priorizar liberar espacio.

## Fase 0d — WSL + Docker interno (read-only)

```bash
wsl -e bash -c "df -h / && du -x -d2 -h / 2>/dev/null | sort -rh | head -40"
wsl -e bash -c "du -x -d1 -h ~ 2>/dev/null | sort -rh | head -30"
docker system df && docker system df -v   # el build cache suele ser el mayor
```
- Si una CLI de análisis no está instalada dentro, NO instalarla (sería escritura); usar `du` fino.
- Nunca `wsl --shutdown` sin avisar: mata sesiones activas del usuario.

## ORDER OF OPERATIONS para limpieza futura (solo con aprobación explícita por fase)

1. Limpieza interna (caches, node_modules, session-state muertos, docker prune con lista revisada antes)
2. `wsl --shutdown` + cerrar Docker Desktop
3. Compactar VHDX: `Optimize-VHD -Path <vhdx> -Mode Full` (consola admin) o `wsl --manage <distro> --set-sparse true`
4. Pagefile de tamaño manual fijo + reboot (recupera decenas de GB si estaba en modo automático)
5. Verificación: `Get-Volume` por fase, registrar Δ en el informe

## NO TOCAR (salvaguardas)

- Copias de trabajo activas de la app (`.copilot\repos\<repo>` raíz), `Packages`, drafts de editores de vídeo, `ms-playwright-mcp`, `Docker\wsl\main`, `System Volume Information` directamente.
- `docker volume prune` solo con la lista revisada antes (los volúmenes contienen datos).
- Toda carpeta con locks `inuse.*` activos → la sesión dueña está viva; cerrarla primero desde la app.

## Entrega

Informe con: mapa completo que cuadre ±2% + tabla Δ vs medición previa + lista priorizada de candidatos (GB, riesgo, comando de regeneración) + qué quedó aparcado para aprobación futura.
