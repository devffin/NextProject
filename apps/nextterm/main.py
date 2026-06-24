#!/usr/bin/env python3
"""
NextTerm - Terminal Aero pour NextProjectOS
Avec thème verre transparent et profils personnalisables
"""
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Vte", "2.91")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Vte, Pango
import os
import subprocess


class NextTermWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="NextTerm - Terminal")

        self.set_default_size(800, 500)
        self.set_position(Gtk.WindowPosition.CENTER)
        self._setup_style()
        self._build_ui()
        self.connect("key-press-event", self._on_keyboard_shortcut)
        self.show_all()

    def _setup_style(self):
        css = b"""
        #nt-notebook { background: transparent; }
        #nt-notebook tab { background: rgba(30,136,229,0.2); color: white; border: none; padding: 2px 16px; }
        #nt-notebook tab:checked { background: rgba(30,136,229,0.4); }
        #nt-notebook tab button { min-width: 16px; min-height: 16px; padding: 0; color: rgba(255,255,255,0.5); }
        #nt-notebook tab button:hover { color: white; }
        """
        style = Gtk.CssProvider()
        style.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self.notebook = Gtk.Notebook()
        self.notebook.set_name("nt-notebook")
        self.notebook.set_scrollable(True)
        self.notebook.connect("tab-removed", self._on_tab_removed)

        self._add_terminal_tab()

        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        toolbar.set_margin_top(2)
        toolbar.set_margin_bottom(2)
        toolbar.set_margin_left(4)
        toolbar.set_margin_right(4)

        new_btn = Gtk.Button(label="+")
        new_btn.set_tooltip_text("Nouvel onglet")
        new_btn.connect("clicked", lambda b: self._add_terminal_tab())
        new_btn.set_size_request(32, 24)
        toolbar.pack_start(new_btn, False, False, 0)

        vbox.pack_start(toolbar, False, False, 0)
        vbox.pack_start(self.notebook, True, True, 0)

        self.add(vbox)

    def _add_terminal_tab(self, label="Terminal"):
        terminal = Vte.Terminal()
        terminal.set_name("nt-terminal")

        terminal.set_cursor_blink_mode(Vte.CursorBlinkMode.ON)
        terminal.set_cursor_shape(Vte.CursorShape.BLOCK)

        terminal.set_colors(
            Gdk.RGBA(0.93, 0.93, 0.93, 1.0),
            Gdk.RGBA(0.08, 0.08, 0.12, 0.85),
            []
        )
        terminal.set_font(Pango.FontDescription("JetBrains Mono, Iosevka, monospace 11"))

        tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        tab_label = Gtk.Label(label=label)
        tab_box.pack_start(tab_label, True, True, 0)

        close_btn = Gtk.Button(label="×")
        close_btn.set_relief(Gtk.ReliefStyle.NONE)
        close_btn.connect("clicked", lambda b, t=terminal: self._close_tab(t))
        tab_box.pack_start(close_btn, False, False, 0)
        tab_box.show_all()

        scrolled = Gtk.ScrolledWindow()
        scrolled.add(terminal)

        page_num = self.notebook.append_page(scrolled, tab_box)
        self.notebook.set_current_page(page_num)
        self.notebook.set_tab_reorderable(scrolled, True)

        shell = os.environ.get("SHELL", "/bin/bash")
        terminal.spawn_async(
            Vte.PtyFlags.DEFAULT,
            os.path.expanduser("~"),
            [shell],
            [],
            GLib.SpawnFlags.SEARCH_PATH,
            None,
            None,
            -1,
            None,
        )

        terminal.connect("child-exited", lambda t: self._close_tab(t))

    def _close_tab(self, terminal):
        for i in range(self.notebook.get_n_pages()):
            page = self.notebook.get_nth_page(i)
            if isinstance(page, Gtk.ScrolledWindow) and page.get_child() is terminal:
                self.notebook.remove_page(i)
                break

    def _on_tab_removed(self, notebook, child, page_num):
        if notebook.get_n_pages() == 0:
            self.destroy()

    def _on_keyboard_shortcut(self, widget, event):
        if event.keyval == Gdk.KEY_T and event.state & Gdk.ModifierType.CONTROL_MASK:
            self._add_terminal_tab()
            return True
        if event.keyval == Gdk.KEY_W and event.state & Gdk.ModifierType.CONTROL_MASK:
            current = self.notebook.get_nth_page(self.notebook.get_current_page())
            if current:
                terminal = current.get_child()
                self._close_tab(terminal)
            return True
        return False


def main():
    win = NextTermWindow()
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    main()
