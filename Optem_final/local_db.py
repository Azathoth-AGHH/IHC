# ╔══════════════════════════════════════════════════════════════════╗
# ║  local_db.py — Base de datos local (JSON) y datos de ejemplo     ║
# ╚══════════════════════════════════════════════════════════════════╝
import os, json, logging, tempfile
from datetime import datetime, timedelta

CATEGORIAS_PERSONAL = [
    "📚 Estudio", "🏃 Deporte", "🎮 Ocio", "🤝 Reunión",
    "🏥 Salud", "✈️ Viaje", "🎵 Cultura", "💼 Trabajo",
    "📝 Tarea", "⭐ Personal"]

CATEGORIAS_GLOBAL = [
    "📚 Tarea", "📝 Examen", "🧪 Práctica",
    "📋 Proyecto", "📢 Aviso", "🎓 Evento"]

def _file_personal(key):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), f"personal_{key}.json")

GLOBAL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "admin_global.json")

# ── Caché en memoria: evita leer disco en cada render ────────────
_cache_personal: dict = {}
_cache_global = None

def _validar_lista_json(data, origen: str) -> list:
    """Verifica que el JSON sea una lista válida; registra advertencia si no."""
    if not isinstance(data, list):
        logging.warning("local_db: esquema inválido en %s — se esperaba lista, se obtuvo %s",
                        origen, type(data).__name__)
        return []
    return data

def cargar_personal(key):
    if key in _cache_personal:
        return _cache_personal[key]
    f = _file_personal(key)
    if os.path.exists(f):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                raw = fp.read()
            data = json.loads(raw)
            data = _validar_lista_json(data, f)
            _cache_personal[key] = data
            return data
        except json.JSONDecodeError as e:
            logging.warning("cargar_personal(%s): JSON truncado o inválido – %s", key, e)
        except Exception as e:
            logging.warning("cargar_personal(%s): error inesperado – %s", key, e)
    _cache_personal[key] = []
    return []

def guardar_personal(key, lista):
    _cache_personal[key] = lista          # actualiza caché antes de escribir
    dest = _file_personal(key)
    try:
        dir_ = os.path.dirname(dest) or "."
        with tempfile.NamedTemporaryFile("w", encoding="utf-8",
                                         dir=dir_, delete=False, suffix=".tmp") as tmp:
            json.dump(lista, tmp, ensure_ascii=False, indent=2)
            tmp_path = tmp.name
        os.replace(tmp_path, dest)
    except Exception as e:
        logging.warning("guardar_personal(%s): fallo al escribir – %s", key, e)

