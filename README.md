# NextProjectOS (NPOS)

**Un OS Linux moderne avec un environnement de bureau XFCE4 pré-configuré style Aero**

NextProjectOS est une distribution Linux utilisant XFCE4 comme environnement de bureau, pré-configuré avec un thème "Aero" transparent (inspiré de Windows 7), picom pour les effets de flou/reflets, et des applications natives faites main.

## Fonctionnalites

- **Bureau XFCE4** — Pre-configure avec theme Aero, picom (flou, transparence, ombres)
- **Personnalisable** — Themes, couleurs, fonds d'ecran, icones
- **Applications natives** — Explorateur de fichiers, terminal, editeur, calculatrice, musique, parametres, lanceur, installateur
- **ISO live** — Bootable, installable sur disque dur via NextInstaller
- **Performant** — XFCE4 leger + picom pour les effets

## Composants

| Composant | Description |
|-----------|-------------|
| `desktop/theme/aero/` | Theme Aero GTK3/4 pour XFCE4 |
| `desktop/compositor/` | Configuration picom pour effets Aero |
| `desktop/wallpaper/` | Fond d'ecran Aero |
| `apps/` | Applications natives (nextfile, nextterm, etc.) |
| `config/` | Configuration par defaut |
| `scripts/npos.sh` | Script unique tout-en-un |

## Installation rapide

```bash
# Sur Debian/Ubuntu existant
sudo bash scripts/npos.sh install
```

## Construire l'ISO

```bash
# Sur Linux (Debian/Ubuntu recommande)
sudo bash scripts/npos.sh build-iso
```

```powershell
# Sur Windows (via Docker)
.\scripts\build-iso-docker.ps1
```

## Applications incluses

| Application | Description |
|-------------|-------------|
| **NextFile** | Explorateur de fichiers |
| **NextTerm** | Terminal avec theme Aero |
| **NextEdit** | Editeur de texte avec coloration syntaxique |
| **NextCalc** | Calculatrice scientifique |
| **NextMedia** | Lecteur audio/video |
| **NextSettings** | Centre de configuration systeme |
| **NextLauncher** | Lanceur d'applications |
| **NextInstaller** | Installateur pour disque dur |

## Script unique

```bash
bash scripts/npos.sh build-iso   # Construire l'ISO live
bash scripts/npos.sh install     # Installer sur le systeme
bash scripts/npos.sh desktop     # Installer theme/icones/wallpaper
bash scripts/npos.sh first-boot  # Config post-installation
bash scripts/npos.sh uninstall   # Supprimer NPOS
```

## Licence

MIT
