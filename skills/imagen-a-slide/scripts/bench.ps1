# imagen-a-slide test bench. Run it after changing any script, rule or example, to see if things got better or worse.
#
#   bench.ps1 -SelfTest
#       Regression with the skill's own example (no client data): builds examples/ejemplo_tarjetas.json three times
#       (source, identical copy, copy with 3 known faults) and checks that compare.ps1 finds exactly those faults,
#       plus compare.ps1 -Demo. Prints PASS/FAIL per check; exit code = number of failures.
#
#   bench.ps1 -Dir <bench folder>
#       Real cases, one sub-folder each:
#         original.png + spec.json (+ the files the spec uses: fondo.png, logos...)  -> rebuilt, then compared
#         original.png + render.png                                                -> compared only
#       Writes <bench>\bench_<date>.md and appends <bench>\history.csv; shows the change against the last run.
#       Keep the bench folder OUTSIDE the skill: it holds client slides and the skill may be published.
#
# Uses build_from_spec.ps1 (PowerPoint, same safety rules) and compare.ps1 (Podman or local Python).
# ASCII only on purpose (PowerShell 5.1 + UTF-8 without BOM breaks accents).
param([switch]$SelfTest, [string]$Dir = '')
$ErrorActionPreference = 'Stop'
$Scripts = $PSScriptRoot
$SkillDir = Split-Path -Parent $Scripts
$Build = Join-Path $Scripts 'build_from_spec.ps1'
$Compare = Join-Path $Scripts 'compare.ps1'
$Utf8 = New-Object Text.UTF8Encoding($false)
$Inv = [Globalization.CultureInfo]::InvariantCulture

function Read-Json([string]$p) { [IO.File]::ReadAllText($p, [Text.Encoding]::UTF8) | ConvertFrom-Json }
function Run-Build([string]$spec) {
  $out = powershell -NoProfile -ExecutionPolicy Bypass -File $Build -Spec $spec
  $last = ($out | Select-Object -Last 1)
  if ($last -notmatch 'antes=(\d+) despues=(\d+)' -or $Matches[1] -ne $Matches[2]) { throw "build of ${spec}: unexpected end '$last'. STOP (PowerPoint safety)." }
  $png = ($out | Where-Object { $_ -like 'png=*' } | Select-Object -First 1)
  return ($png -replace '^png=', '').Split(';')[0].Trim()
}
function Run-Compare([string]$src, [string]$render, [string]$spec) {
  $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $Compare, '-Src', $src, '-Render', $render)
  if ($spec) { $a += @('-Spec', $spec) }
  $null = & powershell @a
  if ($LASTEXITCODE -ne 0) { throw "compare failed for $render" }
  $j = Read-Json ([IO.Path]::ChangeExtension($render, '.compare.json'))
  $flagged = @($j.elements | Where-Object { $_.issues -and @($_.issues).Count -gt 0 })
  return [pscustomobject]@{ ssim = [double]$j.ssim_global; avisos = $flagged.Count; flagged = $flagged; all = $j.elements }
}

$fails = 0
function Check([string]$name, [bool]$ok, [string]$detail) {
  if ($ok) { Write-Host "  PASS  $name" -ForegroundColor Green } else { Write-Host "  FAIL  $name  ($detail)" -ForegroundColor Red; $script:fails++ }
}

