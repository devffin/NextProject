# build-iso-docker.ps1
# Construction de l'ISO NextProjectOS via Docker Desktop pour Windows
#
# Prérequis :
#   - Docker Desktop pour Windows installé et en cours d'exécution
#     https://www.docker.com/products/docker-desktop/
#   - Docker Desktop configuré avec le backend Linux (WSL 2 ou Hyper-V)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$ISODir = Join-Path $ProjectRoot "iso"
$OutputDir = Join-Path $ISODir "output"
$ImageName = "npos-builder"
$ContainerName = "npos-build-$([System.Guid]::NewGuid().ToString().Substring(0,8))"

Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   NextProjectOS - Build ISO via Docker     ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Vérifier Docker
Write-Host "🔍 Vérification de Docker Desktop..." -ForegroundColor Yellow
try {
    $dockerVersion = & docker --version 2>$null
    if (-not $dockerVersion) {
        throw "Docker not found"
    }
    Write-Host "   $dockerVersion" -ForegroundColor Gray
} catch {
    Write-Host "❌ Docker Desktop n'est pas installé ou pas en cours d'exécution." -ForegroundColor Red
    Write-Host ""
    Write-Host "📥 Pour installer Docker Desktop :" -ForegroundColor Yellow
    Write-Host "   1. Télécharger depuis https://www.docker.com/products/docker-desktop/" -ForegroundColor White
    Write-Host "   2. Installer Docker Desktop" -ForegroundColor White
    Write-Host "   3. Lancer Docker Desktop (attendez que l'icône soit stable)" -ForegroundColor White
    Write-Host "   4. Relancer ce script" -ForegroundColor White
    exit 1
}

# Vérifier que Docker est en cours d'exécution
try {
    $dockerInfo = & docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker daemon not running"
    }
    Write-Host "✅ Docker Desktop est prêt." -ForegroundColor Green
} catch {
    Write-Host "❌ Le service Docker n'est pas en cours d'exécution." -ForegroundColor Red
    Write-Host "   Lancez Docker Desktop et attendez qu'il soit prêt." -ForegroundColor Yellow
    exit 1
}

# Étape 1 : Build de l'image Docker
Write-Host ""
Write-Host "🏗️  Construction de l'image Docker ($ImageName)..." -ForegroundColor Yellow
Write-Host "   (Cela peut prendre 1-2 minutes)" -ForegroundColor Gray

$buildOutput = & docker build -t $ImageName -f "$ProjectRoot/Dockerfile" "$ProjectRoot" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Échec de la construction de l'image Docker." -ForegroundColor Red
    Write-Host $buildOutput -ForegroundColor Red
    exit 1
}
Write-Host "✅ Image Docker construite." -ForegroundColor Green

# Étape 2 : Créer le répertoire de sortie
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

# Étape 3 : Créer un conteneur temporaire et copier l'ISO
Write-Host ""
Write-Host "📦 Création du conteneur de build..." -ForegroundColor Yellow

# Méthode 1 : Utiliser un conteneur avec volume monté (recommandé)
Write-Host "🚀 Lancement de la construction de l'ISO..." -ForegroundColor Cyan
Write-Host "   Cette opération peut prendre 20 à 45 minutes." -ForegroundColor Yellow
Write-Host "   (Téléchargement de Debian + installation des paquets)" -ForegroundColor Gray
Write-Host ""

# On utilise un conteneur temporaire avec mount bind
& docker run --name $ContainerName `
    -v "${ProjectRoot}:/opt/npos" `
    -v "${OutputDir}:/opt/npos/iso/output" `
    --rm `
    $ImageName `
    bash -c "cd /opt/npos && bash scripts/npos.sh build-iso --non-interactive" 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ La construction de l'ISO a échoué." -ForegroundColor Red
    Write-Host "   Consultez les logs ci-dessus pour les détails." -ForegroundColor Yellow
    exit 1
}

# Vérifier que l'ISO existe
$isoPath = Join-Path $OutputDir "NextProjectOS.iso"
if (Test-Path $isoPath) {
    $size = (Get-Item $isoPath).Length / 1MB
    $sizeGB = $size / 1024

    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║   ✅ ISO créée avec succès !               ║" -ForegroundColor Green
    Write-Host "║                                            ║" -ForegroundColor Green
    Write-Host "║   📁 Fichier :" -ForegroundColor Green
    Write-Host "║      $isoPath" -ForegroundColor White
    if ($sizeGB -ge 1) {
        Write-Host "║   📦 Taille  : $([math]::Round($sizeGB, 2)) Go" -ForegroundColor White
    } else {
        Write-Host "║   📦 Taille  : $([math]::Round($size, 1)) Mo" -ForegroundColor White
    }
    Write-Host "║                                            ║" -ForegroundColor Green
    Write-Host "║   💿 Pour graver sur une clé USB :         ║" -ForegroundColor Green
    Write-Host "║      Utiliser Rufus (https://rufus.ie)     ║" -ForegroundColor White
    Write-Host "║      Sélectionner l'ISO et graver          ║" -ForegroundColor White
    Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Green

    Write-Host ""
    Write-Host "📋 Résumé des étapes pour créer une clé USB bootable :" -ForegroundColor Cyan
    Write-Host "   1. Télécharger Rufus : https://rufus.ie" -ForegroundColor White
    Write-Host "   2. Lancer Rufus" -ForegroundColor White
    Write-Host "   3. Sélectionner votre clé USB" -ForegroundColor White
    Write-Host "   4. Cliquer 'Sélectionner' et choisir :" -ForegroundColor White
    Write-Host "      $isoPath" -ForegroundColor Gray
    Write-Host "   5. Cliquer 'Démarrer' et attendre" -ForegroundColor White
    Write-Host "   6. Redémarrer le PC et booter sur la clé USB" -ForegroundColor White
    Write-Host ""
    Write-Host "   Accès rapide : explorer `"$OutputDir`"" -ForegroundColor Gray
} else {
    Write-Host "❌ L'ISO n'a pas été trouvée à l'emplacement attendu." -ForegroundColor Red
    Write-Host "   Chemin attendu : $isoPath" -ForegroundColor Yellow
}

# Nettoyage de l'image Docker (optionnel)
Write-Host ""
$cleanup = Read-Host "🧹 Supprimer l'image Docker pour libérer de l'espace ? (O/N)"
if ($cleanup -eq "O" -or $cleanup -eq "o") {
    Write-Host "🗑️  Suppression de l'image Docker..." -ForegroundColor Yellow
    & docker rmi $ImageName 2>&1 | Out-Null
    Write-Host "✅ Image supprimée." -ForegroundColor Green
}

Write-Host ""
Write-Host "✨ Terminé !" -ForegroundColor Cyan
