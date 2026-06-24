#!/bin/bash
# DEPRECATED - Utilisez pluto: sudo bash scripts/npos.sh build-iso
# NextProjectOS - Construction d'une ISO live

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
for cmd in debootstrap mksquashfs xorriso isohybrid; do
    if ! command -v $cmd &> /dev/null; then
        echo "❌ $cmd n'est pas installé."
        echo "   Installez-le d'abord : sudo apt install debootstrap squashfs-tools xorriso syslinux-utils"
        exit 1
    fi
done

echo "🚀 Début de la construction de l'ISO NextProjectOS..."
echo ""

# Fonction de nettoyage d'urgence (appelée en cas d'erreur)
cleanup_mounts() {
    local dir="$1"
    [ -z "$dir" ] && return
    # Démonter silencieusement tout ce qui est monté (ignorer les erreurs)
    umount -lf "$dir/dev/pts" 2>/dev/null || true
    umount -lf "$dir/dev" 2>/dev/null || true
    umount -lf "$dir/proc" 2>/dev/null || true
    umount -lf "$dir/sys" 2>/dev/null || true
}

# Nettoyage avant de commencer (démonte les vestiges d'une exécution précédente)
echo "🧹 Nettoyage du répertoire de travail..."
# Démontage des vestiges d'une exécution précédente (si existants)
[ -d "$CHROOT_DIR" ] && cleanup_mounts "$CHROOT_DIR"
# Suppression silencieuse du répertoire de travail précédent
rm -rf "$WORK_DIR" 2>/dev/null || true
mkdir -p "$CHROOT_DIR" "$OUTPUT_DIR" "$WORK_DIR"

# Piège pour nettoyer en cas d'erreur (sans faire echo pour éviter les boucles)
trap 'cleanup_mounts "$CHROOT_DIR" 2>/dev/null; rm -rf "$WORK_DIR" 2>/dev/null; exit 1' ERR INT TERM

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
    python3-pil plymouth-label plymouth-themes-spinfinity \
    librsvg2-common \
    parted rsync dosfstools efibootmgr

echo "📦 Installation de GRUB (paquets binaires pour cibles BIOS+UEFI)..."
chroot "$CHROOT_DIR" apt-get install -y --no-install-recommends \
    grub2-common grub-common \
    grub-pc-bin grub-efi-amd64-bin

# Configuration des locales (français)
echo "🌐 Configuration des locales fr_FR.UTF-8..."
chroot "$CHROOT_DIR" sed -i 's/^# *\(fr_FR.UTF-8\)/\1/' /etc/locale.gen
chroot "$CHROOT_DIR" locale-gen
chroot "$CHROOT_DIR" update-locale LANG=fr_FR.UTF-8 LANGUAGE=fr_FR.UTF-8 LC_ALL=fr_FR.UTF-8

# Configuration du clavier (AZERTY français)
echo "Configuration du clavier AZERTY francais..."
cat > "$CHROOT_DIR/etc/default/keyboard" << KEYB
# NextProjectOS - Clavier AZERTY français
XKBMODEL=pc105
XKBLAYOUT=fr
XKBVARIANT=
XKBOPTIONS=terminate:ctrl_alt_bksp
BACKSPACE=guess
KEYB

# Police console UTF-8 (support des accents)
echo "Configuration de la police console UTF-8..."
cat > "$CHROOT_DIR/etc/default/console-setup" << CONSFONT
# NextProjectOS - Console UTF-8
ACTIVE_CONSOLES="/dev/tty[1-6]"
CHARMAP="UTF-8"
CODESET="Lat2"
FONTFACE="Terminus"
FONTSIZE="16x32"
CONSFONT

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
mkdir -p "$CHROOT_DIR/etc/sudoers.d"
echo "user ALL=(ALL) NOPASSWD:ALL" > "$CHROOT_DIR/etc/sudoers.d/npos-user"
chmod 440 "$CHROOT_DIR/etc/sudoers.d/npos-user"

# Permettre a l'utilisateur console de lancer X (startx)
mkdir -p "$CHROOT_DIR/etc/X11"
cat > "$CHROOT_DIR/etc/X11/Xwrapper.config" << XWRAP
allowed_users=anybody
needs_root_rights=yes
XWRAP

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

# Creer les lanceurs en /usr/bin pour chaque app (points d'entree)
for app_dir in "$(dirname "$(dirname "$(readlink -f "$0")")")/apps/"*/; do
    app_name=$(basename "$app_dir")
    cat > "$CHROOT_DIR/usr/bin/$app_name" << LAUNCHER
#!/bin/bash
export PYTHONPATH="/opt/npos:\$PYTHONPATH"
exec python3 /opt/npos/apps/$app_name/main.py "\$@"
LAUNCHER
    chmod +x "$CHROOT_DIR/usr/bin/$app_name"
done

# Creer le lanceur systeme (demarrage auto de X + bureau)
cat > "$CHROOT_DIR/usr/bin/npos-session" << 'SESSION'
#!/bin/bash
# NextProjectOS Session
export PYTHONPATH="$PYTHONPATH:/opt/npos"
LOG="$HOME/.npos-session.log"

