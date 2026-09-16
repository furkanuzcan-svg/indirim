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
$Gorevler = @('Indirim Hizli Tur', 'Indirim Tam Tur')

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

# 5) Zamanlanmis gorevler (sadece bu kullanici oturum acikken calisir; ekran kilitli olabilir)
Write-Host '5/5 Zamanlanmis gorevler kaydediliyor...'
$Ayar = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

function Kaydet($Ad, $Arguman, $Dakika, $Gecikme) {
    $Eylem = New-ScheduledTaskAction -Execute $PyW -Argument $Arguman -WorkingDirectory $Proje
    $Tetik = New-ScheduledTaskTrigger -Once -At ((Get-Date).AddMinutes($Gecikme)) `
        -RepetitionInterval (New-TimeSpan -Minutes $Dakika)
    Register-ScheduledTask -TaskName $Ad -Action $Eylem -Trigger $Tetik -Settings $Ayar -Force | Out-Null
    Write-Host "   '$Ad' her $Dakika dakikada bir"
}
Kaydet 'Indirim Hizli Tur' '-m tracker.run --quick --publish' 5 2
Kaydet 'Indirim Tam Tur' '-m tracker.run --publish' 60 7

$Log = Join-Path $env:LOCALAPPDATA 'indirim\tracker.log'
Write-Host ''
Write-Host 'Kurulum tamam.'
Write-Host "  Tablo : $(Join-Path $Proje 'docs\index.html')  (cift tikla)"
Write-Host '  Online: https://furkanuzcan-svg.github.io/indirim/'
Write-Host "  Log   : $Log"
Write-Host '  Onemli: Bilgisayarin uyku moduna gecmesini kapat (Ayarlar > Sistem > Guc).'
