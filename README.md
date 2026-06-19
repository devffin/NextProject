# NextProjectOS (NPOS)

**Un OS Linux moderne avec un environnement de bureau style Aero personnalisable**

NextProjectOS est une distribution Linux proposant un environnement de bureau "Aero" transparent, inspiré de Windows 7, entièrement personnalisable et accompagné d'applications natives faites main.

## ✨ Fonctionnalités

- **Bureau Aero** — Transparence, flou, reflets, animations fluides
- **Personnalisable** — Thèmes, couleurs, fonds d'écran, icônes
- **Applications natives** — Explorateur de fichiers, terminal, éditeur, calculatrice, musique, paramètres, lanceur
- **Performant** — Léger, rapide, optimisé pour le matériel moderne
- **Open Source** — Sous licence MIT

## 🖥️ Composants

| Composant | Description |
|-----------|-------------|
| `desktop/npshell/` | Environnement de bureau (panneau, dock, bureau, menu) |
| `desktop/theme/aero/` | Thème Aero (GTK3/4, Metacity, Openbox) |
| `desktop/compositor/` | Configuration picom pour effets Aero |
| `desktop/wallpaper/` | Fond d'écran style Windows 7 |
| `apps/` | Applications natives |
| `scripts/` | Scripts d'installation et de construction |

## 🚀 Installation rapide

```bash
# Sur une distribution Linux existante (Debian/Ubuntu recommandé)
sudo bash scripts/install.sh
```

## 📦 Construire une ISO

```bash
sudo bash scripts/build-iso.sh
```

## 🧩 Applications incluses

| Application | Description |
|-------------|-------------|
| **NextFile** | Explorateur de fichiers avec onglets et aperçu |
| **NextTerm** | Terminal avec thème Aero |
| **NextEdit** | Éditeur de texte avec coloration syntaxique |
| **NextCalc** | Calculatrice scientifique |
| **NextMedia** | Lecteur audio/vidéo |
| **NextSettings** | Centre de configuration système |
| **NextLauncher** | Lanceur d'applications style Aero |

## 🎨 Personnalisation

- **Thèmes** : `~/.local/share/themes/NextAero/`
- **Icônes** : `~/.local/share/icons/NPIcons/`
- **Fonds d'écran** : `~/.local/share/backgrounds/npos/`
- **Configuration** : `~/.config/npos/npos.conf`

## 📦 Construire l'ISO sur Windows (via Docker)

**Prérequis :** Docker Desktop pour Windows installé
- https://www.docker.com/products/docker-desktop/

**Méthode 1 — Double-clic (recommandé) :**
```cmd
double-clic sur build.bat
```

**Méthode 2 — PowerShell :**
```powershell
.\scripts\build-iso-docker.ps1
```

**Méthode 3 — Manuellement :**
```bash
# Construire l'image
docker build -t npos-builder .

# Lancer la construction
docker run --rm -v "$(pwd):/opt/npos" npos-builder bash scripts/build-iso.sh --non-interactive
```

L'ISO sera créée dans `iso/output/NextProjectOS.iso`.

Pour graver sur une clé USB sous Windows, utilisez **Rufus** : https://rufus.ie

## 📋 Prérequis

### Linux (pour exécuter le bureau)
- Debian 12+, Ubuntu 22.04+, Fedora 38+, Arch Linux
- Python 3.10+
- GTK 3.24+
- picom 10.2+

### Windows (pour construire l'ISO)
- Docker Desktop

## 📄 Licence

MIT
