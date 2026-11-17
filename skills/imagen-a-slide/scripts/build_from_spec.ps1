# imagen-a-slide engine: builds editable slides (.pptx + .png renders) from a JSON spec using desktop PowerPoint (COM).
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File build_from_spec.ps1 -Spec slide.json
# Safety: PowerPoint is single-instance, COM attaches to the USER's PowerPoint. This script only closes the deck it
#         creates (and the chart workbooks it opens). It never calls Quit() and never kills processes.
param([Parameter(Mandatory)][string]$Spec)
$ErrorActionPreference = 'Stop'
[Threading.Thread]::CurrentThread.CurrentCulture = [Globalization.CultureInfo]::InvariantCulture

$specPath = (Resolve-Path $Spec).Path
$base = Split-Path -Parent $specPath
$skillDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$S = [IO.File]::ReadAllText($specPath, [Text.Encoding]::UTF8) | ConvertFrom-Json

function Prop($o, [string]$n, $d = $null) { if ($null -ne $o -and $null -ne $o.PSObject.Properties[$n]) { return $o.$n } return $d }
# Optional client profile (kept OUTSIDE this skill): spec "profile" or env IMAGEN_A_SLIDE_PROFILE -> perfil.json
#   { "name": "...", "logos": "assets/logos", "theme": { "font", "headFont", "text", "bg" } }
#   Its logos are searched first for @logos/<file>; its theme fills whatever the spec theme does not set.
$PRF = $null; $PRFDIR = $null
$pp = Prop $S 'profile' $env:IMAGEN_A_SLIDE_PROFILE
if ($pp) {
  if (-not [IO.Path]::IsPathRooted($pp)) { $pp = Join-Path $base $pp }
  if (-not (Test-Path -LiteralPath $pp)) { throw "profile not found: $pp" }
  $pp = (Resolve-Path -LiteralPath $pp).Path; $PRFDIR = Split-Path -Parent $pp
  $PRF = [IO.File]::ReadAllText($pp, [Text.Encoding]::UTF8) | ConvertFrom-Json
  $pt = Prop $PRF 'theme'
  if ($pt) {
    if ($null -eq (Prop $S 'theme')) { $S | Add-Member -NotePropertyName theme -NotePropertyValue ([pscustomobject]@{}) }
    foreach ($q in $pt.PSObject.Properties) { if ($null -eq (Prop $S.theme $q.Name)) { $S.theme | Add-Member -NotePropertyName $q.Name -NotePropertyValue $q.Value } }
  }
}
function PathOf([string]$p) {
  if ($p.StartsWith('@logos/')) {
    $name = $p.Substring(7)
    if ($PRF) { $c = Join-Path (Join-Path $PRFDIR (Prop $PRF 'logos' 'logos')) $name; if (Test-Path -LiteralPath $c) { return $c } }
    $c = Join-Path $skillDir ('assets\logos\' + $name); if (Test-Path -LiteralPath $c) { return $c }
    throw "logo not found: $p (looked in the profile logos folder and in the skill's assets\logos)"
  }
  if ([IO.Path]::IsPathRooted($p)) { return $p } return Join-Path $base $p
}
function C([string]$hex) { $hex = $hex.TrimStart('#'); return [Convert]::ToInt32($hex.Substring(0,2),16) + 256*[Convert]::ToInt32($hex.Substring(2,2),16) + 65536*[Convert]::ToInt32($hex.Substring(4,2),16) }
function Tri($b) { if ($b) { return -1 } return 0 }
$k = 960.0 / [double](Prop $S 'sourceWidth' 2000)          # source px -> pt (slide is 960 x 540 pt)
function U($v) { return [single]([double]$v * $k) }
$THEME = Prop $S 'theme'
$FONT = Prop $S 'font' (Prop $THEME 'font' 'Segoe UI')
$TEXTC = Prop $THEME 'text' '374151'
$tmp = Join-Path $env:TEMP ('spec_' + [guid]::NewGuid().ToString('N')); New-Item -ItemType Directory -Force $tmp | Out-Null
$utf8 = New-Object Text.UTF8Encoding($false)
$doubts = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]

