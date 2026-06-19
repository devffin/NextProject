#!/usr/bin/env python3
"""
NextEdit - Éditeur de texte Aero pour NextProjectOS
Avec coloration syntaxique, numérotation de lignes, thème sombre Aero
"""
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GtkSource", "4")
from gi.repository import Gtk, Gdk, GLib, GtkSource, Pango
import os


class NextEditWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="NextEdit - Éditeur de texte")
        self.set_default_size(900, 600)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.current_file = None
        self._modified = False

        self._setup_style()
        self._build_ui()
        self.show_all()

    def _setup_style(self):
        css = b"""
        #ne-menubar { background: rgba(30,136,229,0.15); color: white; }
        #ne-menubar item { color: white; }
        #ne-toolbar { background: rgba(30,136,229,0.1); padding: 2px; }
        #ne-toolbar button { background: transparent; border: none; color: white; border-radius: 3px; padding: 2px 8px; }
        #ne-toolbar button:hover { background: rgba(255,255,255,0.15); }
        #ne-statusbar { background: rgba(0,0,0,0.2); color: rgba(255,255,255,0.7); font-size: 11px; }
        """
        style = Gtk.CssProvider()
        style.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self._build_menubar(vbox)
        self._build_toolbar(vbox)
        self._build_editor(vbox)
        self._build_statusbar(vbox)

        self.add(vbox)

    def _build_menubar(self, parent):
        menubar = Gtk.MenuBar()
        menubar.set_name("ne-menubar")

        file_menu = Gtk.Menu()
        file_items = [
            ("Nouveau", "<Ctrl>N", self._new_file),
            ("Ouvrir...", "<Ctrl>O", self._open_file),
            ("Enregistrer", "<Ctrl>S", self._save_file),
            ("Enregistrer sous...", "<Ctrl>Shift>S", self._save_as),
            (None, None, None),
            ("Quitter", "<Ctrl>Q", lambda m: self.destroy()),
        ]
        for label, accel, cb in file_items:
            if label is None:
                file_menu.append(Gtk.SeparatorMenuItem())
            else:
                item = Gtk.MenuItem(label=label)
                item.connect("activate", cb)
                file_menu.append(item)

        file_item = Gtk.MenuItem(label="Fichier")
        file_item.set_submenu(file_menu)
        menubar.append(file_item)

        edit_menu = Gtk.Menu()
        edit_items = [
            ("Annuler", "<Ctrl>Z", lambda m: self.buffer.undo()),
            ("Rétablir", "<Ctrl>Shift>Z", lambda m: self.buffer.redo()),
            (None, None, None),
            ("Rechercher...", "<Ctrl>F", self._search),
            ("Remplacer...", "<Ctrl>H", self._replace),
        ]
        for label, accel, cb in edit_items:
            if label is None:
                edit_menu.append(Gtk.SeparatorMenuItem())
            else:
                item = Gtk.MenuItem(label=label)
                item.connect("activate", cb)
                edit_menu.append(item)

        edit_item = Gtk.MenuItem(label="Édition")
        edit_item.set_submenu(edit_menu)
        menubar.append(edit_item)

        view_item = Gtk.MenuItem(label="Affichage")
        view_menu = Gtk.Menu()
        theme_item = Gtk.MenuItem(label="Mode sombre Aero")
        theme_item.set_sensitive(False)
        view_menu.append(theme_item)
        view_item.set_submenu(view_menu)
        menubar.append(view_item)

        parent.pack_start(menubar, False, False, 0)

    def _build_toolbar(self, parent):
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        toolbar.set_name("ne-toolbar")
        toolbar.set_margin_top(2)
        toolbar.set_margin_bottom(2)
        toolbar.set_margin_left(4)
        toolbar.set_margin_right(4)

        actions = [
            ("📄", "Nouveau", self._new_file),
            ("📂", "Ouvrir", self._open_file),
            ("💾", "Enregistrer", self._save_file),
        ]
        for icon, tip, cb in actions:
            btn = Gtk.Button(label=icon)
            btn.set_tooltip_text(tip)
            btn.connect("clicked", cb)
            toolbar.pack_start(btn, False, False, 0)

        parent.pack_start(toolbar, False, False, 0)

    def _build_editor(self, parent):
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.buffer = GtkSource.Buffer()
        lang_manager = GtkSource.LanguageManager.get_default()
        self.buffer.set_language(lang_manager.get_language("text"))
        self.buffer.set_highlight_syntax(True)
        self.buffer.set_highlight_matching_brackets(True)

        self.buffer.connect("changed", self._on_buffer_changed)

        self.view = GtkSource.View.new_with_buffer(self.buffer)
        self.view.set_show_line_numbers(True)
        self.view.set_show_right_margin(True)
        self.view.set_right_margin_position(80)
        self.view.set_tab_width(4)
        self.view.set_insert_spaces_instead_of_tabs(True)
        self.view.set_monospace(True)

        font = Pango.FontDescription("JetBrains Mono, Iosevka, monospace 12")
        self.view.modify_font(font)

        bg_color = Gdk.RGBA(0.08, 0.08, 0.12, 0.85)
        fg_color = Gdk.RGBA(0.93, 0.93, 0.93, 1.0)
        self.view.override_background_color(Gtk.StateFlags.NORMAL, bg_color)
        self.view.override_color(Gtk.StateFlags.NORMAL, fg_color)

        scrolled.add(self.view)
        parent.pack_start(scrolled, True, True, 0)

        self._setup_source_style()

    def _setup_source_style(self):
        style_scheme_manager = GtkSource.StyleSchemeManager.get_default()
        try:
            scheme = style_scheme_manager.get_scheme("oblivion")
            if scheme:
                self.buffer.set_style_scheme(scheme)
        except Exception:
            pass

    def _build_statusbar(self, parent):
        self.statusbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.statusbar.set_name("ne-statusbar")
        self.statusbar.set_margin_top(2)
        self.statusbar.set_margin_bottom(2)
        self.statusbar.set_margin_left(8)
        self.statusbar.set_margin_right(8)

        self.pos_label = Gtk.Label(label="L:1  C:1")
        self.statusbar.pack_start(self.pos_label, False, False, 0)

        self.encoding_label = Gtk.Label(label="UTF-8")
        self.statusbar.pack_end(self.encoding_label, False, False, 0)

        self.lang_label = Gtk.Label(label="Texte")
        self.statusbar.pack_end(self.lang_label, False, False, 4)

        parent.pack_start(self.statusbar, False, False, 0)

        self.buffer.connect("notify::cursor-position", self._update_cursor_pos)

    def _on_buffer_changed(self, buffer):
        if not self._modified:
            self._modified = True
            title = self.get_title()
            if not title.endswith("*"):
                self.set_title(title + " *")

    def _update_cursor_pos(self, *args):
        cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        line = cursor.get_line() + 1
        col = cursor.get_line_offset() + 1
        self.pos_label.set_text(f"L:{line}  C:{col}")

    def _new_file(self, *args):
        self.buffer.set_text("")
        self.current_file = None
        self._modified = False
        self.set_title("Nouveau fichier — NextEdit")

    def _open_file(self, *args):
        dialog = Gtk.FileChooserDialog(
            "Ouvrir un fichier", self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT),
        )

        if dialog.run() == Gtk.ResponseType.ACCEPT:
            path = dialog.get_filename()
            self._load_file(path)

        dialog.destroy()

    def _load_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            self.buffer.set_text(text)
            self.current_file = path
            self._modified = False
            self.set_title(f"{os.path.basename(path)} — NextEdit")

            lang_manager = GtkSource.LanguageManager.get_default()
            lang = lang_manager.guess_language(path, text)
            if lang:
                self.buffer.set_language(lang)
                self.lang_label.set_text(lang.get_name())
        except Exception as e:
            self._show_error(f"Erreur: {e}")

    def _save_file(self, *args):
        if self.current_file:
            self._write_file(self.current_file)
        else:
            self._save_as()

    def _save_as(self, *args):
        dialog = Gtk.FileChooserDialog(
            "Enregistrer sous...", self,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_SAVE, Gtk.ResponseType.ACCEPT),
        )

        if dialog.run() == Gtk.ResponseType.ACCEPT:
            path = dialog.get_filename()
            self._write_file(path)
            self.current_file = path
            self.set_title(f"{os.path.basename(path)} — NextEdit")

        dialog.destroy()

    def _write_file(self, path):
        try:
            start, end = self.buffer.get_bounds()
            text = self.buffer.get_text(start, end, False)
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self._modified = False
            self.set_title(f"{os.path.basename(path)} — NextEdit")
        except Exception as e:
            self._show_error(f"Erreur: {e}")

    def _search(self, *args):
        dialog = Gtk.Dialog("Rechercher", self, 0,
                           (Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE))
        entry = Gtk.Entry()
        entry.set_placeholder_text("Rechercher...")
        dialog.get_content_area().pack_start(entry, False, False, 8)
        entry.connect("activate", lambda e: self._do_search(e.get_text()))
        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def _do_search(self, text):
        if text:
            start = self.buffer.get_start_iter()
            match = start.forward_search(text, 0, None)
            if match:
                self.buffer.select_range(match[0], match[1])
                self.view.scroll_to_iter(match[0], 0.0, False, 0, 0)

    def _replace(self, *args):
        pass

    def _show_error(self, msg):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR,
                                  Gtk.ButtonsType.OK, msg)
        dialog.run()
        dialog.destroy()

    def _on_keyboard_shortcut(self, widget, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            key = event.keyval
            if key == Gdk.KEY_n:
                self._new_file()
                return True
            elif key == Gdk.KEY_o:
                self._open_file()
                return True
            elif key == Gdk.KEY_s:
                self._save_file()
                return True
        return False


def main():
    win = NextEditWindow()
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    main()
