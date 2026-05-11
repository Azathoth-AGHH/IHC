# ╔══════════════════════════════════════════════════════════════════╗
# ║  notification_manager.py — Notificaciones del sistema + campana  ║
# ╚══════════════════════════════════════════════════════════════════╝
import threading, time, platform
import tkinter as tk
import customtkinter as ctk
from datetime import datetime, timedelta
from ui_theme import C, FS

# ── Sonido de campana suave (cross-platform) ─────────────────────
def _play_bell(root_widget=None):
    """Reproduce campana suave. Usa TK bell como fallback universal."""
    try:
        if platform.system() == "Windows":
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        elif platform.system() == "Darwin":
            import subprocess
            subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            # Linux: paplay / pacat o bell de tk
            try:
                import subprocess
                subprocess.Popen(["paplay", "/usr/share/sounds/freedesktop/stereo/bell.oga"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                if root_widget:
                    root_widget.bell()
    except Exception:
        try:
            if root_widget:
                root_widget.bell()
        except Exception:
            pass


# ── Toast flotante ────────────────────────────────────────────────
class _Toast:
    """Ventana de notificación estilo toast que aparece en la esquina."""
    _queue: list = []
    _showing: bool = False
    _root = None

    @classmethod
    def show(cls, titulo: str, cuerpo: str, icono: str = "🔔",
             duracion_ms: int = 4500, color: str | None = None):
        cls._queue.append((titulo, cuerpo, icono, duracion_ms, color))
        if not cls._showing:
            cls._dequeue()

    @classmethod
    def _dequeue(cls):
        if not cls._queue:
            cls._showing = False
            return
        cls._showing = True
        titulo, cuerpo, icono, dur, color = cls._queue.pop(0)
        cls._create(titulo, cuerpo, icono, dur, color)

    @classmethod
    def _create(cls, titulo, cuerpo, icono, dur, color):
        try:
            root = cls._root
            if root is None or not root.winfo_exists():
                cls._showing = False
                return

            accent = color or C("accent")
            win = tk.Toplevel(root)
            win.overrideredirect(True)
            win.attributes("-topmost", True)
            win.configure(bg=C("surface"))

            # Tamaño y posición — más grande, esquina superior derecha
            W, H = 400, 120
            sw = root.winfo_screenwidth()
            sh = root.winfo_screenheight()
            x  = sw - W - 24
            y0 = -H          # empieza arriba fuera de vista
            y1 = 24          # destino: esquina superior derecha

            win.geometry(f"{W}x{H}+{x}+{y0}")

            # Sombra simulada (frame oscuro detrás)
            try:
                win.attributes("-alpha", 0.97)
            except Exception:
                pass

            # Borde de acento izquierdo más grueso
            tk.Frame(win, bg=accent, width=7).pack(side="left", fill="y")

            # Banda de color superior (mini header de acento)
            outer = tk.Frame(win, bg=C("surface"))
            outer.pack(fill="both", expand=True)

            header = tk.Frame(outer, bg=accent, height=8)
            header.pack(fill="x")

            ctn = tk.Frame(outer, bg=C("surface"), padx=14, pady=10)
            ctn.pack(fill="both", expand=True)

            # Fila de título
            top_row = tk.Frame(ctn, bg=C("surface"))
            top_row.pack(fill="x")
            tk.Label(top_row, text=f"{icono}  {titulo}",
                     font=("Helvetica", 13, "bold"),
                     fg=C("text"), bg=C("surface"), anchor="w").pack(side="left")
            tk.Button(top_row, text="✕", font=("Helvetica", 11),
                      fg=C("text2"), bg=C("surface"), relief="flat",
                      cursor="hand2", bd=0,
                      command=win.destroy).pack(side="right")

            # Cuerpo más grande
            tk.Label(ctn, text=cuerpo, font=("Helvetica", 11),
                     fg=C("text2"), bg=C("surface"),
                     anchor="w", wraplength=W - 50, justify="left").pack(fill="x", pady=(4, 0))

            # Barra de progreso (se vacía en dur_ms)
            pb_bg = tk.Frame(ctn, bg=C("border"), height=4)
            pb_bg.pack(fill="x", pady=(8, 0))
            pb_fg = tk.Frame(pb_bg, bg=accent, height=4)
            pb_fg.place(x=0, y=0, relwidth=1, relheight=1)

            def _shrink_bar(steps=60, elapsed=0):
                try:
                    if not win.winfo_exists():
                        return
                    pct = max(0, 1 - elapsed / dur)
                    pb_fg.place_configure(relwidth=pct)
                    if elapsed < dur:
                        win.after(dur // steps, lambda: _shrink_bar(steps, elapsed + dur // steps))
                except Exception:
                    pass

            # Animación slide-down (desde arriba)
            def _slide(y_cur=y0, speed=20):
                try:
                    if not win.winfo_exists():
                        return
                    ny = min(y_cur + speed, y1)
                    win.geometry(f"{W}x{H}+{x}+{ny}")
                    if ny < y1:
                        win.after(12, lambda: _slide(ny, speed))
                    else:
                        _shrink_bar()
                        win.after(dur, lambda: _fade(win))
                except Exception:
                    pass

            def _fade(w, alpha=1.0):
                try:
                    if not w.winfo_exists():
                        cls._dequeue(); return
                    if alpha <= 0:
                        w.destroy()
                        cls._dequeue()
                        return
                    try:
                        w.attributes("-alpha", alpha)
                    except Exception:
                        pass
                    w.after(40, lambda: _fade(w, alpha - 0.08))
                except Exception:
                    cls._dequeue()

            win.after(10, _slide)

        except Exception:
            cls._showing = False


# ── Motor de notificaciones ───────────────────────────────────────
class NotificationManager:
    """
    Daemon que monitorea actividades y lanza notificaciones del sistema
    con sonido de campana suave.
    """
    _instance: "NotificationManager | None" = None

    def __init__(self, root_widget, file_key: str):
        self._root      = root_widget
        self._file_key  = file_key
        self._running   = False
        self._thread: threading.Thread | None = None
        self._notified: set = set()   # IDs ya notificados en esta sesión
        _Toast._root = root_widget
        NotificationManager._instance = self

    # ── API pública ──────────────────────────────────────────────
    def start(self):
        """Inicia el hilo de monitoreo en background."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    @staticmethod
    def notify(titulo: str, cuerpo: str, icono: str = "🔔",
               color: str | None = None, ring: bool = True,
               root=None):
        """Lanza una notificación desde cualquier parte del código."""
        r = root or _Toast._root
        if ring:
            _play_bell(r)
        if r:
            r.after(0, lambda: _Toast.show(titulo, cuerpo, icono, color=color))

    # ── Loop interno (hilo daemon) ───────────────────────────────
    def _loop(self):
        time.sleep(3)   # espera inicial
        while self._running:
            try:
                self._check()
            except Exception:
                pass
            time.sleep(60)   # chequea cada minuto

    def _check(self):
        from local_db import cargar_personal, cargar_global
        from event_daemon import EventDaemon
        ahora   = datetime.now()
        hoy_str = ahora.strftime("%Y-%m-%d")
        hora_str = ahora.strftime("%H:%M")
        personal = cargar_personal(self._file_key)
        global_  = cargar_global()
        todas    = personal + global_

        # ── EventDaemon: alertas de proximidad (URGENTE / PREPARACION) ──
        try:
            agenda_con_fecha = [
                {**a, "fecha_entrega": f"{a['fecha']} {a.get('hora_fin','23:59')}",
                 "titulo": a.get("titulo",""), "id": a.get("id","")}
                for a in todas if a.get("fecha") and a.get("hora_fin")
            ]
            daemon = EventDaemon(agenda_con_fecha)
            for alerta in daemon.monitorear_proximidad():
                key_daemon = f"daemon_{alerta['tipo']}_{alerta['id']}"
                if key_daemon not in self._notified:
                    self._notified.add(key_daemon)
                    if alerta["tipo"] == "URGENTE":
                        self._post("🚨  ¡Entrega urgente!", alerta["msj"], "🚨", C("red"))
                    else:
                        self._post("⏰  Recordatorio", alerta["msj"], "⏰", C("amber"))
        except Exception:
            pass

        for a in todas:
            aid     = a.get("id", a.get("titulo",""))
            fecha   = a.get("fecha","")
            titulo  = a.get("titulo","Sin título")
            hora_ini = a.get("hora_inicio","")
            hora_fin = a.get("hora_fin","")
            cat      = a.get("categoria","")
            prio     = a.get("prioridad", 0)

            # ── Clase a punto de comenzar (15 min antes) ────────
            key_cls = f"clase_inicio_{aid}"
            if fecha == hoy_str and hora_ini and key_cls not in self._notified:
                try:
                    t_ini = datetime.strptime(f"{fecha} {hora_ini}", "%Y-%m-%d %H:%M")
                    diff  = (t_ini - ahora).total_seconds() / 60
                    if 0 <= diff <= 15:
                        self._notified.add(key_cls)
                        self._post("🏫  Clase próxima",
                                   f"«{titulo}» comienza en {int(diff)} min",
                                   "🏫", C("teal"))
                except Exception:
                    pass

            # ── Tarea a punto de cerrar (1 hora antes) ──────────
            key_close = f"tarea_cierre_{aid}"
            if fecha == hoy_str and hora_fin and key_close not in self._notified:
                try:
                    t_fin = datetime.strptime(f"{fecha} {hora_fin}", "%Y-%m-%d %H:%M")
                    diff  = (t_fin - ahora).total_seconds() / 60
                    if 0 < diff <= 60:
                        self._notified.add(key_close)
                        self._post("⏰  Entrega próxima",
                                   f"«{titulo}» cierra a las {hora_fin}",
                                   "⏰", C("amber"))
                except Exception:
                    pass

            # ── Tarea urgente (vence mañana o hoy sin completar) ─
            key_urg = f"urgente_{aid}"
            if fecha and key_urg not in self._notified:
                try:
                    t_vence = datetime.strptime(fecha, "%Y-%m-%d")
                    dias_restantes = (t_vence.date() - ahora.date()).days
                    if 0 <= dias_restantes <= 1 and any(k in cat for k in ("Tarea","Examen","Proyecto","Práctica")):
                        self._notified.add(key_urg)
                        etiq = "¡Hoy!" if dias_restantes == 0 else "Mañana"
                        self._post("🚨  Tarea urgente",
                                   f"«{titulo}» vence {etiq}. ¡No olvides entregarlo!",
                                   "🚨", C("red") if dias_restantes == 0 else C("amber"))
                except Exception:
                    pass

        # ── Reinscripciones (ejemplo basado en fecha) ────────────
        key_rei = "reinscripcion_2026"
        if key_rei not in self._notified:
            # Periodo de reinscripción de ejemplo: mayo
            if ahora.month == 5 and ahora.day == 1:
                self._notified.add(key_rei)
                self._post("📋  ¡Reinscripción abierta!",
                           "El periodo de reinscripción acaba de comenzar. Revisa tu horario.",
                           "📋", C("accent"))

    def _post(self, titulo: str, cuerpo: str, icono: str, color: str):
        """Encola notificación en el hilo de UI."""
        r = self._root
        if r:
            r.after(0, lambda: NotificationManager.notify(
                titulo, cuerpo, icono, color=color, ring=True, root=r))

    # ── Disparo manual (cuando se guarda una tarea nueva) ────────
    @classmethod
    def on_tarea_nueva(cls, titulo: str, root=None):
        NotificationManager.notify(
            "✅  Nueva tarea agregada",
            f"«{titulo}» fue añadida a tus actividades.",
            "✅", color=C("green"), ring=True, root=root or _Toast._root)

    @classmethod
    def on_reinscripcion_abierta(cls, root=None):
        NotificationManager.notify(
            "📋  ¡Reinscripción abierta!",
            "Ya puedes seleccionar tus materias para el siguiente semestre.",
            "📋", color=C("accent"), ring=True, root=root or _Toast._root)
