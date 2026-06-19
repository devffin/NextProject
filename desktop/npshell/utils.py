import os
import subprocess
import cairo
import math


def run_app(app_name):
    try:
        subprocess.Popen([app_name], start_new_session=True)
    except FileNotFoundError:
        try:
            subprocess.Popen(
                ["python3", f"-m", f"apps.{app_name}.main"],
                start_new_session=True,
            )
        except FileNotFoundError:
            pass


def run_command(cmd):
    try:
        subprocess.Popen(cmd, shell=True, start_new_session=True)
    except Exception:
        pass


def get_app_icon_path(app_name):
    icon_dir = os.path.expanduser("~/.local/share/icons/NPIcons/scalable/apps")
    path = os.path.join(icon_dir, f"{app_name}.svg")
    if os.path.exists(path):
        return path
    return os.path.join(icon_dir, "application-default.svg")


def draw_rounded_rect(cr, x, y, w, h, r):
    cr.move_to(x + r, y)
    cr.line_to(x + w - r, y)
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.line_to(x + w, y + h - r)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.line_to(x + r, y + h)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.line_to(x, y + r)
    cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    cr.close_path()


def draw_glass_rect(cr, x, y, w, h, r, color, alpha):
    draw_rounded_rect(cr, x, y, w, h, r)
    cr.set_source_rgba(color[0], color[1], color[2], alpha)
    cr.fill()


def draw_glass_highlight(cr, x, y, w, h, r):
    draw_rounded_rect(cr, x + 1, y + 1, w - 2, h / 2 - 1, r)
    cr.set_source_rgba(1, 1, 1, 0.12)
    cr.fill()


def hex_to_rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
