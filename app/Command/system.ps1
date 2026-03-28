# system.ps1 — FlaskDjango App Kurulum ve Sistem Kontrol Betiği
# ============================================================
# Kullanım:
#   .\system.ps1                    # tam kurulum
#   .\system.ps1 -Kontrol           # yalnizca sistem kontrol
#   .\system.ps1 -Python python3.11 # belirli Python yürütücüsü

Param(
  [string]$Python   = 'python',
  [switch]$Kontrol  = $false,
  [switch]$Temizle  = $false
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ── Renk yardımcıları ──────────────────────────────────────────────────────
function Yaz-OK    { param($M) Write-Host "  [OK] $M"    -ForegroundColor Green  }
function Yaz-Hata  { param($M) Write-Host "  [!!] $M"    -ForegroundColor Red    }
function Yaz-Uyari { param($M) Write-Host "  [??] $M"    -ForegroundColor Yellow }
function Yaz-Bilgi { param($M) Write-Host "  [--] $M"    -ForegroundColor Cyan   }
function Yaz-Baslik{ param($M) Write-Host "`n=== $M ===" -ForegroundColor Blue   }

# ══════════════════════════════════════════════════════════════════════════════
# 1. SİSTEM GEREKSİNİM KONTROL BLOĞU
# ══════════════════════════════════════════════════════════════════════════════

function Kontrol-Sistem {
  Yaz-Baslik "SİSTEM GEREKSİNİM KONTROLÜ"

  # ── PowerShell sürümü ──────────────────────────────────────────────────────
  $psVer = $PSVersionTable.PSVersion
  if ($psVer.Major -ge 5) {
    Yaz-OK    "PowerShell $($psVer.ToString()) (min 5.0)"
  } else {
    Yaz-Hata  "PowerShell $($psVer.ToString()) — 5.0+ gerekli"
  }

  # ── İşletim sistemi ────────────────────────────────────────────────────────
  $os = [System.Environment]::OSVersion
  Yaz-OK "OS: $($os.VersionString)"

  # ── Disk alanı ─────────────────────────────────────────────────────────────
  $disk  = Get-PSDrive -Name (Split-Path $PSScriptRoot -Qualifier).TrimEnd(':') `
           -ErrorAction SilentlyContinue
  if ($disk) {
    $bosMB = [math]::Round($disk.Free / 1MB)
    if ($bosMB -ge 200) {
      Yaz-OK "Disk: $bosMB MB boş"
    } else {
      Yaz-Uyari "Disk: $bosMB MB — min 200 MB önerilir"
    }
  }

  # ── Python varlığı ─────────────────────────────────────────────────────────
  Yaz-Baslik "PYTHON KONTROL"
  if (-not (Get-Command $Python -ErrorAction SilentlyContinue)) {
    Yaz-Hata "Python '$Python' bulunamadı — https://python.org/downloads"
    exit 1
  }

  $pyVerStr = & $Python --version 2>&1
  Yaz-OK "$pyVerStr  ($((Get-Command $Python).Source))"

  $pyVer = [version]($pyVerStr -replace 'Python ', '')
  if ($pyVer -lt [version]'3.10') {
    Yaz-Hata "Python 3.10+ gerekli, mevcut: $pyVer"
    exit 1
  }

  # ── pip ────────────────────────────────────────────────────────────────────
  $pipVer = & $Python -m pip --version 2>&1
  if ($LASTEXITCODE -eq 0) {
    Yaz-OK "pip: $pipVer"
  } else {
    Yaz-Hata "pip bulunamadı — 'python -m ensurepip' çalıştırın"
    exit 1
  }

  # ── git ────────────────────────────────────────────────────────────────────
  if (Get-Command git -ErrorAction SilentlyContinue) {
    Yaz-OK "git: $((git --version))"
  } else {
    Yaz-Uyari "git bulunamadı (opsiyonel)"
  }

  # ── Port kontrolü ──────────────────────────────────────────────────────────
  Yaz-Baslik "PORT KONTROL"
  foreach ($port in @(5000, 8000)) {
    $test = Test-NetConnection -ComputerName 127.0.0.1 -Port $port `
            -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
    if ($test.TcpTestSucceeded) {
      Yaz-Uyari "Port $port kullanımda"
    } else {
      Yaz-OK    "Port $port boş"
    }
  }

  # ── Proje dosyaları ────────────────────────────────────────────────────────
  Yaz-Baslik "PROJE DOSYA KONTROL"
  $zorunluDosyalar  = @('main.py', 'controller.py', 'requirements_api.txt')
  $opsiyonelDosyalar = @('system.ps1', 'run.bat', '.env', 'syscheck.py')

  foreach ($d in $zorunluDosyalar) {
    if (Test-Path (Join-Path $PSScriptRoot $d)) {
      Yaz-OK    "$d mevcut"
    } else {
      Yaz-Hata  "$d EKSİK — proje çalışmayabilir"
    }
  }
  foreach ($d in $opsiyonelDosyalar) {
    if (Test-Path (Join-Path $PSScriptRoot $d)) {
      Yaz-OK    "$d mevcut (opsiyonel)"
    } else {
      Yaz-Uyari "$d mevcut değil (opsiyonel)"
    }
  }

  # ── Python modül kontrol ───────────────────────────────────────────────────
  Yaz-Baslik "PYTHON PAKET KONTROL"
  $paketler = @(
    @{Ad='flask';        Pip='flask';             Min='3.0.0'},
    @{Ad='flask_sqlalchemy';Pip='flask-sqlalchemy';Min='3.1.0'},
    @{Ad='sqlalchemy';   Pip='sqlalchemy';        Min='2.0.0'},
    @{Ad='jwt';          Pip='PyJWT';             Min='2.8.0'},
    @{Ad='cryptography'; Pip='cryptography';      Min='42.0.0'},
    @{Ad='pytest';       Pip='pytest';            Min='8.0.0'}
  )
  foreach ($p in $paketler) {
    $cikti = & $Python -c "import $($p.Ad); print(getattr($($p.Ad),'__version__','?'))" 2>&1
    if ($LASTEXITCODE -eq 0) {
      Yaz-OK "$($p.Pip)==$cikti"
    } else {
      Yaz-Uyari "$($p.Pip) kurulu değil — pip install $($p.Pip)>=$($p.Min)"
    }
  }
}

