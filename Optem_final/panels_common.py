# ╔══════════════════════════════════════════════════════════════════╗
# ║  panels_common.py — PanelAjustes (compartido por ambos roles)    ║
# ╚══════════════════════════════════════════════════════════════════╝
import customtkinter as ctk
from tkinter import messagebox
from ui_theme import C, FS, PREFS, save_prefs, _darken
from ui_components import Card, Btn, BtnOutline
from dialogs import DialogoVozCmd, LectorPantalla
from session_manager import cerrar_sesion

class PanelAjustes(ctk.CTkScrollableFrame):
    def __init__(self, parent, app_ref, correo="", rol="Estudiante", file_key="", **kw):
        super().__init__(parent, fg_color=C("bg"),
                         scrollbar_button_color=C("accent"), **kw)
        self.app_ref  = app_ref
        self.correo   = correo
        self.rol      = rol
        self.file_key = file_key
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
        for col in ["#5A8F76","#9B8DFF","#FF6B9D","#1ABC9C","#F39C12","#E74C3C","#3498DB","#2ECC71"]:
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

        # ── Número de cuenta (solo 7 dígitos numéricos) ──────────
        rn = ctk.CTkFrame(cc, fg_color="transparent")
        rn.pack(fill="x", padx=18, pady=(12,4))
        ctk.CTkLabel(rn, text="🎓  Número de cuenta",
            font=("Helvetica",FS("body"),"bold"),
            text_color=C("text")).pack(side="left")

        # Cargar valor guardado
        _nc_actual = ""
        if self.file_key:
            try:
                from data_bridge import DataBridge as _DB
                _d = _DB(self.file_key).cargar_datos() or {}
                _nc_actual = _d.get("perfil", {}).get("numero_cuenta", "")
            except Exception:
                pass

        nc_frame = ctk.CTkFrame(rn, fg_color="transparent")
        nc_frame.pack(side="right")
        self._nc_entry = ctk.CTkEntry(nc_frame, width=120, height=36, corner_radius=10,
            font=("Helvetica", FS("body")),
            fg_color=C("surface2"), text_color=C("text"),
            border_color=C("border"), border_width=1,
            placeholder_text="7 dígitos")
        if _nc_actual:
            self._nc_entry.insert(0, _nc_actual)
        self._nc_entry.pack(side="left", padx=(0,6))

        # Botón guardar número
        Btn(nc_frame, text="💾", width=38, height=36,
            command=self._guardar_numero_cuenta).pack(side="left")

        self._nc_msg = ctk.CTkLabel(cc, text="", font=("Helvetica",FS("small")),
            text_color=C("green"))
        self._nc_msg.pack(padx=18, anchor="w", pady=(0,4))

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
                    _msg = "Lector de pantalla activado. Usa las flechas para navegar."
                    inst._hablar(_msg)
                    for delay in (800, 2000, 4000):
                        root.after(delay, lambda m=_msg: inst._hablar(m))
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
        """Abre el diálogo de comandos de voz buscando el sidebar de forma robusta."""
        on_cmd = None
        try:
            # Ruta directa: app_ref → _screen (VentanaPrincipal) → sidebar
            screen = getattr(self.app_ref, "_screen", None)
            if screen and hasattr(screen, "sidebar"):
                on_cmd = screen.sidebar.set_active
        except Exception:
            pass
        if on_cmd is None:
            # Ruta alternativa: escalar por master hasta encontrar VentanaPrincipal
            try:
                w = self
                for _ in range(20):
                    if hasattr(w, "sidebar") and hasattr(w.sidebar, "set_active"):
                        on_cmd = w.sidebar.set_active
                        break
                    w = getattr(w, "master", None) or getattr(w, "_parent", None)
                    if w is None:
                        break
            except Exception:
                pass
        if on_cmd is None:
            on_cmd = lambda _: None
        DialogoVozCmd(self, on_cmd, rol=getattr(self, "rol", "Estudiante"))

    def _cerrar_sesion(self):
        if messagebox.askyesno("Cerrar sesión",
            "¿Seguro que quieres cerrar sesión?\nDeberás iniciar sesión la próxima vez."):
            cerrar_sesion()
            self.app_ref.volver_a_login()

    def _guardar_numero_cuenta(self):
        """Valida y guarda el número de cuenta (exactamente 7 dígitos numéricos)."""
        val = self._nc_entry.get().strip()
        # Validación: exactamente 7 dígitos, solo números
        if not val.isdigit():
            self._nc_entry.configure(border_color=C("red"), border_width=2)
            self._nc_msg.configure(
                text="❌ Solo se permiten números", text_color=C("red"))
            return
        if len(val) != 7:
            self._nc_entry.configure(border_color=C("red"), border_width=2)
            self._nc_msg.configure(
                text=f"❌ Debe tener exactamente 7 dígitos (tienes {len(val)})",
                text_color=C("red"))
            return
        # Guardar
        try:
            from data_bridge import DataBridge as _DB
            db   = _DB(self.file_key)
            data = db.cargar_datos() or {}
            data.setdefault("perfil", {})["numero_cuenta"] = val
            db.guardar_datos(data)
            self._nc_entry.configure(border_color=C("green"), border_width=2)
            self._nc_msg.configure(text="✅ Número de cuenta guardado", text_color=C("green"))
        except Exception as e:
            self._nc_msg.configure(text=f"⚠ Error al guardar: {e}", text_color=C("amber"))

# ─────────────────────────────────────────────────────────────────
#  PANELES ADMINISTRATIVO
# ─────────────────────────────────────────────────────────────────
