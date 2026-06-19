# Architecture de NextProjectOS

## Vue d'ensemble

NextProjectOS (NPOS) est un environnement de bureau Linux complet
avec un style Aero transparent inspiré de Windows 7, accompagné
d'applications natives et d'un système de construction d'ISO.

## Structure des composants

```
NextProjectOS/
├── desktop/               # Environnement de bureau
│   ├── npshell/           # Shell du bureau (Python/GTK3)
│   │   ├── main.py        # Point d'entrée
│   │   ├── panel.py       # Barre des tâches
│   │   ├── desktop.py     # Bureau avec icônes
│   │   ├── dock.py        # Dock d'applications
│   │   ├── menu.py        # Menu démarrer Aero
│   │   ├── taskbar.py     # Gestionnaire de fenêtres
│   │   ├── systemtray.py  # Zone de notification
│   │   ├── config.py      # Gestionnaire de configuration
│   │   └── utils.py       # Utilitaires
│   ├── theme/aero/        # Thème visuel Aero
│   │   ├── gtk-3.0/       # Thème GTK3
│   │   ├── gtk-4.0/       # Thème GTK4
│   │   ├── metacity-1/    # Thème Metacity/Compiz
│   │   └── openbox-3/     # Thème Openbox
│   ├── theme/icons/       # Thème d'icônes
│   ├── compositor/        # Configuration picom
│   └── wallpaper/         # Fonds d'écran
├── apps/                  # Applications natives
│   ├── nextfile/          # Explorateur de fichiers
│   ├── nextterm/          # Terminal
│   ├── nextedit/          # Éditeur de texte
│   ├── nextcalc/          # Calculatrice
│   ├── nextmedia/         # Lecteur multimédia
│   ├── nextsettings/      # Paramètres système
│   └── nextlauncher/      # Lanceur d'applications
├── config/                # Configuration système
├── scripts/               # Scripts d'installation
├── iso/                   # Construction d'ISO
└── docs/                  # Documentation
```

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Noyau | Linux |
| Affichage | X.Org / Wayland |
| Gestionnaire de fenêtres | Openbox |
| Compositeur | picom |
| Interface utilisateur | Python + GTK3 |
| Thème | CSS GTK personnalisé |
| Paquetage | .deb / .rpm / ISO |

## Effets Aero

Les effets visuels Aero (verre transparent, flou, ombres,
animations) sont réalisés via :
1. **picom** — Compositeur avec flou (dual_kawase),
   ombres portées, transparence, animations
2. **GTK CSS** — Thème avec dégradés, transparences,
   couleurs verre (#1e88e5, #4fc3f7)
3. **Openbox** — Gestion des fenêtres sans
   décorations lourdes

## Flux de démarrage

1. Login manager → Openbox
2. Openbox autostart → picom + npos-session
3. npos-session → npshell/main.py
4. NPOS Shell → Panel + Desktop + Dock

## Applications

Les applications sont écrites en Python/GTK3 et suivent
le thème Aero. Elles peuvent être lancées depuis le menu,
le dock, le bureau ou le lanceur rapide (Super+Espace).
