#!/usr/bin/env python3
"""
NextMedia - Lecteur multimédia Aero pour NextProjectOS
Avec interface verre, playlist, contrôle de lecture
"""
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Gio, Pango
import os
import subprocess


class NextMediaWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="NextMedia - Musique")
        self.set_default_size(750, 500)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.current_track = None
        self.playlist = []

        self._setup_style()
        self._build_ui()
        self.show_all()

    def _setup_style(self):
        css = b"""
        #nm-playlist { background: rgba(0,0,0,0.15); color: white; }
        #nm-playlist row { padding: 6px 12px; }
        #nm-playlist row:selected { background: rgba(30,136,229,0.4); }
        #nm-controls { background: rgba(0,0,0,0.2); padding: 6px; }
        #nm-controls button { background: transparent; color: white; border: none; font-size: 18px; min-width: 36px; min-height: 36px; border-radius: 50%; }
        #nm-controls button:hover { background: rgba(255,255,255,0.15); }
        #nm-controls button#nm-play { background: linear-gradient(to bottom, #4fc3f7, #1e88e5); font-size: 20px; min-width: 44px; min-height: 44px; }
        #nm-controls button#nm-play:hover { background: linear-gradient(to bottom, #6dd5fa, #2196f3); }
        #nm-info { color: white; }
        #nm-title { font-weight: bold; font-size: 14px; }
        #nm-artist { color: rgba(255,255,255,0.7); font-size: 11px; }
        #nm-progress { background: rgba(255,255,255,0.1); border-radius: 4px; }
        #nm-progress trough { min-height: 4px; }
        #nm-progress highlight { background: linear-gradient(to bottom, #4fc3f7, #1e88e5); border-radius: 4px; }
        """
        style = Gtk.CssProvider()
        style.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self._build_header(vbox)
        self._build_content(vbox)
        self._build_controls(vbox)

        self.add(vbox)

    def _build_header(self, parent):
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        header.set_margin_top(6)
        header.set_margin_bottom(6)
        header.set_margin_left(8)
        header.set_margin_right(8)

        self.cover_art = Gtk.DrawingArea()
        self.cover_art.set_size_request(48, 48)
        self.cover_art.connect("draw", self._draw_cover)
        header.pack_start(self.cover_art, False, False, 0)

        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info_box.set_margin_left(8)

        self.title_label = Gtk.Label(label="Aucun morceau")
        self.title_label.set_name("nm-title")
        self.title_label.set_xalign(0)
        info_box.pack_start(self.title_label, False, False, 0)

        self.artist_label = Gtk.Label(label="Ouvrez un fichier audio")
        self.artist_label.set_name("nm-artist")
        self.artist_label.set_xalign(0)
        info_box.pack_start(self.artist_label, False, False, 0)

        header.pack_start(info_box, True, True, 0)

        add_btn = Gtk.Button(label="+")
        add_btn.set_tooltip_text("Ajouter des morceaux")
        add_btn.set_name("nm-add")
        add_btn.connect("clicked", self._add_files)
        header.pack_end(add_btn, False, False, 0)

        parent.pack_start(header, False, False, 0)

    def _build_content(self, parent):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.playlist_widget = Gtk.ListBox()
        self.playlist_widget.set_name("nm-playlist")
        self.playlist_widget.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.playlist_widget.connect("row-activated", self._play_track)

        placeholder = Gtk.ListBoxRow()
        lbl = Gtk.Label(label="Ajoutez de la musique pour commencer\n(+) Ajouter des fichiers")
        lbl.set_margin_top(60)
        lbl.set_margin_bottom(60)
        lbl.set_opacity(0.5)
        placeholder.add(lbl)
        self.playlist_widget.add(placeholder)

        scroll.add(self.playlist_widget)
        parent.pack_start(scroll, True, True, 0)

    def _build_controls(self, parent):
        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        controls.set_name("nm-controls")
        controls.set_homogeneous(False)

        self.progress = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        self.progress.set_name("nm-progress")
        self.progress.set_draw_value(False)
        self.progress.set_range(0, 100)
        self.progress.set_size_request(-1, 8)
        controls.pack_start(self.progress, True, True, 8)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        btn_box.set_halign(Gtk.Align.CENTER)

        prev_btn = Gtk.Button(label="⏮")
        prev_btn.connect("clicked", self._prev_track)
        btn_box.pack_start(prev_btn, False, False, 0)

        self.play_btn = Gtk.Button(label="▶")
        self.play_btn.set_name("nm-play")
        self.play_btn.connect("clicked", self._toggle_play)
        btn_box.pack_start(self.play_btn, False, False, 0)

        next_btn = Gtk.Button(label="⏭")
        next_btn.connect("clicked", self._next_track)
        btn_box.pack_start(next_btn, False, False, 0)

        controls.pack_start(btn_box, True, True, 0)

        vol_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        vol_btn = Gtk.Button(label="🔊")
        vol_btn.connect("clicked", self._toggle_mute)
        vol_box.pack_start(vol_btn, False, False, 0)

        self.volume = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        self.volume.set_draw_value(False)
        self.volume.set_range(0, 100)
        self.volume.set_value(70)
        self.volume.set_size_request(80, -1)
        vol_box.pack_start(self.volume, False, False, 0)

        controls.pack_end(vol_box, False, False, 8)

        parent.pack_start(controls, False, False, 0)

    def _add_files(self, btn):
        dialog = Gtk.FileChooserDialog(
            "Ajouter de la musique", self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT),
        )
        dialog.set_select_multiple(True)

        filt = Gtk.FileFilter()
        filt.set_name("Audio")
        filt.add_mime_type("audio/*")
        dialog.add_filter(filt)

        if dialog.run() == Gtk.ResponseType.ACCEPT:
            for path in dialog.get_filenames():
                self._add_to_playlist(path)

        dialog.destroy()

    def _add_to_playlist(self, path):
        if path in self.playlist:
            return

        self.playlist.append(path)
        name = os.path.basename(path)

        if self.playlist_widget.get_row_at_index(0) and \
           self.playlist_widget.get_row_at_index(0).get_child().get_text() == "Ajoutez de la musique pour commencer\n(+) Ajouter des fichiers":
            self.playlist_widget.remove(self.playlist_widget.get_row_at_index(0))

        row = Gtk.ListBoxRow()
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        hbox.set_margin_top(4)
        hbox.set_margin_bottom(4)
        hbox.set_margin_left(8)
        hbox.set_margin_right(8)

        icon = Gtk.Label(label="🎵")
        hbox.pack_start(icon, False, False, 0)

        lbl = Gtk.Label(label=name)
        lbl.set_xalign(0)
        lbl.set_ellipsize(Pango.EllipsizeMode.END)
        hbox.pack_start(lbl, True, True, 0)

        row.add(hbox)
        row.path = path
        self.playlist_widget.add(row)
        self.playlist_widget.show_all()

    def _play_track(self, listbox, row):
        if hasattr(row, 'path'):
            self.current_track = row.path
            self.title_label.set_text(os.path.basename(row.path))
            self.artist_label.set_text(os.path.dirname(row.path))
            self.play_btn.set_label("⏸")
            self._simulate_playback()

    def _toggle_play(self, btn):
        if self.current_track:
            label = btn.get_label()
            btn.set_label("⏸" if label == "▶" else "▶")

    def _prev_track(self, btn):
        if self.current_track and self.current_track in self.playlist:
            idx = self.playlist.index(self.current_track)
            if idx > 0:
                self._play_by_index(idx - 1)

    def _next_track(self, btn):
        if self.current_track and self.current_track in self.playlist:
            idx = self.playlist.index(self.current_track)
            if idx < len(self.playlist) - 1:
                self._play_by_index(idx + 1)

    def _play_by_index(self, idx):
        if 0 <= idx < len(self.playlist):
            self.current_track = self.playlist[idx]
            self.title_label.set_text(os.path.basename(self.current_track))
            self.artist_label.set_text(os.path.dirname(self.current_track))
            self.play_btn.set_label("⏸")
            self._simulate_playback()

    def _simulate_playback(self):
        def advance():
            val = self.progress.get_value()
            if val < 100 and self.play_btn.get_label() == "⏸":
                self.progress.set_value(val + 0.5)
                self.progress.queue_draw()
                return True
            return False

        self.progress.set_value(0)
        self._playback_timer = GLib.timeout_add(100, advance)

    def _toggle_mute(self, btn):
        pass

    def _draw_cover(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        cr.set_source_rgba(0.3, 0.6, 0.9, 0.3)
        cr.rectangle(0, 0, w, h)
        cr.fill()
        cr.set_source_rgba(1, 1, 1, 0.6)
        cr.arc(w / 2, h / 2, 10, 0, 2 * 3.14159)
        cr.fill()


def main():
    win = NextMediaWindow()
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    main()
