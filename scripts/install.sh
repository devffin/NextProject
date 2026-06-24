#!/bin/bash
# DEPRECATED - Utilisez pluto: bash scripts/npos.sh install
# NextProjectOS - Script d'installation

set -e

echo "╔══════════════════════════════════════════════╗"
echo "║     NextProjectOS - Installation            ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Détection de la distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
else
    DISTRO=$(uname -s)
fi

echo "📦 Distribution détectée : $DISTRO"
echo ""

# Installation des dépendances
install_deps() {
    echo "📥 Installation des dépendances..."

    case $DISTRO in
        debian|ubuntu)
            sudo apt-get update
            sudo apt-get install -y \
                python3 python3-gi python3-gi-cairo \
                gir1.2-gtk-3.0 gir1.2-gtksource-4 \
                gir1.2-vte-2.91 gir1.2-wnck-3.0 \
                picom openbox \
                fonts-cantarell \
                git make gcc libgl1-mesa-glx
            ;;

        fedora)
            sudo dnf install -y \
                python3 python3-gobject python3-gobject-cairo \
                gtk3 gtksourceview4 vte291 \
                libwnck3 picom openbox \
                cantarell-fonts \
                git make gcc mesa-libGL
            ;;

        arch|manjaro)
            sudo pacman -S --noconfirm \
                python python-gobject python-cairo \
                gtk3 gtksourceview4 vte3 \
                libwnck3 picom openbox \
                cantarell-fonts \
                git make gcc mesa
            ;;

        *)
            echo "⚠️  Distribution non reconnue. Veuillez installer les dépendances manuellement."
            echo "   Paquets requis : python3, python3-gi, gtk3, gtksourceview4, vte, picom"
            ;;
    esac
}

# Installation des fichiers de l'environnement de bureau
install_desktop() {
    echo "🖥️  Installation de l'environnement de bureau Aero..."

    NPOS_DIR="$HOME/.local/share/npos"
    CONFIG_DIR="$HOME/.config/npos"
    THEME_DIR="$HOME/.local/share/themes/NextAero"
    ICON_DIR="$HOME/.local/share/icons/NPIcons"
    WP_DIR="$HOME/.local/share/backgrounds/npos"
    APP_DIR="$HOME/.local/share/applications"

    mkdir -p "$NPOS_DIR" "$CONFIG_DIR" "$THEME_DIR" "$ICON_DIR" "$WP_DIR" "$APP_DIR"

    SOURCE_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"

    # Copier le thème
    cp -r "$SOURCE_DIR/desktop/theme/aero/"* "$THEME_DIR/"

    # Copier les icônes
    cp -r "$SOURCE_DIR/desktop/theme/icons/np-icons/"* "$ICON_DIR/"

    # Copier les fonds d'écran
    cp -r "$SOURCE_DIR/desktop/wallpaper/"* "$WP_DIR/"

    # Copier la configuration
    cp "$SOURCE_DIR/config/npos.conf" "$CONFIG_DIR/" 2>/dev/null || true

    # Copier le compositor
    mkdir -p "$HOME/.config/picom"
    cp "$SOURCE_DIR/desktop/compositor/picom.conf" "$HOME/.config/picom/"

    echo "✅ Environnement de bureau installé"
}

# Installation des applications
install_apps() {
    echo "📱 Installation des applications NextProjectOS..."

    APP_DIR="$HOME/.local/share/npos/apps"
    BIN_DIR="$HOME/.local/bin"

    mkdir -p "$APP_DIR" "$BIN_DIR"

    SOURCE_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"

    # Copier les applications
    cp -r "$SOURCE_DIR/apps/"* "$APP_DIR/"

    # Créer les lanceurs dans le PATH
    for app in nextfile nextterm nextedit nextcalc nextmedia nextsettings nextlauncher; do
        cat > "$BIN_DIR/$app" << EOF
#!/bin/bash
exec python3 "$APP_DIR/$app/main.py" "\$@"
EOF
        chmod +x "$BIN_DIR/$app"

        # Créer les entrées de menu .desktop
        cat > "$HOME/.local/share/applications/npos-$app.desktop" << EOF
[Desktop Entry]
Name=Next$app
Comment=Application NextProjectOS
Exec=$BIN_DIR/$app
Icon=$ICON_DIR/scalable/apps/$app.svg
Terminal=false
Type=Application
Categories=Utility;
StartupNotify=true
EOF
    done

    # Ajouter BIN_DIR au PATH si pas déjà présent
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        echo "export PATH=\"\$PATH:$BIN_DIR\"" >> "$HOME/.bashrc"
        echo "export PATH=\"\$PATH:$BIN_DIR\"" >> "$HOME/.zshrc" 2>/dev/null || true
        echo "🔧 Répertoire $BIN_DIR ajouté au PATH"
    fi

    echo "✅ Applications installées dans $APP_DIR"
}

