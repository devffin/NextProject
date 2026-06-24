#!/usr/bin/env python3
"""
NextLauncher - Lanceur d'applications Aero pour NextProjectOS
Lancement rapide d'applications avec recherche intégrée
"""
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
import os
import subprocess


class NextLauncherWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, type=Gtk.WindowType.POPUP)
        self.set_default_size(520, 380)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_keep_above(True)

        self._setup_style()
        self._build_ui()

        self.connect("key-press-event", self._on_key)

    def _setup_style(self):
        css = b"""
        #nl-window { background: rgba(20,20,30,0.92); border: 1px solid #4fc3f7; border-radius: 8px; }
        #nl-search { background: rgba(0,0,0,0.3); color: white; font-size: 18px; border: none; border-bottom: 2px solid #4fc3f7; border-radius: 0; padding: 12px 16px; }
        #nl-search:focus { box-shadow: none; }
        #nl-list { background: transparent; color: white; }
        #nl-list row { padding: 8px 16px; }
        #nl-list row:selected { background: rgba(30,136,229,0.4); }
        #nl-app-name { font-size: 14px; color: white; }
        #nl-app-desc { font-size: 11px; color: rgba(255,255,255,0.6); }
        #nl-app-icon { font-size: 24px; }
        """
        style = Gtk.CssProvider()
        style.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_ui(self):
        self.set_name("nl-window")
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_name("nl-search")
        self.search_entry.set_placeholder_text("Rechercher une application...")
        self.search_entry.connect("search-changed", self._on_search)
        self.search_entry.connect("activate", self._on_activate)
        vbox.pack_start(self.search_entry, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.app_list = Gtk.ListBox()
        self.app_list.set_name("nl-list")
        self.app_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.app_list.connect("row-activated", self._launch_app)

        self._populate_apps("")

        scroll.add(self.app_list)
        vbox.pack_start(scroll, True, True, 0)

        self.add(vbox)

    def _populate_apps(self, filter_text):
        for child in self.app_list.get_children():
            self.app_list.remove(child)

        filter_text = filter_text.lower()

        apps = [
            ("nextfile", "📁", "Explorateur de fichiers", "Naviguer dans vos fichiers"),
            ("nextterm", "💻", "Terminal", "Ligne de commande"),
            ("nextedit", "📝", "Éditeur de texte", "Modifier des fichiers texte"),
            ("nextcalc", "🧮", "Calculatrice", "Calculs mathématiques"),
            ("nextmedia", "🎵", "Musique", "Lecteur audio"),
            ("nextsettings", "⚙", "Paramètres", "Configuration du système"),
            ("nextinstaller", "💿", "Installateur", "Installer NPOS sur disque dur"),
        ]

        for app_id, icon, name, desc in apps:
            if filter_text and filter_text not in name.lower() and filter_text not in desc.lower():
                continue

            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            hbox.set_margin_top(4)
            hbox.set_margin_bottom(4)
            hbox.set_margin_left(8)
            hbox.set_margin_right(8)

            icon_lbl = Gtk.Label(label=icon)
            icon_lbl.set_name("nl-app-icon")
            hbox.pack_start(icon_lbl, False, False, 0)

            text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            name_lbl = Gtk.Label(label=name)
            name_lbl.set_name("nl-app-name")
            name_lbl.set_xalign(0)
            text_box.pack_start(name_lbl, False, False, 0)

            desc_lbl = Gtk.Label(label=desc)
            desc_lbl.set_name("nl-app-desc")
            desc_lbl.set_xalign(0)
            text_box.pack_start(desc_lbl, False, False, 0)

            hbox.pack_start(text_box, True, True, 0)
            row.add(hbox)
            row.app_id = app_id
            self.app_list.add(row)

        self.app_list.show_all()

    def _on_search(self, entry):
        self._populate_apps(entry.get_text())

    def _on_activate(self, entry):
        row = self.app_list.get_row_at_index(0)
        if row and hasattr(row, 'app_id'):
            self._launch(None, row)

    def _launch_app(self, listbox, row):
        if hasattr(row, 'app_id'):
            self._launch(None, row)

    def _launch(self, widget, row):
        try:
            subprocess.Popen([row.app_id], start_new_session=True)
        except FileNotFoundError:
            try:
                subprocess.Popen(
                    ["python3", "-m", f"apps.{row.app_id}.main"],
                    start_new_session=True,
                )
            except Exception:
                pass
        self.destroy()

    def _on_key(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
        return False

    def show(self):
        self.search_entry.grab_focus()
        Gtk.Window.show(self)


def main():
    win = NextLauncherWindow()
    win.show()
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    main()
