#!/bin/bash
# NextProjectOS - Construction d'une ISO live
# Basé sur Debian Live

set -e

echo "╔══════════════════════════════════════════════╗"
echo "║     NextProjectOS - Construction ISO        ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Support du mode non-interactif (appelé depuis Docker/WSL)
NON_INTERACTIVE=false
for arg in "$@"; do
    [ "$arg" = "--non-interactive" ] && NON_INTERACTIVE=true
done

ISO_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")/iso"
WORK_DIR="/tmp/npos-build"
CHROOT_DIR="$WORK_DIR/chroot"
OUTPUT_DIR="$ISO_DIR/output"

# Vérification des privilèges
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté en tant que root (sudo)."
    echo "   sudo bash scripts/build-iso.sh"
    exit 1
fi

# Vérification des outils requis
for cmd in debootstrap mksquashfs xorriso; do
    if ! command -v $cmd &> /dev/null; then
        echo "❌ $cmd n'est pas installé."
        echo "   Installez-le d'abord : sudo apt install debootstrap squashfs-tools xorriso"
        exit 1
    fi
done

echo "🚀 Début de la construction de l'ISO NextProjectOS..."
echo ""

# Nettoyage
echo "🧹 Nettoyage du répertoire de travail..."
rm -rf "$WORK_DIR"
mkdir -p "$CHROOT_DIR" "$OUTPUT_DIR" "$WORK_DIR"

# Étape 1: Debootstrap (système de base)
echo "📦 Création du système de base (Debian)..."
debootstrap --arch=amd64 --variant=minbase \
    bookworm "$CHROOT_DIR" http://deb.debian.org/debian/

# Étape 2: Configuration du système
echo "⚙️  Configuration du système..."
cat > "$CHROOT_DIR/etc/hostname" << EOF
nextprojectos
EOF

cat > "$CHROOT_DIR/etc/hosts" << EOF
127.0.0.1   localhost
127.0.1.1   nextprojectos
EOF

# Étape 3: Installation des paquets
echo "📥 Installation des paquets..."
chroot "$CHROOT_DIR" apt-get update
chroot "$CHROOT_DIR" apt-get install -y --no-install-recommends \
    linux-image-amd64 live-boot systemd-sysv \
    xorg openbox \
    python3 python3-gi python3-gi-cairo \
    gir1.2-gtk-3.0 gir1.2-gtksource-4 \
    gir1.2-vte-2.91 gir1.2-wnck-3.0 \
    picom \
    network-manager pulseaudio \
    fonts-cantarell fonts-dejavu \
    firefox-esr \
    xinit xterm \
    plymouth plymouth-themes

# Étape 4: Installation de l'environnement de bureau NPOS
echo "🖥️  Installation de l'environnement Aero..."
NPOS_DIR="/opt/npos"
mkdir -p "$CHROOT_DIR/$NPOS_DIR"
cp -r "$(dirname "$(dirname "$(readlink -f "$0")")")/desktop" "$CHROOT_DIR/$NPOS_DIR/"
cp -r "$(dirname "$(dirname "$(readlink -f "$0")")")/apps" "$CHROOT_DIR/$NPOS_DIR/"
cp -r "$(dirname "$(dirname "$(readlink -f "$0")")")/config" "$CHROOT_DIR/$NPOS_DIR/"

# Créer le lanceur système
cat > "$CHROOT_DIR/usr/bin/npos-session" << 'SESSION'
#!/bin/bash
# NextProjectOS Session
export PYTHONPATH="$PYTHONPATH:/opt/npos"

# Démarrer picom (compositeur Aero)
picom --config /opt/npos/desktop/compositor/picom.conf &

# Démarrer le shell NPOS
python3 /opt/npos/desktop/npshell/main.py
SESSION
chmod +x "$CHROOT_DIR/usr/bin/npos-session"

# Configurer Openbox comme WM de base
mkdir -p "$CHROOT_DIR/etc/xdg/openbox"
cat > "$CHROOT_DIR/etc/xdg/openbox/autostart" << 'OBMENU'
# NextProjectOS Openbox Autostart
npos-session &
OBMENU

