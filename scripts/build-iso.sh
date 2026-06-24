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

# Étape 2: Monter les systèmes de fichiers nécessaires
echo "🔧 Montage des systèmes de fichiers..."
mount --bind /dev "$CHROOT_DIR/dev"
mount --bind /dev/pts "$CHROOT_DIR/dev/pts"
mount -t proc proc "$CHROOT_DIR/proc"
mount -t sysfs sys "$CHROOT_DIR/sys"

# Étape 3: Configuration du système
echo "⚙️  Configuration du système..."
cat > "$CHROOT_DIR/etc/hostname" << EOF
nextprojectos
EOF

cat > "$CHROOT_DIR/etc/hosts" << EOF
127.0.0.1   localhost
127.0.1.1   nextprojectos

# Réseau
::1         localhost ip6-localhost ip6-loopback
fe00::0     ip6-localnet
ff00::0     ip6-mcastprefix
ff02::1     ip6-allnodes
ff02::2     ip6-allrouters
EOF

cat > "$CHROOT_DIR/etc/apt/sources.list" << APT
# Debian bookworm (stable)
deb http://deb.debian.org/debian bookworm main contrib non-free-firmware
deb http://deb.debian.org/debian-security bookworm-security main contrib non-free-firmware
deb http://deb.debian.org/debian bookworm-updates main contrib non-free-firmware
APT

# Copier la configuration DNS (résout les problèmes de réseau dans le chroot)
cp /etc/resolv.conf "$CHROOT_DIR/etc/resolv.conf"

# Étape 4: Installation des paquets
echo "📥 Installation des paquets (cela peut prendre 5-10 minutes)..."
chroot "$CHROOT_DIR" apt-get update
chroot "$CHROOT_DIR" apt-get install -y --no-install-recommends \
    linux-image-amd64 live-boot systemd-sysv \
    xorg openbox \
    python3 python3-gi python3-gi-cairo \
    python3-gi-cairo gir1.2-gtk-3.0 gir1.2-gtksource-4 \
    gir1.2-vte-2.91 gir1.2-wnck-3.0 \
    picom \
    network-manager pulseaudio \
    fonts-cantarell fonts-dejavu-core \
    firefox-esr \
    xinit xterm \
    plymouth plymouth-themes \
    locales keyboard-configuration console-setup \
    nano \
    python3-pil plymouth-label plymouth-themes-spinfinity

# Configuration des locales (français)
echo "🌐 Configuration des locales fr_FR.UTF-8..."
chroot "$CHROOT_DIR" sed -i 's/^# *\(fr_FR.UTF-8\)/\1/' /etc/locale.gen
chroot "$CHROOT_DIR" locale-gen
chroot "$CHROOT_DIR" update-locale LANG=fr_FR.UTF-8 LANGUAGE=fr_FR.UTF-8 LC_ALL=fr_FR.UTF-8

# Configuration du clavier (AZERTY français)
echo "⌨️  Configuration du clavier AZERTY français..."
cat > "$CHROOT_DIR/etc/default/keyboard" << KEYB
# NextProjectOS - Clavier AZERTY français
XKBMODEL=pc105
XKBLAYOUT=fr
XKBVARIANT=
XKBOPTIONS=terminate:ctrl_alt_bksp
BACKSPACE=guess
KEYB

# Configuration du fuseau horaire Europe/Paris
echo "🕐 Configuration du fuseau horaire Europe/Paris..."
chroot "$CHROOT_DIR" ln -sf /usr/share/zoneinfo/Europe/Paris /etc/localtime
echo "Europe/Paris" > "$CHROOT_DIR/etc/timezone"

# Connexion automatique sur tty1
echo "🔑 Configuration de la connexion automatique..."
mkdir -p "$CHROOT_DIR/etc/systemd/system/getty@tty1.service.d"
cat > "$CHROOT_DIR/etc/systemd/system/getty@tty1.service.d/autologin.conf" << GETTY
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin user --noclear %I \$TERM
GETTY

# Créer un utilisateur par défaut pour le live
chroot "$CHROOT_DIR" useradd -m -G sudo,audio,video,input -s /bin/bash user 2>/dev/null || true
echo "user:user" | chroot "$CHROOT_DIR" chpasswd

