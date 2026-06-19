#!/usr/bin/env python3
"""
NextProjectOS - Point d'entrée de la session
Lance l'environnement de bureau Aero complet
"""
import sys
import os
import subprocess
import signal
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from desktop.npshell.main import main as shell_main


def start_compositor():
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "desktop", "compositor", "picom.conf"
    )
    try:
        subprocess.Popen(
            ["picom", "--config", config_path],
            start_new_session=True,
        )
        print("✨ Compositeur Aero démarré")
    except FileNotFoundError:
        print("⚠️  picom non trouvé. Installez picom pour les effets Aero.")


def start_applications():
    pass


def main():
    print("🚀 Démarrage de NextProjectOS...")
    print(f"📁 Répertoire: {os.path.dirname(os.path.abspath(__file__))}")

    start_compositor()

    time.sleep(0.5)
    shell_main()


if __name__ == "__main__":
    main()