# Créer un .desktop pour le démarrage automatique
mkdir -p "$CHROOT_DIR/etc/skel/.config/autostart"
cat > "$CHROOT_DIR/etc/skel/.config/autostart/npos-shell.desktop" << 'AUTOSTART'
[Desktop Entry]
Type=Application
Name=NextProjectOS Shell
Exec=npos-session
Comment=Environnement de bureau Aero
X-GNOME-Autostart-enabled=true
AUTOSTART

# Étape 5: Configuration du thème par défaut
echo "🎨 Configuration du thème..."
mkdir -p "$CHROOT_DIR/etc/skel/.local/share/themes"
mkdir -p "$CHROOT_DIR/etc/skel/.local/share/icons"
mkdir -p "$CHROOT_DIR/etc/skel/.local/share/backgrounds"
mkdir -p "$CHROOT_DIR/etc/skel/.config"

# Copier depuis le dépot
cp -r "$CHROOT_DIR/$NPOS_DIR/desktop/theme/aero" "$CHROOT_DIR/etc/skel/.local/share/themes/NextAero"
cp -r "$CHROOT_DIR/$NPOS_DIR/desktop/theme/icons/np-icons" "$CHROOT_DIR/etc/skel/.local/share/icons/NPIcons"
cp -r "$CHROOT_DIR/$NPOS_DIR/desktop/wallpaper" "$CHROOT_DIR/etc/skel/.local/share/backgrounds/npos"

# Étape 6: Configuration du démarrage
echo "🔧 Configuration du démarrage..."
mkdir -p "$CHROOT_DIR/boot/grub"

cat > "$CHROOT_DIR/etc/default/grub" << GRUB
GRUB_DEFAULT=0
GRUB_TIMEOUT=5
GRUB_DISTRIBUTOR="NextProjectOS"
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"
GRUB_CMDLINE_LINUX=""
GRUB_TERMINAL=console
GRUB_GFXMODE=1280x720
GRUB_BACKGROUND=/usr/share/backgrounds/npos/default.svg
GRUB
echo "GRUB_THEME=/boot/grub/themes/npos/theme.txt" >> "$CHROOT_DIR/etc/default/grub"

# Étape 7: Nettoyage
echo "🧹 Nettoyage..."
chroot "$CHROOT_DIR" apt-get clean
rm -rf "$CHROOT_DIR/var/lib/apt/lists/*"
rm -rf "$CHROOT_DIR/tmp/*"
rm -rf "$CHROOT_DIR/root/.bash_history"

# Étape 8: Création de l'ISO
echo "💿 Création de l'ISO..."

# SquashFS du système
mksquashfs "$CHROOT_DIR" "$WORK_DIR/filesystem.squashfs" \
    -comp xz -e boot

# Copier le noyau et initrd
mkdir -p "$WORK_DIR/isolinux"
cp "$CHROOT_DIR/boot/vmlinuz-"* "$WORK_DIR/isolinux/vmlinuz"
cp "$CHROOT_DIR/boot/initrd.img-"* "$WORK_DIR/isolinux/initrd"

# Configuration ISOLINUX
cat > "$WORK_DIR/isolinux/isolinux.cfg" << ISOLINUX
DEFAULT npos
LABEL npos
    SAY Démarrer NextProjectOS...
    KERNEL /isolinux/vmlinuz
    APPEND initrd=/isolinux/initrd boot=live quiet splash
ISOLINUX

# Création de l'ISO
xorriso -as mkisofs \
    -iso-level 3 \
    -full-iso9660-filenames \
    -volid "NextProjectOS" \
    -output "$OUTPUT_DIR/NextProjectOS.iso" \
    -isohybrid-mbr /usr/lib/ISOLINUX/isohdpfx.bin \
    -eltorito-boot isolinux/isolinux.bin \
    -eltorito-catalog isolinux/boot.cat \
    -no-emul-boot \
    -boot-load-size 4 \
    -boot-info-table \
    "$WORK_DIR"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   ISO créée avec succès ! 🎉               ║"
echo "║                                            ║"
echo "║   Fichier: $OUTPUT_DIR/NextProjectOS.iso   ║"
echo "║                                            ║"
echo "║   Gravez sur une clé USB avec:             ║"
echo "║     dd if=NextProjectOS.iso of=/dev/sdX    ║"
echo "╚══════════════════════════════════════════════╝"