if ($SelfTest) {
  $W = Join-Path $env:TEMP ('imagen-a-slide-selftest_' + [guid]::NewGuid().ToString('N').Substring(0, 8))
  New-Item -ItemType Directory -Force $W | Out-Null
  $ex = [IO.File]::ReadAllText((Join-Path $SkillDir 'examples\ejemplo_tarjetas.json'), [Text.Encoding]::UTF8)
  function Variant([string]$name, [string]$txt) {
    $t = $txt.Replace('"ejemplo_tarjetas.pptx"', "`"$name.pptx`"").Replace('"ejemplo_tarjetas.png"', "`"$name.png`"")
    $p = Join-Path $W "$name.json"; [IO.File]::WriteAllText($p, $t, $Utf8); return $p
  }
  # Known faults: title +25 px right, card text 10% smaller, client logo +20 px down.
  $faults = @(@('"x": 62, "y": 58', '"x": 87, "y": 58'), @('"anchor": "middle", "size": 13.2', '"anchor": "middle", "size": 12'), @('"x": 1795, "y": 31', '"x": 1795, "y": 51'))
  $mal = $ex
  foreach ($f in $faults) { if (-not $mal.Contains($f[0])) { throw "self-test: example no longer contains '$($f[0])'; update the faults in bench.ps1" }; $mal = $mal.Replace($f[0], $f[1]) }
  Write-Host "Self-test in $W"
  $srcPng = Run-Build (Variant 'fuente' $ex)
  $idSpec = Variant 'identica' $ex; $idPng = Run-Build $idSpec
  $malSpec = Variant 'mal' $mal; $malPng = Run-Build $malSpec

  $r = Run-Compare $srcPng $idPng $idSpec
  Check 'identical copy: 0 warnings' ($r.avisos -eq 0) "avisos=$($r.avisos): $(($r.flagged | ForEach-Object { $_.name }) -join ', ')"
  Check 'identical copy: SSIM >= 0.995' ($r.ssim -ge 0.995) "ssim=$($r.ssim)"

  $r = Run-Compare $srcPng $malPng $malSpec
  $names = @($r.flagged | ForEach-Object { $_.name } | Sort-Object)
  Check 'faulty copy: exactly Titulo, Texto 1, Logo cliente' (($names -join '|') -eq 'Logo cliente|Texto 1|Titulo') "flagged: $($names -join ', ')"
  $t = $r.all | Where-Object { $_.name -eq 'Titulo' }
  Check 'Titulo: dx = +25 (+-3)' ($t -and [Math]::Abs([double]$t.dx - 25) -le 3) "dx=$($t.dx)"
  $l = $r.all | Where-Object { $_.name -eq 'Logo cliente' }
  Check 'Logo cliente: dy = +20 (+-3)' ($l -and [Math]::Abs([double]$l.dy - 20) -le 3) "dy=$($l.dy)"
  $x = $r.all | Where-Object { $_.name -eq 'Texto 1' }
  Check 'Texto 1: suggested size 13.2 (+-0.5)' ($x -and $x.size_sugerido -and [Math]::Abs([double]$x.size_sugerido - 13.2) -le 0.5) "size_sugerido=$($x.size_sugerido)"

  $d = & powershell -NoProfile -ExecutionPolicy Bypass -File $Compare -Demo
  $demoJson = Read-Json (Join-Path $env:TEMP 'imagen-a-slide-demo\render.compare.json')
  $dt = $demoJson.elements | Where-Object { $_.name -eq 'titulo' }; $dc = $demoJson.elements | Where-Object { $_.name -eq 'cuerpo' }
  Check 'demo: titulo dx = +20 (+-3)' ($dt -and [Math]::Abs([double]$dt.dx - 20) -le 3) "dx=$($dt.dx)"
  Check 'demo: cuerpo wider (wratio > 1.05)' ($dc -and [double]$dc.wratio -gt 1.05) "wratio=$($dc.wratio)"
  Check 'demo: nothing else flagged' (@($demoJson.elements | Where-Object { $_.issues -and @($_.issues).Count -gt 0 }).Count -eq 2) ''

  if ($fails -eq 0) { Write-Host "SELF-TEST OK" -ForegroundColor Green; Remove-Item -Recurse -Force $W } else { Write-Host "SELF-TEST: $fails failure(s). Files kept in $W" -ForegroundColor Red }
  exit $fails
}

if (-not $Dir) { Write-Host 'Usage: bench.ps1 -SelfTest   |   bench.ps1 -Dir <bench folder>'; exit 2 }
$Dir = (Resolve-Path -LiteralPath $Dir).Path
$stamp = Get-Date -Format 'yyyy-MM-dd_HHmm'
$hist = Join-Path $Dir 'history.csv'
$prev = @{}
if (Test-Path $hist) { foreach ($row in (Import-Csv $hist)) { $prev[$row.case] = $row } }
$rows = @()
foreach ($case in (Get-ChildItem -LiteralPath $Dir -Directory | Sort-Object Name)) {
  $orig = Join-Path $case.FullName 'original.png'
  if (-not (Test-Path $orig)) { Write-Host "skip $($case.Name): no original.png"; continue }
  $spec = Join-Path $case.FullName 'spec.json'; $render = Join-Path $case.FullName 'render.png'
  try {
    if (Test-Path $spec) {
      $work = Join-Path $env:TEMP ("imagen-a-slide-bench_" + $case.Name + '_' + [guid]::NewGuid().ToString('N').Substring(0, 6))
      Copy-Item -LiteralPath $case.FullName -Destination $work -Recurse
      $png = Run-Build (Join-Path $work 'spec.json'); $mode = 'build'
      $r = Run-Compare $orig $png (Join-Path $work 'spec.json')
      Copy-Item $png (Join-Path $case.FullName 'last_render.png') -Force
      Copy-Item ([IO.Path]::ChangeExtension($png, '.compare.png')) (Join-Path $case.FullName 'last_compare.png') -Force
      Remove-Item -Recurse -Force $work
    } elseif (Test-Path $render) {
      $mode = 'render'; $r = Run-Compare $orig $render ''
    } else { Write-Host "skip $($case.Name): no spec.json or render.png"; continue }
  } catch { Write-Host "ERROR $($case.Name): $_" -ForegroundColor Red; $fails++; continue }
  $p = $prev[$case.Name]
  # history.csv always uses '.' as decimal separator (the Spanish locale would write '0,91').
  $delta = $(if ($p) { ($r.ssim - [double]::Parse($p.ssim, $Inv)).ToString('+0.000;-0.000;0.000', $Inv) + ' / ' + ($r.avisos - [int]$p.avisos).ToString('+0;-0;0', $Inv) } else { 'new' })
  $rows += [pscustomobject]@{ case = $case.Name; mode = $mode; ssim = $r.ssim.ToString('0.000', $Inv); avisos = $r.avisos; delta = $delta
                             top = (($r.flagged | Select-Object -First 3 | ForEach-Object { $_.name }) -join ', ') }
}
$rows | Format-Table -AutoSize | Out-String | Write-Host
$md = @("# Bench $stamp", '', '| Case | Mode | SSIM | Warnings | Change vs last (SSIM / warnings) | Main warnings |', '|---|---|---|---|---|---|')
$md += $rows | ForEach-Object { "| $($_.case) | $($_.mode) | $($_.ssim) | $($_.avisos) | $($_.delta) | $($_.top) |" }
[IO.File]::WriteAllText((Join-Path $Dir "bench_$stamp.md"), ($md -join "`n") + "`n", $Utf8)
$newRows = $rows | ForEach-Object { [pscustomobject]@{ date = $stamp; case = $_.case; mode = $_.mode; ssim = $_.ssim; avisos = $_.avisos } }
if (Test-Path $hist) { $newRows | Export-Csv $hist -Append -NoTypeInformation } else { $newRows | Export-Csv $hist -NoTypeInformation }
Write-Host "report: $(Join-Path $Dir "bench_$stamp.md")"
exit $fails
