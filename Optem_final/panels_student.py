# ╔══════════════════════════════════════════════════════════════════╗
# ║  panels_student.py — Paneles de la vista Estudiante              ║
# ╚══════════════════════════════════════════════════════════════════╝
import logging
import time, threading, uuid
import customtkinter as ctk
import tkinter as tk
from datetime import datetime, timedelta, date
from tkinter import messagebox
import random
from ui_theme import C, FS, PREFS, _darken
from ui_images import load_img_rounded, make_wave
from ui_components import Card, Btn, BtnOutline
from local_db import (cargar_personal, guardar_personal, cargar_global,
                      CATEGORIAS_PERSONAL)
from dialogs import DialogoActividad
from academic_engine import AcademicEngine
from event_daemon import EventDaemon
from productivity_manager import ProductivityManager
from data_bridge import DataBridge
from notification_manager import NotificationManager

class PanelInicioEst(ctk.CTkScrollableFrame):
    def __init__(self, parent, datos, file_key, on_tab):
        super().__init__(parent, fg_color=C("bg"), scrollbar_button_color=C("accent"))
        self.datos    = datos
        self.file_key = file_key
        self.on_tab   = on_tab
        self._after_ids: list = []   # todos los IDs de after() para cancelarlos al destruir
        self._clock_after = None     # ID del reloj en vivo (se sobreescribe cada tick)
        self._build()

    def destroy(self):
        """Cancela todos los timers activos antes de destruir el frame."""
        for aid in self._after_ids:
            try:
                self.after_cancel(aid)
            except Exception as e:
                logging.warning("PanelInicioEst.destroy: after_cancel falló – %s", e)
        self._after_ids.clear()
        if self._clock_after:
            try: self.after_cancel(self._clock_after)
            except Exception as e: logging.warning("PanelInicioEst.destroy: clock_after falló – %s", e)
        super().destroy()

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
            ("lofi_desk",   "📝  notas",    "Mis apuntes y resúmenes",  "Actividades"),
            ("cozy_desk",   "📅  agenda",   "Horario y actividades",    "Mi Agenda"),
            ("green_nook",  "🎯  tareas",   "Pendientes y proyectos",   "Actividades"),
            ("chemistry",   "⭐  logros",   "XP, rachas y niveles",     "Logros"),
            ("study_mot",   "⏱  pomodoro", "Sesiones de estudio",      "Pomodoro"),
            ("notion_grn",  "🔗  recursos", "Links y materiales",       "Actividades"),
        ]
        # 3 columnas x 2 filas
        for row_i in range(2):
            row_fr = ctk.CTkFrame(gal_frame, fg_color="transparent")
            row_fr.pack(fill="x", pady=4)
            row_fr.columnconfigure((0,1,2), weight=1)
            for col_i in range(3):
                idx = row_i * 3 + col_i
                if idx >= len(_gal_data): break
                key, label, sub, tab_dest = _gal_data[idx]
                card = ctk.CTkFrame(row_fr, fg_color=C("surface"), corner_radius=14,
                    cursor="hand2")
                card.grid(row=0, column=col_i, padx=5, sticky="ew")
                card.bind("<Enter>", lambda e, c=card: c.configure(fg_color=C("surface2")))
                card.bind("<Leave>", lambda e, c=card: c.configure(fg_color=C("surface")))
                card.bind("<Button-1>", lambda e, t=tab_dest: self.on_tab(t))
                inner = ctk.CTkFrame(card, fg_color="transparent")
                inner.pack(fill="both", expand=True)
                inner.bind("<Button-1>", lambda e, t=tab_dest: self.on_tab(t))
                # Lazy load: crea el label vacío y carga la imagen diferido
                img_lbl = ctk.CTkLabel(inner, image=None, text="")
                img_lbl.pack(fill="x", padx=0, pady=0)
                img_lbl.bind("<Button-1>", lambda e, t=tab_dest: self.on_tab(t))
                def _lazy(lbl=img_lbl, k=key):
                    gi = load_img_rounded(k, size=(220, 120), radius=10)
                    if gi and lbl.winfo_exists():
                        lbl.configure(image=gi)
                self.after(60, _lazy)
                lbl_widget = ctk.CTkLabel(inner, text=label,
                    font=("Helvetica", FS("body"), "bold"), text_color=C("text"),
                    anchor="w")
                lbl_widget.pack(fill="x", padx=10, pady=(6,0))
                lbl_widget.bind("<Button-1>", lambda e, t=tab_dest: self.on_tab(t))
                sub_widget = ctk.CTkLabel(inner, text=sub,
                    font=("Helvetica", FS("small")), text_color=C("text2"),
                    anchor="w")
                sub_widget.pack(fill="x", padx=10, pady=(0,8))
                sub_widget.bind("<Button-1>", lambda e, t=tab_dest: self.on_tab(t))

        # ── Currently... sidebar-style widget ───────────────────
        curr_row = ctk.CTkFrame(self, fg_color="transparent")
        curr_row.pack(fill="x", padx=20, pady=(0,12))
        curr_row.columnconfigure(0, weight=3); curr_row.columnconfigure(1, weight=2)

        curr_card = Card(curr_row)
        curr_card.grid(row=0, column=1, sticky="nsew")

        # Encabezado con botón de edición
        curr_hdr = ctk.CTkFrame(curr_card, fg_color="transparent")
        curr_hdr.pack(fill="x", padx=14, pady=(12, 4))
        ctk.CTkLabel(curr_hdr, text="✨  currently...",
            font=("Helvetica", FS("small"), "bold"),
            text_color=C("accent")).pack(side="left")
        ctk.CTkButton(curr_hdr, text="✏️", width=28, height=24, corner_radius=6,
            fg_color=C("surface2"), hover_color=C("border"),
            text_color=C("text2"), font=("Helvetica", 11),
            command=lambda: self._editar_currently(curr_card)
            ).pack(side="right")

        hora_act = datetime.now().hour
        _defaults = {
            "musica":    "lo-fi hip hop 🎵" if 6 <= hora_act < 22 else "ambient chill 🌙",
            "leyendo":   "Ingeniería de Software cap. 5",
            "trabajando": "Proyecto App Móvil",
            "bebiendo":  "café con leche",
        }
        curr_data = self.datos.get("perfil", {}).get("currently", _defaults)

        self._curr_labels: dict = {}
        _items_curr = [
            ("🎵 listening to:", "musica"),
            ("📖 leyendo:",       "leyendo"),
            ("💻 trabajando en:", "trabajando"),
            ("☕ bebiendo:",      "bebiendo"),
        ]
        for ico_txt, key in _items_curr:
            rw = ctk.CTkFrame(curr_card, fg_color="transparent")
            rw.pack(fill="x", padx=14, pady=2)
            ctk.CTkLabel(rw, text=ico_txt, font=("Helvetica", FS("small")),
                text_color=C("text2"), anchor="w").pack(side="left")
            lbl = ctk.CTkLabel(rw, text=curr_data.get(key, _defaults.get(key, "")),
                font=("Helvetica", FS("small"), "bold"),
                text_color=C("text"), anchor="e")
            lbl.pack(side="right")
            self._curr_labels[key] = lbl
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
            self._clock_after = self.after(1000, self._tick_clock)  # sobreescribe, no acumula
        except Exception:
            pass

    def _pulse_label(self, lbl, col_a, col_b, _state=True):
        """Alterna el color de un label para efecto pulso. Se detiene si el widget fue destruido."""
        try:
            if not lbl.winfo_exists():
                return
            lbl.configure(text_color=col_a if _state else col_b)
            # Sobreescribir en el widget (no acumular en _after_ids)
            lbl._pulse_aid = lbl.after(800, lambda: self._pulse_label(lbl, col_a, col_b, not _state))
        except Exception as e:
            logging.warning("_pulse_label: widget destruido o error inesperado – %s", e)

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

    def _editar_currently(self, _parent_card=None):
        """Diálogo para editar el widget 'currently...' con persistencia."""
        top = ctk.CTkToplevel(self)
        top.title("Editar — currently...")
        top.geometry("420x310")
        top.configure(fg_color=C("bg"))
        top.grab_set(); top.lift(); top.focus_force()

        ctk.CTkLabel(top, text="✨  Edita tu estado actual",
            font=("Helvetica", FS("h3"), "bold"),
            text_color=C("accent")).pack(padx=24, pady=(18, 2), anchor="w")
        ctk.CTkLabel(top, text="Los cambios se guardan en tu perfil",
            font=("Helvetica", FS("small")), text_color=C("text2")).pack(padx=24, anchor="w")

        hora_act = datetime.now().hour
        _defaults = {
            "musica":    "lo-fi hip hop 🎵" if 6 <= hora_act < 22 else "ambient chill 🌙",
            "leyendo":   "Ingeniería de Software cap. 5",
            "trabajando": "Proyecto App Móvil",
            "bebiendo":  "café con leche",
        }
        curr = self.datos.get("perfil", {}).get("currently", _defaults)

        entries: dict = {}
        _fields = [
            ("🎵 Escuchando:",   "musica"),
            ("📖 Leyendo:",      "leyendo"),
            ("💻 Trabajando en:","trabajando"),
            ("☕ Bebiendo:",     "bebiendo"),
        ]
        form = ctk.CTkFrame(top, fg_color="transparent")
        form.pack(fill="x", padx=24, pady=(12, 0))
        for lbl_txt, key in _fields:
            r = ctk.CTkFrame(form, fg_color="transparent")
            r.pack(fill="x", pady=4)
            ctk.CTkLabel(r, text=lbl_txt, font=("Helvetica", FS("small"), "bold"),
                text_color=C("text"), width=130, anchor="w").pack(side="left")
            e = ctk.CTkEntry(r, height=34, corner_radius=8,
                fg_color=C("surface"), text_color=C("text"),
                border_color=C("border"), border_width=1,
                font=("Helvetica", FS("small")))
            e.insert(0, curr.get(key, _defaults.get(key, "")))
            e.pack(side="left", fill="x", expand=True)
            entries[key] = e

        def _guardar():
            nueva = {k: e.get().strip() or _defaults.get(k,"") for k, e in entries.items()}
            self.datos.setdefault("perfil", {})["currently"] = nueva
            try:
                DataBridge(self.file_key).guardar_datos(self.datos)
            except Exception:
                pass
            # Actualizar labels en vivo
            for k, lbl in getattr(self, "_curr_labels", {}).items():
                try:
                    if lbl.winfo_exists():
                        lbl.configure(text=nueva.get(k, ""))
                except Exception:
                    pass
            top.destroy()

        br = ctk.CTkFrame(top, fg_color="transparent")
        br.pack(pady=14)
        from ui_components import Btn, BtnOutline
        Btn(br, text="💾  Guardar", width=140, command=_guardar).pack(side="left", padx=6)
        BtnOutline(br, text="Cancelar", width=100, command=top.destroy).pack(side="left", padx=6)

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
            "id": str(uuid.uuid4()),
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
        # Aumentar racha y registrar XP via ProductivityManager
        try:
            from productivity_manager import ProductivityManager
            db = DataBridge(self.file_key)
            datos = db.cargar_datos() or {}
            perfil = datos.get("perfil", {})
            # Normalizar campos necesarios para ProductivityManager
            if "racha" not in perfil:
                perfil["racha"] = 0
            if "xp" not in perfil:
                perfil["xp"] = 0
            if "nivel" not in perfil:
                perfil["nivel"] = "Novato"
            perfil["racha"] = int(str(perfil["racha"]).replace("🔥", "").strip() or 0)
            pm = ProductivityManager(perfil)
            pm.registrar_entrega_exitosa(puntual=True, dificultad="media")
            # perfil fue modificado in-place por ProductivityManager
            datos["perfil"] = perfil
            db.guardar_datos(datos)
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
        # Notificación del sistema
        try:
            root = self.winfo_toplevel()
            NotificationManager.on_tarea_nueva(nueva.get("titulo","Nueva tarea"), root=root)
        except Exception:
            pass
        self._refresh()

