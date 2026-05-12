#!/bin/bash
# Creates a double-clickable Kate.app in your Applications folder
# Run once: bash create_app.sh

KATE_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="Kate"
APP_PATH="/Applications/$APP_NAME.app"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║       Creating Kate.app              ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── Create .app bundle structure ─────────────────────────────────────────────
mkdir -p "$APP_PATH/Contents/MacOS"
mkdir -p "$APP_PATH/Contents/Resources"

# ── Write the launcher script ─────────────────────────────────────────────────
cat > "$APP_PATH/Contents/MacOS/Kate" << EOF
#!/bin/bash
source ~/.zshrc 2>/dev/null || true
osascript << 'APPLESCRIPT'
tell application "Terminal"
    activate
    set newTab to do script "source ~/.zshrc && python3 \"$KATE_DIR/jarvis.py\" chat"
    set custom title of front window to "Kate"
end tell
APPLESCRIPT
EOF

chmod +x "$APP_PATH/Contents/MacOS/Kate"

# ── Write Info.plist ──────────────────────────────────────────────────────────
cat > "$APP_PATH/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Kate</string>
    <key>CFBundleDisplayName</key>
    <string>Kate</string>
    <key>CFBundleIdentifier</key>
    <string>com.kofi.kate</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleExecutable</key>
    <string>Kate</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
    <key>LSUIElement</key>
    <false/>
</dict>
</plist>
EOF

# ── Create a simple icon using Python ────────────────────────────────────────
python3 << 'PYEOF'
import struct, zlib, os

def create_png(size=512):
    """Create a simple dark icon with K letter."""
    width = height = size
    # Dark background with gradient feel
    pixels = []
    for y in range(height):
        row = []
        for x in range(width):
            # Dark navy background
            r, g, b = 10, 12, 26
            # Subtle radial gradient
            cx, cy = width//2, height//2
            dist = ((x-cx)**2 + (y-cy)**2) ** 0.5
            max_dist = (width**2 + height**2) ** 0.5 / 2
            factor = 1 - (dist / max_dist) * 0.4
            r = int(r * factor + 20 * (1-factor))
            g = int(g * factor + 30 * (1-factor))
            b = int(b * factor + 60 * (1-factor))
            row.extend([r, g, b, 255])
        pixels.append(row)

    # Draw letter K
    cx, cy = width//2, height//2
    stroke = max(4, size//50)
    accent = (79, 195, 247)  # light blue

    def set_pixel(px, py, color, thick=1):
        for dy in range(-thick, thick+1):
            for dx in range(-thick, thick+1):
                nx, ny = px+dx, py+dy
                if 0 <= nx < width and 0 <= ny < height:
                    pixels[ny][nx*4:nx*4+4] = list(color) + [255]

    # K dimensions
    kx = cx - size//8
    ky_top = cy - size//4
    ky_bot = cy + size//4
    arm_x = kx + size//8

    # Vertical bar of K
    for y in range(ky_top, ky_bot):
        set_pixel(kx, y, accent, stroke)

    # Upper arm of K
    steps = size//4
    for i in range(steps):
        px = kx + i * (arm_x - kx + size//8) // steps
        py = cy - i * (cy - ky_top) // steps
        set_pixel(px, py, accent, stroke)

    # Lower arm of K
    for i in range(steps):
        px = kx + i * (arm_x - kx + size//8) // steps
        py = cy + i * (ky_bot - cy) // steps
        set_pixel(px, py, accent, stroke)

    # Build PNG
    def png_chunk(name, data):
        c = zlib.crc32(name + data) & 0xffffffff
        return struct.pack('>I', len(data)) + name + data + struct.pack('>I', c)

    raw = b''
    for row in pixels:
        raw += b'\x00' + bytes(row)

    compressed = zlib.compress(raw, 9)

    png = (b'\x89PNG\r\n\x1a\n' +
           png_chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) +
           png_chunk(b'IDAT', compressed) +
           png_chunk(b'IEND', b''))
    return png

# Save icon
icon_dir = "/Applications/Kate.app/Contents/Resources"
os.makedirs(icon_dir, exist_ok=True)
with open(f"{icon_dir}/AppIcon.png", 'wb') as f:
    f.write(create_png(512))
print("Icon created.")
PYEOF

# ── Convert PNG to ICNS ───────────────────────────────────────────────────────
ICONSET="/tmp/Kate.iconset"
mkdir -p "$ICONSET"
ICON_SRC="/Applications/Kate.app/Contents/Resources/AppIcon.png"

# Generate required icon sizes
for SIZE in 16 32 64 128 256 512; do
    sips -z $SIZE $SIZE "$ICON_SRC" --out "$ICONSET/icon_${SIZE}x${SIZE}.png" 2>/dev/null
    DOUBLE=$((SIZE*2))
    sips -z $DOUBLE $DOUBLE "$ICON_SRC" --out "$ICONSET/icon_${SIZE}x${SIZE}@2x.png" 2>/dev/null
done

iconutil -c icns "$ICONSET" -o "/Applications/Kate.app/Contents/Resources/AppIcon.icns" 2>/dev/null || true
rm -rf "$ICONSET"

# ── Register the app ──────────────────────────────────────────────────────────
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister \
    -f "$APP_PATH" 2>/dev/null || true

echo "   ✓ Kate.app created in /Applications"
echo ""

# ── Add to Dock ───────────────────────────────────────────────────────────────
echo "▶  Adding Kate to your Dock..."
defaults write com.apple.dock persistent-apps -array-add \
    "<dict><key>tile-data</key><dict><key>file-data</key><dict><key>_CFURLString</key><string>$APP_PATH</string><key>_CFURLStringType</key><integer>0</integer></dict></dict></dict>" \
    2>/dev/null || true
killall Dock 2>/dev/null || true
echo "   ✓ Kate added to Dock"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║         ✅  Done!                    ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "  • Double-click Kate in your Dock or Applications"
echo "  • Or press ⌘ + Shift + K from anywhere"
echo "  • Or say Spotlight: Cmd+Space → type 'Kate' → Enter"
echo ""
