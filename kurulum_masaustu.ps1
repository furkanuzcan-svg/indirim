# Indirim takipcisi - evdeki masaustu kurulumu
#
# Calistirma (proje klasorunde, normal PowerShell penceresinde):
#   powershell -ExecutionPolicy Bypass -File kurulum_masaustu.ps1
# Zamanlanmis gorevleri kaldirmak icin:
#   powershell -ExecutionPolicy Bypass -File kurulum_masaustu.ps1 -Kaldir
#
# Not: Bu dosya bilerek sadece ASCII karakter icerir (PowerShell 5.1 BOM'suz
# UTF-8 dosyalardaki Turkce karakterleri bozuyor).

param([switch]$Kaldir)

$ErrorActionPreference = 'Stop'
$Proje = $PSScriptRoot
$Venv = Join-Path $env:USERPROFILE '.venvs\indirim'
$Py = Join-Path $Venv 'Scripts\python.exe'
$PyW = Join-Path $Venv 'Scripts\pythonw.exe'
# 'Indirim Hizli Tur' / 'Indirim Tam Tur': eski (5 dk'lik) gorevler, artik surekli dongu kullaniliyor
$Gorevler = @('Indirim Hizli Tur', 'Indirim Tam Tur', 'Indirim Takip Dongu')

if ($Kaldir) {
    foreach ($g in $Gorevler) {
        Unregister-ScheduledTask -TaskName $g -Confirm:$false -ErrorAction SilentlyContinue
    }
    Write-Host 'Zamanlanmis gorevler kaldirildi.'
    exit
}

Write-Host "Proje klasoru: $Proje"

# 1) Python 3.12
$SysPy = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
if (-not (Test-Path $SysPy)) {
    Write-Host '1/4 Python 3.12 kuruluyor...'
    winget install --id Python.Python.3.12 -e --silent --scope user --accept-package-agreements --accept-source-agreements
    if (-not (Test-Path $SysPy)) { throw "Python kurulamadi: $SysPy bulunamadi" }
} else {
    Write-Host '1/4 Python 3.12 zaten kurulu.'
}

# 2) Sanal ortam (Drive disinda) + paketler
if (-not (Test-Path $Py)) {
    Write-Host "2/4 Sanal ortam olusturuluyor: $Venv"
    & $SysPy -m venv $Venv
}
Write-Host '2/4 Paketler kuruluyor...'
& $Py -m pip install -q --disable-pip-version-check -r (Join-Path $Proje 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Paket kurulumu basarisiz' }

# 3) Deneme turu (ekranda gorunur)
Write-Host '3/5 Deneme icin bir hizli tur calistiriliyor (1-3 dakika)...'
Push-Location $Proje
try { & $Py -m tracker.run --quick } finally { Pop-Location }
if ($LASTEXITCODE -ne 0) { throw 'Deneme turu hata verdi, yukaridaki ciktiya bak' }

# 4) Git + GitHub girisi (online tablo icin). Ilk gonderimde tarayicida GitHub giris penceresi acilir.
$Git = 'C:\Program Files\Git\cmd\git.exe'
if (-not (Test-Path $Git)) {
    Write-Host '4/5 Git kuruluyor (yonetici izni penceresi acilabilir)...'
    winget install --id Git.Git -e --silent --accept-package-agreements --accept-source-agreements
    if (-not (Test-Path $Git)) { throw "Git kurulamadi: $Git bulunamadi" }
} else {
    Write-Host '4/5 Git zaten kurulu.'
}
$env:Path = "C:\Program Files\Git\cmd;$env:Path"
Write-Host '4/5 GitHub girisi: tarayicida pencere acilirsa GitHub hesabinla giris yap ve izin ver.'
Push-Location $Proje
try { & $Py -m tracker.run --publish-only } finally { Pop-Location }
if ($LASTEXITCODE -ne 0) { throw 'GitHub a gonderim basarisiz, yukaridaki ciktiya bak' }

# 5) Surekli calisan tek gorev (oturum acikken; ekran kilitli olabilir).
# Tur biter bitmez yenisi baslar (~2 dk), saatte bir tam tur, 5 dk'da bir GitHub'a gonderim.
Write-Host '5/5 Surekli tarama gorevi kaydediliyor...'
foreach ($g in @('Indirim Hizli Tur', 'Indirim Tam Tur')) {
    if (Get-ScheduledTask -TaskName $g -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $g -Confirm:$false
        Write-Host "   eski gorev kaldirildi: $g"
    }
}
$Ayar = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -RestartCount 99 -RestartInterval (New-TimeSpan -Minutes 5) `
    -ExecutionTimeLimit ([TimeSpan]::Zero)
$Eylem = New-ScheduledTaskAction -Execute $PyW -Argument '-m tracker.run --loop --publish' -WorkingDirectory $Proje
$Tetik = @((New-ScheduledTaskTrigger -AtLogOn), (New-ScheduledTaskTrigger -Once -At ((Get-Date).AddMinutes(1))))
Register-ScheduledTask -TaskName 'Indirim Takip Dongu' -Action $Eylem -Trigger $Tetik -Settings $Ayar -Force | Out-Null
Write-Host "   'Indirim Takip Dongu' kaydedildi (oturum acilinca baslar, surekli calisir)"

$Log = Join-Path $env:LOCALAPPDATA 'indirim\tracker.log'
Write-Host ''
Write-Host 'Kurulum tamam.'
Write-Host "  Tablo : $(Join-Path $Proje 'docs\index.html')  (cift tikla)"
Write-Host '  Online: https://furkanuzcan-svg.github.io/indirim/'
Write-Host "  Log   : $Log"
Write-Host '  Onemli: Bilgisayarin uyku moduna gecmesini kapat (Ayarlar > Sistem > Guc).'
