# Cuts a region of the source image into its own PNG, to place it as a movable `picture` element (a photo or
# screenshot inside a card, a logo with no official SVG, a complex icon that is not worth redrawing).
# Usage: crop.ps1 -Src slide.png -Out logo.png -Box "x0,y0,x1,y1" [-Transparent] [-Tol 28] [-SourceWidth 2000]
#   -Box          in px of a SourceWidth-wide source (the same coordinates as the spec); scaled if the image differs
#   -Transparent  makes the background colour transparent (estimated as the median colour of the crop's border),
#                 with a soft edge so anti-aliased outlines stay clean. Only for flat backgrounds (logo/icon on a
#                 plain colour); never on photos.
# Prints the spec line to paste: { "type": "picture", "path": ..., "x", "y", "w", "h" }.
# Do NOT use it to cut a photo out of a gradient background with a blur (vertical seam): that is clean_bg's job.
param([Parameter(Mandatory)][string]$Src, [Parameter(Mandatory)][string]$Out, [Parameter(Mandatory)][string]$Box,
      [switch]$Transparent, [double]$Tol = 28, [int]$SourceWidth = 2000)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationCore,WindowsBase
if (-not ('CropAlpha' -as [type])) {
Add-Type -TypeDefinition @"
public static class CropAlpha {
  // BGRA buffer: alpha from colour distance to the median border colour, with a soft ramp of width tol/2.
  public static int Apply(byte[] b, int w, int h, double tol) {
    int nb = 2 * w + 2 * h; int[] r = new int[nb], g = new int[nb], bl = new int[nb]; int k = 0;
    for (int x = 0; x < w; x++) { Add(b, w, x, 0, r, g, bl, ref k); Add(b, w, x, h - 1, r, g, bl, ref k); }
    for (int y = 0; y < h; y++) { Add(b, w, 0, y, r, g, bl, ref k); Add(b, w, w - 1, y, r, g, bl, ref k); }
    System.Array.Sort(r, 0, k); System.Array.Sort(g, 0, k); System.Array.Sort(bl, 0, k);
    double mr = r[k / 2], mg = g[k / 2], mb = bl[k / 2]; int clear = 0;
    for (int i = 0; i < w * h; i++) {
      int p = i * 4;
      double d = System.Math.Sqrt((b[p] - mb) * (b[p] - mb) + (b[p + 1] - mg) * (b[p + 1] - mg) + (b[p + 2] - mr) * (b[p + 2] - mr));
      double a = (d - tol * 0.5) / (tol * 0.5); if (a < 0) a = 0; if (a > 1) a = 1;
      if (a < 1) {
        // un-blend the background from semi-transparent edge pixels so no halo of the old colour remains
        if (a > 0.02) { b[p] = Clamp((b[p] - mb * (1 - a)) / a); b[p + 1] = Clamp((b[p + 1] - mg * (1 - a)) / a); b[p + 2] = Clamp((b[p + 2] - mr * (1 - a)) / a); }
        b[p + 3] = (byte)System.Math.Round(b[p + 3] * a); if (a == 0) clear++;
      }
    }
    return (int)(100.0 * clear / (w * h));
  }
  static void Add(byte[] b, int w, int x, int y, int[] r, int[] g, int[] bl, ref int k) { int p = (y * w + x) * 4; bl[k] = b[p]; g[k] = b[p + 1]; r[k] = b[p + 2]; k++; }
  static byte Clamp(double v) { return (byte)System.Math.Max(0, System.Math.Min(255, System.Math.Round(v))); }
}
"@
}
$srcPath = (Resolve-Path -LiteralPath $Src).Path
$fs = [IO.File]::OpenRead($srcPath)
$dec = [Windows.Media.Imaging.BitmapDecoder]::Create($fs, 'PreservePixelFormat', 'OnLoad'); $f = $dec.Frames[0]; $fs.Close()
$cv = New-Object Windows.Media.Imaging.FormatConvertedBitmap($f, [Windows.Media.PixelFormats]::Bgra32, $null, 0)
$k = $cv.PixelWidth / [double]$SourceWidth
$v = [double[]]($Box.Split(',') | ForEach-Object { [double]::Parse($_.Trim(), [Globalization.CultureInfo]::InvariantCulture) })
if ($v.Count -ne 4 -or $v[2] -le $v[0] -or $v[3] -le $v[1]) { throw "Box must be x0,y0,x1,y1 with x1>x0 and y1>y0 (got '$Box')" }
$x0 = [int][Math]::Max(0, [Math]::Round($v[0] * $k)); $y0 = [int][Math]::Max(0, [Math]::Round($v[1] * $k))
$x1 = [int][Math]::Min($cv.PixelWidth, [Math]::Round($v[2] * $k)); $y1 = [int][Math]::Min($cv.PixelHeight, [Math]::Round($v[3] * $k))
$w = $x1 - $x0; $h = $y1 - $y0
$buf = New-Object byte[] ($w * $h * 4)
$cv.CopyPixels((New-Object Windows.Int32Rect($x0, $y0, $w, $h)), $buf, $w * 4, 0)
$note = ''
if ($Transparent) { $pct = [CropAlpha]::Apply($buf, $w, $h, $Tol); $note = " ($pct% transparent)"; if ($pct -lt 15) { $note += ' WARNING: little background removed; is the background really flat?' } }
$bmp = [Windows.Media.Imaging.BitmapSource]::Create($w, $h, 96, 96, [Windows.Media.PixelFormats]::Bgra32, $null, $buf, $w * 4)
$enc = New-Object Windows.Media.Imaging.PngBitmapEncoder; $enc.Frames.Add([Windows.Media.Imaging.BitmapFrame]::Create($bmp))
$o = [IO.File]::Create($Out); $enc.Save($o); $o.Close()
$inv = [Globalization.CultureInfo]::InvariantCulture
"OK $Out ($w x $h px)$note"
'spec: { "type": "picture", "name": "...", "path": "' + [IO.Path]::GetFileName($Out) + '", "x": ' + $v[0].ToString($inv) + ', "y": ' + $v[1].ToString($inv) + ', "w": ' + ($v[2] - $v[0]).ToString($inv) + ', "h": ' + ($v[3] - $v[1]).ToString($inv) + ', "alt": "..." }'
