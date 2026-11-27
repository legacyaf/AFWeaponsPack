# Steam Workshop cards: one 1920 x 1080 picture per weapon, the studio render with a stats panel on the right.
#   powershell -ExecutionPolicy Bypass -File workshop\make_cards.ps1 -Renders <folder with <tag>_studio_card.png>
# The renders come from blender\af_studio.py (shot "card"); the text from workshop\cards.json.
# Writes workshop\cards\<nn>_<tag>.jpg.
param([Parameter(Mandatory = $true)][string]$Renders)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$here = $PSScriptRoot
$out = Join-Path $here 'cards'
New-Item -ItemType Directory -Force $out | Out-Null
$data = Get-Content (Join-Path $here 'cards.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$W = 1920; $H = 1080; $PanelX = 1385                      # the panel starts here; text from $PanelX + 56

function New-Font([string]$name, [float]$size, [System.Drawing.FontStyle]$style = 'Regular') {
    New-Object System.Drawing.Font($name, $size, $style, [System.Drawing.GraphicsUnit]::Pixel)
}
$orange = [System.Drawing.Color]::FromArgb(255, 240, 138, 30)
$white  = [System.Drawing.Color]::FromArgb(255, 240, 240, 236)
$grey   = [System.Drawing.Color]::FromArgb(255, 150, 152, 156)
$fTitle = New-Font 'Bahnschrift SemiBold Condensed' 74
$fKind  = New-Font 'Bahnschrift Light' 27
$fLabel = New-Font 'Bahnschrift SemiBold' 17
$fValue = New-Font 'Bahnschrift' 25
$fFeat  = New-Font 'Bahnschrift Light' 22
$fPack  = New-Font 'Bahnschrift SemiBold' 17
$jpeg = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object MimeType -eq 'image/jpeg'
$quality = New-Object System.Drawing.Imaging.EncoderParameters 1
$quality.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, [long]93)

function Draw-Spaced($g, [string]$text, $font, $brush, [float]$x, [float]$y, [float]$gap) {
    # Letter-spaced capitals (GDI+ has no tracking).
    foreach ($ch in $text.ToCharArray()) {
        $g.DrawString([string]$ch, $font, $brush, $x, $y, [System.Drawing.StringFormat]::GenericTypographic)
        $x += $g.MeasureString([string]$ch, $font, 1000, [System.Drawing.StringFormat]::GenericTypographic).Width + $gap
        if ($ch -eq ' ') { $x += $font.Size * 0.28 }
    }
}

function Fit-Font($g, [string]$text, [string]$name, [float]$size, [float]$maxWidth) {
    do {
        $f = New-Font $name $size
        $w = $g.MeasureString($text, $f, 4000, [System.Drawing.StringFormat]::GenericTypographic).Width
        if ($w -le $maxWidth) { return $f }
        $f.Dispose(); $size -= 2
    } while ($size -gt 20)
    return (New-Font $name 20)
}

