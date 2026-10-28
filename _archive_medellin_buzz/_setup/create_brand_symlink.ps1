# Medellin Buzz Shorts - link the brand assets from Alejo's long-form kit (one source of truth).
#
# Run ONCE, in PowerShell opened as Administrator:
#   powershell -ExecutionPolicy Bypass -File "E:\FRANCO\MEDELLIN_BUZZ_SHORTS\_setup\create_brand_symlink.ps1"
#
# Alejo's kit has no single "brand" folder. The brand lives in two places, so brand\ is a real
# folder holding two directory symlinks:
#   brand\fonts -> ...\CLAUDE\tools\fonts      (Poppins ExtraBold/SemiBold/Medium, Lora Italic, Playfair Display + OFL licenses)
#   brand\marca -> ...\CLAUDE\activos\marca    (official end banner PNG + banner_oficial.json registry with sha256)
#
# Nothing in Alejo's kit is copied, moved or modified. Removing a link (Remove-Item on the link)
# never touches the target folder.

$ErrorActionPreference = 'Stop'

$shorts = 'E:\FRANCO\MEDELLIN_BUZZ_SHORTS'
$alejo  = 'E:\FRANCO\MEDELLIN_BUZZ CLAUDE KIT\CLAUDE'

$links = [ordered]@{
    "$shorts\brand\fonts" = "$alejo\tools\fonts"
    "$shorts\brand\marca" = "$alejo\activos\marca"
}

New-Item -ItemType Directory -Force -Path "$shorts\brand" | Out-Null

foreach ($link in $links.Keys) {
    $target = $links[$link]
    if (-not (Test-Path -LiteralPath $target)) { throw "Target missing: $target" }
    if (Test-Path -LiteralPath $link) {
        $item = Get-Item -LiteralPath $link -Force
        if ($item.LinkType -eq 'SymbolicLink' -and $item.Target -eq $target) {
            Write-Host "OK (already linked): $link -> $target"
            continue
        }
        throw "Something already exists at $link and it is not the expected link. Look at it before re-running."
    }
    New-Item -ItemType SymbolicLink -Path $link -Target $target | Out-Null
    Write-Host "Linked: $link -> $target"
}

Write-Host ""
Get-ChildItem "$shorts\brand" -Force | Select-Object Name, LinkType, Target | Format-Table -AutoSize