# ─────────────────────────────────────────────────────────────────
#  PANEL: AGENDA SEMANAL
# ─────────────────────────────────────────────────────────────────
class PanelAgendaSemanal(ctk.CTkFrame):
    DIAS = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]

    def __init__(self, parent, file_key, **kw):
        super().__init__(parent, fg_color=C("bg"), **kw)
        self.file_key       = file_key
        self._offset        = 0
        self._vista         = "semana"   # "semana" | "mes" | "dia"
        self._dia_offset    = 0          # días desde hoy para vista día
        self._refresh_after = None
        self._vista_btns: dict = {}
        self._build()

    def destroy(self):
        if self._refresh_after:
            try: self.after_cancel(self._refresh_after)
            except Exception as e: logging.warning("PanelAgendaSemanal.destroy: after_cancel falló – %s", e)
        super().destroy()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=C("surface"), corner_radius=0, height=70)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ih = ctk.CTkFrame(hdr, fg_color="transparent")
        ih.pack(fill="both", expand=True, padx=24, pady=14)
        ctk.CTkLabel(ih, text="📅  Mi Agenda",
                     font=("Helvetica",FS("h2"),"bold"), text_color=C("text")).pack(side="left")

        # ── Toggle de vista ───────────────────────────────────────
        tgl = ctk.CTkFrame(ih, fg_color=C("surface2"), corner_radius=10)
        tgl.pack(side="left", padx=18)
        for v_key, v_lbl in [("dia","📆 Día"), ("semana","📅 Semana"), ("mes","🗓 Mes")]:
            b = ctk.CTkButton(tgl, text=v_lbl, width=84, height=32, corner_radius=8,
                fg_color=C("accent") if v_key == self._vista else "transparent",
                text_color="white" if v_key == self._vista else C("text2"),
                hover_color=C("accent"),
                font=("Helvetica", FS("small")),
                command=lambda v=v_key: self._set_vista(v))
            b.pack(side="left", padx=2, pady=2)
            self._vista_btns[v_key] = b

        # ── Navegación ────────────────────────────────────────────
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

    def _set_vista(self, v):
        self._vista = v
        self._offset = 0
        self._dia_offset = 0
        for k, btn in self._vista_btns.items():
            btn.configure(
                fg_color=C("accent") if k == v else "transparent",
                text_color="white" if k == v else C("text2"))
        self._refresh()

    def _nav(self, delta):
        if self._vista == "dia":
            self._dia_offset += delta
        elif self._vista == "mes":
            self._offset += delta
        else:
            self._offset += delta
        self._refresh()

    def _refresh(self):
        for w in self.grid_fr.winfo_children(): w.destroy()
        if self._vista == "dia":
            self._render_dia()
        elif self._vista == "mes":
            self._render_mes()
        else:
            self._render_semana()
        # Auto-refresh 60s
        try:
            if self.winfo_exists():
                if self._refresh_after:
                    try: self.after_cancel(self._refresh_after)
                    except Exception as e: logging.warning("PanelAgendaSemanal._refresh: after_cancel falló – %s", e)
                self._refresh_after = self.after(60000, self._refresh)
        except Exception as e:
            logging.warning("PanelAgendaSemanal._refresh: no se pudo programar auto-refresh – %s", e)

    # ── Vista: SEMANA ─────────────────────────────────────────────
    def _render_semana(self):
        hoy   = datetime.now().date()
        lunes = hoy - timedelta(days=hoy.weekday()) + timedelta(weeks=self._offset)
        self.lbl_sem.configure(
            text=f"{lunes.strftime('%d %b')} – {(lunes+timedelta(6)).strftime('%d %b %Y')}")
        all_acts = cargar_personal(self.file_key) + cargar_global()
        dias_mostrar = []
        for i, dia in enumerate(self.DIAS):
            fecha_dia = lunes + timedelta(days=i)
            if self._offset == 0 and fecha_dia < hoy:
                continue
            dias_mostrar.append((i, dia, fecha_dia))
        if not dias_mostrar and self._offset == 0:
            self._offset = 1; self._refresh(); return
        for i, dia, fecha_dia in dias_mostrar:
            fecha_str = fecha_dia.strftime("%Y-%m-%d")
            es_hoy    = (fecha_dia == hoy)
            acts_dia  = sorted([a for a in all_acts if a.get("fecha")==fecha_str],
                               key=lambda x: x.get("hora_inicio","00:00"))
            col_fr = ctk.CTkFrame(self.grid_fr, fg_color=C("surface"), corner_radius=14)
            col_fr.pack(side="left", fill="y", padx=5, expand=True, anchor="n")
            dh = ctk.CTkFrame(col_fr, fg_color=C("accent") if es_hoy else C("surface2"),
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
                    font=("Helvetica",FS("small")), text_color=C("text3")).pack(pady=14)
            for a in acts_dia:
                arow = ctk.CTkFrame(col_fr, fg_color=C("accent_bg"), corner_radius=8)
                arow.pack(fill="x", padx=8, pady=3)
                ctk.CTkLabel(arow, text=a.get("titulo","?")[:16],
                    font=("Helvetica",FS("small"),"bold"), text_color=C("text")
                    ).pack(anchor="w", padx=8, pady=(6,0))
                ctk.CTkLabel(arow,
                    text=f"{a.get('hora_inicio','?')}–{a.get('hora_fin','?')}",
                    font=("Helvetica",FS("small")), text_color=C("text2")
                    ).pack(anchor="w", padx=8, pady=(0,6))
            ctk.CTkFrame(col_fr, fg_color="transparent", height=6).pack()

    # ── Vista: MES (cuadrícula) ───────────────────────────────────
    def _render_mes(self):
        import calendar
        hoy   = datetime.now().date()
        base  = date(hoy.year, hoy.month, 1)
        # Avanzar/retroceder meses con self._offset
        m = hoy.month + self._offset
        y = hoy.year + (m - 1) // 12
        m = ((m - 1) % 12) + 1
        base = date(y, m, 1)
        self.lbl_sem.configure(text=base.strftime("%B %Y").capitalize())
        all_acts = cargar_personal(self.file_key) + cargar_global()
        n_dias  = calendar.monthrange(y, m)[1]
        primer_wd = base.weekday()   # 0=Lunes

        COLS = 7
        # Cabecera días de la semana
        for ci, dia_hdr in enumerate(["L","M","Mi","J","V","S","D"]):
            self.grid_fr.columnconfigure(ci, weight=1)
            ctk.CTkLabel(self.grid_fr, text=dia_hdr,
                font=("Helvetica",FS("small"),"bold"), text_color=C("text2"),
                width=50, anchor="center").grid(row=0, column=ci, padx=2, pady=(0,4), sticky="ew")

        row_i, col_i = 1, primer_wd
        for d in range(1, n_dias + 1):
            fecha_obj = date(y, m, d)
            fecha_str = fecha_obj.strftime("%Y-%m-%d")
            es_hoy    = (fecha_obj == hoy)
            acts      = [a for a in all_acts if a.get("fecha") == fecha_str]

            cell = ctk.CTkFrame(self.grid_fr,
                fg_color=C("accent") if es_hoy else C("surface"),
                corner_radius=10, width=50, height=64)
            cell.grid(row=row_i, column=col_i, padx=2, pady=2, sticky="nsew")
            cell.pack_propagate(False)
            ctk.CTkLabel(cell, text=str(d),
                font=("Helvetica",FS("small"),"bold"),
                text_color="white" if es_hoy else C("text")).pack(pady=(6,2))
            # Puntos de actividad
            if acts:
                dots = ctk.CTkFrame(cell, fg_color="transparent")
                dots.pack()
                for a in acts[:3]:
                    cat = a.get("categoria","")
                    col_dot = C("teal") if "Estudio" in cat else \
                              C("amber") if "Tarea" in cat else C("green")
                    ctk.CTkFrame(dots, fg_color=col_dot,
                        width=6, height=6, corner_radius=3
                        ).pack(side="left", padx=1)

            col_i += 1
            if col_i == COLS:
                col_i = 0; row_i += 1

    # ── Vista: DÍA (timeline por horas) ──────────────────────────
    def _render_dia(self):
        hoy       = datetime.now().date()
        dia_obj   = hoy + timedelta(days=self._dia_offset)
        dia_str   = dia_obj.strftime("%Y-%m-%d")
        dia_label = dia_obj.strftime("%A %d de %B")
        self.lbl_sem.configure(text=dia_label.capitalize())
        all_acts  = cargar_personal(self.file_key) + cargar_global()
        acts_dia  = sorted([a for a in all_acts if a.get("fecha") == dia_str],
                           key=lambda x: x.get("hora_inicio","00:00"))

        HORA_INI, HORA_FIN = 6, 22
        hora_act = datetime.now().hour if dia_obj == hoy else -1

        for h in range(HORA_INI, HORA_FIN + 1):
            slot = ctk.CTkFrame(self.grid_fr,
                fg_color=C("surface") if h != hora_act else C("accent_bg"),
                corner_radius=0)
            slot.pack(fill="x", pady=0)
            # Línea de hora
            hdr_sl = ctk.CTkFrame(slot, fg_color="transparent")
            hdr_sl.pack(fill="x")
            ctk.CTkLabel(hdr_sl, text=f"{h:02d}:00",
                font=("Helvetica", 10, "bold"),
                text_color=C("accent") if h == hora_act else C("text3"),
                width=46, anchor="e").pack(side="left", padx=(8,4))
            ctk.CTkFrame(hdr_sl, fg_color=C("border"), height=1
                ).pack(side="left", fill="x", expand=True)

            # Actividades en esta hora
            for a in acts_dia:
                try:
                    h_ini = int(a.get("hora_inicio","99:00").split(":")[0])
                except Exception:
                    h_ini = 99
                if h_ini == h:
                    acard = ctk.CTkFrame(slot,
                        fg_color=C("accent"), corner_radius=8)
                    acard.pack(fill="x", padx=(62, 12), pady=3)
                    ctk.CTkLabel(acard,
                        text=f"  {a.get('hora_inicio','?')}–{a.get('hora_fin','?')}  {a.get('titulo','?')}",
                        font=("Helvetica", FS("small"), "bold"),
                        text_color="white", anchor="w").pack(anchor="w", padx=8, pady=6)
            ctk.CTkFrame(slot, fg_color="transparent", height=4).pack()

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
        if not self._on:
            return
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
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
                except Exception as _pom_err:
                    logging.warning("PanelPomodoro: error al guardar sesión – %s", _pom_err)
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
        # Crear los 4 círculos la primera vez; después solo reconfigurar color
        children = self._cir_fr.winfo_children()
        if not children:
            for i in range(4):
                ctk.CTkFrame(self._cir_fr,
                    fg_color=C("accent") if i < self._sesiones else C("border"),
                    width=20, height=20, corner_radius=10).pack(side="left", padx=4)
        else:
            for i, w in enumerate(children):
                w.configure(fg_color=C("accent") if i < self._sesiones else C("border"))

    def destroy(self):
        """Cancela el temporizador activo antes de destruir el panel."""
        self._on = False
        if self._tid:
            try:
                self.after_cancel(self._tid)
            except Exception:
                pass
            self._tid = None
        super().destroy()


