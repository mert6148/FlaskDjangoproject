# MySQL güvenlik denetimi
# Bu betik, MySQL serverının çalışıp çalışmadığını kontrol eder ve güvenlik uygunluğunu raporlar.
$log = Join-Path (Split-Path $MyInvocation.MyCommand.Path -Parent) "mysql_protection.log"
function Write-Log($msg) {
    "$((Get-Date -Format s)) - $msg" | Out-File -FilePath $log -Append -Encoding utf8
}

Write-Log "MySQL koruma betiği başladı."

# MySQL hizmet durumu
$serviceName = "MySQL"  # ya da MySQL80
$service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
if (-not $service) {
    Write-Log "MySQL servisi bulunamadı: $serviceName"
    Write-Host "Uyarı: MySQL servisi bulunamadı ($serviceName)."
    exit 1
}

Write-Log "MySQL servisi durumu: $($service.Status)"
if ($service.Status -ne 'Running') {
    Write-Log "MySQL servisi çalışmıyor (durum: $($service.Status))"
    Write-Host "MySQL servisi çalışmıyor: $($service.Status)"
    exit 1
}

# Güvenlik kontrolü (varsayılan kimlik bilgileri uyarısı)
$myCnf = "$env:ProgramData\MySQL\MySQL Server 8.0\my.ini"
if (-Not (Test-Path $myCnf)) {
    Write-Log "MySQL config dosyası bulunamadı: $myCnf"
    Write-Host "Uyarı: my.ini bulunamadı."
} else {
    $conf = Get-Content $myCnf
    if ($conf -match "bind-address\s*=\s*127.0.0.1") {
        Write-Log "bind-address yerel ayağa sabitlenmiş."
    } else {
        Write-Log "bind-address localhost dışı olabilir."
        Write-Host "Uyarı: bind-address kontrolü başarısız."
    }
}

Write-Log "MySQL koruma kontrolü tamamlandı."
Write-Host "MySQL koruma betiği tamamlandı."