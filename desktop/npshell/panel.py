import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango, GObject
import os

from desktop.npshell.utils import hex_to_rgb
from desktop.npshell.menu import NPOSMenu


class NPOSPanel(Gtk.Window):
    def __init__(self, config):
        Gtk.Window.__init__(self, type=Gtk.WindowType.TOPLEVEL)
        self.config = config
        self._setup_window()
        self._build_ui()
        self._apply_style()
        self.show_all()

    def _setup_window(self):
        self.set_title("npos-panel")
        self.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.set_keep_above(True)
        self.set_accept_focus(False)
        self.set_resizable(False)
        self.stick()

        screen = Gdk.Screen.get_default()
        self.monitor = screen.get_monitor_geometry(0)
        self.panel_height = self.config.getint("Panel", "height")

        pos = self.config.get("Panel", "position")
        if pos == "bottom":
            self.set_default_size(self.monitor.width, self.panel_height)
            self.move(0, self.monitor.height - self.panel_height)
        elif pos == "top":
            self.set_default_size(self.monitor.width, self.panel_height)
            self.move(0, 0)

    def _build_ui(self):
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.add(self.main_box)

        self._build_menu_button()
        self._build_search()
        self._build_taskbar()
        self._build_system_tray()

    def _build_menu_button(self):
        self.menu_btn = Gtk.Button(label="Next")
        self.menu_btn.set_name("npos-menu-button")
        self.menu_btn.connect("clicked", self._on_menu_clicked)
        self.menu_btn.set_size_request(80, -1)
        self.main_box.pack_start(self.menu_btn, False, False, 0)

        self.menu = NPOSMenu(self.config)
        self.menu_btn.menu = self.menu

    def _on_menu_clicked(self, btn):
        if self.menu.get_visible():
            self.menu.hide()
            return
        alloc = btn.get_allocation()
        x, y = btn.get_window().get_origin()
        pos = self.config.get("Panel", "position")
        if pos == "bottom":
            menu_y = y - self.menu.get_allocated_height()
        else:
            menu_y = y + alloc.height
        self.menu.move(x, menu_y)
        self.menu.show_all()

    def _build_search(self):
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Rechercher...")
        self.search_entry.set_name("npos-search")
        self.search_entry.set_size_request(200, 24)
        self.search_entry.connect("search-changed", self._on_search)
        self.main_box.pack_start(self.search_entry, False, False, 6)

    def _on_search(self, entry):
        pass

    def _build_taskbar(self):
        from desktop.npshell.taskbar import NPOSTaskbar
        self.taskbar = NPOSTaskbar(self.config)
        self.main_box.pack_start(self.taskbar, True, True, 0)

    def _build_system_tray(self):
        from desktop.npshell.systemtray import NPOSSystemTray
        self.tray = NPOSSystemTray(self.config)
        self.main_box.pack_end(self.tray, False, False, 0)

    def _apply_style(self):
        bg_color = hex_to_rgb(self.config.get("Theme", "glass_color"))
        opacity = self.config.getfloat("Panel", "opacity")

        css = b"""
        #npos-menu-button {
            background: linear-gradient(to bottom, #4fc3f7, #1e88e5);
            color: white;
            font-weight: bold;
            border: none;
            border-radius: 0;
            padding: 0 16px;
            font-size: 12px;
        }
        #npos-menu-button:hover {
            background: linear-gradient(to bottom, #6dd5fa, #2196f3);
        }
        #npos-search {
            background: rgba(255,255,255,0.15);
            color: white;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 4px;
            padding: 2px 8px;
        }
        #npos-search:focus {
            background: rgba(255,255,255,0.25);
            border-color: #4fc3f7;
        }
        """
        style = Gtk.CssProvider()
        style.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
