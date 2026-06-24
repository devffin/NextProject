#!/bin/bash
# NextProjectOS - Script tout-en-un
# Usage: sudo bash scripts/npos.sh <commande>
#
# Commandes :
#   build-iso   Construire l'ISO live
#   install     Installer NPOS sur ce systeme
#   desktop     Installer theme/icones/wallpaper
#   first-boot  Config post-installation
#   uninstall   Supprimer NPOS

set -e

NPOS_DIR="/opt/npos"
SOURCE_DIR="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
NON_INTERACTIVE=false
for arg in "$@"; do
    [ "$arg" = "--non-interactive" ] && NON_INTERACTIVE=true
done

show_usage() {
    echo "Usage: sudo bash scripts/npos.sh <commande>"
    echo ""
    echo "Commandes :"
    echo "  build-iso   Construire l'ISO live"
    echo "  install     Installer NPOS sur ce systeme"
    echo "  desktop     Installer theme/icones/wallpaper"
    echo "  first-boot  Config post-installation"
    echo "  uninstall   Supprimer NPOS"
    echo ""
    echo "Options :"
    echo "  --non-interactive  Mode automatique (pas de questions)"
}

# === BUILD ISO ===

build_iso() {
    echo "╔══════════════════════════════════════════════╗"
    echo "║     NextProjectOS - Construction ISO        ║"
    echo "╚══════════════════════════════════════════════╝"

    if [ "$EUID" -ne 0 ]; then
        echo "Erreur: Ce script doit etre execute en tant que root (sudo)." >&2
        exit 1
    fi

    for cmd in debootstrap mksquashfs xorriso isohybrid; do
        if ! command -v "$cmd" &>/dev/null; then
            echo "Erreur: $cmd nest pas installe." >&2
            echo "  sudo apt install debootstrap squashfs-tools xorriso syslinux-utils" >&2
            exit 1
        fi
    done

    ISO_DIR="$SOURCE_DIR/iso"
    WORK_DIR="/tmp/npos-build"
    CHROOT_DIR="$WORK_DIR/chroot"
    OUTPUT_DIR="$ISO_DIR/output"

    cleanup_mounts() {
        local dir="$1"
        [ -z "$dir" ] && return
        umount -lf "$dir/dev/pts" 2>/dev/null || true
        umount -lf "$dir/dev" 2>/dev/null || true
        umount -lf "$dir/proc" 2>/dev/null || true
        umount -lf "$dir/sys" 2>/dev/null || true
    }

    trap 'cleanup_mounts "$CHROOT_DIR" 2>/dev/null; rm -rf "$WORK_DIR" 2>/dev/null; exit 1' ERR INT TERM

    echo "Nettoyage du repertoire de travail..."
    [ -d "$CHROOT_DIR" ] && cleanup_mounts "$CHROOT_DIR"
    rm -rf "$WORK_DIR" 2>/dev/null || true
    mkdir -p "$CHROOT_DIR" "$OUTPUT_DIR" "$WORK_DIR"

    echo "Creation du systeme de base (Debian)..."
    debootstrap --arch=amd64 --variant=minbase \
        bookworm "$CHROOT_DIR" http://deb.debian.org/debian/

    echo "Montage des systemes de fichiers..."
    mount --bind /dev "$CHROOT_DIR/dev"
    mount --bind /dev/pts "$CHROOT_DIR/dev/pts"
    mount -t proc proc "$CHROOT_DIR/proc"
    mount -t sysfs sys "$CHROOT_DIR/sys"

    echo "Configuration du systeme..."
    echo "nextprojectos" > "$CHROOT_DIR/etc/hostname"

    cat > "$CHROOT_DIR/etc/hosts" << EOF
127.0.0.1   localhost
127.0.1.1   nextprojectos

::1         localhost ip6-localhost ip6-loopback
fe00::0     ip6-localnet
ff00::0     ip6-mcastprefix
ff02::1     ip6-allnodes
ff02::2     ip6-allrouters
EOF

    cat > "$CHROOT_DIR/etc/apt/sources.list" << APT
deb http://deb.debian.org/debian bookworm main contrib non-free-firmware
deb http://deb.debian.org/debian-security bookworm-security main contrib non-free-firmware
deb http://deb.debian.org/debian bookworm-updates main contrib non-free-firmware
APT

    cp /etc/resolv.conf "$CHROOT_DIR/etc/resolv.conf"

    echo "Installation des paquets (5-10 minutes)..."
    chroot "$CHROOT_DIR" apt-get update
    chroot "$CHROOT_DIR" apt-get install -y --no-install-recommends \
        linux-image-amd64 live-boot systemd-sysv \
        xorg openbox \
        python3 python3-gi python3-gi-cairo \
        python3-gi-cairo gir1.2-gtk-3.0 gir1.2-gtksource-4 \
        gir1.2-vte-2.91 gir1.2-wnck-3.0 \
        picom network-manager pulseaudio \
        fonts-cantarell fonts-dejavu-core \
        firefox-esr xinit xterm \
        plymouth plymouth-themes \
        locales keyboard-configuration console-setup nano \
        python3-pil plymouth-label plymouth-themes-spinfinity \
        librsvg2-common parted rsync dosfstools efibootmgr

    chroot "$CHROOT_DIR" apt-get install -y --no-install-recommends \
        grub2-common grub-common grub-pc-bin grub-efi-amd64-bin

    echo "Configuration des locales fr_FR.UTF-8..."
    chroot "$CHROOT_DIR" sed -i 's/^# *\(fr_FR.UTF-8\)/\1/' /etc/locale.gen
    chroot "$CHROOT_DIR" locale-gen
    chroot "$CHROOT_DIR" update-locale LANG=fr_FR.UTF-8 LANGUAGE=fr_FR.UTF-8 LC_ALL=fr_FR.UTF-8

    echo "Configuration du clavier AZERTY francais..."
    cat > "$CHROOT_DIR/etc/default/keyboard" << KEYB
XKBMODEL=pc105
XKBLAYOUT=fr
XKBVARIANT=
XKBOPTIONS=terminate:ctrl_alt_bksp
BACKSPACE=guess
KEYB

    cat > "$CHROOT_DIR/etc/default/console-setup" << CONSFONT
ACTIVE_CONSOLES="/dev/tty[1-6]"
CHARMAP="UTF-8"
CODESET="Lat2"
FONTFACE="Terminus"
FONTSIZE="16x32"
CONSFONT

    echo "Configuration du fuseau horaire Europe/Paris..."
    chroot "$CHROOT_DIR" ln -sf /usr/share/zoneinfo/Europe/Paris /etc/localtime
    echo "Europe/Paris" > "$CHROOT_DIR/etc/timezone"

    echo "Configuration de la connexion automatique..."
    mkdir -p "$CHROOT_DIR/etc/systemd/system/getty@tty1.service.d"
    cat > "$CHROOT_DIR/etc/systemd/system/getty@tty1.service.d/autologin.conf" << GETTY
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin user --noclear %I \$TERM
GETTY

    chroot "$CHROOT_DIR" useradd -m -G sudo,audio,video,input -s /bin/bash user 2>/dev/null || true
    echo "user:user" | chroot "$CHROOT_DIR" chpasswd

    mkdir -p "$CHROOT_DIR/etc/sudoers.d"
    echo "user ALL=(ALL) NOPASSWD:ALL" > "$CHROOT_DIR/etc/sudoers.d/npos-user"
    chmod 440 "$CHROOT_DIR/etc/sudoers.d/npos-user"

    mkdir -p "$CHROOT_DIR/etc/X11"
    cat > "$CHROOT_DIR/etc/X11/Xwrapper.config" << XWRAP
allowed_users=anybody
needs_root_rights=yes
XWRAP

    chroot "$CHROOT_DIR" update-initramfs -u -k all

    echo "Installation de lenvironnement Aero..."
    mkdir -p "$CHROOT_DIR/$NPOS_DIR"
    cp -r "$SOURCE_DIR/desktop" "$CHROOT_DIR/$NPOS_DIR/"
    cp -r "$SOURCE_DIR/apps" "$CHROOT_DIR/$NPOS_DIR/"
    cp -r "$SOURCE_DIR/config" "$CHROOT_DIR/$NPOS_DIR/"

    for app_dir in "$SOURCE_DIR/apps/"*/; do
        app_name=$(basename "$app_dir")
        cat > "$CHROOT_DIR/usr/bin/$app_name" << LAUNCHER
#!/bin/bash
export PYTHONPATH="/opt/npos:\$PYTHONPATH"
exec python3 /opt/npos/apps/$app_name/main.py "\$@"
LAUNCHER
        chmod +x "$CHROOT_DIR/usr/bin/$app_name"
    done

    cat > "$CHROOT_DIR/usr/bin/npos-session" << 'SESSION'
#!/bin/bash
export PYTHONPATH="$PYTHONPATH:/opt/npos"
LOG="$HOME/.npos-session.log"
echo "[npos-session] Starting at $(date)" > "$LOG"
echo "[npos-session] DISPLAY=$DISPLAY" >> "$LOG"
openbox >> "$LOG" 2>&1 &
echo "[npos-session] Openbox started (PID=$!)" >> "$LOG"
picom --config /opt/npos/desktop/compositor/picom.conf >> "$LOG" 2>&1 &
echo "[npos-session] Picom started (PID=$!)" >> "$LOG"
echo "[npos-session] Launching NPOS shell..." >> "$LOG"
exec python3 /opt/npos/desktop/npshell/main.py >> "$LOG" 2>&1
SESSION
    chmod +x "$CHROOT_DIR/usr/bin/npos-session"

    cat > "$CHROOT_DIR/usr/bin/npos-startx" << 'STARTX'
#!/bin/bash
xsetroot -solid "#0d47a1"
exec npos-session
STARTX
    chmod +x "$CHROOT_DIR/usr/bin/npos-startx"

    cat > "$CHROOT_DIR/etc/skel/.profile" << 'PROFILE'
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    echo "[NextProjectOS] Starting Aero desktop..." > /tmp/npos-autostart.log 2>&1
    startx /usr/bin/npos-startx >> /tmp/npos-autostart.log 2>&1
    echo "[NextProjectOS] X session ended." >> /tmp/npos-autostart.log
fi
PROFILE

    if [ -d "$CHROOT_DIR/home/user" ]; then
        cp "$CHROOT_DIR/etc/skel/.profile" "$CHROOT_DIR/home/user/.profile"
        chown 1000:1000 "$CHROOT_DIR/home/user/.profile" 2>/dev/null || true
    fi

    mkdir -p "$CHROOT_DIR/etc/xdg/openbox"
    cat > "$CHROOT_DIR/etc/xdg/openbox/rc.xml" << 'OBCONF'
<?xml version="1.0" encoding="UTF-8"?>
<openbox_config xmlns="http://openbox.org/3.4/rc">
  <theme>
    <name>NextAero</name>
    <titleLayout>NLIMC</titleLayout>
    <keepBorder>yes</keepBorder>
    <animateIconify>no</animateIconify>
    <font place="ActiveWindow"><name>Cantarell</name><size>10</size><weight>bold</weight></font>
    <font place="InactiveWindow"><name>Cantarell</name><size>10</size><weight>normal</weight></font>
    <font place="MenuHeader"><name>Cantarell</name><size>10</size><weight>bold</weight></font>
    <font place="MenuItem"><name>Cantarell</name><size>10</size><weight>normal</weight></font>
    <font place="ActiveOnScreenDisplay"><name>Cantarell</name><size>10</size><weight>normal</weight></font>
    <font place="InactiveOnScreenDisplay"><name>Cantarell</name><size>10</size><weight>normal</weight></font>
  </theme>
  <desktops><number>1</number><firstdesk>1</firstdesk><names><name>Principal</name></names></desktops>
  <resistance><strength>10</strength><screen_edge_strength>20</screen_edge_strength></resistance>
  <focus><focusNew>yes</focusNew><followMouse>no</followMouse><focusLast>yes</focusLast><underMouse>no</underMouse><focusDelay>200</focusDelay><raiseOnFocus>no</raiseOnFocus></focus>
  <placement><policy>UnderMouse</policy><center>yes</center><monitor>Primary</monitor><primaryMonitor>1</primaryMonitor></placement>
  <mouse>
    <context menu="Root"><mousebutton button="Right" action="ShowMenu" root="true"/></context>
    <context menu="Client">
      <mousebutton button="Left" action="Raise"/>
      <mousebutton button="Middle" action="Iconify"/>
      <mousebutton button="Right" action="Focus"/>
    </context>
  </mouse>
  <menu><file>system-menu.xml</file><hideDelay>200</hideDelay><middle>no</middle><submenuShowDelay>100</submenuShowDelay><showIcons>yes</showIcons><generate>yes</generate></menu>
  <applications>
    <application class="*"><decor>yes</decor><focus>yes</focus><desktop>1</desktop><layer>normal</layer></application>
  </applications>
</openbox_config>
OBCONF

    cat > "$CHROOT_DIR/etc/xdg/openbox/autostart" << 'OBMENU'
true
OBMENU

    mkdir -p "$CHROOT_DIR/etc/skel/.config/autostart"
    cat > "$CHROOT_DIR/etc/skel/.config/autostart/npos-shell.desktop" << 'AUTOSTART'
[Desktop Entry]
Type=Application
Name=NextProjectOS Shell
Exec=npos-session
Comment=Environnement de bureau Aero
X-GNOME-Autostart-enabled=true
AUTOSTART

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

    echo "Configuration du theme..."
    mkdir -p "$CHROOT_DIR/etc/skel/.local/share/themes"
    mkdir -p "$CHROOT_DIR/etc/skel/.local/share/icons"
    mkdir -p "$CHROOT_DIR/etc/skel/.local/share/backgrounds"
    mkdir -p "$CHROOT_DIR/etc/skel/.config"

    cp -r "$CHROOT_DIR/$NPOS_DIR/desktop/theme/aero" "$CHROOT_DIR/etc/skel/.local/share/themes/NextAero"
    cp -r "$CHROOT_DIR/$NPOS_DIR/desktop/theme/icons/np-icons" "$CHROOT_DIR/etc/skel/.local/share/icons/NPIcons"
    cp -r "$CHROOT_DIR/$NPOS_DIR/desktop/wallpaper" "$CHROOT_DIR/etc/skel/.local/share/backgrounds/npos"

    echo "Configuration du demarrage..."
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

    echo "Nettoyage..."
    chroot "$CHROOT_DIR" apt-get clean
    rm -rf "$CHROOT_DIR/var/lib/apt/lists/*"
    rm -rf "$CHROOT_DIR/tmp/*"
    rm -rf "$CHROOT_DIR/root/.bash_history"

    cleanup_mounts "$CHROOT_DIR"

    ISO_STAGING="$WORK_DIR/iso-staging"
    mkdir -p "$ISO_STAGING/live" "$ISO_STAGING/isolinux"

    echo "Creation du squashfs..."
    mksquashfs "$CHROOT_DIR" "$ISO_STAGING/live/filesystem.squashfs" -comp xz
    echo "   live/filesystem.squashfs cree"

    cp "$CHROOT_DIR/boot/vmlinuz-"* "$ISO_STAGING/isolinux/vmlinuz"
    cp "$CHROOT_DIR/boot/vmlinuz-"* "$ISO_STAGING/live/vmlinuz"
    cp "$CHROOT_DIR/boot/initrd.img-"* "$ISO_STAGING/isolinux/initrd.img"
    cp "$CHROOT_DIR/boot/initrd.img-"* "$ISO_STAGING/live/initrd.img"

    echo "Copie des modules ISOLINUX..."
    ISOLINUX_MODULES="isolinux.bin ldlinux.c32 libutil.c32 libcom32.c32 vesamenu.c32 chain.c32"
    SEARCH_DIRS="/usr/lib/ISOLINUX /usr/lib/syslinux/modules/bios /usr/lib/syslinux /usr/share/syslinux"
    for f in $ISOLINUX_MODULES; do
        for d in $SEARCH_DIRS; do
            if [ -f "$d/$f" ]; then
                cp "$d/$f" "$ISO_STAGING/isolinux/$f"
                echo "   $f"
                break
            fi
        done
    done

    for m in "$CHROOT_DIR/boot/memtest86+"*.bin "$CHROOT_DIR/boot/memtest".bin; do
        [ -f "$m" ] && cp "$m" "$ISO_STAGING/live/memtest" && break
    done

    echo "Generation du splash screen du boot..."
    SPLASH_OK=false
    if command -v convert &>/dev/null; then
        convert -size 640x480 gradient:'#0d47a1'-'#1e88e5' \
            -fill white -gravity center \
            -pointsize 28 -annotate +0-40 "NextProjectOS" \
            -pointsize 16 -annotate +0+20 "Development by AI" \
            "$ISO_STAGING/isolinux/splash.png" 2>/dev/null && SPLASH_OK=true
    fi
    if [ "$SPLASH_OK" = false ] && python3 -c "from PIL import Image; print('ok')" 2>/dev/null; then
        python3 -c "
from PIL import Image, ImageDraw
img = Image.new('RGB', (640, 480), '#0d47a1')
draw = ImageDraw.Draw(img)
for y in range(480):
    r = 13 + int((30-13) * y / 480)
    g = 71 + int((136-71) * y / 480)
    b = 161 + int((229-161) * y / 480)
    draw.line([(0,y), (639,y)], fill=(r,g,b))
img.save('$ISO_STAGING/isolinux/splash.png')
" 2>/dev/null && SPLASH_OK=true
    fi
    [ "$SPLASH_OK" = true ] && echo "   splash.png cree" || echo "   splash ignore"

    for f in "$ISO_STAGING/isolinux/isolinux.bin" "$ISO_STAGING/isolinux/ldlinux.c32" "$ISO_STAGING/isolinux/vmlinuz" "$ISO_STAGING/live/filesystem.squashfs"; do
        [ ! -f "$f" ] && echo "Erreur: $f introuvable" >&2 && exit 1
    done

    du -sb "$CHROOT_DIR" | cut -f1 > "$ISO_STAGING/live/filesystem.size"

    cat > "$ISO_STAGING/isolinux/isolinux.cfg" << 'ISOCFG'
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

    echo "Generation de lISO..."
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

    command -v isohybrid &>/dev/null && isohybrid "$OUTPUT_DIR/NextProjectOS.iso" 2>/dev/null && echo "   isohybrid OK"

    ISO_SIZE=$(du -sh "$OUTPUT_DIR/NextProjectOS.iso" 2>/dev/null | cut -f1)
    echo ""
    echo "+----------------------------------------------------+"
    echo "| ISO creee avec succes !                            |"
    echo "| Fichier: $OUTPUT_DIR/NextProjectOS.iso"
    echo "| Taille : $ISO_SIZE"
    echo "+----------------------------------------------------+"

    cleanup_mounts "$CHROOT_DIR" 2>/dev/null
    rm -rf "$WORK_DIR" 2>/dev/null || true
    trap - ERR INT TERM
}

