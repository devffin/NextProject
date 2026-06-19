import os
import configparser

CONFIG_DIR = os.path.expanduser("~/.config/npos")
CONFIG_FILE = os.path.join(CONFIG_DIR, "npos.conf")
THEME_DIR = os.path.expanduser("~/.local/share/themes/NextAero")
ICON_DIR = os.path.expanduser("~/.local/share/icons/NPIcons")
WALLPAPER_DIR = os.path.expanduser("~/.local/share/backgrounds/npos")


class NPOSConfig:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self._set_defaults()
        self._load()

    def _set_defaults(self):
        self.config["Desktop"] = {
            "wallpaper": os.path.join(WALLPAPER_DIR, "default.svg"),
            "wallpaper_style": "stretch",
            "show_icons": "true",
            "icon_size": "64",
            "text_shadow": "true",
        }
        self.config["Panel"] = {
            "position": "bottom",
            "height": "36",
            "opacity": "0.85",
            "blur": "true",
            "autohide": "false",
            "glass_effect": "true",
        }
        self.config["Dock"] = {
            "enabled": "true",
            "position": "bottom",
            "icon_size": "48",
            "autohide": "false",
            "opacity": "0.80",
        }
        self.config["Menu"] = {
            "style": "aero",
            "show_recent": "true",
            "show_favorites": "true",
            "blur_background": "true",
        }
        self.config["Theme"] = {
            "name": "NextAero",
            "gtk_theme": "NextAero",
            "icon_theme": "NPIcons",
            "cursor_theme": "default",
            "font": "Cantarell 10",
            "accent_color": "#4fc3f7",
            "glass_color": "#1e88e5",
        }
        self.config["Compositor"] = {
            "enabled": "true",
            "shadow": "true",
            "blur": "true",
            "animation": "true",
            "fade": "true",
        }
        self.config["Apps"] = {
            "file_manager": "nextfile",
            "terminal": "nextterm",
            "editor": "nextedit",
            "browser": "firefox",
        }

    def _load(self):
        if os.path.exists(CONFIG_FILE):
            self.config.read(CONFIG_FILE)

    def save(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            self.config.write(f)

    def get(self, section, key):
        return self.config.get(section, key)

    def getint(self, section, key):
        return self.config.getint(section, key)

    def getboolean(self, section, key):
        return self.config.getboolean(section, key)

    def set(self, section, key, value):
        self.config.set(section, str(key), str(value))
