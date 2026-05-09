# ╔══════════════════════════════════════════════════════════════════╗
# ║  dialogs.py — Diálogos: Actividad, Comandos de Voz, Lector       ║
# ╚══════════════════════════════════════════════════════════════════╝
import time, threading, uuid
import customtkinter as ctk
import tkinter as tk
from datetime import datetime
from ui_theme import C, FS, PREFS
from ui_components import Btn, BtnOutline
from local_db import CATEGORIAS_PERSONAL
from academic_engine import AcademicEngine

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

        # ── Fecha — selección por día/mes/año ──
        self._lbl(form, "Fecha")
        fecha_actual = act.get("fecha", datetime.now().strftime("%Y-%m-%d"))
        try:
            _fd = datetime.strptime(fecha_actual, "%Y-%m-%d")
            _dia_val, _mes_val, _anio_val = str(_fd.day), str(_fd.month), str(_fd.year)
        except Exception:
            _fd = datetime.now()
            _dia_val, _mes_val, _anio_val = str(_fd.day), str(_fd.month), str(_fd.year)

        fecha_row = ctk.CTkFrame(form, fg_color="transparent")
        fecha_row.pack(fill="x", pady=(4,12))
        fecha_row.columnconfigure((0,1,2), weight=1)

        _dias = [str(d) for d in range(1,32)]
        _NOMBRES_MES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                        "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
        _meses = [f"{i+1} - {m}" for i, m in enumerate(_NOMBRES_MES)]
        _anio_actual = datetime.now().year
        _anios = [str(y) for y in range(_anio_actual, _anio_actual+3)]

        ctk.CTkLabel(fecha_row, text="Día", font=("Helvetica",FS("small"),"bold"),
            text_color=C("text2")).grid(row=0, column=0, sticky="w", padx=(0,4))
        ctk.CTkLabel(fecha_row, text="Mes", font=("Helvetica",FS("small"),"bold"),
            text_color=C("text2")).grid(row=0, column=1, sticky="w", padx=(4,4))
        ctk.CTkLabel(fecha_row, text="Año", font=("Helvetica",FS("small"),"bold"),
            text_color=C("text2")).grid(row=0, column=2, sticky="w", padx=(4,0))

        self._om_dia = ctk.CTkOptionMenu(fecha_row, values=_dias, height=40, corner_radius=10,
            fg_color=C("surface"), text_color=C("text"),
            button_color=C("accent"), button_hover_color=C("accent_dark"),
            font=("Helvetica",FS("small")))
        self._om_dia.set(_dia_val)
        self._om_dia.grid(row=1, column=0, sticky="ew", padx=(0,4), pady=(2,0))

        self._om_mes = ctk.CTkOptionMenu(fecha_row, values=_meses, height=40, corner_radius=10,
            fg_color=C("surface"), text_color=C("text"),
            button_color=C("accent"), button_hover_color=C("accent_dark"),
            font=("Helvetica",FS("small")))
        _mes_idx = int(_mes_val) - 1
        self._om_mes.set(_meses[_mes_idx] if 0 <= _mes_idx < 12 else _meses[0])
        self._om_mes.grid(row=1, column=1, sticky="ew", padx=(4,4), pady=(2,0))

        self._om_anio = ctk.CTkOptionMenu(fecha_row, values=_anios, height=40, corner_radius=10,
            fg_color=C("surface"), text_color=C("text"),
            button_color=C("accent"), button_hover_color=C("accent_dark"),
            font=("Helvetica",FS("small")))
        self._om_anio.set(_anio_val if _anio_val in _anios else _anios[0])
        self._om_anio.grid(row=1, column=2, sticky="ew", padx=(4,0), pady=(2,0))

        # ── Hora inicio / fin — selección por OptionMenu ──
        _HORAS = [f"{h:02d}:{m:02d}" for h in range(6,23) for m in (0,30)]
        hrow = ctk.CTkFrame(form, fg_color="transparent")
        hrow.pack(fill="x", pady=(0,12))
        hrow.columnconfigure((0,1), weight=1)

        lef = ctk.CTkFrame(hrow, fg_color="transparent")
        lef.grid(row=0, column=0, sticky="ew", padx=(0,6))
        self._lbl(lef, "Hora inicio")
        _ini_val = act.get("hora_inicio", "09:00")
        _HORAS_ini = _HORAS if _ini_val in _HORAS else [_ini_val] + _HORAS
        self.e_ini = ctk.CTkOptionMenu(lef, values=_HORAS_ini, height=42, corner_radius=12,
            fg_color=C("surface"), text_color=C("text"),
            button_color=C("accent"), button_hover_color=C("accent_dark"),
            font=("Helvetica",FS("body")))
        self.e_ini.set(_ini_val)
        self.e_ini.pack(fill="x", pady=(4,0))

        rig = ctk.CTkFrame(hrow, fg_color="transparent")
        rig.grid(row=0, column=1, sticky="ew", padx=(6,0))
        self._lbl(rig, "Hora fin")
        _fin_val = act.get("hora_fin", "10:00")
        _HORAS_fin = _HORAS if _fin_val in _HORAS else [_fin_val] + _HORAS
        self.e_fin = ctk.CTkOptionMenu(rig, values=_HORAS_fin, height=42, corner_radius=12,
            fg_color=C("surface"), text_color=C("text"),
            button_color=C("accent"), button_hover_color=C("accent_dark"),
            font=("Helvetica",FS("body")))
        self.e_fin.set(_fin_val)
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

        try:
            _dia  = int(self._om_dia.get())
            _mes  = int(self._om_mes.get().split(" - ")[0])
            _anio = int(self._om_anio.get())
            fecha = f"{_anio:04d}-{_mes:02d}-{_dia:02d}"
        except Exception:
            fecha = datetime.now().strftime("%Y-%m-%d")
        hora_ini = self.e_ini.get() or "09:00"
        hora_fin = self.e_fin.get() or "10:00"

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
            "id":          str(uuid.uuid4()),
            "prioridad":   prioridad,
        })
        self.destroy()

