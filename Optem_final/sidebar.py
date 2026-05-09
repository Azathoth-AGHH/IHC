# ╔══════════════════════════════════════════════════════════════════╗
# ║  sidebar.py — Sidebar colapsable con navegación                  ║
# ╚══════════════════════════════════════════════════════════════════╝
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageDraw
from ui_theme import C, FS, PREFS, save_prefs
from ui_images import load_logo, load_uaem_logo, load_img_rounded, make_wave
from dialogs import DialogoVozCmd

class Sidebar(ctk.CTkFrame):
    TABS_EST = [("🏠", "Inicio"),     ("📅", "Mi Agenda"),
                ("🎯", "Actividades"),("⏱",  "Pomodoro"),
                ("⭐", "Logros"),      ("📋", "Reinscripción"),
                ("⚙️", "Ajustes")]
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
        self._anim_after_id = None   # ID del after() activo para cancelar si se destruye
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
        self._add_tooltip(self._btn_ham, "Abrir/cerrar menú")

        # Logo pequeño de OPTEM junto al título
        _optem_top = load_logo(size=(24, 24))
        if _optem_top:
            self._optem_top_lbl = ctk.CTkLabel(
                self._topbar, image=_optem_top, text="", fg_color="transparent")
            self._optem_top_lbl.place(x=60, rely=0.5, anchor="w")
            self._lbl_app = ctk.CTkLabel(
                self._topbar, text="OPTEM",
                font=("Helvetica", 15, "bold"), text_color=C("text"))
            self._lbl_app.place(x=90, rely=0.5, anchor="w")
        else:
            self._optem_top_lbl = None
            self._lbl_app = ctk.CTkLabel(
                self._topbar, text="OPTEM",
                font=("Helvetica", 15, "bold"), text_color=C("text"))
            self._lbl_app.place(x=64, rely=0.5, anchor="w")

        # Separador
        ctk.CTkFrame(self, fg_color=C("border"), height=1).pack(fill="x")

        # — Bloque hero: logo arriba, perfil abajo —
        self._hero = ctk.CTkFrame(self, fg_color=C("accent"), corner_radius=0)
        self._hero.pack(fill="x")

        # Onda decorativa (colocada al fondo, no interfiere con pack)
        _hw = make_wave(self.W_OPEN, 28, C("accent_dark"), 80)
        self._hero_wave_lbl = ctk.CTkLabel(
            self._hero, image=_hw, text="", fg_color="transparent")
        self._hero_wave_lbl.place(x=0, rely=1.0, anchor="sw")

        # — Fila 1: Logo UAEMéx + texto —
        self._logo_row = ctk.CTkFrame(self._hero, fg_color="transparent")
        self._logo_row.pack(fill="x", padx=10, pady=(10, 4))

        _uaem_sm = load_uaem_logo(size=(48, 48))
        self._uaem_lbl = None
        if _uaem_sm:
            self._uaem_lbl = ctk.CTkLabel(
                self._logo_row, image=_uaem_sm, text="", fg_color="transparent")
            self._uaem_lbl.pack(side="left")

        # Guardar referencia ANTES de pack para no depender de winfo_children
        self._uaem_txt_lbl = ctk.CTkLabel(self._logo_row, text="UAEMéx",
            font=("Helvetica", 14, "bold"), text_color="white",
            fg_color="transparent")
        self._uaem_txt_lbl.pack(side="left", padx=(8, 0))

        # — Separador interno —
        ctk.CTkFrame(self._hero, fg_color="#AACCBB", height=1).pack(
            fill="x", padx=10, pady=(2, 6))

        # — Fila 2: Avatar + badge de rol —
        self._profile_row = ctk.CTkFrame(self._hero, fg_color="transparent")
        self._profile_row.pack(fill="x", padx=10, pady=(0, 12))

        self._avatar_size = 40
        self._avatar_img  = None
        self._avatar_path = PREFS.get("avatar_path", "")
        self._avatar_btn  = ctk.CTkButton(
            self._profile_row,
            width=self._avatar_size, height=self._avatar_size,
            corner_radius=self._avatar_size // 2,
            fg_color=C("accent_dark"), hover_color=C("accent_dark"),
            text="", border_width=2, border_color="white",
            command=self._pick_avatar)
        self._avatar_btn.pack(side="left")
        self._refresh_avatar()
        self._add_tooltip(self._avatar_btn, "Cambiar foto de perfil")

        # Badge de rol (visible solo con sidebar abierta)
        _rol_ico = "🏛️" if rol == "Administrativo" else "🎓"
        _rol_txt = "Admin" if rol == "Administrativo" else "Estudiante"
        self._hero_txt = ctk.CTkFrame(self._profile_row, fg_color="transparent")
        self._hero_txt.pack(side="left", padx=(8, 0))

        self._hero_badge = ctk.CTkFrame(
            self._hero_txt, fg_color=C("accent_dark"), corner_radius=6)
        self._hero_badge.pack(anchor="w")
        ctk.CTkLabel(self._hero_badge,
            text=f"{_rol_ico} {_rol_txt}",
            font=("Helvetica", 9, "bold"), text_color="white"
            ).pack(padx=6, pady=3)

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
            # Tooltip visible solo cuando la sidebar está cerrada
            self._add_tooltip(btn, f"{ico} {nombre}")

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

        # — Indicador de reinscripción (solo admins) —
        if rol == "Administrativo":
            reinsc_on = PREFS.get("reinscripcion_activa", False)
            _ri_color = C("green") if reinsc_on else C("red")
            _ri_text  = "🟢 Reinscripción ABIERTA" if reinsc_on else "🔴 Reinscripción CERRADA"
            self._reinsc_frame = ctk.CTkFrame(self, fg_color="transparent",
                                              corner_radius=8, height=36)
            self._reinsc_frame.pack(side="bottom", fill="x", padx=10, pady=(0, 6))
            self._reinsc_frame.pack_propagate(False)
            self._reinsc_pill = ctk.CTkFrame(self._reinsc_frame, fg_color=_ri_color,
                                             corner_radius=8, height=36)
            self._reinsc_pill.pack(fill="x")
            self._reinsc_pill.pack_propagate(False)
            self._reinsc_lbl = ctk.CTkLabel(self._reinsc_pill,
                text=_ri_text, font=("Helvetica", 8, "bold"), text_color="white")
            self._reinsc_lbl.place(relx=0.5, rely=0.5, anchor="center")

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

    # ── Tooltip helper ───────────────────────────────────────────
    def _add_tooltip(self, widget, text: str):
        """Muestra un tooltip flotante al pasar el cursor sobre el widget."""
        tip_win = None

        def _show(event=None):
            nonlocal tip_win
            if tip_win:
                return
            x = widget.winfo_rootx() + widget.winfo_width() + 8
            y = widget.winfo_rooty() + widget.winfo_height() // 2 - 14
            tip_win = tk.Toplevel(widget)
            tip_win.wm_overrideredirect(True)
            tip_win.wm_geometry(f"+{x}+{y}")
            tip_win.attributes("-topmost", True)
            frame = tk.Frame(tip_win, bg="#222", padx=8, pady=4,
                             highlightthickness=1, highlightbackground="#444")
            frame.pack()
            tk.Label(frame, text=text, fg="white", bg="#222",
                     font=("Helvetica", 10)).pack()

        def _hide(event=None):
            nonlocal tip_win
            if tip_win:
                tip_win.destroy()
                tip_win = None

        widget.bind("<Enter>", _show)
        widget.bind("<Leave>", _hide)

    # ── Avatar de perfil ──────────────────────────────────────────
    def _refresh_avatar(self):
        """Actualiza el avatar: foto circular si hay path, o iniciales."""
        size = self._avatar_size
        path = PREFS.get("avatar_path", "")
        try:
            if path:
                from PIL import Image as PILImage
                img = PILImage.open(path).convert("RGBA").resize((size, size))
                # Máscara circular
                mask = PILImage.new("L", (size, size), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
                result = PILImage.new("RGBA", (size, size), (0, 0, 0, 0))
                result.paste(img, mask=mask)
                self._avatar_img = ctk.CTkImage(light_image=result,
                                                dark_image=result,
                                                size=(size, size))
                self._avatar_btn.configure(image=self._avatar_img, text="",
                                           fg_color="transparent",
                                           hover_color=C("accent_dark"))
            else:
                raise ValueError("no path")
        except Exception:
            # Fallback: iniciales con fondo de acento
            self._avatar_img = None
            self._avatar_btn.configure(image="", text="👤",
                                       font=("Helvetica", 20),
                                       fg_color=C("accent_dark"),
                                       text_color="white")

    def _pick_avatar(self):
        """Abre diálogo para elegir foto de perfil."""
        path = filedialog.askopenfilename(
            title="Selecciona tu foto de perfil",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.webp *.gif"),
                       ("Todos", "*.*")])
        if path:
            PREFS["avatar_path"] = path
            save_prefs(PREFS)
            self._refresh_avatar()

    # ── Limpieza segura ───────────────────────────────────────────
    def destroy(self):
        """Cancela cualquier callback de animación pendiente antes de destruir."""
        if self._anim_after_id is not None:
            try:
                self.after_cancel(self._anim_after_id)
            except Exception:
                pass
            self._anim_after_id = None
        self._animating = False
        super().destroy()

    # ── Toggle con animación suave ────────────────────────────────
    def _toggle(self):
        if self._animating:
            return
        self._animating = True
        self._open = not self._open
        target = self.W_OPEN if self._open else self.W_CLOSED
        if not self._open:
            self._on_close_sidebar()
        self._animate(target)

    def _on_close_sidebar(self):
        """Oculta textos al colapsar."""
        self._lbl_app.place_forget()
        if hasattr(self, "_uaem_txt_lbl"):
            self._uaem_txt_lbl.pack_forget()
        self._hero_txt.pack_forget()
        self._sec_lbl.configure(text="")
        if self._deco_lbl:
            self._deco_lbl.pack_forget()
        self._ver_lbl.configure(text="")
        for nombre, (btn, pill, ico, label) in self._btns.items():
            btn.configure(text=f" {ico}", anchor="center")
            btn.place(x=4, y=1, relwidth=0.92, relheight=0.95)

    def _on_open_sidebar(self):
        """Restaura textos al expandir."""
        self._lbl_app.place(x=64, rely=0.5, anchor="w")
        if hasattr(self, "_uaem_txt_lbl"):
            self._uaem_txt_lbl.pack(side="left", padx=(8, 0))
        self._hero_txt.pack(side="left", padx=(8, 0))
        self._sec_lbl.configure(text="  MENÚ")
        if self._deco_lbl:
            self._deco_lbl.pack(side="bottom", pady=(0, 8), padx=10)
        self._ver_lbl.configure(text="v2.0 · UAEMéx 2025")
        for nombre, (btn, pill, ico, label) in self._btns.items():
            btn.configure(text=f"  {ico}   {label}", anchor="w")
            btn.place(x=8, y=1, relwidth=1, relheight=0.95)

    def _animate(self, target):
        diff = target - self._cur_w
        step = int(diff * 0.35)
        if step == 0:
            step = 8 if diff > 0 else -8
        self._cur_w += step
        if (diff > 0 and self._cur_w >= target) or (diff < 0 and self._cur_w <= target):
            self._cur_w = target
            self._animating = False
            if self._open:
                self._on_open_sidebar()
        self.configure(width=self._cur_w)
        if self._animating:
            self._anim_after_id = self.after(16, lambda: self._animate(target))

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
        """Abre el diálogo de comandos de voz usando el callback de navegación del sidebar."""
        DialogoVozCmd(self, self.on_tab, rol=getattr(self, "_rol", "Estudiante"))
# ─────────────────────────────────────────────────────────────────
#  PANEL: INICIO ESTUDIANTE
# ─────────────────────────────────────────────────────────────────
