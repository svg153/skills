# imagen-a-slide HTML engine: builds ONE self-contained .html presentation from the same JSON spec(s) that
# build_from_spec.ps1 turns into PowerPoint. Nothing to install, no network: the renderer (html/deck.js + deck.css),
# the specs and every image/logo are embedded in the file (data URIs). Send the .html and it opens in any browser.
# Usage: build_html.ps1 -Spec a.json[,b.json,...] -Out deck.html [-Title "..."] [-NoPng] [-BgQuality 88]
#   Several specs (or one spec with "slides") = one deck, in the given order.
#   Unless -NoPng, writes a PNG of every slide with headless Edge (temporary profile, never the user's) for comparing:
#   <stem>_html.png (1 slide) or <stem>_html_sN.png, 2000 px wide, same as the PowerPoint renders.
#   Background images bigger than 400 KB are re-encoded as JPEG (BgQuality) to keep the file small.
# ASCII only on purpose (PowerShell 5.1 + UTF-8 without BOM breaks accents).
param([Parameter(Mandatory)][string[]]$Spec, [Parameter(Mandatory)][string]$Out, [string]$Title = '', [switch]$NoPng, [int]$BgQuality = 88)
$ErrorActionPreference = 'Stop'
[Threading.Thread]::CurrentThread.CurrentCulture = [Globalization.CultureInfo]::InvariantCulture
$skillDir = Split-Path -Parent $PSScriptRoot
$utf8 = New-Object Text.UTF8Encoding($false)
Add-Type -AssemblyName System.Drawing

