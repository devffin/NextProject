#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Wnck", "3.0")
from gi.repository import Gtk, Gdk, GLib, Wnck
import signal
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from desktop.npshell.config import NPOSConfig
from desktop.npshell.panel import NPOSPanel
from desktop.npshell.desktop import NPOSDesktop
from desktop.npshell.dock import NPOSDock


class NPOSShell:
    def __init__(self):
        self.config = NPOSConfig()

        self.screen = Gdk.Screen.get_default()
        self.screen_width = self.screen.get_width()
        self.screen_height = self.screen.get_height()

        self.panel = NPOSPanel(self.config)
        self.desktop = NPOSDesktop(self.config)
        self.dock = NPOSDock(self.config)

        self._setup_wm()

    def _setup_wm(self):
        self.wm_screen = Wnck.Screen.get_default()
        self.wm_screen.force_update()

    def run(self):
        Gtk.main()

    def quit(self):
        Gtk.main_quit()


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    shell = NPOSShell()
    shell.run()


if __name__ == "__main__":
    main()
