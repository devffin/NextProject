import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
import datetime


class NPOSSystemTray(Gtk.Box):
    def __init__(self, config):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.config = config
        self.set_name("system-tray")

        self._build_clock()
        self._build_volume()
        self._build_network()
        self._build_power()
        self._apply_style()

        GLib.timeout_add_seconds(30, self._update_clock)

    def _build_clock(self):
        self.clock_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        now = datetime.datetime.now()
        self.time_label = Gtk.Label(label=now.strftime("%H:%M"))
        self.time_label.set_name("tray-time")
        self.clock_box.pack_start(self.time_label, False, False, 0)

        self.date_label = Gtk.Label(label=now.strftime("%d/%m/%Y"))
        self.date_label.set_name("tray-date")
        self.clock_box.pack_start(self.date_label, False, False, 0)

        self.clock_box.set_margin_left(8)
        self.clock_box.set_margin_right(8)
        self.pack_end(self.clock_box, False, False, 0)

    def _build_volume(self):
        btn = Gtk.Button(label="🔊")
        btn.set_name("tray-btn")
        btn.set_relief(Gtk.ReliefStyle.NONE)
        self.pack_end(btn, False, False, 0)

    def _build_network(self):
        btn = Gtk.Button(label="📶")
        btn.set_name("tray-btn")
        btn.set_relief(Gtk.ReliefStyle.NONE)
        self.pack_end(btn, False, False, 0)

    def _build_power(self):
        btn = Gtk.Button(label="🔋")
        btn.set_name("tray-btn")
        btn.set_relief(Gtk.ReliefStyle.NONE)
        self.pack_end(btn, False, False, 0)

    def _update_clock(self):
        now = datetime.datetime.now()
        self.time_label.set_text(now.strftime("%H:%M"))
        self.date_label.set_text(now.strftime("%d/%m/%Y"))
        return True

    def _apply_style(self):
        css = b"""
        #tray-time {
            color: white;
            font-weight: bold;
            font-size: 12px;
        }
        #tray-date {
            color: rgba(255,255,255,0.7);
            font-size: 9px;
        }
        #tray-btn {
            color: white;
            font-size: 14px;
            padding: 2px 4px;
            min-width: 28px;
            border: none;
            background: transparent;
        }
        #tray-btn:hover {
            background: rgba(255,255,255,0.15);
            border-radius: 4px;
        }
        """
        style = Gtk.CssProvider()
        style.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
