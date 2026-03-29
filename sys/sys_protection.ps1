# sys_protection.ps1
# Windows PowerShell script for project integrity and obstacle detection

$projectFolder = Split-Path -Parent $MyInvocation.MyCommand.Path
$logFile = Join-Path $projectFolder "sys_protection.log"

function Write-Log($m) {
    "$((Get-Date).ToString('s')) - $m" | Out-File -FilePath $logFile -Encoding utf8 -Append
}

Write-Log "Başlatıldı."

# 1) Kritik dosyalar var mı?
$required = @('auth\\main.py','app\\app.py','docs\\documentation.html','index.html')
$missing = @()
foreach ($f in $required) {
    if (-not (Test-Path (Join-Path $projectFolder $f))) { $missing += $f }
}
if ($missing.Count -gt 0) {
    Write-Log "Eksik kritik dosyalar: $($missing -join ', ')"
    Write-Host "Uyarı: eksik dosyalar: $($missing -join ', ')"
} else {
    Write-Log "Tüm kritik dosyalar bulundu."
}

# 2) Değişiklik izni olan bir yedekleme
$backupFolder = Join-Path $projectFolder "sys_backup"
if (-not (Test-Path $backupFolder)) { New-Item -ItemType Directory -Path $backupFolder | Out-Null }
Get-ChildItem -Path $projectFolder -Include '*.py','*.html','*.js' -Recurse | ForEach-Object {
    $dest = Join-Path $backupFolder $_.FullName.Substring($projectFolder.Length+1)
    $dir = Split-Path $dest -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
    Copy-Item -Path $_.FullName -Destination $dest -Force
}
Write-Log "Yedekleme tamamlandı: $backupFolder"

# 3) Kötü niyetli .exe dosyalarını tarama
$black = Get-ChildItem -Path $projectFolder -Include '*.exe','*.dll' -Recurse | ? { $_.Length -gt 1024KB }
if ($black) {
    Write-Log "Şüpheli ikili dosyalar bulundu: $($black.FullName -join ', ')"
    Write-Host "Uyarı: şüpheli ikili dosya bulundu. Loga bakın."
}

Write-Log "Tamamlandı."