$SHAPES = @{ rect = 1; parallelogram = 2; trapezoid = 3; diamond = 4; roundRect = 5; octagon = 6; triangle = 7; rtTriangle = 8
  ellipse = 9; hexagon = 10; plus = 11; regularPentagon = 12; can = 13; cube = 14; donut = 18; rightArrow = 33; leftArrow = 34
  upArrow = 35; downArrow = 36; leftRightArrow = 37; homePlate = 51; pentagon = 51; chevron = 52; flowChartProcess = 61
  flowChartDecision = 63; flowChartTerminator = 69; star5 = 92; cloud = 179 }
$ARROWS = @{ none = 1; triangle = 2; open = 3; arrow = 3; stealth = 4; diamond = 5; oval = 6 }
$DASH = @{ solid = 1; squareDot = 2; dot = 3; dash = 4; dashDot = 5; longDash = 7 }
$CHARTS = @{ 'bar-col' = 51; 'bar-col-stacked' = 52; 'bar-bar' = 57; 'bar-bar-stacked' = 58; 'line' = 4; 'line-markers' = 65
  'pie' = 5; 'doughnut' = -4120; 'area' = 1; 'scatter' = -4169 }

function Set-Text($shape, $e) {
  $tf = $shape.TextFrame
  $m = [single](Prop $e 'margin' 0); $tf.MarginLeft = $m; $tf.MarginRight = $m; $tf.MarginTop = $m; $tf.MarginBottom = $m
  $align = @{ left = 1; center = 2; right = 3; justify = 4 }[[string](Prop $e 'align' 'left')]
  $tf.WordWrap = Tri ((Prop $e 'wrap' $false) -or $align -ne 1)
  $paras = Prop $e 'paragraphs'
  if (-not $paras) { $paras = @([pscustomobject]@{ text = $e.text }) }
  $tf.TextRange.Text = (($paras | ForEach-Object { ([string]$_.text) -replace "`n", [string][char]11 }) -join "`r")
  $tr = $tf.TextRange
  $role = Prop $e 'role'
  $tr.Font.Name = (Prop $e 'font' $(if ($role -in 'title', 'subtitle') { Prop $THEME 'headFont' $FONT } else { $FONT }))
  $tr.Font.Size = [single](Prop $e 'size' 12)
  $tr.Font.Color.RGB = (C (Prop $e 'color' $TEXTC)); $tr.Font.Bold = Tri (Prop $e 'bold' $false); $tr.Font.Italic = Tri (Prop $e 'italic' $false)
  $tr.ParagraphFormat.Alignment = $align
  $tr.ParagraphFormat.Bullet.Visible = 0
  $ls = Prop $e 'lineSpacing'; if ($ls) { $tr.ParagraphFormat.LineRuleWithin = 0; $tr.ParagraphFormat.SpaceWithin = [single]$ls }
  $sa = Prop $e 'spaceAfter'; if ($sa) { $tr.ParagraphFormat.SpaceAfter = [single]$sa }
  $cs = Prop $e 'charSpacing'; if ($null -ne $cs) { $shape.TextFrame2.TextRange.Font.Spacing = [single]$cs }
  $pi = 0
  foreach ($p in $paras) {
    $pi++; $pr = $tr.Paragraphs($pi)
    if (Prop $p 'size') { $pr.Font.Size = [single]$p.size }
    if ($null -ne (Prop $p 'bold')) { $pr.Font.Bold = Tri $p.bold }
    if ($null -ne (Prop $p 'italic')) { $pr.Font.Italic = Tri $p.italic }
    if (Prop $p 'color') { $pr.Font.Color.RGB = (C $p.color) }
    if (Prop $p 'align') { $pr.ParagraphFormat.Alignment = @{ left = 1; center = 2; right = 3 }[[string]$p.align] }
    $b = Prop $p 'bullet'
    if ($b) {
      $pr.ParagraphFormat.Bullet.Visible = -1
      if ($b -is [string] -and $b -eq 'number') { $pr.ParagraphFormat.Bullet.Type = 2 }
      else { $pr.ParagraphFormat.Bullet.Type = 1; $pr.ParagraphFormat.Bullet.Character = 8226 }
      $pr.IndentLevel = [int](Prop $p 'level' 0) + 1
    }
  }
  foreach ($run in @(Prop $e 'runs' @())) {
    $txt = [string]$run.match; $start = 0; $all = [bool](Prop $run 'all' $false); $found = $false
    while ($true) {
      $idx = $tr.Text.IndexOf($txt, $start); if ($idx -lt 0) { break }
      $found = $true; $len = $txt.Length; $cr = $tr.Characters($idx + 1, $len)
      if ($null -ne (Prop $run 'bold')) { $cr.Font.Bold = Tri $run.bold }
      if ($null -ne (Prop $run 'italic')) { $cr.Font.Italic = Tri $run.italic }
      if ($null -ne (Prop $run 'underline')) { $cr.Font.Underline = Tri $run.underline }
      if (Prop $run 'color') { $cr.Font.Color.RGB = (C $run.color) }
      if (Prop $run 'size') { $cr.Font.Size = [single]$run.size }
      $g = Prop $run 'gradient'
      if ($g) {
        # PowerPoint spreads a text gradient over the whole text box: pin the stops to where the word actually is
        $c2 = $shape.TextFrame2.TextRange.Characters($idx + 1, $len)
        $c2.Font.Fill.TwoColorGradient(2, 1); $c2.Font.Fill.ForeColor.RGB = (C $g[0]); $c2.Font.Fill.BackColor.RGB = (C $g[1])
        try {
          $p0 = [Math]::Max(0.0, [Math]::Min(1.0, ($c2.BoundLeft - $shape.Left) / $shape.Width))
          $p1 = [Math]::Max($p0, [Math]::Min(1.0, ($c2.BoundLeft + $c2.BoundWidth - $shape.Left) / $shape.Width))
          $gs = $c2.Font.Fill.GradientStops
          $gs.Item(1).Position = [single]$p0; $gs.Item($gs.Count).Position = [single]$p1
        } catch { $warnings.Add("gradient stops not pinned for '$txt': $($_.Exception.Message)") }
      }
      if (-not $all) { break }; $start = $idx + $len
    }
    if (-not $found) { $warnings.Add("run '$txt' not found in '$($shape.Name)'") }
  }
  $tf.AutoSize = 0
  $tf.VerticalAnchor = @{ top = 1; middle = 3; bottom = 4 }[[string](Prop $e 'anchor' (Prop $e 'valign' 'top'))]
}
function Set-Fill($sh, $e) {
  $fill = Prop $e 'fill'
  if ($fill) { $sh.Fill.Visible = -1; $sh.Fill.Solid(); $sh.Fill.ForeColor.RGB = (C $fill); $sh.Fill.Transparency = [single](Prop $e 'fillTransparency' 0) } else { $sh.Fill.Visible = 0 }
  $ln = Prop $e 'line'
  if ($ln) {
    if ($ln -is [string]) { $lc = $ln; $lw = Prop $e 'lineWidth' 1; $ld = 'solid' } else { $lc = Prop $ln 'color' '000000'; $lw = Prop $ln 'width' 1; $ld = Prop $ln 'dash' 'solid' }
    $sh.Line.Visible = -1; $sh.Line.ForeColor.RGB = (C $lc); $sh.Line.Weight = [single]$lw; $sh.Line.DashStyle = $DASH[[string]$ld]
  } else { $sh.Line.Visible = 0 }
  if (Prop $e 'shadow' $false) { $sh.Shadow.Visible = -1; $sh.Shadow.OffsetX = 0; $sh.Shadow.OffsetY = 2; $sh.Shadow.Blur = 10; $sh.Shadow.ForeColor.RGB = (C '1E3A8A'); $sh.Shadow.Transparency = [single]0.9 } else { $sh.Shadow.Visible = 0 }
}
function Add-Table($sl, $e, $name) {
  $rows = @($e.rows); $nr = $rows.Count; $nc = @($rows[0]).Count
  $sh = $sl.Shapes.AddTable($nr, $nc, (U $e.x), (U $e.y), (U $e.w), (U $e.h)); $sh.Name = $name
  $tb = $sh.Table
  try { $tb.ApplyStyle('{2D5ABB26-0587-4C30-8999-92F81FD0307C}', $false) } catch { }   # "No Style, No Grid"
  $colW = Prop $e 'colW'; if ($colW) { for ($c = 1; $c -le $nc; $c++) { $tb.Columns($c).Width = (U $colW[$c - 1]) } }
  $hdr = Prop $e 'header'; $bd = Prop $e 'border'
  for ($r = 1; $r -le $nr; $r++) {
    for ($c = 1; $c -le $nc; $c++) {
      $v = @($rows[$r - 1])[$c - 1]; $cell = $tb.Cell($r, $c); $csh = $cell.Shape
      $cellSpec = if ($v -is [string] -or $v -is [ValueType]) { [pscustomobject]@{ text = [string]$v } } else { $v }
      $tr = $csh.TextFrame.TextRange; $tr.Text = [string](Prop $cellSpec 'text' '')
      $tr.Font.Name = $FONT; $tr.Font.Size = [single](Prop $cellSpec 'size' (Prop $e 'size' 12))
      $isH = ($r -eq 1 -and $hdr)
      $tr.Font.Color.RGB = (C (Prop $cellSpec 'color' $(if ($isH) { Prop $hdr 'color' 'FFFFFF' } else { Prop $e 'color' $TEXTC })))
      $tr.Font.Bold = Tri (Prop $cellSpec 'bold' $(if ($isH) { Prop $hdr 'bold' $true } else { $false }))
      $tr.ParagraphFormat.Alignment = @{ left = 1; center = 2; right = 3 }[[string](Prop $cellSpec 'align' (Prop $e 'align' 'left'))]
      $csh.TextFrame.VerticalAnchor = 3
      $f = Prop $cellSpec 'fill' $(if ($isH) { Prop $hdr 'fill' } else { Prop $e 'fill' })
      if ($f) { $csh.Fill.Visible = -1; $csh.Fill.Solid(); $csh.Fill.ForeColor.RGB = (C $f) } else { $csh.Fill.Visible = 0 }
      if ($bd) { foreach ($side in 1, 2, 3, 4) { $b = $cell.Borders($side); $b.Visible = -1; $b.ForeColor.RGB = (C (Prop $bd 'color' 'CBD5E1')); $b.Weight = [single](Prop $bd 'width' 1) } }
    }
  }
  $rh = (U $e.h) / $nr; for ($r = 1; $r -le $nr; $r++) { $tb.Rows($r).Height = $rh }
}
function Add-Chart($sl, $e, $name) {
  $key = [string](Prop $e 'chartType' 'bar'); if ($key -eq 'bar') { $key = 'bar-' + (Prop $e 'dir' 'col') + $(if (Prop $e 'stacked' $false) { '-stacked' } else { '' }) }
  if ($key -eq 'line' -and (Prop $e 'markers' $false)) { $key = 'line-markers' }
  $type = $CHARTS[$key]; if ($null -eq $type) { throw "chartType '$key' not supported" }
  # AddChart2 started returning E_FAIL after the Office update of 2026-11-13 (16.0.20527); try the variants in order
  $sh = $null; $errs = @()
  $tries = @(
    @{ n = 'AddChart2'; f = { $sl.Shapes.AddChart2(-1, $type, (U $e.x), (U $e.y), (U $e.w), (U $e.h), $true) } },
    @{ n = 'AddChart2-noLayout'; f = { $sl.Shapes.AddChart2(-1, $type, (U $e.x), (U $e.y), (U $e.w), (U $e.h)) } },
    @{ n = 'AddChart'; f = { $sl.Shapes.AddChart($type, (U $e.x), (U $e.y), (U $e.w), (U $e.h)) } })
  foreach ($t in $tries) {
    try { $sh = & $t.f; if ($t.n -ne 'AddChart2') { $warnings.Add("chart '$name' created with $($t.n) (AddChart2 failed)") }; break }
    catch { $errs += "$($t.n): $($_.Exception.Message)" }
  }
  if ($null -eq $sh) { throw ("chart '$name' could not be created. " + ($errs -join ' | ')) }
  $sh.Name = $name
  $series = @($e.series); $labels = @($series[0].labels)
  $want = (@($series[0].values) | ForEach-Object { [double]$_ }) -join ';'
  # With a cold Excel the first chart can silently keep Excel's sample data: read the values back and retry
  for ($round = 1; $round -le 3; $round++) {
    $sh.Chart.ChartData.Activate(); $wb = $null
    for ($w = 0; $w -lt 20 -and $null -eq $wb; $w++) { try { $wb = $sh.Chart.ChartData.Workbook } catch { }; if ($null -eq $wb) { Start-Sleep -Milliseconds 300 } }
    if ($null -eq $wb) { throw "chart '$name': Excel workbook not available (is Excel installed?)" }
    try {
      try { $wb.Application.Visible = $false } catch { }
      $ws = $wb.Worksheets(1); $ws.Cells.Clear()
      for ($i = 0; $i -lt $labels.Count; $i++) { $ws.Cells($i + 2, 1).Value2 = [string]$labels[$i] }
      for ($s = 0; $s -lt $series.Count; $s++) {
        $ws.Cells(1, $s + 2).Value2 = [string]$series[$s].name
        $vals = @($series[$s].values); for ($i = 0; $i -lt $vals.Count; $i++) { $ws.Cells($i + 2, $s + 2).Value2 = [double]$vals[$i] }
      }
      $last = $ws.Cells($labels.Count + 1, $series.Count + 1).Address($false, $false)
      $sh.Chart.SetSourceData("='" + $ws.Name + "'!A1:" + $last)
    } finally { $wb.Close() }
    $got = ''; try { $got = (@($sh.Chart.SeriesCollection(1).Values) | ForEach-Object { [double]$_ }) -join ';' } catch { }
    if ($got -eq $want) { break }
    if ($round -eq 3) { throw "chart '$name': data did not reach the chart (expected $want, got $got)" }
    $warnings.Add("chart '$name': data not applied on try $round (got $got), retrying"); Start-Sleep -Milliseconds 800
  }
  $ch = $sh.Chart
  $title = Prop $e 'title'; $ch.HasTitle = [bool]$title; if ($title) { $ch.ChartTitle.Text = [string]$title }
  $ch.HasLegend = [bool](Prop $e 'showLegend' ($series.Count -gt 1))
  $cols = @(Prop $e 'colors' @())
  for ($s = 1; $s -le $ch.SeriesCollection().Count; $s++) {
    $se = $ch.SeriesCollection($s)
    if ($key -in 'pie', 'doughnut') { for ($p = 1; $p -le $labels.Count -and $p -le $cols.Count; $p++) { $se.Points($p).Format.Fill.ForeColor.RGB = (C $cols[$p - 1]) } }
    elseif ($cols.Count -ge $s) { $se.Format.Fill.ForeColor.RGB = (C $cols[$s - 1]); $se.Format.Line.ForeColor.RGB = (C $cols[$s - 1]) }
    if (Prop $e 'showValue' $false) { $se.HasDataLabels = $true; $nf = Prop $e 'valueFormat'; if ($nf) { $se.DataLabels().NumberFormat = [string]$nf } }
  }
  try { $ch.ChartArea.Format.TextFrame2.TextRange.Font.Name = $FONT } catch { }
  if (Prop $e 'estimated' $false) { $doubts.Add("$name : valores estimados midiendo el grafico, revisar cifras") }
}

