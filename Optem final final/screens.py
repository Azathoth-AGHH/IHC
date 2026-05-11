# ╔══════════════════════════════════════════════════════════════════╗
# ║  screens.py — Pantallas principales: Principal, Carga, Login     ║
# ╚══════════════════════════════════════════════════════════════════╝
import logging
import math, time, tkinter as tk
import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox
from ui_theme import C, FS, PREFS, _darken
from ui_images import load_logo, load_uaem_logo, make_wave, load_img_rounded
from ui_components import Btn, BtnOutline
from sidebar import Sidebar
from dialogs import LectorPantalla
from panels_student import (PanelInicioEst, PanelActividades,
                             PanelAgendaSemanal, PanelPomodoro, PanelLogros,
                             PanelReinscripcion)
from panels_admin import (PanelInicioAdmin, PanelTareasGlobales,
                          PanelReportes, PanelAlumnos, PanelClasesAdmin,
                          PanelHorarios)
from panels_common import PanelAjustes
from auth_manager import AuthManager
from session_manager import guardar_sesion
from notification_manager import NotificationManager

class VentanaPrincipal(ctk.CTkFrame):
    def __init__(self, parent, rol, datos, file_key, correo):
        super().__init__(parent, fg_color=C("bg"))
        self.rol      = rol
        self.datos    = datos
        self.file_key = file_key
        self.correo   = correo
        self.parent   = parent
        self._panel   = None
        self._autostart_pom = False
        self._build()

    def _consume_autostart_pom(self):
        """Devuelve True una sola vez si se solicitó autostart de Pomodoro."""
        val = self._autostart_pom
        self._autostart_pom = False
        return val

    def ir_pomodoro_autostart(self):
        """Navega a la pestaña Pomodoro e inicia el timer automáticamente."""
        self._autostart_pom = True
        self.sidebar.set_active("Pomodoro")

    def _build(self):
        # ── IMPORTANTE: self.area debe existir ANTES de crear el Sidebar,
        # porque Sidebar._build() llama _select() al final, lo que dispara
        # on_tab → _switch(), que necesita self.area para mostrar el panel.
        self.area = ctk.CTkFrame(self, fg_color=C("bg"), corner_radius=0)

        # Registrar esta instancia en el toplevel para acceso desde sub-panels
        try:
            self.winfo_toplevel()._app_screen = self
        except Exception:
            pass

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

        # ── NotificationManager (solo para Estudiante) ────────────
        if self.rol == "Estudiante":
            try:
                self._notif_mgr = NotificationManager(self.parent, self.file_key)
                self._notif_mgr.start()
            except Exception:
                self._notif_mgr = None

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
        tabs_est = ["Inicio","Mi Agenda","Actividades","Pomodoro","Logros","Reinscripción","Ajustes"]
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
                "Pomodoro":    lambda: PanelPomodoro(self.area, self.file_key, self.datos,
                                                      autostart=self._consume_autostart_pom()),
                "Logros":      lambda: PanelLogros(self.area, self.datos),
                "Reinscripción": lambda: PanelReinscripcion(self.area, self.file_key),
                "Ajustes":     lambda: PanelAjustes(self.area, self.parent, self.correo,
                                                      rol=self.rol, file_key=self.file_key),
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
                "Ajustes":         lambda: PanelAjustes(self.area, self.parent, self.correo,
                                                         rol=self.rol, file_key=self.file_key),
            }

        builder = panels.get(nombre)
        if builder:
            try:
                # ── Barra de carga mientras se construye el panel ──────────
                _overlay = ctk.CTkFrame(self.area, fg_color=C("bg"))
                _overlay.place(x=0, y=0, relwidth=1, relheight=1)
                _overlay.lift()
                _pb_bg = ctk.CTkFrame(_overlay, fg_color=C("border"), height=4, corner_radius=2)
                _pb_bg.place(relx=0, rely=0, relwidth=1)
                _pb_fill = ctk.CTkFrame(_pb_bg, fg_color=C("accent"), height=4, corner_radius=2)
                _pb_fill.place(x=0, y=0, relwidth=0, relheight=1)
                _pb_lbl = ctk.CTkLabel(_overlay, text=f"Cargando {nombre}...",
                    font=("Helvetica", 11), text_color=C("text3"))
                _pb_lbl.place(relx=0.5, rely=0.5, anchor="center")
                self.area.update_idletasks()

                # Animar la barra en steps hasta 80%
                _steps = 8
                def _advance_bar(step=0):
                    try:
                        if not _pb_fill.winfo_exists():
                            return
                        pct = min(0.8, (step + 1) / _steps)
                        _pb_fill.place_configure(relwidth=pct)
                        if step < _steps - 1:
                            _pb_fill.after(30, lambda: _advance_bar(step + 1))
                    except Exception:
                        pass
                _advance_bar()
                self.area.update()

                p = builder()
                p.pack(fill="both", expand=True)
                self._panel = p

                # Completar barra y quitar overlay con fade-in del panel
                try:
                    _pb_fill.place_configure(relwidth=1)
                    self.area.update_idletasks()
                except Exception:
                    pass

                # Animación de entrada: fade-in via alpha si es posible, si no slide
                def _fade_in_panel(alpha=0.0):
                    try:
                        if not p.winfo_exists():
                            return
                        if alpha < 1.0:
                            p.lift()
                            p.after(16, lambda: _fade_in_panel(min(alpha + 0.15, 1.0)))
                        else:
                            try:
                                _overlay.destroy()
                            except Exception:
                                pass
                    except Exception:
                        try:
                            _overlay.destroy()
                        except Exception:
                            pass

                p.after(40, _fade_in_panel)
                self.area.update_idletasks()

                # Re-escanear el lector de pantalla si está activo
                if PREFS.get("screen_reader"):
                    LectorPantalla.rescanear_panel(delay_ms=400, nombre_panel=nombre)
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
        self._after_ids: list = []
        self._bar_aid   = None   # ID actual del loop de barra (no crece en lista)
        self._dots_aid  = None
        self._orbs_aid  = None
        self._build()

    def destroy(self):
        for aid in self._after_ids:
            try:
                self.after_cancel(aid)
            except Exception as e:
                logging.warning("PantallaCarga.destroy: after_cancel falló – %s", e)
        self._after_ids.clear()
        for attr in ('_bar_aid', '_dots_aid', '_orbs_aid'):
            aid = getattr(self, attr, None)
            if aid:
                try: self.after_cancel(aid)
                except Exception as e: logging.warning("PantallaCarga.destroy: %s falló – %s", attr, e)
        super().destroy()

    def _build(self):
        # ── Fondo con círculos decorativos animados (canvas) ─────
        self._canvas = tk.Canvas(self, bg=C("bg"), highlightthickness=0)
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # Dibujar orbs estáticos iniciales
        orb_data = [
            (0.15, 0.20, 180, "#C18D52",   30),
            (0.80, 0.15, 120, "#A3743E",   20),
            (0.70, 0.80, 200, "#96CDB0",   25),
            (0.10, 0.75, 140, "#5A8F76",   20),
            (0.50, 0.10, 90,  "#203B37",   15),
            (0.90, 0.55, 100, "#5A8F76",   18),
        ]
        self._orb_specs = orb_data
        self._orb_phases = [i * 0.9 for i in range(len(orb_data))]
        # Los orbs se dibujan en _animate_orbs cuando el canvas tenga tamaño

        # ── Centro ───────────────────────────────────────────────
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.place(relx=0.5, rely=0.5, anchor="center")

        # Logo con fondo accent
        _splash_logo = load_logo(size=(96, 96), radius=26)
        _uaem_logo   = load_uaem_logo(size=(72, 72))

        logos_row = ctk.CTkFrame(center, fg_color="transparent")
        logos_row.pack(pady=(0, 4))

        if _uaem_logo:
            ctk.CTkLabel(logos_row, image=_uaem_logo, text="",
                         fg_color="transparent").pack(side="left", padx=(0, 16))

        if _splash_logo:
            self._logo_lbl = ctk.CTkLabel(logos_row, image=_splash_logo, text="")
            self._logo_lbl.pack(side="left")
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
        self._after_ids.append(self.after(100, self._animate_bar))
        self._after_ids.append(self.after(200, self._animate_dots))
        self._after_ids.append(self.after(300, self._animate_orbs))

    def _animate_bar(self):
        if not self.winfo_exists(): return
        self._bar_val = min(self._bar_val + 0.012, 1.0)
        try:
            self._bar_fill.configure(width=int(280 * self._bar_val))
        except Exception as e:
            logging.warning("PantallaCarga._animate_bar: configure falló – %s", e)
        if self._bar_val < 1.0:
            self._bar_aid = self.after(40, self._animate_bar)

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
        self._dots_aid = self.after(340, self._animate_dots)

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
                self._orbs_aid = self.after(100, self._animate_orbs); return
            t = time.time() * 0.6
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
        self._orbs_aid = self.after(100, self._animate_orbs)


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
        self._after_ids: list = []
        self._bg_aid    = None   # ID actual del loop bg (no crece en lista)
        self._lorbs_aid = None
        self._logo_aid  = None
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=3)
        self.rowconfigure(0, weight=1)
        self._build()

    def destroy(self):
        for aid in self._after_ids:
            try:
                self.after_cancel(aid)
            except Exception as e:
                logging.warning("PantallaLogin.destroy: after_cancel falló – %s", e)
        self._after_ids.clear()
        for attr in ('_bg_aid', '_lorbs_aid', '_logo_aid'):
            aid = getattr(self, attr, None)
            if aid:
                try: self.after_cancel(aid)
                except Exception as e: logging.warning("PantallaLogin.destroy: %s falló – %s", attr, e)
        super().destroy()

    def _build(self):
        # ── Canvas de fondo con partículas/orbs animadas ─────────
        self._canvas = tk.Canvas(self, bg=C("bg"), highlightthickness=0)
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._orb_specs = [
            (0.08, 0.12, 220, "#C18D52",   "gray25"),
            (0.85, 0.08, 160, "#A3743E",   "gray25"),
            (0.78, 0.88, 240, "#96CDB0",   "gray25"),
            (0.05, 0.82, 170, "#5A8F76",   "gray25"),
            (0.45, 0.05, 110, "#203B37",   "gray12"),
            (0.92, 0.50, 130, "#5A8F76",   "gray12"),
            (0.55, 0.92, 150, "#96CDB0",   "gray12"),
            (0.30, 0.60, 90,  "#C18D52",   "gray12"),
        ]
        self._after_ids.append(self.after(200, self._animate_bg))

        # ── Lado izquierdo: branding ──────────────────────────────
        left = ctk.CTkFrame(self, fg_color="#203B37", corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew")

        # Canvas para orbs animados en panel izquierdo (verde oscuro)
        self._left_canvas = tk.Canvas(left, bg="#203B37", highlightthickness=0)
        self._left_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._left_orb_specs = [
            (0.10, 0.10, 150, "#96CDB0", "gray50"),
            (0.82, 0.12, 110, "#EEE8B2", "gray25"),
            (0.75, 0.82, 170, "#5A8F76", "gray50"),
            (0.12, 0.78, 120, "#C18D52", "gray25"),
            (0.50, 0.04,  75, "#EEE8B2", "gray12"),
            (0.94, 0.48, 100, "#96CDB0", "gray50"),
            (0.38, 0.96, 130, "#5A8F76", "gray25"),
            (0.60, 0.50,  60, "#EEE8B2", "gray12"),
        ]
        self._left_orb_phases = [i * 1.25 for i in range(8)]
        self._after_ids.append(self.after(300, self._animate_left_orbs))

        lc = ctk.CTkFrame(left, fg_color="transparent")
        lc.place(relx=0.5, rely=0.5, anchor="center")

        # Logo animado (bounce + pulse)
        self._logo_raw = None
        _logo = load_logo(size=(80, 80))
        _uaem = load_uaem_logo(size=(64, 64))
        logos_fr = ctk.CTkFrame(lc, fg_color="#D6EDD4", corner_radius=18)
        logos_fr.pack(pady=(0, 10), padx=10, ipadx=12, ipady=8)
        if _uaem:
            ctk.CTkLabel(logos_fr, image=_uaem, text="",
                         fg_color="transparent").pack(side="left", padx=(0, 12))
        if _logo:
            self._logo_widget = ctk.CTkLabel(logos_fr, image=_logo, text="",
                                              fg_color="transparent")
            self._logo_widget.pack(side="left")
        else:
            logo_box = ctk.CTkFrame(lc, fg_color="white", width=100, height=100,
                                    corner_radius=28)
            logo_box.pack(pady=(0, 18)); logo_box.pack_propagate(False)
            ctk.CTkLabel(logo_box, text="OP", font=("Helvetica",34,"bold"),
                         text_color=C("accent")).place(relx=.5,rely=.5,anchor="center")
            self._logo_widget = logo_box
        self._animate_logo()

        ctk.CTkLabel(lc, text="OPTEM",
            font=("Helvetica", 40, "bold"), text_color="#EEE8B2").pack()
        ctk.CTkLabel(lc, text="Agenda Virtual Inteligente",
            font=("Helvetica", 14), text_color="#96CDB0").pack(pady=(4, 2))
        ctk.CTkFrame(lc, fg_color="#5A8F76", height=1, width=180).pack(pady=(0, 22))

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

        # Imagen decorativa en el login (derecha)
        _login_deco = load_img_rounded("mienar", size=(340, 100), radius=14)
        if _login_deco:
            ctk.CTkLabel(form, image=_login_deco, text="",
                         fg_color="transparent").pack(fill="x", pady=(0, 14))

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
            except Exception as e: logging.warning("PantallaLogin._hide_ac_login: destroy falló – %s", e)
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
            self._logo_aid = self.after(2000, self._animate_logo)  # 2s: cálculo sin efecto visual real
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
                self._bg_aid = self.after(100, self._animate_bg)
                return
            t = time.time() * 0.5
            self._canvas.delete("orb")
            for i, (rx, ry, r, col, stip) in enumerate(self._orb_specs):
                phase = self._orb_phases[i]
                ox = rx * W + math.sin(t + phase) * 35
                oy = ry * H + math.cos(t * 0.65 + phase) * 28
                self._canvas.create_oval(
                    ox-r, oy-r, ox+r, oy+r,
                    fill=col, outline="", tags="orb", stipple=stip)
            self._bg_aid = self.after(100, self._animate_bg)
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
                self._lorbs_aid = self.after(100, self._animate_left_orbs)
                return
            t = time.time() * 0.45
            self._left_canvas.delete("lorb")
            for i, (rx, ry, r, col, stip) in enumerate(self._left_orb_specs):
                phase = self._left_orb_phases[i]
                ox = rx * W + math.sin(t + phase) * 32
                oy = ry * H + math.cos(t * 0.65 + phase) * 26
                self._left_canvas.create_oval(
                    ox-r, oy-r, ox+r, oy+r,
                    fill=col, outline="", tags="lorb", stipple=stip)
            self._lorbs_aid = self.after(100, self._animate_left_orbs)
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
