"""
session_manager.py — Mantiene la sesión abierta entre reinicios.
"""
import json, os

_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_FILE = os.path.join(_DIR, "optem_session.json")

def guardar_sesion(correo: str, rol: str, file_key: str):
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump({"correo": correo, "rol": rol, "file_key": file_key, "activa": True}, f)

def cargar_sesion():
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if d.get("activa") else None
    except Exception:
        return None

def cerrar_sesion():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            d["activa"] = False
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(d, f)
        except Exception:
            pass