# ─────────────────────────────────────────────────────────────────
#  SIDEBAR (colapsable — diseño moderno)
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

    @classmethod
    def rescanear_panel(cls, delay_ms: int = 350):
        """Limpia el cursor/resaltado actual y re-escanea la UI tras cambiar de panel.
        Puede llamarse desde cualquier parte sin referencia directa a la instancia."""
        inst = cls._instancia
        if inst is None or not getattr(inst, "_activo", False):
            return
        inst._idx = 0
        # Quitar resaltado anterior de forma segura (el widget puede ya no existir)
        if inst._resaltado:
            try:
                if inst._resaltado.winfo_exists():
                    inst._resaltado.configure(border_width=0)
            except Exception:
                pass
            inst._resaltado = None
        # Quitar cursor flotante
        if getattr(inst, "_cursor_lbl", None):
            try:
                if inst._cursor_lbl.winfo_exists():
                    inst._cursor_lbl.destroy()
            except Exception:
                pass
            inst._cursor_lbl = None
        try:
            inst._root.after(delay_ms, inst._escanear)
        except Exception:
            pass

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
        # Quitar resaltado (el widget puede ya no existir)
        if self._resaltado:
            try:
                if self._resaltado.winfo_exists():
                    self._resaltado.configure(border_width=0)
            except Exception:
                pass
            self._resaltado = None
        # Quitar indicador de cursor
        if getattr(self, "_cursor_lbl", None):
            try:
                if self._cursor_lbl.winfo_exists():
                    self._cursor_lbl.destroy()
            except Exception:
                pass
            self._cursor_lbl = None
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
        "configuracion":("Ajustes",  "Abrir configuración"),
        "configuración":("Ajustes",  "Abrir configuración"),
    }

    # Solo para Estudiante
    COMANDOS_EST = {
        "agenda":          ("Mi Agenda",      "Ver tu agenda semanal"),
        "mi agenda":       ("Mi Agenda",      "Ver tu agenda semanal"),
        "actividades":     ("Actividades",    "Ver tus actividades y tareas"),
        "tareas":          ("Actividades",    "Ver tus tareas pendientes"),
        "mis actividades": ("Actividades",    "Ver tus actividades"),
        "pomodoro":        ("Pomodoro",       "Iniciar temporizador Pomodoro"),
        "temporizador":    ("Pomodoro",       "Iniciar temporizador Pomodoro"),
        "timer":           ("Pomodoro",       "Iniciar temporizador Pomodoro"),
        "logros":          ("Logros",         "Ver tus logros y progreso"),
        "mis logros":      ("Logros",         "Ver tus logros y progreso"),
        "estadísticas":    ("Logros",         "Ver estadísticas personales"),
        "estadisticas":    ("Logros",         "Ver estadísticas personales"),
        "reinscripcion":   ("Reinscripción",  "Ver panel de reinscripción"),
        "reinscripción":   ("Reinscripción",  "Ver panel de reinscripción"),
        "inscripcion":     ("Reinscripción",  "Ver panel de reinscripción"),
        "inscripción":     ("Reinscripción",  "Ver panel de reinscripción"),
    }

    # Solo para Administrativo
    COMANDOS_ADM = {
        "tareas globales":  ("Tareas globales", "Gestionar tareas para todos los alumnos"),
        "tareas":           ("Tareas globales", "Ver tareas globales"),
        "global":           ("Tareas globales", "Ver tareas globales"),
        "reportes":         ("Reportes",        "Ver reportes académicos"),
        "ver reportes":     ("Reportes",        "Abrir panel de reportes"),
        "reporte":          ("Reportes",        "Ver reportes académicos"),
        "alumnos":          ("Alumnos",         "Gestionar lista de alumnos"),
        "ver alumnos":      ("Alumnos",         "Ver listado de alumnos"),
        "estudiantes":      ("Alumnos",         "Gestionar lista de alumnos"),
        "horarios":         ("Horarios",        "Ver y editar horarios de clases"),
        "ver horarios":     ("Horarios",        "Abrir gestión de horarios"),
        "horario":          ("Horarios",        "Ver y editar horarios de clases"),
        "clases":           ("Clases",          "Gestionar clases registradas"),
        "ver clases":       ("Clases",          "Abrir panel de clases"),
        "clase":            ("Clases",          "Gestionar clases registradas"),
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

            # Normalizar: minúsculas + quitar tildes para comparación robusta
            import unicodedata
            def _normalizar(s):
                return ''.join(
                    c for c in unicodedata.normalize('NFD', s.lower())
                    if unicodedata.category(c) != 'Mn'
                )
            texto_norm = _normalizar(texto)

            # Buscar comando más largo que coincida primero (evita falsos positivos)
            encontrado_tab = None
            mejor_clave = ""
            for clave, (tab, _) in self.COMANDOS.items():
                clave_norm = _normalizar(clave)
                if clave_norm in texto_norm and len(clave_norm) > len(mejor_clave):
                    encontrado_tab = tab
                    mejor_clave = clave_norm

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
            def _navegar(t=tab):
                try:
                    # Soltar el grab ANTES de navegar para que la ventana principal
                    # recupere el foco sin bloqueos
                    self.grab_release()
                except Exception:
                    pass
                try:
                    self.on_cmd(t)
                except Exception:
                    pass
                # Destruir el diálogo después de ceder el control, no antes
                try:
                    self.after(80, self.destroy)
                except Exception:
                    pass
            self.after(600, _navegar)



# ─────────────────────────────────────────────────────────────────
#  PANEL: AJUSTES
# ─────────────────────────────────────────────────────────────────
