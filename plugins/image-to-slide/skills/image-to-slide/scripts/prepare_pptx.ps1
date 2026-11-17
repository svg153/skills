# Turns a "flat" PPTX (slides that are just pictures) into one PNG per slide plus its speaker notes, so each
# slide can be rebuilt with build_from_spec.ps1.
# Usage: prepare_pptx.ps1 -Src deck.pptx -OutDir pages      -> pages\s1.png, s2.png ... + pages\manifest.json
# Safety: opens a temporary COPY read-only and without a window; only closes that copy; never Quit().
param([Parameter(Mandatory)][string]$Src, [Parameter(Mandatory)][string]$OutDir, [int]$Width = 2000)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force $OutDir | Out-Null
$OutDir = (Resolve-Path $OutDir).Path
$copy = Join-Path $env:TEMP ('prep_' + [guid]::NewGuid().ToString('N') + '.pptx'); Copy-Item (Resolve-Path $Src).Path $copy
$ppt = New-Object -ComObject PowerPoint.Application
$before = $ppt.Presentations.Count
$pres = $ppt.Presentations.Open($copy, -1, 0, 0)   # ReadOnly, Untitled=false, WithWindow=false
$pages = @()
try {
  $h = [int]($Width * $pres.PageSetup.SlideHeight / $pres.PageSetup.SlideWidth)
  for ($i = 1; $i -le $pres.Slides.Count; $i++) {
    $sl = $pres.Slides($i); $png = Join-Path $OutDir "s$i.png"
    $sl.Export($png, 'PNG', $Width, $h)
    $notes = ''
    try { $notes = $sl.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text } catch { }
    $pages += [ordered]@{ id = "s$i"; source = "s$i.png"; width = $Width; height = $h; notes = $notes }
  }
} finally { $pres.Close(); Remove-Item $copy -Force -ErrorAction SilentlyContinue }
[IO.File]::WriteAllText((Join-Path $OutDir 'manifest.json'), ([ordered]@{ source = $Src; pages = $pages } | ConvertTo-Json -Depth 4), (New-Object Text.UTF8Encoding($false)))
"OK $($pages.Count) slides -> $OutDir  (presentaciones abiertas antes=$before despues=$($ppt.Presentations.Count))"