# Configuration sudo sans mot de passe pour user
echo "user ALL=(ALL) NOPASSWD:ALL" > "$CHROOT_DIR/etc/sudoers.d/npos-user"

# Reconstruire l'initramfs avec live-boot
echo "🔧 Reconstruction de l'initramfs avec live-boot..."
chroot "$CHROOT_DIR" update-initramfs -u -k all

# Étape 5: Installation de l'environnement de bureau NPOS
echo "🖥️  Installation de l'environnement Aero..."
NPOS_DIR="/opt/npos"
mkdir -p "$CHROOT_DIR/$NPOS_DIR"
cp -r "$(dirname "$(dirname "$(readlink -f "$0")")")/desktop" "$CHROOT_DIR/$NPOS_DIR/"
cp -r "$(dirname "$(dirname "$(readlink -f "$0")")")/apps" "$CHROOT_DIR/$NPOS_DIR/"
cp -r "$(dirname "$(dirname "$(readlink -f "$0")")")/config" "$CHROOT_DIR/$NPOS_DIR/"

# Créer le lanceur système (démarrage auto de X + bureau)
cat > "$CHROOT_DIR/usr/bin/npos-session" << 'SESSION'
#!/bin/bash
# NextProjectOS Session
export PYTHONPATH="$PYTHONPATH:/opt/npos"

# Démarrer picom (compositeur Aero)
picom --config /opt/npos/desktop/compositor/picom.conf &

# Démarrer le shell NPOS
exec python3 /opt/npos/desktop/npshell/main.py
SESSION
chmod +x "$CHROOT_DIR/usr/bin/npos-session"

# Script de démarrage X (appelé par .bashrc ou .xinitrc)
cat > "$CHROOT_DIR/usr/bin/npos-startx" << 'STARTX'
#!/bin/bash
# NextProjectOS - Démarrage de la session X
xsetroot -solid "#0d47a1"
exec npos-session
STARTX
chmod +x "$CHROOT_DIR/usr/bin/npos-startx"

# Configurer .bashrc pour lancer X automatiquement sur tty1
cat > "$CHROOT_DIR/etc/skel/.bashrc" << BASHRC
# NextProjectOS - Lancement automatique du bureau
if [ -z "\$DISPLAY" ] && [ "\$(tty)" = "/dev/tty1" ]; then
    echo "🚀 Démarrage de NextProjectOS..."
    startx /usr/bin/npos-startx -- :0 vt1
fi
BASHRC

# Copier dans le home de l'utilisateur live
cp "$CHROOT_DIR/etc/skel/.bashrc" "$CHROOT_DIR/home/user/.bashrc"
chown 1000:1000 "$CHROOT_DIR/home/user/.bashrc"

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

# Étape 6: Configuration du thème par défaut
echo "🎨 Configuration du thème..."
mkdir -p "$CHROOT_DIR/etc/skel/.local/share/themes"
mkdir -p "$CHROOT_DIR/etc/skel/.local/share/icons"
mkdir -p "$CHROOT_DIR/etc/skel/.local/share/backgrounds"
mkdir -p "$CHROOT_DIR/etc/skel/.config"

# Copier depuis le dépot
cp -r "$CHROOT_DIR/$NPOS_DIR/desktop/theme/aero" "$CHROOT_DIR/etc/skel/.local/share/themes/NextAero"
cp -r "$CHROOT_DIR/$NPOS_DIR/desktop/theme/icons/np-icons" "$CHROOT_DIR/etc/skel/.local/share/icons/NPIcons"
cp -r "$CHROOT_DIR/$NPOS_DIR/desktop/wallpaper" "$CHROOT_DIR/etc/skel/.local/share/backgrounds/npos"

# Étape 7: Configuration du démarrage
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

# Étape 8: Nettoyage
echo "🧹 Nettoyage..."
chroot "$CHROOT_DIR" apt-get clean
rm -rf "$CHROOT_DIR/var/lib/apt/lists/*"
rm -rf "$CHROOT_DIR/tmp/*"
rm -rf "$CHROOT_DIR/root/.bash_history"

