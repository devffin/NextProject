import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Wnck", "3.0")
from gi.repository import Gtk, Gdk, GLib, Wnck, Pango


class NPOSTaskbar(Gtk.Box):
    def __init__(self, config):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self.config = config
        self.buttons = {}

        GLib.timeout_add(1000, self._update_windows)

    def _update_windows(self):
        screen = Wnck.Screen.get_default()
        screen.force_update()
        windows = screen.get_windows()

        current_windows = set()
        for win in windows:
            if not win.is_skip_tasklist() and win.get_name():
                current_windows.add(win.get_xid())
                if win.get_xid() not in self.buttons:
                    self._add_window_button(win)

        for xid in list(self.buttons.keys()):
            if xid not in current_windows:
                self._remove_window_button(xid)

        return True

    def _add_window_button(self, win):
        btn = TaskbarButton(win)
        self.buttons[win.get_xid()] = btn
        self.pack_start(btn, False, False, 0)
        self.show_all()

    def _remove_window_button(self, xid):
        if xid in self.buttons:
            self.remove(self.buttons[xid])
            del self.buttons[xid]


class TaskbarButton(Gtk.Button):
    def __init__(self, win):
        Gtk.Button.__init__(self)
        self.win = win
        self.set_relief(Gtk.ReliefStyle.NONE)
        self.set_name("taskbar-btn")

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        hbox.set_margin_left(6)
        hbox.set_margin_right(6)

        lbl = Gtk.Label(label=win.get_name()[:30])
        lbl.set_ellipsize(Pango.EllipsizeMode.END)
        lbl.set_max_width_chars(20)
        hbox.pack_start(lbl, False, False, 0)

        self.add(hbox)
        self.connect("clicked", self._on_click)

    def _on_click(self, btn):
        if self.win.is_active():
            self.win.minimize()
        else:
            self.win.activate(0)
