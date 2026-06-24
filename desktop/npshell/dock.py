import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango, GdkPixbuf
import os
import math

from desktop.npshell.utils import hex_to_rgb, draw_rounded_rect, draw_glass_rect, draw_glass_highlight


class NPOSDock(Gtk.Window):
    def __init__(self, config):
        Gtk.Window.__init__(self, type=Gtk.WindowType.TOPLEVEL)
        self.config = config
        self._setup_window()
        self._build_ui()
        self._apply_style()
        self.show_all()

    def _setup_window(self):
        self.set_title("npos-dock")
        self.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.set_keep_above(True)
        self.set_accept_focus(False)
        self.set_resizable(False)
        self.stick()

        screen = Gdk.Screen.get_default()
        monitor = screen.get_monitor_geometry(0)

        icon_size = self.config.getint("Dock", "icon_size")
        dock_height = icon_size + 24
        dock_width = min(600, monitor.width - 40)

        pos = self.config.get("Dock", "position")
        x = (monitor.width - dock_width) // 2

        if pos == "bottom":
            self.set_default_size(dock_width, dock_height)
            self.move(x, monitor.height - dock_height - 40)
        elif pos == "left":
            self.set_default_size(dock_height, dock_width)
            self.move(0, (monitor.height - dock_width) // 2)
        elif pos == "right":
            self.set_default_size(dock_height, dock_width)
            self.move(monitor.width - dock_height, (monitor.height - dock_width) // 2)

        self.set_app_paintable(True)
        screen = Gdk.Screen.get_default()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.connect("draw", self._on_draw)

    def _build_ui(self):
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.main_box.set_margin_top(6)
        self.main_box.set_margin_bottom(6)
        self.main_box.set_margin_left(8)
        self.main_box.set_margin_right(8)
        self.add(self.main_box)

        apps = [
            ("nextfile", "Explorateur"),
            ("nextterm", "Terminal"),
            ("nextedit", "Éditeur"),
            ("nextcalc", "Calculatrice"),
            ("nextmedia", "Musique"),
            ("nextsettings", "Paramètres"),
            ("nextinstaller", "Installateur"),
        ]

        for app_id, label in apps:
            btn = DockIconButton(app_id, label, self.config.getint("Dock", "icon_size"))
            self.main_box.pack_start(btn, False, False, 0)

        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        sep.set_name("dock-separator")
        self.main_box.pack_start(sep, False, False, 4)

        trash = DockIconButton("trash", "Corbeille", self.config.getint("Dock", "icon_size"))
        self.main_box.pack_end(trash, False, False, 0)

    def _on_draw(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        bg = hex_to_rgb(self.config.get("Theme", "glass_color"))
        draw_glass_rect(cr, 0, 0, w, h, 12, bg, self.config.getfloat("Dock", "opacity"))
        draw_glass_highlight(cr, 0, 0, w, h, 12)

    def _apply_style(self):
        css = b"""
        #dock-separator {
            background: rgba(255,255,255,0.2);
            min-width: 1px;
        }
        """
        style = Gtk.CssProvider()
        style.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


class DockIconButton(Gtk.EventBox):
    def __init__(self, app_id, tooltip_text, size=48):
        Gtk.EventBox.__init__(self)
        self.app_id = app_id
        self.icon_size = size

        self.set_size_request(size + 8, size + 8)
        self.set_has_tooltip(True)
        self.set_tooltip_text(tooltip_text)
        self.connect("button-press-event", self._on_click)

        self.da = Gtk.DrawingArea()
        self.da.set_size_request(size, size)
        self.da.connect("draw", self._draw_icon)
        self.add(self.da)

    def _draw_icon(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()

        icon_path = os.path.expanduser(
            f"~/.local/share/icons/NPIcons/scalable/apps/{self.app_id}.svg"
        )
        if os.path.exists(icon_path):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, w - 4, h - 4)
                Gdk.cairo_set_source_pixbuf(cr, pixbuf, (w - pixbuf.get_width()) / 2, (h - pixbuf.get_height()) / 2)
                cr.paint()
                return
            except Exception:
                pass

        cr.set_source_rgba(0.4, 0.7, 1.0, 0.3)
        draw_rounded_rect(cr, 2, 2, w - 4, h - 4, 6)
        cr.fill()

    def _on_click(self, widget, event):
        if event.button == 1:
            from desktop.npshell.utils import run_app
            run_app(self.app_id)
        return True
