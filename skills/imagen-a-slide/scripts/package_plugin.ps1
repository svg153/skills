# imagen-a-slide: builds the shareable Claude Code plugin (folder + zip) from this skill and its two agents.
# Usage: package_plugin.ps1 -OutDir <folder> [-Author "<name or team>"] [-Version 2.0.0] [-ForbidFile terms.txt]
#   Output: <OutDir>\imagen-a-slide.zip, <OutDir>\entrada_marketplace.json (plugin folder staged in %TEMP%\imagen-a-slide-pkg)
#   Only the logos listed in -Logos are shipped (client logos stay in the local copy).
#   Safety scan: fails if any shipped text file contains a term from -ForbidFile (one per line; keep that file
#   OUTSIDE the skill, e.g. next to the bench, because it names clients), the current user name or a C:\Users path.
# ASCII only on purpose (PowerShell 5.1 + UTF-8 without BOM breaks accents).
param([Parameter(Mandatory)][string]$OutDir, [string]$Author = '<NOMBRE O EQUIPO>', [string]$Version = '2.0.0',
      [string]$ForbidFile = (Join-Path $HOME '.claude\imagen-a-slide-bench\forbid.txt'),
      [string[]]$Logos = @('ejemplo_cliente.svg'))
$ErrorActionPreference = 'Stop'
$skillDir = Split-Path -Parent $PSScriptRoot
$agentsDir = Join-Path $HOME '.claude\agents'
$utf8 = New-Object Text.UTF8Encoding($false)
$OutDir = [IO.Path]::GetFullPath($OutDir); New-Item -ItemType Directory -Force $OutDir | Out-Null
# stage in a short path (deep output folders hit the 260-char path limit); only the zip + entry go to OutDir
$stage = Join-Path $env:TEMP 'imagen-a-slide-pkg'
$root = Join-Path $stage 'imagen-a-slide'
if (Test-Path $root) { Remove-Item -Recurse -Force $root }
$dst = Join-Path $root 'skills\imagen-a-slide'
New-Item -ItemType Directory -Force $dst, (Join-Path $root '.claude-plugin'), (Join-Path $root 'agents') | Out-Null

# 1. skill files (no packaging templates, no generated renders, only allowed logos)
$skip = '\\package\\|\\__pycache__\\|\.compare\.|\.(pptx|png)$'
foreach ($f in Get-ChildItem -Recurse -File $skillDir) {
  $rel = $f.FullName.Substring($skillDir.Length)
  if ($rel -match $skip) { continue }
  if ($rel -like '\assets\logos\*' -and $Logos -notcontains $f.Name) { continue }
  $to = Join-Path $dst $rel.TrimStart('\'); New-Item -ItemType Directory -Force (Split-Path -Parent $to) | Out-Null
  Copy-Item -LiteralPath $f.FullName $to
}
# 2. agents, with the absolute skill path turned into the plugin root
foreach ($a in 'slide-spec-writer.md', 'slide-qa.md') {
  $t = [IO.File]::ReadAllText((Join-Path $agentsDir $a))
  $t = [regex]::Replace($t, '[A-Za-z]:[\\/]Users[\\/][^\\/`"]+[\\/]\.claude[\\/]skills[\\/]imagen-a-slide', '${CLAUDE_PLUGIN_ROOT}/skills/imagen-a-slide')
  [IO.File]::WriteAllText((Join-Path $root "agents\$a"), $t, $utf8)
}
# 3. manifest + README
$pj = [IO.File]::ReadAllText((Join-Path $skillDir 'package\plugin.json')).Replace('__VERSION__', $Version).Replace('__AUTHOR__', $Author)
[IO.File]::WriteAllText((Join-Path $root '.claude-plugin\plugin.json'), $pj, $utf8)
Copy-Item (Join-Path $skillDir 'package\README.md') (Join-Path $root 'README.md')
$entry = [ordered]@{ name = 'imagen-a-slide'; source = './plugins/imagen-a-slide'; description = ($pj | ConvertFrom-Json).description }
[IO.File]::WriteAllText((Join-Path $OutDir 'entrada_marketplace.json'), ($entry | ConvertTo-Json), $utf8)

# 4. safety scan
$terms = New-Object System.Collections.Generic.List[string]
if (Test-Path $ForbidFile) { foreach ($l in [IO.File]::ReadAllLines($ForbidFile, [Text.Encoding]::UTF8)) { if ($l.Trim() -and -not $l.StartsWith('#')) { $terms.Add($l.Trim()) } } }
else { Write-Warning "no forbid file ($ForbidFile): only user name and paths are checked" }
$terms.Add($env:USERNAME)
$bad = @()
foreach ($f in Get-ChildItem -Recurse -File $root | Where-Object { $_.Extension -in '.md', '.json', '.ps1', '.py', '.js', '.css', '.svg', '.txt', '' }) {
  $t = [IO.File]::ReadAllText($f.FullName)
  # term must start a word (so 'ABC' does not hit 'xabc'), but may be a prefix ('ABC' hits 'ABCDE')
  foreach ($w in $terms) { if ($t -match ('(?i)(?<![\p{L}\p{N}_])' + [regex]::Escape($w))) { $bad += "$($f.FullName.Substring($root.Length)): '$w'" } }
  if ($t -match '[A-Za-z]:\\Users\\[^\\<$]+\\') { $bad += "$($f.FullName.Substring($root.Length)): absolute user path" }
}
if ($bad) { $bad | ForEach-Object { Write-Host "  FORBIDDEN $_" }; throw "package NOT safe to share: $($bad.Count) finding(s); fix the skill and run again" }

# 5. zip
$zip = Join-Path $OutDir 'imagen-a-slide.zip'
if (Test-Path $zip) { Remove-Item -Force $zip }
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::CreateFromDirectory($root, $zip, [IO.Compression.CompressionLevel]::Optimal, $true)
$n = @(Get-ChildItem -Recurse -File $root).Count
"OK plugin (staged)=$root ($n files, version $Version)"
"zip=$zip ($([Math]::Round((Get-Item $zip).Length / 1KB)) KB)"
"scan: $($terms.Count) terms checked, 0 findings"