function Build-Slide($pres, $idx, $SD) {
  $sl = $pres.Slides.Add($idx, 12)
  $sl.FollowMasterBackground = 0
  $bg = Prop $SD 'background'
  if (Prop $bg 'image') { $sl.Background.Fill.UserPicture((PathOf $bg.image)) }
  else { $sl.Background.Fill.Solid(); $sl.Background.Fill.ForeColor.RGB = (C (Prop $bg 'color' (Prop $THEME 'bg' 'FFFFFF'))) }
  $groups = @{}; $i = 0
  foreach ($e in @($SD.elements)) {
    $i++; $name = Prop $e 'name' (Prop $e 'id' "$($e.type) $i"); $sh = $null
    $t = [string](Prop $e 'type' (Prop $e 'kind' ''))
    switch ($t) {
      { $_ -in 'rect', 'shape' } {
        $kind = [string](Prop $e 'shape' $(if ([double](Prop $e 'radius' 0) -gt 0) { 'roundRect' } else { 'rect' }))
        $id = $SHAPES[$kind]; if ($null -eq $id) { $warnings.Add("shape '$kind' unknown in '$name', using rect"); $id = 1 }
        $sh = $sl.Shapes.AddShape($id, (U $e.x), (U $e.y), (U $e.w), (U $e.h))
        $r = Prop $e 'radius'; if ($null -ne $r -and $id -eq 5) { $sh.Adjustments.Item(1) = [single]$r }
        Set-Fill $sh $e
        $inner = Prop $e 'textBox'
        if ($inner) { Set-Text $sh $inner } elseif ((Prop $e 'text') -or (Prop $e 'paragraphs')) { Set-Text $sh $e } else { $sh.TextFrame.TextRange.Text = '' }
      }
      'line' {
        $sh = $sl.Shapes.AddLine((U $e.x1), (U $e.y1), (U $e.x2), (U $e.y2))
        $sh.Line.ForeColor.RGB = (C (Prop $e 'color' $TEXTC)); $sh.Line.Weight = [single](Prop $e 'width' 1.25)
        $sh.Line.DashStyle = $DASH[[string](Prop $e 'dash' 'solid')]
        $sh.Line.BeginArrowheadStyle = $ARROWS[[string](Prop $e 'beginArrow' 'none')]
        $sh.Line.EndArrowheadStyle = $ARROWS[[string](Prop $e 'endArrow' 'none')]
      }
      { $_ -in 'picture', 'svg', 'image' } {
        if ($t -eq 'svg') { $p = Join-Path $tmp "$idx-$i.svg"; [IO.File]::WriteAllText($p, [string]$e.svg, $utf8) } else { $p = PathOf (Prop $e 'path' (Prop $e 'src')) }
        $sh = $sl.Shapes.AddPicture($p, 0, -1, (U $e.x), (U $e.y), -1, -1)
        $sh.LockAspectRatio = -1
        if (Prop $e 'h') { $sh.LockAspectRatio = 0; $sh.Width = (U $e.w); $sh.Height = (U $e.h) } else { $sh.Width = (U $e.w) }
        $sh.Left = (U $e.x); $sh.Top = (U $e.y)
        if (($sh.Width * $sh.Height) -gt (0.8 * 960 * 540)) { $warnings.Add("'$name' covers >80% of the slide: only acceptable as a clean background without text") }
      }
      'text' {
        $sh = $sl.Shapes.AddTextbox(1, (U $e.x), (U $e.y), (U $e.w), (U $e.h))
        Set-Text $sh $e
        $f = Prop $e 'fill'; if ($f) { $sh.Fill.Visible = -1; $sh.Fill.Solid(); $sh.Fill.ForeColor.RGB = (C $f) }
      }
      'table' { Add-Table $sl $e $name; $sh = $sl.Shapes.Item($name) }
      'chart' { Add-Chart $sl $e $name; $sh = $sl.Shapes.Item($name) }
      default { $warnings.Add("unknown element type '$t' ($name)"); continue }
    }
    $sh.Name = $name
    if ($t -in 'text', 'rect', 'shape') { $sh.Top = (U $e.y); $sh.Height = (U $e.h) }
    $rot = Prop $e 'rotate'; if ($rot) { $sh.Rotation = [single]$rot }
    $alt = Prop $e 'alt'; if ($alt) { $sh.AlternativeText = [string]$alt }
    $conf = Prop $e 'confidence'; if ($null -ne $conf -and [double]$conf -lt 0.7) { $doubts.Add("diapositiva $idx / $name : confianza $conf") }
    $g = Prop $e 'group'; if ($g) { if (-not $groups.ContainsKey($g)) { $groups[$g] = New-Object System.Collections.Generic.List[string] }; $groups[$g].Add($name) }
  }
  foreach ($g in $groups.Keys) { if ($groups[$g].Count -gt 1) { $grp = $sl.Shapes.Range([string[]]$groups[$g].ToArray()).Group(); $grp.Name = [string]$g } }
  $notes = Prop $SD 'notes'; if ($notes) { $sl.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text = [string]$notes }
  foreach ($d in @(Prop $SD 'doubts' @())) { $doubts.Add("diapositiva $idx : $d") }
  return $sl
}

