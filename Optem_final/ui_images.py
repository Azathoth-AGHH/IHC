# ╔══════════════════════════════════════════════════════════════════╗
# ║  ui_images.py — Carga y procesamiento de imágenes decorativas    ║
# ╚══════════════════════════════════════════════════════════════════╝
import os, math
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont
from ui_theme import PREFS, C

# ── Caché global: evita releer disco y reprocesar imágenes ────────
_CACHE: dict = {}

_IMG_FILES = {
    "mienar":    "Imagenes/hello__i_m_miena___Image.jpg",
    "aesthetic": "Imagenes/_aesthetic.jpg",
    "cozy_desk": "Imagenes/descarga__3_.jpg",
    "lofi_desk": "Imagenes/descarga__1_.webp",
    "green_nook":"Imagenes/descarga.webp",
    "study_mot": "Imagenes/study_motivation.jpg",
    "chemistry": "Imagenes/Cozy_Chemistry_Study_Setup___Electrophile_Generation_Notes___.jpg",
    "notion_grn":"Imagenes/Notion_Gallery_Icon_-_Green_009_bulletjournalpages___1377.jpg",
}

def _crop_center(img, target_w, target_h):
    src_w, src_h = img.size
    ratio = max(target_w / src_w, target_h / src_h)
    new_w = int(src_w * ratio)
    new_h = int(src_h * ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top  = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))

def load_img(key, size=(300, 200)):
    cache_key = ("img", key, size)
    if cache_key in _CACHE:
        return _CACHE[cache_key]
    fname = _IMG_FILES.get(key)
    if not fname:
        return None
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), fname)
    if not os.path.exists(path):
        return None
    try:
        img = Image.open(path).convert("RGBA")
        img = _crop_center(img, size[0], size[1])
        result = ctk.CTkImage(img, size=size)
        _CACHE[cache_key] = result
        return result
    except Exception:
        return None

def load_img_rounded(key, size=(300, 200), radius=18):
    cache_key = ("rounded", key, size, radius)
    if cache_key in _CACHE:
        return _CACHE[cache_key]
    fname = _IMG_FILES.get(key)
    if not fname:
        return None
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), fname)
    if not os.path.exists(path):
        return None
    try:
        img = Image.open(path).convert("RGBA")
        img = _crop_center(img, size[0], size[1])
        mask = Image.new("L", size, 0)
        d = ImageDraw.Draw(mask)
        d.rounded_rectangle([0, 0, size[0]-1, size[1]-1], radius=radius, fill=255)
        img.putalpha(mask)
        result = ctk.CTkImage(img, size=size)
        _CACHE[cache_key] = result
        return result
    except Exception:
        return None

def load_logo(size=(64, 64), radius=0):
    cache_key = ("logo", size, radius)
    if cache_key in _CACHE:
        return _CACHE[cache_key]
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Imagenes", "logo_optem.png")
    if not os.path.exists(path):
        return None
    try:
        img = Image.open(path).convert("RGBA")
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
        img = img.resize(size, Image.LANCZOS)
        result = ctk.CTkImage(img, size=size)
        _CACHE[cache_key] = result
        return result
    except Exception:
        return None

def load_uaem_logo(size=(64, 64)):
    cache_key = ("uaem", size)
    if cache_key in _CACHE:
        return _CACHE[cache_key]
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Imagenes", "logo_uaem.png")
    if not os.path.exists(path):
        return None
    try:
        img = Image.open(path).convert("RGBA")
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
        img = img.resize(size, Image.LANCZOS)
        result = ctk.CTkImage(img, size=size)
        _CACHE[cache_key] = result
        return result
    except Exception:
        return None

def _hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def _hex2rgba(h, a):
    r, g, b = _hex2rgb(h)
    return (r, g, b, a)

def make_avatar(initials, size=48, bg=None):
    bg = bg or PREFS["accent"]
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    d.ellipse([0, 0, size-1, size-1], fill=_hex2rgba(bg, 255))
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            int(size * 0.35))
    except Exception:
        font = ImageFont.load_default()
    bbox = d.textbbox((0, 0), initials, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    d.text(((size-tw)//2, (size-th)//2-2), initials, fill="white", font=font)
    return ctk.CTkImage(img, size=(size, size))

def make_wave(w=900, h=100, color="#9B8DFF", opacity=90):
    cache_key = ("wave", w, h, color, opacity)
    if cache_key in _CACHE:
        return _CACHE[cache_key]
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    r, g, b = _hex2rgb(color)
    pts = []
    for x in range(w+1):
        y = int(h*0.45 + h*0.38*math.sin(x/w*2*math.pi*2.2+0.3))
        pts.append((x, y))
    pts += [(w, h), (0, h)]
    d.polygon(pts, fill=(r, g, b, opacity))
    result = ctk.CTkImage(img, size=(w, h))
    _CACHE[cache_key] = result
    return result