# === INSTALL ===

install() {
    echo "╔══════════════════════════════════════════════╗"
    echo "║     NextProjectOS - Installation            ║"
    echo "╚══════════════════════════════════════════════╝"

    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
    else
        DISTRO=$(uname -s)
    fi

    echo "Distribution detectee : $DISTRO"

    install_deps() {
        echo "Installation des dependances..."
        case $DISTRO in
            debian|ubuntu)
                sudo apt-get update
                sudo apt-get install -y \
                    python3 python3-gi python3-gi-cairo \
                    gir1.2-gtk-3.0 gir1.2-gtksource-4 \
                    gir1.2-vte-2.91 gir1.2-wnck-3.0 \
                    picom openbox fonts-cantarell librsvg2-common
                ;;
            fedora)
                sudo dnf install -y \
                    python3 python3-gobject python3-gobject-cairo \
                    gtk3 gtksourceview4 vte291 libwnck3 \
                    picom openbox cantarell-fonts librsvg2
                ;;
            arch|manjaro)
                sudo pacman -S --noconfirm \
                    python python-gobject python-cairo gtk3 gtksourceview4 vte3 \
                    libwnck3 picom openbox cantarell-fonts librsvg
                ;;
            *)
                echo "Distribution non reconnue. Installez les dependances manuellement." >&2
                ;;
        esac
    }

    install_desktop() {
        echo "Installation de lenvironnement de bureau..."
        local share="$HOME/.local/share"
        local config="$HOME/.config"
        local theme="$share/themes/NextAero"
        local icons="$share/icons/NPIcons"
        local wp="$share/backgrounds/npos"
        local apps="$share/npos/apps"

        mkdir -p "$share/npos" "$config/npos" "$theme" "$icons" "$wp" "$apps" "$share/applications"

        cp -r "$SOURCE_DIR/desktop/theme/aero/"* "$theme/"
        cp -r "$SOURCE_DIR/desktop/theme/icons/np-icons/"* "$icons/"
        cp -r "$SOURCE_DIR/desktop/wallpaper/"* "$wp/"
        cp "$SOURCE_DIR/config/npos.conf" "$config/npos/" 2>/dev/null || true

        mkdir -p "$config/picom"
        cp "$SOURCE_DIR/desktop/compositor/picom.conf" "$config/picom/"

        mkdir -p "$HOME/.local/bin"
        for app in nextfile nextterm nextedit nextcalc nextmedia nextsettings nextlauncher nextinstaller; do
            cat > "$HOME/.local/bin/$app" << EOF
#!/bin/bash
export PYTHONPATH="\$HOME/.local/share/npos:\$PYTHONPATH"
exec python3 "$apps/$app/main.py" "\$@"
EOF
            chmod +x "$HOME/.local/bin/$app"

            cat > "$share/applications/npos-$app.desktop" << EOF
[Desktop Entry]
Name=Next$app
Comment=Application NextProjectOS
Exec=$HOME/.local/bin/$app
Icon=$icons/scalable/apps/$app.svg
Terminal=false
Type=Application
Categories=Utility;
StartupNotify=true
EOF
        done

        if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
            echo "export PATH=\"\$PATH:\$HOME/.local/bin\"" >> "$HOME/.bashrc"
        fi
    }

    setup_autostart() {
        echo "Configuration du demarrage automatique..."
        mkdir -p "$HOME/.config/autostart"

        cat > "$HOME/.config/autostart/npos-shell.desktop" << EOF
[Desktop Entry]
Type=Application
Name=NextProjectOS Shell
Exec=$HOME/.local/bin/npos-shell
X-GNOME-Autostart-enabled=true
EOF

        cat > "$HOME/.config/autostart/picom.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Picom (compositeur Aero)
Exec=picom --config $HOME/.config/picom/picom.conf
X-GNOME-Autostart-enabled=true
EOF
    }

    setup_shell_launcher() {
        mkdir -p "$HOME/.local/bin"
        cat > "$HOME/.local/bin/npos-shell" << EOF
#!/bin/bash
export PYTHONPATH="\$PYTHONPATH:\$HOME/.local/share/npos"
exec python3 "$SOURCE_DIR/desktop/npshell/main.py"
EOF
        chmod +x "$HOME/.local/bin/npos-shell"
    }

    install_deps
    install_desktop
    setup_shell_launcher
    setup_autostart

    echo ""
    echo "Installation terminee !"
    echo "Lancez le bureau Aero avec: npos-shell"
}