# Configuration du démarrage automatique
setup_autostart() {
    echo "⚙️  Configuration du démarrage automatique..."

    AUTOSTART_DIR="$HOME/.config/autostart"
    mkdir -p "$AUTOSTART_DIR"

    # Lanceur pour le shell NPOS
    cat > "$AUTOSTART_DIR/npos-shell.desktop" << EOF
[Desktop Entry]
Type=Application
Name=NextProjectOS Shell
Exec=$HOME/.local/bin/npos-shell
Comment=Environnement de bureau NextProjectOS Aero
X-GNOME-Autostart-enabled=true
EOF

    # Lanceur pour picom
    cat > "$AUTOSTART_DIR/picom.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Picom (compositeur Aero)
Exec=picom --config $HOME/.config/picom/picom.conf
Comment=Compositeur d'effets Aero
X-GNOME-Autostart-enabled=true
EOF

    echo "✅ Démarrage automatique configuré"
}

# Créer le lanceur du shell
setup_shell_launcher() {
    echo "🖥️  Configuration du lanceur du shell..."

    mkdir -p "$HOME/.local/bin"
    BIN_DIR="$HOME/.local/bin"
    SOURCE_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"

    cat > "$BIN_DIR/npos-shell" << EOF
#!/bin/bash
# Lancement de l'environnement de bureau NextProjectOS
export PYTHONPATH="\$PYTHONPATH:$HOME/.local/share/npos"
exec python3 "$SOURCE_DIR/desktop/npshell/main.py"
EOF
    chmod +x "$BIN_DIR/npos-shell"

    echo "✅ Lanceur créé : $BIN_DIR/npos-shell"
}

# Menu principal
echo "Choisissez une option :"
echo "1) Installation complète (recommandée)"
echo "2) Installer uniquement les dépendances"
echo "3) Installer uniquement l'environnement de bureau"
echo "4) Installer uniquement les applications"
echo "5) Désinstaller NextProjectOS"
echo ""

read -p "Votre choix [1-5] : " choice

case $choice in
    1)
        install_deps
        install_desktop
        install_apps
        setup_shell_launcher
        setup_autostart

        echo ""
        echo "╔══════════════════════════════════════════════╗"
        echo "║   Installation terminée ! 🎉               ║"
        echo "║                                            ║"
        echo "║   Déconnectez-vous puis reconnectez-vous   ║"
        echo "║   ou redémarrez votre session.             ║"
        echo "║                                            ║"
        echo "║   Pour lancer le bureau Aero :             ║"
        echo "║     npos-shell                             ║"
        echo "╚══════════════════════════════════════════════╝"
        ;;
    2) install_deps ;;
    3) install_desktop ;;
    4) install_apps ;;
    5)
        echo "🗑️  Désinstallation..."
        rm -rf "$HOME/.local/share/npos"
        rm -rf "$HOME/.config/npos"
        rm -rf "$HOME/.local/share/themes/NextAero"
        rm -rf "$HOME/.local/share/icons/NPIcons"
        rm -f "$HOME/.local/bin/npos-shell"
        rm -f "$HOME/.config/autostart/npos-shell.desktop"
        echo "✅ Désinstallation terminée"
        ;;
    *)
        echo "❌ Choix invalide"
        exit 1
        ;;
esac