def cargar_global():
    global _cache_global
    if _cache_global is not None:
        return _cache_global
    if os.path.exists(GLOBAL_FILE):
        try:
            with open(GLOBAL_FILE, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
            _cache_global = _validar_lista_json(data, GLOBAL_FILE)
            return _cache_global
        except json.JSONDecodeError as e:
            logging.warning("cargar_global: JSON truncado o inválido – %s", e)
        except Exception as e:
            logging.warning("cargar_global: error inesperado – %s", e)
    _cache_global = []
    return []

def guardar_global(lista):
    global _cache_global
    _cache_global = lista                 # actualiza caché antes de escribir
    try:
        dir_ = os.path.dirname(GLOBAL_FILE) or "."
        with tempfile.NamedTemporaryFile("w", encoding="utf-8",
                                          dir=dir_, delete=False, suffix=".tmp") as tmp:
            json.dump(lista, tmp, ensure_ascii=False, indent=2)
            tmp_path = tmp.name
        os.replace(tmp_path, GLOBAL_FILE)
    except Exception as e:
        logging.warning("guardar_global: fallo al escribir – %s", e)

def invalidar_cache_personal(key=None):
    """Invalida la caché personal (útil tras edición externa)."""
    global _cache_personal
    if key:
        _cache_personal.pop(key, None)
    else:
        _cache_personal.clear()

def invalidar_cache_global():
    """Invalida la caché global (útil tras edición externa)."""
    global _cache_global
    _cache_global = None

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
     "desc":"Temas: límites, derivadas, regla de la cadena y optimización. Traer calculadora científica.","prioridad":1},
    {"id":10003,"titulo":"Entrega: Proyecto final — Programación Web","categoria":"📋 Proyecto",
     "fecha":_fecha(10),"hora_inicio":"08:00","hora_fin":"23:59",
     "desc":"Entrega del repositorio en GitHub + presentación de 15 min.","prioridad":1},
    {"id":10004,"titulo":"Práctica de laboratorio — Química Orgánica","categoria":"🧪 Práctica",
     "fecha":_fecha(3),"hora_inicio":"14:00","hora_fin":"16:00",
     "desc":"Práctica 4: Síntesis de compuestos orgánicos. Obligatorio: bata, guantes y gafas.","prioridad":2},
    {"id":10005,"titulo":"📢 Aviso: Semana de registro de materias","categoria":"📢 Aviso",
     "fecha":_fecha(1),"hora_inicio":"00:00","hora_fin":"23:59",
     "desc":"El registro de materias para el siguiente semestre inicia esta semana.","prioridad":3},
    {"id":10006,"titulo":"Evento: Expo Ingeniería UAEMéx 2025","categoria":"🎓 Evento",
     "fecha":_fecha(14),"hora_inicio":"10:00","hora_fin":"18:00",
     "desc":"Feria de proyectos estudiantiles. Entrada libre, pabellón central.","prioridad":4},
    {"id":10007,"titulo":"Tarea: Ensayo — Ética en Ingeniería","categoria":"📚 Tarea",
     "fecha":_fecha(4),"hora_inicio":"23:59","hora_fin":"23:59",
     "desc":"Ensayo de 5 cuartillas sobre dilemas éticos en el desarrollo tecnológico.","prioridad":2},
    {"id":10008,"titulo":"Examen: Física II — Parcial 2","categoria":"📝 Examen",
     "fecha":_fecha(7),"hora_inicio":"08:00","hora_fin":"10:00",
     "desc":"Temas: Electromagnetismo, circuitos RC, ley de Faraday.","prioridad":1},
    {"id":10009,"titulo":"Proyecto: Avance 2 — App Móvil (equipo)","categoria":"📋 Proyecto",
     "fecha":_fecha(6),"hora_inicio":"09:00","hora_fin":"11:00",
     "desc":"Presentar prototipo funcional en Flutter/React Native.","prioridad":1},
    {"id":10010,"titulo":"🎓 Conferencia: IA aplicada a la Ingeniería","categoria":"🎓 Evento",
     "fecha":_fecha(8),"hora_inicio":"16:00","hora_fin":"18:00",
     "desc":"Ponencia del Dr. Martínez sobre aplicaciones de IA.","prioridad":4},
    {"id":10011,"titulo":"Práctica: Redes y Comunicaciones — Lab","categoria":"🧪 Práctica",
     "fecha":_fecha(9),"hora_inicio":"12:00","hora_fin":"14:00",
     "desc":"Configuración de routers y switches en Cisco Packet Tracer.","prioridad":2},
    {"id":10012,"titulo":"📢 Aviso: Entrega de constancias — Ventanilla","categoria":"📢 Aviso",
     "fecha":_fecha(0),"hora_inicio":"09:00","hora_fin":"14:00",
     "desc":"Entrega de constancias de estudio en ventanilla escolar.","prioridad":3},
]