$ppt = New-Object -ComObject PowerPoint.Application
$before = $ppt.Presentations.Count
$slidesSpec = Prop $S 'slides'; if (-not $slidesSpec) { $slidesSpec = @($S) }
$attempt = 0; $saved = $null; $pngs = @()
try {
while (-not $saved) {
  $attempt++; $pres = $null
  try {
    # Charts need a document window since Office 16.0.20527 (windowless -> AddChart2 E_FAIL): open it minimized
    $hasChart = [bool](@($slidesSpec | ForEach-Object { @(Prop $_ 'elements' @()) } | Where-Object { (Prop $_ 'type') -eq 'chart' }).Count)
    if ($hasChart) { $pres = $ppt.Presentations.Add(-1); try { $pres.Windows(1).WindowState = 2 } catch { } } else { $pres = $ppt.Presentations.Add(0) }
    $pres.PageSetup.SlideWidth = 960; $pres.PageSetup.SlideHeight = 540
    $n = 0; foreach ($SD in @($slidesSpec)) { $n++; Build-Slide $pres $n $SD | Out-Null }
    $built = @(); for ($j = 1; $j -le $n; $j++) { $built += $pres.Slides($j) }
    $out = PathOf $S.output
    $stem = [IO.Path]::Combine([IO.Path]::GetDirectoryName($out), [IO.Path]::GetFileNameWithoutExtension($out))
    $v = 1
    while (-not $saved) {
      $try = $(if ($v -eq 1) { $out } else { "${stem}_v$v.pptx" })
      try { $pres.SaveAs($try); $saved = $try } catch { if ($_.Exception.Message -match 'in use|en uso|currently|can.t modify|no puede') { $v++; if ($v -gt 20) { throw } } else { throw } }
    }
    $pngs = @()
    for ($j = 1; $j -le $built.Count; $j++) {
      $png = $(if ($built.Count -eq 1 -and (Prop $S 'png')) { PathOf $S.png } elseif ($built.Count -eq 1) { "$stem.png" } else { "${stem}_s$j.png" })
      $built[$j - 1].Export($png, 'PNG', 2000, 1125); $pngs += $png
    }
  } catch {
    $hr = $_.Exception.HResult
    if ($attempt -lt 4 -and ($hr -eq -2147418111 -or $hr -eq -2147417846)) { Write-Warning "PowerPoint ocupado, reintento $attempt"; Start-Sleep -Seconds (3 * $attempt); $saved = $null }
    else { throw }
  } finally { if ($pres) { $pres.Close() } }
}
} finally {
  Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
  if (-not $saved) { Write-Host "presentaciones abiertas antes=$before despues=$($ppt.Presentations.Count)" }
}
if ($doubts.Count -gt 0) { $dm = [IO.Path]::ChangeExtension($saved, $null).TrimEnd('.') + '_dudas.md'; [IO.File]::WriteAllText($dm, "# Dudas a revisar`r`n`r`n" + (($doubts | ForEach-Object { "- $_" }) -join "`r`n"), $utf8) }
foreach ($w in $warnings) { Write-Warning $w }
"OK pptx=$saved"
"png=" + ($pngs -join ' ; ')
if ($doubts.Count -gt 0) { "dudas=$($doubts.Count) (ver _dudas.md)" }
"presentaciones abiertas antes=$before despues=$($ppt.Presentations.Count)"