# === DESKTOP ===

setup_desktop() {
    echo "Configuration du bureau Aero..."

    local share="$HOME/.local/share"
    local config="$HOME/.config"
    local theme="$share/themes/NextAero"
    local icons="$share/icons/NPIcons"
    local wp="$share/backgrounds/npos"

    mkdir -p "$share/npos" "$config/npos" "$theme" "$icons" "$wp"

    cp -r "$SOURCE_DIR/desktop/theme/aero/"* "$theme/"
    cp -r "$SOURCE_DIR/desktop/theme/icons/np-icons/"* "$icons/"
    cp -r "$SOURCE_DIR/desktop/wallpaper/"* "$wp/"

    mkdir -p "$config/picom"
    cp "$SOURCE_DIR/desktop/compositor/picom.conf" "$config/picom/"

    mkdir -p "$config/gtk-3.0"
    cat > "$config/gtk-3.0/settings.ini" << GTK
[Settings]
gtk-theme-name=NextAero
gtk-icon-theme-name=NPIcons
gtk-font-name=Cantarell 10
gtk-application-prefer-dark-theme=0
GTK

    gsettings set org.gnome.desktop.interface gtk-theme "NextAero" 2>/dev/null || true
    gsettings set org.gnome.desktop.interface icon-theme "NPIcons" 2>/dev/null || true

    echo "Configuration terminee !"
    echo "Lancez picom: picom --config ~/.config/picom/picom.conf &"
    echo "Lancez le bureau: python3 $SOURCE_DIR/desktop/npshell/main.py"
}