# Démontage des systèmes de fichiers
echo "🔌 Démontage des systèmes de fichiers..."
umount -l "$CHROOT_DIR/dev/pts" 2>/dev/null || true
umount -l "$CHROOT_DIR/dev" 2>/dev/null || true
umount -l "$CHROOT_DIR/proc" 2>/dev/null || true
umount -l "$CHROOT_DIR/sys" 2>/dev/null || true

# Réorganiser pour Debian Live (structure ISO standard)
ISO_STAGING="$WORK_DIR/iso-staging"
mkdir -p "$ISO_STAGING/live"
mkdir -p "$ISO_STAGING/isolinux"

# SquashFS du système racine
echo "📦 Création du squashfs..."
mksquashfs "$CHROOT_DIR" "$ISO_STAGING/live/filesystem.squashfs" \
    -comp xz -e boot
echo "   ✓ live/filesystem.squashfs créé"

# Copier le noyau et initrd dans isolinux + live
cp "$CHROOT_DIR/boot/vmlinuz-"* "$ISO_STAGING/isolinux/vmlinuz"
cp "$CHROOT_DIR/boot/vmlinuz-"* "$ISO_STAGING/live/vmlinuz"
cp "$CHROOT_DIR/boot/initrd.img-"* "$ISO_STAGING/isolinux/initrd.img"
cp "$CHROOT_DIR/boot/initrd.img-"* "$ISO_STAGING/live/initrd.img"

# Copier les fichiers ISOLINUX depuis le système hôte
echo "💿 Copie des modules ISOLINUX..."
ISOLINUX_MODULES="isolinux.bin ldlinux.c32 libutil.c32 libcom32.c32 vesamenu.c32 chain.c32"
SEARCH_DIRS="/usr/lib/ISOLINUX /usr/lib/syslinux/modules/bios /usr/lib/syslinux /usr/share/syslinux"

for f in $ISOLINUX_MODULES; do
    for d in $SEARCH_DIRS; do
        if [ -f "$d/$f" ]; then
            cp "$d/$f" "$ISO_STAGING/isolinux/$f"
            echo "   ✓ $f"
            break
        fi
    done
done

# Copier memtest si disponible
if [ -f "$CHROOT_DIR/boot/memtest86+"*.bin ]; then
    cp "$CHROOT_DIR/boot/memtest86+"*.bin "$ISO_STAGING/live/memtest"
fi

# Générer un splash screen pour le menu de boot
echo "🖼️  Génération du splash screen du boot..."
if command -v convert &>/dev/null; then
    # ImageMagick disponible - créer un splash aux couleurs Aero
    convert -size 640x480 gradient:'#0d47a1'-'#1e88e5' \
        -fill white -gravity center \
        -pointsize 28 -annotate +0-40 "NextProjectOS" \
        -pointsize 16 -annotate +0+20 "Developpement by AI" \
        "$ISO_STAGING/isolinux/splash.png" 2>/dev/null
elif command -v python3 &>/dev/null; then
    python3 -c "
from PIL import Image, ImageDraw, ImageFont
img = Image.new('RGB', (640, 480), '#0d47a1')
draw = ImageDraw.Draw(img)
for y in range(480):
    r = 13 + int((30-13) * y / 480)
    g = 71 + int((136-71) * y / 480)
    b = 161 + int((229-161) * y / 480)
    draw.line([(0,y), (639,y)], fill=(r,g,b))
img.save('$ISO_STAGING/isolinux/splash.png')
" 2>/dev/null
fi
# Si aucun outil, le menu texte s'affichera (le splash n'est pas critique)

# Vérifier les fichiers essentiels
if [ ! -f "$ISO_STAGING/isolinux/isolinux.bin" ]; then
    echo "❌ isolinux.bin introuvable. Installez : sudo apt install isolinux syslinux-common"
    exit 1
fi
if [ ! -f "$ISO_STAGING/isolinux/ldlinux.c32" ]; then
    echo "❌ ldlinux.c32 introuvable. Installez : sudo apt install syslinux-common"
    exit 1
