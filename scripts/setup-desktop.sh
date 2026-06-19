#!/bin/bash
# NextProjectOS - Configuration rapide du bureau Aero
# Pour les utilisateurs qui veulent configurer manuellement

set -e

NPOS_DIR="$HOME/.local/share/npos"
CONFIG_DIR="$HOME/.config/npos"
THEME_DIR="$HOME/.local/share/themes/NextAero"
ICON_DIR="$HOME/.local/share/icons/NPIcons"
WP_DIR="$HOME/.local/share/backgrounds/npos"

echo "🎨 Configuration du bureau Aero NextProjectOS..."
echo ""

# Création des répertoires
mkdir -p "$NPOS_DIR" "$CONFIG_DIR" "$THEME_DIR" "$ICON_DIR" "$WP_DIR"

SOURCE_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"

# Thème Aero
echo "📁 Installation du thème Aero..."
cp -r "$SOURCE_DIR/desktop/theme/aero/"* "$THEME_DIR/"

# Icônes
echo "🎯 Installation des icônes..."
cp -r "$SOURCE_DIR/desktop/theme/icons/np-icons/"* "$ICON_DIR/"

# Fonds d'écran
echo "🖼️  Installation des fonds d'écran..."
cp -r "$SOURCE_DIR/desktop/wallpaper/"* "$WP_DIR/"

# Configuration picom
echo "✨ Configuration du compositeur Aero..."
mkdir -p "$HOME/.config/picom"
cp "$SOURCE_DIR/desktop/compositor/picom.conf" "$HOME/.config/picom/"

# Configuration GTK
echo "⚙️  Application du thème GTK..."
mkdir -p "$HOME/.config/gtk-3.0"
cat > "$HOME/.config/gtk-3.0/settings.ini" << GTK
[Settings]
gtk-theme-name=NextAero
gtk-icon-theme-name=NPIcons
gtk-font-name=Cantarell 10
gtk-application-prefer-dark-theme=0
GTK

# Application du thème
gsettings set org.gnome.desktop.interface gtk-theme "NextAero" 2>/dev/null || true
gsettings set org.gnome.desktop.interface icon-theme "NPIcons" 2>/dev/null || true

echo ""
echo "✅ Configuration terminée !"
echo ""
echo "Pour activer les effets Aero :"
echo "  picom --config ~/.config/picom/picom.conf &"
echo ""
echo "Pour lancer le bureau :"
echo "  python3 $SOURCE_DIR/desktop/npshell/main.py"
