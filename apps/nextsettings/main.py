#!/usr/bin/env python3
"""
NextSettings - Centre de configuration Aero pour NextProjectOS
Personnalisation du thème, fond d'écran, panneau, dock
"""
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Gio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from desktop.npshell.config import NPOSConfig, WALLPAPER_DIR


class NextSettingsWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="NextSettings - Paramètres")
        self.set_default_size(800, 550)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.config = NPOSConfig()

        self._setup_style()
        self._build_ui()
        self.show_all()

    def _setup_style(self):
        css = b"""
        #ns-sidebar { background: rgba(0,0,0,0.15); }
        #ns-sidebar row { color: white; padding: 8px 16px; }
        #ns-sidebar row:selected { background: rgba(30,136,229,0.4); }
        #ns-content { background: rgba(0,0,0,0.08); padding: 20px; }
        #ns-section-title { color: #4fc3f7; font-weight: bold; font-size: 18px; }
        #ns-label { color: rgba(255,255,255,0.8); font-size: 13px; }
        #ns-entry { background: rgba(0,0,0,0.2); color: white; border: 1px solid rgba(79,195,247,0.3); border-radius: 4px; padding: 6px 10px; }
        #ns-combo { background: rgba(0,0,0,0.2); color: white; border: 1px solid rgba(79,195,247,0.3); border-radius: 4px; }
        #ns-combo cellview { color: white; }
        #ns-btn { background: rgba(30,136,229,0.3); color: white; border: none; border-radius: 4px; padding: 6px 16px; }
        #ns-btn:hover { background: rgba(30,136,229,0.5); }
        #ns-switch:checked { background: #4fc3f7; }
        #ns-color-btn { min-width: 32px; min-height: 32px; border-radius: 50%; border: 2px solid rgba(255,255,255,0.3); }
        """
        style = Gtk.CssProvider()
        style.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_ui(self):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        self._build_sidebar(hbox)
        self._build_content(hbox)

        self.add(hbox)

    def _build_sidebar(self, parent):
        scroll = Gtk.ScrolledWindow()
        scroll.set_name("ns-sidebar")
        scroll.set_size_request(200, -1)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.sidebar = Gtk.ListBox()
        self.sidebar.set_selection_mode(Gtk.SelectionMode.SINGLE)

        sections = [
            ("🖥", "Apparence"),
            ("🎨", "Personnaliser"),
            ("🖼", "Fond d'écran"),
            ("📋", "Panneau"),
            ("⬇", "Dock"),
            ("⚙", "Avancé"),
            ("ℹ", "À propos"),
        ]

        for icon, label in sections:
            row = Gtk.ListBoxRow()
            h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            lbl = Gtk.Label(label=f"{icon}  {label}")
            lbl.set_xalign(0)
            h.pack_start(lbl, True, True, 0)
            row.add(h)
            row.section = label
            self.sidebar.add(row)

        self.sidebar.connect("row-activated", self._on_section_activate)
        scroll.add(self.sidebar)
        parent.pack_start(scroll, False, True, 0)

        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        parent.pack_start(sep, False, False, 0)

    def _build_content(self, parent):
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.set_name("ns-content")
        parent.pack_start(self.content, True, True, 0)

        self._show_appearance()

    def _on_section_activate(self, listbox, row):
        section = row.section
        for child in self.content.get_children():
            self.content.remove(child)
        {
            "Apparence": self._show_appearance,
            "Personnaliser": self._show_customize,
            "Fond d'écran": self._show_wallpaper,
            "Panneau": self._show_panel,
            "Dock": self._show_dock,
            "Avancé": self._show_advanced,
            "À propos": self._show_about,
        }.get(section, self._show_appearance)()

    def _show_appearance(self):
        self._add_title("Apparence")
        self._add_label("Thème Aero NextProjectOS")
        self._add_label("Personnalisez l'apparence de votre bureau avec des effets de verre transparent style Aero.")

        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        info_box.set_margin_top(16)
        info_box.set_margin_bottom(16)
        info_box.set_margin_left(8)
        info_box.set_margin_right(8)

        for item in [
            ("Thème GTK:", f"{self.config.get('Theme', 'gtk_theme')}"),
            ("Thème d'icônes:", f"{self.config.get('Theme', 'icon_theme')}"),
            ("Police:", f"{self.config.get('Theme', 'font')}"),
            ("Couleur d'accentuation:", f"{self.config.get('Theme', 'accent_color')}"),
            ("Couleur de verre:", f"{self.config.get('Theme', 'glass_color')}"),
        ]:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            lbl = Gtk.Label(label=item[0])
            lbl.set_name("ns-label")
            lbl.set_size_request(160, -1)
            lbl.set_xalign(1)
            row.pack_start(lbl, False, False, 0)

            val = Gtk.Label(label=item[1])
            val.set_name("ns-label")
            val.set_xalign(0)
            row.pack_start(val, False, False, 0)
            info_box.pack_start(row, False, False, 0)

        self.content.pack_start(info_box, False, False, 0)

        self._add_button("Appliquer le thème", self._apply_theme)

    def _show_customize(self):
        self._add_title("Personnaliser")

        accent_box = self._make_color_picker("Couleur d'accentuation", self.config.get("Theme", "accent_color"))
        self.content.pack_start(accent_box, False, False, 8)

        glass_box = self._make_color_picker("Couleur de verre Aero", self.config.get("Theme", "glass_color"))
        self.content.pack_start(glass_box, False, False, 8)

        self._add_label(f"Police: {self.config.get('Theme', 'font')}")
        self._add_label(f"Taille des icônes du bureau: {self.config.get('Desktop', 'icon_size')}px")
        self._add_label(f"Ombre des icônes: {'Activée' if self.config.getboolean('Desktop', 'text_shadow') else 'Désactivée'}")

    def _make_color_picker(self, label, color):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lbl = Gtk.Label(label=label)
        lbl.set_name("ns-label")
        lbl.set_size_request(200, -1)
        box.pack_start(lbl, False, False, 0)

        color_btn = Gtk.ColorButton()
        try:
            c = Gdk.RGBA()
            c.parse(color)
            color_btn.set_rgba(c)
        except Exception:
            pass
        color_btn.set_title(f"Choisir {label}")
        box.pack_start(color_btn, False, False, 0)

        hex_entry = Gtk.Entry()
        hex_entry.set_text(color)
        hex_entry.set_width_chars(10)
        hex_entry.set_name("ns-entry")
        box.pack_start(hex_entry, False, False, 4)

        return box

    def _show_wallpaper(self):
        self._add_title("Fond d'écran")

        preview = Gtk.DrawingArea()
        preview.set_size_request(-1, 200)
        preview.connect("draw", self._draw_wallpaper_preview)
        self.content.pack_start(preview, False, False, 8)

        self._add_label(f"Fond actuel: {self.config.get('Desktop', 'wallpaper')}")
        self._add_label(f"Style: {self.config.get('Desktop', 'wallpaper_style')}")

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_margin_top(8)
        self._add_button_to("Changer le fond d'écran...", self._change_wallpaper, btn_box)
        self._add_button_to("Par défaut", self._reset_wallpaper, btn_box)
        self.content.pack_start(btn_box, False, False, 0)

    def _draw_wallpaper_preview(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()

        cr.set_source_rgba(0.1, 0.2, 0.4, 0.5)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        cr.set_source_rgba(0.3, 0.6, 0.9, 1)
        cr.arc(w - 60, 60, 30, 0, 2 * 3.14159)
        cr.fill()

        cr.set_source_rgba(0.2, 0.5, 0.2, 1)
        cr.rectangle(0, h * 0.7, w, h * 0.3)
        cr.fill()

        cr.set_source_rgba(0.3, 0.7, 0.3, 1)
        cr.arc(w * 0.3, h * 0.5, 40, 0, 2 * 3.14159)
        cr.fill()

        cr.set_source_rgba(0.15, 0.6, 0.15, 1)
        cr.move_to(w * 0.7 + 30, h * 0.65)
        cr.line_to(w * 0.7, h * 0.9)
        cr.line_to(w * 0.7 + 60, h * 0.9)
        cr.close_path()
        cr.fill()

    def _change_wallpaper(self, btn):
        dialog = Gtk.FileChooserDialog(
            "Choisir un fond d'écran", self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT),
        )
        filt = Gtk.FileFilter()
        filt.set_name("Images")
        filt.add_mime_type("image/*")
        dialog.add_filter(filt)

        if dialog.run() == Gtk.ResponseType.ACCEPT:
            path = dialog.get_filename()
            self.config.set("Desktop", "wallpaper", path)
            self.config.save()
        dialog.destroy()

    def _reset_wallpaper(self, btn):
        default = os.path.join(WALLPAPER_DIR, "default.svg")
        self.config.set("Desktop", "wallpaper", default)
        self.config.save()

    def _show_panel(self):
        self._add_title("Panneau")

        for item in [
            ("Position:", self.config.get("Panel", "position")),
            ("Hauteur:", f"{self.config.get('Panel', 'height')}px"),
            ("Opacité:", f"{int(self.config.getfloat('Panel', 'opacity') * 100)}%"),
            ("Effet verre:", "Oui" if self.config.getboolean("Panel", "glass_effect") else "Non"),
            ("Masquage auto:", "Oui" if self.config.getboolean("Panel", "autohide") else "Non"),
        ]:
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            box.set_margin_top(4)
            box.set_margin_bottom(4)
            lbl = Gtk.Label(label=item[0])
            lbl.set_name("ns-label")
            lbl.set_size_request(160, -1)
            lbl.set_xalign(1)
            box.pack_start(lbl, False, False, 0)
            val = Gtk.Label(label=item[1])
            val.set_name("ns-label")
            val.set_xalign(0)
            box.pack_start(val, False, False, 0)
            self.content.pack_start(box, False, False, 0)

    def _show_dock(self):
        self._add_title("Dock")
        enabled = self.config.getboolean("Dock", "enabled")
        self._add_label(f"Dock: {'Activé' if enabled else 'Désactivé'}")
        self._add_label(f"Position: {self.config.get('Dock', 'position')}")
        self._add_label(f"Taille des icônes: {self.config.getint('Dock', 'icon_size')}px")
        self._add_label(f"Opacité: {int(self.config.getfloat('Dock', 'opacity') * 100)}%")

    def _show_advanced(self):
        self._add_title("Paramètres avancés")

        for key in ["Compositor", "shadow", "blur", "animation", "fade"]:
            val = self.config.getboolean(key[0], key[1]) if len(key) == 2 else False
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            box.set_margin_top(4)
            box.set_margin_bottom(4)
            lbl = Gtk.Label(label=f"{key[1].capitalize()}:")
            lbl.set_name("ns-label")
            lbl.set_size_request(160, -1)
            lbl.set_xalign(1)
            box.pack_start(lbl, False, False, 0)

            switch = Gtk.Switch()
            switch.set_name("ns-switch")
            switch.set_active(val)
            box.pack_start(switch, False, False, 0)
            self.content.pack_start(box, False, False, 0)

    def _show_about(self):
        self._add_title("À propos de NextProjectOS")

        about_text = (
            "NextProjectOS (NPOS)\n\n"
            "Version: 1.0.0\n"
            "Environnement de bureau Aero\n"
            "Basé sur Linux\n\n"
            "Un OS moderne avec un bureau transparent\n"
            "style Aero, personnalisable et performant.\n\n"
            "© 2026 NextProjectOS"
        )
        lbl = Gtk.Label(label=about_text)
        lbl.set_name("ns-label")
        lbl.set_justify(Gtk.Justification.CENTER)
        lbl.set_margin_top(32)
        lbl.set_margin_bottom(32)
        self.content.pack_start(lbl, False, False, 0)

    def _add_title(self, text):
        lbl = Gtk.Label(label=text)
        lbl.set_name("ns-section-title")
        lbl.set_xalign(0)
        lbl.set_margin_bottom(12)
        self.content.pack_start(lbl, False, False, 0)

    def _add_label(self, text):
        lbl = Gtk.Label(label=text)
        lbl.set_name("ns-label")
        lbl.set_xalign(0)
        lbl.set_margin_top(2)
        lbl.set_margin_bottom(2)
        lbl.set_margin_left(4)
        self.content.pack_start(lbl, False, False, 0)

    def _add_button(self, text, cb):
        btn = Gtk.Button(label=text)
        btn.set_name("ns-btn")
        btn.connect("clicked", cb)
        btn.set_margin_top(8)
        self.content.pack_start(btn, False, False, 0)

    def _add_button_to(self, text, cb, parent):
        btn = Gtk.Button(label=text)
        btn.set_name("ns-btn")
        btn.connect("clicked", cb)
        parent.pack_start(btn, False, False, 0)

    def _apply_theme(self, btn):
        self.config.save()


def main():
    win = NextSettingsWindow()
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    main()
