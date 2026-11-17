# imagen-a-slide: numeric comparison source image vs render (optional step).
# Runs scripts/compare.py inside the Podman image "imagen-a-slide-compare".
# Falls back to a local Python that has numpy, opencv and scikit-image.
# ASCII only on purpose (PowerShell 5.1 + UTF-8 without BOM breaks accents).
#
#   compare.ps1 -Demo        self-test with generated images (no files needed)
#   compare.ps1 -Build       (re)build the container image
#   compare.ps1 -Src fuente.png -Render Nombre.png [-Spec Nombre.json] [-Slide 1] [-Threshold 0.8] [-Shift 15]
param(
  [string]$Src, [string]$Render, [string]$Spec = '', [int]$Slide = 1,
  [double]$Threshold = 0.80, [double]$Shift = 15, [switch]$Build, [switch]$Demo
)
$ErrorActionPreference = 'Stop'
$SkillDir = Split-Path -Parent $PSScriptRoot
$Image = 'localhost/imagen-a-slide-compare:latest'
$inv = [System.Globalization.CultureInfo]::InvariantCulture

function Fail([string]$msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 2 }

function Find-Podman {
  $c = Get-Command podman -ErrorAction SilentlyContinue
  if ($c) { return $c.Source }
  $p = 'C:\Program Files\RedHat\Podman\podman.exe'
  if (Test-Path $p) { return $p }
  return $null
}

function Get-Runner {
  # Returns 'podman' or the path of a usable local python, or $null.
  $pm = Find-Podman
  if ($pm) {
    & $pm info *> $null
    if ($LASTEXITCODE -ne 0) { Write-Host 'Starting Podman machine...'; & $pm machine start *> $null; & $pm info *> $null }
    if ($LASTEXITCODE -eq 0) {
      & $pm image exists $Image
      if ($LASTEXITCODE -ne 0) {
        Write-Host 'Building comparison image (first time only, ~1-2 min)...'
        & $pm build -t imagen-a-slide-compare -f (Join-Path $SkillDir 'container\Containerfile') (Join-Path $SkillDir 'container') | Out-Null
        if ($LASTEXITCODE -ne 0) { Fail 'podman build failed (proxy? run compare.ps1 -Build to see the log)' }
      }
      return 'podman'
    }
    Write-Host 'Podman is installed but its machine does not start; trying local Python.'
  }
  $py = Get-Command python -ErrorAction SilentlyContinue
  if ($py -and $py.Source -notlike '*WindowsApps*') {
    & $py.Source -c 'import cv2, skimage, numpy' *> $null
    if ($LASTEXITCODE -eq 0) { return $py.Source }
  }
  return $null
}

function Check-File([string]$label, [string]$path) {
  if (-not $path) { return '' }
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
    Fail "$label not found: $path`n       Pass the real path of the file (the C:\ruta\... paths in the docs are only examples)."
  }
  return (Resolve-Path -LiteralPath $path).Path
}

if ($Build) {
  $pm = Find-Podman
  if (-not $pm) { Fail 'Podman is not installed.' }
  & $pm build -t imagen-a-slide-compare -f (Join-Path $SkillDir 'container\Containerfile') (Join-Path $SkillDir 'container')
  exit $LASTEXITCODE
}

$runner = Get-Runner
if (-not $runner) { Fail 'Neither Podman nor a local Python with opencv/scikit-image is available. Skip this optional step.' }

if ($Demo) {
  $d = Join-Path $env:TEMP 'imagen-a-slide-demo'
  New-Item -ItemType Directory -Force $d | Out-Null
  if ($runner -eq 'podman') {
    & (Find-Podman) run --rm -v "${d}:/out" -v "$(Join-Path $SkillDir 'scripts'):/skill:ro" $Image python /skill/compare.py --make-demo /out | Out-Null
  } else {
    & $runner (Join-Path $PSScriptRoot 'compare.py') --make-demo $d | Out-Null
  }
  if ($LASTEXITCODE -ne 0) { Fail 'could not generate the demo files' }
  Write-Host "Demo files in $d (expected: 'titulo' moved dx=+20, 'cuerpo' wider x1.1 -> smaller size; nothing else)"
  $Src = Join-Path $d 'fuente.png'; $Render = Join-Path $d 'render.png'; $Spec = Join-Path $d 'spec.json'
}

if (-not $Src -or -not $Render) {
  Fail "missing arguments.`n       Usage: compare.ps1 -Src source.png -Render render.png [-Spec spec.json] [-Slide N]`n       Self-test: compare.ps1 -Demo"
}
$srcF = Check-File 'Source image (-Src)' $Src
$renF = Check-File 'Render (-Render)' $Render
$specF = Check-File 'Spec (-Spec)' $Spec
$common = @('--slide', "$Slide", '--threshold', $Threshold.ToString($inv), '--shift', $Shift.ToString($inv))

if ($runner -eq 'podman') {
  $mounts = @('-v', "$(Split-Path -Parent $srcF):/src:ro", '-v', "$(Split-Path -Parent $renF):/render",
              '-v', "$(Join-Path $SkillDir 'scripts'):/skill:ro")
  $cargs = @('--src', "/src/$(Split-Path -Leaf $srcF)", '--render', "/render/$(Split-Path -Leaf $renF)")
  if ($specF) { $mounts += @('-v', "$(Split-Path -Parent $specF):/spec:ro"); $cargs += @('--spec', "/spec/$(Split-Path -Leaf $specF)") }
  $all = @('run', '--rm') + $mounts + @($Image, 'python', '/skill/compare.py') + $cargs + $common
  & (Find-Podman) @all | ForEach-Object {
    if ($_ -like 'report=*') {
      'report=' + [IO.Path]::ChangeExtension($renF, '.compare.md')
      'sheet=' + [IO.Path]::ChangeExtension($renF, '.compare.png')
    } else { $_ }
  }
  exit $LASTEXITCODE
}

$cargs = @('--src', $srcF, '--render', $renF)
if ($specF) { $cargs += @('--spec', $specF) }
& $runner (Join-Path $PSScriptRoot 'compare.py') @cargs @common
exit $LASTEXITCODE