# ══════════════════════════════════════════════════════════════════════════════
# 2. SANAL ORTAM KURULUM BLOĞU
# ══════════════════════════════════════════════════════════════════════════════

function Kur-SanalOrtam {
  Yaz-Baslik "SANAL ORTAM"
  $Venv = Join-Path $PSScriptRoot ".venv"

  if ($Temizle -and (Test-Path $Venv)) {
    Yaz-Bilgi "Mevcut .venv siliniyor..."
    Remove-Item $Venv -Recurse -Force
  }

  if (-not (Test-Path $Venv)) {
    Yaz-Bilgi "Sanal ortam oluşturuluyor: $Venv"
    & $Python -m venv $Venv
    if ($LASTEXITCODE -ne 0) { Yaz-Hata "venv oluşturulamadı"; exit 1 }
    Yaz-OK "Sanal ortam oluşturuldu"
  } else {
    Yaz-OK "Mevcut .venv kullanılıyor: $Venv"
  }

  # ── Aktivasyon ─────────────────────────────────────────────────────────────
  $aktivasyon = Join-Path $Venv "Scripts\Activate.ps1"
  if (-not (Test-Path $aktivasyon)) {
    $aktivasyon = Join-Path $Venv "bin/activate"
  }
  & $aktivasyon
  Yaz-OK "Sanal ortam aktive edildi"
}

# ══════════════════════════════════════════════════════════════════════════════
# 3. BAĞIMLILIK KURULUM BLOĞU
# ══════════════════════════════════════════════════════════════════════════════

function Kur-Bagimliliklar {
  Yaz-Baslik "BAĞIMLILIK KURULUM"

  & $Python -m pip install --upgrade pip -q
  Yaz-OK "pip güncellendi"

  $reqDosya = Join-Path $PSScriptRoot "requirements_api.txt"
  if (Test-Path $reqDosya) {
    Yaz-Bilgi "requirements_api.txt yükleniyor..."
    & $Python -m pip install -r $reqDosya -q
    if ($LASTEXITCODE -eq 0) {
      Yaz-OK "Paketler kuruldu"
    } else {
      Yaz-Hata "Paket kurulumu başarısız"
      exit 1
    }
  } else {
    Yaz-Uyari "requirements_api.txt bulunamadı — atlanıyor"
  }

  & $Python -m pip install pytest pytest-cov -q
  Yaz-OK "pytest kuruldu"
}

# ══════════════════════════════════════════════════════════════════════════════
# 4. PYTHON SİSTEM KONTROL BLOĞU (syscheck.py entegrasyonu)
# ══════════════════════════════════════════════════════════════════════════════

function Calistir-SysCheck {
  $syscheckDosya = Join-Path $PSScriptRoot "syscheck.py"
  if (Test-Path $syscheckDosya) {
    Yaz-Baslik "DETAYLI SİSTEM RAPORU (syscheck.py)"
    & $Python $syscheckDosya
  } else {
    Yaz-Uyari "syscheck.py bulunamadı — Python raporu atlandı"
  }
}

# ══════════════════════════════════════════════════════════════════════════════
# ANA AKIŞ
# ══════════════════════════════════════════════════════════════════════════════

Write-Host "`n$('═' * 62)" -ForegroundColor Cyan
Write-Host "  FLASKDJANGO APP — SİSTEM KURULUM VE KONTROL"           -ForegroundColor Cyan
Write-Host "  $($Python)  |  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"  -ForegroundColor DarkGray
Write-Host "$('═' * 62)" -ForegroundColor Cyan

Kontrol-Sistem

if (-not $Kontrol) {
  Kur-SanalOrtam
  Kur-Bagimliliklar
}

Calistir-SysCheck

Write-Host "`n$('═' * 62)" -ForegroundColor Cyan
Yaz-OK "Tüm adımlar tamamlandı."
Write-Host "  Uygulamayı başlatmak için:" -ForegroundColor DarkGray
Write-Host "    python main.py" -ForegroundColor White
Write-Host "$('═' * 62)`n" -ForegroundColor Cyan