@echo off
rem Indirim takipcisi kurulumu - cift tiklayin (masaustunde).
rem Ayni klasordeki kurulum_masaustu.ps1 dosyasini calistirir.
rem Gorevleri kaldirmak icin: KURULUM_BASLAT.bat -Kaldir
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0kurulum_masaustu.ps1" %*
echo.
echo Bitti. Pencereyi kapatabilirsiniz.
pause