fi
if [ ! -f "$ISO_STAGING/isolinux/vmlinuz" ]; then
    echo "❌ vmlinuz introuvable dans le chroot"
    exit 1
fi
if [ ! -f "$ISO_STAGING/live/filesystem.squashfs" ]; then
    echo "❌ filesystem.squashfs introuvable"
    exit 1
fi

# Créer le fichier filesystem.size (optionnel mais recommandé)
du -sb "$CHROOT_DIR" | cut -f1 > "$ISO_STAGING/live/filesystem.size"

# Menu de boot graphique ISOLINUX
cat > "$ISO_STAGING/isolinux/isolinux.cfg" << 'ISOCFG'
# NextProjectOS - Menu de démarrage
DEFAULT vesamenu.c32
TIMEOUT 300
PROMPT 0

MENU TITLE NextProjectOS
MENU BACKGROUND /isolinux/splash.png
MENU COLOR title       1;37;44   #ffffff #1e88e5 std
MENU COLOR border      30;44     #4fc3f7 #0d47a1 std
MENU COLOR sel         7;37;44   #ffffff #1e88e5 std
MENU COLOR hotsel      1;7;37;40 #ffffff #4fc3f7 std
MENU COLOR tabmsg      31;40     #4fc3f7 #000000 std
MENU COLOR unsel       37;44     #bbbbbb #0d47a1 std

LABEL npos
    MENU LABEL ^Démarrer NextProjectOS
    MENU DEFAULT
    KERNEL /live/vmlinuz
    APPEND initrd=/live/initrd.img boot=live live-media-path=/live quiet splash

LABEL npos-safe
    MENU LABEL ^Mode sans échec
    KERNEL /live/vmlinuz
    APPEND initrd=/live/initrd.img boot=live live-media-path=/live nomodeset xforcevesa

LABEL npos-en
    MENU LABEL Boot NextProjectOS (^English)
    KERNEL /live/vmlinuz
    APPEND initrd=/live/initrd.img boot=live live-media-path=/live quiet splash locale=en_US.UTF-8

LABEL local
    MENU LABEL ^Démarrer depuis le disque dur
    COM32 chain.c32
    APPEND hd0

LABEL memtest
    MENU LABEL Test ^mémoire (Memtest86+)
    KERNEL /live/memtest
ISOCFG

# Création de l'ISO
echo "💿 Génération de l'ISO..."
xorriso -as mkisofs \
    -iso-level 3 \
    -full-iso9660-filenames \
    -volid "NEXTOS" \
    -output "$OUTPUT_DIR/NextProjectOS.iso" \
    -isohybrid-mbr /usr/lib/ISOLINUX/isohdpfx.bin \
    -eltorito-boot isolinux/isolinux.bin \
    -eltorito-catalog isolinux/boot.cat \
    -no-emul-boot \
    -boot-load-size 4 \
    -boot-info-table \
    "$ISO_STAGING"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   ✅ ISO créée avec succès !                ║"
echo "╠══════════════════════════════════════════════╣"
echo "║                                            ║"
echo "║   📁 $OUTPUT_DIR/NextProjectOS.iso"  
echo "║                                            ║"
echo "║   🌐 Langue    : Français (fr_FR.UTF-8)    ║"
echo "║   ⌨️  Clavier   : AZERTY français           ║"
echo "║   🕐 Fuseau    : Europe/Paris              ║"
echo "║   👤 Utilisateur: user / user              ║"
echo "║                                            ║"
echo "╠══════════════════════════════════════════════╣"
echo "║   💿 Graver sur une clé USB :              ║"
echo "║   • Linux  : dd if=...iso of=/dev/sdX     ║"
echo "║   • Windows: Rufus (https://rufus.ie)     ║"
echo "║   • Mac    : balenaEtcher                  ║"
echo "╠══════════════════════════════════════════════╣"
echo "║   🔄 Taille du build :                      ║"
ISO_SIZE=$(du -sh "$OUTPUT_DIR/NextProjectOS.iso" 2>/dev/null | cut -f1)
[ -n "$ISO_SIZE" ] && echo "║      $ISO_SIZE" || echo "║      (inconnu)"
echo "╚══════════════════════════════════════════════╝"
