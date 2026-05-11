# ╔══════════════════════════════════════════════════════════════════╗
# ║           OPTEM · Agenda Virtual Inteligente UAEMéx             ║
# ║           Punto de entrada principal (v2.0)                     ║
# ╚══════════════════════════════════════════════════════════════════╝
#
# Estructura de módulos:
#   ui_theme.py       — Preferencias, colores (C), fuentes (FS)
#   ui_images.py      — Carga de imágenes, avatares, ondas decorativas
#   ui_components.py  — Card, Btn, BtnOutline, SectionHeader, StatBadge, EventoRow
#   local_db.py       — Base de datos JSON local, categorías, datos de ejemplo
#   dialogs.py        — DialogoActividad, LectorPantalla, DialogoVozCmd
#   sidebar.py        — Sidebar colapsable
#   panels_student.py — PanelInicioEst, PanelActividades, PanelAgendaSemanal,
#                       PanelPomodoro, PanelLogros
#   panels_admin.py   — PanelInicioAdmin, PanelTareasGlobales, PanelReportes,
#                       PanelAlumnos, PanelClasesAdmin, PanelHorarios
#   panels_common.py  — PanelAjustes
#   screens.py        — VentanaPrincipal, PantallaCarga, PantallaLogin
#
# Módulos externos (ya existían):
#   auth_manager.py, data_bridge.py, config_manager.py,
#   session_manager.py, academic_engine.py, validator_engine.py,
#   event_daemon.py, productivity_manager.py

import logging
import sys
import customtkinter as ctk
from tkinter import messagebox

# ── Verificación de dependencias ──────────────────────────────────
def _verificar_dependencias():
    """Verifica que las librerías necesarias estén instaladas antes de arrancar."""
    faltantes = []
    try:
        import customtkinter  # noqa: F401
    except ImportError:
        faltantes.append("customtkinter")
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        faltantes.append("Pillow")
    if faltantes:
        import tkinter as _tk
        root = _tk.Tk(); root.withdraw()
        _tk.messagebox.showerror(
            "Dependencias faltantes",
            f"Las siguientes librerías no están instaladas:\n\n"
            + "\n".join(f"  • {lib}" for lib in faltantes)
            + "\n\nInstálalas con:\n  pip install " + " ".join(faltantes)
        )
        sys.exit(1)

_verificar_dependencias()

logging.basicConfig(
    filename="optem_errors.log",
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(module)s – %(message)s",
    encoding="utf-8",
)

from ui_theme        import PREFS
from local_db        import (cargar_global, guardar_global, EJEMPLO_GLOBAL,
                              _sembrar_datos_ejemplo,
                              invalidar_cache_global, invalidar_cache_personal)
from screens         import VentanaPrincipal, PantallaCarga, PantallaLogin
from data_bridge     import DataBridge
from session_manager import cargar_sesion


class OptemApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Optem · Agenda Virtual Inteligente — UAEMéx")
        self.geometry("1280x780")
        self.minsize(960, 620)
        ctk.set_appearance_mode("dark" if PREFS["dark_mode"] else "light")
        ctk.set_default_color_theme("green")
        self._screen = None
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._mostrar_splash()

    def _on_close(self):
        """Cierra la ventana con confirmación si hay un Pomodoro activo."""
        if self._pomodoro_activo():
            if not messagebox.askyesno(
                "Pomodoro activo",
                "Tienes un Pomodoro en curso.\n¿Deseas salir de todas formas?",
                icon="warning"
            ):
                return
        self.destroy()

    def _pomodoro_activo(self) -> bool:
        """Devuelve True si algún PanelPomodoro tiene el timer corriendo."""
        try:
            from panels_student import PanelPomodoro
            for widget in self.winfo_children():
                for child in widget.winfo_children():
                    if isinstance(child, PanelPomodoro) and getattr(child, "_on", False):
                        return True
        except Exception:
            pass
        return False

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
                self._entrar(sesion["rol"], sesion["file_key"], sesion.get("correo", ""))
                return
            except Exception:
                pass
        try:
            self._set(PantallaLogin(self, self._entrar))
        except Exception as e:
            messagebox.showerror("Error al iniciar",
                                 f"No se pudo cargar la pantalla de inicio:\n{e}")

    def _entrar(self, rol, file_key, correo=""):
        # Invalidar caché al cambiar de usuario para no mezclar datos entre sesiones
        invalidar_cache_global()
        invalidar_cache_personal()
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
