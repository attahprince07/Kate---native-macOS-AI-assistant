#!/bin/bash
# ── Install Kate Menu Bar App ─────────────────────────────────────────────────
# Run once: bash install_menubar.sh

set -e

KATE_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON=$(which python3)
PLIST="$HOME/Library/LaunchAgents/com.kate.menubar.plist"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║     Kate Menu Bar — Installing       ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── 1. Install deps ───────────────────────────────────────────────────────────
echo "▶  Installing rumps and pynput..."
pip3 install rumps pynput --break-system-packages --quiet
echo "   ✓ Done"

# ── 2. Write LaunchAgent plist ────────────────────────────────────────────────
echo "▶  Registering login item..."
cat > "$PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.kate.menubar</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PYTHON</string>
    <string>$KATE_DIR/kate_menubar.py</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>EnvironmentVariables</key>
  <dict>
    <key>ANTHROPIC_API_KEY</key>
    <string>$ANTHROPIC_API_KEY</string>
    <key>PATH</key>
    <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
  </dict>
  <key>StandardOutPath</key>
  <string>$KATE_DIR/logs/menubar.log</string>
  <key>StandardErrorPath</key>
  <string>$KATE_DIR/logs/menubar_err.log</string>
</dict>
</plist>
EOF

mkdir -p "$KATE_DIR/logs"
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
echo "   ✓ Kate will now start on every login"

# ── 3. Launch right now ───────────────────────────────────────────────────────
echo "▶  Starting Kate menu bar app now..."
nohup "$PYTHON" "$KATE_DIR/kate_menubar.py" > "$KATE_DIR/logs/menubar.log" 2>&1 &
echo "   ✓ Running — look for 𝙺 in your menu bar"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║         ✅  Install Complete         ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "  Menu bar: click 𝙺 in the top-right of your screen"
echo "  Hotkey:   press ⌘ + Shift + K anywhere"
echo ""