EJEMPLO_CLASES = [
    {"id":20001,"titulo":"Clase: Programación Web — HTML/CSS","categoria":"📚 Estudio",
     "fecha":_fecha(0),"hora_inicio":"08:00","hora_fin":"10:00","desc":"Unidad 2: Diseño responsivo con Flexbox y Grid.","prioridad":3},
    {"id":20002,"titulo":"Clase: Cálculo Diferencial","categoria":"📚 Estudio",
     "fecha":_fecha(0),"hora_inicio":"10:00","hora_fin":"12:00","desc":"Derivadas implícitas y optimización.","prioridad":2},
    {"id":20007,"titulo":"Sesión Pomodoro: Repasar apuntes","categoria":"⭐ Personal",
     "fecha":_fecha(0),"hora_inicio":"15:00","hora_fin":"16:30","desc":"Repasar temas de Cálculo y Física.","prioridad":2},
    {"id":20008,"titulo":"Tarea: Ejercicios Álgebra Lineal","categoria":"📝 Tarea",
     "fecha":_fecha(0),"hora_inicio":"18:00","hora_fin":"20:00","desc":"Resolver ejercicios 3.1 al 3.8 del libro.","prioridad":1},
    {"id":20003,"titulo":"Clase: Física II — Electromagnetismo","categoria":"📚 Estudio",
     "fecha":_fecha(1),"hora_inicio":"13:00","hora_fin":"15:00","desc":"Ley de Faraday e inducción electromagnética.","prioridad":3},
    {"id":20006,"titulo":"Tarea: Mapa conceptual Física II","categoria":"📝 Tarea",
     "fecha":_fecha(1),"hora_inicio":"23:59","hora_fin":"23:59","desc":"Entregar mapa conceptual de Electromagnetismo.","prioridad":1},
    {"id":20009,"titulo":"Proyecto: Avance 1 — App Móvil","categoria":"📋 Proyecto",
     "fecha":_fecha(1),"hora_inicio":"16:00","hora_fin":"18:00","desc":"Presentar wireframes y diagrama de casos de uso.","prioridad":2},
    {"id":20004,"titulo":"Clase: Álgebra Lineal","categoria":"📚 Estudio",
     "fecha":_fecha(2),"hora_inicio":"09:00","hora_fin":"11:00","desc":"Transformaciones lineales, valores y vectores propios.","prioridad":3},
    {"id":20010,"titulo":"Práctica: Lab. Circuitos Eléctricos","categoria":"🧪 Práctica",
     "fecha":_fecha(2),"hora_inicio":"11:00","hora_fin":"13:00","desc":"Práctica 3: Circuitos RC y RL.","prioridad":2},
    {"id":20005,"titulo":"Clase: Inglés Técnico","categoria":"📚 Estudio",
     "fecha":_fecha(3),"hora_inicio":"07:00","hora_fin":"09:00","desc":"Unit 4: Technical writing and documentation.","prioridad":3},
    {"id":20011,"titulo":"Asesoría: Cálculo Diferencial","categoria":"⭐ Personal",
     "fecha":_fecha(3),"hora_inicio":"12:00","hora_fin":"13:00","desc":"Asesoría con el profesor para aclarar dudas.","prioridad":2},
    {"id":20012,"titulo":"Entrega: Reporte Práctica Química","categoria":"📝 Tarea",
     "fecha":_fecha(4),"hora_inicio":"08:00","hora_fin":"08:00","desc":"Subir reporte de la práctica 4 a Moodle.","prioridad":1},
    {"id":20013,"titulo":"Actividad: Lectura crítica cap. 5","categoria":"⭐ Personal",
     "fecha":_fecha(4),"hora_inicio":"20:00","hora_fin":"21:30","desc":"Leer y hacer resumen del capítulo 5 de Ingeniería de Software.","prioridad":3},
    {"id":20014,"titulo":"Estudio grupal: Examen Física II","categoria":"📚 Estudio",
     "fecha":_fecha(5),"hora_inicio":"10:00","hora_fin":"13:00","desc":"Sesión de estudio con el equipo.","prioridad":2},
    {"id":20015,"titulo":"Descanso programado 🌿","categoria":"⭐ Personal",
     "fecha":_fecha(6),"hora_inicio":"10:00","hora_fin":"12:00","desc":"Tiempo libre para recargar energía.","prioridad":4},
    {"id":20016,"titulo":"Clase: Redes y Comunicaciones","categoria":"📚 Estudio",
     "fecha":_fecha(3),"hora_inicio":"08:00","hora_fin":"10:00","desc":"Protocolos TCP/IP y modelo OSI.","prioridad":2},
    {"id":20017,"titulo":"Clase: Programación Orientada a Objetos","categoria":"📚 Estudio",
     "fecha":_fecha(4),"hora_inicio":"10:00","hora_fin":"12:00","desc":"Herencia, polimorfismo e interfaces.","prioridad":2},
    {"id":20018,"titulo":"Clase: Base de Datos Avanzadas","categoria":"📚 Estudio",
     "fecha":_fecha(5),"hora_inicio":"09:00","hora_fin":"11:00","desc":"Procedimientos almacenados y triggers en MySQL.","prioridad":2},
    {"id":20019,"titulo":"Clase: Sistemas Operativos","categoria":"📚 Estudio",
     "fecha":_fecha(6),"hora_inicio":"11:00","hora_fin":"13:00","desc":"Planificación de procesos y gestión de memoria.","prioridad":3},
    {"id":20020,"titulo":"⚽ Entrenamiento: Fútbol — Selección UAEMéx","categoria":"🏃 Deporte",
     "fecha":_fecha(0),"hora_inicio":"17:00","hora_fin":"19:00","desc":"Entrenamiento semanal del equipo.","prioridad":3},
    {"id":20021,"titulo":"🏀 Práctica: Basquetbol interescolar","categoria":"🏃 Deporte",
     "fecha":_fecha(1),"hora_inicio":"18:00","hora_fin":"20:00","desc":"Práctica para el torneo interescolar.","prioridad":3},
    {"id":20024,"titulo":"🏊 Natación: Clase semanal","categoria":"🏃 Deporte",
     "fecha":_fecha(4),"hora_inicio":"07:00","hora_fin":"08:00","desc":"Clase de natación en alberca universitaria.","prioridad":4},
    {"id":20027,"titulo":"🏃 Carrera: 5K Campus UAEMéx","categoria":"🏃 Deporte",
     "fecha":_fecha(7),"hora_inicio":"08:00","hora_fin":"10:00","desc":"Carrera recreativa de 5km dentro del campus.","prioridad":4},
    {"id":20030,"titulo":"🏐 Voleibol: Liga interna UAEMéx","categoria":"🏃 Deporte",
     "fecha":_fecha(2),"hora_inicio":"18:00","hora_fin":"20:00","desc":"Partido de la liga interna.","prioridad":3},
    {"id":20022,"titulo":"👥 Reunión: Comité estudiantil","categoria":"📋 Reunión",
     "fecha":_fecha(2),"hora_inicio":"13:00","hora_fin":"14:00","desc":"Reunión mensual del comité.","prioridad":2},
    {"id":20025,"titulo":"👥 Reunión de equipo: Proyecto App Móvil","categoria":"📋 Reunión",
     "fecha":_fecha(2),"hora_inicio":"14:00","hora_fin":"15:30","desc":"Revisión de avances del proyecto.","prioridad":2},
    {"id":20028,"titulo":"👥 Junta: Semana de bienvenida","categoria":"📋 Reunión",
     "fecha":_fecha(6),"hora_inicio":"12:00","hora_fin":"13:00","desc":"Organización de actividades para la semana de bienvenida.","prioridad":3},
    {"id":20031,"titulo":"👥 Reunión: Servicio social — Coordinación","categoria":"📋 Reunión",
     "fecha":_fecha(3),"hora_inicio":"09:00","hora_fin":"10:00","desc":"Reunión con el coordinador de servicio social.","prioridad":2},
    {"id":20023,"titulo":"🎤 Ensayo: Grupo de teatro universitario","categoria":"🎭 Cultural",
     "fecha":_fecha(3),"hora_inicio":"17:00","hora_fin":"19:00","desc":"Ensayo de la obra 'La vida es sueño'.","prioridad":3},
    {"id":20026,"titulo":"🎸 Taller: Música y bienestar estudiantil","categoria":"🎭 Cultural",
     "fecha":_fecha(5),"hora_inicio":"16:00","hora_fin":"17:30","desc":"Taller de música organizado por bienestar universitario.","prioridad":4},
    {"id":20029,"titulo":"🎨 Taller: Diseño UX/UI para apps","categoria":"🎭 Cultural",
     "fecha":_fecha(8),"hora_inicio":"15:00","hora_fin":"17:00","desc":"Taller extracurricular de diseño de interfaces.","prioridad":3},
    {"id":20032,"titulo":"📸 Taller: Fotografía digital","categoria":"🎭 Cultural",
     "fecha":_fecha(9),"hora_inicio":"14:00","hora_fin":"16:00","desc":"Taller de fotografía para proyectos universitarios.","prioridad":4},
]