echo "[npos-session] Starting at $(date)" > "$LOG"

echo "[npos-session] DISPLAY=$DISPLAY" >> "$LOG"

# Demarrer Openbox (gestionnaire de fenetres)
openbox >> "$LOG" 2>&1 &
echo "[npos-session] Openbox started (PID=$!)" >> "$LOG"

# Demarrer picom (compositeur Aero)
picom --config /opt/npos/desktop/compositor/picom.conf >> "$LOG" 2>&1 &
echo "[npos-session] Picom started (PID=$!)" >> "$LOG"

# Demarrer le shell NPOS (court delai pour que X soit pret)
echo "[npos-session] Launching NPOS shell..." >> "$LOG"
exec python3 /opt/npos/desktop/npshell/main.py >> "$LOG" 2>&1
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

# Configurer .profile pour lancer X automatiquement sur tty1
# (les shells de connexion lisent .profile, pas .bashrc)
cat > "$CHROOT_DIR/etc/skel/.profile" << 'PROFILE'
# NextProjectOS - Auto-start desktop on tty1
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    echo "[NextProjectOS] Starting Aero desktop..." > /tmp/npos-autostart.log 2>&1
    startx /usr/bin/npos-startx >> /tmp/npos-autostart.log 2>&1
    echo "[NextProjectOS] X session ended." >> /tmp/npos-autostart.log
fi
PROFILE

# Copier dans le home de l'utilisateur live
if [ -d "$CHROOT_DIR/home/user" ]; then
    cp "$CHROOT_DIR/etc/skel/.profile" "$CHROOT_DIR/home/user/.profile"
    chown 1000:1000 "$CHROOT_DIR/home/user/.profile" 2>/dev/null || true
fi

# Configurer Openbox comme WM de base
mkdir -p "$CHROOT_DIR/etc/xdg/openbox"
cat > "$CHROOT_DIR/etc/xdg/openbox/rc.xml" << 'OBCONF'
<?xml version="1.0" encoding="UTF-8"?>
<openbox_config xmlns="http://openbox.org/3.4/rc">
  <theme>
    <name>NextAero</name>
    <titleLayout>NLIMC</titleLayout>
    <keepBorder>yes</keepBorder>
    <animateIconify>no</animateIconify>
    <font place="ActiveWindow">
      <name>Cantarell</name>
      <size>10</size>
      <weight>bold</weight>
    </font>
    <font place="InactiveWindow">
      <name>Cantarell</name>
      <size>10</size>
      <weight>normal</weight>
    </font>
    <font place="MenuHeader">
      <name>Cantarell</name>
      <size>10</size>
      <weight>bold</weight>
    </font>
    <font place="MenuItem">
      <name>Cantarell</name>
      <size>10</size>
      <weight>normal</weight>
    </font>
    <font place="ActiveOnScreenDisplay">
      <name>Cantarell</name>
      <size>10</size>
      <weight>normal</weight>
    </font>
    <font place="InactiveOnScreenDisplay">
      <name>Cantarell</name>
      <size>10</size>
      <weight>normal</weight>
    </font>
  </theme>
  <desktops>
    <number>1</number>
    <firstdesk>1</firstdesk>
    <names><name>Principal</name></names>
  </desktops>
  <resistance>
    <strength>10</strength>
    <screen_edge_strength>20</screen_edge_strength>
  </resistance>
  <focus>
    <focusNew>yes</focusNew>
    <followMouse>no</followMouse>
    <focusLast>yes</focusLast>
    <underMouse>no</underMouse>
    <focusDelay>200</focusDelay>
    <raiseOnFocus>no</raiseOnFocus>
  </focus>
  <placement>
    <policy>UnderMouse</policy>
    <center>yes</center>
    <monitor>Primary</monitor>
    <primaryMonitor>1</primaryMonitor>
  </placement>
  <mouse>
    <context menu="Root">
      <mousebutton button="Right" action="ShowMenu" root="true"/>
    </context>
    <context menu="Client">
      <mousebutton button="Left" action="Raise"/>
      <mousebutton button="Middle" action="Iconify"/>
      <mousebutton button="Right" action="Focus"/>
    </context>
  </mouse>
  <menu>
    <file>system-menu.xml</file>
    <hideDelay>200</hideDelay>
    <middle>no</middle>
    <submenuShowDelay>100</submenuShowDelay>
    <showIcons>yes</showIcons>
    <generate>yes</generate>
  </menu>
  <applications>
    <application class="*">
      <decor>yes</decor>
      <focus>yes</focus>
      <desktop>1</desktop>
      <layer>normal</layer>
    </application>
  </applications>
</openbox_config>
OBCONF

cat > "$CHROOT_DIR/etc/xdg/openbox/autostart" << 'OBMENU'
# NextProjectOS Openbox Autostart (minimal - npos-session demarre openbox)
true
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

