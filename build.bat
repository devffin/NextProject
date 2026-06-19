@echo off
title NextProjectOS - Build ISO

echo ============================================
echo    NextProjectOS - Build ISO via Docker
echo ============================================
echo.
echo Ce script va construire l'ISO de NextProjectOS
echo en utilisant Docker Desktop.
echo.
echo Prerequis : Docker Desktop installe et en cours
echo d'execution sur votre machine.
echo.
echo ============================================
echo.

where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERREUR] Docker Desktop n'est pas installe.
    echo.
    echo Telechargez-le depuis : https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

echo [OK] Docker trouve.
echo.
echo Demarrage de la construction de l'ISO...
echo Cela peut prendre 20 a 45 minutes.
echo.
pause

cd /d "%~dp0"
powershell.exe -ExecutionPolicy Bypass -File "scripts\build-iso-docker.ps1"

if %errorlevel% equ 0 (
    echo.
    echo Construction terminee avec succes !
) else (
    echo.
    echo La construction a echoue. Consultez les logs ci-dessus.
)

echo.
pause