def _sembrar_datos_ejemplo(file_key):
    """Carga datos de ejemplo solo si el archivo en disco no existe o está vacío.
    Comprueba el archivo directamente para evitar que una caché vacía
    confunda datos inexistentes con datos ya existentes."""
    # Global: solo sembrar si el archivo físico no existe o está vacío
    if not os.path.exists(GLOBAL_FILE):
        guardar_global(EJEMPLO_GLOBAL)
    else:
        try:
            with open(GLOBAL_FILE, "r", encoding="utf-8") as f:
                datos_disco = json.load(f)
            if not datos_disco:
                guardar_global(EJEMPLO_GLOBAL)
        except Exception as e:
            logging.warning("_sembrar_datos_ejemplo: no se pudo leer global – %s", e)

    # Personal: solo sembrar si el archivo físico no existe o está vacío
    arch_personal = _file_personal(file_key)
    if not os.path.exists(arch_personal):
        guardar_personal(file_key, EJEMPLO_CLASES)
    else:
        try:
            with open(arch_personal, "r", encoding="utf-8") as f:
                datos_disco = json.load(f)
            if not datos_disco:
                guardar_personal(file_key, EJEMPLO_CLASES)
        except Exception as e:
            logging.warning("_sembrar_datos_ejemplo(%s): no se pudo leer personal – %s", file_key, e)
