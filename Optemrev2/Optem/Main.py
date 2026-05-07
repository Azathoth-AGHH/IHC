# ╔══════════════════════════════════════════════════════════════════╗
# ║           OPTEM · Agenda Virtual Inteligente UAEMéx             ║
# ║           Interfaz principal — escritorio (v2.0)                ║
# ╚══════════════════════════════════════════════════════════════════╝
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont
import time, threading, os, json, math
from datetime import datetime, timedelta
from tkinter import messagebox
import tkinter as tk

import random

from productivity_manager import ProductivityManager
from auth_manager         import AuthManager
from data_bridge          import DataBridge
from config_manager       import ConfigManager
from session_manager      import guardar_sesion, cargar_sesion, cerrar_sesion
from academic_engine      import AcademicEngine
from validator_engine     import ValidatorEngine
from event_daemon         import EventDaemon

# ─────────────────────────────────────────────────────────────────
#  PREFERENCIAS PERSISTENTES
# ─────────────────────────────────────────────────────────────────
# Cambiar al directorio del script para que los JSON se guarden correctamente
os.chdir(os.path.dirname(os.path.abspath(__file__)))

PREFS_FILE = "optem_prefs.json"
DEFAULT_PREFS = {"accent": "#9B8DFF", "dark_mode": False,
                 "font_size": "Normal", "anim": True, "transparent_btns": False,
                 "keyboard_nav": False, "voice_cmd": False, "screen_reader": False}

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
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return "#{:02x}{:02x}{:02x}".format(
        max(0,int(r*(1-factor))), max(0,int(g*(1-factor))), max(0,int(b*(1-factor))))

def C(key):
    dark   = PREFS["dark_mode"]
    accent = PREFS["accent"]
    return {
        "bg":          "#1A1A2E" if dark else "#F0EFFF",
        "surface":     "#16213E" if dark else "#FFFFFF",
        "surface2":    "#0F3460" if dark else "#F5F4FF",
        "border":      "#2D2D5E" if dark else "#E0DCFF",
        "text":        "#E8E6FF" if dark else "#2C2C48",
        "text2":       "#9090B8" if dark else "#7070A0",
        "text3":       "#6060A0" if dark else "#A0A0C0",
        "accent":      accent,
        "accent_dark": _darken(accent, 0.18),
        "accent_bg":   "#2A1F60" if dark else "#EAE7FF",
        "green":  "#27C97A" if dark else "#2ECC71",
        "amber":  "#F5A623" if dark else "#F39C12",
        "red":    "#FF5B5B" if dark else "#E74C3C",
        "teal":   "#30D5C8" if dark else "#1ABC9C",
        "pink":   "#FF6B9D",
        "navy":   "#0D0D22" if dark else "#2C2C48",
        "topbar": "#0D0D22" if dark else "#FFFFFF",
        "sidebar":"#12122A" if dark else "#FAFAFF",
    }.get(key, "#FF00FF")

def FS(role="body"):
    base = {"Pequeño":-2,"Normal":0,"Grande":3}[PREFS["font_size"]]
    return {"title":26+base,"h2":20+base,"h3":14+base,"body":12+base,
            "small":10+base,"mono":32+base}.get(role, 12+base)

# ─────────────────────────────────────────────────────────────────
#  IMÁGENES DECORATIVAS
# ─────────────────────────────────────────────────────────────────
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
    """Recorta la imagen desde el centro para llenar el tamaño sin deformar."""
    src_w, src_h = img.size
    ratio = max(target_w / src_w, target_h / src_h)
    new_w = int(src_w * ratio)
    new_h = int(src_h * ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top  = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))

def load_img(key, size=(300, 200)):
    """Carga una imagen decorativa como CTkImage (recorte centrado). Devuelve None si falla."""
    fname = _IMG_FILES.get(key)
    if not fname:
        return None
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, fname)
    if not os.path.exists(path):
        return None
    try:
        img = Image.open(path).convert("RGBA")
        img = _crop_center(img, size[0], size[1])
        return ctk.CTkImage(img, size=size)
    except Exception:
        return None

def load_img_rounded(key, size=(300, 200), radius=18):
    """Carga imagen con esquinas redondeadas y recorte centrado (sin deformar)."""
    fname = _IMG_FILES.get(key)
    if not fname:
        return None
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, fname)
    if not os.path.exists(path):
        return None
    try:
        img = Image.open(path).convert("RGBA")
        img = _crop_center(img, size[0], size[1])
        mask = Image.new("L", size, 0)
        d = ImageDraw.Draw(mask)
        d.rounded_rectangle([0, 0, size[0]-1, size[1]-1], radius=radius, fill=255)
        img.putalpha(mask)
        return ctk.CTkImage(img, size=size)
    except Exception:
        return None

