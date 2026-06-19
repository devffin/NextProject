#!/bin/bash
# NextProjectOS - Premier démarrage
# Configurations initiales pour l'utilisateur

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   Bienvenue sur NextProjectOS !            ║"
echo "║   Premier démarrage en cours...            ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

CONFIG_DIR="$HOME/.config/npos"
NPOS_DIR="$HOME/.local/share/npos"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$CONFIG_DIR" "$NPOS_DIR" "$BIN_DIR"

# Création de la configuration par défaut
if [ ! -f "$CONFIG_DIR/npos.conf" ]; then
    cat > "$CONFIG_DIR/npos.conf" << CONF
[Desktop]
wallpaper = $HOME/.local/share/backgrounds/npos/default.svg
wallpaper_style = stretch
show_icons = true
icon_size = 64
text_shadow = true

[Panel]
position = bottom
height = 36
opacity = 0.85
blur = true
autohide = false
glass_effect = true

[Dock]
enabled = true
position = bottom
icon_size = 48
autohide = false
opacity = 0.80

[Menu]
style = aero
show_recent = true
show_favorites = true
blur_background = true

[Theme]
name = NextAero
gtk_theme = NextAero
icon_theme = NPIcons
cursor_theme = default
font = Cantarell 10
accent_color = #4fc3f7
glass_color = #1e88e5

[Compositor]
enabled = true
shadow = true
blur = true
animation = true
fade = true

[Apps]
file_manager = nextfile
terminal = nextterm
editor = nextedit
browser = firefox
CONF
    echo "✅ Configuration par défaut créée"
fi

# Configuration GTK
mkdir -p "$HOME/.config/gtk-3.0"
cat > "$HOME/.config/gtk-3.0/settings.ini" << 'GTK'
[Settings]
gtk-theme-name=NextAero
gtk-icon-theme-name=NPIcons
gtk-font-name=Cantarell 10
gtk-application-prefer-dark-theme=0
GTK

# Démarrage du compositeur Aero
if command -v picom &> /dev/null; then
    if [ -f "$HOME/.config/picom/picom.conf" ]; then
        picom --config "$HOME/.config/picom/picom.conf" &
        echo "✨ Compositeur Aero démarré"
    fi
fi

# Message de bienvenue
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   🎉 NextProjectOS est prêt !              ║"
echo "║                                            ║"
echo "║   Raccourcis utiles :                      ║"
echo "║   • Super + Espace : Lanceur d'applis      ║"
echo "║   • Alt + F2 : Commande                    ║"
echo "║   • Alt + Tab : Changement de fenêtre      ║"
echo "║                                            ║"
echo "║   Applications :                            ║"
echo "║   🔵 NextFile - Explorateur                 ║"
echo "║   🖥️  NextTerm - Terminal                    ║"
echo "║   📝 NextEdit - Éditeur                     ║"
echo "║   🧮 NextCalc - Calculatrice                ║"
echo "║   🎵 NextMedia - Musique                    ║"
echo "║   ⚙️  NextSettings - Paramètres              ║"
echo "╚══════════════════════════════════════════════╝"