#  PANEL: LOGROS
# ─────────────────────────────────────────────────────────────────
class PanelLogros(ctk.CTkScrollableFrame):
    def __init__(self, parent, datos, **kw):
        super().__init__(parent, fg_color=C("bg"),
                         scrollbar_button_color=C("accent"), **kw)
        self.datos = datos
        self._after_ids: list = []
        self._flame_after = None  # ID actual del loop de llama (no crece en lista)
        self._build()

    def destroy(self):
        for aid in self._after_ids:
            try:
                self.after_cancel(aid)
            except Exception as e:
                logging.warning("PanelLogros.destroy: after_cancel falló – %s", e)
        self._after_ids.clear()
        if self._flame_after:
            try: self.after_cancel(self._flame_after)
            except Exception as e: logging.warning("PanelLogros.destroy: flame_after falló – %s", e)
        super().destroy()

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
            self._flame_after = self.after(200, self._animate_flame)  # sobreescribe, no acumula
        except Exception:
            pass

# ─────────────────────────────────────────────────────────────────
#  DIALOGO: COMANDOS DE VOZ
# ─────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────
#  LECTOR DE PANTALLA — Accesibilidad con TTS + navegación por flechas
# ─────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────
#  PANEL INSCRIPCIÓN — Constructor de horario semestral
# ─────────────────────────────────────────────────────────────────
class PanelReinscripcion(ctk.CTkScrollableFrame):
    """
    Permite al alumno visualizar las materias disponibles y construir su
    horario semestral. Ofrece:
      • Tabla semanal visual (Lun-Vie + Sab) con bloques de color por materia.
      • Modo manual: el alumno elige grupo por materia con combo-boxes.
      • Sugerencia inteligente: genera 2 horarios sin traslapes con criterios
        de compacidad y distribución equitativa de carga.
    """

    # Catálogo de materias extraído de las capturas
    MATERIAS_DISPONIBLES = [
        {
            "clave": "L40848", "nombre": "Programación de Microcontroladores",
            "creditos": 6,
            "grupos": [
                {"grupo":"SE","profesor":"Carlos Eduardo Torres Reyes","dias":["Lunes","Miércoles"],"hora_ini":"13:00","hora_fin":"15:00","aula":"D22","modalidad":"PRESENCIAL"},
                {"grupo":"SF","profesor":"Carlos Eduardo Torres Reyes","dias":["Lunes","Miércoles"],"hora_ini":"11:00","hora_fin":"13:00","aula":"D22","modalidad":"PRESENCIAL"},
                {"grupo":"SG","profesor":"Oliver David Melgarejo Castañeda","dias":["Miércoles","Viernes"],"hora_ini":"07:30","hora_fin":"09:30","aula":"D25","modalidad":"PRESENCIAL"},
                {"grupo":"SH","profesor":"Oliver David Melgarejo Castañeda","dias":["Miércoles","Viernes"],"hora_ini":"09:30","hora_fin":"11:30","aula":"-","modalidad":"PRESENCIAL"},
                {"grupo":"S3","profesor":"José Arturo Pérez Martínez","dias":["Lunes"],"hora_ini":"07:00","hora_fin":"15:00","aula":"E32","modalidad":"PRESENCIAL"},
                {"grupo":"S4","profesor":"José Arturo Pérez Martínez","dias":["Lunes","Miércoles"],"hora_ini":"11:00","hora_fin":"13:00","aula":"E32","modalidad":"PRESENCIAL"},
            ]
        },
        {
            "clave": "L40852", "nombre": "Requisitos y Especificación de Software",
            "creditos": 6,
            "grupos": [
                {"grupo":"SE","profesor":"José Rafael Cruz Reyes","dias":["Lunes","Miércoles"],"hora_ini":"19:00","hora_fin":"20:30","aula":"VIRTUAL","modalidad":"CON MEDIACIÓN TECNOLÓGICA"},
                {"grupo":"SF","profesor":"José Rafael Cruz Reyes","dias":["Lunes","Miércoles"],"hora_ini":"17:30","hora_fin":"19:00","aula":"-","modalidad":"CON MEDIACIÓN TECNOLÓGICA"},
                {"grupo":"SG","profesor":"J. Ghandi Patiño Manzanarez","dias":["Viernes"],"hora_ini":"17:00","hora_fin":"20:00","aula":"VIRTUAL","modalidad":"CON MEDIACIÓN TECNOLÓGICA"},
                {"grupo":"S3","profesor":"Selene Itzel Vargas Flores","dias":["Martes","Jueves"],"hora_ini":"07:00","hora_fin":"08:30","aula":"E33","modalidad":"PRESENCIAL"},
                {"grupo":"S4","profesor":"Selene Itzel Vargas Flores","dias":["Martes","Jueves"],"hora_ini":"08:30","hora_fin":"10:00","aula":"E33","modalidad":"PRESENCIAL"},
            ]
        },
        {
            "clave": "L40831", "nombre": "Administración",
            "creditos": 6,
            "grupos": [
                {"grupo":"SH","profesor":"Carlos Landeros Guzmán","dias":["Lunes","Miércoles"],"hora_ini":"09:00","hora_fin":"10:30","aula":"D23","modalidad":"PRESENCIAL"},
                {"grupo":"SI","profesor":"V. Manuel González Herrera","dias":["Lunes","Miércoles"],"hora_ini":"09:00","hora_fin":"10:30","aula":"D23","modalidad":"PRESENCIAL"},
                {"grupo":"SJ","profesor":"Carlos Landeros Guzmán","dias":["Lunes","Miércoles"],"hora_ini":"07:00","hora_fin":"08:30","aula":"D23","modalidad":"PRESENCIAL"},
                {"grupo":"S5","profesor":"Carlos Landeros Guzmán","dias":["Lunes","Miércoles"],"hora_ini":"11:00","hora_fin":"12:30","aula":"D23","modalidad":"PRESENCIAL"},
                {"grupo":"S6","profesor":"Carlos Landeros Guzmán","dias":["Lunes","Miércoles"],"hora_ini":"13:00","hora_fin":"14:30","aula":"D23","modalidad":"PRESENCIAL"},
            ]
        },
        {
            "clave": "L40836", "nombre": "Arquitectura de Software",
            "creditos": 6,
            "grupos": [
                {"grupo":"SH","profesor":"María Alcántara Fernández","dias":["Martes","Jueves"],"hora_ini":"13:30","hora_fin":"15:30","aula":"D23","modalidad":"PRESENCIAL"},
                {"grupo":"SI","profesor":"—","dias":["Lunes","Miércoles"],"hora_ini":"18:00","hora_fin":"20:00","aula":"VIRTUAL","modalidad":"PRESENCIAL"},
                {"grupo":"SJ","profesor":"Leonor González Muñoz","dias":["Lunes"],"hora_ini":"11:00","hora_fin":"13:00","aula":"D25","modalidad":"PRESENCIAL"},
                {"grupo":"S5","profesor":"María Alcántara Fernández","dias":["Martes","Jueves"],"hora_ini":"09:00","hora_fin":"11:00","aula":"D23","modalidad":"PRESENCIAL"},
                {"grupo":"S6","profesor":"María Alcántara Fernández","dias":["Martes","Jueves"],"hora_ini":"11:00","hora_fin":"13:00","aula":"D23","modalidad":"PRESENCIAL"},
            ]
        },
        {
            "clave": "ISWK14", "nombre": "Desarrollo de Aplicaciones Web",
            "creditos": 6,
            "grupos": [
                {"grupo":"SH","profesor":"J. Ghandi Patiño Manzanarez","dias":["Viernes"],"hora_ini":"07:00","hora_fin":"11:00","aula":"F12","modalidad":"PRESENCIAL"},
                {"grupo":"SI","profesor":"Jesús Mares Montes","dias":["Lunes","Miércoles"],"hora_ini":"07:00","hora_fin":"09:00","aula":"E32","modalidad":"PRESENCIAL"},
                {"grupo":"SJ","profesor":"J. Ghandi Patiño Manzanarez","dias":["Viernes"],"hora_ini":"11:00","hora_fin":"15:00","aula":"F12","modalidad":"PRESENCIAL"},
                {"grupo":"S5","profesor":"Jesús Mares Montes","dias":["Lunes","Miércoles"],"hora_ini":"09:00","hora_fin":"11:00","aula":"D22","modalidad":"PRESENCIAL"},
                {"grupo":"S6","profesor":"J. Ghandi Patiño Manzanarez","dias":["Sábado"],"hora_ini":"07:00","hora_fin":"11:00","aula":"F12","modalidad":"PRESENCIAL"},
            ]
        },
        {
            "clave": "L40844", "nombre": "Graficación",
            "creditos": 6,
            "grupos": [
                {"grupo":"SH","profesor":"Selene Itzel Vargas Flores","dias":["Martes","Jueves"],"hora_ini":"12:00","hora_fin":"14:00","aula":"C5","modalidad":"PRESENCIAL"},
                {"grupo":"SI","profesor":"Selene Itzel Vargas Flores","dias":["Martes","Jueves"],"hora_ini":"10:00","hora_fin":"12:00","aula":"C5","modalidad":"PRESENCIAL"},
                {"grupo":"SJ","profesor":"—","dias":["Sábado"],"hora_ini":"07:00","hora_fin":"11:00","aula":"F11","modalidad":"PRESENCIAL"},
                {"grupo":"S5","profesor":"Yanet Hernández Casimiro","dias":["Lunes","Miércoles"],"hora_ini":"19:00","hora_fin":"21:00","aula":"VIRTUAL","modalidad":"CON MEDIACIÓN TECNOLÓGICA"},
                {"grupo":"S6","profesor":"Selene Itzel Vargas Flores","dias":["Martes","Jueves"],"hora_ini":"14:00","hora_fin":"16:00","aula":"C5","modalidad":"PRESENCIAL"},
            ]
        },
        {
            "clave": "L40858", "nombre": "Teoría de Lenguajes de Programación",
            "creditos": 6,
            "grupos": [
                {"grupo":"SH","profesor":"José Esteban Ruiz Melo","dias":["Sábado"],"hora_ini":"07:00","hora_fin":"10:00","aula":"VIRTUAL","modalidad":"CON MEDIACIÓN TECNOLÓGICA"},
                {"grupo":"SI","profesor":"Marcela Camacho Ávila","dias":["Lunes","Miércoles"],"hora_ini":"12:00","hora_fin":"13:30","aula":"F13","modalidad":"PRESENCIAL"},
                {"grupo":"SJ","profesor":"Gerardo Arturo Ávila Vilchis","dias":["Martes","Jueves"],"hora_ini":"10:00","hora_fin":"12:00","aula":"D24","modalidad":"PRESENCIAL"},
                {"grupo":"S5","profesor":"José Esteban Ruiz Melo","dias":["Jueves"],"hora_ini":"18:00","hora_fin":"19:30","aula":"VIRTUAL","modalidad":"CON MEDIACIÓN TECNOLÓGICA"},
                {"grupo":"S6","profesor":"José Esteban Ruiz Melo","dias":["Viernes"],"hora_ini":"19:30","hora_fin":"21:00","aula":"VIRTUAL","modalidad":"CON MEDIACIÓN TECNOLÓGICA"},
            ]
        },
        {
            "clave": "L40840", "nombre": "Estructuras de Datos",
            "creditos": 8,
            "grupos": [
                {"grupo":"SE","profesor":"Mauro Sánchez Sánchez","dias":["Lunes","Miércoles"],"hora_ini":"09:30","hora_fin":"12:00","aula":"F12","modalidad":"PRESENCIAL"},
                {"grupo":"SF","profesor":"Marcela Camacho Ávila","dias":["Lunes","Miércoles"],"hora_ini":"07:00","hora_fin":"09:30","aula":"D22","modalidad":"PRESENCIAL"},
                {"grupo":"SG","profesor":"Angélica Millán Díaz","dias":["Sábado"],"hora_ini":"08:00","hora_fin":"13:00","aula":"F12","modalidad":"PRESENCIAL"},
                {"grupo":"S3","profesor":"Marcela Camacho Ávila","dias":["Lunes","Miércoles"],"hora_ini":"09:30","hora_fin":"12:00","aula":"-","modalidad":"PRESENCIAL"},
                {"grupo":"S4","profesor":"Mauro Sánchez Sánchez","dias":["Lunes","Miércoles"],"hora_ini":"07:00","hora_fin":"09:30","aula":"F12","modalidad":"PRESENCIAL"},
            ]
        },
        {
            "clave": "LMU404", "nombre": "Inglés 7",
            "creditos": 6,
            "grupos": [
                {"grupo":"C3","profesor":"Lucia Alarcón Márquez","dias":["Lunes"],"hora_ini":"09:00","hora_fin":"11:00","aula":"B3","modalidad":"PRESENCIAL"},
                {"grupo":"I1","profesor":"Bertha Rodríguez Gutiérrez","dias":["Martes","Jueves"],"hora_ini":"19:00","hora_fin":"21:00","aula":"VIRTUAL","modalidad":"CON MEDIACIÓN TECNOLÓGICA"},
                {"grupo":"I2","profesor":"Bertha Rodríguez Gutiérrez","dias":["Martes","Jueves"],"hora_ini":"17:00","hora_fin":"19:00","aula":"VIRTUAL","modalidad":"CON MEDIACIÓN TECNOLÓGICA"},
                {"grupo":"M1","profesor":"Adriana Carolina Zárate Neri","dias":["Martes","Jueves"],"hora_ini":"19:00","hora_fin":"21:00","aula":"VIRTUAL","modalidad":"CON MEDIACIÓN TECNOLÓGICA"},
                {"grupo":"M2","profesor":"Erika Lizbeth Alanis Contreras","dias":["Martes","Jueves"],"hora_ini":"19:00","hora_fin":"21:00","aula":"VIRTUAL","modalidad":"CON MEDIACIÓN TECNOLÓGICA"},
                {"grupo":"SE","profesor":"Víctor Manuel Galán Hernández","dias":["Sábado"],"hora_ini":"07:00","hora_fin":"11:00","aula":"VIRTUAL","modalidad":"CON MEDIACIÓN TECNOLÓGICA"},
                {"grupo":"SF","profesor":"Elizabeth Fierro Moreno","dias":["Sábado"],"hora_ini":"07:00","hora_fin":"11:00","aula":"VIRTUAL","modalidad":"CON MEDIACIÓN TECNOLÓGICA"},
                {"grupo":"SG","profesor":"Elizabeth Fierro Moreno","dias":["Martes","Jueves"],"hora_ini":"19:00","hora_fin":"21:00","aula":"VIRTUAL","modalidad":"CON MEDIACIÓN TECNOLÓGICA"},
            ]
        },
        {
            "clave": "L40816", "nombre": "Interacción Humano-Computadora",
            "creditos": 5,
            "grupos": [
                {"grupo":"SE","profesor":"Brenda Yazmín Reza Curiel","dias":["Martes","Jueves"],"hora_ini":"07:00","hora_fin":"08:30","aula":"D22","modalidad":"PRESENCIAL"},
                {"grupo":"SG","profesor":"Griselda Areli Matias Mendoza","dias":["Martes","Jueves"],"hora_ini":"11:00","hora_fin":"12:30","aula":"D22","modalidad":"PRESENCIAL"},
                {"grupo":"S3","profesor":"Griselda Areli Matias Mendoza","dias":["Martes","Jueves"],"hora_ini":"15:00","hora_fin":"16:30","aula":"F13","modalidad":"PRESENCIAL"},
                {"grupo":"S4","profesor":"Brenda Yazmín Reza Curiel","dias":["Lunes","Miércoles"],"hora_ini":"07:00","hora_fin":"08:30","aula":"E37","modalidad":"PRESENCIAL"},
            ]
        },
    ]

    DIAS_ORDEN = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado"]
    PALETA = ["#2E7D32","#1565C0","#6A1B9A","#E65100","#C62828","#00695C",
              "#4E342E","#37474F","#AD1457","#00838F"]

    def __init__(self, parent, file_key):
        super().__init__(parent, fg_color=C("bg"),
                         scrollbar_button_color=C("accent"))
        self.file_key = file_key
        self._selecciones = {}   # clave_materia → grupo dict o None
        self._color_mat   = {}   # clave → color
        self._modo        = tk.StringVar(value="manual")
        for i, m in enumerate(self.MATERIAS_DISPONIBLES):
            self._color_mat[m["clave"]] = self.PALETA[i % len(self.PALETA)]
        self._build()

    # ── UI principal ────────────────────────────────────────────────
    def _build(self):
        from ui_theme import PREFS
        if not PREFS.get("reinscripcion_activa", False):
            self._build_bloqueado()
            return
        # Header
        hdr = ctk.CTkFrame(self, fg_color=C("accent"), corner_radius=0, height=80)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="📋  Reinscripción — Constructor de Horario Semestral",
                     font=("Helvetica", 22, "bold"), text_color="white").place(x=24, y=12)
        ctk.CTkLabel(hdr, text="Selecciona tus materias y grupos · Vista semanal automática",
                     font=("Helvetica", 12), text_color="white").place(x=24, y=46)

        # Controles superiores
        ctrl = ctk.CTkFrame(self, fg_color=C("surface"), corner_radius=10)
        ctrl.pack(fill="x", padx=20, pady=(14, 6))

        ctk.CTkLabel(ctrl, text="Modo:", font=("Helvetica", 13, "bold"),
                     text_color=C("text")).pack(side="left", padx=(16, 6), pady=10)
        ctk.CTkRadioButton(ctrl, text="Manual", variable=self._modo,
                           value="manual", command=self._on_modo,
                           fg_color=C("accent")).pack(side="left", padx=6, pady=10)
        ctk.CTkRadioButton(ctrl, text="Sugerencia inteligente", variable=self._modo,
                           value="auto", command=self._on_modo,
                           fg_color=C("accent")).pack(side="left", padx=6, pady=10)

        Btn(ctrl, text="🔄 Limpiar todo", command=self._limpiar,
            width=130).pack(side="right", padx=10, pady=8)
        Btn(ctrl, text="✅ Confirmar horario", command=self._confirmar,
            width=160).pack(side="right", padx=4, pady=8)

        # Cuerpo: izquierda (selector) + derecha (tabla)
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=8)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=5)
        body.rowconfigure(0, weight=1)

        # Panel izquierdo — selector de grupos
        self._left = ctk.CTkScrollableFrame(body, fg_color=C("surface"),
                                            corner_radius=10,
                                            scrollbar_button_color=C("accent"))
        self._left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # Panel derecho — tabla semanal
        self._right = ctk.CTkFrame(body, fg_color=C("surface"), corner_radius=10)
        self._right.grid(row=0, column=1, sticky="nsew")

        self._build_selector()
        self._build_tabla()

    def _build_bloqueado(self):
        """Muestra mensaje cuando la reinscripción está desactivada."""
        ctk.CTkFrame(self, fg_color="transparent", height=60).pack()
        lock = ctk.CTkFrame(self, fg_color=C("surface"), corner_radius=20)
        lock.pack(padx=60, pady=40, fill="x")
        ctk.CTkLabel(lock, text="🔒", font=("Helvetica", 52)).pack(pady=(30, 8))
        ctk.CTkLabel(lock, text="Reinscripción no disponible",
                     font=("Helvetica", 20, "bold"), text_color=C("text")).pack()
        ctk.CTkLabel(lock,
                     text="El período de reinscripción está cerrado en este momento.\n"
                          "Cuando el administrador lo habilite podrás armar tu horario.",
                     font=("Helvetica", 12), text_color=C("text2"),
                     justify="center", wraplength=400).pack(pady=(8, 30))

    def _build_selector(self):
        for w in self._left.winfo_children():
            w.destroy()
        ctk.CTkLabel(self._left, text="📚  Materias disponibles",
                     font=("Helvetica", 14, "bold"), text_color=C("text")
                     ).pack(padx=12, pady=(12, 6), anchor="w")

        if self._modo.get() == "auto":
            self._build_selector_auto()
            return

        for mat in self.MATERIAS_DISPONIBLES:
            clave  = mat["clave"]
            color  = self._color_mat[clave]
            card   = ctk.CTkFrame(self._left, fg_color=C("card"), corner_radius=8)
            card.pack(fill="x", padx=8, pady=4)

            # Banda de color lateral
            band = ctk.CTkFrame(card, fg_color=color, width=5, corner_radius=4)
            band.pack(side="left", fill="y", padx=(0, 8))
            band.pack_propagate(False)

            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, pady=6)
            ctk.CTkLabel(info, text=f"{mat['nombre']} ({clave})",
                         font=("Helvetica", 12, "bold"), text_color=C("text"),
                         wraplength=200, justify="left").pack(anchor="w")
            # Badge de modalidad: refleja si hay grupos en línea, presenciales o mixtos
            def _es_online(g):
                return (g.get("modalidad", "").upper() in ("CON MEDIACIÓN TECNOLÓGICA", "VIRTUAL")
                        or g.get("aula", "").upper() == "VIRTUAL")
            grupos = mat["grupos"]
            n_online = sum(1 for g in grupos if _es_online(g))
            n_total  = len(grupos)
            if n_online == 0:
                badge_txt, badge_col, badge_w = None, None, 0
            elif n_online == n_total:
                badge_txt, badge_col, badge_w = "🌐 En línea", "#1565C0", 66
            else:
                badge_txt, badge_col, badge_w = "🔀 Mixta", "#6A1B9A", 58

            cred_row = ctk.CTkFrame(info, fg_color="transparent")
            cred_row.pack(anchor="w")
            ctk.CTkLabel(cred_row, text=f"{mat['creditos']} créditos",
                         font=("Helvetica", 10), text_color=C("text2")).pack(side="left")
            if badge_txt:
                badge = ctk.CTkFrame(cred_row, fg_color=badge_col, corner_radius=6,
                                     height=16, width=badge_w)
                badge.pack(side="left", padx=(6, 0))
                badge.pack_propagate(False)
                ctk.CTkLabel(badge, text=badge_txt, font=("Helvetica", 8, "bold"),
                             text_color="white").place(relx=.5, rely=.5, anchor="center")

            # Combo de grupos
            opciones = ["— No cursar —"] + [
                f"Grupo {g['grupo']} · {'/'.join(g['dias'])} {g['hora_ini']}-{g['hora_fin']} · {g['profesor']}"
                for g in mat["grupos"]
            ]
            var = ctk.StringVar(value=opciones[0])
            if clave in self._selecciones and self._selecciones[clave]:
                g_sel = self._selecciones[clave]
                for idx, g in enumerate(mat["grupos"], 1):
                    if g["grupo"] == g_sel["grupo"]:
                        var.set(opciones[idx])
                        break

            cb = ctk.CTkComboBox(info, values=opciones, variable=var,
                                 width=280, state="readonly",
                                 command=lambda v, c=clave, m=mat: self._sel_grupo(c, m, v))
            cb.pack(anchor="w", pady=(4, 0))

    def _build_selector_auto(self):
        """Muestra los 2 horarios sugeridos para elegir."""
        sug1, sug2 = self._generar_sugerencias()
        ctk.CTkLabel(self._left,
                     text="La IA generó 2 opciones sin traslapes.\nElige la que más te convenga:",
                     font=("Helvetica", 11), text_color=C("text2"),
                     wraplength=270, justify="left").pack(padx=12, pady=(0, 10))

        for i, sug in enumerate([sug1, sug2], 1):
            if sug is None:
                ctk.CTkLabel(self._left, text=f"Opción {i}: No fue posible generar.",
                             font=("Helvetica", 11), text_color=C("text2")).pack(padx=12, pady=4)
                continue
            btn_frame = ctk.CTkFrame(self._left, fg_color=C("card"), corner_radius=10)
            btn_frame.pack(fill="x", padx=8, pady=6)
            ctk.CTkLabel(btn_frame,
                         text=f"📅  Opción {i}",
                         font=("Helvetica", 13, "bold"), text_color=C("accent")
                         ).pack(anchor="w", padx=10, pady=(8, 2))
            total_cred = sum(m["creditos"] for m in self.MATERIAS_DISPONIBLES
                             if m["clave"] in sug)
            ctk.CTkLabel(btn_frame, text=f"Créditos: {total_cred}  · Materias: {len(sug)}",
                         font=("Helvetica", 10), text_color=C("text2")
                         ).pack(anchor="w", padx=10)
            for clave, g in sug.items():
                nombre = next(m["nombre"] for m in self.MATERIAS_DISPONIBLES
                              if m["clave"] == clave)
                ctk.CTkLabel(btn_frame,
                             text=f"• {nombre}: Grupo {g['grupo']} "
                                  f"{'/'.join(g['dias'])} {g['hora_ini']}-{g['hora_fin']}",
                             font=("Helvetica", 10), text_color=C("text"),
                             wraplength=260, justify="left"
                             ).pack(anchor="w", padx=14, pady=1)
            Btn(btn_frame, text=f"✅ Usar opción {i}",
                command=lambda s=sug: self._aplicar_sugerencia(s),
                width=180).pack(pady=(8, 10))

    def _sel_grupo(self, clave, mat, valor):
        if "No cursar" in valor:
            self._selecciones[clave] = None
        else:
            idx = [f"Grupo {g['grupo']} · {'/'.join(g['dias'])} {g['hora_ini']}-{g['hora_fin']} · {g['profesor']}"
                   for g in mat["grupos"]].index(valor.split("— No cursar —")[0].strip())
            self._selecciones[clave] = mat["grupos"][idx] | {"clave": clave, "nombre": mat["nombre"]}
        self._build_tabla()

    def _aplicar_sugerencia(self, sug):
        self._selecciones = {}
        for clave, g in sug.items():
            nombre = next(m["nombre"] for m in self.MATERIAS_DISPONIBLES
                          if m["clave"] == clave)
            self._selecciones[clave] = g | {"clave": clave, "nombre": nombre}
        self._modo.set("manual")
        self._build_selector()
        self._build_tabla()

    # ── Tabla semanal ──────────────────────────────────────────────
    def _build_tabla(self):
        for w in self._right.winfo_children():
            w.destroy()

        ctk.CTkLabel(self._right, text="🗓  Vista semanal",
                     font=("Helvetica", 14, "bold"), text_color=C("text")
                     ).pack(padx=14, pady=(10, 4), anchor="w")

        # Construir slots: día → lista de (hora_ini, hora_fin, grupo_dict)
        slots: dict[str, list] = {d: [] for d in self.DIAS_ORDEN}
        for clave, g in self._selecciones.items():
            if g is None:
                continue
            for dia in g["dias"]:
                if dia in slots:
                    slots[dia].append({
                        "hora_ini": g["hora_ini"],
                        "hora_fin": g["hora_fin"],
                        "nombre": g.get("nombre", clave),
                        "clave": clave,
                        "grupo": g["grupo"],
                        "profesor": g["profesor"],
                        "aula": g.get("aula", "-"),
                        "color": self._color_mat.get(clave, "#888"),
                    })

        # Detectar traslapes
        traslapes = self._detectar_traslapes()

        # Horas a mostrar: 07:00 a 22:00 en pasos de 1 hora
        hora_inicio = 7
        hora_fin    = 22
        n_horas     = hora_fin - hora_inicio

        # Canvas con tabla de cuadrícula
        dias_activos = [d for d in self.DIAS_ORDEN if slots[d] or True]
        n_dias       = len(dias_activos)
        col_w        = 120
        row_h        = 36
        head_h       = 36
        time_w       = 58
        canvas_w     = time_w + col_w * n_dias + 4
        canvas_h     = head_h + row_h * n_horas + 4

        outer = ctk.CTkFrame(self._right, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=8, pady=4)

        cv_frame = ctk.CTkFrame(outer, fg_color="transparent")
        cv_frame.pack(fill="both", expand=True)

        h_scroll = ctk.CTkScrollbar(outer, orientation="horizontal")
        v_scroll = ctk.CTkScrollbar(cv_frame, orientation="vertical")
        h_scroll.pack(side="bottom", fill="x")
        v_scroll.pack(side="right", fill="y")

        is_dark = PREFS.get("dark_mode", True)
        bg_cv   = "#1e1e2e" if is_dark else "#f8f9fa"
        fg_grid = "#2a2a3e" if is_dark else "#dee2e6"
        fg_head = "#2d2d44" if is_dark else "#e9ecef"
        tx_col  = "#ffffff" if is_dark else "#212529"
        tx_dim  = "#888aaa" if is_dark else "#6c757d"

        cv = tk.Canvas(cv_frame, bg=bg_cv, highlightthickness=0,
                       xscrollcommand=h_scroll.set,
                       yscrollcommand=v_scroll.set)
        cv.pack(side="left", fill="both", expand=True)
        h_scroll.configure(command=cv.xview)
        v_scroll.configure(command=cv.yview)
        cv.configure(scrollregion=(0, 0, canvas_w, canvas_h))

        # Cabeceras de días
        for ci, dia in enumerate(dias_activos):
            x0 = time_w + ci * col_w
            cv.create_rectangle(x0, 0, x0 + col_w, head_h, fill=fg_head, outline="")
            cv.create_text(x0 + col_w // 2, head_h // 2, text=dia[:3],
                           font=("Helvetica", 10, "bold"), fill=tx_col)

        # Filas de horas
        for hi in range(n_horas + 1):
            y = head_h + hi * row_h
            hora_txt = f"{hora_inicio + hi:02d}:00"
            cv.create_line(0, y, canvas_w, y, fill=fg_grid, width=1)
            if hi < n_horas:
                cv.create_text(time_w // 2, y + row_h // 2, text=hora_txt,
                               font=("Helvetica", 9), fill=tx_dim)

        # Líneas verticales de columnas
        for ci in range(n_dias + 1):
            x = time_w + ci * col_w
            cv.create_line(x, 0, x, canvas_h, fill=fg_grid, width=1)

        # Dibujar bloques de materias
        def hm_to_float(s):
            h, m = map(int, s.split(":"))
            return h + m / 60

        for ci, dia in enumerate(dias_activos):
            x0 = time_w + ci * col_w + 2
            for bloque in slots[dia]:
                yi = hm_to_float(bloque["hora_ini"]) - hora_inicio
                yf = hm_to_float(bloque["hora_fin"]) - hora_inicio
                y0 = head_h + int(yi * row_h) + 1
                y1 = head_h + int(yf * row_h) - 1
                col_bloque = bloque["color"]
                # Borde rojo si hay traslape
                borde = "#FF4444" if traslapes else col_bloque
                cv.create_rectangle(x0, y0, x0 + col_w - 4, y1,
                                    fill=col_bloque, outline=borde, width=2)
                label = f"{bloque['nombre'][:18]}\nGpo {bloque['grupo']} · {bloque['aula']}\n{bloque['profesor'].split()[-1] if bloque['profesor'] else ''}"
                cv.create_text(x0 + (col_w - 4) // 2, (y0 + y1) // 2,
                               text=label, font=("Helvetica", 8), fill="white",
                               width=col_w - 10, justify="center")

        # Leyenda de traslapes
        if traslapes:
            ctk.CTkLabel(self._right,
                         text="⚠️  Hay traslapes en tu horario. Revisa los grupos seleccionados.",
                         font=("Helvetica", 11, "bold"), text_color="#FF4444"
                         ).pack(padx=14, pady=(4, 8))

        # Leyenda de materias
        leyenda = ctk.CTkFrame(self._right, fg_color="transparent")
        leyenda.pack(fill="x", padx=10, pady=(4, 10))
        for clave, g in self._selecciones.items():
            if g is None:
                continue
            nombre = g.get("nombre", clave)
            color  = self._color_mat.get(clave, "#888")
            row    = ctk.CTkFrame(leyenda, fg_color="transparent")
            row.pack(side="left", padx=4)
            dot = ctk.CTkFrame(row, fg_color=color, width=12, height=12, corner_radius=6)
            dot.pack(side="left")
            dot.pack_propagate(False)
            ctk.CTkLabel(row, text=nombre[:20], font=("Helvetica", 9),
                         text_color=C("text2")).pack(side="left", padx=(3, 0))

    # ── Lógica de sugerencias ──────────────────────────────────────
    def _generar_sugerencias(self):
        """
        Genera 2 combinaciones sin traslapes tratando de:
          Sug 1 → mañana / menos días sábado
          Sug 2 → tarde / distribuir carga
        Usa backtracking simple.
        """
        materias = self.MATERIAS_DISPONIBLES

        def hm(s):
            h, m = map(int, s.split(":"))
            return h * 60 + m

        def traslapa(g1, g2):
            dias_c = set(g1["dias"]) & set(g2["dias"])
            if not dias_c:
                return False
            s1, e1 = hm(g1["hora_ini"]), hm(g1["hora_fin"])
            s2, e2 = hm(g2["hora_ini"]), hm(g2["hora_fin"])
            return s1 < e2 and s2 < e1

        def es_valido(selec, nuevo_g):
            for g in selec.values():
                if g and traslapa(g, nuevo_g):
                    return False
            return True

        def backtrack(idx, selec, preferencia):
            if idx == len(materias):
                return dict(selec)
            mat = materias[idx]
            grupos_ord = sorted(mat["grupos"],
                key=lambda g: (
                    ("Sábado" in g["dias"]) * 10 +
                    (hm(g["hora_ini"]) > 14 * 60 if preferencia == "mañana"
                     else hm(g["hora_ini"]) < 12 * 60)
                ))
            for g in grupos_ord:
                if es_valido(selec, g):
                    selec[mat["clave"]] = g
                    result = backtrack(idx + 1, selec, preferencia)
                    if result is not None:
                        return result
                    del selec[mat["clave"]]
            # Permitir no cursar una materia si no hay solución
            return backtrack(idx + 1, selec, preferencia)

        sug1 = backtrack(0, {}, "mañana")
        sug2 = backtrack(0, {}, "tarde")
        return sug1, sug2

    def _detectar_traslapes(self):
        def hm(s):
            h, m = map(int, s.split(":"))
            return h * 60 + m

        grupos = [g for g in self._selecciones.values() if g]
        for i in range(len(grupos)):
            for j in range(i + 1, len(grupos)):
                g1, g2 = grupos[i], grupos[j]
                dias_c = set(g1["dias"]) & set(g2["dias"])
                if dias_c:
                    s1, e1 = hm(g1["hora_ini"]), hm(g1["hora_fin"])
                    s2, e2 = hm(g2["hora_ini"]), hm(g2["hora_fin"])
                    if s1 < e2 and s2 < e1:
                        return True
        return False

    def _on_modo(self):
        self._selecciones = {}
        self._build_selector()
        self._build_tabla()

    def _limpiar(self):
        self._selecciones = {}
        self._modo.set("manual")
        self._build_selector()
        self._build_tabla()

    def _confirmar(self):
        activas = {k: v for k, v in self._selecciones.items() if v}
        if not activas:
            from tkinter import messagebox
            messagebox.showwarning("Sin selección",
                "No has seleccionado ningún grupo todavía.")
            return
        if self._detectar_traslapes():
            from tkinter import messagebox
            if not messagebox.askyesno("Traslapes detectados",
                    "Tu horario tiene traslapes. ¿Deseas guardarlo de todas formas?"):
                return
        # Guardar en local_db
        datos = cargar_personal(self.file_key) or {}
        datos.setdefault("horario_inscripcion", {})
        datos["horario_inscripcion"] = {
            k: {
                "nombre": v.get("nombre", k),
                "grupo": v["grupo"],
                "dias": v["dias"],
                "hora_ini": v["hora_ini"],
                "hora_fin": v["hora_fin"],
                "profesor": v.get("profesor", ""),
                "aula": v.get("aula", ""),
            }
            for k, v in activas.items()
        }
        guardar_personal(self.file_key, datos)
        from tkinter import messagebox
        messagebox.showinfo("Horario guardado",
            f"✅ Horario con {len(activas)} materia(s) guardado correctamente.")