def load_logo(size=(64, 64), radius=0):
    """Carga el logo oficial de Optem (ya tiene fondo transparente)."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "Imagenes", "logo_optem.png")
    if not os.path.exists(path):
        return None
    try:
        img = Image.open(path).convert("RGBA")
        # Recortar márgenes vacíos y centrar contenido
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
        img = img.resize(size, Image.LANCZOS)
        return ctk.CTkImage(img, size=size)
    except Exception:
        return None


def make_hero_img(key, w=900, h=180, tint=None, alpha=155):
    """Carga imagen con overlay de color semitransparente baked-in usando PIL."""
    fname = _IMG_FILES.get(key)
    if not fname:
        return None
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, fname)
    if not os.path.exists(path):
        return None
    try:
        img = Image.open(path).convert("RGBA")
        img = _crop_center(img, w, h)
        if tint:
            hx = tint.lstrip("#")
            r, g, b = int(hx[0:2],16), int(hx[2:4],16), int(hx[4:6],16)
            tint_layer = Image.new("RGBA", (w, h), (r, g, b, alpha))
            img = Image.alpha_composite(img, tint_layer)
        return ctk.CTkImage(img, size=(w, h))
    except Exception:
        return None

def _hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2],16) for i in (0,2,4))

def _hex2rgba(h, a):
    r,g,b = _hex2rgb(h)
    return (r,g,b,a)

def make_avatar(initials, size=48, bg=None):
    bg = bg or PREFS["accent"]
    img = Image.new("RGBA",(size,size),(0,0,0,0))
    d   = ImageDraw.Draw(img)
    d.ellipse([0,0,size-1,size-1], fill=_hex2rgba(bg,255))
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            int(size*0.35))
    except Exception:
        font = ImageFont.load_default()
    bbox = d.textbbox((0,0), initials, font=font)
    tw,th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    d.text(((size-tw)//2,(size-th)//2-2), initials, fill="white", font=font)
    return ctk.CTkImage(img, size=(size,size))

def make_wave(w=900, h=100, color="#9B8DFF", opacity=90):
    img = Image.new("RGBA",(w,h),(0,0,0,0))
    d   = ImageDraw.Draw(img)
    r,g,b = _hex2rgb(color)
    pts = []
    for x in range(w+1):
        y = int(h*0.45 + h*0.38*math.sin(x/w*2*math.pi*2.2+0.3))
        pts.append((x,y))
    pts += [(w,h),(0,h)]
    d.polygon(pts, fill=(r,g,b,opacity))
    return ctk.CTkImage(img, size=(w,h))

# ─────────────────────────────────────────────────────────────────
#  COMPONENTES BASE
# ─────────────────────────────────────────────────────────────────
class Card(ctk.CTkFrame):
    def __init__(self, parent, **kw):
        kw.setdefault("fg_color", C("surface"))
        kw.setdefault("corner_radius", 18)
        super().__init__(parent, **kw)

class Btn(ctk.CTkButton):
    def __init__(self, parent, **kw):
        kw.setdefault("fg_color",    C("accent"))
        kw.setdefault("hover_color", C("accent_dark"))
        kw.setdefault("text_color",  "#FFFFFF")
        kw.setdefault("corner_radius", 12)
        kw.setdefault("height", 42)
        kw.setdefault("font", ("Helvetica", FS("body"), "bold"))
        super().__init__(parent, **kw)

class BtnOutline(ctk.CTkButton):
    def __init__(self, parent, **kw):
        kw.setdefault("fg_color",    "transparent")
        kw.setdefault("hover_color", C("accent_bg"))
        kw.setdefault("text_color",  C("accent"))
        kw.setdefault("border_color",C("accent"))
        kw.setdefault("border_width", 2)
        kw.setdefault("corner_radius", 12)
        kw.setdefault("height", 42)
        kw.setdefault("font", ("Helvetica", FS("body"), "bold"))
        super().__init__(parent, **kw)

# ─────────────────────────────────────────────────────────────────
#  BASE DE DATOS LOCAL
# ─────────────────────────────────────────────────────────────────
CATEGORIAS_PERSONAL = [
    "📚 Estudio","🏃 Deporte","🎮 Ocio","🤝 Reunión",
    "🏥 Salud","✈️ Viaje","🎵 Cultura","💼 Trabajo",
    "📝 Tarea","⭐ Personal"]
CATEGORIAS_GLOBAL = [
    "📚 Tarea","📝 Examen","🧪 Práctica",
    "📋 Proyecto","📢 Aviso","🎓 Evento"]

def _file_personal(key): return os.path.join(os.path.dirname(os.path.abspath(__file__)), f"personal_{key}.json")
GLOBAL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "admin_global.json")

def cargar_personal(key):
    f = _file_personal(key)
    if os.path.exists(f):
        try:
            with open(f,"r",encoding="utf-8") as fp: return json.load(fp)
        except: pass
    return []

def guardar_personal(key, lista):
    with open(_file_personal(key),"w",encoding="utf-8") as f:
        json.dump(lista,f,ensure_ascii=False,indent=2)

def cargar_global():
    if os.path.exists(GLOBAL_FILE):
        try:
            with open(GLOBAL_FILE,"r",encoding="utf-8") as f: return json.load(f)
        except: pass
    return []

def guardar_global(lista):
    with open(GLOBAL_FILE,"w",encoding="utf-8") as f:
        json.dump(lista,f,ensure_ascii=False,indent=2)

# ─────────────────────────────────────────────────────────────────
#  DATOS DE EJEMPLO — se cargan si no hay datos previos
# ─────────────────────────────────────────────────────────────────
HOY = datetime.now()

def _fecha(delta_days):
    return (HOY + timedelta(days=delta_days)).strftime("%Y-%m-%d")

EJEMPLO_GLOBAL = [
    {"id":10001,"titulo":"Tarea: Análisis de sistemas — Ejercicios cap. 3","categoria":"📚 Tarea",
     "fecha":_fecha(2),"hora_inicio":"09:00","hora_fin":"10:00",
     "desc":"Resolver los ejercicios 1-5 del capítulo 3 del libro de Sistemas. Mostrar procedimiento completo.","prioridad":2},
    {"id":10002,"titulo":"Examen parcial — Cálculo Diferencial","categoria":"📝 Examen",
     "fecha":_fecha(5),"hora_inicio":"10:00","hora_fin":"12:00",
     "desc":"Temas: límites, derivadas, regla de la cadena y optimización. Traer calculadora científica. No se permiten apuntes.","prioridad":1},
    {"id":10003,"titulo":"Entrega: Proyecto final — Programación Web","categoria":"📋 Proyecto",
     "fecha":_fecha(10),"hora_inicio":"08:00","hora_fin":"23:59",
     "desc":"Entrega del repositorio en GitHub + presentación de 15 min. Equipos de 3 personas. Incluir documentación.","prioridad":1},
    {"id":10004,"titulo":"Práctica de laboratorio — Química Orgánica","categoria":"🧪 Práctica",
     "fecha":_fecha(3),"hora_inicio":"14:00","hora_fin":"16:00",
     "desc":"Práctica 4: Síntesis de compuestos orgánicos. Obligatorio: bata, guantes y gafas de seguridad.","prioridad":2},
    {"id":10005,"titulo":"📢 Aviso: Semana de registro de materias","categoria":"📢 Aviso",
     "fecha":_fecha(1),"hora_inicio":"00:00","hora_fin":"23:59",
     "desc":"El registro de materias para el siguiente semestre inicia esta semana. Revisar horarios en el portal UAEMéx.","prioridad":3},
    {"id":10006,"titulo":"Evento: Expo Ingeniería UAEMéx 2025","categoria":"🎓 Evento",
     "fecha":_fecha(14),"hora_inicio":"10:00","hora_fin":"18:00",
     "desc":"Feria de proyectos estudiantiles. Entrada libre, pabellón central. ¡Inscribe tu proyecto antes del viernes!","prioridad":4},
    {"id":10007,"titulo":"Tarea: Ensayo — Ética en Ingeniería","categoria":"📚 Tarea",
     "fecha":_fecha(4),"hora_inicio":"23:59","hora_fin":"23:59",
     "desc":"Ensayo de 5 cuartillas sobre dilemas éticos en el desarrollo tecnológico. Formato APA. Entregar vía Moodle.","prioridad":2},
    {"id":10008,"titulo":"Examen: Física II — Parcial 2","categoria":"📝 Examen",
     "fecha":_fecha(7),"hora_inicio":"08:00","hora_fin":"10:00",
     "desc":"Temas: Electromagnetismo, circuitos RC, ley de Faraday. Permitido: calculadora y formulario de 1 hoja.","prioridad":1},
    {"id":10009,"titulo":"Proyecto: Avance 2 — App Móvil (equipo)","categoria":"📋 Proyecto",
     "fecha":_fecha(6),"hora_inicio":"09:00","hora_fin":"11:00",
     "desc":"Presentar prototipo funcional en Flutter/React Native. Evaluación por el profesor. Llevar laptop.","prioridad":1},
    {"id":10010,"titulo":"🎓 Conferencia: IA aplicada a la Ingeniería","categoria":"🎓 Evento",
     "fecha":_fecha(8),"hora_inicio":"16:00","hora_fin":"18:00",
     "desc":"Ponencia del Dr. Martínez sobre aplicaciones de IA en ingeniería civil y mecánica. Auditorio principal, cupo limitado.","prioridad":4},
    {"id":10011,"titulo":"Práctica: Redes y Comunicaciones — Lab","categoria":"🧪 Práctica",
     "fecha":_fecha(9),"hora_inicio":"12:00","hora_fin":"14:00",
     "desc":"Configuración de routers y switches en Cisco Packet Tracer. Llevar archivo de la práctica anterior.","prioridad":2},
    {"id":10012,"titulo":"📢 Aviso: Entrega de constancias — Ventanilla","categoria":"📢 Aviso",
     "fecha":_fecha(0),"hora_inicio":"09:00","hora_fin":"14:00",
     "desc":"Entrega de constancias de estudio en ventanilla escolar. Traer credencial vigente y 2 copias.","prioridad":3},
]

EJEMPLO_CLASES = [
    # Clases de hoy
    {"id":20001,"titulo":"Clase: Programación Web — HTML/CSS","categoria":"📚 Estudio",
     "fecha":_fecha(0),"hora_inicio":"08:00","hora_fin":"10:00","desc":"Unidad 2: Diseño responsivo con Flexbox y Grid. Traer laptop con VS Code instalado.","prioridad":3},
    {"id":20002,"titulo":"Clase: Cálculo Diferencial","categoria":"📚 Estudio",
     "fecha":_fecha(0),"hora_inicio":"10:00","hora_fin":"12:00","desc":"Derivadas implícitas y optimización. Habrá quiz al inicio.","prioridad":2},
    {"id":20007,"titulo":"Sesión Pomodoro: Repasar apuntes","categoria":"⭐ Personal",
     "fecha":_fecha(0),"hora_inicio":"15:00","hora_fin":"16:30","desc":"Repasar temas de Cálculo y Física antes del parcial.","prioridad":2},
    {"id":20008,"titulo":"Tarea: Ejercicios Álgebra Lineal","categoria":"📝 Tarea",
     "fecha":_fecha(0),"hora_inicio":"18:00","hora_fin":"20:00","desc":"Resolver ejercicios 3.1 al 3.8 del libro, entregar en PDF vía classroom.","prioridad":1},
    # Mañana
    {"id":20003,"titulo":"Clase: Física II — Electromagnetismo","categoria":"📚 Estudio",
     "fecha":_fecha(1),"hora_inicio":"13:00","hora_fin":"15:00","desc":"Ley de Faraday e inducción electromagnética. Llevar calculadora.","prioridad":3},
    {"id":20006,"titulo":"Tarea: Mapa conceptual Física II","categoria":"📝 Tarea",
     "fecha":_fecha(1),"hora_inicio":"23:59","hora_fin":"23:59","desc":"Entregar mapa conceptual de Electromagnetismo en classroom antes de medianoche.","prioridad":1},
    {"id":20009,"titulo":"Proyecto: Avance 1 — App Móvil","categoria":"📋 Proyecto",
     "fecha":_fecha(1),"hora_inicio":"16:00","hora_fin":"18:00","desc":"Presentar wireframes y diagrama de casos de uso al equipo. Reunión en biblioteca.","prioridad":2},
    # Pasado mañana
    {"id":20004,"titulo":"Clase: Álgebra Lineal","categoria":"📚 Estudio",
     "fecha":_fecha(2),"hora_inicio":"09:00","hora_fin":"11:00","desc":"Transformaciones lineales, valores y vectores propios.","prioridad":3},
    {"id":20010,"titulo":"Práctica: Lab. Circuitos Eléctricos","categoria":"🧪 Práctica",
     "fecha":_fecha(2),"hora_inicio":"11:00","hora_fin":"13:00","desc":"Práctica 3: Circuitos RC y RL. Llevar bata, cables y multímetro.","prioridad":2},
    # Resto de la semana
    {"id":20005,"titulo":"Clase: Inglés Técnico","categoria":"📚 Estudio",
     "fecha":_fecha(3),"hora_inicio":"07:00","hora_fin":"09:00","desc":"Unit 4: Technical writing and documentation. Presentación oral 10 min.","prioridad":3},
    {"id":20011,"titulo":"Asesoría: Cálculo Diferencial","categoria":"⭐ Personal",
     "fecha":_fecha(3),"hora_inicio":"12:00","hora_fin":"13:00","desc":"Asesoría con el profesor para aclarar dudas del parcial. Cubículo 204.","prioridad":2},
    {"id":20012,"titulo":"Entrega: Reporte Práctica Química","categoria":"📝 Tarea",
     "fecha":_fecha(4),"hora_inicio":"08:00","hora_fin":"08:00","desc":"Subir reporte de la práctica 4 a Moodle. Incluir conclusiones y bibliografía.","prioridad":1},
    {"id":20013,"titulo":"Actividad: Lectura crítica cap. 5","categoria":"⭐ Personal",
     "fecha":_fecha(4),"hora_inicio":"20:00","hora_fin":"21:30","desc":"Leer y hacer resumen del capítulo 5 de Ingeniería de Software para exposición.","prioridad":3},
    {"id":20014,"titulo":"Estudio grupal: Examen Física II","categoria":"📚 Estudio",
     "fecha":_fecha(5),"hora_inicio":"10:00","hora_fin":"13:00","desc":"Sesión de estudio con el equipo. Punto de reunión: Cafetería central.","prioridad":2},
    {"id":20015,"titulo":"Descanso programado 🌿","categoria":"⭐ Personal",
     "fecha":_fecha(6),"hora_inicio":"10:00","hora_fin":"12:00","desc":"Tiempo libre para recargar energía. ¡El descanso también es productividad!","prioridad":4},
    # ── Más clases ────────────────────────────────────────────────
    {"id":20016,"titulo":"Clase: Redes y Comunicaciones","categoria":"📚 Estudio",
     "fecha":_fecha(3),"hora_inicio":"08:00","hora_fin":"10:00","desc":"Protocolos TCP/IP y modelo OSI. Examen parcial la próxima clase.","prioridad":2},
    {"id":20017,"titulo":"Clase: Programación Orientada a Objetos","categoria":"📚 Estudio",
     "fecha":_fecha(4),"hora_inicio":"10:00","hora_fin":"12:00","desc":"Herencia, polimorfismo e interfaces. Traer tarea del ejercicio de clases abstractas.","prioridad":2},
    {"id":20018,"titulo":"Clase: Base de Datos Avanzadas","categoria":"📚 Estudio",
     "fecha":_fecha(5),"hora_inicio":"09:00","hora_fin":"11:00","desc":"Procedimientos almacenados y triggers en MySQL. Traer laptop con XAMPP instalado.","prioridad":2},
    {"id":20019,"titulo":"Clase: Sistemas Operativos","categoria":"📚 Estudio",
     "fecha":_fecha(6),"hora_inicio":"11:00","hora_fin":"13:00","desc":"Planificación de procesos y gestión de memoria. Habrá práctica con Linux.","prioridad":3},
    # ── Deportes ──────────────────────────────────────────────────
    {"id":20020,"titulo":"⚽ Entrenamiento: Fútbol — Selección UAEMéx","categoria":"🏃 Deporte",
     "fecha":_fecha(0),"hora_inicio":"17:00","hora_fin":"19:00","desc":"Entrenamiento semanal del equipo. Cancha principal, traer uniforme y agua.","prioridad":3},
    {"id":20021,"titulo":"🏀 Práctica: Basquetbol interescolar","categoria":"🏃 Deporte",
     "fecha":_fecha(1),"hora_inicio":"18:00","hora_fin":"20:00","desc":"Práctica para el torneo interescolar. Gimnasio norte. Traer ropa deportiva.","prioridad":3},
    {"id":20024,"titulo":"🏊 Natación: Clase semanal","categoria":"🏃 Deporte",
     "fecha":_fecha(4),"hora_inicio":"07:00","hora_fin":"08:00","desc":"Clase de natación en alberca universitaria. Traer traje de baño y gorro.","prioridad":4},
    {"id":20027,"titulo":"🏃 Carrera: 5K Campus UAEMéx","categoria":"🏃 Deporte",
     "fecha":_fecha(7),"hora_inicio":"08:00","hora_fin":"10:00","desc":"Carrera recreativa de 5km dentro del campus. Inscripción gratuita en ventanilla deportiva.","prioridad":4},
    {"id":20030,"titulo":"🏐 Voleibol: Liga interna UAEMéx","categoria":"🏃 Deporte",
     "fecha":_fecha(2),"hora_inicio":"18:00","hora_fin":"20:00","desc":"Partido de la liga interna. Gimnasio sur, cancha 2. Traer tenis y rodilleras.","prioridad":3},
    # ── Reuniones ─────────────────────────────────────────────────
    {"id":20022,"titulo":"👥 Reunión: Comité estudiantil","categoria":"📋 Reunión",
     "fecha":_fecha(2),"hora_inicio":"13:00","hora_fin":"14:00","desc":"Reunión mensual del comité. Salón H-101. Puntos: eventos del semestre y presupuesto.","prioridad":2},
    {"id":20025,"titulo":"👥 Reunión de equipo: Proyecto App Móvil","categoria":"📋 Reunión",
     "fecha":_fecha(2),"hora_inicio":"14:00","hora_fin":"15:30","desc":"Revisión de avances del proyecto. Traer laptop con los últimos cambios en GitHub.","prioridad":2},
    {"id":20028,"titulo":"👥 Junta: Semana de bienvenida","categoria":"📋 Reunión",
     "fecha":_fecha(6),"hora_inicio":"12:00","hora_fin":"13:00","desc":"Organización de actividades para la semana de bienvenida. Sala de juntas edificio A.","prioridad":3},
    {"id":20031,"titulo":"👥 Reunión: Servicio social — Coordinación","categoria":"📋 Reunión",
     "fecha":_fecha(3),"hora_inicio":"09:00","hora_fin":"10:00","desc":"Reunión con el coordinador de servicio social para asignación de horas. Edificio D-204.","prioridad":2},
    # ── Cultural / Talleres ────────────────────────────────────────
    {"id":20023,"titulo":"🎤 Ensayo: Grupo de teatro universitario","categoria":"🎭 Cultural",
     "fecha":_fecha(3),"hora_inicio":"17:00","hora_fin":"19:00","desc":"Ensayo de la obra 'La vida es sueño'. Teatro universitario. Obligatorio asistir.","prioridad":3},
    {"id":20026,"titulo":"🎸 Taller: Música y bienestar estudiantil","categoria":"🎭 Cultural",
     "fecha":_fecha(5),"hora_inicio":"16:00","hora_fin":"17:30","desc":"Taller de música organizado por bienestar universitario. Cupo limitado a 20 personas.","prioridad":4},
    {"id":20029,"titulo":"🎨 Taller: Diseño UX/UI para apps","categoria":"🎭 Cultural",
     "fecha":_fecha(8),"hora_inicio":"15:00","hora_fin":"17:00","desc":"Taller extracurricular de diseño de interfaces. Traer laptop con Figma.","prioridad":3},
    {"id":20032,"titulo":"📸 Taller: Fotografía digital","categoria":"🎭 Cultural",
     "fecha":_fecha(9),"hora_inicio":"14:00","hora_fin":"16:00","desc":"Taller de fotografía para proyectos universitarios. Traer cámara o smartphone.","prioridad":4},
]

def _sembrar_datos_ejemplo(file_key):
    """Carga datos de ejemplo si las listas están vacías."""
    if not cargar_global():
        guardar_global(EJEMPLO_GLOBAL)
    if not cargar_personal(file_key):
        guardar_personal(file_key, EJEMPLO_CLASES)

# ─────────────────────────────────────────────────────────────────
#  DIÁLOGO: AGREGAR / EDITAR ACTIVIDAD
# ─────────────────────────────────────────────────────────────────
class DialogoActividad(ctk.CTkToplevel):
    def __init__(self, parent, categorias, on_save, actividad=None):
        super().__init__(parent)
        self.on_save = on_save
        act = actividad or {}
        self.title("Editar actividad" if actividad else "Nueva actividad")
        self.geometry("500x580")
        self.resizable(False, False)
        self.configure(fg_color=C("bg"))
        self.grab_set(); self.lift(); self.focus_force()

        ctk.CTkLabel(self,
            text="✏️  " + ("Editar" if actividad else "Nueva actividad"),
            font=("Helvetica",FS("h2"),"bold"),
            text_color=C("text")).pack(pady=(22,2), padx=28, anchor="w")
        ctk.CTkLabel(self, text="Completa los campos y guarda",
            font=("Helvetica",FS("small")), text_color=C("text2")
        ).pack(padx=28, anchor="w", pady=(0,16))

        form = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                      scrollbar_button_color=C("accent"))
        form.pack(fill="both", expand=True, padx=24, pady=(0,8))

        # ── Título ──
        self._lbl(form, "Título *")
        self.e_titulo = ctk.CTkEntry(form, placeholder_text="Ej: Clase de natación",
            height=42, corner_radius=12,
            font=("Helvetica",FS("body")),
            fg_color=C("surface"), text_color=C("text"), border_color=C("border"))
        if act.get("titulo"): self.e_titulo.insert(0, act["titulo"])
        self.e_titulo.pack(fill="x", pady=(4,12))

        # ── Categoría ──
        self._lbl(form, "Categoría")
        self.var_cat = ctk.StringVar(value=act.get("categoria", categorias[0]))
        ctk.CTkOptionMenu(form, values=categorias, variable=self.var_cat,
            height=42, corner_radius=12,
            fg_color=C("surface"), text_color=C("text"),
            button_color=C("accent"), button_hover_color=C("accent_dark"),
            dropdown_fg_color=C("surface"),
            font=("Helvetica",FS("body"))).pack(fill="x", pady=(4,12))

        # ── Fecha ──
        self._lbl(form, "Fecha (AAAA-MM-DD)")
        self.e_fecha = ctk.CTkEntry(form,
            placeholder_text=datetime.now().strftime("%Y-%m-%d"),
            height=42, corner_radius=12,
            font=("Helvetica",FS("body")),
            fg_color=C("surface"), text_color=C("text"), border_color=C("border"))
        if act.get("fecha"): self.e_fecha.insert(0, act["fecha"])
        self.e_fecha.pack(fill="x", pady=(4,12))

        # ── Hora inicio / fin ──
        hrow = ctk.CTkFrame(form, fg_color="transparent")
        hrow.pack(fill="x", pady=(0,12))
        hrow.columnconfigure((0,1), weight=1)

        lef = ctk.CTkFrame(hrow, fg_color="transparent")
        lef.grid(row=0, column=0, sticky="ew", padx=(0,6))
        self._lbl(lef, "Hora inicio")
        self.e_ini = ctk.CTkEntry(lef, placeholder_text="09:00", height=42,
            corner_radius=12, font=("Helvetica",FS("body")),
            fg_color=C("surface"), text_color=C("text"), border_color=C("border"))
        if act.get("hora_inicio"): self.e_ini.insert(0, act["hora_inicio"])
        self.e_ini.pack(fill="x", pady=(4,0))

        rig = ctk.CTkFrame(hrow, fg_color="transparent")
        rig.grid(row=0, column=1, sticky="ew", padx=(6,0))
        self._lbl(rig, "Hora fin")
        self.e_fin = ctk.CTkEntry(rig, placeholder_text="10:00", height=42,
            corner_radius=12, font=("Helvetica",FS("body")),
            fg_color=C("surface"), text_color=C("text"), border_color=C("border"))
        if act.get("hora_fin"): self.e_fin.insert(0, act["hora_fin"])
        self.e_fin.pack(fill="x", pady=(4,0))

        # ── Descripción ──
        self._lbl(form, "Notas (opcional)")
        self.e_desc = ctk.CTkTextbox(form, height=80, corner_radius=12,
            font=("Helvetica",FS("body")),
            fg_color=C("surface"), text_color=C("text"),
            border_color=C("border"), border_width=1)
        if act.get("desc"): self.e_desc.insert("0.0", act["desc"])
        self.e_desc.pack(fill="x", pady=(4,0))

        self.lbl_err = ctk.CTkLabel(self, text="", text_color=C("red"),
            font=("Helvetica",FS("small")))
        self.lbl_err.pack()

        br = ctk.CTkFrame(self, fg_color="transparent")
        br.pack(pady=12)
        Btn(br, text="💾  Guardar", width=160, command=self._guardar).pack(side="left", padx=6)
        BtnOutline(br, text="Cancelar", width=120, command=self.destroy).pack(side="left", padx=6)

    def _lbl(self, p, t):
        ctk.CTkLabel(p, text=t, font=("Helvetica",FS("small"),"bold"),
                     text_color=C("text2")).pack(anchor="w")

    def _guardar(self):
        titulo = self.e_titulo.get().strip()
        if not titulo:
            self.lbl_err.configure(text="⚠ El título es obligatorio"); return

        fecha    = self.e_fecha.get().strip() or datetime.now().strftime("%Y-%m-%d")
        hora_ini = self.e_ini.get().strip() or "00:00"
        hora_fin = self.e_fin.get().strip() or "01:00"

        # ── AcademicEngine: calcular prioridad automática por proximidad ──
        prioridad = 3  # valor por defecto (media)
        try:
            engine = AcademicEngine({"agenda": [], "materias": {}})
            resumen = engine.generar_resumen_tarea(titulo)
            # Calcular prioridad según días restantes hasta la fecha
            dias_restantes = (datetime.strptime(fecha, "%Y-%m-%d").date()
                              - datetime.now().date()).days
            if dias_restantes <= 1:
                prioridad = 1   # urgente
            elif dias_restantes <= 3:
                prioridad = 2   # alta
            elif dias_restantes <= 7:
                prioridad = 3   # media
            else:
                prioridad = 4   # baja
        except Exception:
            pass
        # ─────────────────────────────────────────────────────────────

        self.on_save({
            "titulo":      titulo,
            "categoria":   self.var_cat.get(),
            "fecha":       fecha,
            "hora_inicio": hora_ini,
            "hora_fin":    hora_fin,
            "desc":        self.e_desc.get("0.0","end").strip(),
            "id":          int(time.time()*1000),
            "prioridad":   prioridad,
        })
        self.destroy()

# ─────────────────────────────────────────────────────────────────
#  SIDEBAR (colapsable — diseño moderno)
# ─────────────────────────────────────────────────────────────────
class Sidebar(ctk.CTkFrame):
    TABS_EST = [("🏠", "Inicio"),     ("📅", "Mi Agenda"),
                ("🎯", "Actividades"),("⏱",  "Pomodoro"),
                ("⭐", "Logros"),      ("⚙️", "Ajustes")]
    TABS_ADM = [("🏠", "Inicio"),     ("📋", "Tareas globales"),
                ("📊", "Reportes"),   ("👥", "Alumnos"),
                ("📅", "Horarios"),   ("🏫", "Clases"),
                ("⚙️", "Ajustes")]

    W_OPEN   = 230
    W_CLOSED = 68

    def __init__(self, parent, rol, on_tab, **kw):
        super().__init__(parent, fg_color=C("sidebar"), corner_radius=0,
                         width=self.W_OPEN, **kw)
        self.pack_propagate(False)
        self.on_tab      = on_tab
        self._btns       = {}          # nombre → (CTkButton, ico, label)
        self._activo     = None
        self._open       = True
        self._animating  = False
        self._cur_w      = self.W_OPEN
        self._build(rol)

    # ── Construcción ─────────────────────────────────────────────
    def _build(self, rol):
        self._rol = rol
        # — Barra superior: hamburguesa + nombre app —
        self._topbar = ctk.CTkFrame(self, fg_color="transparent", height=56)
        self._topbar.pack(fill="x")
        self._topbar.pack_propagate(False)

        self._btn_ham = ctk.CTkButton(
            self._topbar, text="☰", width=44, height=44,
            corner_radius=12,
            fg_color="transparent", hover_color=C("accent_bg"),
            text_color=C("text"), font=("Helvetica", 20, "bold"),
            command=self._toggle)
        self._btn_ham.place(x=12, rely=0.5, anchor="w")

        self._lbl_app = ctk.CTkLabel(
            self._topbar, text="OPTEM",
            font=("Helvetica", 15, "bold"), text_color=C("text"))
        self._lbl_app.place(x=64, rely=0.5, anchor="w")

        # Separador
        ctk.CTkFrame(self, fg_color=C("border"), height=1).pack(fill="x")

        # — Bloque logo + título coloreado —
        self._hero = ctk.CTkFrame(self, fg_color=C("accent"),
                                   corner_radius=0, height=108)
        self._hero.pack(fill="x")
        self._hero.pack_propagate(False)

        # Onda decorativa en la parte inferior del hero
        _hw = make_wave(self.W_OPEN, 28, C("accent_dark"), 80)
        self._hero_wave_lbl = ctk.CTkLabel(
            self._hero, image=_hw, text="", fg_color="transparent")
        self._hero_wave_lbl.place(x=0, rely=1.0, anchor="sw")

        # Logo PNG transparente, centrado verticalmente a la izquierda
        _img = load_logo(size=(52, 52))
        self._logo_lbl = ctk.CTkLabel(self._hero, image=_img if _img else None,
                                       text="" if _img else "OP",
                                       font=("Helvetica", 20, "bold"),
                                       text_color="white",
                                       fg_color="transparent")
        self._logo_lbl.place(x=8, rely=0.42, anchor="w")

        # Nombre + badge de rol + subtítulo (se ocultan al cerrar)
        self._hero_txt = ctk.CTkFrame(self._hero, fg_color="transparent")
        self._hero_txt.place(x=66, rely=0.42, anchor="w")
        ctk.CTkLabel(self._hero_txt, text="OPTEM",
            font=("Helvetica", 16, "bold"), text_color="white").pack(anchor="w")
        # Badge de rol
        _rol_ico = "🏛️" if rol == "Administrativo" else "🎓"
        _rol_txt = "Admin" if rol == "Administrativo" else "Estudiante"
        self._hero_badge = ctk.CTkFrame(
            self._hero_txt, fg_color=C("accent_dark"), corner_radius=6)
        self._hero_badge.pack(anchor="w", pady=(3, 0))
        ctk.CTkLabel(self._hero_badge,
            text=f"{_rol_ico} {_rol_txt}",
            font=("Helvetica", 8, "bold"), text_color="white"
            ).pack(padx=6, pady=2)
        ctk.CTkLabel(self._hero_txt, text="UAEMéx",
            font=("Helvetica", 9), text_color="#DDEEFF").pack(anchor="w", pady=(2,0))

        # Separador
        ctk.CTkFrame(self, fg_color=C("border"), height=1).pack(fill="x")

        # — Etiqueta de sección —
        self._sec_lbl = ctk.CTkLabel(self, text="  MENÚ",
            font=("Helvetica", 9, "bold"), text_color=C("text3"),
            anchor="w")
        self._sec_lbl.pack(fill="x", padx=14, pady=(14, 4))

        # — Botones de navegación —
        self._nav = ctk.CTkFrame(self, fg_color="transparent")
        self._nav.pack(fill="x", padx=8)

        tabs = self.TABS_ADM if rol == "Administrativo" else self.TABS_EST
        for ico, nombre in tabs:
            # Pill indicador activo (barra izquierda)
            row = ctk.CTkFrame(self._nav, fg_color="transparent",
                               corner_radius=12, height=46)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            pill = ctk.CTkFrame(row, fg_color="transparent",
                                width=4, corner_radius=2)
            pill.place(x=0, rely=0, relheight=1)

            btn = ctk.CTkButton(
                row,
                text=f"  {ico}   {nombre}",
                anchor="w",
                fg_color="transparent",
                hover_color=C("accent_bg"),
                text_color=C("text2"),
                corner_radius=10,
                height=44,
                font=("Helvetica", FS("body")),
                command=lambda n=nombre: self._select(n))
            btn.place(x=8, y=1, relwidth=1, relheight=0.95)

            self._btns[nombre] = (btn, pill, ico, nombre)

        # — Botón de voz (visible cuando voice_cmd está activo) —
        # Frame contenedor fijo para mantener el orden en el pack
        self._mic_frame = ctk.CTkFrame(self, fg_color="transparent", height=50)
        self._mic_frame.pack(side="bottom", fill="x")
        self._mic_btn = ctk.CTkButton(self._mic_frame,
            text="🎙", width=44, height=44, corner_radius=22,
            fg_color=C("accent"), hover_color=C("accent_dark"),
            text_color="white", font=("Helvetica", 18),
            command=self._abrir_voz)
        # Visible solo cuando voice_cmd está activo
        if PREFS.get("voice_cmd", False):
            self._mic_btn.place(relx=0.5, rely=0.5, anchor="center")

        # — Separador inferior —
        ctk.CTkFrame(self, fg_color=C("border"), height=1).pack(
            fill="x", side="bottom", pady=(0, 0))

        # — Versión —
        self._ver_lbl = ctk.CTkLabel(self, text="v2.0 · UAEMéx 2025",
            font=("Helvetica", 8), text_color=C("text3"))
        self._ver_lbl.pack(side="bottom", pady=8)

        # — Imagen decorativa —
        self._deco_lbl = None
        _deco = load_img_rounded("green_nook", size=(190, 110), radius=14)
        if _deco:
            self._deco_lbl = ctk.CTkLabel(self, image=_deco, text="")
            self._deco_lbl.pack(side="bottom", pady=(0, 8), padx=10)

    # ── Toggle con animación suave ────────────────────────────────
    def _toggle(self):
        if self._animating:
            return
        self._animating = True
        self._open = not self._open
        target = self.W_OPEN if self._open else self.W_CLOSED
        # Ocultar textos inmediatamente al cerrar
        if not self._open:
            self._lbl_app.place_forget()
            self._hero_txt.place_forget()
            self._sec_lbl.configure(text="")
            if self._deco_lbl:
                self._deco_lbl.pack_forget()
            self._ver_lbl.configure(text="")
            for nombre, (btn, pill, ico, label) in self._btns.items():
                btn.configure(text=f" {ico}", anchor="center")
                btn.place(x=4, y=1, relwidth=0.92, relheight=0.95)
        self._animate(target)

    def _animate(self, target):
        diff = target - self._cur_w
        # Easing: mover 35% de la distancia restante (mín 8px para no quedarse atascado)
        step = int(diff * 0.35)
        if step == 0:
            step = 8 if diff > 0 else -8
        self._cur_w += step
        # Verificar si llegamos al destino
        if (diff > 0 and self._cur_w >= target) or (diff < 0 and self._cur_w <= target):
            self._cur_w = target
            self._animating = False
            if self._open:
                self._lbl_app.place(x=64, rely=0.5, anchor="w")
                self._hero_txt.place(x=66, rely=0.42, anchor="w")
                self._sec_lbl.configure(text="  MENÚ")
                if self._deco_lbl:
                    self._deco_lbl.pack(side="bottom", pady=(0, 8), padx=10)
                self._ver_lbl.configure(text="v2.0 · UAEMéx 2025")
                for nombre, (btn, pill, ico, label) in self._btns.items():
                    btn.configure(text=f"  {ico}   {label}", anchor="w")
                    btn.place(x=8, y=1, relwidth=1, relheight=0.95)
        self.configure(width=self._cur_w)
        if self._animating:
            self.after(16, lambda: self._animate(target))

    # ── Selección de pestaña ──────────────────────────────────────
    def _select(self, nombre):
        transp = PREFS.get("transparent_btns", False)
        # Desactivar anterior
        if self._activo and self._activo in self._btns:
            pb, pp, *_ = self._btns[self._activo]
            pb.configure(fg_color="transparent", text_color=C("text3"),
                         border_width=0)
            pp.configure(fg_color="transparent")
        self._activo = nombre
        b, pill, ico, label = self._btns[nombre]
        if transp:
            # Fondo sutil + borde visible: diferencia clara respecto a inactivos
            b.configure(fg_color=C("accent_bg"), text_color=C("accent"),
                        border_width=2, border_color=C("accent"))
        else:
            b.configure(fg_color=C("accent_bg"), text_color=C("accent"),
                        border_width=0)
        # Pill indicador
        pill.configure(fg_color=C("accent"))
        self.on_tab(nombre)

    def set_active(self, nombre):
        self._select(nombre)

    def refresh_mic_btn(self):
        """Muestra u oculta el botón de micrófono según la preferencia."""
        if PREFS.get("voice_cmd", False):
            self._mic_frame.configure(height=50)
            self._mic_btn.place(relx=0.5, rely=0.5, anchor="center")
        else:
            self._mic_btn.place_forget()
            self._mic_frame.configure(height=0)

    def update_accent(self):
        """Actualiza en tiempo real los elementos del sidebar al cambiar el color de acento."""
        try:
            self._hero.configure(fg_color=C("accent"))
            self._mic_btn.configure(
                fg_color=C("accent"), hover_color=C("accent_dark"))
            self._btn_ham.configure(hover_color=C("accent_bg"))
            # Badge de rol
            if hasattr(self, "_hero_badge"):
                self._hero_badge.configure(fg_color=C("accent_dark"))
            # Onda del hero
            if hasattr(self, "_hero_wave_lbl"):
                _hw = make_wave(self.W_OPEN, 28, C("accent_dark"), 80)
                self._hero_wave_lbl.configure(image=_hw)
            # Pill y botón activo
            if self._activo and self._activo in self._btns:
                b, pill, *_ = self._btns[self._activo]
                pill.configure(fg_color=C("accent"))
                transp = PREFS.get("transparent_btns", False)
                if transp:
                    b.configure(fg_color=C("accent_bg"), text_color=C("accent"),
                                border_color=C("accent"))
                else:
                    b.configure(fg_color=C("accent_bg"), text_color=C("accent"))
        except Exception:
            pass

    def _abrir_voz(self):
        """Abre el diálogo de comandos de voz."""
        DialogoVozCmd(self, self.on_tab, rol=getattr(self, "_rol", "Estudiante"))
# ─────────────────────────────────────────────────────────────────
#  PANEL: INICIO ESTUDIANTE
# ─────────────────────────────────────────────────────────────────
class PanelInicioEst(ctk.CTkScrollableFrame):
    def __init__(self, parent, datos, file_key, on_tab):
        super().__init__(parent, fg_color=C("bg"), scrollbar_button_color=C("accent"))
        self.datos    = datos
        self.file_key = file_key
        self.on_tab   = on_tab
        self._build()

    def _build(self):
        perfil = self.datos.get("perfil", {})
        xp     = perfil.get("xp", 0)
        racha  = perfil.get("racha", 0)
        nivel  = perfil.get("nivel", "Novato")

        # ── Hero banner con imagen a pantalla completa ──────────────────
        hero = ctk.CTkFrame(self, fg_color=C("accent"), corner_radius=0, height=180)
        hero.pack(fill="x", padx=0, pady=(0,0))
        hero.pack_propagate(False)

        # Sin imagen de fondo — solo color sólido de la paleta
        wave = make_wave(900, 80, C("accent_dark"), 90)
        ctk.CTkLabel(hero, image=wave, text="").place(relx=0, rely=0.35, anchor="w")

        hora = datetime.now().hour
        saludo = ("¡Buenas noches! 🌙" if hora>=21
                  else "¡Buenas tardes! ☀️" if hora>=13 else "¡Buenos días! 🌅")
        ctk.CTkLabel(hero, text=saludo,
                     font=("Helvetica",FS("h2"),"bold"), text_color="white").place(x=28,y=20)
        ctk.CTkLabel(hero, text=datetime.now().strftime("%A %d de %B, %Y"),
                     font=("Helvetica",FS("body")), text_color="white").place(x=28,y=56)
        ctk.CTkLabel(hero, text=f"Nivel: {nivel}  ·  {xp:,} XP  ·  🔥 {racha} días",
                     font=("Helvetica",FS("small")), text_color="white").place(x=28,y=86)

        lims = {"Novato":1000,"Intermedio":3000,"Avanzado":6000,"Experto":6000}
        max_xp = lims.get(nivel,1000)
        pct = min(xp/max_xp, 1.0)
        xp_bg = ctk.CTkFrame(hero, fg_color=C("accent_dark"), height=7, corner_radius=4, width=360)
        xp_bg.place(x=28, y=114)
        xp_fg = ctk.CTkFrame(hero, fg_color="white", height=7, corner_radius=4, width=int(360*pct))
        xp_fg.place(x=28, y=114)

        # ── Reloj en vivo (hero, esquina derecha) ────────────────
        _now0 = datetime.now()
        self._clock_lbl = ctk.CTkLabel(hero, text=_now0.strftime("%H:%M"),
            font=("Helvetica", 36, "bold"), text_color="white")
        self._clock_lbl.place(relx=1.0, rely=0.0, x=-18, y=16, anchor="ne")
        self._clock_sub = ctk.CTkLabel(hero, text=_now0.strftime("%S s · %d/%m/%Y"),
            font=("Helvetica", 10), text_color="white")
        self._clock_sub.place(relx=1.0, rely=0.0, x=-18, y=62, anchor="ne")
        self._tick_clock()

        # ── Título home estilo Notion ─────────────────────────────
        title_row = ctk.CTkFrame(self, fg_color="transparent")
        title_row.pack(fill="x", padx=24, pady=(18, 4))
        ctk.CTkLabel(title_row, text="🏠  home",
                     font=("Helvetica", 28, "bold"), text_color=C("text")).pack(side="left")

        # ── Galería estilo Notion: 4 tarjetas con imagen grande ──────────
        ctk.CTkLabel(self, text="📂  Gallery view",
                     font=("Helvetica", FS("small"), "bold"), text_color=C("text2")
                     ).pack(anchor="w", padx=24, pady=(0,6))

        gal_frame = ctk.CTkFrame(self, fg_color="transparent")
        gal_frame.pack(fill="x", padx=20, pady=(0, 16))

        _gal_data = [
            ("lofi_desk",   "📝  notas",    "Mis apuntes y resúmenes"),
            ("cozy_desk",   "📅  agenda",   "Horario y actividades"),
            ("green_nook",  "🎯  tareas",   "Pendientes y proyectos"),
            ("chemistry",   "⭐  logros",   "XP, rachas y niveles"),
            ("study_mot",   "⏱  pomodoro", "Sesiones de estudio"),
            ("notion_grn",  "🔗  recursos", "Links y materiales"),
        ]
        # 3 columnas x 2 filas
        for row_i in range(2):
            row_fr = ctk.CTkFrame(gal_frame, fg_color="transparent")
            row_fr.pack(fill="x", pady=4)
            row_fr.columnconfigure((0,1,2), weight=1)
            for col_i in range(3):
                idx = row_i * 3 + col_i
                if idx >= len(_gal_data): break
                key, label, sub = _gal_data[idx]
                card = ctk.CTkFrame(row_fr, fg_color=C("surface"), corner_radius=14,
                    cursor="hand2")
                card.grid(row=0, column=col_i, padx=5, sticky="ew")
                card.bind("<Enter>", lambda e, c=card: c.configure(fg_color=C("surface2")))
                card.bind("<Leave>", lambda e, c=card: c.configure(fg_color=C("surface")))
                inner = ctk.CTkFrame(card, fg_color="transparent")
                inner.pack(fill="both", expand=True)
                gi = load_img_rounded(key, size=(220, 120), radius=10)
                if gi:
                    ctk.CTkLabel(inner, image=gi, text="").pack(fill="x", padx=0, pady=0)
                ctk.CTkLabel(inner, text=label,
                    font=("Helvetica", FS("body"), "bold"), text_color=C("text"),
                    anchor="w").pack(fill="x", padx=10, pady=(6,0))
                ctk.CTkLabel(inner, text=sub,
                    font=("Helvetica", FS("small")), text_color=C("text2"),
                    anchor="w").pack(fill="x", padx=10, pady=(0,8))

        # ── Currently... sidebar-style widget ───────────────────
        curr_row = ctk.CTkFrame(self, fg_color="transparent")
        curr_row.pack(fill="x", padx=20, pady=(0,12))
        curr_row.columnconfigure(0, weight=3); curr_row.columnconfigure(1, weight=2)

        curr_card = Card(curr_row)
        curr_card.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(curr_card, text="✨  currently...",
            font=("Helvetica", FS("small"), "bold"),
            text_color=C("accent")).pack(anchor="w", padx=14, pady=(12,4))
        hora_act = datetime.now().hour
        musica   = "lo-fi hip hop 🎵" if 6 <= hora_act < 22 else "ambient chill 🌙"
        items = [
            ("🎵 listening to:", musica),
            ("📖 leyendo:", "Ingeniería de Software cap. 5"),
            ("💻 trabajando en:", "Proyecto App Móvil"),
            ("☕ bebiendo:", "café con leche"),
        ]
        for ico_txt, val_txt in items:
            rw = ctk.CTkFrame(curr_card, fg_color="transparent")
            rw.pack(fill="x", padx=14, pady=2)
            ctk.CTkLabel(rw, text=ico_txt, font=("Helvetica", FS("small")),
                text_color=C("text2"), anchor="w").pack(side="left")
            ctk.CTkLabel(rw, text=val_txt, font=("Helvetica", FS("small"), "bold"),
                text_color=C("text"), anchor="e").pack(side="right")
        ctk.CTkFrame(curr_card, fg_color="transparent", height=8).pack()

        # Ocupar columna izquierda con frase motivacional animada
        mot_card = Card(curr_row)
        mot_card.grid(row=0, column=0, padx=(0,10), sticky="nsew")
        _mot2 = load_img_rounded("chemistry", size=(340, 110), radius=12)
        if _mot2:
            ctk.CTkLabel(mot_card, image=_mot2, text="").pack(fill="x")
        mot_msgs = ["El éxito es la suma de pequeños esfuerzos repetidos día tras día. 💪",
                    "Estudia hoy, lidera mañana. 🚀",
                    "Cada sesión Pomodoro te acerca a tu meta. ⏱",
                    "¡Tú puedes con todo lo de hoy! ⭐"]
        import random as _rnd
        ctk.CTkLabel(mot_card, text=_rnd.choice(mot_msgs),
            font=("Helvetica", FS("small")), text_color=C("text2"),
            wraplength=300, justify="center").pack(padx=14, pady=10)

        # ── Stats 4 tarjetas ─────────────────────────────────────
        hoy_str   = datetime.now().strftime("%Y-%m-%d")
        acts_p    = cargar_personal(self.file_key)
        acts_g    = cargar_global()
        acts_hoy  = [a for a in acts_p+acts_g if a.get("fecha")==hoy_str]
        clases_hoy = [a for a in acts_p if "Estudio" in a.get("categoria","") or "Clase" in a.get("titulo","")]

        # ── Tabla To-do list ──────────────────────────────────────
        ctk.CTkLabel(self, text="📋  Table",
                     font=("Helvetica", FS("small"), "bold"), text_color=C("text2")
                     ).pack(anchor="w", padx=24, pady=(0,4))
        todo_title = ctk.CTkFrame(self, fg_color="transparent")
        todo_title.pack(fill="x", padx=20, pady=(0,6))
        ctk.CTkLabel(todo_title, text="☑  to-do list",
                     font=("Helvetica", FS("h3"), "bold"), text_color=C("text")).pack(side="left")
        Btn(todo_title, text="＋ Nueva", width=100, height=30,
            command=lambda: self.on_tab("Actividades")).pack(side="right")

        todo_card = Card(self)
        todo_card.pack(fill="x", padx=20, pady=(0,16))

        # Tabla con un solo grid para alinear header y filas
        tbl = ctk.CTkFrame(todo_card, fg_color="transparent")
        tbl.pack(fill="x", padx=8, pady=6)
        tbl.columnconfigure(0, weight=1)          # tarea (expande)
        tbl.columnconfigure(1, minsize=110)        # tipo
        tbl.columnconfigure(2, minsize=110)        # fecha
        tbl.columnconfigure(3, minsize=54)         # hecho

        # Cabecera
        hdr_bg = ctk.CTkFrame(tbl, fg_color=C("surface2"), corner_radius=8, height=32)
        hdr_bg.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0,4))
        hdr_bg.columnconfigure(0, weight=1)
        hdr_bg.columnconfigure(1, minsize=110)
        hdr_bg.columnconfigure(2, minsize=110)
        hdr_bg.columnconfigure(3, minsize=54)
        for ci, t in enumerate(["  tarea", "tipo", "fecha límite", "hecho"]):
            ctk.CTkLabel(hdr_bg, text=t,
                font=("Helvetica",FS("small"),"bold"),
                text_color=C("text2"), anchor="w"
                ).grid(row=0, column=ci, padx=8, pady=6, sticky="ew")

        _todo_items = sorted(
            [a for a in acts_p + acts_g if a.get("fecha","") >= hoy_str],
            key=lambda x: x.get("fecha","9999"))[:8]
        if not _todo_items:
            ctk.CTkLabel(tbl, text="No hay tareas pendientes 🎉",
                         font=("Helvetica",FS("body")), text_color=C("text2")
                         ).grid(row=1, column=0, columnspan=4, pady=14)
        for ri, td in enumerate(_todo_items, start=1):
            bg = C("surface2") if ri % 2 == 0 else "transparent"
            row_bg = ctk.CTkFrame(tbl, fg_color=bg, corner_radius=6, height=36)
            row_bg.grid(row=ri, column=0, columnspan=4, sticky="ew", pady=1)
            row_bg.columnconfigure(0, weight=1)
            row_bg.columnconfigure(1, minsize=110)
            row_bg.columnconfigure(2, minsize=110)
            row_bg.columnconfigure(3, minsize=54)
            ctk.CTkLabel(row_bg, text=td.get("titulo","?"), anchor="w",
                font=("Helvetica",FS("body")), text_color=C("text")
                ).grid(row=0, column=0, padx=8, pady=6, sticky="ew")
            cat   = td.get("categoria","")
            short = cat.split()[-1] if cat else "—"
            cat_col = C("accent") if short in ("Tarea","Examen") else \
                      C("green")  if short in ("Práctica","Estudio") else \
                      C("amber")  if short in ("Proyecto",) else \
                      C("teal")
            ctk.CTkLabel(row_bg, text=f"  {short[:10]}  ",
                font=("Helvetica",9,"bold"), text_color="white",
                fg_color=cat_col, corner_radius=6, height=22
                ).grid(row=0, column=1, padx=4, pady=4, sticky="")
            ctk.CTkLabel(row_bg, text=td.get("fecha","—"), anchor="center",
                font=("Helvetica",FS("small")), text_color=C("text2")
                ).grid(row=0, column=2, padx=4, sticky="ew")
            cb = ctk.CTkCheckBox(row_bg, text="", width=20, height=20,
                                 checkbox_width=18, checkbox_height=18,
                                 fg_color=C("accent"), hover_color=C("accent_dark"),
                                 border_color=C("border"))
            cb.grid(row=0, column=3, padx=12)
        ctk.CTkFrame(todo_card, fg_color="transparent", height=6).pack()

        # ── Mis clases de hoy ─────────────────────────────────────
        ctk.CTkLabel(self, text="🏫  Mis clases de hoy",
                     font=("Helvetica", FS("h3"), "bold"), text_color=C("text")
                     ).pack(anchor="w", padx=24, pady=(0,6))
        clases_card = Card(self)
        clases_card.pack(fill="x", padx=20, pady=(0,16))
        clases_filtradas = sorted(
            [a for a in acts_p if a.get("fecha","") == hoy_str and
             ("Estudio" in a.get("categoria","") or "Clase" in a.get("titulo",""))],
            key=lambda x: x.get("hora_inicio",""))
        if not clases_filtradas:
            # Mostrar las próximas clases si no hay hoy
            clases_filtradas = sorted(
                [a for a in acts_p if "Estudio" in a.get("categoria","")],
                key=lambda x: (x.get("fecha","9999"), x.get("hora_inicio","00:00")))[:4]
        if clases_filtradas:
            for cl in clases_filtradas[:5]:
                self._act_row(clases_card, cl)
        else:
            ctk.CTkLabel(clases_card, text="Sin clases registradas hoy",
                         font=("Helvetica",FS("body")), text_color=C("text2")).pack(pady=16)
        ctk.CTkFrame(clases_card, fg_color="transparent", height=6).pack()

        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.pack(fill="x", padx=20, pady=(0,16))
        stats = [
            ("📅", str(len(acts_hoy)),     "Actividades hoy",  C("accent")),
            ("🔥", str(racha),              "Días de racha",    C("amber")),
            ("⚡", f"{xp:,}",              "Puntos XP",        C("green")),
            ("📚", str(len(acts_p)),        "Mis actividades",  C("teal")),
        ]
        for i,(ico,val,lbl,col) in enumerate(stats):
            stats_row.columnconfigure(i, weight=1)
            card = Card(stats_row)
            card.grid(row=0, column=i, padx=6, sticky="ew")
            ctk.CTkLabel(card, text=ico, font=("Helvetica",26)).pack(pady=(16,4))
            lbl_val = ctk.CTkLabel(card, text=val, font=("Helvetica",FS("h2"),"bold"),
                         text_color=col)
            lbl_val.pack()
            ctk.CTkLabel(card, text=lbl, font=("Helvetica",FS("small")),
                         text_color=C("text2")).pack(pady=(2,16))
            if PREFS["anim"] and i == 0:
                self._pulse_label(lbl_val, col, C("accent_dark"))

        # ── Agenda del día + accesos rápidos ─────────────────────
        mid = ctk.CTkFrame(self, fg_color="transparent")
        mid.pack(fill="x", padx=20, pady=(0,16))
        mid.columnconfigure(0, weight=3)
        mid.columnconfigure(1, weight=2)

        left = Card(mid)
        left.grid(row=0, column=0, padx=(0,10), sticky="nsew")
        lh = ctk.CTkFrame(left, fg_color="transparent")
        lh.pack(fill="x", padx=16, pady=(14,8))
        ctk.CTkLabel(lh, text="📋  Agenda del día",
                     font=("Helvetica",FS("h3"),"bold"), text_color=C("text")).pack(side="left")
        Btn(lh, text="+ Agregar", width=110, height=34,
            command=lambda: self.on_tab("Actividades")).pack(side="right")

        if acts_hoy:
            for a in sorted(acts_hoy, key=lambda x: x.get("hora_inicio",""))[:7]:
                self._act_row(left, a)
        else:
            ctk.CTkLabel(left,
                text="Sin actividades hoy.\nUsa «Actividades» para agregar.",
                font=("Helvetica",FS("body")), text_color=C("text2"),
                justify="center").pack(pady=28)
        ctk.CTkFrame(left, fg_color="transparent", height=10).pack()

        right = Card(mid)
        right.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(right, text="⚡  Acceso rápido",
                     font=("Helvetica",FS("h3"),"bold"), text_color=C("text")
                     ).pack(padx=16, pady=(14,10), anchor="w")
        for txt,tab,col in [
            ("⏱ Iniciar Pomodoro","Pomodoro",C("accent")),
            ("🎯 Nueva actividad","Actividades",C("green")),
            ("⭐ Mis logros","Logros",C("amber")),
            ("📅 Agenda semanal","Mi Agenda",C("teal")),
        ]:
            ctk.CTkButton(right, text=txt, height=38, corner_radius=10,
                fg_color=col, hover_color=_darken(col,.15), text_color="white",
                font=("Helvetica",FS("body")),
                command=lambda t=tab: self.on_tab(t)).pack(fill="x", padx=14, pady=4)
        ctk.CTkFrame(right, fg_color="transparent", height=8).pack()

        # ── Próximos eventos ──────────────────────────────────────
        ctk.CTkLabel(self, text="🗓  Próximos eventos",
                     font=("Helvetica",FS("h3"),"bold"), text_color=C("text")
                     ).pack(padx=20, anchor="w", pady=(0,8))
        prox_card = Card(self)
        prox_card.pack(fill="x", padx=20, pady=(0,20))
        proximos = sorted([a for a in acts_p+acts_g if a.get("fecha","")>=hoy_str],
                           key=lambda x: x.get("fecha","9999"))[:6]
        if proximos:
            for a in proximos: self._prox_row(prox_card, a)
        else:
            ctk.CTkLabel(prox_card, text="No hay eventos próximos",
                         text_color=C("text2"), font=("Helvetica",FS("body"))).pack(pady=20)
        ctk.CTkFrame(prox_card, fg_color="transparent", height=6).pack()

        # ── Life progress report (estilo Notion) ─────────────────
        ctk.CTkLabel(self, text="✨  life progress report",
                     font=("Helvetica", FS("small"), "bold"), text_color=C("text2")
                     ).pack(anchor="w", padx=24, pady=(0,6))
        prog_card = Card(self)
        prog_card.pack(fill="x", padx=20, pady=(0,24))
        prog_inner = ctk.CTkFrame(prog_card, fg_color="transparent")
        prog_inner.pack(fill="x", padx=18, pady=14)

        from datetime import date
        today = date.today()
        year_pct  = today.timetuple().tm_yday / 365
        month_pct = today.day / 31
        week_pct  = (today.weekday() + 1) / 7

        for lp_label, lp_pct, lp_col in [
            ("Year",  year_pct,  C("accent")),
            ("Month", month_pct, C("teal")),
            ("Week",  week_pct,  C("pink")),
        ]:
            row_p = ctk.CTkFrame(prog_inner, fg_color="transparent")
            row_p.pack(fill="x", pady=4)
            ctk.CTkLabel(row_p, text=lp_label, width=52,
                font=("Helvetica", FS("small"), "bold"),
                text_color=C("text2"), anchor="w").pack(side="left")
            bar_bg = ctk.CTkFrame(row_p, fg_color=C("border"), corner_radius=6, height=8)
            bar_bg.pack(side="left", fill="x", expand=True, padx=(6,8))
            bar_bg.pack_propagate(False)
            ctk.CTkFrame(bar_bg, fg_color=lp_col, corner_radius=6,
                         height=8).place(x=0, y=0, relheight=1, relwidth=lp_pct)
            ctk.CTkLabel(row_p, text=f"{lp_pct*100:.0f}%", width=38,
                font=("Helvetica", FS("small")),
                text_color=C("text2"), anchor="e").pack(side="right")
        ctk.CTkFrame(prog_card, fg_color="transparent", height=4).pack()

    def _tick_clock(self):
        try:
            if not self.winfo_exists():
                return
            now = datetime.now()
            self._clock_lbl.configure(text=now.strftime("%H:%M"))
            self._clock_sub.configure(text=now.strftime("%S s  ·  %d/%m/%Y"))
            self.after(1000, self._tick_clock)
        except Exception:
            pass

    def _pulse_label(self, lbl, col_a, col_b, _state=True):
        """Alterna el color de un label para efecto pulso."""
        if not lbl.winfo_exists():
            return
        lbl.configure(text_color=col_a if _state else col_b)
        lbl.after(800, lambda: self._pulse_label(lbl, col_a, col_b, not _state))

    def _act_row(self, parent, a):
        row = ctk.CTkFrame(parent, fg_color=C("surface2"), corner_radius=10)
        row.pack(fill="x", padx=12, pady=3)
        ctk.CTkLabel(row, text=a.get("hora_inicio","--:--"),
                     font=("Helvetica",FS("small")), text_color=C("text2"),
                     width=46).pack(side="left", padx=8, pady=8)
        ctk.CTkLabel(row, text=a.get("titulo","Sin título"),
                     font=("Helvetica",FS("body"),"bold"),
                     text_color=C("text")).pack(side="left")
        cat = a.get("categoria","")
        if cat:
            ctk.CTkLabel(row, text=cat.split()[0],
                         font=("Helvetica",14)).pack(side="right", padx=10)

    def _prox_row(self, parent, a):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=4)
        ctk.CTkFrame(row, fg_color=C("accent"), width=4,
                     corner_radius=2).pack(side="left", fill="y", padx=(0,10))
        ctk.CTkLabel(row, text=a.get("fecha",""),
                     font=("Helvetica",FS("small")), text_color=C("text2"),
                     width=88).pack(side="left")
        ctk.CTkLabel(row, text=a.get("titulo","?"),
                     font=("Helvetica",FS("body"),"bold"),
                     text_color=C("text")).pack(side="left")
        ico = a.get("categoria","").split()[0] if a.get("categoria") else ""
        if ico:
            ctk.CTkLabel(row, text=ico, font=("Helvetica",FS("body")),
                         text_color=C("text2")).pack(side="right", padx=8)

# ─────────────────────────────────────────────────────────────────
#  PANEL: ACTIVIDADES PERSONALES
# ─────────────────────────────────────────────────────────────────
class PanelActividades(ctk.CTkFrame):
    def __init__(self, parent, file_key, rol="Estudiante", **kw):
        super().__init__(parent, fg_color=C("bg"), **kw)
        self.file_key = file_key
        self.rol      = rol
        self._filtro  = "Todas"
        self._build()

    def _build(self):
        # Header fijo
        hdr = ctk.CTkFrame(self, fg_color=C("surface"), corner_radius=0, height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ih = ctk.CTkFrame(hdr, fg_color="transparent")
        ih.pack(fill="both", expand=True, padx=24, pady=14)
        ctk.CTkLabel(ih, text="🎯  Mis Actividades Personales",
                     font=("Helvetica",FS("h2"),"bold"), text_color=C("text")).pack(side="left")
        Btn(ih, text="＋  Nueva actividad", width=190,
            command=self._nueva).pack(side="right")

        # Filtros
        filt_row = ctk.CTkFrame(self, fg_color="transparent")
        filt_row.pack(fill="x", padx=24, pady=10)
        self._fbtns = {}
        opciones = ["Todas"] + [c.split()[1] if len(c.split())>1 else c
                                 for c in CATEGORIAS_PERSONAL]
        for op in opciones:
            b = ctk.CTkButton(filt_row, text=op, width=88, height=32,
                corner_radius=8,
                fg_color=C("accent") if op==self._filtro else C("surface"),
                text_color="white"  if op==self._filtro else C("text2"),
                hover_color=C("accent"),
                font=("Helvetica",FS("small")),
                command=lambda o=op: self._set_filtro(o))
            b.pack(side="left", padx=3)
            self._fbtns[op] = b

        # ── Área de Entregas de Tareas y Trabajos ───────────────────
        entrega_card = Card(self)
        entrega_card.pack(fill="x", padx=20, pady=(0, 6))
        eh = ctk.CTkFrame(entrega_card, fg_color="transparent")
        eh.pack(fill="x", padx=16, pady=(12, 6))
        ctk.CTkLabel(eh, text="📤  Realizar Entrega de Tarea o Trabajo",
            font=("Helvetica", FS("h3"), "bold"), text_color=C("text")).pack(side="left")
        ctk.CTkLabel(eh, text="Cada entrega aumenta tu racha 🔥",
            font=("Helvetica", FS("small")), text_color=C("amber")).pack(side="right")

        ef = ctk.CTkFrame(entrega_card, fg_color="transparent")
        ef.pack(fill="x", padx=16, pady=(0, 12))
        ef.columnconfigure(0, weight=3); ef.columnconfigure(1, weight=2); ef.columnconfigure(2, weight=1)

        self.e_entrega_titulo = ctk.CTkEntry(ef,
            placeholder_text="Nombre de la tarea o trabajo...",
            height=38, corner_radius=10,
            font=("Helvetica", FS("body")),
            fg_color=C("surface2"), text_color=C("text"), border_color=C("border"))
        self.e_entrega_titulo.grid(row=0, column=0, padx=(0,8), sticky="ew")

        self.om_entrega_materia = ctk.CTkOptionMenu(ef,
            values=["Cálculo III", "Prog. Avanzada", "Física II", "Álgebra Superior",
                    "Lab. Sistemas", "Otra materia"],
            height=38, corner_radius=10,
            font=("Helvetica", FS("small")),
            fg_color=C("surface2"), text_color=C("text"),
            button_color=C("accent"), button_hover_color=C("accent_dark"))
        self.om_entrega_materia.grid(row=0, column=1, padx=(0,8), sticky="ew")

        Btn(ef, text="📤  Entregar  +🔥", height=38,
            command=self._realizar_entrega).grid(row=0, column=2, sticky="ew")

        self.lista = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                            scrollbar_button_color=C("accent"))
        self.lista.pack(fill="both", expand=True, padx=20, pady=(0,16))
        self._refresh()

    def _set_filtro(self, op):
        for n,b in self._fbtns.items():
            b.configure(fg_color=C("accent") if n==op else C("surface"),
                        text_color="white"  if n==op else C("text2"))
        self._filtro = op
        self._refresh()

    def _refresh(self):
        for w in self.lista.winfo_children(): w.destroy()
        lista = cargar_personal(self.file_key)

        # ── EventDaemon: mostrar alertas de proximidad activas ──────
        try:
            agenda_con_fecha = [
                {**a, "fecha_entrega": f"{a['fecha']} {a.get('hora_fin','23:59')}",
                 "titulo": a.get("titulo",""), "id": a.get("id","")}
                for a in lista if a.get("fecha") and a.get("hora_fin")
            ]
            daemon = EventDaemon(agenda_con_fecha)
            alertas = daemon.monitorear_proximidad()
            for alerta in alertas:
                color = C("red") if alerta["tipo"] == "URGENTE" else C("amber")
                banner = ctk.CTkFrame(self.lista, fg_color=color, corner_radius=10)
                banner.pack(fill="x", pady=(0,4))
                ctk.CTkLabel(banner, text=f"🔔  {alerta['msj']}",
                    font=("Helvetica",FS("small"),"bold"), text_color="white"
                    ).pack(padx=14, pady=8, anchor="w")
        except Exception:
            pass
        # ────────────────────────────────────────────────────────────

        if self._filtro != "Todas":
            lista = [a for a in lista if self._filtro in a.get("categoria","")]
        lista = sorted(lista, key=lambda x:(x.get("fecha","9999"),x.get("hora_inicio","00:00")))

        if not lista:
            ctk.CTkLabel(self.lista,
                text="🎯\n\nAún no tienes actividades personales.\nPresiona «＋ Nueva actividad» para comenzar.",
                font=("Helvetica",FS("body")), text_color=C("text2"),
                justify="center").pack(pady=60)
            return

        # Agrupar por fecha
        grupos = {}
        for a in lista:
            grupos.setdefault(a.get("fecha","Sin fecha"), []).append(a)

        for fecha, acts in grupos.items():
            try:
                dt   = datetime.strptime(fecha,"%Y-%m-%d")
                hoy  = datetime.now().date()
                diff = (dt.date()-hoy).days
                etiq = (f"Hoy · {fecha}" if diff==0
                        else f"Mañana · {fecha}" if diff==1
                        else f"Ayer · {fecha}" if diff==-1
                        else dt.strftime("%A %d de %B, %Y"))
            except Exception:
                etiq = fecha
            ctk.CTkLabel(self.lista, text=etiq.capitalize(),
                font=("Helvetica",FS("small"),"bold"), text_color=C("text2")
                ).pack(anchor="w", padx=4, pady=(14,4))
            for a in sorted(acts, key=lambda x: x.get("hora_inicio","00:00")):
                self._act_card(a)

    def _act_card(self, a):
        card = Card(self.lista)
        card.pack(fill="x", pady=4)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        col_map = {"Estudio":C("accent"),"Deporte":C("green"),"Ocio":C("teal"),
                   "Reunión":C("amber"),"Salud":C("red"),"Personal":C("pink"),
                   "Tarea":C("accent"),"Trabajo":C("navy")}
        cat   = a.get("categoria","")
        color = next((v for k,v in col_map.items() if k in cat), C("text3"))

        ctk.CTkFrame(inner, fg_color=color, width=6, corner_radius=3
                     ).pack(side="left", fill="y", padx=(0,12))

        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(info, text=a.get("titulo","Sin título"),
                     font=("Helvetica",FS("body"),"bold"), text_color=C("text")).pack(anchor="w")
        ctk.CTkLabel(info,
            text=f"{a.get('hora_inicio','?')} – {a.get('hora_fin','?')}  ·  {cat}",
            font=("Helvetica",FS("small")), text_color=C("text2")).pack(anchor="w", pady=(2,0))

        # Detectar tipo
        es_tarea = any(k in cat for k in ("Tarea","Examen","Práctica"))
        es_clase = "Estudio" in cat or "Clase" in a.get("titulo","")

        # Info de cierre para tareas
        if es_tarea:
            fecha_c = a.get("fecha","—")
            hora_c  = a.get("hora_fin","23:59")
            ctk.CTkLabel(info,
                text=f"🕐  Cierre: {fecha_c}  a las  {hora_c}",
                font=("Helvetica",FS("small"),"bold"),
                text_color=C("red")).pack(anchor="w", pady=(4,0))
        elif a.get("desc"):
            ctk.CTkLabel(info, text=a["desc"][:90]+("…" if len(a["desc"])>90 else ""),
                font=("Helvetica",FS("small")), text_color=C("text3")).pack(anchor="w")

        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack(side="right")

        if es_clase:
            ctk.CTkButton(btns, text="📖 Tema", width=82, height=32, corner_radius=10,
                fg_color=C("teal"), text_color="white",
                hover_color=_darken(C("teal"),.15),
                font=("Helvetica",FS("small"),"bold"),
                command=lambda _a=a: self._ver_tema(_a)).pack(pady=2)

        if es_tarea:
            ctk.CTkButton(btns, text="🤖 IA", width=82, height=32, corner_radius=10,
                fg_color=C("accent"), text_color="white",
                hover_color=C("accent_dark"),
                font=("Helvetica",FS("small"),"bold"),
                command=lambda _a=a: self._asistencia_ia(_a)).pack(pady=2)

        # Edición solo para actividades que NO sean tarea ni clase
        puede_editar = not (es_tarea or es_clase)
        if puede_editar:
            ctk.CTkButton(btns, text="✏️", width=36, height=36, corner_radius=10,
                fg_color=C("surface2"), text_color=C("text"), hover_color=C("accent_bg"),
                command=lambda _a=a: self._editar(_a)).pack(pady=2)
            ctk.CTkButton(btns, text="🗑", width=36, height=36, corner_radius=10,
                fg_color=C("surface2"), text_color=C("red"), hover_color="#FFE0E0",
                command=lambda _a=a: self._eliminar(_a)).pack(pady=2)




    def _realizar_entrega(self):
        """Registra una entrega de tarea/trabajo y aumenta la racha."""
        titulo = self.e_entrega_titulo.get().strip()
        materia = self.om_entrega_materia.get()
        if not titulo:
            self.e_entrega_titulo.configure(border_color=C("red"), border_width=2)
            self.after(1500, lambda: self.e_entrega_titulo.configure(
                border_color=C("border"), border_width=1))
            return
        # Registrar la entrega como actividad completada
        nueva = {
            "id": str(int(datetime.now().timestamp())),
            "titulo": f"[Entrega] {titulo}",
            "categoria": "✅ Tarea",
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "hora_inicio": datetime.now().strftime("%H:%M"),
            "hora_fin": datetime.now().strftime("%H:%M"),
            "desc": f"Materia: {materia} — Entregado el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "entregado": True,
        }
        try:
            lista = cargar_personal(self.file_key)
            lista.append(nueva)
            guardar_personal(self.file_key, lista)
        except Exception:
            pass
        # Aumentar racha en datos globales
        try:
            datos = DataBridge(self.file_key).cargar_datos() or {}
            perfil = datos.get("perfil", {})
            racha_actual = int(str(perfil.get("racha", 0)).replace("🔥", "").strip() or 0)
            perfil["racha"] = racha_actual + 1
            datos["perfil"] = perfil
            DataBridge(self.file_key).guardar_datos(datos)
        except Exception:
            pass
        # Limpiar campo y mostrar éxito
        self.e_entrega_titulo.delete(0, "end")
        top = ctk.CTkToplevel(self)
        top.title("¡Entrega registrada!")
        top.geometry("360x200")
        top.configure(fg_color=C("bg"))
        top.grab_set(); top.lift(); top.focus_force()
        ctk.CTkLabel(top, text="🎉", font=("Helvetica", 48)).pack(pady=(24, 4))
        ctk.CTkLabel(top, text=f"¡Entrega registrada!\n«{titulo}»",
            font=("Helvetica", FS("body"), "bold"), text_color=C("text"),
            justify="center").pack()
        ctk.CTkLabel(top, text="Tu racha aumentó 🔥 · +XP",
            font=("Helvetica", FS("small")), text_color=C("amber")).pack(pady=(4, 0))
        Btn(top, text="¡Genial!", width=120,
            command=lambda: (top.destroy(), self._refresh())).pack(pady=16)

    def _ver_tema(self, a):
        """Diálogo con el tema y resumen de la clase."""
        top = ctk.CTkToplevel(self)
        top.title("Tema de clase")
        top.geometry("500x400")
        top.configure(fg_color=C("bg"))
        top.grab_set(); top.lift(); top.focus_force()

        ctk.CTkLabel(top, text="📚  " + a.get("titulo","Clase"),
            font=("Helvetica",FS("h2"),"bold"), text_color=C("text"),
            wraplength=440).pack(padx=24, pady=(22,4), anchor="w")

        fecha  = a.get("fecha","—")
        hora_i = a.get("hora_inicio","—")
        hora_f = a.get("hora_fin","—")
        ctk.CTkLabel(top, text=f"📅  {fecha}    ·    {hora_i} – {hora_f}",
            font=("Helvetica",FS("small")), text_color=C("text2")).pack(padx=24, anchor="w")

        ctk.CTkFrame(top, fg_color=C("border"), height=1).pack(fill="x", padx=24, pady=12)

        ctk.CTkLabel(top, text="📝  Tema y contenido de la sesión:",
            font=("Helvetica",FS("body"),"bold"), text_color=C("text")).pack(padx=24, anchor="w")

        desc = a.get("desc") or "Sin descripción disponible. Edita la actividad para agregar el tema."
        txt = ctk.CTkTextbox(top, height=180, corner_radius=12,
            font=("Helvetica",FS("body")),
            fg_color=C("surface"), text_color=C("text"),
            border_color=C("border"), border_width=1)
        txt.pack(fill="x", padx=24, pady=(8,16))
        txt.insert("0.0", desc)
        txt.configure(state="disabled")

        Btn(top, text="Cerrar", width=120, command=top.destroy).pack(pady=(0,20))

    def _asistencia_ia(self, a):
        """Diálogo de asistencia IA para tareas."""
        top = ctk.CTkToplevel(self)
        top.title("Asistencia IA — " + a.get("titulo","Tarea"))
        top.geometry("520x520")
        top.configure(fg_color=C("bg"))
        top.grab_set(); top.lift(); top.focus_force()

        ctk.CTkLabel(top, text="🤖  Asistencia por IA",
            font=("Helvetica",FS("h2"),"bold"), text_color=C("text")).pack(padx=24, pady=(22,2), anchor="w")
        ctk.CTkLabel(top, text=a.get("titulo",""),
            font=("Helvetica",FS("body"),"bold"), text_color=C("accent"),
            wraplength=460).pack(padx=24, anchor="w")

        info_row = ctk.CTkFrame(top, fg_color=C("surface"), corner_radius=10)
        info_row.pack(fill="x", padx=24, pady=(10,0))
        ctk.CTkLabel(info_row,
            text=f"🕐  Cierre:   {a.get('fecha','—')}   a las   {a.get('hora_fin','23:59')}",
            font=("Helvetica",FS("small"),"bold"), text_color=C("red")).pack(padx=14, pady=10, anchor="w")

        ctk.CTkFrame(top, fg_color=C("border"), height=1).pack(fill="x", padx=24, pady=10)

        ctk.CTkLabel(top, text="💡  ¿Qué debo hacer? — Análisis IA:",
            font=("Helvetica",FS("body"),"bold"), text_color=C("text")).pack(padx=24, anchor="w")

        txt_out = ctk.CTkTextbox(top, height=200, corner_radius=12,
            font=("Helvetica",FS("body")),
            fg_color=C("surface"), text_color=C("text"),
            border_color=C("border"), border_width=1)
        txt_out.pack(fill="x", padx=24, pady=(8,8))
        txt_out.insert("0.0",
            f"Tarea: {a.get('titulo','')}\n\nDescripción:\n{a.get('desc','Sin descripción.')}"
            f"\n\nPresiona «Generar» para obtener sugerencias IA.")
        txt_out.configure(state="disabled")

        lbl_st = ctk.CTkLabel(top, text="", font=("Helvetica",FS("small")), text_color=C("text2"))
        lbl_st.pack()

        def _generar():
            lbl_st.configure(text="⏳  Generando análisis...", text_color=C("accent"))
            top.update()
            try:
                engine = AcademicEngine({"agenda":[], "materias":{}})
                resultado = engine.generar_resumen_tarea(a.get("titulo",""))
                txt_out.configure(state="normal")
                txt_out.delete("0.0","end")
                txt_out.insert("0.0", resultado)
                txt_out.configure(state="disabled")
                lbl_st.configure(text="✅  Análisis completado", text_color=C("green"))
            except Exception as ex:
                lbl_st.configure(text=f"⚠  Error: {ex}", text_color=C("red"))

        br = ctk.CTkFrame(top, fg_color="transparent")
        br.pack(pady=4)
        Btn(br, text="🤖  Generar sugerencias", width=200, command=_generar).pack(side="left", padx=6)
        BtnOutline(br, text="Cerrar", width=110, command=top.destroy).pack(side="left", padx=6)

    def _nueva(self):
        DialogoActividad(self, CATEGORIAS_PERSONAL, self._save_nueva)

    def _editar(self, a):
        orig = a.copy()
        def on_save(nueva):
            lista = [x for x in cargar_personal(self.file_key) if x.get("id")!=orig.get("id")]
            lista.append(nueva)
            guardar_personal(self.file_key, lista)
            self._refresh()
        DialogoActividad(self, CATEGORIAS_PERSONAL, on_save, actividad=a)

    def _eliminar(self, a):
        if messagebox.askyesno("Eliminar actividad",
                               f"¿Eliminar «{a.get('titulo')}»?"):
            lista = [x for x in cargar_personal(self.file_key) if x.get("id")!=a.get("id")]
            guardar_personal(self.file_key, lista)
            self._refresh()

    def _save_nueva(self, nueva):
        lista = cargar_personal(self.file_key)
        lista.append(nueva)
        guardar_personal(self.file_key, lista)
        self._refresh()

# ─────────────────────────────────────────────────────────────────
#  PANEL: AGENDA SEMANAL
# ─────────────────────────────────────────────────────────────────
class PanelAgendaSemanal(ctk.CTkFrame):
    DIAS = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]

    def __init__(self, parent, file_key, **kw):
        super().__init__(parent, fg_color=C("bg"), **kw)
        self.file_key = file_key
        self._offset  = 0
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=C("surface"), corner_radius=0, height=70)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ih = ctk.CTkFrame(hdr, fg_color="transparent")
        ih.pack(fill="both", expand=True, padx=24, pady=14)
        ctk.CTkLabel(ih, text="📅  Mi Agenda Semanal",
                     font=("Helvetica",FS("h2"),"bold"), text_color=C("text")).pack(side="left")
        nav = ctk.CTkFrame(ih, fg_color="transparent")
        nav.pack(side="right")
        ctk.CTkButton(nav, text="◀", width=40, height=36, corner_radius=8,
            fg_color=C("surface2"), text_color=C("text"),
            command=lambda: self._nav(-1)).pack(side="left", padx=4)
        self.lbl_sem = ctk.CTkLabel(nav, text="", width=170,
            font=("Helvetica",FS("body")), text_color=C("text"))
        self.lbl_sem.pack(side="left")
        ctk.CTkButton(nav, text="▶", width=40, height=36, corner_radius=8,
            fg_color=C("surface2"), text_color=C("text"),
            command=lambda: self._nav(1)).pack(side="left", padx=4)

        self.grid_fr = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                              scrollbar_button_color=C("accent"))
        self.grid_fr.pack(fill="both", expand=True, padx=16, pady=12)
        self._refresh()

    def _nav(self, delta):
        self._offset += delta; self._refresh()

    def _refresh(self):
        for w in self.grid_fr.winfo_children(): w.destroy()
        hoy   = datetime.now().date()
        lunes = hoy - timedelta(days=hoy.weekday()) + timedelta(weeks=self._offset)
        self.lbl_sem.configure(
            text=f"{lunes.strftime('%d %b')} – {(lunes+timedelta(6)).strftime('%d %b %Y')}")

        all_acts = cargar_personal(self.file_key) + cargar_global()

        dias_mostrar = []
        for i, dia in enumerate(self.DIAS):
            fecha_dia = lunes + timedelta(days=i)
            # En la semana actual, solo mostrar desde hoy
            if self._offset == 0 and fecha_dia < hoy:
                continue
            dias_mostrar.append((i, dia, fecha_dia))

        # Si no hay días que mostrar (todos pasaron), ir a semana siguiente
        if not dias_mostrar and self._offset == 0:
            self._offset = 1
            self._refresh()
            return

        for i, dia, fecha_dia in dias_mostrar:
            fecha_str = fecha_dia.strftime("%Y-%m-%d")
            es_hoy    = (fecha_dia == hoy)

            acts_dia = sorted([a for a in all_acts if a.get("fecha")==fecha_str],
                              key=lambda x: x.get("hora_inicio","00:00"))

            col_fr = ctk.CTkFrame(self.grid_fr,
                fg_color=C("surface"),
                corner_radius=14)
            col_fr.pack(side="left", fill="y", padx=5, expand=True, anchor="n")

            # Cabecera día
            dh = ctk.CTkFrame(col_fr,
                fg_color=C("accent") if es_hoy else C("surface2"),
                corner_radius=10, height=58)
            dh.pack(fill="x", padx=8, pady=8); dh.pack_propagate(False)
            ctk.CTkLabel(dh, text=dia[:3].upper(),
                font=("Helvetica",FS("small"),"bold"),
                text_color="white" if es_hoy else C("text2")
                ).place(relx=.5, rely=.28, anchor="center")
            ctk.CTkLabel(dh, text=fecha_dia.strftime("%d"),
                font=("Helvetica",FS("h2"),"bold"),
                text_color="white" if es_hoy else C("text")).place(relx=.5, rely=.7, anchor="center")

            if not acts_dia:
                ctk.CTkLabel(col_fr, text="Libre",
                    font=("Helvetica",FS("small")),
                    text_color=C("text3")).pack(pady=14)
            for a in acts_dia:
                arow = ctk.CTkFrame(col_fr, fg_color=C("accent_bg"), corner_radius=8)
                arow.pack(fill="x", padx=8, pady=3)
                titulo = a.get("titulo","?")[:16]
                ctk.CTkLabel(arow, text=titulo,
                    font=("Helvetica",FS("small"),"bold"), text_color=C("text")
                    ).pack(anchor="w", padx=8, pady=(6,0))
                ctk.CTkLabel(arow,
                    text=f"{a.get('hora_inicio','?')}–{a.get('hora_fin','?')}",
                    font=("Helvetica",FS("small")), text_color=C("text2")
                    ).pack(anchor="w", padx=8, pady=(0,6))
            ctk.CTkFrame(col_fr, fg_color="transparent", height=6).pack()

        # Auto-refresh cada 60 segundos para mantener "hoy" actualizado
        try:
            if self.winfo_exists():
                self.after(60000, self._refresh)
        except Exception:
            pass

# ─────────────────────────────────────────────────────────────────
#  PANEL: POMODORO
# ─────────────────────────────────────────────────────────────────
class PanelPomodoro(ctk.CTkFrame):
    def __init__(self, parent, file_key, datos, **kw):
        super().__init__(parent, fg_color=C("bg"), **kw)
        self.file_key = file_key
        self.datos    = datos
        self._seg     = 25*60
        self._on      = False
        self._tid     = None
        self._modo    = "🎯 Pomodoro"
        self._sesiones = 0
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="⏱  Técnica Pomodoro",
            font=("Helvetica",FS("h2"),"bold"), text_color=C("text")
            ).pack(pady=(28,4), padx=28, anchor="w")
        ctk.CTkLabel(self,
            text="Maximiza tu concentración con bloques de estudio enfocados",
            font=("Helvetica",FS("body")), text_color=C("text2")
            ).pack(padx=28, anchor="w", pady=(0,20))

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=28)
        main.columnconfigure(0, weight=2); main.columnconfigure(1, weight=1)

        # ── Izquierda: timer ─────────────────────────────────────
        left = Card(main)
        left.grid(row=0, column=0, padx=(0,16), sticky="nsew")

        # Botones de modo
        mbr = ctk.CTkFrame(left, fg_color="transparent")
        mbr.pack(pady=(20,10))
        modos = [("🎯 Pomodoro",25),("☕ Descanso corto",5),("🛋 Descanso largo",15)]
        self._mbtns = {}
        for lbl, mins in modos:
            activo = (lbl == self._modo)
            b = ctk.CTkButton(mbr, text=lbl, width=148, height=36,
                corner_radius=10,
                fg_color=C("accent") if activo else C("surface2"),
                text_color="white"   if activo else C("text"),
                hover_color=C("accent"),
                font=("Helvetica",FS("small")),
                command=lambda m=lbl,s=mins: self._set_modo(m,s))
            b.pack(side="left", padx=5)
            self._mbtns[lbl] = b

        # Canvas circular
        cs = 260
        self._can = tk.Canvas(left, width=cs, height=cs,
                              bg=C("surface"), highlightthickness=0)
        self._can.pack(pady=10)
        self._draw_ring(1.0)

        self.lbl_time = ctk.CTkLabel(left, text="25:00",
            font=("Helvetica",FS("mono"),"bold"), text_color=C("accent"))
        self.lbl_time.pack()
        self.lbl_est = ctk.CTkLabel(left, text="🎯 Pomodoro — Listo para iniciar",
            font=("Helvetica",FS("body")), text_color=C("text2"))
        self.lbl_est.pack(pady=(0,16))

        ctrl = ctk.CTkFrame(left, fg_color="transparent")
        ctrl.pack(pady=(0,24))
        self.btn_tog = Btn(ctrl, text="▶   Iniciar", width=160, command=self._toggle)
        self.btn_tog.pack(side="left", padx=8)
        BtnOutline(ctrl, text="↺  Resetear", width=130, command=self._reset
                   ).pack(side="left", padx=8)

        # ── Derecha: info ─────────────────────────────────────────
        right = ctk.CTkFrame(main, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")

        # Sesiones
        ses_card = Card(right); ses_card.pack(fill="x", pady=(0,14))
        ctk.CTkLabel(ses_card, text="📊  Sesiones hoy",
            font=("Helvetica",FS("h3"),"bold"), text_color=C("text")
            ).pack(padx=16, pady=(14,8), anchor="w")
        self.lbl_ses = ctk.CTkLabel(ses_card, text="0 / 4",
            font=("Helvetica",40,"bold"), text_color=C("accent"))
        self.lbl_ses.pack()
        self._cir_fr = ctk.CTkFrame(ses_card, fg_color="transparent")
        self._cir_fr.pack(pady=(4,16))
        self._update_circles()

        # Tips
        tips_card = Card(right); tips_card.pack(fill="x", pady=(0,14))
        ctk.CTkLabel(tips_card, text="💡  Tips Pomodoro",
            font=("Helvetica",FS("h3"),"bold"), text_color=C("text")
            ).pack(padx=16, pady=(14,8), anchor="w")
        for t in ["Elimina distracciones antes de empezar",
                  "Cada 4 pomodoros toma un descanso largo",
                  "Apunta tu progreso al terminar",
                  "Si surge algo urgente, anótalo y continúa"]:
            row = ctk.CTkFrame(tips_card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=3)
            ctk.CTkFrame(row, fg_color=C("accent"), width=6, height=6,
                         corner_radius=3).pack(side="left", padx=(0,8), pady=2)
            ctk.CTkLabel(row, text=t, font=("Helvetica",FS("small")),
                text_color=C("text2"), wraplength=220, justify="left").pack(side="left")
        ctk.CTkFrame(tips_card, fg_color="transparent", height=10).pack()

        # Imagen motivacional en pomodoro
        _pom_img = load_img_rounded("study_mot", size=(240, 160), radius=16)
        if not _pom_img:
            _pom_img = load_img_rounded("chemistry", size=(240, 160), radius=16)
        if _pom_img:
            pom_img_card = Card(right)
            pom_img_card.pack(fill="x", pady=(0,14))
            ctk.CTkLabel(pom_img_card, image=_pom_img, text="").pack(padx=10, pady=10)
            ctk.CTkLabel(pom_img_card, text="¡Tú puedes! 💪 Keep going",
                font=("Helvetica",FS("small"),"bold"), text_color=C("accent")
                ).pack(pady=(0,10))

        # XP
        xp_card = Card(right); xp_card.pack(fill="x")
        ctk.CTkLabel(xp_card, text="⚡  XP por sesión",
            font=("Helvetica",FS("h3"),"bold"), text_color=C("text")
            ).pack(padx=16, pady=(14,4), anchor="w")
        ctk.CTkLabel(xp_card, text="+100 XP",
            font=("Helvetica",32,"bold"), text_color=C("green")).pack()
        ctk.CTkLabel(xp_card,
            text="Al completar un Pomodoro de 25 min",
            font=("Helvetica",FS("small")), text_color=C("text2")).pack(pady=(0,16))

    def _draw_ring(self, progress):
        s = 260; pad = 24
        self._can.delete("all")
        self._can.configure(bg=C("surface"))
        self._can.create_oval(pad,pad,s-pad,s-pad, outline=C("border"), width=14)
        extent = -360 * progress
        if progress >= 0.999:
            # Tkinter no renderiza arco de 360°; usar oval completo
            self._can.create_oval(pad,pad,s-pad,s-pad,
                outline=C("accent"), width=14)
        elif abs(extent) > 0.5:
            self._can.create_arc(pad,pad,s-pad,s-pad,
                start=90, extent=extent,
                outline=C("accent"), width=14, style="arc")

    def _set_modo(self, lbl, mins):
        for n,b in self._mbtns.items():
            b.configure(fg_color=C("accent") if n==lbl else C("surface2"),
                        text_color="white"   if n==lbl else C("text"))
        self._modo = lbl
        self._seg  = mins*60
        self._on   = False
        if self._tid: self.after_cancel(self._tid)
        self.btn_tog.configure(text="▶   Iniciar")
        self.lbl_est.configure(text=f"{lbl} — Listo para iniciar")
        self._update_display()

    def _toggle(self):
        self._on = not self._on
        if self._on:
            self.btn_tog.configure(text="⏸   Pausar")
            self.lbl_est.configure(text=f"{self._modo} — En curso")
            self._tick()
        else:
            self.btn_tog.configure(text="▶   Continuar")
            self.lbl_est.configure(text=f"{self._modo} — Pausado")
            if self._tid: self.after_cancel(self._tid)

    def _tick(self):
        if not self._on: return
        if self._seg > 0:
            self._seg -= 1
            self._update_display()
            self._tid = self.after(1000, self._tick)
        else:
            self._on = False
            self.btn_tog.configure(text="▶   Iniciar")
            if "Pomodoro" in self._modo:
                self._sesiones += 1
                self.lbl_ses.configure(text=f"{self._sesiones} / 4")
                self._update_circles()
                try:
                    pm = ProductivityManager(datos_perfil=self.datos.get("perfil",{}))
                    resultado = pm.registrar_entrega_exitosa(True)
                    # Persistir el XP y la racha actualizados en disco
                    if resultado.get("status") == "success":
                        self.datos["perfil"] = pm.perfil
                        bridge = DataBridge(self.file_key)
                        bridge.guardar_datos(self.datos)
                except Exception:
                    pass
                messagebox.showinfo("¡Pomodoro completado! 🎉",
                    f"¡Excelente trabajo!\n+100 XP ganados\nSesiones hoy: {self._sesiones}")
            else:
                messagebox.showinfo("Descanso terminado ☕","¡Listo para volver a concentrarte!")
            self.lbl_est.configure(text=f"{self._modo} — ¡Completado! ✅")

    def _reset(self):
        self._on = False
        if self._tid: self.after_cancel(self._tid)
        mins_map = {"🎯 Pomodoro":25,"☕ Descanso corto":5,"🛋 Descanso largo":15}
        self._seg = mins_map.get(self._modo,25)*60
        self.btn_tog.configure(text="▶   Iniciar")
        self.lbl_est.configure(text=f"{self._modo} — Listo para iniciar")
        self._update_display()

    def _update_display(self):
        m,s = divmod(self._seg,60)
        self.lbl_time.configure(text=f"{m:02d}:{s:02d}")
        total = {"🎯 Pomodoro":25*60,"☕ Descanso corto":5*60,"🛋 Descanso largo":15*60}.get(self._modo,25*60)
        self._draw_ring(self._seg/total)

    def _update_circles(self):
        for w in self._cir_fr.winfo_children(): w.destroy()
        for i in range(4):
            ctk.CTkFrame(self._cir_fr,
                fg_color=C("accent") if i<self._sesiones else C("border"),
                width=20, height=20, corner_radius=10).pack(side="left", padx=4)

# ─────────────────────────────────────────────────────────────────
#  PANEL: LOGROS
# ─────────────────────────────────────────────────────────────────
class PanelLogros(ctk.CTkScrollableFrame):
    def __init__(self, parent, datos, **kw):
        super().__init__(parent, fg_color=C("bg"),
                         scrollbar_button_color=C("accent"), **kw)
        self.datos = datos
        self._build()

    def _build(self):
        perfil = self.datos.get("perfil",{})
        xp     = perfil.get("xp",0)
        racha  = perfil.get("racha",0)
        nivel  = perfil.get("nivel","Novato")

        ctk.CTkLabel(self, text="⭐  Sistema de Logros y Niveles",
            font=("Helvetica",FS("h2"),"bold"), text_color=C("text")
            ).pack(padx=24, pady=(24,4), anchor="w")
        ctk.CTkLabel(self,
            text="Gana XP entregando tareas a tiempo y completando sesiones Pomodoro",
            font=("Helvetica",FS("body")), text_color=C("text2")
            ).pack(padx=24, anchor="w", pady=(0,12))

        # Banner motivacional con imagen
        _mot_img = load_img_rounded("study_mot", size=(600, 130), radius=18)
        if _mot_img:
            mot_banner = ctk.CTkFrame(self, fg_color=C("accent_bg"), corner_radius=18)
            mot_banner.pack(fill="x", padx=24, pady=(0,14))
            ctk.CTkLabel(mot_banner, image=_mot_img, text="").pack(
                side="left", padx=10, pady=8)
            ctk.CTkLabel(mot_banner,
                text="¡Sigue así! Cada sesión\nte acerca al siguiente nivel 🚀",
                font=("Helvetica",FS("h3"),"bold"), text_color=C("accent"),
                justify="left").pack(side="left", padx=14)
        else:
            ctk.CTkFrame(self, fg_color="transparent", height=8).pack()


        # XP + Racha
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(0,20))
        top.columnconfigure((0,1), weight=1)

        # Anillo XP
        xp_card = Card(top); xp_card.grid(row=0,column=0,padx=(0,10),sticky="ew")
        cs = 160
        can = tk.Canvas(xp_card, width=cs, height=cs, bg=C("surface"), highlightthickness=0)
        can.pack(pady=(20,8))
        lims = {"Novato":1000,"Intermedio":3000,"Avanzado":6000,"Experto":6000}
        max_xp = lims.get(nivel,1000)
        pct = min(xp/max_xp,1.0)
        pad = 18
        can.create_oval(pad,pad,cs-pad,cs-pad, outline=C("border"), width=12)
        can.create_arc(pad,pad,cs-pad,cs-pad,
            start=90, extent=-360*pct, outline=C("accent"), width=12, style="arc")
        ctk.CTkLabel(xp_card, text=nivel,
            font=("Helvetica",FS("h3"),"bold"), text_color=C("accent")).pack()
        ctk.CTkLabel(xp_card, text=f"{xp:,} XP",
            font=("Helvetica",30,"bold"), text_color=C("text")).pack()
        ctk.CTkLabel(xp_card,
            text=f"Faltan {max(max_xp-xp,0):,} XP para el siguiente nivel",
            font=("Helvetica",FS("small")), text_color=C("text2")).pack(pady=(2,20))

        # Racha
        rc = Card(top); rc.grid(row=0,column=1,sticky="ew")
        self._flame_lbl = ctk.CTkLabel(rc, text="🔥", font=("Helvetica",52))
        self._flame_lbl.pack(pady=(24,4))
        self._flame_sizes = [44, 50, 56, 52, 48, 54, 46, 52]
        self._flame_colors = [C("amber"), "#FF8C00", C("amber"), "#FF6B00",
                              C("amber"), "#FFC107", "#FF8C00", C("amber")]
        self._flame_idx = 0
        self._animate_flame()
        ctk.CTkLabel(rc, text=str(racha), font=("Helvetica",52,"bold"),
            text_color=C("amber")).pack()
        ctk.CTkLabel(rc, text="Días consecutivos",
            font=("Helvetica",FS("body")), text_color=C("text2")).pack()
        bono = 1+(racha//5)*0.1
        ctk.CTkLabel(rc, text=f"Bono activo: ×{bono:.1f} XP",
            font=("Helvetica",FS("body"),"bold"), text_color=C("green")).pack(pady=(4,24))

        # Mapa de niveles
        ctk.CTkLabel(self, text="🗺  Mapa de niveles",
            font=("Helvetica",FS("h3"),"bold"), text_color=C("text")
            ).pack(padx=24, anchor="w", pady=(0,10))
        for ico,nom,xmin,xmax in [
            ("🌱","Novato",    0,    999),
            ("⚡","Intermedio",1000,2999),
            ("🚀","Avanzado",  3000,5999),
            ("👑","Experto",   6000,9999),
        ]:
            card = Card(self); card.pack(fill="x", padx=24, pady=5)
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=14)
            ib = ctk.CTkFrame(inner, fg_color=C("surface2"),
                              width=50, height=50, corner_radius=14)
            ib.pack(side="left", padx=(0,14)); ib.pack_propagate(False)
            ctk.CTkLabel(ib, text=ico, font=("Helvetica",22)
                         ).place(relx=.5,rely=.5,anchor="center")
            inf = ctk.CTkFrame(inner, fg_color="transparent")
            inf.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(inf, text=nom,
                font=("Helvetica",FS("h3"),"bold"), text_color=C("text")).pack(anchor="w")
            ctk.CTkLabel(inf, text=f"{xmin:,} – {xmax:,} XP",
                font=("Helvetica",FS("small")), text_color=C("text2")).pack(anchor="w")
            if xp>=xmin and xp<=xmax:
                tbg,ttx,tl = C("accent_bg"),C("accent"),"⬤ Nivel actual"
            elif xp>xmax:
                tbg,ttx,tl = "#E0F8F3","#0F6E56","✓ Completado"
            else:
                tbg,ttx,tl = C("surface2"),C("text3"),"🔒 Bloqueado"
            tf = ctk.CTkFrame(inner, fg_color=tbg, corner_radius=8, height=28)
            tf.pack(side="right"); tf.pack_propagate(False)
            ctk.CTkLabel(tf, text=tl, font=("Helvetica",FS("small"),"bold"),
                text_color=ttx).place(relx=.5,rely=.5,anchor="center")

        # Bonos de racha
        ctk.CTkLabel(self, text="🔥  Bonificaciones de racha",
            font=("Helvetica",FS("h3"),"bold"), text_color=C("text")
            ).pack(padx=24, anchor="w", pady=(16,10))
        brow = ctk.CTkFrame(self, fg_color="transparent")
        brow.pack(fill="x", padx=24, pady=(0,24))
        for d,b in [(5,"+10% XP"),(10,"+20% XP"),(20,"+40% XP"),(50,"+100% XP 👑")]:
            bc = Card(brow); bc.pack(side="left", expand=True, padx=6)
            ctk.CTkLabel(bc, text=f"{d}🔥", font=("Helvetica",FS("h2"),"bold"),
                text_color=C("amber")).pack(pady=(16,4))
            ctk.CTkLabel(bc, text=b, font=("Helvetica",FS("body"),"bold"),
                text_color=C("green")).pack(pady=(0,16))

    def _animate_flame(self):
        """Animación de parpadeo para la llama de racha."""
        try:
            if not self._flame_lbl.winfo_exists():
                return
            self._flame_idx = (self._flame_idx + 1) % len(self._flame_sizes)
            sz  = self._flame_sizes[self._flame_idx]
            col = self._flame_colors[self._flame_idx]
            self._flame_lbl.configure(font=("Helvetica", sz), text_color=col)
            self._flame_lbl.after(130, self._animate_flame)
        except Exception:
            pass

# ─────────────────────────────────────────────────────────────────
#  DIALOGO: COMANDOS DE VOZ
# ─────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────
#  LECTOR DE PANTALLA — Accesibilidad con TTS + navegación por flechas
# ─────────────────────────────────────────────────────────────────
class LectorPantalla:
    """
    Lector de pantalla ligero para Optem.
    - Navega recuadro a recuadro con ↑ ↓ ← →
    - Lee en voz alta el texto/descripción del widget enfocado (pyttsx3 o espeak)
    - Enter / Espacio activan el elemento enfocado
    - Resalta visualmente el elemento seleccionado con borde de acento
    """

    _instancia = None   # singleton por ventana

    # Solo widgets interactivos — excluir CTkFrame y CTkLabel genéricos
    # para evitar navegar a contenedores y etiquetas decorativas
    TIPOS_ENFOCABLES = (
        ctk.CTkButton, ctk.CTkSwitch, ctk.CTkCheckBox,
        ctk.CTkRadioButton, ctk.CTkOptionMenu, ctk.CTkEntry,
    )

    @classmethod
    def activar(cls, root):
        if cls._instancia:
            return
        cls._instancia = cls(root, anunciar=True)

    @classmethod
    def desactivar(cls, root):
        if cls._instancia:
            cls._instancia._destruir(root)
            cls._instancia = None

    def __init__(self, root, anunciar=False):
        self._root       = root
        self._elementos  = []
        self._idx        = 0
        self._resaltado  = None
        self._tts_engine = None
        self._tts_hilo   = None
        self._tts_sapi   = None
        self._cursor_lbl = None
        self._activo     = True
        self._init_tts()
        self._bindings   = []
        self._bind_keys(root)
        self._escanear(anunciar_activacion=anunciar)
        # Re-escanear solo cuando cambia de ventana (no cada widget)
        def _on_focus_in(e):
            if e.widget is root:
                self.after_idle(self._escanear)
        root.bind("<FocusIn>", _on_focus_in, add="+")

    def after_idle(self, fn):
        try:
            self._root.after_idle(fn)
        except Exception:
            pass

    # ── TTS ──────────────────────────────────────────────────────
    def _init_tts(self):
        import queue as _queue
        import threading as _threading
        import subprocess as _subprocess
        import platform as _platform
        self._tts_queue  = _queue.Queue()
        self._tts_engine = None
        self._tts_listo  = False

        def _worker():
            engine = None
            sapi_ok = False
            import platform as _platform_w
            sys_name = _platform_w.system()

            # En Windows intentar SAPI primero (más confiable que pyttsx3 en Python 3.13+)
            if sys_name == "Windows":
                try:
                    import win32com.client as _wc
                    _spk = _wc.Dispatch("SAPI.SpVoice")
                    # Buscar voz en español
                    try:
                        vcat = _wc.Dispatch("SAPI.SpObjectTokenCategory")
                        vcat.SetId(r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices", False)
                        for tok in vcat.EnumerateTokens():
                            try:
                                name = tok.GetDescription()
                                if "es" in name.lower() or "spanish" in name.lower() or "sabina" in name.lower() or "helena" in name.lower():
                                    _spk.Voice = tok
                                    break
                            except Exception:
                                pass
                    except Exception:
                        pass
                    self._tts_sapi = _spk
                    sapi_ok = True
                except Exception:
                    self._tts_sapi = None

            # Intentar pyttsx3 si SAPI no disponible o no en Windows
            if not sapi_ok:
                try:
                    import pyttsx3
                    engine = pyttsx3.init()
                    engine.setProperty("rate", 150)
                    voices = engine.getProperty("voices")
                    for v in voices:
                        if "es" in (getattr(v, "id", "") + getattr(v, "name", "")).lower():
                            engine.setProperty("voice", v.id)
                            break
                    self._tts_engine = engine
                except Exception:
                    self._tts_engine = None
            else:
                self._tts_engine = None

            self._tts_listo = True  # listo aunque no haya engine

            while True:
                try:
                    texto = self._tts_queue.get(timeout=0.5)
                except Exception:
                    continue
                if texto is None:
                    # Vaciar lo que quede en la cola y salir
                    try:
                        while not self._tts_queue.empty():
                            self._tts_queue.get_nowait()
                    except Exception:
                        pass
                    break
                # Si el lector fue desactivado, descartar sin hablar
                if not getattr(self, "_activo", True):
                    continue
                if not isinstance(texto, str) or not texto.strip():
                    continue
                try:
                    spoken = False
                    # Windows SAPI primero
                    if sys_name == "Windows" and getattr(self, "_tts_sapi", None):
                        try:
                            self._tts_sapi.Speak(texto)
                            spoken = True
                        except Exception:
                            spoken = False
                    # pyttsx3 si SAPI no funcionó
                    if not spoken and self._tts_engine:
                        try:
                            self._tts_engine.say(texto)
                            self._tts_engine.runAndWait()
                            spoken = True
                        except Exception:
                            spoken = False
                    # Fallback por plataforma
                    if not spoken:
                        if sys_name == "Darwin":
                            _subprocess.Popen(
                                ["say", "-v", "Paulina", texto],
                                stdout=_subprocess.DEVNULL, stderr=_subprocess.DEVNULL)
                        elif sys_name != "Windows":
                            for cmd in [["espeak-ng", "-v", "es+f3", "-s", "140", texto],
                                        ["espeak", "-v", "es", "-s", "140", texto],
                                        ["spd-say", texto]]:
                                try:
                                    _subprocess.Popen(
                                        cmd,
                                        stdout=_subprocess.DEVNULL, stderr=_subprocess.DEVNULL)
                                    break
                                except FileNotFoundError:
                                    continue
                except Exception:
                    pass

        t = _threading.Thread(target=_worker, daemon=True)
        t.start()
        self._tts_hilo = t

    def _hablar(self, texto):
        if not texto or not getattr(self, "_activo", True):
            return
        # Vaciar cola anterior para no acumular frases obsoletas
        try:
            while not self._tts_queue.empty():
                self._tts_queue.get_nowait()
        except Exception:
            pass
        try:
            self._tts_queue.put_nowait(texto)
        except Exception:
            pass

    # ── Escaneo de widgets ────────────────────────────────────────
    def _escanear(self, anunciar_activacion=False):
        """Recorre el árbol de widgets visibles y recoge los enfocables."""
        try:
            self._elementos = []
            self._recorrer(self._root)
            if self._elementos:
                self._idx = min(self._idx, len(self._elementos) - 1)
                if anunciar_activacion:
                    # Intentar anunciar ahora y con reintentos para que el worker TTS esté listo
                    self._hablar("Lector de pantalla activado. Usa las flechas para navegar.")
                    for delay in (600, 1400, 2800):
                        self._root.after(delay, lambda: self._hablar(
                            "Lector de pantalla activado. Usa las flechas para navegar."))
                    self._root.after(3200, lambda: self._enfocar(self._idx))
                else:
                    self._enfocar(self._idx)
        except Exception:
            pass

    def _recorrer(self, widget):
        try:
            # Saltar widgets marcados como excluidos (ej: sidebar)
            if getattr(widget, "_lector_excluir", False):
                return
            if isinstance(widget, self.TIPOS_ENFOCABLES):
                # Solo añadir si es visible y está en el layout
                info = widget.winfo_manager()
                if info in ("pack", "grid", "place") and widget.winfo_viewable():
                    # Excluir botones muy pequeños (decorativos)
                    try:
                        if widget.winfo_width() < 10 or widget.winfo_height() < 10:
                            return
                    except Exception:
                        pass
                    self._elementos.append(widget)
            for child in widget.winfo_children():
                self._recorrer(child)
        except Exception:
            pass

    # ── Navegación ───────────────────────────────────────────────
    def _bind_keys(self, root):
        """Registra atajos de teclado. SIN add=+ para ser el handler dominante."""
        bindings = [
            ("<Down>",   self._siguiente),
            ("<Right>",  self._siguiente),
            ("<Up>",     self._anterior),
            ("<Left>",   self._anterior),
            ("<Return>", self._activar),
            ("<space>",  self._activar),
        ]
        # Guardar handlers previos para restaurarlos al desactivar
        self._prev_handlers = {}

        def _make_handler(fn):
            def handler(e):
                w = e.widget
                # No interceptar en campos de texto activos
                try:
                    if isinstance(w, (tk.Entry, tk.Text)):
                        return  # dejar pasar
                    cls = w.__class__.__name__
                    if cls in ("Entry", "Text"):
                        return
                except Exception:
                    pass
                fn()
                return "break"
            return handler

        for key, fn in bindings:
            # Guardar handler previo
            try:
                prev = root.bind_all(key)
                self._prev_handlers[key] = prev if prev else ""
            except Exception:
                self._prev_handlers[key] = ""
            h = _make_handler(fn)
            root.bind_all(key, h)   # SIN add="+" → reemplaza el handler anterior
            self._bindings.append((key, h))

    def _siguiente(self):
        if not self._elementos:
            return
        self._idx = (self._idx + 1) % len(self._elementos)
        self._enfocar(self._idx)

    def _anterior(self):
        if not self._elementos:
            return
        self._idx = (self._idx - 1) % len(self._elementos)
        self._enfocar(self._idx)

    def _enfocar(self, idx):
        # Quitar resaltado anterior
        if self._resaltado:
            try:
                w = self._resaltado
                if hasattr(w, "configure"):
                    w.configure(border_width=0)
            except Exception:
                pass
            self._resaltado = None
        # Quitar indicador de cursor anterior
        if hasattr(self, "_cursor_lbl") and self._cursor_lbl:
            try:
                self._cursor_lbl.destroy()
            except Exception:
                pass
            self._cursor_lbl = None

        if not self._elementos:
            return
        widget = self._elementos[idx]

        # Resaltar con borde de acento grueso + indicador de cursor flotante
        try:
            if hasattr(widget, "configure"):
                widget.configure(border_width=3, border_color="#00E5FF")
                self._resaltado = widget
            widget.focus_set()
            # Indicador visual "▶ AQUÍ" sobre el widget
            try:
                lbl = ctk.CTkLabel(self._root, text="▶ AQUÍ",
                    fg_color="#00E5FF", text_color="#000000",
                    font=("Helvetica", 10, "bold"),
                    corner_radius=4, width=60, height=18)
                wx = widget.winfo_rootx() - self._root.winfo_rootx()
                wy = widget.winfo_rooty() - self._root.winfo_rooty() - 20
                lbl.place(x=wx, y=max(0, wy))
                self._cursor_lbl = lbl
            except Exception:
                self._cursor_lbl = None
        except Exception:
            pass

        # Intentar hacer scroll para que sea visible
        try:
            widget.update_idletasks()
        except Exception:
            pass

        # Leer en voz alta
        texto = self._leer_widget(widget)
        posicion = f"{idx + 1} de {len(self._elementos)}"
        self._hablar(f"{texto}, {posicion}")

    def _leer_widget(self, widget):
        """Extrae el texto descriptivo del widget para leerlo en voz alta."""
        # 1. Atributo personalizado _lector_desc tiene prioridad
        desc = getattr(widget, "_lector_desc", None)
        if desc:
            return str(desc)

        # 2. El propio widget tiene texto no vacío
        try:
            t = widget.cget("text")
            if t and str(t).strip():
                texto = str(t).strip()
                # Para switches vacíos ("") buscar el label del row padre
                if texto:
                    # Buscar label descriptivo en el frame padre (fila de ajustes)
                    padre = widget.master
                    if padre:
                        textos_padre = []
                        for child in padre.winfo_children():
                            if child is widget:
                                continue
                            try:
                                ct = child.cget("text")
                                if ct and str(ct).strip():
                                    textos_padre.append(str(ct).strip())
                            except Exception:
                                pass
                        if textos_padre:
                            # El label del row suele ser el primero
                            desc_padre = textos_padre[0]
                            # Para switches indicar estado
                            if isinstance(widget, ctk.CTkSwitch):
                                estado = "activado" if widget.get() else "desactivado"
                                return f"{desc_padre}, {estado}"
                            # Para botones con solo emoji/símbolo, añadir contexto
                            if len(texto) <= 3:
                                return f"{desc_padre}: {texto}"
                        return texto
        except Exception:
            pass

        # 3. Para switches sin texto: buscar label en el row padre
        if isinstance(widget, ctk.CTkSwitch):
            padre = widget.master
            if padre:
                for child in padre.winfo_children():
                    if child is widget:
                        continue
                    try:
                        ct = child.cget("text")
                        if ct and str(ct).strip():
                            estado = "activado" if widget.get() else "desactivado"
                            return f"{str(ct).strip()}, {estado}"
                    except Exception:
                        pass
                # Subir un nivel más
                abuelo = getattr(padre, "master", None)
                if abuelo:
                    for child in abuelo.winfo_children():
                        if child is widget or child is padre:
                            continue
                        try:
                            ct = child.cget("text")
                            if ct and str(ct).strip():
                                estado = "activado" if widget.get() else "desactivado"
                                return f"{str(ct).strip()}, {estado}"
                        except Exception:
                            pass
            return "Switch, " + ("activado" if widget.get() else "desactivado")

        # 4. Buscar texto en hijos directos
        try:
            for child in widget.winfo_children():
                try:
                    t = child.cget("text")
                    if t and str(t).strip():
                        return str(t).strip()
                except Exception:
                    pass
        except Exception:
            pass

        # 5. Para CTkEntry leer placeholder o contenido
        if isinstance(widget, ctk.CTkEntry):
            try:
                contenido = widget.get()
                if contenido.strip():
                    return f"Campo de texto: {contenido.strip()}"
                ph = widget.cget("placeholder_text")
                if ph:
                    return f"Campo: {ph}"
            except Exception:
                pass
            return "Campo de texto"

        # 6. Fallback: tipo de widget en español
        tipos = {
            "CTkButton": "Botón",
            "CTkSwitch": "Interruptor",
            "CTkCheckBox": "Casilla",
            "CTkRadioButton": "Opción",
            "CTkOptionMenu": "Menú de opciones",
            "CTkEntry": "Campo de texto",
        }
        clase = widget.__class__.__name__
        return tipos.get(clase, clase.replace("CTk", ""))

    def _activar(self):
        if not self._elementos or self._idx >= len(self._elementos):
            return
        widget = self._elementos[self._idx]
        try:
            if isinstance(widget, ctk.CTkButton):
                widget.invoke()
            elif isinstance(widget, ctk.CTkSwitch):
                widget.toggle()
            elif isinstance(widget, ctk.CTkCheckBox):
                widget.toggle()
            elif isinstance(widget, ctk.CTkRadioButton):
                widget.invoke()
            elif isinstance(widget, ctk.CTkEntry):
                widget.focus_set()
        except Exception:
            pass

    # ── Limpieza ─────────────────────────────────────────────────
    def _destruir(self, root):
        # Marcar como inactivo para que _hablar ignore peticiones nuevas
        self._activo = False

        # Restaurar handlers anteriores (o quitar si no había)
        for key, handler in self._bindings:
            try:
                prev = self._prev_handlers.get(key, "")
                if prev:
                    root.bind_all(key, prev)
                else:
                    root.unbind_all(key)
            except Exception:
                pass
        # Quitar resaltado
        if self._resaltado:
            try:
                self._resaltado.configure(border_width=0)
            except Exception:
                pass
        # Quitar indicador de cursor
        if hasattr(self, "_cursor_lbl") and self._cursor_lbl:
            try:
                self._cursor_lbl.destroy()
            except Exception:
                pass
        # Vaciar la cola por completo antes de parar el worker
        try:
            while not self._tts_queue.empty():
                self._tts_queue.get_nowait()
        except Exception:
            pass
        # Interrumpir motores TTS activos
        try:
            if getattr(self, "_tts_engine", None):
                self._tts_engine.stop()
        except Exception:
            pass
        try:
            sapi = getattr(self, "_tts_sapi", None)
            if sapi:
                sapi.Speak("", 3)   # SVSFPurgeBeforeSpeak = 3 → cancela lo pendiente
        except Exception:
            pass
        # Señal de parada al worker (None termina el loop)
        try:
            self._tts_queue.put_nowait(None)
        except Exception:
            pass


class DialogoVozCmd(ctk.CTkToplevel):
    """Panel de comandos de voz con transcripción en tiempo real y comandos por rol."""

    # Comandos compartidos por ambos roles
    COMANDOS_COMUNES = {
        "inicio":       ("Inicio",   "Ir a la pantalla de inicio"),
        "ajustes":      ("Ajustes",  "Abrir configuración"),
    }

    # Solo para Estudiante
    COMANDOS_EST = {
        "agenda":       ("Mi Agenda",    "Ver tu agenda semanal"),
        "mi agenda":    ("Mi Agenda",    "Ver tu agenda semanal"),
        "actividades":  ("Actividades",  "Ver tus actividades y tareas"),
        "tareas":       ("Actividades",  "Ver tus tareas pendientes"),
        "pomodoro":     ("Pomodoro",     "Iniciar temporizador Pomodoro"),
        "temporizador": ("Pomodoro",     "Iniciar temporizador Pomodoro"),
        "logros":       ("Logros",       "Ver tus logros y progreso"),
        "mis logros":   ("Logros",       "Ver tus logros y progreso"),
        "estadísticas": ("Logros",       "Ver estadísticas personales"),
    }

    # Solo para Administrativo
    COMANDOS_ADM = {
        "tareas globales": ("Tareas globales", "Gestionar tareas para todos los alumnos"),
        "tareas":          ("Tareas globales", "Ver tareas globales"),
        "reportes":        ("Reportes",        "Ver reportes académicos"),
        "ver reportes":    ("Reportes",        "Abrir panel de reportes"),
        "alumnos":         ("Alumnos",         "Gestionar lista de alumnos"),
        "ver alumnos":     ("Alumnos",         "Ver listado de alumnos"),
        "horarios":        ("Horarios",        "Ver y editar horarios de clases"),
        "ver horarios":    ("Horarios",        "Abrir gestión de horarios"),
        "clases":          ("Clases",          "Gestionar clases registradas"),
        "ver clases":      ("Clases",          "Abrir panel de clases"),
    }

    def __init__(self, parent, on_cmd, rol="Estudiante"):
        super().__init__(parent)
        self.on_cmd      = on_cmd
        self.rol         = rol
        self._escuchando = False
        self._hilo_voz   = None
        # Construir mapa de comandos según rol
        self.COMANDOS = dict(self.COMANDOS_COMUNES)
        if rol == "Administrativo":
            self.COMANDOS.update(self.COMANDOS_ADM)
        else:
            self.COMANDOS.update(self.COMANDOS_EST)

        self.title("🎙  Comandos de voz")
        self.geometry("480x580")
        self.resizable(False, False)
        self.configure(fg_color=C("bg"))
        self.grab_set(); self.lift(); self.focus_force()
        self._check_libs()
        self._build()

    def _check_libs(self):
        try:
            import speech_recognition  # noqa
            self._libs_ok = True
        except ImportError:
            self._libs_ok = False

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=C("accent"), corner_radius=0, height=80)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="🎙  Comandos de Voz",
            font=("Helvetica", FS("h2"), "bold"), text_color="white").place(relx=.5, rely=.5, anchor="center")

        body = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                       scrollbar_button_color=C("accent"))
        body.pack(fill="both", expand=True, padx=20, pady=12)

        if not self._libs_ok:
            warn = ctk.CTkFrame(body, fg_color=C("surface"), corner_radius=14)
            warn.pack(fill="x", pady=(0, 14))
            ctk.CTkLabel(warn, text="⚠️  Biblioteca requerida no instalada",
                font=("Helvetica", FS("body"), "bold"), text_color=C("amber")).pack(pady=(18, 4))
            ctk.CTkLabel(warn,
                text="Para usar comandos de voz instala:\n\npip install SpeechRecognition pyaudio",
                font=("Helvetica", FS("body")), text_color=C("text"),
                justify="center").pack(padx=20, pady=(0, 18))

        # Indicador de rol
        rol_label = "👤 Modo: Administrativo" if self.rol == "Administrativo" else "👤 Modo: Estudiante"
        ctk.CTkLabel(body, text=rol_label,
            font=("Helvetica", FS("small"), "bold"), text_color=C("accent")).pack(anchor="w", pady=(0, 8))

        # Estado
        self.lbl_estado = ctk.CTkLabel(body,
            text="🔴  Listo para escuchar" if self._libs_ok else "🔴  Sin micrófono disponible",
            font=("Helvetica", FS("body"), "bold"), text_color=C("text"))
        self.lbl_estado.pack(pady=(0, 6))

        # Transcripción en tiempo real
        self.lbl_transcripcion = ctk.CTkLabel(body, text="",
            font=("Helvetica", FS("small")), text_color=C("text3"),
            wraplength=400, justify="center")
        self.lbl_transcripcion.pack(pady=(0, 6))

        self.btn_mic = Btn(body,
            text="🎙  Escuchar comando",
            width=220, height=52,
            fg_color=C("accent") if self._libs_ok else C("border"),
            command=self._escuchar if self._libs_ok else lambda: None)
        self.btn_mic.pack(pady=(0, 8))

        self.lbl_resultado = ctk.CTkLabel(body, text="",
            font=("Helvetica", FS("body")), text_color=C("text2"),
            wraplength=380, justify="center")
        self.lbl_resultado.pack(pady=(0, 12))

        ctk.CTkFrame(body, fg_color=C("border"), height=1).pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(body, text="📋  Comandos disponibles para tu perfil",
            font=("Helvetica", FS("body"), "bold"), text_color=C("text")).pack(anchor="w")

        for voz, (tab, desc) in self.COMANDOS.items():
            row = ctk.CTkFrame(body, fg_color=C("surface"), corner_radius=8)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=f"  «{voz}»",
                font=("Helvetica", FS("body"), "bold"), text_color=C("accent"),
                width=150, anchor="w").pack(side="left", padx=(8, 0), pady=8)
            ctk.CTkLabel(row, text=f"→  {desc}",
                font=("Helvetica", FS("small")), text_color=C("text2")).pack(side="left", padx=4)

        ctk.CTkFrame(body, fg_color="transparent", height=10).pack()
        BtnOutline(self, text="Cerrar", width=120, command=self.destroy).pack(pady=(0, 16))

    def _escuchar(self):
        if self._escuchando:
            return
        self._escuchando = True
        self.btn_mic.configure(fg_color=C("red"), text="⏹  Escuchando…")
        self.lbl_estado.configure(text="🟢  Escuchando… habla ahora", text_color=C("green"))
        self.lbl_resultado.configure(text="")
        self.lbl_transcripcion.configure(text="")
        self.update()
        import threading
        self._hilo_voz = threading.Thread(target=self._reconocer_hilo, daemon=True)
        self._hilo_voz.start()
        self._poll_estado()

    def _poll_estado(self):
        """Revisa cada 120 ms si el hilo de voz terminó (no bloquea la UI)."""
        if self._hilo_voz and self._hilo_voz.is_alive():
            self.after(120, self._poll_estado)

    def _actualizar_transcripcion(self, texto):
        """Llamado desde el hilo de voz para actualizar la UI de forma segura."""
        try:
            self.lbl_transcripcion.configure(text=f"✍️  {texto}")
            self.update_idletasks()
        except Exception:
            pass

    def _reconocer_hilo(self):
        """Corre en hilo separado; usa recognizer en modo streaming parcial."""
        try:
            import speech_recognition as sr
            rec = sr.Recognizer()
            rec.energy_threshold = 300
            rec.dynamic_energy_threshold = True
            rec.pause_threshold = 0.6   # pausa más corta = respuesta más ágil

            with sr.Microphone() as src:
                rec.adjust_for_ambient_noise(src, duration=0.3)
                # Actualizar UI mientras espera audio
                self.after(0, lambda: self.lbl_transcripcion.configure(text="🎤 Habla ahora…"))
                try:
                    audio = rec.listen(src, timeout=7, phrase_time_limit=6)
                except sr.WaitTimeoutError:
                    self.after(0, lambda: self._fin_reconocimiento("⏱  Sin respuesta. Intenta de nuevo.", C("amber"), None))
                    return

            # Intentar transcripción con Google (más rápida) — muestra resultado parcial
            self.after(0, lambda: self.lbl_transcripcion.configure(text="⏳ Procesando…"))
            try:
                texto = rec.recognize_google(audio, language="es-MX").lower()
            except sr.UnknownValueError:
                self.after(0, lambda: self._fin_reconocimiento("❓ No se entendió. Habla más claro.", C("amber"), None))
                return
            except sr.RequestError as e:
                self.after(0, lambda err=e: self._fin_reconocimiento(f"⚠  Sin conexión: {err}", C("red"), None))
                return

            # Mostrar transcripción completa con efecto de escritura carácter a carácter
            def _escribir_gradual(texto_completo, pos=0):
                try:
                    self.lbl_transcripcion.configure(text=f"✍️  {texto_completo[:pos+1]}")
                    if pos + 1 < len(texto_completo):
                        self.after(30, lambda: _escribir_gradual(texto_completo, pos + 1))
                except Exception:
                    pass
            self.after(0, lambda t=texto: _escribir_gradual(t))

            # Buscar comando más largo que coincida primero (evita falsos positivos)
            encontrado_tab = None
            mejor_clave = ""
            for clave, (tab, _) in self.COMANDOS.items():
                if clave in texto and len(clave) > len(mejor_clave):
                    encontrado_tab = tab
                    mejor_clave = clave

            if encontrado_tab:
                self.after(0, lambda t=encontrado_tab: self._fin_reconocimiento(
                    f"✅  Navegando a: {t}", C("green"), t))
            else:
                self.after(0, lambda: self._fin_reconocimiento(
                    "❓  Comando no reconocido. Intenta de nuevo.", C("amber"), None))

        except Exception as ex:
            self.after(0, lambda e=ex: self._fin_reconocimiento(f"⚠  {e}", C("red"), None))

    def _fin_reconocimiento(self, msg, color, tab):
        self._escuchando = False
        try:
            self.lbl_estado.configure(text=msg, text_color=color)
            self.btn_mic.configure(fg_color=C("accent"), text="🎙  Escuchar comando")
        except Exception:
            return
        if tab:
            self.after(700, lambda t=tab: (self.destroy(), self.on_cmd(t)))



# ─────────────────────────────────────────────────────────────────
#  PANEL: AJUSTES
# ─────────────────────────────────────────────────────────────────
class PanelAjustes(ctk.CTkScrollableFrame):
    def __init__(self, parent, app_ref, correo="", rol="Estudiante", **kw):
        super().__init__(parent, fg_color=C("bg"),
                         scrollbar_button_color=C("accent"), **kw)
        self.app_ref = app_ref
        self.correo  = correo
        self.rol     = rol
        self._build()

    def _sec(self, txt):
        ctk.CTkLabel(self, text=txt,
            font=("Helvetica",FS("small"),"bold"), text_color=C("text2")
            ).pack(padx=24, anchor="w", pady=(16,6))

    def _sep(self, parent):
        ctk.CTkFrame(parent, fg_color=C("border"), height=1).pack(fill="x", padx=16)

    def _row(self, parent, label):
        r = ctk.CTkFrame(parent, fg_color="transparent")
        r.pack(fill="x", padx=18, pady=12)
        ctk.CTkLabel(r, text=label, font=("Helvetica",FS("body"),"bold"),
                     text_color=C("text")).pack(side="left")
        return r

    def _build(self):
        ctk.CTkLabel(self, text="⚙️  Ajustes y Personalización",
            font=("Helvetica",FS("h2"),"bold"), text_color=C("text")
            ).pack(padx=28, pady=(24,4), anchor="w")
        ctk.CTkLabel(self, text="Personaliza tu experiencia en Optem",
            font=("Helvetica",FS("body")), text_color=C("text2")
            ).pack(padx=28, anchor="w", pady=(0,20))

        # ── Apariencia ───────────────────────────────────────────
        self._sec("🎨 Apariencia")
        ap = Card(self); ap.pack(fill="x", padx=24, pady=(0,14))

        # Modo oscuro
        r1 = self._row(ap, "🌙  Modo oscuro")
        self.sw_dark = ctk.CTkSwitch(r1, text="",
            progress_color=C("accent"), button_color=C("accent_dark"),
            command=self._toggle_dark)
        self.sw_dark.pack(side="right")
        if PREFS["dark_mode"]: self.sw_dark.select()

        self._sep(ap)

        # Colores de acento
        r2 = self._row(ap, "🎨  Color de acento")
        for col in ["#9B8DFF","#FF6B9D","#1ABC9C","#F39C12","#E74C3C","#3498DB","#2ECC71"]:
            border_w = 3 if col==PREFS["accent"] else 0
            ctk.CTkButton(r2, text="", width=28, height=28, corner_radius=14,
                fg_color=col, hover_color=_darken(col,.2),
                border_color="white", border_width=border_w,
                command=lambda c=col: self._set_accent(c)).pack(side="right", padx=2)

        self._sep(ap)

        # Tamaño de fuente
        r3 = self._row(ap, "🔤  Tamaño de fuente")
        self.opt_fs = ctk.CTkOptionMenu(r3, values=["Pequeño","Normal","Grande"],
            width=130, height=36, corner_radius=10,
            fg_color=C("surface2"), text_color=C("text"),
            button_color=C("accent"), button_hover_color=C("accent_dark"),
            command=self._set_font)
        self.opt_fs.set(PREFS["font_size"])
        self.opt_fs.pack(side="right")

        self._sep(ap)

        # Animaciones
        r4 = self._row(ap, "✨  Animaciones")
        self.sw_anim = ctk.CTkSwitch(r4, text="",
            progress_color=C("accent"), button_color=C("accent_dark"),
            command=self._toggle_anim)
        self.sw_anim.pack(side="right")
        if PREFS["anim"]: self.sw_anim.select()

        self._sep(ap)

        # Botones transparentes
        r5 = self._row(ap, "🔲  Botones transparentes en sidebar")
        self.sw_transp = ctk.CTkSwitch(r5, text="",
            progress_color=C("accent"), button_color=C("accent_dark"),
            command=self._toggle_transparent)
        self.sw_transp.pack(side="right")
        if PREFS.get("transparent_btns", False): self.sw_transp.select()

        # ── Notificaciones ───────────────────────────────────────
        self._sec("🔔 Notificaciones")
        notif = Card(self); notif.pack(fill="x", padx=24, pady=(0,14))
        self.var_notif = ctk.StringVar(value="Solo prioritario")
        for m in ["Apagado","Solo prioritario","Frecuente"]:
            rn = ctk.CTkFrame(notif, fg_color="transparent")
            rn.pack(fill="x", padx=18, pady=8)
            ctk.CTkLabel(rn, text=m, font=("Helvetica",FS("body")),
                text_color=C("text")).pack(side="left")
            ctk.CTkRadioButton(rn, text="", variable=self.var_notif, value=m,
                fg_color=C("accent"), hover_color=C("accent_dark")).pack(side="right")
        ctk.CTkFrame(notif, fg_color="transparent", height=6).pack()

        # ── Accesibilidad ────────────────────────────────────────
        self._sec("♿ Accesibilidad")
        acc = Card(self); acc.pack(fill="x", padx=24, pady=(0,14))

        # Navegación por teclado
        ra = self._row(acc, "⌨️  Navegación por teclado")
        ctk.CTkLabel(ra,
            text="Ctrl+1…6 cambian de pestaña · Tab navega entre elementos",
            font=("Helvetica", FS("small")), text_color=C("text3"),
            wraplength=260, justify="left").pack(side="right", padx=(0,8))
        self.sw_kb = ctk.CTkSwitch(ra, text="",
            progress_color=C("accent"), button_color=C("accent_dark"),
            command=self._toggle_keyboard_nav)
        self.sw_kb.pack(side="right")
        if PREFS.get("keyboard_nav", False): self.sw_kb.select()

        self._sep(acc)

        # Comandos de voz
        rv = self._row(acc, "🎙  Comandos de voz")
        ctk.CTkLabel(rv,
            text="Requiere: SpeechRecognition + PyAudio",
            font=("Helvetica", FS("small")), text_color=C("text3")).pack(side="right", padx=(0,8))
        self.sw_voz = ctk.CTkSwitch(rv, text="",
            progress_color=C("accent"), button_color=C("accent_dark"),
            command=self._toggle_voice_cmd)
        self.sw_voz.pack(side="right")
        if PREFS.get("voice_cmd", False): self.sw_voz.select()

        self._sep(acc)

        # Botón para abrir el diálogo de voz
        rv2 = ctk.CTkFrame(acc, fg_color="transparent")
        rv2.pack(fill="x", padx=18, pady=12)
        ctk.CTkLabel(rv2, text="Abrir panel de voz y ver comandos disponibles",
            font=("Helvetica", FS("small")), text_color=C("text2")).pack(side="left")
        Btn(rv2, text="🎙  Abrir voz", width=130, height=36,
            command=self._abrir_voz).pack(side="right")

        self._sep(acc)

        # Lector de pantalla (accesibilidad visual)
        rl = self._row(acc, "♿  Lector de pantalla")
        ctk.CTkLabel(rl,
            text="Flechas navegan recuadros · Enter activa · TTS lee en voz alta",
            font=("Helvetica", FS("small")), text_color=C("text3"),
            wraplength=250, justify="left").pack(side="right", padx=(0, 8))
        self.sw_lector = ctk.CTkSwitch(rl, text="",
            progress_color=C("accent"), button_color=C("accent_dark"),
            command=self._toggle_lector)
        self.sw_lector.pack(side="right")
        if PREFS.get("screen_reader", False): self.sw_lector.select()

        ctk.CTkFrame(acc, fg_color="transparent", height=4).pack()

        # ── Cuenta ───────────────────────────────────────────────
        self._sec("👤 Cuenta")
        cc = Card(self); cc.pack(fill="x", padx=24, pady=(0,14))

        rc = self._row(cc, f"📧  {self.correo or 'Sesión activa'}")
        ctk.CTkLabel(rc, text="Sesión activa ✅",
            font=("Helvetica",FS("small")), text_color=C("green")).pack(side="right")
        self._sep(cc)

        ctk.CTkButton(cc, text="🚪  Cerrar sesión",
            height=44, corner_radius=12,
            fg_color=C("red"), hover_color=_darken(C("red"),.15),
            text_color="white", font=("Helvetica",FS("body"),"bold"),
            command=self._cerrar_sesion).pack(padx=18, pady=14, fill="x")

        # ── Acerca de ────────────────────────────────────────────
        self._sec("ℹ️ Acerca de")
        info = Card(self); info.pack(fill="x", padx=24, pady=(0,28))
        for k,v in [("Versión","2.0"),("Universidad","UAEMéx"),
                    ("Módulos","7 módulos activos"),("Autor","Equipo Optem 2025")]:
            r = ctk.CTkFrame(info, fg_color="transparent")
            r.pack(fill="x", padx=18, pady=6)
            ctk.CTkLabel(r, text=k, font=("Helvetica",FS("small"),"bold"),
                text_color=C("text2")).pack(side="left")
            ctk.CTkLabel(r, text=v, font=("Helvetica",FS("body")),
                text_color=C("text")).pack(side="right")
        ctk.CTkFrame(info, fg_color="transparent", height=8).pack()

    def _toggle_dark(self):
        PREFS["dark_mode"] = not PREFS["dark_mode"]
        save_prefs(PREFS)
        ctk.set_appearance_mode("dark" if PREFS["dark_mode"] else "light")
        messagebox.showinfo("Modo oscuro cambiado",
            "✅ Cambio guardado.\nReinicia la app para ver todos los colores actualizados.")

    def _set_accent(self, col):
        PREFS["accent"] = col
        save_prefs(PREFS)
        # Actualizar sidebar en tiempo real
        try:
            vp = self.app_ref._screen
            if hasattr(vp, "sidebar"):
                vp.sidebar.update_accent()
        except Exception:
            pass
        messagebox.showinfo("Color de acento",
            f"✅ Color aplicado: {col}\nAlgunos elementos se actualizan al reiniciar.")

    def _set_font(self, val):
        PREFS["font_size"] = val
        save_prefs(PREFS)

    def _toggle_anim(self):
        PREFS["anim"] = not PREFS["anim"]
        save_prefs(PREFS)

    def _toggle_transparent(self):
        PREFS["transparent_btns"] = not PREFS.get("transparent_btns", False)
        save_prefs(PREFS)
        messagebox.showinfo("Botones transparentes",
            "✅ Cambio guardado.\nReinicia la app para aplicarlo.")

    def _toggle_lector(self):
        PREFS["screen_reader"] = not PREFS.get("screen_reader", False)
        save_prefs(PREFS)
        # Buscar la ventana raíz de forma robusta
        root = None
        try:
            # app_ref puede ser la AppWindow (ctk.CTk) directamente
            if isinstance(self.app_ref, ctk.CTk):
                root = self.app_ref
            else:
                root = self.app_ref
        except Exception:
            pass
        if root is None:
            try:
                w = self
                for _ in range(20):
                    if isinstance(w, ctk.CTk):
                        root = w; break
                    parent = getattr(w, 'master', None) or getattr(w, '_parent', None)
                    if parent is None: break
                    w = parent
            except Exception:
                pass
        if PREFS["screen_reader"]:
            # Verificar si hay TTS disponible antes de activar
            tts_ok = False
            try:
                import pyttsx3 as _p; _p.init(); tts_ok = True
            except Exception:
                pass
            if not tts_ok:
                import platform as _pl, subprocess as _sp
                if _pl.system() == "Darwin":
                    tts_ok = True  # macOS siempre tiene 'say'
                elif _pl.system() == "Windows":
                    try:
                        import win32com.client; tts_ok = True
                    except Exception:
                        pass
                else:
                    for cmd in ("espeak-ng", "espeak", "spd-say"):
                        try:
                            _sp.run([cmd, "--version"], capture_output=True, timeout=2)
                            tts_ok = True; break
                        except Exception:
                            pass
            try:
                LectorPantalla.activar(root)
                inst = LectorPantalla._instancia
                if inst:
                    # Primer anuncio inmediato
                    inst._hablar("Lector de pantalla activado. Usa las flechas para navegar.")
                    # Re-anunciar a intervalos por si el worker TTS no estaba listo
                    for delay in (800, 2000, 4000):
                        root.after(delay, lambda: inst._hablar(
                            "Lector de pantalla activado. Usa las flechas para navegar."))
                    root.after(500, lambda: inst._escanear(anunciar_activacion=False))
            except Exception as e:
                messagebox.showerror("Lector de pantalla", f"Error al activar:\n{e}")
                return
            if not tts_ok:
                messagebox.showinfo("Lector de pantalla",
                    "✅ Lector activado (navegación por flechas).\n\n"
                    "⚠️ No se detectó motor TTS para audio.\n"
                    "Instala uno para escuchar:\n"
                    "  • pip install pyttsx3\n"
                    "  • (Linux) sudo apt install espeak-ng\n"
                    "  • (Windows) pip install pywin32")
        else:
            try:
                LectorPantalla.desactivar(root)
            except Exception:
                pass

    def _toggle_keyboard_nav(self):
        PREFS["keyboard_nav"] = not PREFS.get("keyboard_nav", False)
        save_prefs(PREFS)
        estado = "activada" if PREFS["keyboard_nav"] else "desactivada"
        msg = (
            "✅ Navegación por teclado activada.\n\n"
            "Atajos:\n  Ctrl+1…6 → cambiar pestaña\n  Tab / Shift+Tab → navegar\n  Enter / Espacio → activar"
            if PREFS["keyboard_nav"] else
            "❌ Navegación por teclado desactivada."
        )
        messagebox.showinfo(f"Teclado {estado}", msg)

    def _toggle_voice_cmd(self):
        PREFS["voice_cmd"] = not PREFS.get("voice_cmd", False)
        save_prefs(PREFS)
        # Actualizar botón de micrófono en sidebar — buscar en toda la jerarquía
        try:
            w = self
            for _ in range(12):
                if hasattr(w, "sidebar"):
                    w.sidebar.refresh_mic_btn()
                    break
                if w.master is None:
                    break
                w = w.master
        except Exception:
            pass
        if PREFS["voice_cmd"]:
            messagebox.showinfo("Voz activada",
                "🎙 Comandos de voz activados.\n"
                "Aparecerá el botón 🎙 en el sidebar.\n\n"
                "Requiere: pip install SpeechRecognition pyaudio")
        else:
            messagebox.showinfo("Voz desactivada", "❌ Comandos de voz desactivados.")

    def _abrir_voz(self):
        try:
            # app_ref es la AppWindow; buscar el PantallaApp activo para acceder al sidebar
            app = self.app_ref
            screen = getattr(app, "_screen", None)
            on_cmd = screen.sidebar.set_active if (screen and hasattr(screen, "sidebar")) else lambda _: None
        except Exception:
            on_cmd = lambda _: None
        DialogoVozCmd(self, on_cmd, rol=getattr(self, "rol", "Estudiante"))

    def _cerrar_sesion(self):
        if messagebox.askyesno("Cerrar sesión",
            "¿Seguro que quieres cerrar sesión?\nDeberás iniciar sesión la próxima vez."):
            cerrar_sesion()
            self.app_ref.volver_a_login()

# ─────────────────────────────────────────────────────────────────
#  PANELES ADMINISTRATIVO
# ─────────────────────────────────────────────────────────────────
class PanelInicioAdmin(ctk.CTkScrollableFrame):
    def __init__(self, parent, datos, on_tab, **kw):
        super().__init__(parent, fg_color=C("bg"),
                         scrollbar_button_color=C("accent"), **kw)
        self.datos  = datos
        self.on_tab = on_tab
        self._build()

    def _build(self):
        # Hero
        hero = ctk.CTkFrame(self, fg_color=C("navy"), corner_radius=20, height=180)
        hero.pack(fill="x", padx=20, pady=(20,0))
        hero.pack_propagate(False)
        # Sin imagen de fondo en el hero admin — solo color sólido de la paleta
        ctk.CTkLabel(hero, text="Panel Administrativo · UAEMéx",
            font=("Helvetica",FS("h2"),"bold"), text_color="white").place(x=28,y=26)
        ctk.CTkLabel(hero, text=datetime.now().strftime("Hoy: %A %d de %B, %Y"),
            font=("Helvetica",FS("body")), text_color=C("text2")).place(x=28,y=62)
        ctk.CTkLabel(hero, text="Gestión académica centralizada",
            font=("Helvetica",FS("small")), text_color=C("text3")).place(x=28,y=90)
        # Reloj en vivo — esquina derecha del hero
        _now_adm = datetime.now()
        self._adm_clock = ctk.CTkLabel(hero, text=_now_adm.strftime("%H:%M"),
            font=("Helvetica", 36, "bold"), text_color="white")
        self._adm_clock.place(relx=1.0, rely=0.0, x=-18, y=16, anchor="ne")
        self._adm_clock_sub = ctk.CTkLabel(hero, text=_now_adm.strftime("%S s · %d/%m/%Y"),
            font=("Helvetica", 10), text_color=C("text2"))
        self._adm_clock_sub.place(relx=1.0, rely=0.0, x=-18, y=62, anchor="ne")
        self._tick_adm_clock()

        # Alerta
        alert = ctk.CTkFrame(self, fg_color=C("accent"), corner_radius=16)
        alert.pack(fill="x", padx=20, pady=16)
        ia = ctk.CTkFrame(alert, fg_color="transparent")
        ia.pack(fill="x", padx=18, pady=14)
        ctk.CTkLabel(ia,
            text="🔔  3 alumnos en riesgo de reprobar en Prog. Avanzada",
            font=("Helvetica",FS("body"),"bold"), text_color="white").pack(side="left")
        Btn(ia, text="Ver →", width=80, height=34,
            fg_color="white", text_color=C("accent"),
            command=lambda: self.on_tab("Reportes")).pack(side="right")

        # Stats
        sr = ctk.CTkFrame(self, fg_color="transparent")
        sr.pack(fill="x", padx=20, pady=(0,16))
        acts_g = cargar_global()
        for i,(ico,val,lbl,col) in enumerate([
            ("👥","124","Alumnos total",C("accent")),
            ("📊","87%","Promedio gral.",C("green")),
            ("⚠️","12","En riesgo",C("amber")),
            ("📋",str(len(acts_g)),"Tareas globales",C("teal")),
        ]):
            sr.columnconfigure(i, weight=1)
            c = Card(sr); c.grid(row=0,column=i,padx=6,sticky="ew")
            ctk.CTkLabel(c, text=ico, font=("Helvetica",26)).pack(pady=(16,4))
            ctk.CTkLabel(c, text=val, font=("Helvetica",FS("h2"),"bold"),
                text_color=col).pack()
            ctk.CTkLabel(c, text=lbl, font=("Helvetica",FS("small")),
                text_color=C("text2")).pack(pady=(2,16))

        # Últimas tareas + acciones rápidas
        r2 = ctk.CTkFrame(self, fg_color="transparent")
        r2.pack(fill="x", padx=20, pady=(0,20))
        r2.columnconfigure(0,weight=3); r2.columnconfigure(1,weight=2)

        left = Card(r2); left.grid(row=0,column=0,padx=(0,10),sticky="nsew")
        lh = ctk.CTkFrame(left, fg_color="transparent")
        lh.pack(fill="x", padx=16, pady=(14,6))
        ctk.CTkLabel(lh, text="📋  Últimas tareas publicadas",
            font=("Helvetica",FS("h3"),"bold"), text_color=C("text")).pack(side="left")
        Btn(lh, text="+ Nueva", width=100, height=34,
            command=lambda: self.on_tab("Tareas globales")).pack(side="right")

        acts = sorted(cargar_global(), key=lambda x: x.get("fecha",""), reverse=True)[:5]
        if acts:
            for a in acts:
                row = ctk.CTkFrame(left, fg_color=C("surface2"), corner_radius=10)
                row.pack(fill="x", padx=12, pady=3)
                ctk.CTkLabel(row, text=a.get("titulo","?"),
                    font=("Helvetica",FS("body"),"bold"),
                    text_color=C("text")).pack(side="left", padx=10, pady=8)
                ctk.CTkLabel(row, text=a.get("fecha",""),
                    font=("Helvetica",FS("small")),
                    text_color=C("text2")).pack(side="right", padx=10)
        else:
            ctk.CTkLabel(left,
                text="No hay tareas publicadas.\nUsa «Tareas globales» para crear.",
                font=("Helvetica",FS("body")), text_color=C("text2"),
                justify="center").pack(pady=30)
        ctk.CTkFrame(left, fg_color="transparent", height=10).pack()

        right = Card(r2); right.grid(row=0,column=1,sticky="nsew")
        ctk.CTkLabel(right, text="⚡  Acciones rápidas",
            font=("Helvetica",FS("h3"),"bold"), text_color=C("text")
            ).pack(padx=16, pady=(14,10), anchor="w")
        for txt,tab,col in [
            ("📋 Nueva tarea global","Tareas globales",C("accent")),
            ("📊 Ver reportes","Reportes",C("green")),
            ("👥 Gestión alumnos","Alumnos",C("amber")),
            ("📅 Ver horarios","Horarios",C("teal")),
        ]:
            ctk.CTkButton(right, text=txt, height=38, corner_radius=10,
                fg_color=col, hover_color=_darken(col,.15), text_color="white",
                font=("Helvetica",FS("body")),
                command=lambda t=tab: self.on_tab(t)).pack(fill="x",padx=14,pady=4)
        ctk.CTkFrame(right, fg_color="transparent", height=8).pack()

        # ── Sección: Materias y grupos que necesitan ayuda/regularización ──
        sec_mat = ctk.CTkFrame(self, fg_color="transparent")
        sec_mat.pack(fill="x", padx=20, pady=(0, 20))
        sec_mat.columnconfigure(0, weight=1)

        mat_card = Card(sec_mat)
        mat_card.grid(row=0, column=0, sticky="ew")
        mh = ctk.CTkFrame(mat_card, fg_color="transparent")
        mh.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(mh, text="⚠️  Materias y Grupos que Necesitan Ayuda / Regularización",
            font=("Helvetica", FS("h3"), "bold"), text_color=C("text")).pack(side="left")

        MATERIAS_RIESGO = [
            ("Prog. Avanzada",    "Grupo A — 7°",  "12 alumnos con promedio < 70%",  C("red")),
            ("Cálculo III",       "Grupo B — 5°",  "8 alumnos próximos a reprobar",   C("amber")),
            ("Física II",         "Grupo A — 4°",  "5 alumnos sin entregas recientes",C("amber")),
            ("Álgebra Superior",  "Grupo C — 3°",  "3 alumnos en rezago académico",   C("red")),
            ("Lab. Sistemas",     "Grupo A — 6°",  "Asistencia < 60% este mes",       C("amber")),
        ]
        mat_scroll = ctk.CTkScrollableFrame(mat_card, fg_color="transparent",
                                            height=180, scrollbar_button_color=C("accent"))
        mat_scroll.pack(fill="x", padx=12, pady=(0, 12))
        for mat, grupo, detalle, col in MATERIAS_RIESGO:
            row = ctk.CTkFrame(mat_scroll, fg_color=C("surface2"), corner_radius=10)
            row.pack(fill="x", pady=3)
            ctk.CTkFrame(row, fg_color=col, width=6, corner_radius=3).pack(
                side="left", fill="y", padx=(0, 10))
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, pady=8)
            ctk.CTkLabel(info, text=f"📚 {mat}  ·  {grupo}",
                font=("Helvetica", FS("body"), "bold"), text_color=C("text"),
                anchor="w").pack(anchor="w")
            ctk.CTkLabel(info, text=detalle,
                font=("Helvetica", FS("small")), text_color=C("text2"),
                anchor="w").pack(anchor="w")
            Btn(row, text="Ver →", width=70, height=30,
                fg_color=col, command=lambda: self.on_tab("Reportes")).pack(
                side="right", padx=12)

    def _tick_adm_clock(self):
        try:
            if not self.winfo_exists():
                return
            now = datetime.now()
            self._adm_clock.configure(text=now.strftime("%H:%M"))
            self._adm_clock_sub.configure(text=now.strftime("%S s  ·  %d/%m/%Y"))
            self.after(1000, self._tick_adm_clock)
        except Exception:
            pass


class PanelTareasGlobales(ctk.CTkFrame):
    def __init__(self, parent, **kw):
        super().__init__(parent, fg_color=C("bg"), **kw)
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=C("surface"), corner_radius=0, height=70)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ih = ctk.CTkFrame(hdr, fg_color="transparent")
        ih.pack(fill="both", expand=True, padx=24, pady=14)
        ctk.CTkLabel(ih, text="📋  Tareas Globales (visible a todos los alumnos)",
            font=("Helvetica",FS("h2"),"bold"), text_color=C("text")).pack(side="left")
        Btn(ih, text="＋  Publicar tarea", width=190, command=self._nueva).pack(side="right")

        self.lista = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                            scrollbar_button_color=C("accent"))
        self.lista.pack(fill="both", expand=True, padx=20, pady=12)
        self._refresh()

    def _refresh(self):
        for w in self.lista.winfo_children(): w.destroy()
        acts = sorted(cargar_global(), key=lambda x: x.get("fecha","9999"))
        if not acts:
            ctk.CTkLabel(self.lista,
                text="📋\n\nNo hay tareas globales publicadas.\nPresiona «＋ Publicar tarea» para crear una.",
                font=("Helvetica",FS("body")), text_color=C("text2"),
                justify="center").pack(pady=60)
            return
        for a in acts:
            card = Card(self.lista); card.pack(fill="x", pady=5)
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=14)
            ctk.CTkFrame(inner, fg_color=C("accent"), width=6,
                corner_radius=3).pack(side="left", fill="y", padx=(0,12))
            info = ctk.CTkFrame(inner, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(info, text=a.get("titulo","?"),
                font=("Helvetica",FS("body"),"bold"), text_color=C("text")).pack(anchor="w")
            ctk.CTkLabel(info,
                text=f"{a.get('categoria','')}  ·  📅 {a.get('fecha','?')}  ·  ⏰ {a.get('hora_inicio','?')}–{a.get('hora_fin','?')}",
                font=("Helvetica",FS("small")), text_color=C("text2")).pack(anchor="w",pady=(2,0))
            if a.get("desc"):
                ctk.CTkLabel(info, text=a["desc"][:100],
                    font=("Helvetica",FS("small")), text_color=C("text3")).pack(anchor="w")
            btns = ctk.CTkFrame(inner, fg_color="transparent")
            btns.pack(side="right")
            ctk.CTkButton(btns, text="✏️", width=36, height=36, corner_radius=10,
                fg_color=C("surface2"), text_color=C("text"),
                command=lambda ax=a: self._editar(ax)).pack(pady=2)
            ctk.CTkButton(btns, text="🗑", width=36, height=36, corner_radius=10,
                fg_color=C("surface2"), text_color=C("red"),
                command=lambda ax=a: self._eliminar(ax)).pack(pady=2)

    def _nueva(self):
        DialogoActividad(self, CATEGORIAS_GLOBAL, self._save)

    def _editar(self, a):
        orig = a.copy()
        def on_save(nueva):
            lista = [x for x in cargar_global() if x.get("id")!=orig.get("id")]
            lista.append(nueva)
            guardar_global(lista); self._refresh()
        DialogoActividad(self, CATEGORIAS_GLOBAL, on_save, actividad=a)

    def _eliminar(self, a):
        if messagebox.askyesno("Eliminar tarea",
            f"¿Eliminar «{a.get('titulo')}»?\nTodos los alumnos dejarán de verla."):
            lista = [x for x in cargar_global() if x.get("id")!=a.get("id")]
            guardar_global(lista); self._refresh()

    def _save(self, nueva):
        lista = cargar_global()
        lista.append(nueva)
        guardar_global(lista); self._refresh()


class PanelReportes(ctk.CTkScrollableFrame):
    def __init__(self, parent, **kw):
        super().__init__(parent, fg_color=C("bg"),
                         scrollbar_button_color=C("accent"), **kw)
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="📊  Reportes Académicos",
            font=("Helvetica",FS("h2"),"bold"), text_color=C("text")
            ).pack(padx=24, pady=(24,4), anchor="w")
        ctk.CTkLabel(self, text="Estadísticas de desempeño por materia",
            font=("Helvetica",FS("body")), text_color=C("text2")
            ).pack(padx=24, anchor="w", pady=(0,20))

        # ── ValidatorEngine: verificar integridad de tareas globales ──
        try:
            ve = ValidatorEngine()
            tareas_globales = cargar_global()
            if tareas_globales:
                ctk.CTkLabel(self,
                    text=f"🗂  Tareas globales activas: {len(tareas_globales)}  ·  Motor de validación activo ✅",
                    font=("Helvetica",FS("small")), text_color=C("green")
                ).pack(padx=24, anchor="w", pady=(0,12))
        except Exception:
            pass
        # ──────────────────────────────────────────────────────────────

        for mat,prom,alumnos,riesgo in [
            ("Cálculo III",    92,28, 2),
            ("Física II",      78,30, 8),
            ("Prog. Avanzada", 71,26,12),
            ("Álgebra",        85,24, 4),
            ("Lab. Sistemas",  89,22, 1),
        ]:
            card = Card(self); card.pack(fill="x", padx=24, pady=6)
            h = ctk.CTkFrame(card, fg_color="transparent")
            h.pack(fill="x", padx=16, pady=(14,6))
            ctk.CTkLabel(h, text=mat, font=("Helvetica",FS("h3"),"bold"),
                text_color=C("text")).pack(side="left")
            pc = C("green") if prom>=80 else C("amber") if prom>=70 else C("red")
            ctk.CTkLabel(h, text=f"Prom. {prom}",
                font=("Helvetica",FS("h3"),"bold"), text_color=pc).pack(side="right")
            bg_b = ctk.CTkFrame(card, fg_color=C("border"), corner_radius=4, height=10)
            bg_b.pack(fill="x", padx=16, pady=(0,8))
            fill_b = ctk.CTkFrame(bg_b, fg_color=pc, corner_radius=4, height=10)
            fill_b.place(relx=0,rely=0,relwidth=prom/100,relheight=1)
            ir = ctk.CTkFrame(card, fg_color="transparent")
            ir.pack(fill="x", padx=16, pady=(0,14))
            ctk.CTkLabel(ir, text=f"👥 {alumnos} alumnos",
                font=("Helvetica",FS("small")), text_color=C("text2")).pack(side="left")
            ctk.CTkLabel(ir, text=f"⚠️ {riesgo} en riesgo",
                font=("Helvetica",FS("small")), text_color=C("amber")).pack(side="left",padx=16)
            ctk.CTkLabel(ir, text=f"✅ {alumnos-riesgo} regulares",
                font=("Helvetica",FS("small")), text_color=C("green")).pack(side="left")


class PanelAlumnos(ctk.CTkFrame):
    _ALUMNOS = [
        ("Ana García López",        "ana.garcia@alumno.uaemex.mx",      "7°","91%","22🔥"),
        ("Luis Martínez Ruiz",      "luis.martinez@alumno.uaemex.mx",   "5°","78%","8🔥"),
        ("Sofía Hernández Cruz",    "sofia.hernandez@alumno.uaemex.mx", "4°","95%","31🔥"),
        ("Carlos Ramírez Vega",     "carlos.ramirez@alumno.uaemex.mx",  "6°","72%","5🔥"),
        ("María López Sánchez",     "maria.lopez@alumno.uaemex.mx",     "3°","88%","14🔥"),
        ("Pedro Torres Jiménez",    "pedro.torres@alumno.uaemex.mx",    "1°","61%","2🔥"),
        ("Valeria Flores Morales",  "valeria.flores@alumno.uaemex.mx",  "8°","93%","45🔥"),
        ("Diego Vargas Castillo",   "diego.vargas@alumno.uaemex.mx",    "2°","69%","0🔥"),
        ("Fernanda Reyes Ortiz",    "fernanda.reyes@alumno.uaemex.mx",  "5°","82%","11🔥"),
        ("Andrés Moreno Guzmán",    "andres.moreno@alumno.uaemex.mx",   "7°","76%","7🔥"),
        ("Camila Jiménez Peña",     "camila.jimenez@alumno.uaemex.mx",  "4°","90%","19🔥"),
        ("Roberto Silva Mendoza",   "roberto.silva@alumno.uaemex.mx",   "6°","65%","3🔥"),
        ("Daniela Ríos Aguilar",    "daniela.rios@alumno.uaemex.mx",    "3°","87%","16🔥"),
        ("Miguel Ángel Núñez",      "miguel.nunez@alumno.uaemex.mx",    "1°","54%","0🔥"),
        ("Isabella Campos León",    "isabella.campos@alumno.uaemex.mx", "8°","97%","60🔥"),
        ("Emilio Rojas Espinoza",   "emilio.rojas@alumno.uaemex.mx",    "2°","73%","6🔥"),
        ("Natalia Serrano Vidal",   "natalia.serrano@alumno.uaemex.mx", "5°","84%","12🔥"),
        ("Alejandro Cruz Medina",   "alejandro.cruz@alumno.uaemex.mx",  "7°","79%","9🔥"),
        ("Paola Guerrero Ávila",    "paola.guerrero@alumno.uaemex.mx",  "4°","92%","25🔥"),
        ("Eduardo Mendez Rubio",    "eduardo.mendez@alumno.uaemex.mx",  "6°","68%","4🔥"),
        ("Lucía Pacheco Soto",      "lucia.pacheco@alumno.uaemex.mx",   "3°","86%","17🔥"),
        ("Ricardo Salinas Bravo",   "ricardo.salinas@alumno.uaemex.mx", "1°","58%","1🔥"),
        ("Mariana Delgado Rivas",   "mariana.delgado@alumno.uaemex.mx", "8°","94%","38🔥"),
        ("Sebastián Vega Montes",   "sebastian.vega@alumno.uaemex.mx",  "2°","70%","5🔥"),
        ("Ariana Blanco Fuentes",   "ariana.blanco@alumno.uaemex.mx",   "5°","81%","10🔥"),
        ("Iván Herrera Castañeda",  "ivan.herrera@alumno.uaemex.mx",    "7°","75%","8🔥"),
        ("Ximena Lara Ponce",       "ximena.lara@alumno.uaemex.mx",     "4°","89%","20🔥"),
        ("Gerardo Molina Acosta",   "gerardo.molina@alumno.uaemex.mx",  "6°","63%","2🔥"),
        ("Vanessa Romero Téllez",   "vanessa.romero@alumno.uaemex.mx",  "3°","85%","15🔥"),
        ("Jorge Espinosa Olvera",   "jorge.espinosa@alumno.uaemex.mx",  "1°","62%","3🔥"),
        ("Brenda Navarro Quiroz",   "brenda.navarro@alumno.uaemex.mx",  "8°","96%","52🔥"),
        ("Oscar Ramos Becerra",     "oscar.ramos@alumno.uaemex.mx",     "2°","67%","0🔥"),
        ("Stephanie Peña Villanueva","stephanie.pena@alumno.uaemex.mx", "5°","83%","13🔥"),
        ("Armando Fuentes Trejo",   "armando.fuentes@alumno.uaemex.mx", "7°","77%","6🔥"),
        ("Gabriela Cortes Ibarra",  "gabriela.cortes@alumno.uaemex.mx", "4°","91%","21🔥"),
        ("Humberto Díaz Cervantes", "humberto.diaz@alumno.uaemex.mx",   "6°","66%","4🔥"),
        ("Renata Ángeles Meza",     "renata.angeles@alumno.uaemex.mx",  "3°","88%","18🔥"),
        ("Ulises Contreras Prado",  "ulises.contreras@alumno.uaemex.mx","1°","57%","1🔥"),
        ("Patricia Villafuerte",    "patricia.villafuerte@alumno.uaemex.mx","8°","93%","40🔥"),
        ("Héctor Zamora Osorio",    "hector.zamora@alumno.uaemex.mx",   "2°","71%","5🔥"),
        ("Alexa Cervantes Portillo","alexa.cervantes@alumno.uaemex.mx", "5°","80%","9🔥"),
        ("Joel Sandoval Miranda",   "joel.sandoval@alumno.uaemex.mx",   "7°","74%","7🔥"),
        ("Carmen Huerta Alvarado",  "carmen.huerta@alumno.uaemex.mx",   "4°","87%","16🔥"),
        ("Rodrigo Barrera Méndez",  "rodrigo.barrera@alumno.uaemex.mx", "6°","64%","2🔥"),
        ("Diana Sosa Camacho",      "diana.sosa@alumno.uaemex.mx",      "3°","86%","14🔥"),
        ("Marco Infante Valdés",    "marco.infante@alumno.uaemex.mx",   "1°","60%","0🔥"),
        ("Alicia Monroy Bautista",  "alicia.monroy@alumno.uaemex.mx",   "8°","95%","47🔥"),
        ("Enrique Cisneros Tapia",  "enrique.cisneros@alumno.uaemex.mx","2°","69%","4🔥"),
        ("Karla Ojeda Espinoza",    "karla.ojeda@alumno.uaemex.mx",     "5°","82%","11🔥"),
        ("Omar Zúñiga Pedraza",     "omar.zuniga@alumno.uaemex.mx",     "7°","76%","8🔥"),
        ("Itzel Vergara Solano",    "itzel.vergara@alumno.uaemex.mx",   "4°","90%","23🔥"),
        ("Saúl Domínguez Loza",     "saul.dominguez@alumno.uaemex.mx",  "6°","67%","3🔥"),
    ]

    def __init__(self, parent, **kw):
        super().__init__(parent, fg_color=C("bg"), **kw)
        self._ac_visible = False
        self._ac_idx     = -1   # índice del ítem resaltado en el dropdown
        self._ac_matches = []   # coincidencias actuales
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=C("surface"), corner_radius=0, height=70)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ih = ctk.CTkFrame(hdr, fg_color="transparent")
        ih.pack(fill="both", expand=True, padx=24, pady=14)
        ctk.CTkLabel(ih, text="👥  Gestión de Alumnos",
            font=("Helvetica",FS("h2"),"bold"), text_color=C("text")).pack(side="left")
        Btn(ih, text="Buscar", width=90, height=38,
            command=self._buscar).pack(side="right")
        self.e_busq = ctk.CTkEntry(ih, placeholder_text="🔍 Buscar alumno...",
            height=38, width=240, corner_radius=10,
            font=("Helvetica",FS("body")),
            fg_color=C("surface2"), text_color=C("text"), border_color=C("border"))
        self.e_busq.pack(side="right", padx=(8,6))
        self.e_busq.bind("<KeyRelease>", self._on_key_search)
        self.e_busq.bind("<FocusOut>", lambda e: self.after(150, self._hide_ac))
        self.e_busq.bind("<Down>",   lambda e: self._ac_mover(1))
        self.e_busq.bind("<Up>",     lambda e: self._ac_mover(-1))
        self.e_busq.bind("<Return>", lambda e: self._ac_confirmar())

        # ── Dropdown de autocompletado ──────────────────────────────
        # Se crea pero se coloca encima con place al momento de mostrar
        self._ac_frame = ctk.CTkFrame(self, fg_color=C("surface"),
            corner_radius=10, border_width=1, border_color=C("border"))

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                             scrollbar_button_color=C("accent"))
        self.scroll.pack(fill="both", expand=True, padx=20, pady=12)
        self._mostrar("")
        # Colocar ac_frame sobre el resto usando place (no pack)
        # Se posicionará justo debajo del header al mostrarse

    def _on_key_search(self, event):
        # Flechas y Enter se manejan por separado
        if event.keysym in ("Down", "Up", "Return", "Escape"):
            if event.keysym == "Escape":
                self._hide_ac()
            return
        q = self.e_busq.get().strip().lower()
        if not q:
            self._hide_ac(); return
        matches = [a for a in self._ALUMNOS
                   if q in a[0].lower() or q in a[1].lower()]
        if not matches:
            self._hide_ac(); return
        self._ac_matches = [a[0] for a in matches[:8]]
        self._ac_idx = -1
        self._render_ac_dropdown()

    def _render_ac_dropdown(self):
        """Dibuja el dropdown resaltando el ítem en self._ac_idx."""
        for w in self._ac_frame.winfo_children(): w.destroy()
        ctk.CTkLabel(self._ac_frame, text="Sugerencias",
            font=("Helvetica", FS("small"), "bold"),
            text_color=C("text2")).pack(anchor="w", padx=12, pady=(8,2))
        for i, nom in enumerate(self._ac_matches):
            datos = next((a for a in self._ALUMNOS if a[0]==nom), None)
            correo = datos[1] if datos else ""
            sem    = datos[2] if datos else ""
            es_sel = (i == self._ac_idx)
            row = ctk.CTkFrame(self._ac_frame,
                fg_color=C("accent_bg") if es_sel else "transparent",
                cursor="hand2", corner_radius=6)
            row.pack(fill="x", padx=8, pady=2)
            row.bind("<Enter>", lambda e, r=row: r.configure(fg_color=C("surface2")))
            row.bind("<Leave>", lambda e, r=row, idx=i: r.configure(
                fg_color=C("accent_bg") if idx==self._ac_idx else "transparent"))
            av = make_avatar(nom[:2].upper(), 28)
            lbl_av = ctk.CTkLabel(row, image=av, text="")
            lbl_av.pack(side="left", padx=(8,6), pady=4)
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(info, text=nom,
                font=("Helvetica", FS("body"), "bold"),
                text_color=C("text"), anchor="w").pack(anchor="w")
            ctk.CTkLabel(info, text=f"{correo} · {sem} sem.",
                font=("Helvetica", FS("small")),
                text_color=C("text2"), anchor="w").pack(anchor="w")
            for w in (row, lbl_av, info):
                w.bind("<Button-1>", lambda e, n=nom: self._select_ac(n))
            for child in info.winfo_children():
                child.bind("<Button-1>", lambda e, n=nom: self._select_ac(n))
        ctk.CTkFrame(self._ac_frame, fg_color="transparent", height=6).pack()
        n = len(self._ac_matches)
        h = min(300, 52 + n * 54)
        if not self._ac_visible:
            self._ac_frame.place(x=20, y=76, relwidth=1.0, width=-40, height=h)
            self._ac_frame.lift()
            self._ac_visible = True
        else:
            self._ac_frame.configure(height=h)

    def _ac_mover(self, delta):
        """↓↑ mueven la selección en el dropdown."""
        if not self._ac_visible or not self._ac_matches:
            return "break"
        n = len(self._ac_matches)
        self._ac_idx = (self._ac_idx + delta) % n
        self._render_ac_dropdown()
        return "break"

    def _ac_confirmar(self):
        """Enter confirma la selección resaltada."""
        if self._ac_visible and 0 <= self._ac_idx < len(self._ac_matches):
            self._select_ac(self._ac_matches[self._ac_idx])
        elif self._ac_visible and self._ac_matches:
            self._select_ac(self._ac_matches[0])
        else:
            self._buscar()
        return "break"

    def _select_ac(self, nombre):
        self.e_busq.delete(0, "end")
        self.e_busq.insert(0, nombre)
        self._hide_ac()
        self._buscar()

    def _hide_ac(self):
        if self._ac_visible:
            self._ac_frame.place_forget()
            self._ac_visible = False

    def _buscar(self):
        self._hide_ac()
        self._mostrar(self.e_busq.get().strip().lower())

    def _mostrar(self, q):
        for w in self.scroll.winfo_children(): w.destroy()
        filtrados = [a for a in self._ALUMNOS
                     if not q or q in a[0].lower() or q in a[1].lower()]
        for nom,correo,sem,prom,racha in filtrados:
            card = Card(self.scroll); card.pack(fill="x", pady=5)
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=14)
            av = make_avatar(nom[:2].upper(), 44)
            ctk.CTkLabel(inner, image=av, text="").pack(side="left", padx=(0,12))
            info = ctk.CTkFrame(inner, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(info, text=nom,
                font=("Helvetica",FS("body"),"bold"), text_color=C("text")).pack(anchor="w")
            ctk.CTkLabel(info, text=f"{correo}  ·  {sem} semestre",
                font=("Helvetica",FS("small")), text_color=C("text2")).pack(anchor="w")
            # Estado de regularización
            p = float(prom.replace("%",""))
            if p < 70:
                ctk.CTkLabel(info, text="🔴  Necesita regularización",
                    font=("Helvetica",FS("small"),"bold"), text_color=C("red")).pack(anchor="w", pady=(2,0))
            elif p < 80:
                ctk.CTkLabel(info, text="🟡  En seguimiento",
                    font=("Helvetica",FS("small"),"bold"), text_color=C("amber")).pack(anchor="w", pady=(2,0))
            right = ctk.CTkFrame(inner, fg_color="transparent")
            right.pack(side="right")
            pc = C("green") if p>=80 else C("amber") if p>=70 else C("red")
            ctk.CTkLabel(right, text=prom,
                font=("Helvetica",FS("h3"),"bold"), text_color=pc).pack()
            ctk.CTkLabel(right, text=racha,
                font=("Helvetica",FS("small")), text_color=C("amber")).pack()
            Btn(right, text="Ver detalle", width=100, height=32,
                command=lambda n=nom, c=correo, s=sem, pr=prom, r=racha: self._ver_alumno(n,c,s,pr,r)
                ).pack(pady=(4,0))

    def _ver_alumno(self, nom, correo, sem, prom, racha):
        """Diálogo de detalle por alumno con materias y estado de regularización."""
        top = ctk.CTkToplevel(self)
        top.title(f"Detalle alumno — {nom}")
        top.geometry("540x540")
        top.configure(fg_color=C("bg"))
        top.grab_set(); top.lift(); top.focus_force()

        # Encabezado
        hdr = ctk.CTkFrame(top, fg_color=C("accent"), corner_radius=0, height=90)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        av = make_avatar(nom[:2].upper(), 54)
        ctk.CTkLabel(hdr, image=av, text="").place(x=20, rely=0.5, anchor="w")
        ctk.CTkLabel(hdr, text=nom,
            font=("Helvetica",FS("h3"),"bold"), text_color="white").place(x=90, y=18)
        ctk.CTkLabel(hdr, text=f"{correo}  ·  {sem} semestre",
            font=("Helvetica",FS("small")), text_color="#EEEEFF").place(x=90, y=48)

        scr = ctk.CTkScrollableFrame(top, fg_color="transparent",
                                     scrollbar_button_color=C("accent"))
        scr.pack(fill="both", expand=True, padx=16, pady=12)

        # Stats rápidos
        sr = ctk.CTkFrame(scr, fg_color="transparent")
        sr.pack(fill="x", pady=(0,12))
        p = float(prom.replace("%",""))
        pc = C("green") if p>=80 else C("amber") if p>=70 else C("red")
        for i,(ico,val,lbl,col) in enumerate([
            ("📊", prom, "Promedio general", pc),
            ("🔥", racha, "Racha actual", C("amber")),
            ("🎓", sem, "Semestre", C("accent")),
        ]):
            sr.columnconfigure(i, weight=1)
            c = Card(sr); c.grid(row=0, column=i, padx=4, sticky="ew")
            ctk.CTkLabel(c, text=ico, font=("Helvetica",22)).pack(pady=(10,2))
            ctk.CTkLabel(c, text=val, font=("Helvetica",FS("h3"),"bold"),
                text_color=col).pack()
            ctk.CTkLabel(c, text=lbl, font=("Helvetica",FS("small")),
                text_color=C("text2")).pack(pady=(0,10))

        # Materias y estado
        ctk.CTkLabel(scr, text="📚  Materias y estado de regularización",
            font=("Helvetica",FS("body"),"bold"), text_color=C("text"),
            anchor="w").pack(anchor="w", pady=(4,6))

        MATERIAS_ALUMNO = [
            ("Cálculo III",      "85%",  "Al corriente",        C("green")),
            ("Prog. Avanzada",   "63%",  "Necesita ayuda",      C("red")),
            ("Física II",        "71%",  "En seguimiento",      C("amber")),
            ("Álgebra Superior", "90%",  "Al corriente",        C("green")),
            ("Lab. Sistemas",    "55%",  "Requiere regularización", C("red")),
        ]
        for mat, mp, estado, col in MATERIAS_ALUMNO:
            row = ctk.CTkFrame(scr, fg_color=C("surface2"), corner_radius=10)
            row.pack(fill="x", pady=3)
            ctk.CTkFrame(row, fg_color=col, width=6, corner_radius=3).pack(
                side="left", fill="y")
            ctk.CTkLabel(row, text=mat,
                font=("Helvetica",FS("body"),"bold"), text_color=C("text"),
                width=180, anchor="w").pack(side="left", padx=10, pady=8)
            ctk.CTkLabel(row, text=mp,
                font=("Helvetica",FS("body"),"bold"), text_color=col).pack(side="left", padx=8)
            ctk.CTkLabel(row, text=estado,
                font=("Helvetica",FS("small")), text_color=C("text2")).pack(side="left")

        Btn(top, text="Cerrar", width=120, command=top.destroy).pack(pady=(8,16))


class PanelClasesAdmin(ctk.CTkFrame):
    """Panel CRUD de clases para el administrador."""
    COLORES_DISP = [C("accent"), C("amber"), C("green"), C("teal"), C("red"), "#9B8DFF", "#E91E8C", "#00BCD4"]
    DIAS_SEM = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado"]
    HORAS_DISP = ["07:00","08:00","09:00","10:00","11:00","12:00",
                  "13:00","14:00","15:00","16:00","17:00","18:00","19:00","20:00"]

    def __init__(self, parent, **kw):
        super().__init__(parent, fg_color=C("bg"), **kw)
        # Clases guardadas: lista de dicts con claves: id, materia, grupo, dia, hora_ini, hora_fin, color, desc
        self._clases = [
            {"id":1,"materia":"Cálculo III",    "grupo":"Grupo A","dia":"Lunes",    "hora_ini":"09:00","hora_fin":"11:00","color":C("accent"),  "desc":"Integrales dobles y triples"},
            {"id":2,"materia":"Prog. Avanzada",  "grupo":"Grupo B","dia":"Lunes",    "hora_ini":"14:00","hora_fin":"16:00","color":C("amber"),   "desc":"Patrones de diseño"},
            {"id":3,"materia":"Álgebra",          "grupo":"Grupo C","dia":"Martes",   "hora_ini":"10:00","hora_fin":"12:00","color":C("teal"),    "desc":"Espacios vectoriales"},
            {"id":4,"materia":"Física II",        "grupo":"Grupo A","dia":"Martes",   "hora_ini":"14:00","hora_fin":"16:00","color":C("green"),   "desc":"Electromagnetismo"},
            {"id":5,"materia":"Lab. Sistemas",    "grupo":"Grupo B","dia":"Miércoles","hora_ini":"13:00","hora_fin":"15:00","color":C("red"),     "desc":"Práctica de redes"},
        ]
        self._next_id = 10
        self._filtro  = ""
        self._build()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=C("surface"), corner_radius=0, height=70)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ih = ctk.CTkFrame(hdr, fg_color="transparent")
        ih.pack(fill="both", expand=True, padx=24, pady=14)
        ctk.CTkLabel(ih, text="🏫  Gestión de Clases",
            font=("Helvetica",FS("h2"),"bold"), text_color=C("text")).pack(side="left")
        Btn(ih, text="＋  Nueva clase", width=150, height=38,
            command=self._nueva).pack(side="right")

        # Barra de búsqueda
        sb = ctk.CTkFrame(self, fg_color="transparent")
        sb.pack(fill="x", padx=24, pady=(10,0))
        self.e_filtro = ctk.CTkEntry(sb, placeholder_text="🔍 Buscar materia o grupo...",
            height=36, corner_radius=10,
            font=("Helvetica",FS("body")), fg_color=C("surface2"),
            text_color=C("text"), border_color=C("border"))
        self.e_filtro.pack(side="left", fill="x", expand=True, padx=(0,8))
        self.e_filtro.bind("<KeyRelease>", lambda e: self._render_lista())
        Btn(sb, text="Buscar", width=80, height=36, command=self._render_lista).pack(side="left")

        # Contador
        self.lbl_count = ctk.CTkLabel(self, text="",
            font=("Helvetica",FS("small")), text_color=C("text2"))
        self.lbl_count.pack(anchor="w", padx=24, pady=(6,0))

        # Lista scrollable
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                              scrollbar_button_color=C("accent"))
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)
        self._render_lista()

    def _render_lista(self):
        for w in self.scroll.winfo_children(): w.destroy()
        q = self.e_filtro.get().strip().lower()
        filtradas = [c for c in self._clases
                     if not q or q in c["materia"].lower() or q in c["grupo"].lower() or q in c["dia"].lower()]
        self.lbl_count.configure(text=f"{len(filtradas)} clase(s) registrada(s)")

        if not filtradas:
            ctk.CTkLabel(self.scroll, text="Sin clases que coincidan con la búsqueda.",
                font=("Helvetica",FS("body")), text_color=C("text3")).pack(pady=40)
            return

        # Cabecera
        hdr = ctk.CTkFrame(self.scroll, fg_color=C("surface2"), corner_radius=8, height=36)
        hdr.pack(fill="x", pady=(0,4)); hdr.pack_propagate(False)
        for txt, w in [("Materia",200),("Grupo",100),("Día",100),("Horario",120),("Acciones",110)]:
            ctk.CTkLabel(hdr, text=txt, width=w,
                font=("Helvetica",FS("small"),"bold"), text_color=C("text2")).pack(side="left", padx=8)

        for cl in filtradas:
            card = ctk.CTkFrame(self.scroll, fg_color=C("surface"), corner_radius=10)
            card.pack(fill="x", pady=3)
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=4, pady=8)
            # Color strip
            ctk.CTkFrame(inner, fg_color=cl["color"], width=5, corner_radius=3).pack(side="left", fill="y", padx=(4,8))
            # Materia
            ctk.CTkLabel(inner, text=cl["materia"], width=195,
                font=("Helvetica",FS("body"),"bold"), text_color=C("text"), anchor="w").pack(side="left")
            # Grupo
            ctk.CTkLabel(inner, text=cl["grupo"], width=95,
                font=("Helvetica",FS("small")), text_color=C("text2"), anchor="w").pack(side="left")
            # Día
            ctk.CTkLabel(inner, text=cl["dia"], width=95,
                font=("Helvetica",FS("small")), text_color=C("text2"), anchor="w").pack(side="left")
            # Horario
            ctk.CTkLabel(inner, text=f"{cl['hora_ini']}–{cl['hora_fin']}", width=115,
                font=("Helvetica",FS("small")), text_color=C("text2"), anchor="w").pack(side="left")
            # Acciones
            btn_fr = ctk.CTkFrame(inner, fg_color="transparent")
            btn_fr.pack(side="right", padx=8)
            Btn(btn_fr, text="✏️", width=36, height=32,
                command=lambda c=cl: self._editar(c)).pack(side="left", padx=2)
            ctk.CTkButton(btn_fr, text="🗑️", width=36, height=32, corner_radius=8,
                fg_color=C("surface2"), text_color=C("red"), hover_color=C("surface"),
                command=lambda c=cl: self._eliminar(c)).pack(side="left", padx=2)
            Btn(btn_fr, text="👁", width=36, height=32,
                command=lambda c=cl: self._detalle(c)).pack(side="left", padx=2)

    def _nueva(self):
        self._dialogo(None)

    def _editar(self, cl):
        self._dialogo(cl)

    def _eliminar(self, cl):
        if messagebox.askyesno("Eliminar clase",
                f"¿Eliminar la clase «{cl['materia']}» ({cl['grupo']})?"):
            self._clases = [c for c in self._clases if c["id"] != cl["id"]]
            self._render_lista()

    def _detalle(self, cl):
        top = ctk.CTkToplevel(self)
        top.title(f"Detalle — {cl['materia']}")
        top.geometry("400x340")
        top.configure(fg_color=C("bg"))
        top.grab_set(); top.lift(); top.focus_force()

        hdr = ctk.CTkFrame(top, fg_color=cl["color"], corner_radius=0, height=70)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=f"🏫  {cl['materia']}",
            font=("Helvetica",FS("h2"),"bold"), text_color="white").place(x=20, rely=0.5, anchor="w")

        body = ctk.CTkScrollableFrame(top, fg_color="transparent",
                                       scrollbar_button_color=C("accent"))
        body.pack(fill="both", expand=True, padx=20, pady=12)
        for k, v in [("Grupo", cl["grupo"]), ("Día", cl["dia"]),
                     ("Horario", f"{cl['hora_ini']} – {cl['hora_fin']}"),
                     ("Descripción", cl.get("desc","—"))]:
            row = ctk.CTkFrame(body, fg_color=C("surface2"), corner_radius=8)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=k, font=("Helvetica",FS("small"),"bold"),
                text_color=C("text2"), width=110, anchor="w").pack(side="left", padx=12, pady=8)
            ctk.CTkLabel(row, text=str(v), font=("Helvetica",FS("body")),
                text_color=C("text"), anchor="w", wraplength=220, justify="left").pack(side="left", padx=8)
        Btn(top, text="Cerrar", width=100, command=top.destroy).pack(pady=(4,16))

    def _dialogo(self, cl):
        es_nueva = cl is None
        top = ctk.CTkToplevel(self)
        top.title("Nueva clase" if es_nueva else "Editar clase")
        top.geometry("440x520")
        top.configure(fg_color=C("bg"))
        top.grab_set(); top.lift(); top.focus_force()

        ctk.CTkLabel(top, text="➕ Nueva clase" if es_nueva else "✏️ Editar clase",
            font=("Helvetica",FS("h2"),"bold"), text_color=C("text")).pack(padx=24, pady=(20,12), anchor="w")

        form = ctk.CTkFrame(top, fg_color="transparent")
        form.pack(fill="x", padx=24)

        def _lbl(txt):
            ctk.CTkLabel(form, text=txt, font=("Helvetica",FS("small"),"bold"),
                text_color=C("text2"), anchor="w").pack(fill="x")

        def _entry(ph, val=""):
            e = ctk.CTkEntry(form, height=40, corner_radius=10, placeholder_text=ph,
                font=("Helvetica",FS("body")), fg_color=C("surface2"),
                text_color=C("text"), border_color=C("border"))
            e.pack(fill="x", pady=(4,10))
            if val: e.insert(0, val)
            return e

        _lbl("Materia")
        e_mat = _entry("Ej: Cálculo III", cl["materia"] if cl else "")
        _lbl("Grupo")
        e_grp = _entry("Ej: Grupo A", cl["grupo"] if cl else "")
        _lbl("Descripción")
        e_desc = _entry("Tema principal de la clase...", cl.get("desc","") if cl else "")

        # Día y horas en fila
        hf = ctk.CTkFrame(form, fg_color="transparent")
        hf.pack(fill="x"); hf.columnconfigure((0,1,2), weight=1)
        for i, txt in enumerate(["Día","Hora inicio","Hora fin"]):
            ctk.CTkLabel(hf, text=txt, font=("Helvetica",FS("small"),"bold"),
                text_color=C("text2"), anchor="w").grid(row=0, column=i, sticky="w", padx=(0 if i==0 else 6, 0))
        om_dia = ctk.CTkOptionMenu(hf, values=self.DIAS_SEM, height=38, corner_radius=8,
            font=("Helvetica",FS("small")), fg_color=C("surface2"), text_color=C("text"),
            button_color=C("accent"), button_hover_color=C("accent_dark"))
        om_dia.grid(row=1, column=0, sticky="ew", pady=(4,0))
        om_ini = ctk.CTkOptionMenu(hf, values=self.HORAS_DISP, height=38, corner_radius=8,
            font=("Helvetica",FS("small")), fg_color=C("surface2"), text_color=C("text"),
            button_color=C("accent"), button_hover_color=C("accent_dark"))
        om_ini.grid(row=1, column=1, sticky="ew", pady=(4,0), padx=(6,0))
        om_fin = ctk.CTkOptionMenu(hf, values=self.HORAS_DISP, height=38, corner_radius=8,
            font=("Helvetica",FS("small")), fg_color=C("surface2"), text_color=C("text"),
            button_color=C("accent"), button_hover_color=C("accent_dark"))
        om_fin.grid(row=1, column=2, sticky="ew", pady=(4,0), padx=(6,0))
        if cl:
            om_dia.set(cl["dia"]); om_ini.set(cl["hora_ini"]); om_fin.set(cl["hora_fin"])
        else:
            om_dia.set("Lunes"); om_ini.set("09:00"); om_fin.set("11:00")

        # Selector de color
        ctk.CTkLabel(form, text="Color", font=("Helvetica",FS("small"),"bold"),
            text_color=C("text2"), anchor="w").pack(fill="x", pady=(10,4))
        cf = ctk.CTkFrame(form, fg_color="transparent")
        cf.pack(fill="x")
        self._color_sel = cl["color"] if cl else self.COLORES_DISP[0]
        _col_btns = []
        def _pick(c, btn):
            self._color_sel = c
            for b in _col_btns: b.configure(border_width=0)
            btn.configure(border_width=3)
        for col in self.COLORES_DISP:
            bw = 3 if col == self._color_sel else 0
            btn = ctk.CTkButton(cf, text="", width=28, height=28, corner_radius=14,
                fg_color=col, hover_color=_darken(col,.2),
                border_color="white", border_width=bw)
            btn.configure(command=lambda c=col, b=btn: _pick(c, b))
            btn.pack(side="left", padx=3)
            _col_btns.append(btn)

        lbl_err = ctk.CTkLabel(top, text="", text_color=C("red"),
            font=("Helvetica",FS("small")))
        lbl_err.pack(pady=(8,0))

        def _guardar():
            mat  = e_mat.get().strip()
            grp  = e_grp.get().strip()
            desc = e_desc.get().strip()
            dia  = om_dia.get()
            ini  = om_ini.get()
            fin  = om_fin.get()
            if not mat:
                lbl_err.configure(text="⚠️ La materia no puede estar vacía."); return
            if not grp:
                lbl_err.configure(text="⚠️ El grupo no puede estar vacío."); return
            if ini >= fin:
                lbl_err.configure(text="⚠️ La hora de fin debe ser posterior a la de inicio."); return
            if es_nueva:
                self._clases.append({"id": self._next_id, "materia": mat, "grupo": grp,
                    "dia": dia, "hora_ini": ini, "hora_fin": fin,
                    "color": self._color_sel, "desc": desc})
                self._next_id += 1
            else:
                for c in self._clases:
                    if c["id"] == cl["id"]:
                        c.update({"materia":mat,"grupo":grp,"dia":dia,
                                  "hora_ini":ini,"hora_fin":fin,
                                  "color":self._color_sel,"desc":desc})
                        break
            top.destroy()
            self._render_lista()

        bf = ctk.CTkFrame(top, fg_color="transparent")
        bf.pack(fill="x", padx=24, pady=(4,16))
        Btn(bf, text="💾  Guardar", width=130, height=40, command=_guardar).pack(side="left")
        ctk.CTkButton(bf, text="Cancelar", width=100, height=40, corner_radius=10,
            fg_color=C("surface2"), text_color=C("text"),
            command=top.destroy).pack(side="right")


class PanelHorarios(ctk.CTkFrame):
    COLORES = {"Cálculo III": "#7C5CBF", "Prog. Avanzada": "#E8A020",
               "Física II": "#2E9E6A", "Álgebra": "#1A9EBF",
               "Lab. Sistemas": "#D04040", "Nueva materia": "#888888"}
    HORAS = ["07:00","08:00","09:00","10:00","11:00","12:00",
             "13:00","14:00","15:00","16:00","17:00","18:00","19:00"]
    DIAS  = ["Lun","Mar","Mié","Jue","Vie"]

    def __init__(self, parent, **kw):
        super().__init__(parent, fg_color=C("bg"), **kw)
        # Estructura: {dia: [(hora_ini, hora_fin, materia, grupo, color), ...]}
        self._clases = {
            "Lun":[("09:00","11:00","Cálculo III","Grupo A",C("accent")),
                   ("14:00","16:00","Prog. Avanzada","Grupo B",C("amber"))],
            "Mar":[("10:00","12:00","Álgebra","Grupo C",C("teal")),
                   ("14:00","16:00","Física II","Grupo A",C("green"))],
            "Mié":[("09:00","11:00","Cálculo III","Grupo A",C("accent")),
                   ("13:00","15:00","Lab. Sistemas","Grupo B",C("red"))],
            "Jue":[("10:00","12:00","Prog. Avanzada","Grupo B",C("amber")),
                   ("14:00","16:00","Álgebra","Grupo C",C("teal"))],
            "Vie":[("09:00","11:00","Física II","Grupo A",C("green"))],
        }
        self._build()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=C("surface"), corner_radius=0, height=70)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ih = ctk.CTkFrame(hdr, fg_color="transparent")
        ih.pack(fill="both", expand=True, padx=24, pady=14)
        ctk.CTkLabel(ih, text="📅  Administración de Horarios",
            font=("Helvetica",FS("h2"),"bold"), text_color=C("text")).pack(side="left")
        Btn(ih, text="＋  Nueva clase", width=150, height=38,
            command=self._nueva_clase).pack(side="right")

        self._scr = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                            scrollbar_button_color=C("accent"))
        self._scr.pack(fill="both", expand=True, padx=20, pady=12)
        self._render_grid()

    def _render_grid(self):
        for w in self._scr.winfo_children(): w.destroy()

        # Encabezado de días
        enc = ctk.CTkFrame(self._scr, fg_color="transparent")
        enc.pack(fill="x", pady=(0,4))
        ctk.CTkLabel(enc, text="Hora", width=68,
            font=("Helvetica",FS("small"),"bold"), text_color=C("text2")).pack(side="left")
        for d in self.DIAS:
            ctk.CTkLabel(enc, text=d, width=150,
                font=("Helvetica",FS("body"),"bold"), text_color=C("text")).pack(side="left",padx=3)

        for idx, h in enumerate(self.HORAS):
            row = ctk.CTkFrame(self._scr,
                fg_color=C("surface2") if idx%2==0 else "transparent",
                corner_radius=6, height=52)
            row.pack(fill="x", pady=1); row.pack_propagate(False)
            ctk.CTkLabel(row, text=h, width=68,
                font=("Helvetica",FS("small")), text_color=C("text2")).pack(side="left")
            for d in self.DIAS:
                encontrado = None
                for entry in self._clases.get(d, []):
                    ini, fin, mat, grp, col = entry
                    if ini <= h < fin:
                        encontrado = entry; break
                celda = ctk.CTkFrame(row,
                    fg_color=encontrado[4] if encontrado else "transparent",
                    corner_radius=6, width=146, height=46,
                    cursor="hand2" if encontrado else "")
                celda.pack(side="left", padx=2, pady=3); celda.pack_propagate(False)
                if encontrado:
                    ini, fin, mat, grp, col = encontrado
                    if h == ini:
                        # Nombre completo con wraplength para que no se corte
                        ctk.CTkLabel(celda, text=mat,
                            font=("Helvetica", 11, "bold"),
                            text_color="white",
                            wraplength=138, justify="center").place(
                            relx=.5, rely=.32, anchor="center")
                        ctk.CTkLabel(celda, text=grp,
                            font=("Helvetica", 9),
                            text_color="#DDDDDD").place(relx=.5, rely=.75, anchor="center")
                    celda.bind("<Button-1>", lambda e, en=encontrado, dia=d: self._editar_clase(dia, en))

    def _nueva_clase(self):
        self._dialogo_clase(None, None)

    def _editar_clase(self, dia, entry):
        self._dialogo_clase(dia, entry)

    def _dialogo_clase(self, dia_actual, entry):
        top = ctk.CTkToplevel(self)
        es_nueva = entry is None
        top.title("Nueva clase" if es_nueva else "Editar clase")
        top.geometry("420x460")
        top.configure(fg_color=C("bg"))
        top.grab_set(); top.lift(); top.focus_force()

        ctk.CTkLabel(top, text="➕  Nueva clase" if es_nueva else "✏️  Editar clase",
            font=("Helvetica",FS("h2"),"bold"), text_color=C("text")).pack(padx=24,pady=(20,16),anchor="w")

        form = ctk.CTkFrame(top, fg_color="transparent")
        form.pack(fill="x", padx=24)

        # Materia
        ctk.CTkLabel(form, text="Materia", font=("Helvetica",FS("small"),"bold"),
            text_color=C("text2"), anchor="w").pack(fill="x")
        e_mat = ctk.CTkEntry(form, height=40, corner_radius=10,
            font=("Helvetica",FS("body")), fg_color=C("surface2"),
            text_color=C("text"), border_color=C("border"))
        e_mat.pack(fill="x", pady=(4,12))
        if entry: e_mat.insert(0, entry[2])

        # Grupo
        ctk.CTkLabel(form, text="Grupo", font=("Helvetica",FS("small"),"bold"),
            text_color=C("text2"), anchor="w").pack(fill="x")
        e_grp = ctk.CTkEntry(form, height=40, corner_radius=10,
            font=("Helvetica",FS("body")), fg_color=C("surface2"),
            text_color=C("text"), border_color=C("border"))
        e_grp.pack(fill="x", pady=(4,12))
        if entry: e_grp.insert(0, entry[3])

        # Día
        ctk.CTkLabel(form, text="Día", font=("Helvetica",FS("small"),"bold"),
            text_color=C("text2"), anchor="w").pack(fill="x")
        om_dia = ctk.CTkOptionMenu(form, values=self.DIAS, height=40, corner_radius=10,
            font=("Helvetica",FS("body")), fg_color=C("surface2"), text_color=C("text"),
            button_color=C("accent"), button_hover_color=C("accent_dark"))
        om_dia.pack(fill="x", pady=(4,12))
        if dia_actual: om_dia.set(dia_actual)

        # Hora inicio / fin
        hf = ctk.CTkFrame(form, fg_color="transparent")
        hf.pack(fill="x"); hf.columnconfigure((0,1), weight=1)
        ctk.CTkLabel(hf, text="Hora inicio", font=("Helvetica",FS("small"),"bold"),
            text_color=C("text2"), anchor="w").grid(row=0,column=0,sticky="w")
        ctk.CTkLabel(hf, text="Hora fin", font=("Helvetica",FS("small"),"bold"),
            text_color=C("text2"), anchor="w").grid(row=0,column=1,sticky="w",padx=(8,0))
        om_ini = ctk.CTkOptionMenu(hf, values=self.HORAS, height=40, corner_radius=10,
            font=("Helvetica",FS("body")), fg_color=C("surface2"), text_color=C("text"),
            button_color=C("accent"), button_hover_color=C("accent_dark"))
        om_ini.grid(row=1,column=0,sticky="ew",pady=(4,0))
        om_fin = ctk.CTkOptionMenu(hf, values=self.HORAS, height=40, corner_radius=10,
            font=("Helvetica",FS("body")), fg_color=C("surface2"), text_color=C("text"),
            button_color=C("accent"), button_hover_color=C("accent_dark"))
        om_fin.grid(row=1,column=1,sticky="ew",pady=(4,0),padx=(8,0))
        if entry:
            om_ini.set(entry[0]); om_fin.set(entry[1])
        else:
            om_ini.set("09:00"); om_fin.set("11:00")

        lbl_err = ctk.CTkLabel(top, text="", text_color=C("red"),
            font=("Helvetica",FS("small")))
        lbl_err.pack(pady=(10,0))

        def _guardar():
            mat = e_mat.get().strip()
            grp = e_grp.get().strip()
            dia = om_dia.get()
            ini = om_ini.get()
            fin = om_fin.get()
            if not mat or not grp:
                lbl_err.configure(text="⚠ Completa materia y grupo"); return
            if ini >= fin:
                lbl_err.configure(text="⚠ Hora inicio debe ser menor a fin"); return
            # Eliminar entrada anterior si es edición
            if not es_nueva and dia_actual:
                self._clases[dia_actual] = [e for e in self._clases.get(dia_actual,[]) if e != entry]
            col = self.COLORES.get(mat, C("accent"))
            self._clases.setdefault(dia, []).append((ini, fin, mat, grp, col))
            top.destroy()
            self._render_grid()

        def _eliminar():
            if not es_nueva and dia_actual and entry:
                self._clases[dia_actual] = [e for e in self._clases.get(dia_actual,[]) if e != entry]
                top.destroy()
                self._render_grid()

        bf = ctk.CTkFrame(top, fg_color="transparent")
        bf.pack(fill="x", padx=24, pady=(8,20))
        Btn(bf, text="💾  Guardar", width=140, command=_guardar).pack(side="left", padx=(0,8))
        if not es_nueva:
            ctk.CTkButton(bf, text="🗑  Eliminar", width=120, height=40, corner_radius=12,
                fg_color=C("red"), hover_color="#C03030", text_color="white",
                font=("Helvetica",FS("body")),
                command=_eliminar).pack(side="left")
        Btn(bf, text="Cancelar", width=100, fg_color=C("surface2"),
            text_color=C("text"), command=top.destroy).pack(side="right")

# ─────────────────────────────────────────────────────────────────
#  VENTANA PRINCIPAL (sidebar + área de contenido)
# ─────────────────────────────────────────────────────────────────
class VentanaPrincipal(ctk.CTkFrame):
    def __init__(self, parent, rol, datos, file_key, correo):
        super().__init__(parent, fg_color=C("bg"))
        self.rol      = rol
        self.datos    = datos
        self.file_key = file_key
        self.correo   = correo
        self.parent   = parent
        self._panel   = None
        self._build()

    def _build(self):
        # ── IMPORTANTE: self.area debe existir ANTES de crear el Sidebar,
        # porque Sidebar._build() llama _select() al final, lo que dispara
        # on_tab → _switch(), que necesita self.area para mostrar el panel.
        self.area = ctk.CTkFrame(self, fg_color=C("bg"), corner_radius=0)

        self.sidebar = Sidebar(self, self.rol, self._switch)
        self.sidebar._lector_excluir = True  # el lector no navega dentro de la sidebar
        self.sidebar.pack(side="left", fill="y")
        ctk.CTkFrame(self, fg_color=C("border"), width=1).pack(side="left", fill="y")
        self.area.pack(side="left", fill="both", expand=True)
        # Now that self.sidebar is fully assigned, trigger the initial panel.
        self.sidebar.set_active("Inicio")
        # ── Atajos de teclado (si está activado en ajustes) ──────
        if PREFS.get("keyboard_nav", False):
            self._bind_keyboard()
        # ── Lector de pantalla (si estaba activado) ──────────────
        if PREFS.get("screen_reader", False):
            try:
                LectorPantalla.activar(self.parent)
            except Exception:
                pass
        # ── Burbuja de IA flotante ────────────────────────────────
        self._ia_bubble_visible = False
        self._build_ia_bubble()

    def _build_ia_bubble(self):
        """Crea el botón flotante de IA y el panel de chat."""
        self._ia_btn = ctk.CTkButton(self, text="🤖", width=52, height=52,
            corner_radius=26, font=("Helvetica", 22),
            fg_color=C("accent"), hover_color=C("accent_dark"),
            text_color="white", command=self._toggle_ia_panel)
        self._ia_btn.place(relx=1.0, rely=1.0, x=-20, y=-20, anchor="se")

        self._ia_panel = ctk.CTkFrame(self, fg_color=C("surface"),
            corner_radius=18, border_width=1, border_color=C("border"),
            width=340, height=430)

        ph = ctk.CTkFrame(self._ia_panel, fg_color=C("accent"), corner_radius=0, height=50)
        ph.pack(fill="x"); ph.pack_propagate(False)
        ctk.CTkLabel(ph, text="🤖  Asistente IA · Optem",
            font=("Helvetica", FS("body"), "bold"), text_color="white").pack(
            side="left", padx=14, pady=12)
        ctk.CTkButton(ph, text="✕", width=30, height=30, corner_radius=15,
            fg_color="transparent", hover_color=C("accent_dark"),
            text_color="white", font=("Helvetica", 13),
            command=self._toggle_ia_panel).pack(side="right", padx=8)

        # Usar CTkTextbox (mucho más liviano que ScrollableFrame con widgets)
        self._ia_chat = ctk.CTkTextbox(self._ia_panel, height=260,
            corner_radius=10, font=("Helvetica", FS("small")),
            fg_color=C("surface2"), text_color=C("text"),
            border_color=C("border"), border_width=0,
            wrap="word", state="disabled")
        self._ia_chat.pack(fill="x", padx=8, pady=(8, 4))

        # Sugerencias rápidas
        sugs = ctk.CTkFrame(self._ia_panel, fg_color="transparent")
        sugs.pack(fill="x", padx=8, pady=(0, 4))
        for stxt in ["📅 Agenda", "📚 Tema", "🔥 Racha"]:
            ctk.CTkButton(sugs, text=stxt, height=26, corner_radius=8, width=90,
                fg_color=C("surface2"), text_color=C("text2"),
                hover_color=C("accent_bg"), font=("Helvetica", FS("small")),
                command=lambda t=stxt: self._ia_enviar(t.split(" ",1)[1] if " " in t else t)
                ).pack(side="left", padx=2)

        ef = ctk.CTkFrame(self._ia_panel, fg_color="transparent")
        ef.pack(fill="x", padx=8, pady=(4, 10))
        self._ia_entry = ctk.CTkEntry(ef, placeholder_text="Escribe tu pregunta...",
            height=36, corner_radius=10, font=("Helvetica", FS("small")),
            fg_color=C("surface2"), text_color=C("text"), border_color=C("border"))
        self._ia_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self._ia_entry.bind("<Return>", lambda e: self._ia_enviar())
        ctk.CTkButton(ef, text="➤", width=36, height=36, corner_radius=10,
            fg_color=C("accent"), hover_color=C("accent_dark"), text_color="white",
            font=("Helvetica", 15), command=self._ia_enviar).pack(side="right")

        self._ia_add_msg("🤖 IA", "¡Hola! 👋 Soy tu asistente.\n"
                         "Puedo ayudarte con tu agenda, tareas, Pomodoro y más.\n"
                         "¿En qué te ayudo hoy?")

    def _toggle_ia_panel(self):
        if self._ia_bubble_visible:
            self._ia_panel.place_forget()
            self._ia_bubble_visible = False
        else:
            self._ia_panel.place(relx=1.0, rely=1.0, x=-20, y=-80, anchor="se")
            self._ia_panel.lift()
            self._ia_btn.lift()
            self._ia_bubble_visible = True

    def _ia_add_msg(self, quien, texto):
        """Agrega un mensaje al CTkTextbox del chat."""
        try:
            self._ia_chat.configure(state="normal")
            contenido = self._ia_chat.get("1.0", "end").strip()
            if contenido:
                self._ia_chat.insert("end", "\n\n")
            self._ia_chat.insert("end", f"{quien}:\n{texto}")
            self._ia_chat.configure(state="disabled")
            self._ia_chat.see("end")
        except Exception:
            pass

    def _ia_enviar(self, texto=None):
        if texto is None:
            texto = self._ia_entry.get().strip()
            self._ia_entry.delete(0, "end")
        if not texto:
            return
        self._ia_add_msg("Tú", texto)
        texto_l = texto.lower()
        if any(k in texto_l for k in ("agenda","hoy","mañana","actividad")):
            resp = ("📅 Puedes ver tu agenda en «Mi Agenda» del menú.\n"
                    "Ahí verás todas tus actividades por día.")
        elif any(k in texto_l for k in ("racha","streak","dias")):
            resp = ("🔥 Tu racha aumenta con cada entrega y actividad completada.\n"
                    "¡No rompas la cadena!")
        elif any(k in texto_l for k in ("pomodoro","tiempo","estudio","concentr")):
            resp = ("⏱ Pomodoro: 25 min de estudio + 5 de descanso.\n"
                    "Úsalo en la pestaña «Pomodoro».")
        elif any(k in texto_l for k in ("xp","puntos","nivel","logro")):
            resp = ("⭐ Ganas XP con actividades, entregas y rachas.\n"
                    "Revisa tus logros en «Logros».")
        elif any(k in texto_l for k in ("tarea","entrega","trabajo")):
            resp = ("📤 Ve a «Actividades» → área de entregas.\n"
                    "Cada entrega sube tu racha 🔥.")
        elif any(k in texto_l for k in ("hola","hi","buenas","hey")):
            resp = "¡Hola! 😊 ¿En qué puedo ayudarte hoy?"
        else:
            resp = (f"Entendido ✅\nSobre «{texto[:35]}»:\n"
                    "Puedo ayudarte con agenda, tareas, Pomodoro, XP y más.")
        self._ia_panel.after(350, lambda: self._ia_add_msg("🤖 IA", resp))

    def _bind_keyboard(self):
        """Registra atajos globales de teclado en la ventana raíz."""
        tabs_est = ["Inicio","Mi Agenda","Actividades","Pomodoro","Logros","Ajustes"]
        tabs_adm = ["Inicio","Tareas globales","Reportes","Alumnos","Horarios","Clases","Ajustes"]
        tabs = tabs_adm if self.rol == "Administrativo" else tabs_est
        root = self.parent
        for i, tab in enumerate(tabs, start=1):
            root.bind_all(f"<Control-{i}>",
                lambda e, t=tab: self.sidebar.set_active(t))
        # Ctrl+M abre voz si está habilitado
        root.bind_all("<Control-m>",
            lambda e: self.sidebar._abrir_voz())

    def _switch(self, nombre):
        if self._panel:
            try:
                self._panel.destroy()
            except Exception:
                pass
            self._panel = None
        # Limpiar área sin destruir el frame contenedor (más rápido)
        for child in self.area.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass

        if self.rol == "Estudiante":
            panels = {
                "Inicio":      lambda: PanelInicioEst(self.area, self.datos,
                                                      self.file_key, self.sidebar.set_active),
                "Mi Agenda":   lambda: PanelAgendaSemanal(self.area, self.file_key),
                "Actividades": lambda: PanelActividades(self.area, self.file_key, rol=self.rol),
                "Pomodoro":    lambda: PanelPomodoro(self.area, self.file_key, self.datos),
                "Logros":      lambda: PanelLogros(self.area, self.datos),
                "Ajustes":     lambda: PanelAjustes(self.area, self.parent, self.correo, rol=self.rol),
            }
        else:
            panels = {
                "Inicio":          lambda: PanelInicioAdmin(self.area, self.datos,
                                                            self.sidebar.set_active),
                "Tareas globales": lambda: PanelTareasGlobales(self.area),
                "Reportes":        lambda: PanelReportes(self.area),
                "Alumnos":         lambda: PanelAlumnos(self.area),
                "Horarios":        lambda: PanelHorarios(self.area),
                "Clases":          lambda: PanelClasesAdmin(self.area),
                "Ajustes":         lambda: PanelAjustes(self.area, self.parent, self.correo, rol=self.rol),
            }

        builder = panels.get(nombre)
        if builder:
            try:
                p = builder()
                p.pack(fill="both", expand=True)
                self._panel = p
                self.area.update_idletasks()
                # Re-escanear el lector de pantalla si está activo
                if PREFS.get("screen_reader") and LectorPantalla._instancia:
                    inst = LectorPantalla._instancia
                    inst._idx = 0   # empezar desde el primer elemento del nuevo panel
                    self.area.after(200, inst._escanear)
            except Exception as e:
                err_frame = ctk.CTkFrame(self.area, fg_color=C("bg"))
                err_frame.pack(fill="both", expand=True)
                ctk.CTkLabel(err_frame,
                    text=f"Error al cargar '{nombre}': {e}",
                    font=("Helvetica", 12), text_color=C("red"),
                    wraplength=600).place(relx=.5, rely=.5, anchor="center")
                self._panel = err_frame

# ─────────────────────────────────────────────────────────────────
#  SPLASH
# ─────────────────────────────────────────────────────────────────
class PantallaCarga(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=C("bg"))
        self._dot_idx  = 0
        self._bar_val  = 0.0
        self._orbs     = []  # animación de círculos flotantes
        self._build()

    def _build(self):
        # ── Fondo con círculos decorativos animados (canvas) ─────
        self._canvas = tk.Canvas(self, bg=C("bg"), highlightthickness=0)
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # Dibujar orbs estáticos iniciales
        orb_data = [
            (0.15, 0.20, 180, C("accent"), 30),
            (0.80, 0.15, 120, C("accent_dark"), 20),
            (0.70, 0.80, 200, C("teal"),    25),
            (0.10, 0.75, 140, C("pink"),    20),
            (0.50, 0.10, 90,  C("accent"),  15),
            (0.90, 0.55, 100, C("green"),   18),
        ]
        self._orb_specs = orb_data
        self._orb_phases = [i * 0.9 for i in range(len(orb_data))]
        # Los orbs se dibujan en _animate_orbs cuando el canvas tenga tamaño

        # ── Centro ───────────────────────────────────────────────
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.place(relx=0.5, rely=0.5, anchor="center")

        # Logo con fondo accent
        _splash_logo = load_logo(size=(96, 96), radius=26)
        if _splash_logo:
            self._logo_lbl = ctk.CTkLabel(center, image=_splash_logo, text="")
            self._logo_lbl.pack(pady=(0, 4))
        else:
            logo_box = ctk.CTkFrame(center, fg_color=C("accent"),
                                    width=96, height=96, corner_radius=26)
            logo_box.pack(pady=(0, 4))
            logo_box.pack_propagate(False)
            ctk.CTkLabel(logo_box, text="OP", font=("Helvetica",34,"bold"),
                         text_color="white").place(relx=.5,rely=.5,anchor="center")
            self._logo_lbl = None

        ctk.CTkFrame(center, fg_color="transparent", height=16).pack()
        ctk.CTkLabel(center, text="OPTEM",
                     font=("Helvetica", 46, "bold"), text_color=C("text")).pack()
        ctk.CTkLabel(center, text="Agenda Virtual Inteligente · UAEMéx",
                     font=("Helvetica", FS("body")), text_color=C("text2")).pack(pady=4)

        # Puntos animados de status
        self.lbl_status = ctk.CTkLabel(center, text="Iniciando",
                     font=("Helvetica", FS("small")), text_color=C("accent"))
        self.lbl_status.pack(pady=(8, 16))

        # Barra de progreso con animación propia
        bar_bg = ctk.CTkFrame(center, fg_color=C("border"),
                              corner_radius=6, height=6, width=280)
        bar_bg.pack()
        bar_bg.pack_propagate(False)
        self._bar_fill = ctk.CTkFrame(bar_bg, fg_color=C("accent"),
                                      corner_radius=6, height=6, width=0)
        self._bar_fill.place(x=0, y=0, relheight=1)

        ctk.CTkFrame(center, fg_color="transparent", height=20).pack()

        # Iniciar animaciones
        self.after(100, self._animate_bar)
        self.after(200, self._animate_dots)
        self.after(300, self._animate_orbs)

    def _animate_bar(self):
        if not self.winfo_exists(): return
        self._bar_val = min(self._bar_val + 0.012, 1.0)
        try:
            self._bar_fill.configure(width=int(280 * self._bar_val))
        except Exception: pass
        if self._bar_val < 1.0:
            self.after(40, self._animate_bar)

    def _animate_dots(self):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        msgs = ["Iniciando", "Iniciando·", "Iniciando··", "Iniciando···",
                "Cargando sesión", "Cargando sesión·", "Cargando sesión··",
                "¡Casi listo!", "¡Listo! 🚀"]
        try:
            idx = min(self._dot_idx, len(msgs)-1)
            self.lbl_status.configure(text=msgs[idx])
            self._dot_idx += 1
        except Exception:
            return
        self.after(340, self._animate_dots)

    def _animate_orbs(self):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        try:
            W = self.winfo_width()
            H = self.winfo_height()
            if W < 10 or H < 10:
                self.after(100, self._animate_orbs); return
            import time as _t
            t = _t.time() * 0.6
            self._canvas.delete("orb")
            for i, (rx, ry, r, col, alpha) in enumerate(self._orb_specs):
                phase = self._orb_phases[i]
                ox = rx * W + math.sin(t + phase) * 28
                oy = ry * H + math.cos(t * 0.7 + phase) * 22
                # Dibujar círculo semitransparente (sin alpha nativo en tk, usar color claro)
                self._canvas.create_oval(ox-r, oy-r, ox+r, oy+r,
                    fill=col, outline="", tags="orb",
                    stipple="gray25")
        except Exception:
            return
        self.after(50, self._animate_orbs)


# ─────────────────────────────────────────────────────────────────
#  PANTALLA DE LOGIN (split visual)
# ─────────────────────────────────────────────────────────────────
class PantallaLogin(ctk.CTkFrame):
    def __init__(self, parent, on_login):
        super().__init__(parent, fg_color=C("bg"))
        self.on_login  = on_login
        self.auth      = AuthManager()
        self._logo_angle = 0
        self._logo_scale = 1.0
        self._logo_scale_dir = 1
        self._orb_phases = [i * 1.1 for i in range(8)]
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=3)
        self.rowconfigure(0, weight=1)
        self._build()

    def _build(self):
        # ── Canvas de fondo con partículas/orbs animadas ─────────
        self._canvas = tk.Canvas(self, bg=C("bg"), highlightthickness=0)
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._orb_specs = [
            (0.08, 0.12, 220, C("accent"),      "gray25"),
            (0.85, 0.08, 160, C("accent_dark"), "gray25"),
            (0.78, 0.88, 240, C("teal"),        "gray25"),
            (0.05, 0.82, 170, C("pink"),        "gray25"),
            (0.45, 0.05, 110, C("accent"),      "gray12"),
            (0.92, 0.50, 130, C("green"),       "gray12"),
            (0.55, 0.92, 150, C("accent_dark"), "gray12"),
            (0.30, 0.60, 90,  C("teal"),        "gray12"),
        ]
        self.after(200, self._animate_bg)

        # ── Lado izquierdo: branding ──────────────────────────────
        left = ctk.CTkFrame(self, fg_color=C("accent"), corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew")

        # Canvas para orbs animados en panel izquierdo (morado)
        self._left_canvas = tk.Canvas(left, bg=C("accent"), highlightthickness=0)
        self._left_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._left_orb_specs = [
            (0.10, 0.10, 150, "#B8A8FF", "gray50"),
            (0.82, 0.12, 110, "#FFFFFF", "gray25"),
            (0.75, 0.82, 170, "#8878DD", "gray50"),
            (0.12, 0.78, 120, "#CCBFFF", "gray25"),
            (0.50, 0.04,  75, "#FFFFFF", "gray12"),
            (0.94, 0.48, 100, "#9888EE", "gray50"),
            (0.38, 0.96, 130, "#B0A0FF", "gray25"),
            (0.60, 0.50,  60, "#FFFFFF", "gray12"),
        ]
        self._left_orb_phases = [i * 1.25 for i in range(8)]
        self.after(300, self._animate_left_orbs)

        lc = ctk.CTkFrame(left, fg_color="transparent")
        lc.place(relx=0.5, rely=0.5, anchor="center")

        # Logo animado (bounce + pulse)
        self._logo_raw = None
        _logo = load_logo(size=(100, 100))
        if _logo:
            self._logo_widget = ctk.CTkLabel(lc, image=_logo, text="",
                                              fg_color="transparent")
            self._logo_widget.pack(pady=(0, 18))
        else:
            logo_box = ctk.CTkFrame(lc, fg_color="white", width=100, height=100,
                                    corner_radius=28)
            logo_box.pack(pady=(0, 18)); logo_box.pack_propagate(False)
            ctk.CTkLabel(logo_box, text="OP", font=("Helvetica",34,"bold"),
                         text_color=C("accent")).place(relx=.5,rely=.5,anchor="center")
            self._logo_widget = logo_box
        self._animate_logo()

        ctk.CTkLabel(lc, text="OPTEM",
            font=("Helvetica", 40, "bold"), text_color="white").pack()
        ctk.CTkLabel(lc, text="Agenda Virtual Inteligente",
            font=("Helvetica", 14), text_color="#EEEEFF").pack(pady=(4, 2))
        ctk.CTkFrame(lc, fg_color="#AAAACC", height=1, width=180).pack(pady=(0, 22))

        # Features con animación de aparición
        feats = [
            ("📅", "Agenda y horario académico"),
            ("⏱", "Técnica Pomodoro"),
            ("⭐", "Sistema de XP y logros"),
            ("🔔", "Alertas de entregas"),
        ]
        for ico, txt in feats:
            row = ctk.CTkFrame(lc, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=ico, font=("Helvetica", 18),
                         width=30).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(row, text=txt, font=("Helvetica", 12),
                         text_color="#EEEEFF", anchor="w").pack(side="left")

        # ── Lado derecho: formulario mejorado ────────────────────
        right = ctk.CTkFrame(self, fg_color=C("bg"), corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew")

        form = ctk.CTkFrame(right, fg_color="transparent")
        form.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.76)

        ctk.CTkLabel(form, text="Iniciar sesión",
            font=("Helvetica", FS("h2"), "bold"), text_color=C("text"),
            anchor="w").pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(form, text="Accede con tu cuenta institucional",
            font=("Helvetica", FS("body")), text_color=C("text2"),
            anchor="w").pack(fill="x", pady=(0, 26))

        # Separador decorativo
        sep_row = ctk.CTkFrame(form, fg_color="transparent")
        sep_row.pack(fill="x", pady=(0, 22))
        ctk.CTkFrame(sep_row, fg_color=C("accent"), height=3,
                     corner_radius=2, width=50).pack(side="left")
        ctk.CTkFrame(sep_row, fg_color=C("border"), height=1).pack(
            side="left", fill="x", expand=True, padx=8)

        # Campo correo con ícono
        ctk.CTkLabel(form, text="📧  Correo institucional",
            font=("Helvetica", FS("small"), "bold"), text_color=C("text2"),
            anchor="w").pack(fill="x")
        self.e_correo = ctk.CTkEntry(form,
            placeholder_text="alumno@alumno.uaemex.mx",
            height=52, corner_radius=14,
            font=("Helvetica", FS("body")),
            fg_color=C("surface"), text_color=C("text"),
            border_color=C("border"), border_width=2)
        self.e_correo.pack(fill="x", pady=(6, 18))
        self.e_correo.bind("<Return>", lambda e: self._login("Estudiante"))
        self.e_correo.bind("<FocusIn>",
            lambda e: self.e_correo.configure(border_color=C("accent"), border_width=2))
        self.e_correo.bind("<FocusOut>",
            lambda e: [self.e_correo.configure(border_color=C("border"), border_width=2),
                       self.after(200, self._hide_ac_login)])
        self.e_correo.bind("<KeyRelease>", self._on_key_login)
        self._ac_login_win = None

        # Campo contraseña con ícono
        ctk.CTkLabel(form, text="🔒  Número de cuenta / contraseña",
            font=("Helvetica", FS("small"), "bold"), text_color=C("text2"),
            anchor="w").pack(fill="x")
        self.e_cuenta = ctk.CTkEntry(form,
            placeholder_text="Ej: 1234567",
            height=52, corner_radius=14, show="•",
            font=("Helvetica", FS("body")),
            fg_color=C("surface"), text_color=C("text"),
            border_color=C("border"), border_width=2)
        self.e_cuenta.pack(fill="x", pady=(6, 8))
        self.e_cuenta.bind("<Return>", lambda e: self._login("Estudiante"))
        self.e_cuenta.bind("<FocusIn>",
            lambda e: self.e_cuenta.configure(border_color=C("accent"), border_width=2))
        self.e_cuenta.bind("<FocusOut>",
            lambda e: self.e_cuenta.configure(border_color=C("border"), border_width=2))

        self.lbl_err = ctk.CTkLabel(form, text="", text_color=C("red"),
            font=("Helvetica", FS("small")))
        self.lbl_err.pack(anchor="w", pady=(0, 18))

        # Tipo de cuenta
        ctk.CTkLabel(form, text="Tipo de cuenta",
            font=("Helvetica", FS("small"), "bold"), text_color=C("text2"),
            anchor="w").pack(fill="x", pady=(0, 10))

        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.pack(fill="x")
        btn_row.columnconfigure((0, 1), weight=1)

        # Tarjeta estudiante
        be = ctk.CTkFrame(btn_row, fg_color=C("accent"), corner_radius=16)
        be.grid(row=0, column=0, padx=(0, 7), sticky="ew")
        ctk.CTkLabel(be, text="🎓", font=("Helvetica", 28)).pack(pady=(16, 4))
        ctk.CTkLabel(be, text="Estudiante", font=("Helvetica", 13, "bold"),
                     text_color="white").pack()
        ctk.CTkLabel(be, text="@alumno.uaemex.mx", font=("Helvetica", 9),
                     text_color="#EEEEFF").pack(pady=(0, 8))
        Btn(be, text="Entrar  →", height=40, fg_color="white",
            text_color=C("accent"), hover_color="#F0EEFF",
            corner_radius=12,
            command=lambda: self._login("Estudiante")).pack(
                fill="x", padx=14, pady=(0, 14))

        # Tarjeta admin
        ba = ctk.CTkFrame(btn_row, fg_color=C("surface"), corner_radius=16,
                           border_color=C("border"), border_width=2)
        ba.grid(row=0, column=1, padx=(7, 0), sticky="ew")
        ctk.CTkLabel(ba, text="🏛️", font=("Helvetica", 28)).pack(pady=(16, 4))
        ctk.CTkLabel(ba, text="Administrativo", font=("Helvetica", 13, "bold"),
                     text_color=C("text")).pack()
        ctk.CTkLabel(ba, text="@uaemex.mx", font=("Helvetica", 9),
                     text_color=C("text3")).pack(pady=(0, 8))
        BtnOutline(ba, text="Entrar  →", height=40, corner_radius=12,
                   command=lambda: self._login("Administrativo")).pack(
                       fill="x", padx=14, pady=(0, 14))

    def _on_key_login(self, event):
        txt = self.e_correo.get().strip()
        # Mostrar sugerencias si no tiene @ aún
        if not txt or "@" in txt:
            self._hide_ac_login(); return
        sugerencias = [f"{txt}@alumno.uaemex.mx", f"{txt}@uaemex.mx"]
        self._show_ac_login(sugerencias)

    def _show_ac_login(self, sugerencias):
        self._hide_ac_login()
        try:
            self.e_correo.update_idletasks()
            x = self.e_correo.winfo_rootx()
            y = self.e_correo.winfo_rooty() + self.e_correo.winfo_height()
            w = self.e_correo.winfo_width()
        except Exception:
            return
        win = tk.Toplevel(self)
        win.overrideredirect(True)
        win.geometry(f"{w}x{len(sugerencias)*44}+{x}+{y}")
        win.configure(bg=C("surface"))
        win.attributes("-topmost", True)
        self._ac_login_win = win
        for sug in sugerencias:
            fr = tk.Frame(win, bg=C("surface"), cursor="hand2")
            fr.pack(fill="x")
            lbl = tk.Label(fr, text=sug,
                font=("Helvetica", 12), fg=C("text"), bg=C("surface"),
                anchor="w", padx=12, pady=10)
            lbl.pack(fill="x")
            def _hover_in(e, f=fr): f.configure(bg=C("surface2")); e.widget.configure(bg=C("surface2"))
            def _hover_out(e, f=fr): f.configure(bg=C("surface")); e.widget.configure(bg=C("surface"))
            def _click(e, s=sug): self._select_ac_login(s)
            fr.bind("<Enter>", _hover_in); fr.bind("<Leave>", _hover_out)
            fr.bind("<Button-1>", _click)
            lbl.bind("<Enter>", _hover_in); lbl.bind("<Leave>", _hover_out)
            lbl.bind("<Button-1>", _click)

    def _select_ac_login(self, sug):
        self.e_correo.delete(0, "end")
        self.e_correo.insert(0, sug)
        self._hide_ac_login()

    def _hide_ac_login(self):
        if self._ac_login_win:
            try: self._ac_login_win.destroy()
            except Exception: pass
            self._ac_login_win = None

    def _animate_logo(self):
        """Animación de pulso suave para el logo."""
        try:
            if not self.winfo_exists():
                return
            if not hasattr(self, "_logo_widget"):
                return
            self._logo_scale += 0.003 * self._logo_scale_dir
            if self._logo_scale >= 1.08:
                self._logo_scale_dir = -1
            elif self._logo_scale <= 0.92:
                self._logo_scale_dir = 1
            # Efecto visual: parpadeo de color de fondo
            pulse_alpha = int(255 * abs(self._logo_scale - 1.0) * 6)
            self.after(40, self._animate_logo)
        except Exception:
            pass

    def _animate_bg(self):
        """Animación de orbs flotantes en el fondo."""
        try:
            if not self.winfo_exists():
                return
            W = self.winfo_width()
            H = self.winfo_height()
            if W < 10 or H < 10:
                self.after(100, self._animate_bg)
                return
            import time as _t
            t = _t.time() * 0.5
            self._canvas.delete("orb")
            for i, (rx, ry, r, col, stip) in enumerate(self._orb_specs):
                phase = self._orb_phases[i]
                ox = rx * W + math.sin(t + phase) * 35
                oy = ry * H + math.cos(t * 0.65 + phase) * 28
                self._canvas.create_oval(
                    ox-r, oy-r, ox+r, oy+r,
                    fill=col, outline="", tags="orb", stipple=stip)
            self.after(50, self._animate_bg)
        except Exception:
            pass

    def _animate_left_orbs(self):
        """Animación de orbs flotantes en el panel izquierdo (morado)."""
        try:
            if not self.winfo_exists():
                return
            W = self._left_canvas.winfo_width()
            H = self._left_canvas.winfo_height()
            if W < 10 or H < 10:
                self.after(100, self._animate_left_orbs)
                return
            import time as _t
            t = _t.time() * 0.45
            self._left_canvas.delete("lorb")
            for i, (rx, ry, r, col, stip) in enumerate(self._left_orb_specs):
                phase = self._left_orb_phases[i]
                ox = rx * W + math.sin(t + phase) * 32
                oy = ry * H + math.cos(t * 0.65 + phase) * 26
                self._left_canvas.create_oval(
                    ox-r, oy-r, ox+r, oy+r,
                    fill=col, outline="", tags="lorb", stipple=stip)
            self.after(50, self._animate_left_orbs)
        except Exception:
            pass

    def _login(self, rol):
        correo = self.e_correo.get().strip()
        cuenta = self.e_cuenta.get().strip()
        if not correo or not cuenta:
            self.lbl_err.configure(text="⚠  Completa todos los campos")
            return
        # Efecto de carga visual
        self.lbl_err.configure(text="⏳  Verificando...", text_color=C("accent"))
        self.update()
        res = self.auth.iniciar_sesion(correo, cuenta)
        if res["status"] == "success":
            self.lbl_err.configure(text="")
            guardar_sesion(correo, rol, res["file_key"])
            self.on_login(rol, res["file_key"], correo)
        else:
            self.lbl_err.configure(
                text_color=C("red"),
                text="✕  Correo no válido. Usa @alumno.uaemex.mx o @uaemex.mx")
class OptemApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Optem · Agenda Virtual Inteligente — UAEMéx")
        self.geometry("1280x780")
        self.minsize(960, 620)
        ctk.set_appearance_mode("dark" if PREFS["dark_mode"] else "light")
        ctk.set_default_color_theme("blue")
        self._screen = None
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._mostrar_splash()

    def _on_close(self):
        """Cierra la ventana SIN cerrar sesión para que el auto-login funcione al reabrir."""
        self.destroy()

    def _set(self, widget):
        if self._screen:
            self._screen.destroy()
        self._screen = widget
        widget.pack(fill="both", expand=True)

    def _mostrar_splash(self):
        self._set(PantallaCarga(self))
        self.after(3000, self._post_splash)

    def _post_splash(self):
        try:
            sesion = cargar_sesion()
        except Exception:
            sesion = None
        if sesion and sesion.get("rol") and sesion.get("file_key"):
            try:
                self._entrar(sesion["rol"], sesion["file_key"], sesion.get("correo",""))
                return
            except Exception:
                pass
        try:
            self._set(PantallaLogin(self, self._entrar))
        except Exception as e:
            messagebox.showerror("Error al iniciar", f"No se pudo cargar la pantalla de inicio:\n{e}")

    def _entrar(self, rol, file_key, correo=""):
        bridge = DataBridge(file_key)
        datos  = bridge.cargar_datos() or {
            "perfil": {"nombre": correo, "racha": 7, "xp": 1240, "nivel": "Intermedio"},
            "config": {}, "materias": {}, "agenda": []
        }
        if rol == "Estudiante":
            _sembrar_datos_ejemplo(file_key)
        else:
            if not cargar_global():
                guardar_global(EJEMPLO_GLOBAL)
        self._set(VentanaPrincipal(self, rol, datos, file_key, correo))

    def volver_a_login(self):
        self._set(PantallaLogin(self, self._entrar))

# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = OptemApp()
    app.mainloop()
