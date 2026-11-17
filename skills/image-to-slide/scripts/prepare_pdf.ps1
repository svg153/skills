# Turns a PDF (slides exported as PDF, scanned decks) into one PNG per page, so each page can be rebuilt with
# build_from_spec.ps1. Uses the PDF renderer built into Windows (Windows.Data.Pdf): no install, nothing leaves the machine.
# Usage: prepare_pdf.ps1 -Src deck.pdf -OutDir pages [-Width 2000] [-Pages "1,3-5"]
#        -> pages\s1.png, s2.png ... + pages\manifest.json (same format as prepare_pptx.ps1; notes are empty)
param([Parameter(Mandatory)][string]$Src, [Parameter(Mandatory)][string]$OutDir, [int]$Width = 2000, [string]$Pages = '')
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Storage.StorageFolder, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Data.Pdf.PdfDocument, Windows.Data.Pdf, ContentType = WindowsRuntime]
$ext = [System.WindowsRuntimeSystemExtensions].GetMethods()
$asTaskOp = ($ext | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
$asTaskAct = ($ext | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction' })[0]
function Await($op, [Type]$t) { $task = $asTaskOp.MakeGenericMethod($t).Invoke($null, @($op)); $task.Wait(-1) | Out-Null; return $task.Result }
function AwaitAction($act) { $task = $asTaskAct.Invoke($null, @($act)); $task.Wait(-1) | Out-Null }

function Parse-Pages([string]$spec, [int]$count) {
  if (-not $spec.Trim()) { return 1..$count }
  $list = @()
  foreach ($part in $spec.Split(',')) {
    $p = $part.Trim(); if (-not $p) { continue }
    if ($p -match '^(\d+)-(\d+)$') { $list += [int]$Matches[1]..[int]$Matches[2] } else { $list += [int]$p }
  }
  return $list | Where-Object { $_ -ge 1 -and $_ -le $count }
}

$srcPath = (Resolve-Path -LiteralPath $Src).Path
New-Item -ItemType Directory -Force $OutDir | Out-Null
$OutDir = (Resolve-Path -LiteralPath $OutDir).Path
$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($srcPath)) ([Windows.Storage.StorageFile])
$doc = Await ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($file)) ([Windows.Data.Pdf.PdfDocument])
if ($doc.IsPasswordProtected) { throw 'The PDF is password protected.' }
$folder = Await ([Windows.Storage.StorageFolder]::GetFolderFromPathAsync($OutDir)) ([Windows.Storage.StorageFolder])

$out = @(); $n = 0
foreach ($p in (Parse-Pages $Pages ([int]$doc.PageCount))) {
  $n++
  $page = $doc.GetPage([uint32]($p - 1))
  $h = [int][Math]::Round($Width * $page.Size.Height / $page.Size.Width)
  $opts = New-Object Windows.Data.Pdf.PdfPageRenderOptions
  $opts.DestinationWidth = [uint32]$Width; $opts.DestinationHeight = [uint32]$h
  $sf = Await ($folder.CreateFileAsync("s$n.png", [Windows.Storage.CreationCollisionOption]::ReplaceExisting)) ([Windows.Storage.StorageFile])
  $stream = Await ($sf.OpenAsync([Windows.Storage.FileAccessMode]::ReadWrite)) ([Windows.Storage.Streams.IRandomAccessStream])
  try { AwaitAction ($page.RenderToStreamAsync($stream, $opts)) } finally { $stream.Dispose(); $page.Dispose() }
  $ratio = $page.Size.Width / $page.Size.Height
  $out += [ordered]@{ id = "s$n"; source = "s$n.png"; pdf_page = $p; width = $Width; height = $h; notes = '' }
  if ([Math]::Abs($ratio - 16.0 / 9.0) -gt 0.02) { Write-Host "  page $p is not 16:9 (ratio $([Math]::Round($ratio, 3))): set sourceWidth/layout accordingly" }
}
[IO.File]::WriteAllText((Join-Path $OutDir 'manifest.json'), ([ordered]@{ source = $Src; pages = $out } | ConvertTo-Json -Depth 4), (New-Object Text.UTF8Encoding($false)))
"OK $($out.Count) paginas -> $OutDir"
