import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango, GdkPixbuf
import os

from desktop.npshell.utils import hex_to_rgb, draw_glass_rect, draw_glass_highlight


class NPOSMenu(Gtk.Window):
    def __init__(self, config):
        Gtk.Window.__init__(self, type=Gtk.WindowType.POPUP)
        self.config = config
        self._setup_window()
        self._build_ui()
        self._apply_style()

    def _setup_window(self):
        self.set_title("npos-menu")
        self.set_default_size(400, 500)
        self.set_position(Gtk.WindowPosition.NONE)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_keep_above(True)
        self.connect("draw", self._on_draw)
        self.connect("key-press-event", self._on_key)
        self.connect("focus-out-event", lambda w, e: w.hide())

    def _build_ui(self):
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.sidebar.set_size_request(180, -1)

        self.pinned_label = Gtk.Label(label="Épinglés")
        self.pinned_label.set_name("menu-section-title")
        self.pinned_label.set_xalign(0)
        self.pinned_label.set_margin_top(12)
        self.pinned_label.set_margin_bottom(6)
        self.pinned_label.set_margin_left(12)
        self.sidebar.pack_start(self.pinned_label, False, False, 0)

        pinned_apps = [
            ("nextfile", "Explorateur"),
            ("nextterm", "Terminal"),
            ("nextedit", "Éditeur"),
        ]
        for app_id, label in pinned_apps:
            btn = MenuAppButton(app_id, label)
            self.sidebar.pack_start(btn, False, False, 0)

        sep = Gtk.Separator()
        sep.set_margin_top(6)
        sep.set_margin_bottom(6)
        self.sidebar.pack_start(sep, False, False, 0)

        self.all_apps_label = Gtk.Label(label="Toutes les applis")
        self.all_apps_label.set_name("menu-section-title")
        self.all_apps_label.set_xalign(0)
        self.all_apps_label.set_margin_left(12)
        self.all_apps_label.set_margin_bottom(6)
        self.sidebar.pack_start(self.all_apps_label, False, False, 0)

        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.apps_list = Gtk.ListBox()
        self.apps_list.set_activate_on_single_click(True)
        all_apps = [
            ("nextfile", "Explorateur de fichiers"),
            ("nextterm", "Terminal"),
            ("nextedit", "Éditeur de texte"),
            ("nextcalc", "Calculatrice"),
            ("nextmedia", "Musique"),
            ("nextsettings", "Paramètres"),
            ("nextinstaller", "Installateur"),
        ]
        for app_id, label in all_apps:
            row = MenuAppButton(app_id, label)
            self.apps_list.add(row)

        self.scroll.add(self.apps_list)
        self.sidebar.pack_start(self.scroll, True, True, 0)

        self.main_box.pack_start(self.sidebar, False, False, 0)

        sep2 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.pack_start(sep2, False, False, 0)

        self.right_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.right_panel.set_size_request(220, -1)

        self.user_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.user_box.set_margin_top(16)
        self.user_box.set_margin_bottom(12)
        self.user_box.set_margin_left(12)
        self.user_box.set_margin_right(12)

        avatar = Gtk.DrawingArea()
        avatar.set_size_request(40, 40)
        avatar.connect("draw", self._draw_avatar)
        self.user_box.pack_start(avatar, False, False, 0)

        user_info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        user_name = Gtk.Label(label=os.getenv("USER", "Utilisateur"))
        user_name.set_name("menu-user-name")
        user_name.set_xalign(0)
        user_info.pack_start(user_name, False, False, 0)

        user_status = Gtk.Label(label="En ligne")
        user_status.set_name("menu-user-status")
        user_status.set_xalign(0)
        user_info.pack_start(user_status, False, False, 0)

        self.user_box.pack_start(user_info, False, False, 0)
        self.right_panel.pack_start(self.user_box, False, False, 0)

        quick_actions = [
            ("document", "Documents"),
            ("download", "Téléchargements"),
            ("picture", "Images"),
            ("music", "Musique"),
            ("video", "Vidéos"),
        ]
        for icon, label in quick_actions:
            btn = MenuActionButton(icon, label)
            self.right_panel.pack_start(btn, False, False, 0)

        self.right_panel.pack_end(self._build_bottom_actions(), False, False, 0)

        self.main_box.pack_start(self.right_panel, True, True, 0)
        self.add(self.main_box)

    def _build_bottom_actions(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_left(8)
        box.set_margin_right(8)

        actions = [("⚙", "Paramètres", self._open_settings), ("⏻", "Arrêter", self._power_off)]
        for icon, label, cb in actions:
            btn = Gtk.Button(label=f"{icon} {label}")
            btn.set_name("menu-action-btn")
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.connect("clicked", lambda b, c=cb: (self.hide(), c()))
            box.pack_start(btn, True, True, 4)

        return box

    def _on_key(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.hide()
        return False

    def _on_draw(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        bg = hex_to_rgb(self.config.get("Theme", "glass_color"))
        draw_glass_rect(cr, 0, 0, w, h, 0, bg, 0.92)
        draw_glass_highlight(cr, 0, 0, w, h, 0)

    def _open_settings(self):
        from desktop.npshell.utils import run_app
        run_app("nextsettings")

    def _power_off(self):
        import subprocess
        subprocess.Popen(["systemctl", "poweroff", "-i"], start_new_session=True)

    def _draw_avatar(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        cr.set_source_rgba(0.3, 0.6, 0.9, 0.5)
        cr.arc(w / 2, h / 2, w / 2 - 2, 0, 2 * 3.14159)
        cr.fill()
        cr.set_source_rgba(1, 1, 1, 0.8)
        cr.arc(w / 2, h / 2 - 4, 8, 0, 2 * 3.14159)
        cr.fill()

    def _apply_style(self):
        css = b"""
        #menu-section-title {
            color: rgba(255,255,255,0.8);
            font-weight: bold;
            font-size: 11px;
            padding: 0;
        }
        #menu-user-name {
            color: white;
            font-weight: bold;
            font-size: 14px;
        }
        #menu-user-status {
            color: rgba(255,255,255,0.7);
            font-size: 11px;
        }
        #menu-action-btn {
            color: white;
            font-size: 12px;
            border: none;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            padding: 6px 12px;
        }
        #menu-action-btn:hover {
            background: rgba(255,255,255,0.2);
        }
        """
        style = Gtk.CssProvider()
        style.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


class MenuAppButton(Gtk.EventBox):
    def __init__(self, app_id, label):
        Gtk.EventBox.__init__(self)
        self.app_id = app_id

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.set_margin_top(4)
        box.set_margin_bottom(4)
        box.set_margin_left(12)
        box.set_margin_right(12)

        icon_da = Gtk.DrawingArea()
        icon_da.set_size_request(24, 24)
        icon_da.connect("draw", self._draw_icon)
        box.pack_start(icon_da, False, False, 0)

        lbl = Gtk.Label(label=label)
        lbl.set_xalign(0)
        lbl.set_name("menu-app-label")
        box.pack_start(lbl, True, True, 0)

        self.add(box)
        self.connect("button-press-event", self._on_click)

    def _draw_icon(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        cr.set_source_rgba(0.4, 0.7, 1.0, 0.6)
        cr.arc(w / 2, h / 2, w / 2 - 2, 0, 2 * 3.14159)
        cr.fill()

    def _on_click(self, widget, event):
        if event.button == 1:
            from desktop.npshell.utils import run_app
            run_app(self.app_id)
        return True


class MenuActionButton(Gtk.EventBox):
    def __init__(self, icon, label):
        Gtk.EventBox.__init__(self)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_left(16)
        box.set_margin_right(16)

        lbl = Gtk.Label(label=label)
        lbl.set_xalign(0)
        lbl.set_name("menu-action-label")
        box.pack_start(lbl, True, True, 0)

        self.add(box)
