# build-iso.ps1
# Construction de l'ISO NextProjectOS via WSL 2
# Utilise Ubuntu/Debian dans WSL pour exécuter build-iso.sh

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$ISODir = Join-Path $ProjectRoot "iso"
$WSLDistro = "Ubuntu"

Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   NextProjectOS - Build ISO via WSL       ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Étape 1: Vérifier WSL
Write-Host "🔍 Vérification de WSL..." -ForegroundColor Yellow
$wsl = Get-Command "wsl.exe" -ErrorAction SilentlyContinue
if (-not $wsl) {
    Write-Host "❌ WSL n'est pas installé." -ForegroundColor Red
    Write-Host ""
    Write-Host "📥 Pour installer WSL 2 :" -ForegroundColor Yellow
    Write-Host "   1. Ouvrir PowerShell en Administrateur" -ForegroundColor White
    Write-Host "   2. Exécuter : wsl --install" -ForegroundColor White
    Write-Host "   3. Redémarrer l'ordinateur" -ForegroundColor White
    Write-Host "   4. Relancer ce script" -ForegroundColor White
    Write-Host ""
    Write-Host "   Ou manuellement : https://learn.microsoft.com/fr-fr/windows/wsl/install" -ForegroundColor Gray
    exit 1
}

# Étape 2: Vérifier que Ubuntu est installé
Write-Host "🔍 Vérification de la distribution WSL ($WSLDistro)..." -ForegroundColor Yellow
$distros = & wsl.exe --list --quiet 2>&1 | ForEach-Object { $_.Trim() }
$hasUbuntu = $distros -match $WSLDistro

if (-not $hasUbuntu) {
    Write-Host "⚠️  $WSLDistro n'est pas installée." -ForegroundColor Yellow
    Write-Host "📥 Installation de $WSLDistro..." -ForegroundColor Yellow
    & wsl.exe --install -d $WSLDistro
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Échec de l'installation de WSL." -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Installation de $WSLDistro terminée." -ForegroundColor Green
    Write-Host "⚠️  Veuillez redémarrer le script après le premier démarrage d'Ubuntu." -ForegroundColor Yellow
    exit 0
}

# Étape 3: Installer les dépendances de build dans WSL
Write-Host "📥 Installation des outils de build dans WSL..." -ForegroundColor Yellow
$setupTools = @'
sudo apt-get update
sudo apt-get install -y debootstrap squashfs-tools xorriso isolinux grub-pc-bin \
    grub-common mtools dosfstools
'@
& wsl.exe -d $WSLDistro -e bash -c $setupTools
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Échec de l'installation des outils." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Outils installés." -ForegroundColor Green

# Étape 4: Copier le projet dans WSL
Write-Host "📁 Copie du projet dans WSL..." -ForegroundColor Yellow
$wslProjectDir = '/opt/npos-build-project'
$copyCmd = "sudo rm -rf $wslProjectDir && sudo mkdir -p $wslProjectDir"
& wsl.exe -d $WSLDistro -e bash -c $copyCmd

# Copier via tar (plus fiable que les montages)
$tempTar = Join-Path $env:TEMP "npos-project.tar"
if (Test-Path $tempTar) { Remove-Item $tempTar -Force }
& tar -cf $tempTar -C $ProjectRoot --exclude='node_modules' --exclude='.git' .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Échec de la création de l'archive." -ForegroundColor Red
    exit 1
}

# Copier dans WSL
$copyArchive = @'
cd /opt/npos-build-project
sudo tar -xf /mnt/c/Users/{0}/AppData/Local/Temp/npos-project.tar -C /opt/npos-build-project
'@ -f $env:USERNAME
# Correction du chemin car /mnt/c/Users/... utilise le chemin Windows
$wslPath = "/mnt/c/" + ($tempTar -replace '^C:\\', '' -replace '\\', '/')
$copyCmd2 = "cd $wslProjectDir && sudo tar -xf '$wslPath' -C $wslProjectDir"
& wsl.exe -d $WSLDistro -e bash -c $copyCmd2
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Échec de la copie du projet." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Projet copié dans WSL." -ForegroundColor Green

# Étape 5: Exécuter le build dans WSL
Write-Host ""
Write-Host "🚀 Lancement de la construction de l'ISO..." -ForegroundColor Cyan
Write-Host "   (Cela peut prendre 20-45 minutes selon votre connexion)" -ForegroundColor Yellow
Write-Host ""

$buildCmd = "cd $wslProjectDir && sudo bash scripts/build-iso.sh --non-interactive"
& wsl.exe -d $WSLDistro -e bash -c $buildCmd
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Échec de la construction de l'ISO." -ForegroundColor Red
    exit 1
}

# Étape 6: Récupérer l'ISO depuis WSL
Write-Host "📦 Récupération de l'ISO..." -ForegroundColor Yellow
$isoOutputDir = Join-Path $ISODir "output"
if (-not (Test-Path $isoOutputDir)) {
    New-Item -ItemType Directory -Path $isoOutputDir -Force | Out-Null
}

$copyBackCmd = "sudo cp $wslProjectDir/iso/output/NextProjectOS.iso /mnt/c/" + ($isoOutputDir -replace '^C:\\', '' -replace '\\', '/')
& wsl.exe -d $WSLDistro -e bash -c $copyBackCmd

$isoPath = Join-Path $isoOutputDir "NextProjectOS.iso"
if (Test-Path $isoPath) {
    $size = (Get-Item $isoPath).Length / 1MB
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║   ✅ ISO créée avec succès !               ║" -ForegroundColor Green
    Write-Host "║                                            ║" -ForegroundColor Green
    Write-Host "║   Fichier : $isoPath" -ForegroundColor White
    Write-Host "║   Taille  : $([math]::Round($size, 1)) MB" -ForegroundColor White
    Write-Host "║                                            ║" -ForegroundColor Green
    Write-Host "║   Pour graver sur une clé USB :            ║" -ForegroundColor Green
    Write-Host "║   Utiliser Rufus (https://rufus.ie)        ║" -ForegroundColor White
    Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Green
} else {
    Write-Host "❌ ISO non trouvée après le build." -ForegroundColor Red
}

# Nettoyage
Remove-Item $tempTar -Force -ErrorAction SilentlyContinue
Write-Host ""
Write-Host "🧹 Nettoyage terminé." -ForegroundColor Gray
