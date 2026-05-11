# ╔══════════════════════════════════════════════════════════════════╗
# ║  ui_theme.py — Preferencias, colores y fuentes de Optem         ║
# ╚══════════════════════════════════════════════════════════════════╝
import os, json

# ─────────────────────────────────────────────────────────────────
#  PREFERENCIAS PERSISTENTES
# ─────────────────────────────────────────────────────────────────
os.chdir(os.path.dirname(os.path.abspath(__file__)))

PREFS_FILE = "optem_prefs.json"
DEFAULT_PREFS = {
    "accent": "#5A8F76", "dark_mode": False,
    "font_size": "Normal", "anim": True, "transparent_btns": False,
    "keyboard_nav": False, "voice_cmd": False, "screen_reader": False,
    "reinscripcion_activa": False
}

def load_prefs():
    if os.path.exists(PREFS_FILE):
        try:
            with open(PREFS_FILE, "r", encoding="utf-8") as f:
                p = json.load(f)
            for k, v in DEFAULT_PREFS.items():
                p.setdefault(k, v)
            return p
        except Exception:
            pass
    return dict(DEFAULT_PREFS)

def save_prefs(p):
    with open(PREFS_FILE, "w", encoding="utf-8") as f:
        json.dump(p, f, ensure_ascii=False, indent=2)

PREFS = load_prefs()

# ─────────────────────────────────────────────────────────────────
#  COLORES Y FUENTES
# ─────────────────────────────────────────────────────────────────
def _darken(hex_color, factor=0.15):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return "#{:02x}{:02x}{:02x}".format(
        max(0, int(r * (1 - factor))),
        max(0, int(g * (1 - factor))),
        max(0, int(b * (1 - factor))))

def _lighten(hex_color, factor=0.25):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return "#{:02x}{:02x}{:02x}".format(
        min(255, int(r + (255 - r) * factor)),
        min(255, int(g + (255 - g) * factor)),
        min(255, int(b + (255 - b) * factor)))

def C(key):
    dark   = PREFS["dark_mode"]
    accent = PREFS["accent"]
    # Superficie base en modo oscuro: gris neutro oscuro (sin verde forzado)
    return {
        "bg":          "#1A1A1F" if dark else "#FFFFFF",
        "surface":     "#26262E" if dark else "#FFFFFF",
        "surface2":    "#1E1E26" if dark else "#F5F5F5",
        "card":        "#2C2C36" if dark else "#F8F9FC",
        "border":      "#38383E" if dark else "#E0E0E0",
        "text":        "#E8E8F0" if dark else "#1A1A2E",
        "text2":       "#9898B0" if dark else "#4A4A6A",
        "text3":       "#6868A0" if dark else "#7A7A9A",
        "accent":      accent,
        "accent_dark": _darken(accent, 0.18),
        "accent_bg":   "#26262E" if dark else _lighten(accent, 0.88),
        "green":       "#4CAF7A" if dark else "#3A8F5A",
        "amber":       "#C18D52" if dark else "#B07A3A",
        "red":         "#C94A3A" if dark else "#B03A2A",
        "teal":        "#6AB0D4" if dark else "#3A7A9E",
        "pink":        "#B06898" if dark else "#8A4A7A",
        "navy":        "#1A1A1F" if dark else "#1A1A2E",
        "topbar":      "#1A1A1F" if dark else "#FFFFFF",
        "sidebar":     "#1A1A1F" if dark else "#F5F5F5",
    }.get(key, "#FF00FF")

def FS(role="body"):
    base = {"Pequeño": -2, "Normal": 0, "Grande": 3}[PREFS["font_size"]]
    return {
        "title": 26 + base, "h2": 20 + base, "h3": 14 + base,
        "body": 12 + base, "small": 10 + base, "mono": 32 + base
    }.get(role, 12 + base)
