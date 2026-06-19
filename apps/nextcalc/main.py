#!/usr/bin/env python3
"""
NextCalc - Calculatrice scientifique Aero pour NextProjectOS
Avec interface verre transparent style Aero
"""
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import math


class NextCalcWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="NextCalc - Calculatrice")
        self.set_default_size(320, 440)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(False)

        self.current = ""
        self.result = ""
        self.operation = None
        self.clear_next = False
        self.memory = 0
        self._deg = True

        self._setup_style()
        self._build_ui()
        self.show_all()

    def _setup_style(self):
        css = b"""
        #nc-display { background: rgba(0,0,0,0.3); color: white; font-size: 28px; font-weight: bold; padding: 12px 16px; border-radius: 6px; }
        #nc-btn { background: rgba(255,255,255,0.1); color: white; font-size: 16px; border: none; border-radius: 4px; min-width: 48px; min-height: 40px; }
        #nc-btn:hover { background: rgba(255,255,255,0.2); }
        #nc-btn:active { background: rgba(30,136,229,0.4); }
        #nc-btn-op { background: rgba(30,136,229,0.3); color: white; font-size: 18px; border: none; border-radius: 4px; min-width: 48px; min-height: 40px; }
        #nc-btn-op:hover { background: rgba(30,136,229,0.5); }
        #nc-btn-fn { background: rgba(79,195,247,0.15); color: #4fc3f7; font-size: 13px; border: none; border-radius: 4px; min-width: 48px; min-height: 36px; }
        #nc-btn-fn:hover { background: rgba(79,195,247,0.3); }
        #nc-btn-eq { background: linear-gradient(to bottom, #4fc3f7, #1e88e5); color: white; font-size: 20px; font-weight: bold; border: none; border-radius: 4px; min-width: 48px; min-height: 40px; }
        #nc-btn-eq:hover { background: linear-gradient(to bottom, #6dd5fa, #2196f3); }
        #nc-btn-c { background: rgba(229,57,53,0.3); color: #ef5350; font-size: 16px; border: none; border-radius: 4px; min-width: 48px; min-height: 40px; }
        #nc-btn-c:hover { background: rgba(229,57,53,0.5); }
        """
        style = Gtk.CssProvider()
        style.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(8)
        vbox.set_margin_bottom(8)
        vbox.set_margin_left(8)
        vbox.set_margin_right(8)

        self.display = Gtk.Label(label="0")
        self.display.set_name("nc-display")
        self.display.set_xalign(1)
        self.display.set_size_request(-1, 60)
        vbox.pack_start(self.display, False, False, 0)

        self._build_buttons(vbox)
        self.add(vbox)

    def _button(self, label, name="nc-btn", cb=None):
        btn = Gtk.Button(label=label)
        btn.set_name(name)
        if cb:
            btn.connect("clicked", cb)
        else:
            btn.connect("clicked", self._on_digit, label)
        return btn

    def _build_buttons(self, parent):
        grid = Gtk.Grid()
        grid.set_row_spacing(4)
        grid.set_column_spacing(4)

        # Ligne 1: fonctions scientifiques
        fn_buttons = [
            ("sin", "sin"), ("cos", "cos"), ("tan", "tan"), ("π", "pi"),
            ("x²", "sqr"), ("√", "sqrt"), ("log", "log"), ("ln", "ln"),
        ]
        for i, (lbl, action) in enumerate(fn_buttons):
            btn = self._button(lbl, "nc-btn-fn", lambda b, a=action: self._fn_action(a))
            grid.attach(btn, i, 0, 1, 1)

        # Ligne 2: mémoire
        mem_buttons = [("MC", "mc"), ("MR", "mr"), ("M+", "m+"), ("M-", "m-")]
        for i, (lbl, action) in enumerate(mem_buttons):
            btn = self._button(lbl, "nc-btn-fn", lambda b, a=action: self._mem_action(a))
            grid.attach(btn, i, 1, 1, 1)

        # Ligne 3: C / CE / % / ÷
        grid.attach(self._button("C", "nc-btn-c", self._clear), 0, 2, 1, 1)
        grid.attach(self._button("CE", "nc-btn-c", self._clear_entry), 1, 2, 1, 1)
        grid.attach(self._button("%", "nc-btn-op", lambda b: self._operation("/100")), 2, 2, 1, 1)
        grid.attach(self._button("÷", "nc-btn-op", lambda b: self._operation("/")), 3, 2, 1, 1)

        # Ligne 4: 7 8 9 ×
        grid.attach(self._button("7"), 0, 3, 1, 1)
        grid.attach(self._button("8"), 1, 3, 1, 1)
        grid.attach(self._button("9"), 2, 3, 1, 1)
        grid.attach(self._button("×", "nc-btn-op", lambda b: self._operation("*")), 3, 3, 1, 1)

        # Ligne 5: 4 5 6 -
        grid.attach(self._button("4"), 0, 4, 1, 1)
        grid.attach(self._button("5"), 1, 4, 1, 1)
        grid.attach(self._button("6"), 2, 4, 1, 1)
        grid.attach(self._button("-", "nc-btn-op", lambda b: self._operation("-")), 3, 4, 1, 1)

        # Ligne 6: 1 2 3 +
        grid.attach(self._button("1"), 0, 5, 1, 1)
        grid.attach(self._button("2"), 1, 5, 1, 1)
        grid.attach(self._button("3"), 2, 5, 1, 1)
        grid.attach(self._button("+", "nc-btn-op", lambda b: self._operation("+")), 3, 5, 1, 1)

        # Ligne 7: 0 . ± =
        grid.attach(self._button("0"), 0, 6, 1, 1)
        grid.attach(self._button("."), 1, 6, 1, 1)
        grid.attach(self._button("±", "nc-btn-op", lambda b: self._negate()), 2, 6, 1, 1)
        grid.attach(self._button("=", "nc-btn-eq", self._calculate), 3, 6, 1, 1)

        parent.pack_start(grid, True, True, 0)

    def _on_digit(self, btn, digit):
        if self.clear_next:
            self.current = ""
            self.clear_next = False
        self.current += digit
        self._update_display()

    def _operation(self, op):
        if self.current:
            self.result = self.current if not self.result else self._eval_op()
        self.operation = op
        self.current = ""
        self._update_display()

    def _eval_op(self):
        try:
            a = float(self.result)
            b = float(self.current) if self.current else 0
            if self.operation == "+": return str(a + b)
            elif self.operation == "-": return str(a - b)
            elif self.operation == "*": return str(a * b)
            elif self.operation == "/":
                return "Erreur" if b == 0 else str(a / b)
            elif self.operation == "/100": return str(a / 100 * b) if b else str(a / 100)
        except Exception:
            return "Erreur"
        return self.result

    def _calculate(self, btn):
        if self.operation and self.current:
            self.result = self._eval_op()
            self.current = self.result
            self.operation = None
            self.result = ""
            self.clear_next = True
            self._update_display()

    def _clear(self, btn):
        self.current = ""
        self.result = ""
        self.operation = None
        self._update_display()

    def _clear_entry(self, btn):
        self.current = ""
        self._update_display()

    def _negate(self):
        if self.current:
            self.current = str(-float(self.current))
            self._update_display()

    def _fn_action(self, action):
        try:
            val = float(self.current) if self.current else 0
            if action == "sin": val = math.sin(math.radians(val) if self._deg else val)
            elif action == "cos": val = math.cos(math.radians(val) if self._deg else val)
            elif action == "tan": val = math.tan(math.radians(val) if self._deg else val)
            elif action == "pi": val = math.pi
            elif action == "sqr": val = val ** 2
            elif action == "sqrt": val = math.sqrt(val)
            elif action == "log": val = math.log10(val)
            elif action == "ln": val = math.log(val)
            self.current = str(round(val, 10))
            self.clear_next = True
        except Exception:
            self.current = "Erreur"
        self._update_display()

    def _mem_action(self, action):
        try:
            val = float(self.current) if self.current else 0
            if action == "mc": self.memory = 0
            elif action == "mr": self.current = str(self.memory)
            elif action == "m+": self.memory += val
            elif action == "m-": self.memory -= val
        except Exception:
            pass
        self._update_display()

    def _update_display(self):
        display_text = self.current if self.current else self.result if self.result else "0"
        if len(display_text) > 14:
            display_text = display_text[:14]
        self.display.set_text(display_text)


def main():
    win = NextCalcWindow()
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    main()
