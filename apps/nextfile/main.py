#!/usr/bin/env python3
"""
NextFile - Explorateur de fichiers Aero pour NextProjectOS
Avec onglets, aperçu, navigation par chemins
"""
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango, Gio, GdkPixbuf
import os
import subprocess


class NextFileWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="NextFile - Explorateur de fichiers")
        self.set_default_size(900, 600)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.current_path = os.path.expanduser("~")
        self.history = []
        self.history_pos = -1

        self._setup_style()
        self._build_ui()
        self._navigate_to(self.current_path)
        self.show_all()

    def _setup_style(self):
        css = b"""
        #nf-toolbar { background: rgba(30,136,229,0.15); padding: 2px; }
        #nf-toolbar button { background: rgba(255,255,255,0.1); border: none; color: white; border-radius: 4px; }
        #nf-toolbar button:hover { background: rgba(255,255,255,0.2); }
        #nf-toolbar entry { background: rgba(0,0,0,0.2); color: white; border: 1px solid #4fc3f7; }
        #nf-sidebar { background: rgba(0,0,0,0.15); }
        #nf-sidebar row { color: white; padding: 4px 8px; }
        #nf-sidebar row:selected { background: rgba(30,136,229,0.4); }
        #nf-view { background: rgba(0,0,0,0.1); color: white; }
        #nf-view:selected { background: rgba(30,136,229,0.4); }
        #nf-statusbar { background: rgba(0,0,0,0.2); color: rgba(255,255,255,0.7); font-size: 11px; }
        """
        style = Gtk.CssProvider()
        style.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self._build_toolbar(vbox)
        self._build_main_area(vbox)
        self._build_statusbar(vbox)

        self.add(vbox)

    def _build_toolbar(self, parent):
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        toolbar.set_name("nf-toolbar")
        toolbar.set_margin_top(2)
        toolbar.set_margin_bottom(2)
        toolbar.set_margin_left(4)
        toolbar.set_margin_right(4)

        self.back_btn = Gtk.Button(label="◀")
        self.back_btn.set_tooltip_text("Retour")
        self.back_btn.connect("clicked", self._go_back)
        toolbar.pack_start(self.back_btn, False, False, 0)

        self.fwd_btn = Gtk.Button(label="▶")
        self.fwd_btn.set_tooltip_text("Suivant")
        self.fwd_btn.connect("clicked", self._go_forward)
        toolbar.pack_start(self.fwd_btn, False, False, 0)

        self.up_btn = Gtk.Button(label="⬆")
        self.up_btn.set_tooltip_text("Dossier parent")
        self.up_btn.connect("clicked", self._go_up)
        toolbar.pack_start(self.up_btn, False, False, 0)

        self.home_btn = Gtk.Button(label="⌂")
        self.home_btn.set_tooltip_text("Dossier personnel")
        self.home_btn.connect("clicked", lambda b: self._navigate_to(os.path.expanduser("~")))
        toolbar.pack_start(self.home_btn, False, False, 0)

        self.path_entry = Gtk.Entry()
        self.path_entry.set_hexpand(True)
        self.path_entry.connect("activate", self._on_path_enter)
        toolbar.pack_start(self.path_entry, True, True, 4)

        self.refresh_btn = Gtk.Button(label="⟳")
        self.refresh_btn.set_tooltip_text("Actualiser")
        self.refresh_btn.connect("clicked", self._refresh)
        toolbar.pack_start(self.refresh_btn, False, False, 0)

        parent.pack_start(toolbar, False, False, 0)

    def _build_main_area(self, parent):
        hpaned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)

        self._build_sidebar(hpaned)
        self._build_file_view(hpaned)

        hpaned.set_position(180)
        parent.pack_start(hpaned, True, True, 0)

    def _build_sidebar(self, parent):
        sidebar = Gtk.ScrolledWindow()
        sidebar.set_name("nf-sidebar")
        sidebar.set_size_request(160, -1)
        sidebar.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.sidebar_list = Gtk.ListBox()
        self.sidebar_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.sidebar_list.connect("row-activated", self._on_sidebar_activate)

        places = [
            ("⌂", "Dossier personnel", os.path.expanduser("~")),
            ("🖥", "Ordinateur", "/"),
            ("📄", "Documents", os.path.expanduser("~/Documents")),
            ("📥", "Téléchargements", os.path.expanduser("~/Downloads")),
            ("🎵", "Musique", os.path.expanduser("~/Music")),
            ("🖼", "Images", os.path.expanduser("~/Pictures")),
            ("🎬", "Vidéos", os.path.expanduser("~/Videos")),
            ("🗑", "Corbeille", "trash://"),
        ]

        for icon, label, path in places:
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            hbox.set_margin_top(4)
            hbox.set_margin_bottom(4)
            hbox.set_margin_left(8)
            hbox.set_margin_right(8)
            lbl = Gtk.Label(label=f"{icon}  {label}")
            lbl.set_xalign(0)
            lbl.set_name("nf-sidebar-label")
            hbox.pack_start(lbl, True, True, 0)
            row.add(hbox)
            row.path = path
            self.sidebar_list.add(row)

        sidebar.add(self.sidebar_list)
        parent.pack1(sidebar, False, True)

    def _build_file_view(self, parent):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.file_view = Gtk.IconView()
        self.file_view.set_name("nf-view")
        self.file_view.set_text_column(1)
        self.file_view.set_pixbuf_column(0)
        self.file_view.set_item_width(80)
        self.file_view.set_item_padding(6)
        self.file_view.connect("item-activated", self._on_item_activated)

        self.model = Gtk.ListStore(GdkPixbuf.Pixbuf, str, str)
        self.file_view.set_model(self.model)

        scroll.add(self.file_view)
        parent.pack2(scroll, True, True)

    def _build_statusbar(self, parent):
        self.statusbar = Gtk.Label()
        self.statusbar.set_name("nf-statusbar")
        self.statusbar.set_xalign(0)
        self.statusbar.set_margin_left(8)
        self.statusbar.set_margin_top(2)
        self.statusbar.set_margin_bottom(2)
        parent.pack_start(self.statusbar, False, False, 0)

    def _navigate_to(self, path):
        path = os.path.abspath(os.path.expanduser(path))
        if not os.path.isdir(path):
            return

        self.current_path = path
        self.path_entry.set_text(path)

        if self.history_pos < 0 or self.history[self.history_pos] != path:
            self.history = self.history[: self.history_pos + 1]
            self.history.append(path)
            self.history_pos = len(self.history) - 1

        self._load_directory(path)
        self._update_nav_buttons()

        if hasattr(self, 'sidebar_list'):
            for row in self.sidebar_list.get_children():
                if hasattr(row, 'path') and os.path.abspath(row.path) == path:
                    self.sidebar_list.select_row(row)
                    break

    def _load_directory(self, path):
        self.model.clear()

        try:
            items = sorted(os.listdir(path))
        except PermissionError:
            self.statusbar.set_text("⛔ Permission refusée")
            return

        dirs = []
        files = []
        for item in items:
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                dirs.append(item)
            else:
                files.append(item)

        if path != "/":
            dirs.insert(0, "..")

        for item in dirs + files:
            full_path = os.path.join(path, item)
            icon = self._get_icon_for_path(full_path)
            display_name = item[:40] + "..." if len(item) > 40 else item
            self.model.append([icon, display_name, full_path])

        count = len(dirs) + len(files)
        self.statusbar.set_text(f"{count} éléments — {path}")

    def _get_icon_for_path(self, path):
        try:
            if os.path.isdir(path):
                icon_theme = Gtk.IconTheme.get_default()
                icon = icon_theme.load_icon("folder", 48, 0)
                if icon:
                    return icon
            else:
                icon_theme = Gtk.IconTheme.get_default()
                icon = icon_theme.load_icon("text-x-generic", 48, 0)
                if icon:
                    return icon
        except Exception:
            pass

        w, h = 48, 48
        surface = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, w, h)
        surface.fill(0x1e88e500 if os.path.isdir(path) else 0x33333300)
        return surface

    def _on_item_activated(self, view, path):
        model = view.get_model()
        iter_ = model.get_iter(path)
        filepath = model.get_value(iter_, 2)

        if os.path.isdir(filepath):
            self._navigate_to(filepath)
        else:
            try:
                subprocess.Popen(["xdg-open", filepath], start_new_session=True)
            except Exception:
                pass

    def _on_path_enter(self, entry):
        self._navigate_to(entry.get_text())

    def _on_sidebar_activate(self, listbox, row):
        self._navigate_to(os.path.expanduser(row.path))

    def _go_back(self, btn):
        if self.history_pos > 0:
            self.history_pos -= 1
            self._navigate_to(self.history[self.history_pos])

    def _go_forward(self, btn):
        if self.history_pos < len(self.history) - 1:
            self.history_pos += 1
            self._navigate_to(self.history[self.history_pos])

    def _go_up(self, btn):
        parent = os.path.dirname(self.current_path)
        if parent and parent != self.current_path:
            self._navigate_to(parent)

    def _refresh(self, btn):
        self._load_directory(self.current_path)

    def _update_nav_buttons(self):
        self.back_btn.set_sensitive(self.history_pos > 0)
        self.fwd_btn.set_sensitive(self.history_pos < len(self.history) - 1)


def main():
    win = NextFileWindow()
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    main()