# .desktop pour l'installateur
cat > "$CHROOT_DIR/usr/share/applications/nextinstaller.desktop" << 'INSTALLERDESK'
[Desktop Entry]
Type=Application
Name=NextInstaller
Comment=Installer NextProjectOS sur disque dur
Exec=python3 -m apps.nextinstaller.main
Icon=drive-harddisk
Terminal=false
Categories=System;
INSTALLERDESK

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
cleanup_mounts "$CHROOT_DIR"

# Réorganiser pour Debian Live (structure ISO standard)
ISO_STAGING="$WORK_DIR/iso-staging"
mkdir -p "$ISO_STAGING/live"
mkdir -p "$ISO_STAGING/isolinux"

# SquashFS du système racine
echo "📦 Création du squashfs..."
mksquashfs "$CHROOT_DIR" "$ISO_STAGING/live/filesystem.squashfs" \
    -comp xz
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
for m in "$CHROOT_DIR/boot/memtest86+"*.bin "$CHROOT_DIR/boot/memtest".bin; do
    [ -f "$m" ] && cp "$m" "$ISO_STAGING/live/memtest" && break
done

# Générer un splash screen pour le menu de boot (optionnel, pas critique)
echo "🖼️  Génération du splash screen du boot..."
SPLASH_OK=false
if command -v convert &>/dev/null; then
    convert -size 640x480 gradient:'#0d47a1'-'#1e88e5' \
        -fill white -gravity center \
        -pointsize 28 -annotate +0-40 "NextProjectOS" \
        -pointsize 16 -annotate +0+20 "Developpement by AI" \
        "$ISO_STAGING/isolinux/splash.png" 2>/dev/null && SPLASH_OK=true
fi
if [ "$SPLASH_OK" = false ] && command -v python3 &>/dev/null; then
    python3 -c "
import sys
try:
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (640, 480), '#0d47a1')
    draw = ImageDraw.Draw(img)
    for y in range(480):
        r = 13 + int((30-13) * y / 480)
        g = 71 + int((136-71) * y / 480)
        b = 161 + int((229-161) * y / 480)
        draw.line([(0,y), (639,y)], fill=(r,g,b))
    img.save('$ISO_STAGING/isolinux/splash.png')
    sys.exit(0)
except ImportError:
    sys.exit(1)
" 2>/dev/null && SPLASH_OK=true
fi
if [ "$SPLASH_OK" = true ]; then
    echo "   ✓ splash.png créé"
else
    echo "   - splash ignoré (ImageMagick ou PIL non disponible)"
fi

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
    MENU LABEL ^1) Boot NextProjectOS (AZERTY - Francais)
    MENU DEFAULT
    KERNEL /live/vmlinuz
    APPEND initrd=/live/initrd.img boot=live live-media-path=/live quiet splash

LABEL npos-safe
    MENU LABEL ^2) Mode sans echec (nomodeset)
    KERNEL /live/vmlinuz
    APPEND initrd=/live/initrd.img boot=live live-media-path=/live nomodeset xforcevesa

LABEL npos-en
    MENU LABEL ^3) Boot NextProjectOS (QWERTY - English)
    KERNEL /live/vmlinuz
    APPEND initrd=/live/initrd.img boot=live live-media-path=/live quiet splash locale=en_US.UTF-8

LABEL local
    MENU LABEL ^4) Boot from local disk
    COM32 chain.c32
    APPEND hd0

LABEL memtest
    MENU LABEL ^5) Memory test (Memtest86+)
    KERNEL /live/memtest
ISOCFG

# Création de l'ISO
echo "Generation de l'ISO..."
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

# Rendre l'ISO bootable en USB (isohybrid)
echo "Preparation du boot USB..."
if command -v isohybrid &>/dev/null; then
    isohybrid "$OUTPUT_DIR/NextProjectOS.iso" 2>/dev/null && echo "   ✓ isohybrid OK"
fi

echo ""
echo "+----------------------------------------------------+"
echo "| ISO creee avec succes !                            |"
echo "|                                                    |"
echo "| Fichier: $OUTPUT_DIR/NextProjectOS.iso"  
echo "|                                                    |"
echo "| Configuration par defaut dans le Live :            |"
echo "| - Langue    : Francais (fr_FR.UTF-8)              |"
echo "| - Clavier   : AZERTY francais                     |"
echo "| - Fuseau    : Europe/Paris                        |"
echo "| - Utilisateur: user / user                        |"
echo "|                                                    |"
echo "| Pour graver sur une cle USB :                     |"
echo "| - Linux  : dd if=...iso of=/dev/sdX bs=4M        |"
echo "| - Windows: Rufus (https://rufus.ie)              |"
echo "| - Mac    : balenaEtcher                           |"
echo "|                                                    |"
ISO_SIZE=$(du -sh "$OUTPUT_DIR/NextProjectOS.iso" 2>/dev/null | cut -f1)
[ -n "$ISO_SIZE" ] && echo "| Taille : $ISO_SIZE" || echo "| Taille : (inconnue)"
echo "+----------------------------------------------------+"

# Nettoyage final
echo "Nettoyage des fichiers temporaires..."
cleanup_mounts "$CHROOT_DIR" 2>/dev/null
rm -rf "$WORK_DIR" 2>/dev/null || true
trap - ERR INT TERM
