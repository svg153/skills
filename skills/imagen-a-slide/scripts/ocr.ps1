# Local OCR with the OCR engine built into Windows (no install, nothing leaves the machine).
# Usage: ocr.ps1 -Src slide.png|webp|jpg [-Out slide.ocr.json]
# Output: JSON with one entry per text line: text (draft: may lack accents), x,y,w,h in px of a $SourceWidth-wide source,
#         pt_regular / pt_bold = font size (pt) that reproduces the line's measured WIDTH in $Font (regular or bold).
#         Lines mixing a bold lead-in and regular text fall between both values.
# Use OCR for GEOMETRY only; always take the final text from reading the image.
# Also writes <out>.png (unless -NoOverlay): the image with every OCR line boxed and numbered (n in the JSON).
#   Blue = text line with a font size; red = no size (icons, symbols, 1-3 chars): measure those by reading the image.
param([Parameter(Mandatory)][string]$Src, [string]$Out, [string]$Font = 'Segoe UI', [int]$SourceWidth = 2000, [switch]$NoOverlay)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationCore,WindowsBase
# font size (pt) that makes $text exactly $wpx wide (px of a $SourceWidth-px source rendered on a 960 pt slide)
function FitPt([string]$text, [double]$wpx, [bool]$bold, [double]$scale) {
  if ($text.Length -lt 4) { return $null }
  $tf = New-Object Windows.Media.Typeface((New-Object Windows.Media.FontFamily($Font)), [Windows.FontStyles]::Normal, $(if ($bold) { [Windows.FontWeights]::Bold } else { [Windows.FontWeights]::Normal }), [Windows.FontStretches]::Normal)
  $ft = New-Object Windows.Media.FormattedText($text, [Globalization.CultureInfo]::InvariantCulture, [Windows.FlowDirection]::LeftToRight, $tf, 100.0, [Windows.Media.Brushes]::Black)
  $targetPt = $wpx * $scale * (960.0 / $SourceWidth)
  return [Math]::Round(100.0 * 0.75 * $targetPt / ($ft.WidthIncludingTrailingWhitespace * 0.75), 1)
}
[Threading.Thread]::CurrentThread.CurrentCulture = [Globalization.CultureInfo]::InvariantCulture
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType = WindowsRuntime]
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, [Type]$t) { $task = $asTask.MakeGenericMethod($t).Invoke($null, @($op)); $task.Wait(-1) | Out-Null; return $task.Result }

$path = (Resolve-Path $Src).Path
if (-not $Out) { $Out = [IO.Path]::ChangeExtension($path, '.ocr.json') }
$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($path)) ([Windows.Storage.StorageFile])
$stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
$dec = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bmp = Await ($dec.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if (-not $engine) { $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage((New-Object Windows.Globalization.Language 'en-US')) }
$res = Await ($engine.RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult])
$scale = [double]$SourceWidth / $bmp.PixelWidth
$lines = @(); $raw = @()
foreach ($ln in $res.Lines) {
  $x0 = [double]::MaxValue; $y0 = [double]::MaxValue; $x1 = 0; $y1 = 0
  foreach ($w in $ln.Words) { $r = $w.BoundingRect; $x0 = [Math]::Min($x0, $r.X); $y0 = [Math]::Min($y0, $r.Y); $x1 = [Math]::Max($x1, $r.X + $r.Width); $y1 = [Math]::Max($y1, $r.Y + $r.Height) }
  $h = $y1 - $y0
  $wpx = $x1 - $x0
  $ptR = FitPt $ln.Text $wpx $false $scale
  $lines += [ordered]@{ n = $lines.Count + 1; text = $ln.Text; x = [int]($x0 * $scale); y = [int]($y0 * $scale); w = [int]($wpx * $scale); h = [int]($h * $scale)
    pt_regular = $ptR; pt_bold = (FitPt $ln.Text $wpx $true $scale) }
  $raw += , @($x0, $y0, $wpx, $h, ($null -ne $ptR))
}
$doc = [ordered]@{ source = $path; width = $bmp.PixelWidth; height = $bmp.PixelHeight; language = $engine.RecognizerLanguage.LanguageTag; lines = $lines }
$json = $doc | ConvertTo-Json -Depth 5
[IO.File]::WriteAllText($Out, $json, (New-Object Text.UTF8Encoding($false)))
$stream.Dispose()
$ovNote = ''
if (-not $NoOverlay) {
  # Overlay in the image's own pixels: original + numbered boxes, for checking the OCR at a glance.
  $fs = [IO.File]::OpenRead($path)
  $wdec = [Windows.Media.Imaging.BitmapDecoder]::Create($fs, 'PreservePixelFormat', 'OnLoad'); $frame = $wdec.Frames[0]; $fs.Close()
  $W = $frame.PixelWidth; $H = $frame.PixelHeight
  $dv = New-Object Windows.Media.DrawingVisual; $dc = $dv.RenderOpen()
  $dc.DrawImage($frame, (New-Object Windows.Rect(0, 0, $W, $H)))
  $fsz = [Math]::Max(11.0, $W / 120.0)
  $blue = [Windows.Media.Color]::FromRgb(37, 99, 235); $red = [Windows.Media.Color]::FromRgb(220, 38, 38)
  $tf = New-Object Windows.Media.Typeface('Segoe UI')
  for ($i = 0; $i -lt $raw.Count; $i++) {
    $q = $raw[$i]; $col = $(if ($q[4]) { $blue } else { $red })
    $br = New-Object Windows.Media.SolidColorBrush($col)
    $dc.DrawRectangle($null, (New-Object Windows.Media.Pen($br, [Math]::Max(1.5, $W / 1000.0))), (New-Object Windows.Rect($q[0], $q[1], $q[2], $q[3])))
    $ft = New-Object Windows.Media.FormattedText([string]($i + 1), [Globalization.CultureInfo]::InvariantCulture, [Windows.FlowDirection]::LeftToRight, $tf, $fsz, [Windows.Media.Brushes]::White)
    $lw = [double]$ft.Width + 6.0; $lh = [double]$ft.Height
    $lx = [double][Math]::Max(0, $q[0] - $lw); $ly = [double][Math]::Max(0, $q[1]); $tx = $lx + 3.0
    $dc.DrawRectangle($br, $null, (New-Object Windows.Rect($lx, $ly, $lw, $lh)))
    $dc.DrawText($ft, (New-Object Windows.Point($tx, $ly)))
  }
  $dc.Close()
  $rtb = New-Object Windows.Media.Imaging.RenderTargetBitmap($W, $H, 96, 96, [Windows.Media.PixelFormats]::Pbgra32); $rtb.Render($dv)
  $ovPath = [IO.Path]::ChangeExtension($Out, '.png')
  if ($ovPath -eq $path) { $ovPath = [IO.Path]::ChangeExtension($Out, '.ocr.png') }
  $enc = New-Object Windows.Media.Imaging.PngBitmapEncoder; $enc.Frames.Add([Windows.Media.Imaging.BitmapFrame]::Create($rtb))
  $o = [IO.File]::Create($ovPath); $enc.Save($o); $o.Close()
  $ovNote = ", control: $ovPath"
}
"OK $Out ($($lines.Count) lineas, idioma $($doc.language)$ovNote)"