# === FIRST BOOT ===

first_boot() {
    echo "Premier demarrage NextProjectOS..."

    local config="$HOME/.config/npos"
    mkdir -p "$config"

    if [ ! -f "$config/npos.conf" ]; then
        cat > "$config/npos.conf" << CONF
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
        echo "Configuration par defaut creee"
    fi

    mkdir -p "$HOME/.config/gtk-3.0"
    cat > "$HOME/.config/gtk-3.0/settings.ini" << 'GTK'
[Settings]
gtk-theme-name=NextAero
gtk-icon-theme-name=NPIcons
gtk-font-name=Cantarell 10
gtk-application-prefer-dark-theme=0
GTK

    if command -v picom &>/dev/null && [ -f "$HOME/.config/picom/picom.conf" ]; then
        picom --config "$HOME/.config/picom/picom.conf" &
        echo "Compositeur Aero demarre"
    fi

    echo "NextProjectOS est pret !"
}

# === UNINSTALL ===

uninstall() {
    echo "Suppression de NextProjectOS..."

    rm -rf "$HOME/.local/share/npos"
    rm -rf "$HOME/.config/npos"
    rm -rf "$HOME/.local/share/themes/NextAero"
    rm -rf "$HOME/.local/share/icons/NPIcons"
    rm -f "$HOME/.local/bin/npos-shell" "$HOME/.local/bin/nextfile" "$HOME/.local/bin/nextterm" "$HOME/.local/bin/nextedit" "$HOME/.local/bin/nextcalc" "$HOME/.local/bin/nextmedia" "$HOME/.local/bin/nextsettings" "$HOME/.local/bin/nextlauncher" "$HOME/.local/bin/nextinstaller"
    rm -f "$HOME/.config/autostart/npos-shell.desktop" "$HOME/.config/autostart/picom.desktop"
    rm -rf "$HOME/.local/share/applications/npos-"*.desktop

    echo "NextProjectOS a ete supprime."
}

# === MAIN ===

CMD="${1:-help}"
shift 2>/dev/null || true

case "$CMD" in
    build-iso)
        build_iso "$@"
        ;;
    install)
        install "$@"
        ;;
    desktop)
        setup_desktop "$@"
        ;;
    first-boot)
        first_boot "$@"
        ;;
    uninstall)
        uninstall "$@"
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        echo "Commande inconnue: $CMD" >&2
        echo ""
        show_usage
        exit 1
        ;;
esac
