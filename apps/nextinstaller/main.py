#!/usr/bin/env python3
"""
NextInstaller - Installateur NPOS pour disque dur
Interface Aero pour installer NextProjectOS sur le disque
"""
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import os
import subprocess
import threading


class NextInstaller(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="NextInstaller - Installer NPOS")
        self.set_default_size(720, 520)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(False)

        self.step = 0
        self.total_steps = 5
        self.target_disk = None
        self.hostname = "nextprojectos"
        self.username = "user"
        self.password = "user"
        self.use_efi = os.path.exists("/sys/firmware/efi")

        self._setup_style()
        self._build_ui()
        self._update_step()
        self.show_all()

    def _setup_style(self):
        css = b"""
        #ni-header { background: linear-gradient(to bottom, #1e88e5, #0d47a1); padding: 16px; }
        #ni-title { color: white; font-size: 22px; font-weight: bold; }
        #ni-subtitle { color: rgba(255,255,255,0.8); font-size: 12px; }
        #ni-content { background: rgba(10,10,20,0.85); padding: 20px; }
        #ni-label { color: white; font-size: 13px; }
        #ni-entry { background: rgba(255,255,255,0.1); color: white; border: 1px solid #4fc3f7; border-radius: 4px; padding: 6px 10px; }
        #ni-btn { background: linear-gradient(to bottom, #4fc3f7, #1e88e5); color: white; border: none; border-radius: 4px; padding: 8px 24px; font-weight: bold; }
        #ni-btn:hover { background: linear-gradient(to bottom, #6dd5fa, #2196f3); }
        #ni-btn:disabled { background: rgba(255,255,255,0.1); color: rgba(255,255,255,0.3); }
        #ni-disk-row { color: white; padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.1); }
        #ni-disk-row:selected { background: rgba(30,136,229,0.4); }
        #ni-progress { background: rgba(255,255,255,0.1); border-radius: 4px; }
        #ni-progress trough { min-height: 6px; border-radius: 4px; }
        #ni-progress highlight { background: linear-gradient(to bottom, #4fc3f7, #1e88e5); border-radius: 4px; }
        #ni-log { background: rgba(0,0,0,0.3); color: #4fc3f7; font-family: monospace; font-size: 11px; border-radius: 4px; }
        #ni-step-counter { color: rgba(255,255,255,0.6); font-size: 11px; }
        """
        style = Gtk.CssProvider()
        style.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Header fixe
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        header.set_name("ni-header")
        title = Gtk.Label(label="NextInstaller")
        title.set_name("ni-title")
        header.pack_start(title, False, False, 0)
        self.step_label = Gtk.Label(label="")
        self.step_label.set_name("ni-subtitle")
        header.pack_start(self.step_label, False, False, 0)
        vbox.pack_start(header, False, False, 0)

        # Contenu
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.content.set_name("ni-content")
        vbox.pack_start(self.content, True, True, 0)

        # Barre de progression
        self.progress = Gtk.ProgressBar()
        self.progress.set_name("ni-progress")
        self.progress.set_show_text(True)
        vbox.pack_start(self.progress, False, False, 0)

        # Boutons navigation
        nav = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        nav.set_margin_top(8)
        nav.set_margin_bottom(8)
        nav.set_margin_left(8)
        nav.set_margin_right(8)

        self.back_btn = Gtk.Button(label="< Retour")
        self.back_btn.set_name("ni-btn")
        self.back_btn.connect("clicked", self._on_back)
        nav.pack_start(self.back_btn, False, False, 0)

        self.next_btn = Gtk.Button(label="Suivant >")
        self.next_btn.set_name("ni-btn")
        self.next_btn.connect("clicked", self._on_next)
        nav.pack_end(self.next_btn, False, False, 0)

        vbox.pack_start(nav, False, False, 0)
        self.add(vbox)

    def _clear_content(self):
        for c in self.content.get_children():
            self.content.remove(c)

    def _update_step(self):
        self.progress.set_fraction(self.step / self.total_steps)
        self.progress.set_text(f"Etape {self.step}/{self.total_steps}")
        self.step_label.set_text(f"Etape {self.step} sur {self.total_steps}")
        self.back_btn.set_sensitive(self.step > 1)
        self.next_btn.set_sensitive(True)
        {
            0: self._step_welcome,
            1: self._step_disk,
            2: self._step_config,
            3: self._step_install,
            4: self._step_finish,
        }.get(self.step, self._step_welcome)()

    def _step_welcome(self):
        self._clear_content()
        self.next_btn.set_label("Commencer >")

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_valign(Gtk.Align.CENTER)
        vbox.set_halign(Gtk.Align.CENTER)

        logo = Gtk.DrawingArea()
        logo.set_size_request(80, 80)
        logo.connect("draw", self._draw_logo)
        vbox.pack_start(logo, False, False, 0)

        lbl = Gtk.Label(label="Bienvenue sur NextProjectOS !")
        lbl.set_name("ni-title")
        vbox.pack_start(lbl, False, False, 0)

        desc = Gtk.Label(
            label="Cet assistant va installer NPOS sur votre ordinateur.\n\n"
                  "Boot : " + ("UEFI" if self.use_efi else "Legacy BIOS") + "\n\n"
                  "Prerequisites :\n"
                  "  - Au moins 10 Go de libre sur le disque\n"
                  "  - Une connexion internet (optionnel)\n\n"
                  "Le disque selectionne sera ENTIEREMENT EFFACE."
        )
        desc.set_name("ni-label")
        desc.set_justify(Gtk.Justification.CENTER)
        desc.set_line_wrap(True)
        vbox.pack_start(desc, False, False, 0)

        self.content.pack_start(vbox, True, True, 0)

    def _step_disk(self):
        self._clear_content()
        self.next_btn.set_label("Installer >")
        self.next_btn.set_sensitive(False)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        lbl = Gtk.Label(label="Selectionnez le disque pour l'installation :")
        lbl.set_name("ni-label")
        lbl.set_xalign(0)
        vbox.pack_start(lbl, False, False, 0)

        lbl2 = Gtk.Label(label="ATTENTION : Tout le contenu du disque sera efface !")
        lbl2.set_name("ni-label")
        lbl2.set_xalign(0)
        lbl2.set_opacity(0.7)
        vbox.pack_start(lbl2, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.disk_list = Gtk.ListBox()
        self.disk_list.connect("row-activated", self._on_disk_selected)

        try:
            output = subprocess.check_output(
                ["lsblk", "-d", "-o", "NAME,SIZE,TYPE,MODEL", "-n"],
                universal_newlines=True,
            )
            for line in output.strip().split("\n"):
                parts = line.split()
                if not parts:
                    continue
                name = parts[0]
                size = parts[1] if len(parts) > 1 else "?"
                model = " ".join(parts[3:]) if len(parts) > 3 else name
                if parts[2] == "disk":
                    row = Gtk.ListBoxRow()
                    h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                    h.set_margin_top(6)
                    h.set_margin_bottom(6)
                    h.set_margin_left(12)
                    h.set_margin_right(12)

                    icon = Gtk.Label(label="[HDD]")
                    h.pack_start(icon, False, False, 0)

                    info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                    name_lbl = Gtk.Label(label=f"/dev/{name}  ({size})")
                    name_lbl.set_name("ni-label")
                    name_lbl.set_xalign(0)
                    info.pack_start(name_lbl, False, False, 0)

                    model_lbl = Gtk.Label(label=model)
                    model_lbl.set_name("ni-label")
                    model_lbl.set_opacity(0.6)
                    model_lbl.set_xalign(0)
                    info.pack_start(model_lbl, False, False, 0)

                    h.pack_start(info, True, True, 0)
                    row.add(h)
                    row.disk = f"/dev/{name}"
                    self.disk_list.add(row)
        except Exception:
            lbl_err = Gtk.Label(label="Impossible de lister les disques.")
            self.disk_list.add(lbl_err)

        scroll.add(self.disk_list)
        vbox.pack_start(scroll, True, True, 0)
        self.content.pack_start(vbox, True, True, 0)

    def _on_disk_selected(self, listbox, row):
        if hasattr(row, 'disk'):
            self.target_disk = row.disk
            self.next_btn.set_sensitive(True)

    def _step_config(self):
        self._clear_content()
        self.next_btn.set_label("Installer >")

        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(12)
        grid.set_margin_top(20)
        grid.set_margin_left(40)
        grid.set_margin_right(40)

        # Hostname
        lbl = Gtk.Label(label="Nom du systeme (hostname) :")
        lbl.set_name("ni-label")
        lbl.set_xalign(1)
        grid.attach(lbl, 0, 0, 1, 1)

        self.hostname_entry = Gtk.Entry(text=self.hostname)
        self.hostname_entry.set_name("ni-entry")
        grid.attach(self.hostname_entry, 1, 0, 1, 1)

        # Utilisateur
        lbl = Gtk.Label(label="Nom d'utilisateur :")
        lbl.set_name("ni-label")
        lbl.set_xalign(1)
        grid.attach(lbl, 0, 1, 1, 1)

        self.user_entry = Gtk.Entry(text=self.username)
        self.user_entry.set_name("ni-entry")
        grid.attach(self.user_entry, 1, 1, 1, 1)

        # Mot de passe
        lbl = Gtk.Label(label="Mot de passe :")
        lbl.set_name("ni-label")
        lbl.set_xalign(1)
        grid.attach(lbl, 0, 2, 1, 1)

        self.pass_entry = Gtk.Entry(text=self.password)
        self.pass_entry.set_name("ni-entry")
        self.pass_entry.set_visibility(False)
        grid.attach(self.pass_entry, 1, 2, 1, 1)

        # Clavier
        lbl = Gtk.Label(label="Disposition clavier :")
        lbl.set_name("ni-label")
        lbl.set_xalign(1)
        grid.attach(lbl, 0, 3, 1, 1)

        self.kbd_combo = Gtk.ComboBoxText()
        self.kbd_combo.append("fr", "AZERTY (Francais)")
        self.kbd_combo.append("be", "AZERTY (Belge)")
        self.kbd_combo.append("de", "QWERTZ (Allemand)")
        self.kbd_combo.append("us", "QWERTY (USA)")
        self.kbd_combo.append("gb", "QWERTY (UK)")
        self.kbd_combo.append("ch", "QWERTZ (Suisse)")
        self.kbd_combo.set_active(0)
        self.kbd_combo.set_name("ni-entry")
        grid.attach(self.kbd_combo, 1, 3, 1, 1)

        # Info disque
        disk_info = Gtk.Label(label=f"Installation sur : {self.target_disk or '(aucun)'}")
        disk_info.set_name("ni-label")
        disk_info.set_opacity(0.7)
        disk_info.set_margin_top(16)
        grid.attach(disk_info, 0, 4, 2, 1)

        self.content.pack_start(grid, True, True, 0)

    def _step_install(self):
        self._clear_content()
        self.next_btn.set_label("Finaliser >")
        self.next_btn.set_sensitive(False)
        self.back_btn.set_sensitive(False)

        self.hostname = self.hostname_entry.get_text()
        self.username = self.user_entry.get_text()
        self.password = self.pass_entry.get_text()
        kbd_iter = self.kbd_combo.get_active_iter()
        self.keyboard = self.kbd_combo.get_model()[kbd_iter][0] if kbd_iter else "fr"

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        lbl = Gtk.Label(label="Installation en cours...")
        lbl.set_name("ni-title")
        vbox.pack_start(lbl, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.log_view = Gtk.TextView()
        self.log_view.set_name("ni-log")
        self.log_view.set_editable(False)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.log_buffer = self.log_view.get_buffer()
        scroll.add(self.log_view)
        vbox.pack_start(scroll, True, True, 0)

        self.content.pack_start(vbox, True, True, 0)

        # Lancer l'installation dans un thread
        thread = threading.Thread(target=self._do_install, daemon=True)
        thread.start()

    def _log(self, msg):
        GLib.idle_add(self._append_log, msg)

    def _append_log(self, msg):
        end = self.log_buffer.get_end_iter()
        self.log_buffer.insert(end, msg + "\n")
        return False

    def _run_cmd(self, cmd, check=True):
        self._log(f"> {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.stdout:
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        self._log(f"  {line}")
            if result.returncode != 0:
                self._log(f"  [ERROR] {result.stderr[:200]}")
                if check:
                    return False
            return True
        except Exception as e:
            self._log(f"  [ERROR] {e}")
            return False

    def _do_install(self):
        disk = self.target_disk
        if not disk:
            self._log("[ERROR] Aucun disque selectionne")
            return

        # Étape 1 : Partitionnement
        self._log("=== Partitionnement du disque ===")
        if self.use_efi:
            # UEFI: /boot/efi + / (ext4)
            parted_cmds = (
                f"parted -s {disk} mklabel gpt",
                f"parted -s {disk} mkpart primary fat32 1MiB 512MiB",
                f"parted -s {disk} set 1 esp on",
                f"parted -s {disk} mkpart primary ext4 512MiB 100%",
            )
        else:
            # BIOS: / (ext4) + swap
            parted_cmds = (
                f"parted -s {disk} mklabel msdos",
                f"parted -s {disk} mkpart primary ext4 1MiB 100%",
                f"parted -s {disk} set 1 boot on",
            )

        for cmd in parted_cmds:
            if not self._run_cmd(cmd.split()):
                self._log("[ERROR] Partitionnement echoue")
                return

        # Obtenir le nom des partitions
        parts = subprocess.check_output(["lsblk", "-nlo", "NAME", disk], universal_newlines=True).strip().split("\n")
        parts = [f"/dev/{p}" for p in parts if p != disk.split("/")[-1]]

        if self.use_efi and len(parts) >= 2:
            efi_part = parts[0]
            root_part = parts[1]
        else:
            root_part = parts[0]
            efi_part = None

        # Étape 2 : Formater
        self._log("=== Formatage des partitions ===")
        if not self._run_cmd(["mkfs.ext4", "-F", root_part]):
            return
        if efi_part:
            self._run_cmd(["mkfs.fat", "-F32", efi_part])

        # Étape 3 : Montage
        self._log("=== Montage ===")
        self._run_cmd(["mount", root_part, "/mnt"])
        if efi_part:
            self._run_cmd(["mkdir", "-p", "/mnt/boot/efi"])
            self._run_cmd(["mount", efi_part, "/mnt/boot/efi"])

        # Étape 4 : Copie du système live
        self._log("=== Copie du systeme (cela peut prendre plusieurs minutes) ===")
        exclude = "--exclude=/proc --exclude=/sys --exclude=/dev --exclude=/tmp --exclude=/mnt --exclude=/run"
        cmd = f"rsync -aAX {exclude} / /mnt/"
        if not self._run_cmd(cmd.split()):
            # Essayer avec cp si rsync n'est pas dispo
            self._log("rsync pas disponible, utilisation de cp...")
            if not self._run_cmd(["cp", "-ax", "--exclude=/proc", "--exclude=/sys",
                                 "--exclude=/dev", "--exclude=/tmp", "--exclude=/mnt",
                                 "--exclude=/run", "/", "/mnt/"]):
                return

        # Étape 5 : Chroot et configuration
        self._log("=== Configuration du systeme installe ===")

        # Chroot + mount proc/sys/dev
        chroot_cmds = [
            "mount --bind /dev /mnt/dev",
            "mount --bind /dev/pts /mnt/dev/pts",
            "mount -t proc proc /mnt/proc",
            "mount -t sysfs sys /mnt/sys",
        ]
        for c in chroot_cmds:
            self._run_cmd(c.split())

        # Hostname
        self._log(f"Configuration hostname : {self.hostname}")
        self._run_cmd(["chroot", "/mnt", "bash", "-c", f"echo '{self.hostname}' > /etc/hostname"])
        self._run_cmd(["chroot", "/mnt", "bash", "-c",
                       f"sed -i 's/127.0.1.1.*/127.0.1.1\\t{self.hostname}/' /etc/hosts"])

        # Locale
        self._run_cmd(["chroot", "/mnt", "bash", "-c",
                       "sed -i 's/^# *\\(fr_FR.UTF-8\\)/\\1/' /etc/locale.gen"])
        self._run_cmd(["chroot", "/mnt", "locale-gen"])
        self._run_cmd(["chroot", "/mnt", "update-locale", "LANG=fr_FR.UTF-8"])

        # Clavier
        self._run_cmd(["chroot", "/mnt", "bash", "-c",
                       f"echo 'XKBLAYOUT={self.keyboard}' > /etc/default/keyboard"])

        # Grub
        self._log("=== Installation de GRUB ===")
        if self.use_efi:
            self._run_cmd(["chroot", "/mnt", "apt-get", "install", "-y", "grub-efi"])
            self._run_cmd(["chroot", "/mnt", "grub-install", "--target=x86_64-efi",
                          "--efi-directory=/boot/efi", "--bootloader-id=NextProjectOS"])
        else:
            self._run_cmd(["chroot", "/mnt", "grub-install", disk])

        self._run_cmd(["chroot", "/mnt", "update-grub"])

        # Créer l'utilisateur
        self._log(f"Creation de l'utilisateur : {self.username}")
        self._run_cmd(["chroot", "/mnt", "useradd", "-m", "-G", "sudo,audio,video,input",
                       "-s", "/bin/bash", self.username])
        self._run_cmd(["chroot", "/mnt", "bash", "-c",
                       f"echo '{self.username}:{self.password}' | chpasswd"])

        # Nettoyage
        self._log("=== Nettoyage ===")
        for c in reversed([
            "umount -l /mnt/dev/pts",
            "umount -l /mnt/dev",
            "umount -l /mnt/proc",
            "umount -l /mnt/sys",
        ]):
            self._run_cmd(c.split(), check=False)

        self._run_cmd(["umount", "-lf", "/mnt/boot/efi"], check=False)
        self._run_cmd(["umount", "-lf", "/mnt"])

        self._log("")
        self._log("=== INSTALLATION TERMINEE ! ===")
        self._log("Vous pouvez redemarrer sur le disque installe.")

        GLib.idle_add(self._install_done)

    def _install_done(self):
        self.next_btn.set_sensitive(True)
        self.back_btn.set_sensitive(True)

    def _step_finish(self):
        self._clear_content()
        self.next_btn.set_label("Redemarrer")
        self.next_btn.connect("clicked", lambda b: self._run_cmd(["reboot"]))

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_valign(Gtk.Align.CENTER)
        vbox.set_halign(Gtk.Align.CENTER)

        lbl = Gtk.Label(label="Installation terminee !")
        lbl.set_name("ni-title")
        vbox.pack_start(lbl, False, False, 0)

        desc = Gtk.Label(
            label=f"NextProjectOS a ete installe sur {self.target_disk}.\n\n"
                  f"Utilisateur : {self.username}\n"
                  f"Mot de passe : {self.password}\n"
                  f"Clavier : {self.keyboard}\n\n"
                  "Retirez le support d'installation et cliquez sur Redemarrer."
        )
        desc.set_name("ni-label")
        desc.set_justify(Gtk.Justification.CENTER)
        desc.set_line_wrap(True)
        vbox.pack_start(desc, False, False, 0)

        self.content.pack_start(vbox, True, True, 0)

    def _draw_logo(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        cr.set_source_rgba(0.3, 0.6, 0.9, 0.3)
        cr.arc(w / 2, h / 2, min(w, h) / 2 - 4, 0, 2 * 3.14159)
        cr.fill()
        cr.set_source_rgba(1, 1, 1, 0.8)
        cr.select_font_face("Arial", 0, 1)
        cr.set_font_size(36)
        cr.move_to(w / 2 - 14, h / 2 + 12)
        cr.show_text("N")

    def _on_next(self, btn):
        self.step += 1
        if self.step > self.total_steps:
            self.step = self.total_steps
        self._update_step()

    def _on_back(self, btn):
        self.step -= 1
        if self.step < 0:
            self.step = 0
        self._update_step()


def main():
    win = NextInstaller()
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    main()
