# Erases rectangular regions (text, logos) from an image and fills them by continuing the surrounding gradient.
# Usage: clean_bg.ps1 -Src in.webp|png|jpg -Out out.png -Boxes "x0,y0,x1,y1;x0,y0,x1,y1"   (px of the source image)
# Rules: each box's top and bottom edges must sit on smooth background (not on text/photo detail);
#        merge boxes that touch or overlap into one; works best on gradients/sky, not on textured photo areas.
param([Parameter(Mandatory)][string]$Src, [Parameter(Mandatory)][string]$Out, [Parameter(Mandatory)][string]$Boxes)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationCore,WindowsBase
if (-not ('Fill' -as [type])) {
Add-Type -TypeDefinition @"
public static class Fill {
  // Replace box [x0,x1]x[y0,y1] by vertical interpolation between smoothed boundary rows.
  public static void Box(byte[] b, int stride, int w, int h, int x0, int y0, int x1, int y1, int rad) {
    int n = x1 - x0 + 1;
    double[,] top = Row(b, stride, w, x0, x1, y0 - 3, y0 - 1, rad);
    double[,] bot = Row(b, stride, w, x0, x1, y1 + 1, y1 + 3, rad);
    System.Random rnd = new System.Random(7);
    for (int y = y0; y <= y1; y++) {
      double t = (double)(y - y0 + 1) / (y1 - y0 + 2);
      t = t * t * (3 - 2 * t) * 0.5 + t * 0.5;
      for (int i = 0; i < n; i++) {
        int x = x0 + i; int p = y * stride + x * 4;
        double e = System.Math.Min(i, n - 1 - i) / 12.0; if (e > 1) e = 1;   // feather left/right edges
        for (int c = 0; c < 3; c++) {
          double v = top[i, c] * (1 - t) + bot[i, c] * t + (rnd.NextDouble() - 0.5) * 1.6;
          v = v * e + b[p + c] * (1 - e);
          b[p + c] = (byte)System.Math.Max(0, System.Math.Min(255, System.Math.Round(v)));
        }
      }
    }
  }
  static double[,] Row(byte[] b, int stride, int w, int x0, int x1, int ya, int yb, int rad) {
    int n = x1 - x0 + 1; double[,] raw = new double[n, 3]; double[,] o = new double[n, 3];
    for (int i = 0; i < n; i++) for (int c = 0; c < 3; c++) { double s = 0; for (int y = ya; y <= yb; y++) s += b[y * stride + (x0 + i) * 4 + c]; raw[i, c] = s / (yb - ya + 1); }
    for (int i = 0; i < n; i++) for (int c = 0; c < 3; c++) { double s = 0; int k = 0; for (int j = i - rad; j <= i + rad; j++) { if (j < 0 || j >= n) continue; s += raw[j, c]; k++; } o[i, c] = s / k; }
    return o;
  }
}
"@
}
$fs = [IO.File]::OpenRead((Resolve-Path $Src).Path)
$dec = [Windows.Media.Imaging.BitmapDecoder]::Create($fs, 'PreservePixelFormat', 'OnLoad'); $f = $dec.Frames[0]; $fs.Close()
$cv = New-Object Windows.Media.Imaging.FormatConvertedBitmap($f, [Windows.Media.PixelFormats]::Bgra32, $null, 0)
$w = $cv.PixelWidth; $h = $cv.PixelHeight; $stride = $w * 4
$buf = New-Object byte[] ($stride * $h); $cv.CopyPixels($buf, $stride, 0)
foreach ($spec in $Boxes.Split(';')) {
  if (-not $spec.Trim()) { continue }
  $v = [int[]]($spec.Split(',') | ForEach-Object { $_.Trim() })
  if ($v[1] -lt 3 -or $v[3] -gt $h - 4) { throw "box $spec too close to the image edge (needs 3 px of background above and below)" }
  [Fill]::Box($buf, $stride, $w, $h, $v[0], $v[1], $v[2], $v[3], 8)
}
$bmp = [Windows.Media.Imaging.BitmapSource]::Create($w, $h, 96, 96, [Windows.Media.PixelFormats]::Bgra32, $null, $buf, $stride)
$enc = New-Object Windows.Media.Imaging.PngBitmapEncoder; $enc.Frames.Add([Windows.Media.Imaging.BitmapFrame]::Create($bmp))
$o = [IO.File]::Create($Out); $enc.Save($o); $o.Close()
"OK $Out ($w x $h)"