function Prop($o, [string]$n, $d = $null) { if ($null -ne $o -and $null -ne $o.PSObject.Properties[$n]) { return $o.$n } return $d }
function Set-Prop($o, [string]$n, $v) { if ($o.PSObject.Properties[$n]) { $o.$n = $v } else { $o | Add-Member -NotePropertyName $n -NotePropertyValue $v } }
$cache = @{}
# Optional client profile (kept OUTSIDE this skill), same rules as build_from_spec.ps1:
# spec "profile" or env IMAGEN_A_SLIDE_PROFILE -> perfil.json { "logos": "assets/logos", "theme": {...} }
$script:PRF = $null; $script:PRFDIR = $null
function Load-Profile($doc, [string]$base) {
  $pp = Prop $doc 'profile' $env:IMAGEN_A_SLIDE_PROFILE
  if (-not $pp) { $script:PRF = $null; return }
  if (-not [IO.Path]::IsPathRooted($pp)) { $pp = Join-Path $base $pp }
  if (-not (Test-Path -LiteralPath $pp)) { throw "profile not found: $pp" }
  $pp = (Resolve-Path -LiteralPath $pp).Path; $script:PRFDIR = Split-Path -Parent $pp
  $script:PRF = [IO.File]::ReadAllText($pp, [Text.Encoding]::UTF8) | ConvertFrom-Json
}
function Merge-ProfileTheme($s) {
  $pt = Prop $script:PRF 'theme'; if (-not $pt) { return }
  if ($null -eq (Prop $s 'theme')) { Set-Prop $s 'theme' ([pscustomobject]@{}) }
  foreach ($q in $pt.PSObject.Properties) { if ($null -eq (Prop $s.theme $q.Name)) { Set-Prop $s.theme $q.Name $q.Value } }
}
function LogoPath([string]$name) {
  if ($script:PRF) { $c = Join-Path (Join-Path $script:PRFDIR (Prop $script:PRF 'logos' 'logos')) $name; if (Test-Path -LiteralPath $c) { return $c } }
  $c = Join-Path $skillDir ('assets\logos\' + $name); if (Test-Path -LiteralPath $c) { return $c }
  throw "logo not found: @logos/$name (looked in the profile logos folder and in the skill's assets\logos)"
}
function DataUri([string]$p, [string]$base, [bool]$isBg) {
  if ($p.StartsWith('data:')) { return $p }
  $full = $(if ($p.StartsWith('@logos/')) { LogoPath $p.Substring(7) } elseif ([IO.Path]::IsPathRooted($p)) { $p } else { Join-Path $base $p })
  if (-not (Test-Path -LiteralPath $full)) { throw "asset not found: $p ($full)" }
  $key = "$full|$isBg"; if ($cache.ContainsKey($key)) { return $cache[$key] }
  $ext = [IO.Path]::GetExtension($full).ToLower().TrimStart('.')
  $bytes = [IO.File]::ReadAllBytes($full)
  $mime = @{ png = 'image/png'; jpg = 'image/jpeg'; jpeg = 'image/jpeg'; svg = 'image/svg+xml'; webp = 'image/webp'; gif = 'image/gif' }[$ext]
  if (-not $mime) { throw "unsupported asset type: $full" }
  if ($isBg -and $ext -eq 'png' -and $bytes.Length -gt 400KB) {
    $img = [Drawing.Image]::FromFile($full)
    $codec = [Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
    $ep = New-Object Drawing.Imaging.EncoderParameters(1); $ep.Param[0] = New-Object Drawing.Imaging.EncoderParameter([Drawing.Imaging.Encoder]::Quality, [long]$BgQuality)
    $ms = New-Object IO.MemoryStream; $img.Save($ms, $codec, $ep); $img.Dispose(); $bytes = $ms.ToArray(); $mime = 'image/jpeg'
  }
  $uri = "data:$mime;base64," + [Convert]::ToBase64String($bytes)
  $cache[$key] = $uri; return $uri
}

$slides = New-Object System.Collections.Generic.List[object]
foreach ($sp in ($Spec | ForEach-Object { $_.Split(',') } | Where-Object { $_.Trim() })) {
  $path = (Resolve-Path -LiteralPath $sp.Trim()).Path; $base = Split-Path -Parent $path
  $doc = [IO.File]::ReadAllText($path, [Text.Encoding]::UTF8) | ConvertFrom-Json
  Load-Profile $doc $base
  $list = $(if (Prop $doc 'slides') { @($doc.slides) } else { @($doc) })
  foreach ($s in $list) {
    foreach ($inh in 'sourceWidth', 'theme', 'font') { if ($null -eq (Prop $s $inh) -and $null -ne (Prop $doc $inh)) { Set-Prop $s $inh $doc.$inh } }
    if ($script:PRF) { Merge-ProfileTheme $s }
    if ($s.PSObject.Properties['profile']) { $s.PSObject.Properties.Remove('profile') }
    $bg = Prop $s 'background'; if ($bg -and (Prop $bg 'image')) { $bg.image = DataUri $bg.image $base $true }
    foreach ($e in @(Prop $s 'elements' @())) {
      $t = [string](Prop $e 'type' (Prop $e 'kind' ''))
      if ($t -in 'picture', 'image') {
        $p = Prop $e 'path' (Prop $e 'src')
        if ($p) { Set-Prop $e 'path' (DataUri $p $base $false) }
      }
    }
    foreach ($drop in 'output', 'png') { if ($s.PSObject.Properties[$drop]) { $s.PSObject.Properties.Remove($drop) } }
    $slides.Add($s)
  }
}
if (-not $Title) { $Title = [IO.Path]::GetFileNameWithoutExtension($Out) }
$deck = [pscustomobject]@{ title = $Title; slides = $slides.ToArray() }
# ConvertTo-Json (PS 5.1) escapes < > ' & as \uXXXX, so the JSON cannot close the <script> tag.
$json = $deck | ConvertTo-Json -Depth 30 -Compress
$css = [IO.File]::ReadAllText((Join-Path $skillDir 'html\deck.css'), [Text.Encoding]::UTF8)
$js = [IO.File]::ReadAllText((Join-Path $skillDir 'html\deck.js'), [Text.Encoding]::UTF8)
$safeTitle = [Net.WebUtility]::HtmlEncode($Title)
$html = "<!DOCTYPE html>`n<html lang=`"es`">`n<head>`n<meta charset=`"utf-8`">`n<meta name=`"viewport`" content=`"width=device-width, initial-scale=1`">`n<title>$safeTitle</title>`n<style>`n$css`n</style>`n</head>`n<body>`n<script type=`"application/json`" id=`"deck-data`">$json</script>`n<script>`n$js`n</script>`n</body>`n</html>`n"
$outFull = [IO.Path]::GetFullPath($(if ([IO.Path]::IsPathRooted($Out)) { $Out } else { Join-Path (Get-Location).Path $Out }))
[IO.File]::WriteAllText($outFull, $html, $utf8)
"OK html=$outFull ($($slides.Count) diapositivas, $([Math]::Round((Get-Item $outFull).Length / 1KB)) KB)"

if (-not $NoPng) {
  $edge = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe", "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
  if (-not $edge) { Write-Host 'Edge not found: PNG renders skipped'; exit 0 }
  $profileDir = Join-Path $env:TEMP ('html_render_' + [guid]::NewGuid().ToString('N'))
  $stem = [IO.Path]::Combine([IO.Path]::GetDirectoryName($outFull), [IO.Path]::GetFileNameWithoutExtension($outFull))
  $uri = ([Uri]$outFull).AbsoluteUri
  $pngs = @()
  try {
    for ($i = 1; $i -le $slides.Count; $i++) {
      $png = $(if ($slides.Count -eq 1) { "${stem}_html.png" } else { "${stem}_html_s$i.png" })
      if (Test-Path $png) { Remove-Item $png -Force }
      $args2 = @('--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1', '--no-first-run',
                 '--disable-extensions', "--user-data-dir=$profileDir", '--window-size=2000,1125', '--virtual-time-budget=4000',
                 "--screenshot=$png", "$uri#export=1&slide=$i")
      $quoted = $args2 | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } }   # Start-Process does not quote
      $p = Start-Process -FilePath $edge -ArgumentList $quoted -PassThru -WindowStyle Hidden
      if (-not $p.WaitForExit(60000)) { try { $p.Kill() } catch { }; throw "Edge did not finish rendering slide $i" }
      if (-not (Test-Path $png)) { throw "Edge produced no screenshot for slide $i" }
      $pngs += $png
    }
  } finally { Start-Sleep -Milliseconds 300; Remove-Item -Recurse -Force $profileDir -ErrorAction SilentlyContinue }
  "png=" + ($pngs -join ' ; ')
}