$n = 0
foreach ($card in $data.cards) {
    $n++
    $src = Join-Path $Renders "$($card.tag)_studio_card.png"
    if (-not (Test-Path $src)) { "missing render: $src"; continue }
    $img = [System.Drawing.Image]::FromFile($src)
    $bmp = New-Object System.Drawing.Bitmap $W, $H
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = 'AntiAlias'; $g.InterpolationMode = 'HighQualityBicubic'
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
    $g.DrawImage($img, 0, 0, $W, $H)
    $img.Dispose()

    # Cinema bars of shade top and bottom, and the stage falling to black under the panel.
    foreach ($band in @(@(0, 150, 150, 0), @(($H - 190), 190, 0, 170))) {
        $r = New-Object System.Drawing.Rectangle 0, $band[0], $W, $band[1]
        $b = New-Object System.Drawing.Drawing2D.LinearGradientBrush($r, [System.Drawing.Color]::FromArgb($band[2], 0, 0, 0), [System.Drawing.Color]::FromArgb($band[3], 0, 0, 0), 90.0)
        $b.WrapMode = 'TileFlipXY'; $g.FillRectangle($b, $r); $b.Dispose()
    }
    $fade = New-Object System.Drawing.Rectangle ($PanelX - 240), 0, 241, $H
    $b = New-Object System.Drawing.Drawing2D.LinearGradientBrush($fade, [System.Drawing.Color]::FromArgb(0, 6, 7, 9), [System.Drawing.Color]::FromArgb(236, 6, 7, 9), 0.0)
    $b.WrapMode = 'TileFlipXY'; $g.FillRectangle($b, $fade); $b.Dispose()
    $b = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(236, 6, 7, 9))
    $g.FillRectangle($b, $PanelX, 0, ($W - $PanelX), $H); $b.Dispose()

    $bo = New-Object System.Drawing.SolidBrush $orange
    $bw = New-Object System.Drawing.SolidBrush $white
    $bg = New-Object System.Drawing.SolidBrush $grey
    $x = $PanelX + 56; $maxW = $W - $x - 60
    $y = 84
    $g.FillRectangle($bo, $x, $y, 64, 5)
    $y += 26
    Draw-Spaced $g $data.pack $fPack $bg $x $y 2.4
    $y += 40
    $ft = Fit-Font $g $card.name 'Bahnschrift SemiBold Condensed' 74 $maxW
    $g.DrawString($card.name, $ft, $bw, ($x - 3), $y, [System.Drawing.StringFormat]::GenericTypographic)
    $y += $ft.Size + 18; $ft.Dispose()
    $g.DrawString($card.kind, $fKind, $bo, $x, $y, [System.Drawing.StringFormat]::GenericTypographic)
    $y += 52

    $pen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(70, 255, 255, 255)), 1
    $rect = New-Object System.Drawing.StringFormat ([System.Drawing.StringFormat]::GenericTypographic)
    foreach ($row in $card.stats) {
        $g.DrawLine($pen, $x, $y, ($x + $maxW), $y)
        $y += 11
        $cols = [int]($row.Count / 2); $colW = ($maxW - 24 * ($cols - 1)) / $cols; $rowH = 0
        for ($c = 0; $c -lt $cols; $c++) {
            $cx = $x + $c * ($colW + 24)
            Draw-Spaced $g $row[2 * $c].ToUpper() $fLabel $bg $cx $y 1.6
            $size = $g.MeasureString($row[2 * $c + 1], $fValue, [int]$colW, $rect)
            $g.DrawString($row[2 * $c + 1], $fValue, $bw, (New-Object System.Drawing.RectangleF $cx, ($y + 24), $colW, ($size.Height + 4)), $rect)
            if ($size.Height -gt $rowH) { $rowH = $size.Height }
        }
        $y += 24 + $rowH + 11
    }
    $g.DrawLine($pen, $x, $y, ($x + $maxW), $y)
    $y += 24
    foreach ($f in $card.features) {
        $g.FillRectangle($bo, $x, ($y + 10), 9, 9)
        $size = $g.MeasureString($f, $fFeat, [int]($maxW - 26), $rect)
        $g.DrawString($f, $fFeat, $bw, (New-Object System.Drawing.RectangleF ($x + 26), $y, ($maxW - 26), ($size.Height + 4)), $rect)
        $y += $size.Height + 9
    }
    Draw-Spaced $g ('SPAWNS: ' + $card.loot.ToUpper()) $fLabel $bg $x ($H - 66) 1.4

    $file = Join-Path $out ('{0:d2}_{1}.jpg' -f $n, $card.tag)
    $bmp.Save($file, $jpeg, $quality)
    $pen.Dispose(); $bo.Dispose(); $bw.Dispose(); $bg.Dispose(); $g.Dispose(); $bmp.Dispose()
    "wrote $file"
}
