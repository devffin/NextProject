import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango, cairo
import os
import math

from desktop.npshell.utils import hex_to_rgb, draw_rounded_rect


class NPOSDesktop(Gtk.Window):
    def __init__(self, config):
        Gtk.Window.__init__(self, type=Gtk.WindowType.TOPLEVEL)
        self.config = config
        self.icons = []
        self._setup_window()
        self._build_ui()
        self._load_wallpaper()
        self.show_all()

    def _setup_window(self):
        self.set_title("npos-desktop")
        self.set_type_hint(Gdk.WindowTypeHint.DESKTOP)
        self.set_keep_below(True)
        self.set_accept_focus(False)
        self.set_resizable(False)
        self.stick()
        self.fullscreen()

        self.connect("draw", self._on_draw)
        self.connect("button-press-event", self._on_click)

        screen = Gdk.Screen.get_default()
        self.monitor = screen.get_monitor_geometry(0)
        self.screen_width = self.monitor.width
        self.screen_height = self.monitor.height

    def _build_ui(self):
        self.overlay = Gtk.Overlay()
        self.add(self.overlay)

        self.fixed = Gtk.Fixed()
        self.overlay.add(self.fixed)

        self._create_desktop_icons()

    def _load_wallpaper(self):
        wp = self.config.get("Desktop", "wallpaper")
        if os.path.exists(wp):
            self.wallpaper = Gdk.pixbuf_new_from_file(wp)
            self.wallpaper = self.wallpaper.scale_simple(
                self.screen_width, self.screen_height,
                Gdk.InterpType.BILINEAR,
            )
        else:
            self.wallpaper = None

    def _on_draw(self, widget, cr):
        if self.wallpaper:
            Gdk.cairo_set_source_pixbuf(cr, self.wallpaper, 0, 0)
            cr.paint()

    def _create_desktop_icons(self):
        apps = [
            ("nextfile", "Explorateur"),
            ("nextterm", "Terminal"),
            ("nextedit", "Éditeur"),
            ("nextcalc", "Calculatrice"),
            ("nextmedia", "Musique"),
            ("nextsettings", "Paramètres"),
            ("nextinstaller", "Installateur"),
        ]

        icon_size = self.config.getint("Desktop", "icon_size")
        padding = 20
        x = padding

        for app_id, label in apps:
            icon = DesktopIcon(app_id, label, icon_size)
            self.fixed.put(icon, x, self.screen_height - icon_size - 80)
            x += icon_size + padding
            self.icons.append(icon)

    def _on_click(self, widget, event):
        if event.button == 3:
            self._show_context_menu(event)
        return True

    def _show_context_menu(self, event):
        menu = Gtk.Menu()
        items = [
            ("Changer le fond d'écran...", self._change_wallpaper),
            ("Icônes du bureau", None),
            ("Alignement", None),
            ("Coller", None),
            ("Nouveau dossier", None),
            ("Paramètres d'affichage", None),
        ]
        for label, cb in items:
            item = Gtk.MenuItem(label=label)
            if cb:
                item.connect("activate", cb)
            else:
                item.set_sensitive(False)
            menu.append(item)
        menu.show_all()
        menu.popup_at_pointer(event)

    def _change_wallpaper(self, *args):
        dialog = Gtk.FileChooserDialog(
            "Choisir un fond d'écran", None,
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
            self._load_wallpaper()
            self.queue_draw()

        dialog.destroy()


class DesktopIcon(Gtk.EventBox):
    def __init__(self, app_id, label, size=64):
        Gtk.EventBox.__init__(self)
        self.app_id = app_id
        self.label_text = label
        self.icon_size = size

        self.set_size_request(size + 20, size + 40)
        self.set_above_child(True)
        self.connect("button-press-event", self._on_activate)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        vbox.set_homogeneous(False)

        self.icon_area = Gtk.DrawingArea()
        self.icon_area.set_size_request(size, size)
        self.icon_area.connect("draw", self._draw_icon)
        vbox.pack_start(self.icon_area, False, False, 0)

        label_w = Gtk.Label(label=label)
        label_w.set_name("desktop-icon-label")
        label_w.set_line_wrap(True)
        label_w.set_max_width_chars(10)
        label_w.set_justify(Gtk.Justification.CENTER)
        vbox.pack_start(label_w, False, False, 0)

        self.add(vbox)

    def _draw_icon(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()

        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()

        icon_path = os.path.expanduser(
            f"~/.local/share/icons/NPIcons/scalable/apps/{self.app_id}.svg"
        )
        if os.path.exists(icon_path):
            try:
                pixbuf = Gdk.pixbuf_new_from_file_at_size(icon_path, w - 8, h - 8)
                Gdk.cairo_set_source_pixbuf(cr, pixbuf, (w - pixbuf.get_width()) / 2, (h - pixbuf.get_height()) / 2)
                cr.paint()
                return
            except Exception:
                pass

        cr.set_source_rgba(0.3, 0.6, 0.9, 0.3)
        draw_rounded_rect(cr, 4, 4, w - 8, h - 8, 8)
        cr.fill()

    def _on_activate(self, widget, event):
        if event.button == 1 and event.type == Gdk.EventType._2BUTTON_PRESS:
            from desktop.npshell.utils import run_app
            run_app(self.app_id)
        return True
