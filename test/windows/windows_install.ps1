<#
.SYNOPSIS
    Windows sistem kurulumu ve ortam hazırlığı.
.DESCRIPTION
    Bu script, Pester testleri, Python ve Node.js kurulumunu kontrol eder,
    gerekli paketleri kurar ve Windows koruma testlerini çalıştırmak için hazırlar.
#>

param(
    [string]$PesterReportDir = "test-results",
    [string]$PythonPath = "C:\Python39",
    [switch]$SkipPackageInstall
)

# 1) Sistem gereksinimi kontrolü
Write-Host "[INFO] Windows ortam kontrolü" -ForegroundColor Cyan
if (-not (Get-Command powershell.exe -ErrorAction SilentlyContinue)) {
    Write-Error "PowerShell bulinamadi."
    exit 1
}

# 2) Python kontrolü
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Warning "Python bulunamadi. Lutfen https://www.python.org/downloads/ adresinden kurun."
    exit 1
}
Write-Host "[INFO] Python bulundu: $($py.Source)" -ForegroundColor Green

if (-not $SkipPackageInstall) {
    py -m pip install --upgrade pip
    py -m pip install -r "$(Split-Path -Parent $MyInvocation.MyCommand.Path)\..\requirements.txt" -ErrorAction SilentlyContinue
    py -m pip install pytest pester2
}

# 3) Node.js kontrolü
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
    Write-Warning "Node.js bulunamadi. Lutfen https://nodejs.org/ adresinden kurun."
    exit 1
}
Write-Host "[INFO] Node.js bulundu: $($node.Source)" -ForegroundColor Green

npm install --silent

# 4) Pester testi calistir
& "$PSScriptRoot\Run-Tests.ps1" -ReportPath $PesterReportDir
