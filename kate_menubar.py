#!/usr/bin/env python3
"""
Kate Menu Bar App
─────────────────
Sits in your Mac menu bar.
Click the icon OR press Cmd+Shift+K to launch Kate in a Terminal window.

Install deps once:
    pip3 install rumps pynput
"""

import rumps
import subprocess
import threading
import os
from pathlib import Path
from pynput import keyboard

# ── Config ───────────────────────────────────────────────────────────────────
KATE_DIR    = Path(__file__).parent
JARVIS_PY   = KATE_DIR / "jarvis.py"
PYTHON      = "/usr/bin/python3"
HOTKEY      = {keyboard.Key.cmd, keyboard.Key.shift, keyboard.KeyCode.from_char('k')}

# ── Launch helper ─────────────────────────────────────────────────────────────

def launch_kate(mode="chat"):
    """Open a new Terminal window running Kate."""
    script = f'''
    tell application "Terminal"
        activate
        do script "source ~/.zshrc && python3 \\"{JARVIS_PY}\\" {mode}"
    end tell
    '''
    subprocess.run(["osascript", "-e", script], check=False)

# ── Menu Bar App ──────────────────────────────────────────────────────────────

class KateMenuBar(rumps.App):
    def __init__(self):
        super().__init__(
            name="Kate",
            title="𝙺",           # shows in menu bar
            quit_button=None      # we'll add our own
        )
        self.menu = [
            rumps.MenuItem("💬  Chat with Kate",     callback=self.open_chat),
            rumps.MenuItem("🌤  Morning Briefing",    callback=self.open_briefing),
            None,                                      # separator
            rumps.MenuItem("📋  Open Task Manager",   callback=self.open_tasks),
            None,
            rumps.MenuItem("⌨️   Hotkey: ⌘⇧K",        callback=None),
            None,
            rumps.MenuItem("Quit Kate",               callback=self.quit_app),
        ]
        self._start_hotkey_listener()
        rumps.notification(
            title="Kate is running",
            subtitle="",
            message="Press ⌘⇧K or click 𝙺 in your menu bar to chat.",
            sound=False
        )

    # ── Menu actions ──────────────────────────────────────────────────────────

    @rumps.clicked("💬  Chat with Kate")
    def open_chat(self, _):
        launch_kate("chat")

    @rumps.clicked("🌤  Morning Briefing")
    def open_briefing(self, _):
        launch_kate("briefing")

    @rumps.clicked("📋  Open Task Manager")
    def open_tasks(self, _):
        task_html = KATE_DIR / "task_manager.html"
        subprocess.run(["open", str(task_html)], check=False)

    def quit_app(self, _):
        rumps.quit_application()

    # ── Global hotkey ─────────────────────────────────────────────────────────

    def _start_hotkey_listener(self):
        self._pressed = set()

        def on_press(key):
            self._pressed.add(key)
            if all(k in self._pressed for k in HOTKEY):
                self._pressed.clear()
                threading.Thread(target=launch_kate, args=("chat",), daemon=True).start()

        def on_release(key):
            self._pressed.discard(key)

        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.daemon = True
        listener.start()

# ── Entry ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    KateMenuBar().run()
