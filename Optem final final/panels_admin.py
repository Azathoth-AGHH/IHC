# ╔══════════════════════════════════════════════════════════════════╗
# ║  panels_admin.py — Paneles de la vista Administrativo            ║
# ╚══════════════════════════════════════════════════════════════════╝
import logging
import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox
from ui_theme import C, FS, _darken
from ui_components import Card, Btn, BtnOutline
from ui_images import make_avatar
from local_db import (cargar_global, guardar_global, CATEGORIAS_GLOBAL,
                      EJEMPLO_GLOBAL)
from dialogs import DialogoActividad, ExportadorPDF
from validator_engine import ValidatorEngine

class PanelInicioAdmin(ctk.CTkScrollableFrame):
    def __init__(self, parent, datos, on_tab, **kw):
        super().__init__(parent, fg_color=C("bg"),
                         scrollbar_button_color=C("accent"), **kw)
        self.datos  = datos
        self.on_tab = on_tab
        self._after_ids: list = []
        self._clock_after = None  # ID del reloj en vivo (no acumula en lista)
        self._build()

    def destroy(self):
        for aid in self._after_ids:
            try:
                self.after_cancel(aid)
            except Exception as e:
                logging.warning("PanelInicioAdmin.destroy: after_cancel falló – %s", e)
        self._after_ids.clear()
        if self._clock_after:
            try: self.after_cancel(self._clock_after)
            except Exception as e: logging.warning("PanelInicioAdmin.destroy: clock_after falló – %s", e)
        super().destroy()

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
        self._build_reinscripcion_toggle()

    def _tick_adm_clock(self):
        try:
            if not self.winfo_exists():
                return
            now = datetime.now()
            self._adm_clock.configure(text=now.strftime("%H:%M"))
            self._adm_clock_sub.configure(text=now.strftime("%S s  ·  %d/%m/%Y"))
            self._clock_after = self.after(1000, self._tick_adm_clock)  # sobreescribe, no acumula
        except Exception:
            pass

    def _build_reinscripcion_toggle(self):
        """Sección para abrir/cerrar el período de reinscripción."""
        from ui_theme import PREFS, save_prefs
        sec = ctk.CTkFrame(self, fg_color="transparent")
        sec.pack(fill="x", padx=20, pady=(0, 24))

        card = ctk.CTkFrame(sec, fg_color=C("surface"), corner_radius=16,
                             border_width=2, border_color=C("border"))
        card.pack(fill="x")

        hdr_row = ctk.CTkFrame(card, fg_color="transparent")
        hdr_row.pack(fill="x", padx=18, pady=(16, 6))

        ctk.CTkLabel(hdr_row, text="🗓  Período de Reinscripción",
            font=("Helvetica", FS("h3"), "bold"), text_color=C("text")).pack(side="left")

        # Estado actual
        _estado_activo = PREFS.get("reinscripcion_activa", False)
        estado_col = C("green") if _estado_activo else C("red")
        estado_txt = "ABIERTO ✅" if _estado_activo else "CERRADO 🔒"
        self._lbl_estado_reinsc = ctk.CTkLabel(hdr_row, text=estado_txt,
            font=("Helvetica", FS("small"), "bold"), text_color=estado_col)
        self._lbl_estado_reinsc.pack(side="right")

        ctk.CTkLabel(card,
            text="Activa o desactiva el acceso a reinscripción para todos los alumnos.",
            font=("Helvetica", FS("small")), text_color=C("text2")).pack(
                padx=18, anchor="w", pady=(0, 10))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=18, pady=(0, 16))

        def _get_sidebar():
            """Busca el Sidebar navegando por la jerarquía de widgets."""
            try:
                # Intento 1: la VentanaPrincipal registra _app_screen en el toplevel
                app = self.winfo_toplevel().__dict__.get("_app_screen") or \
                      getattr(self.winfo_toplevel(), "_app_screen", None)
                if app and hasattr(app, "sidebar"):
                    return app.sidebar
                # Intento 2: buscar sidebar directamente en el master
                w = self
                for _ in range(8):
                    if hasattr(w, "sidebar"):
                        return w.sidebar
                    w = w.master
            except Exception:
                pass
            return None

        def _abrir():
            PREFS["reinscripcion_activa"] = True
            save_prefs(PREFS)
            self._lbl_estado_reinsc.configure(text="ABIERTO ✅", text_color=C("green"))
            sb = _get_sidebar()
            if sb:
                sb.actualizar_reinscripcion(True)

        def _cerrar():
            PREFS["reinscripcion_activa"] = False
            save_prefs(PREFS)
            self._lbl_estado_reinsc.configure(text="CERRADO 🔒", text_color=C("red"))
            sb = _get_sidebar()
            if sb:
                sb.actualizar_reinscripcion(False)

        Btn(btn_row, text="🔓  Abrir Reinscripción", width=200, height=40,
            fg_color=C("green"), command=_abrir).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_row, text="🔒  Cerrar Reinscripción", width=200, height=40,
            corner_radius=10, fg_color=C("red"), hover_color=C("red"),
            text_color="white", font=("Helvetica", FS("body")),
            command=_cerrar).pack(side="left")


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
        # Renderizado diferido para no bloquear la UI al abrir el panel
        self.after(10, self._build)

    # Datos de materias (para exportar)
    _MATERIAS_DATA = [
        {"nombre": "Cálculo III",    "promedio": 92, "alumnos": 28, "riesgo": 2},
        {"nombre": "Física II",      "promedio": 78, "alumnos": 30, "riesgo": 8},
        {"nombre": "Prog. Avanzada", "promedio": 71, "alumnos": 26, "riesgo": 12},
        {"nombre": "Álgebra",        "promedio": 85, "alumnos": 24, "riesgo": 4},
        {"nombre": "Lab. Sistemas",  "promedio": 89, "alumnos": 22, "riesgo": 1},
    ]

    def _build(self):
        # ── Encabezado con botón exportar ────────────────────────
        hdr_row = ctk.CTkFrame(self, fg_color="transparent")
        hdr_row.pack(fill="x", padx=24, pady=(24, 4))
        ctk.CTkLabel(hdr_row, text="📊  Reportes Académicos",
            font=("Helvetica",FS("h2"),"bold"), text_color=C("text")).pack(side="left")
        ctk.CTkButton(hdr_row, text="📥 Exportar PDF", width=130, height=34,
            corner_radius=10,
            font=("Helvetica", FS("small"), "bold"),
            fg_color=C("accent"), hover_color=C("accent_dark"), text_color="white",
            command=self._exportar_pdf).pack(side="right")

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

    def _exportar_pdf(self):
        """Exporta el reporte académico a PDF o HTML."""
        ExportadorPDF.exportar_reporte(
            self._MATERIAS_DATA,
            titulo="Reporte Académico · OPTEM",
            parent=self.winfo_toplevel(),
        )


class PanelAlumnos(ctk.CTkFrame):
    # (nombre, correo, semestre, promedio, racha, tareas_activas, materias_en_riesgo)
    # Los números de cuenta se generan automáticamente al crear _ALUMNOS_CON_CUENTA
    _ALUMNOS_BASE = [
        ("Ana García López",        "ana.garcia@alumno.uaemex.mx",      "7°","91%","22🔥", 4, 0),
        ("Luis Martínez Ruiz",      "luis.martinez@alumno.uaemex.mx",   "5°","78%","8🔥",  7, 1),
        ("Sofía Hernández Cruz",    "sofia.hernandez@alumno.uaemex.mx", "4°","95%","31🔥", 3, 0),
        ("Carlos Ramírez Vega",     "carlos.ramirez@alumno.uaemex.mx",  "6°","72%","5🔥",  9, 2),
        ("María López Sánchez",     "maria.lopez@alumno.uaemex.mx",     "3°","88%","14🔥", 5, 0),
        ("Pedro Torres Jiménez",    "pedro.torres@alumno.uaemex.mx",    "1°","61%","2🔥", 11, 3),
        ("Valeria Flores Morales",  "valeria.flores@alumno.uaemex.mx",  "8°","93%","45🔥", 3, 0),
        ("Diego Vargas Castillo",   "diego.vargas@alumno.uaemex.mx",    "2°","69%","0🔥", 10, 2),
        ("Fernanda Reyes Ortiz",    "fernanda.reyes@alumno.uaemex.mx",  "5°","82%","11🔥", 6, 1),
        ("Andrés Moreno Guzmán",    "andres.moreno@alumno.uaemex.mx",   "7°","76%","7🔥",  7, 1),
        ("Camila Jiménez Peña",     "camila.jimenez@alumno.uaemex.mx",  "4°","90%","19🔥", 4, 0),
        ("Roberto Silva Mendoza",   "roberto.silva@alumno.uaemex.mx",   "6°","65%","3🔥", 10, 3),
        ("Daniela Ríos Aguilar",    "daniela.rios@alumno.uaemex.mx",    "3°","87%","16🔥", 5, 0),
        ("Miguel Ángel Núñez",      "miguel.nunez@alumno.uaemex.mx",    "1°","54%","0🔥", 12, 4),
        ("Isabella Campos León",    "isabella.campos@alumno.uaemex.mx", "8°","97%","60🔥", 2, 0),
        ("Emilio Rojas Espinoza",   "emilio.rojas@alumno.uaemex.mx",    "2°","73%","6🔥",  8, 1),
        ("Natalia Serrano Vidal",   "natalia.serrano@alumno.uaemex.mx", "5°","84%","12🔥", 5, 0),
        ("Alejandro Cruz Medina",   "alejandro.cruz@alumno.uaemex.mx",  "7°","79%","9🔥",  7, 1),
        ("Paola Guerrero Ávila",    "paola.guerrero@alumno.uaemex.mx",  "4°","92%","25🔥", 3, 0),
        ("Eduardo Mendez Rubio",    "eduardo.mendez@alumno.uaemex.mx",  "6°","68%","4🔥",  9, 2),
        ("Lucía Pacheco Soto",      "lucia.pacheco@alumno.uaemex.mx",   "3°","86%","17🔥", 5, 0),
        ("Ricardo Salinas Bravo",   "ricardo.salinas@alumno.uaemex.mx", "1°","58%","1🔥", 11, 3),
        ("Mariana Delgado Rivas",   "mariana.delgado@alumno.uaemex.mx", "8°","94%","38🔥", 3, 0),
        ("Sebastián Vega Montes",   "sebastian.vega@alumno.uaemex.mx",  "2°","70%","5🔥",  8, 2),
        ("Ariana Blanco Fuentes",   "ariana.blanco@alumno.uaemex.mx",   "5°","81%","10🔥", 6, 1),
        ("Iván Herrera Castañeda",  "ivan.herrera@alumno.uaemex.mx",    "7°","75%","8🔥",  7, 1),
        ("Ximena Lara Ponce",       "ximena.lara@alumno.uaemex.mx",     "4°","89%","20🔥", 4, 0),
        ("Gerardo Molina Acosta",   "gerardo.molina@alumno.uaemex.mx",  "6°","63%","2🔥", 10, 3),
        ("Vanessa Romero Téllez",   "vanessa.romero@alumno.uaemex.mx",  "3°","85%","15🔥", 5, 0),
        ("Jorge Espinosa Olvera",   "jorge.espinosa@alumno.uaemex.mx",  "1°","62%","3🔥", 10, 2),
        ("Brenda Navarro Quiroz",   "brenda.navarro@alumno.uaemex.mx",  "8°","96%","52🔥", 2, 0),
        ("Oscar Ramos Becerra",     "oscar.ramos@alumno.uaemex.mx",     "2°","67%","0🔥", 11, 3),
        ("Stephanie Peña Villanueva","stephanie.pena@alumno.uaemex.mx", "5°","83%","13🔥", 5, 1),
        ("Armando Fuentes Trejo",   "armando.fuentes@alumno.uaemex.mx", "7°","77%","6🔥",  7, 1),
        ("Gabriela Cortes Ibarra",  "gabriela.cortes@alumno.uaemex.mx", "4°","91%","21🔥", 4, 0),
        ("Humberto Díaz Cervantes", "humberto.diaz@alumno.uaemex.mx",   "6°","66%","4🔥",  9, 2),
        ("Renata Ángeles Meza",     "renata.angeles@alumno.uaemex.mx",  "3°","88%","18🔥", 5, 0),
        ("Ulises Contreras Prado",  "ulises.contreras@alumno.uaemex.mx","1°","57%","1🔥", 12, 4),
        ("Patricia Villafuerte",    "patricia.villafuerte@alumno.uaemex.mx","8°","93%","40🔥", 3, 0),
        ("Héctor Zamora Osorio",    "hector.zamora@alumno.uaemex.mx",   "2°","71%","5🔥",  8, 1),
        ("Alexa Cervantes Portillo","alexa.cervantes@alumno.uaemex.mx", "5°","80%","9🔥",  6, 1),
        ("Joel Sandoval Miranda",   "joel.sandoval@alumno.uaemex.mx",   "7°","74%","7🔥",  7, 1),
        ("Carmen Huerta Alvarado",  "carmen.huerta@alumno.uaemex.mx",   "4°","87%","16🔥", 4, 0),
        ("Rodrigo Barrera Méndez",  "rodrigo.barrera@alumno.uaemex.mx", "6°","64%","2🔥", 10, 3),
        ("Diana Sosa Camacho",      "diana.sosa@alumno.uaemex.mx",      "3°","86%","14🔥", 5, 0),
        ("Marco Infante Valdés",    "marco.infante@alumno.uaemex.mx",   "1°","60%","0🔥", 11, 2),
        ("Alicia Monroy Bautista",  "alicia.monroy@alumno.uaemex.mx",   "8°","95%","47🔥", 2, 0),
        ("Enrique Cisneros Tapia",  "enrique.cisneros@alumno.uaemex.mx","2°","69%","4🔥",  9, 2),
        ("Karla Ojeda Espinoza",    "karla.ojeda@alumno.uaemex.mx",     "5°","82%","11🔥", 5, 1),
        ("Omar Zúñiga Pedraza",     "omar.zuniga@alumno.uaemex.mx",     "7°","76%","8🔥",  7, 1),
        ("Itzel Vergara Solano",    "itzel.vergara@alumno.uaemex.mx",   "4°","90%","23🔥", 4, 0),
        ("Saúl Domínguez Loza",     "saul.dominguez@alumno.uaemex.mx",  "6°","67%","3🔥",  9, 2),
    ]
    # Tupla extendida: (num_cuenta, nombre, correo, semestre, promedio, racha, tareas, riesgo)
    # Número de cuenta: 7 dígitos — base 2024001 + índice
    _ALUMNOS = tuple(
        (f"{2024001 + i}",) + row
        for i, row in enumerate(_ALUMNOS_BASE)
    )

    def __init__(self, parent, **kw):
        super().__init__(parent, fg_color=C("bg"), **kw)
        self._ac_visible = False
        self._ac_idx     = -1
        self._ac_matches = []   # lista de num_cuenta de coincidencias
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
        self.e_busq = ctk.CTkEntry(ih, placeholder_text="🔍 Nombre o No. de cuenta...",
            height=38, width=280, corner_radius=10,
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
        # Carga diferida para no bloquear la UI al abrir el panel
        self.after(20, lambda: self._mostrar(""))
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
        # _ALUMNOS: (num_cuenta, nombre, correo, semestre, promedio, racha, tareas, riesgo)
        matches = [a for a in self._ALUMNOS
                   if q in a[0] or q in a[1].lower() or q in a[2].lower()]
        if not matches:
            self._hide_ac(); return
        self._ac_matches = [a[0] for a in matches[:8]]  # guarda num_cuenta
        self._ac_idx = -1
        self._render_ac_dropdown()

    def _render_ac_dropdown(self):
        """Dibuja el dropdown resaltando el ítem en self._ac_idx."""
        for w in self._ac_frame.winfo_children(): w.destroy()
        ctk.CTkLabel(self._ac_frame, text="Sugerencias",
            font=("Helvetica", FS("small"), "bold"),
            text_color=C("text2")).pack(anchor="w", padx=12, pady=(8,2))
        for i, nc in enumerate(self._ac_matches):
            datos = next((a for a in self._ALUMNOS if a[0]==nc), None)
            nom    = datos[1] if datos else nc
            correo = datos[2] if datos else ""
            sem    = datos[3] if datos else ""
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
            ctk.CTkLabel(info, text=f"{nom}  ·  #{nc}",
                font=("Helvetica", FS("body"), "bold"),
                text_color=C("text"), anchor="w").pack(anchor="w")
            ctk.CTkLabel(info, text=f"{correo} · {sem} sem.",
                font=("Helvetica", FS("small")),
                text_color=C("text2"), anchor="w").pack(anchor="w")
            for w in (row, lbl_av, info):
                w.bind("<Button-1>", lambda e, n=nc: self._select_ac(n))
            for child in info.winfo_children():
                child.bind("<Button-1>", lambda e, n=nc: self._select_ac(n))
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

    def _select_ac(self, num_cuenta):
        """Al seleccionar del dropdown, busca por número de cuenta."""
        a = next((x for x in self._ALUMNOS if x[0] == num_cuenta), None)
        self.e_busq.delete(0, "end")
        self.e_busq.insert(0, num_cuenta)
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
        # _ALUMNOS: (num_cuenta, nombre, correo, semestre, promedio, racha, tareas, riesgo)
        filtrados = [a for a in self._ALUMNOS
                     if not q or q in a[0] or q in a[1].lower() or q in a[2].lower()]
        # Renderizado por lotes: evita bloquear la UI con 50+ widgets
        self._render_batch(filtrados, 0)

    def _render_batch(self, items, start, batch=8):
        """Renderiza alumnos en lotes pequeños usando after() para no congelar la UI."""
        end = min(start + batch, len(items))
        for a in items[start:end]:
            nc, nom, correo, sem, prom, racha, tareas, riesgo = a
            card = Card(self.scroll); card.pack(fill="x", pady=5)
            card.configure(cursor="hand2")
            inner = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
            inner.pack(fill="x", padx=16, pady=14)
            av = make_avatar(nom[:2].upper(), 44)
            ctk.CTkLabel(inner, image=av, text="", cursor="hand2").pack(side="left", padx=(0,12))
            info = ctk.CTkFrame(inner, fg_color="transparent", cursor="hand2")
            info.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(info, text=nom,
                font=("Helvetica",FS("body"),"bold"), text_color=C("text"), cursor="hand2").pack(anchor="w")
            ctk.CTkLabel(info, text=f"No. Cuenta: {nc}  ·  {correo}  ·  {sem} semestre",
                font=("Helvetica",FS("small")), text_color=C("text2"), cursor="hand2").pack(anchor="w")
            # Estado de regularización
            p = float(prom.replace("%",""))
            if p < 70:
                ctk.CTkLabel(info, text="🔴  Necesita regularización",
                    font=("Helvetica",FS("small"),"bold"), text_color=C("red"), cursor="hand2").pack(anchor="w", pady=(2,0))
            elif p < 80:
                ctk.CTkLabel(info, text="🟡  En seguimiento",
                    font=("Helvetica",FS("small"),"bold"), text_color=C("amber"), cursor="hand2").pack(anchor="w", pady=(2,0))
            # ── Barra de carga de trabajo ─────────────────────────
            carga_fr = ctk.CTkFrame(info, fg_color="transparent", cursor="hand2")
            carga_fr.pack(anchor="w", fill="x", pady=(4,0))
            carga_pct = min(tareas / 12, 1.0)
            carga_col = C("green") if tareas <= 4 else C("amber") if tareas <= 8 else C("red")
            ctk.CTkLabel(carga_fr, text=f"📋 Carga: {tareas} tareas activas",
                font=("Helvetica", FS("small")), text_color=C("text2"), cursor="hand2").pack(side="left", padx=(0,8))
            barra_bg = ctk.CTkFrame(carga_fr, fg_color=C("surface2"), corner_radius=4, height=8, width=120)
            barra_bg.pack(side="left", pady=2)
            barra_bg.pack_propagate(False)
            ctk.CTkFrame(barra_bg, fg_color=carga_col, corner_radius=4,
                         width=int(120 * carga_pct), height=8).place(x=0, y=0)
            if riesgo > 0:
                ctk.CTkLabel(carga_fr, text=f"  ⚠️ {riesgo} mat. en riesgo",
                    font=("Helvetica", FS("small"), "bold"), text_color=C("red"), cursor="hand2").pack(side="left")
            # ── Stats derechos ────────────────────────────────────
            right = ctk.CTkFrame(inner, fg_color="transparent", cursor="hand2")
            right.pack(side="right")
            pc = C("green") if p>=80 else C("amber") if p>=70 else C("red")
            ctk.CTkLabel(right, text=prom,
                font=("Helvetica",FS("h3"),"bold"), text_color=pc, cursor="hand2").pack()
            ctk.CTkLabel(right, text=racha,
                font=("Helvetica",FS("small")), text_color=C("amber"), cursor="hand2").pack()
            # ── Clic en cualquier parte de la card abre el detalle ──
            _fn = lambda e, n=nom, c=correo, s=sem, pr=prom, r=racha, t=tareas, ri=riesgo, num=nc: \
                self._ver_alumno(n, c, s, pr, r, t, ri, num)
            for _w in card.winfo_children() + [card]:
                try:
                    _w.bind("<Button-1>", _fn)
                except Exception:
                    pass
            # bind profundo en todos los descendientes
            def _bind_tree(widget, fn=_fn):
                try:
                    widget.bind("<Button-1>", fn)
                except Exception:
                    pass
                for ch in widget.winfo_children():
                    _bind_tree(ch, fn)
            _bind_tree(card)
            # Efecto hover en la card
            def _on_enter(e, c=card): c.configure(border_width=2, border_color=C("accent"))
            def _on_leave(e, c=card): c.configure(border_width=0)
            card.bind("<Enter>", _on_enter)
            card.bind("<Leave>", _on_leave)
        if end < len(items):
            self.after(10, lambda: self._render_batch(items, end, batch))

    def _ver_alumno(self, nom, correo, sem, prom, racha, tareas=5, riesgo=0, num_cuenta=""):
        """Diálogo de detalle por alumno con materias, carga de trabajo y estado de regularización."""
        top = ctk.CTkToplevel(self)
        top.title(f"Detalle alumno — {nom}")
        top.geometry("540x620")
        top.configure(fg_color=C("bg"))
        top.grab_set(); top.lift(); top.focus_force()

        # Encabezado
        hdr = ctk.CTkFrame(top, fg_color=C("accent"), corner_radius=0, height=100)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        av = make_avatar(nom[:2].upper(), 54)
        ctk.CTkLabel(hdr, image=av, text="").place(x=20, rely=0.5, anchor="w")
        ctk.CTkLabel(hdr, text=nom,
            font=("Helvetica",FS("h3"),"bold"), text_color="white").place(x=90, y=14)
        ctk.CTkLabel(hdr, text=f"No. Cuenta: {num_cuenta}",
            font=("Helvetica",FS("body"),"bold"), text_color="#FFEEDD").place(x=90, y=44)
        ctk.CTkLabel(hdr, text=f"{correo}  ·  {sem} semestre",
            font=("Helvetica",FS("small")), text_color="#EEEEFF").place(x=90, y=68)

        scr = ctk.CTkScrollableFrame(top, fg_color="transparent",
                                     scrollbar_button_color=C("accent"))
        scr.pack(fill="both", expand=True, padx=16, pady=12)

        # Stats rápidos
        sr = ctk.CTkFrame(scr, fg_color="transparent")
        sr.pack(fill="x", pady=(0,8))
        p = float(prom.replace("%",""))
        pc = C("green") if p>=80 else C("amber") if p>=70 else C("red")
        for i,(ico,val,lbl,col) in enumerate([
            ("📊", prom, "Promedio general", pc),
            ("🔥", racha, "Racha actual", C("amber")),
            ("🎓", sem, "Semestre", C("accent")),
            ("📋", str(tareas), "Tareas activas", C("green") if tareas<=4 else C("amber") if tareas<=8 else C("red")),
        ]):
            sr.columnconfigure(i, weight=1)
            c = Card(sr); c.grid(row=0, column=i, padx=3, sticky="ew")
            ctk.CTkLabel(c, text=ico, font=("Helvetica",20)).pack(pady=(10,2))
            ctk.CTkLabel(c, text=val, font=("Helvetica",FS("h3"),"bold"),
                text_color=col).pack()
            ctk.CTkLabel(c, text=lbl, font=("Helvetica",FS("small")),
                text_color=C("text2")).pack(pady=(0,10))

        # ── Carga de trabajo ──────────────────────────────────────
        ctk.CTkLabel(scr, text="⚡  Carga de trabajo actual",
            font=("Helvetica",FS("body"),"bold"), text_color=C("text"),
            anchor="w").pack(anchor="w", pady=(4,4))
        carga_card = Card(scr); carga_card.pack(fill="x", pady=(0,10))
        carga_inner = ctk.CTkFrame(carga_card, fg_color="transparent")
        carga_inner.pack(fill="x", padx=14, pady=10)
        carga_pct = min(tareas / 12, 1.0)
        carga_col = C("green") if tareas<=4 else C("amber") if tareas<=8 else C("red")
        nivel_txt = "Baja ✅" if tareas<=4 else "Media ⚠️" if tareas<=8 else "Alta 🔴"
        ctk.CTkLabel(carga_inner, text=f"Tareas activas: {tareas} / 12   —   Nivel: {nivel_txt}",
            font=("Helvetica",FS("body")), text_color=C("text")).pack(anchor="w")
        barra_bg = ctk.CTkFrame(carga_inner, fg_color=C("surface2"), corner_radius=6, height=14)
        barra_bg.pack(fill="x", pady=(6,4))
        barra_bg.pack_propagate(False)
        barra_bg.update_idletasks()
        ctk.CTkFrame(barra_bg, fg_color=carga_col, corner_radius=6,
                     width=int(barra_bg.winfo_reqwidth() * carga_pct), height=14).place(x=0,y=0)
        if riesgo > 0:
            ctk.CTkLabel(carga_inner,
                text=f"⚠️  {riesgo} materia(s) con calificación en riesgo — se recomienda seguimiento.",
                font=("Helvetica",FS("small"),"bold"), text_color=C("red")).pack(anchor="w", pady=(4,0))

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

        # ── Botones de acción ─────────────────────────────────────
        def _exportar_ficha():
            alumno_data = {
                "nombre":             nom,
                "correo":             correo,
                "semestre":           sem,
                "promedio":           prom,
                "racha":              racha,
                "tareas_activas":     tareas,
                "materias_en_riesgo": riesgo,
                "num_cuenta":         num_cuenta,
                "materias": [
                    {"nombre": m, "calificacion": c, "estado": e}
                    for m, c, e, _ in MATERIAS_ALUMNO
                ],
            }
            ExportadorPDF.exportar_ficha_alumno(alumno_data, parent=top)

        br = ctk.CTkFrame(top, fg_color="transparent")
        br.pack(pady=(8, 16))
        Btn(br, text="📥 Exportar PDF", width=160, command=_exportar_ficha).pack(side="left", padx=8)
        from ui_components import BtnOutline
        BtnOutline(br, text="Cerrar", width=100, command=top.destroy).pack(side="left", padx=8)


class PanelClasesAdmin(ctk.CTkFrame):
    """Panel CRUD de clases para el administrador."""
    COLORES_DISP = [C("accent"), C("amber"), C("green"), C("teal"), C("red"), "#9B8DFF", "#E91E8C", "#00BCD4"]
    DIAS_SEM = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado"]
    HORAS_DISP = ["07:00","08:00","09:00","10:00","11:00","12:00",
                  "13:00","14:00","15:00","16:00","17:00","18:00","19:00","20:00"]

    def __init__(self, parent, **kw):
        super().__init__(parent, fg_color=C("bg"), **kw)
        # Clases sincronizadas con PanelHorarios.MAESTROS_DB
        self._clases = []
        _id = 1
        for m in PanelHorarios.MAESTROS_DB:
            for cl in m["clases"]:
                self._clases.append({
                    "id": _id,
                    "materia": cl["materia"],
                    "grupo": cl["grupo"],
                    "dia": cl["dias"][0] if cl["dias"] else "Lunes",
                    "hora_ini": cl["hora_ini"],
                    "hora_fin": cl["hora_fin"],
                    "color": self.COLORES_DISP[_id % len(self.COLORES_DISP)],
                    "desc": f"Maestro: {m['nombre']} · Aula: {cl.get('aula','-')}",
                })
                _id += 1
        self._next_id = _id
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
    """
    Vista de horarios por maestro.
    Lista todos los maestros extraídos del catálogo de reinscripción.
    Al hacer clic en un maestro se muestra su horario semanal en tabla.
    """

    # Catálogo de maestros y sus clases (sincronizado con PanelReinscripcion.MATERIAS_DISPONIBLES)
    MAESTROS_DB = [
        {"nombre": "Carlos Eduardo Torres Reyes", "depto": "ISW",
         "clases": [
            {"materia": "Prog. Microcontroladores", "grupo": "SE", "dias": ["Lunes","Miércoles"], "hora_ini": "13:00", "hora_fin": "15:00", "aula": "D22"},
            {"materia": "Prog. Microcontroladores", "grupo": "SF", "dias": ["Lunes","Miércoles"], "hora_ini": "11:00", "hora_fin": "13:00", "aula": "D22"},
         ]},
        {"nombre": "Oliver David Melgarejo Castañeda", "depto": "ISW",
         "clases": [
            {"materia": "Prog. Microcontroladores", "grupo": "SG", "dias": ["Miércoles","Viernes"], "hora_ini": "07:30", "hora_fin": "09:30", "aula": "D25"},
            {"materia": "Prog. Microcontroladores", "grupo": "SH", "dias": ["Miércoles","Viernes"], "hora_ini": "09:30", "hora_fin": "11:30", "aula": "-"},
         ]},
        {"nombre": "José Arturo Pérez Martínez", "depto": "ISW",
         "clases": [
            {"materia": "Prog. Microcontroladores", "grupo": "S3", "dias": ["Lunes"], "hora_ini": "07:00", "hora_fin": "15:00", "aula": "E32"},
            {"materia": "Prog. Microcontroladores", "grupo": "S4", "dias": ["Lunes","Miércoles"], "hora_ini": "11:00", "hora_fin": "13:00", "aula": "E32"},
         ]},
        {"nombre": "José Rafael Cruz Reyes", "depto": "ISW",
         "clases": [
            {"materia": "Requisitos y Esp. SW", "grupo": "SE", "dias": ["Lunes","Miércoles"], "hora_ini": "19:00", "hora_fin": "20:30", "aula": "VIRTUAL"},
            {"materia": "Requisitos y Esp. SW", "grupo": "SF", "dias": ["Lunes","Miércoles"], "hora_ini": "17:30", "hora_fin": "19:00", "aula": "VIRTUAL"},
         ]},
        {"nombre": "J. Ghandi Patiño Manzanarez", "depto": "ISW",
         "clases": [
            {"materia": "Requisitos y Esp. SW", "grupo": "SG", "dias": ["Viernes"], "hora_ini": "17:00", "hora_fin": "20:00", "aula": "VIRTUAL"},
            {"materia": "Desarrollo de Apps Web", "grupo": "SH", "dias": ["Viernes"], "hora_ini": "07:00", "hora_fin": "11:00", "aula": "F12"},
            {"materia": "Desarrollo de Apps Web", "grupo": "SJ", "dias": ["Viernes"], "hora_ini": "11:00", "hora_fin": "15:00", "aula": "F12"},
            {"materia": "Desarrollo de Apps Web", "grupo": "S6", "dias": ["Sábado"], "hora_ini": "07:00", "hora_fin": "11:00", "aula": "F12"},
         ]},
        {"nombre": "Selene Itzel Vargas Flores", "depto": "ISW",
         "clases": [
            {"materia": "Requisitos y Esp. SW", "grupo": "S3", "dias": ["Martes","Jueves"], "hora_ini": "07:00", "hora_fin": "08:30", "aula": "E33"},
            {"materia": "Requisitos y Esp. SW", "grupo": "S4", "dias": ["Martes","Jueves"], "hora_ini": "08:30", "hora_fin": "10:00", "aula": "E33"},
            {"materia": "Graficación", "grupo": "SH", "dias": ["Martes","Jueves"], "hora_ini": "12:00", "hora_fin": "14:00", "aula": "C5"},
            {"materia": "Graficación", "grupo": "SI", "dias": ["Martes","Jueves"], "hora_ini": "10:00", "hora_fin": "12:00", "aula": "C5"},
            {"materia": "Graficación", "grupo": "S6", "dias": ["Martes","Jueves"], "hora_ini": "14:00", "hora_fin": "16:00", "aula": "C5"},
         ]},
        {"nombre": "Carlos Landeros Guzmán", "depto": "ISW",
         "clases": [
            {"materia": "Administración", "grupo": "SH", "dias": ["Lunes","Miércoles"], "hora_ini": "09:00", "hora_fin": "10:30", "aula": "D23"},
            {"materia": "Administración", "grupo": "SJ", "dias": ["Lunes","Miércoles"], "hora_ini": "07:00", "hora_fin": "08:30", "aula": "D23"},
            {"materia": "Administración", "grupo": "S5", "dias": ["Lunes","Miércoles"], "hora_ini": "11:00", "hora_fin": "12:30", "aula": "D23"},
            {"materia": "Administración", "grupo": "S6", "dias": ["Lunes","Miércoles"], "hora_ini": "13:00", "hora_fin": "14:30", "aula": "D23"},
         ]},
        {"nombre": "V. Manuel González Herrera", "depto": "ISW",
         "clases": [
            {"materia": "Administración", "grupo": "SI", "dias": ["Lunes","Miércoles"], "hora_ini": "09:00", "hora_fin": "10:30", "aula": "D23"},
         ]},
        {"nombre": "María Alcántara Fernández", "depto": "ISW",
         "clases": [
            {"materia": "Arquitectura de SW", "grupo": "SH", "dias": ["Martes","Jueves"], "hora_ini": "13:30", "hora_fin": "15:30", "aula": "D23"},
            {"materia": "Arquitectura de SW", "grupo": "S5", "dias": ["Martes","Jueves"], "hora_ini": "09:00", "hora_fin": "11:00", "aula": "D23"},
            {"materia": "Arquitectura de SW", "grupo": "S6", "dias": ["Martes","Jueves"], "hora_ini": "11:00", "hora_fin": "13:00", "aula": "D23"},
         ]},
        {"nombre": "Leonor González Muñoz", "depto": "ISW",
         "clases": [
            {"materia": "Arquitectura de SW", "grupo": "SJ", "dias": ["Lunes"], "hora_ini": "11:00", "hora_fin": "13:00", "aula": "D25"},
         ]},
        {"nombre": "Jesús Mares Montes", "depto": "ISW",
         "clases": [
            {"materia": "Desarrollo de Apps Web", "grupo": "SI", "dias": ["Lunes","Miércoles"], "hora_ini": "07:00", "hora_fin": "09:00", "aula": "E32"},
            {"materia": "Desarrollo de Apps Web", "grupo": "S5", "dias": ["Lunes","Miércoles"], "hora_ini": "09:00", "hora_fin": "11:00", "aula": "D22"},
         ]},
        {"nombre": "Yanet Hernández Casimiro", "depto": "ISW",
         "clases": [
            {"materia": "Graficación", "grupo": "S5", "dias": ["Lunes","Miércoles"], "hora_ini": "19:00", "hora_fin": "21:00", "aula": "VIRTUAL"},
            {"materia": "Diseño Comp. e Intérpretes", "grupo": "SF", "dias": ["Martes","Jueves"], "hora_ini": "19:00", "hora_fin": "21:00", "aula": "VIRTUAL"},
            {"materia": "Diseño Comp. e Intérpretes", "grupo": "S3", "dias": ["Martes","Jueves"], "hora_ini": "17:00", "hora_fin": "19:00", "aula": "C5"},
         ]},
        {"nombre": "Marcela Camacho Ávila", "depto": "ISW",
         "clases": [
            {"materia": "Teoría de Lenguajes", "grupo": "SI", "dias": ["Lunes","Miércoles"], "hora_ini": "12:00", "hora_fin": "13:30", "aula": "F13"},
            {"materia": "Estructuras de Datos", "grupo": "SF", "dias": ["Lunes","Miércoles"], "hora_ini": "07:00", "hora_fin": "09:30", "aula": "D22"},
            {"materia": "Estructuras de Datos", "grupo": "S3", "dias": ["Lunes","Miércoles"], "hora_ini": "09:30", "hora_fin": "12:00", "aula": "-"},
         ]},
        {"nombre": "Gerardo Arturo Ávila Vilchis", "depto": "ISW",
         "clases": [
            {"materia": "Teoría de Lenguajes", "grupo": "SJ", "dias": ["Martes","Jueves"], "hora_ini": "10:00", "hora_fin": "12:00", "aula": "D24"},
         ]},
        {"nombre": "José Esteban Ruiz Melo", "depto": "ISW",
         "clases": [
            {"materia": "Teoría de Lenguajes", "grupo": "SH", "dias": ["Sábado"], "hora_ini": "07:00", "hora_fin": "10:00", "aula": "VIRTUAL"},
            {"materia": "Teoría de Lenguajes", "grupo": "S5", "dias": ["Jueves"], "hora_ini": "18:00", "hora_fin": "19:30", "aula": "VIRTUAL"},
            {"materia": "Teoría de Lenguajes", "grupo": "S6", "dias": ["Viernes"], "hora_ini": "19:30", "hora_fin": "21:00", "aula": "VIRTUAL"},
         ]},
        {"nombre": "Mauro Sánchez Sánchez", "depto": "ISW",
         "clases": [
            {"materia": "Estructuras de Datos", "grupo": "SE", "dias": ["Lunes","Miércoles"], "hora_ini": "09:30", "hora_fin": "12:00", "aula": "F12"},
            {"materia": "Estructuras de Datos", "grupo": "S4", "dias": ["Lunes","Miércoles"], "hora_ini": "07:00", "hora_fin": "09:30", "aula": "F12"},
         ]},
        {"nombre": "Angélica Millán Díaz", "depto": "ISW",
         "clases": [
            {"materia": "Estructuras de Datos", "grupo": "SG", "dias": ["Sábado"], "hora_ini": "08:00", "hora_fin": "13:00", "aula": "F12"},
         ]},
        {"nombre": "Brenda Yazmín Reza Curiel", "depto": "ISW",
         "clases": [
            {"materia": "Inter. Humano-Computadora", "grupo": "SE", "dias": ["Martes","Jueves"], "hora_ini": "07:00", "hora_fin": "08:30", "aula": "D22"},
            {"materia": "Inter. Humano-Computadora", "grupo": "S4", "dias": ["Lunes","Miércoles"], "hora_ini": "07:00", "hora_fin": "08:30", "aula": "E37"},
         ]},
        {"nombre": "Griselda Areli Matias Mendoza", "depto": "ISW",
         "clases": [
            {"materia": "Inter. Humano-Computadora", "grupo": "SG", "dias": ["Martes","Jueves"], "hora_ini": "11:00", "hora_fin": "12:30", "aula": "D22"},
            {"materia": "Inter. Humano-Computadora", "grupo": "S3", "dias": ["Martes","Jueves"], "hora_ini": "15:00", "hora_fin": "16:30", "aula": "F13"},
            {"materia": "Diseño Comp. e Intérpretes", "grupo": "SE", "dias": ["Martes","Jueves"], "hora_ini": "09:00", "hora_fin": "11:00", "aula": "F13"},
            {"materia": "Diseño Comp. e Intérpretes", "grupo": "SG", "dias": ["Martes","Jueves"], "hora_ini": "13:00", "hora_fin": "15:00", "aula": "F13"},
         ]},
        {"nombre": "David Hernández Benítez", "depto": "ISW",
         "clases": [
            {"materia": "Arq. de Computadoras", "grupo": "SE", "dias": ["Lunes","Miércoles"], "hora_ini": "07:00", "hora_fin": "09:00", "aula": "D25"},
            {"materia": "Arq. de Computadoras", "grupo": "SF", "dias": ["Viernes"], "hora_ini": "07:00", "hora_fin": "11:00", "aula": "-"},
         ]},
        {"nombre": "Ismael González del Campo", "depto": "ISW",
         "clases": [
            {"materia": "Arq. de Computadoras", "grupo": "S3", "dias": ["Martes","Jueves"], "hora_ini": "07:00", "hora_fin": "09:00", "aula": "F12"},
            {"materia": "Arq. de Computadoras", "grupo": "S4", "dias": ["Martes","Jueves"], "hora_ini": "09:00", "hora_fin": "11:00", "aula": "F12"},
         ]},
        {"nombre": "Lucia Alarcón Márquez", "depto": "Idiomas",
         "clases": [
            {"materia": "Inglés 7", "grupo": "C3", "dias": ["Lunes"], "hora_ini": "09:00", "hora_fin": "11:00", "aula": "B3"},
         ]},
        {"nombre": "Bertha Rodríguez Gutiérrez", "depto": "Idiomas",
         "clases": [
            {"materia": "Inglés 7", "grupo": "I1", "dias": ["Martes","Jueves"], "hora_ini": "19:00", "hora_fin": "21:00", "aula": "VIRTUAL"},
            {"materia": "Inglés 7", "grupo": "I2", "dias": ["Martes","Jueves"], "hora_ini": "17:00", "hora_fin": "19:00", "aula": "VIRTUAL"},
            {"materia": "Inglés 7", "grupo": "P3", "dias": ["Martes","Jueves"], "hora_ini": "15:00", "hora_fin": "17:00", "aula": "VIRTUAL"},
         ]},
        {"nombre": "Erika Lizbeth Alanis Contreras", "depto": "Idiomas",
         "clases": [
            {"materia": "Inglés 7", "grupo": "M2", "dias": ["Martes","Jueves"], "hora_ini": "19:00", "hora_fin": "21:00", "aula": "VIRTUAL"},
         ]},
        {"nombre": "Adriana Carolina Zárate Neri", "depto": "Idiomas",
         "clases": [
            {"materia": "Inglés 7", "grupo": "M1", "dias": ["Martes","Jueves"], "hora_ini": "19:00", "hora_fin": "21:00", "aula": "VIRTUAL"},
         ]},
        {"nombre": "Elizabeth Fierro Moreno", "depto": "Idiomas",
         "clases": [
            {"materia": "Inglés 7", "grupo": "SF", "dias": ["Sábado"], "hora_ini": "07:00", "hora_fin": "11:00", "aula": "VIRTUAL"},
            {"materia": "Inglés 7", "grupo": "SG", "dias": ["Martes","Jueves"], "hora_ini": "19:00", "hora_fin": "21:00", "aula": "VIRTUAL"},
         ]},
        {"nombre": "Víctor Manuel Galán Hernández", "depto": "Idiomas",
         "clases": [
            {"materia": "Inglés 7", "grupo": "SE", "dias": ["Sábado"], "hora_ini": "07:00", "hora_fin": "11:00", "aula": "VIRTUAL"},
            {"materia": "Inglés 7", "grupo": "S4", "dias": ["Viernes"], "hora_ini": "17:00", "hora_fin": "21:00", "aula": "VIRTUAL"},
         ]},
        {"nombre": "Rocío Arriaga Ramírez", "depto": "Idiomas",
         "clases": [
            {"materia": "Inglés 7", "grupo": "SM", "dias": ["Lunes","Miércoles"], "hora_ini": "19:00", "hora_fin": "21:00", "aula": "VIRTUAL"},
         ]},
    ]

    DIAS_ORDEN = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado"]
    HORAS = [f"{h:02d}:00" for h in range(7, 22)]
    COLORES_MAT = ["#1565C0","#2E7D32","#6A1B9A","#E65100","#C62828",
                   "#00695C","#4E342E","#AD1457","#00838F","#37474F"]

    def __init__(self, parent, **kw):
        super().__init__(parent, fg_color=C("bg"), **kw)
        self._maestro_sel = None
        self._ac_visible  = False
        self._ac_idx      = -1
        self._ac_matches  = []   # lista de nombres de maestros coincidentes
        self._build()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=C("surface"), corner_radius=0, height=70)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ih = ctk.CTkFrame(hdr, fg_color="transparent")
        ih.pack(fill="both", expand=True, padx=24, pady=14)
        ctk.CTkLabel(ih, text="👨‍🏫  Horarios por Maestro",
            font=("Helvetica", FS("h2"), "bold"), text_color=C("text")).pack(side="left")
        ctk.CTkLabel(ih, text="Selecciona un maestro para ver su horario semanal",
            font=("Helvetica", FS("small")), text_color=C("text2")).pack(side="left", padx=16)

        # Body: lista maestros (izq) + horario (der)
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=10)
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=5)
        body.rowconfigure(0, weight=1)

        # Panel izquierdo — lista de maestros con filtro
        left = ctk.CTkFrame(body, fg_color=C("surface"), corner_radius=10)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.rowconfigure(1, weight=1)

        ctk.CTkLabel(left, text="Maestros",
            font=("Helvetica", FS("h3"), "bold"), text_color=C("text")
            ).pack(padx=12, pady=(10, 4), anchor="w")

        self._busq_var = ctk.StringVar()
        self._busq_entry = ctk.CTkEntry(left, textvariable=self._busq_var,
                            placeholder_text="🔍 Buscar maestro...",
                            height=34, corner_radius=8,
                            fg_color=C("surface2"), text_color=C("text"),
                            border_color=C("border"))
        self._busq_entry.pack(fill="x", padx=10, pady=(0, 6))
        self._busq_var.trace_add("write", lambda *_: self._on_busq_maestro())
        self._busq_entry.bind("<Down>",   lambda e: (self._ac_mover_m(1),  "break")[1])
        self._busq_entry.bind("<Up>",     lambda e: (self._ac_mover_m(-1), "break")[1])
        self._busq_entry.bind("<Return>", lambda e: (self._ac_confirmar_m(), "break")[1])
        self._busq_entry.bind("<Escape>", lambda e: self._hide_ac_m())
        self._busq_entry.bind("<FocusOut>", lambda e: self.after(180, self._hide_ac_m))

        # Dropdown de autocompletado (se posiciona con place sobre la lista)
        self._ac_m_frame = ctk.CTkFrame(left, fg_color=C("surface"),
            corner_radius=8, border_width=1, border_color=C("accent"))
        self._ac_m_frame.place_forget()

        self._lista_frame = ctk.CTkScrollableFrame(left, fg_color="transparent",
                                                    scrollbar_button_color=C("accent"))
        self._lista_frame.pack(fill="both", expand=True, padx=4, pady=(0, 8))

        # Panel derecho — horario del maestro seleccionado
        self._right = ctk.CTkFrame(body, fg_color=C("surface"), corner_radius=10)
        self._right.grid(row=0, column=1, sticky="nsew")

        self._render_maestros(self.MAESTROS_DB)
        self._render_horario_vacio()

    def _on_busq_maestro(self):
        """Filtra la lista y muestra el dropdown de sugerencias."""
        q = self._busq_var.get().strip().lower()
        self._filtrar_maestros()
        if not q:
            self._hide_ac_m(); return
        matches = [m for m in self.MAESTROS_DB
                   if q in m["nombre"].lower() or q in m["depto"].lower()]
        if not matches:
            self._hide_ac_m(); return
        self._ac_matches = [m["nombre"] for m in matches[:8]]
        self._ac_idx = -1
        self._render_ac_m()

    def _render_ac_m(self):
        """Dibuja el dropdown de sugerencias para maestros."""
        for w in self._ac_m_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self._ac_m_frame, text="Sugerencias",
            font=("Helvetica", FS("small"), "bold"),
            text_color=C("text2")).pack(anchor="w", padx=10, pady=(6, 2))
        for i, nombre in enumerate(self._ac_matches):
            m = next((x for x in self.MAESTROS_DB if x["nombre"] == nombre), None)
            es_sel = (i == self._ac_idx)
            row = ctk.CTkFrame(self._ac_m_frame,
                fg_color=C("accent_bg") if es_sel else "transparent",
                cursor="hand2", corner_radius=6)
            row.pack(fill="x", padx=6, pady=1)
            row.bind("<Enter>", lambda e, r=row: r.configure(fg_color=C("surface2")))
            row.bind("<Leave>", lambda e, r=row, idx=i: r.configure(
                fg_color=C("accent_bg") if idx == self._ac_idx else "transparent"))
            ctk.CTkLabel(row, text=f"👨‍🏫  {nombre}",
                font=("Helvetica", FS("body"), "bold"),
                text_color=C("accent") if es_sel else C("text"),
                anchor="w").pack(anchor="w", padx=10, pady=(4, 0))
            if m:
                ctk.CTkLabel(row, text=f"Depto: {m['depto']}  ·  {len(m['clases'])} grupo(s)",
                    font=("Helvetica", FS("small")),
                    text_color=C("text2"), anchor="w").pack(anchor="w", padx=10, pady=(0, 4))
            _fn = lambda e, nm=nombre: self._select_ac_m(nm)
            for _w in [row] + row.winfo_children():
                _w.bind("<Button-1>", _fn)
        ctk.CTkFrame(self._ac_m_frame, fg_color="transparent", height=4).pack()
        n = len(self._ac_matches)
        h = min(320, 32 + n * 52)
        self._ac_m_frame.place(x=4, y=50, relwidth=1.0, width=-8, height=h)
        self._ac_m_frame.lift()
        self._ac_visible = True

    def _ac_mover_m(self, delta):
        if not self._ac_visible or not self._ac_matches:
            return
        self._ac_idx = (self._ac_idx + delta) % len(self._ac_matches)
        self._render_ac_m()

    def _ac_confirmar_m(self):
        if self._ac_visible and 0 <= self._ac_idx < len(self._ac_matches):
            self._select_ac_m(self._ac_matches[self._ac_idx])
        elif self._ac_visible and self._ac_matches:
            self._select_ac_m(self._ac_matches[0])
        else:
            self._hide_ac_m()

    def _select_ac_m(self, nombre):
        m = next((x for x in self.MAESTROS_DB if x["nombre"] == nombre), None)
        self._busq_var.set(nombre)
        self._hide_ac_m()
        if m:
            self._sel_maestro(m)

    def _hide_ac_m(self):
        if self._ac_visible:
            self._ac_m_frame.place_forget()
            self._ac_visible = False

    def _filtrar_maestros(self):
        q = self._busq_var.get().lower().strip()
        if q:
            filtrado = [m for m in self.MAESTROS_DB if q in m["nombre"].lower()
                        or q in m["depto"].lower()]
        else:
            filtrado = self.MAESTROS_DB
        self._render_maestros(filtrado)

    def _render_maestros(self, lista):
        for w in self._lista_frame.winfo_children():
            w.destroy()
        deptos = {}
        for m in lista:
            deptos.setdefault(m["depto"], []).append(m)
        for depto, maestros in deptos.items():
            ctk.CTkLabel(self._lista_frame, text=depto.upper(),
                font=("Helvetica", 9, "bold"), text_color=C("text3")
                ).pack(anchor="w", padx=6, pady=(8, 2))
            for m in maestros:
                btn = ctk.CTkButton(
                    self._lista_frame,
                    text=f"  {m['nombre']}",
                    anchor="w",
                    height=38, corner_radius=8,
                    fg_color=C("accent") if self._maestro_sel == m["nombre"] else C("surface2"),
                    hover_color=C("accent_dark"),
                    text_color="white" if self._maestro_sel == m["nombre"] else C("text"),
                    font=("Helvetica", 11),
                    command=lambda nm=m: self._sel_maestro(nm)
                )
                btn.pack(fill="x", padx=4, pady=2)

    def _sel_maestro(self, maestro):
        self._maestro_sel = maestro["nombre"]
        self._render_maestros(self.MAESTROS_DB if not self._busq_var.get().strip()
                               else [m for m in self.MAESTROS_DB
                                     if self._busq_var.get().lower() in m["nombre"].lower()])
        self._render_horario_maestro(maestro)

    def _render_horario_vacio(self):
        for w in self._right.winfo_children():
            w.destroy()
        ctk.CTkFrame(self._right, fg_color="transparent", height=40).pack()
        ctk.CTkLabel(self._right, text="👈",
                     font=("Helvetica", 42)).pack(pady=(40, 8))
        ctk.CTkLabel(self._right, text="Selecciona un maestro",
                     font=("Helvetica", 16, "bold"), text_color=C("text")).pack()
        ctk.CTkLabel(self._right,
                     text="Haz clic en un maestro de la lista para ver su horario.",
                     font=("Helvetica", 12), text_color=C("text2")).pack(pady=6)

    def _render_horario_maestro(self, maestro):
        for w in self._right.winfo_children():
            w.destroy()

        # Cabecera maestro
        mhdr = ctk.CTkFrame(self._right, fg_color=C("accent"), corner_radius=0, height=64)
        mhdr.pack(fill="x"); mhdr.pack_propagate(False)
        ctk.CTkLabel(mhdr, text=f"👨‍🏫  {maestro['nombre']}",
                     font=("Helvetica", 15, "bold"), text_color="white").place(x=16, y=10)
        ctk.CTkLabel(mhdr, text=f"Depto: {maestro['depto']}  ·  {len(maestro['clases'])} grupos asignados",
                     font=("Helvetica", 11), text_color="white").place(x=16, y=38)
        # Botón exportar PDF individual del profesor
        ctk.CTkButton(mhdr, text="📥 PDF", width=80, height=28,
                      corner_radius=8, fg_color="white", hover_color="#E8F5E9",
                      text_color=C("accent"), font=("Helvetica", 11, "bold"),
                      command=lambda m=maestro: ExportadorPDF.exportar_horario_profesor(
                          m, parent=self.winfo_toplevel())
                      ).place(relx=1.0, rely=0.5, x=-12, anchor="e")

        # Tabla de clases
        tbl_frame = ctk.CTkScrollableFrame(self._right, fg_color="transparent",
                                            scrollbar_button_color=C("accent"))
        tbl_frame.pack(fill="both", expand=True, padx=10, pady=8)

        # Encabezado tabla
        cols = [("Materia", 220), ("Grupo", 60), ("Días", 160),
                ("Horario", 110), ("Aula", 80), ("Modalidad", 80)]
        hrow = ctk.CTkFrame(tbl_frame, fg_color=C("surface2"), corner_radius=6, height=32)
        hrow.pack(fill="x", pady=(0, 4)); hrow.pack_propagate(False)
        for col_name, col_w in cols:
            ctk.CTkLabel(hrow, text=col_name, width=col_w,
                         font=("Helvetica", 10, "bold"), text_color=C("text2")
                         ).pack(side="left", padx=2)

        mat_colores = {}
        for i, cl in enumerate(maestro["clases"]):
            color_idx = i % len(self.COLORES_MAT)
            mat_colores.setdefault(cl["materia"], self.COLORES_MAT[color_idx])

        for i, cl in enumerate(sorted(maestro["clases"], key=lambda x: x["hora_ini"])):
            aula = cl.get("aula", "-")
            es_virtual = aula.upper() == "VIRTUAL"
            row = ctk.CTkFrame(tbl_frame,
                               fg_color=C("card") if i % 2 == 0 else C("surface2"),
                               corner_radius=8, height=44)
            row.pack(fill="x", pady=2); row.pack_propagate(False)

            # Banda de color por materia
            col_mat = mat_colores.get(cl["materia"], C("accent"))
            band = ctk.CTkFrame(row, fg_color=col_mat, width=4, corner_radius=2)
            band.pack(side="left", fill="y", padx=(2, 4))
            band.pack_propagate(False)

            ctk.CTkLabel(row, text=cl["materia"], width=216,
                         font=("Helvetica", 11, "bold"), text_color=C("text"),
                         anchor="w").pack(side="left", padx=2)
            ctk.CTkLabel(row, text=cl["grupo"], width=60,
                         font=("Helvetica", 11), text_color=C("text2")
                         ).pack(side="left", padx=2)
            ctk.CTkLabel(row, text="/".join(cl["dias"]), width=160,
                         font=("Helvetica", 10), text_color=C("text")
                         ).pack(side="left", padx=2)
            ctk.CTkLabel(row, text=f"{cl['hora_ini']}–{cl['hora_fin']}", width=110,
                         font=("Helvetica", 10), text_color=C("text")
                         ).pack(side="left", padx=2)
            aula_txt = "🌐 Virtual" if es_virtual else aula
            ctk.CTkLabel(row, text=aula_txt, width=80,
                         font=("Helvetica", 10),
                         text_color="#1565C0" if es_virtual else C("text")
                         ).pack(side="left", padx=2)
            modal = "🌐" if es_virtual else "🏫"
            ctk.CTkLabel(row, text=modal, width=40,
                         font=("Helvetica", 14)).pack(side="left", padx=2)

        # Mini tabla semanal canvas
        ctk.CTkLabel(self._right, text="Vista semanal",
                     font=("Helvetica", FS("small"), "bold"), text_color=C("text2")
                     ).pack(anchor="w", padx=14, pady=(4, 0))
        self._render_mini_semana(maestro)

    def _render_mini_semana(self, maestro):
        """Canvas compacto con la semana del maestro."""
        canvas_frame = ctk.CTkFrame(self._right, fg_color="transparent")
        canvas_frame.pack(fill="x", padx=10, pady=(0, 10))

        dias = self.DIAS_ORDEN
        hora_ini_g = 7
        hora_fin_g  = 22
        n_h = hora_fin_g - hora_ini_g
        col_w = 80; row_h = 24; head_h = 24; time_w = 44
        cw = time_w + col_w * len(dias)
        ch = head_h + row_h * n_h

        is_dark = True
        bg_cv  = "#1e1e2e"
        fg_grd = "#2a2a3e"
        fg_hd  = "#2d2d44"
        tx_col = "#ffffff"
        tx_dim = "#888aaa"

        h_sc = ctk.CTkScrollbar(canvas_frame, orientation="horizontal")
        h_sc.pack(side="bottom", fill="x")
        cv = ctk.CTkCanvas(canvas_frame, bg=bg_cv, highlightthickness=0,
                            height=ch, xscrollcommand=h_sc.set)
        cv.pack(fill="x")
        h_sc.configure(command=cv.xview)
        cv.configure(scrollregion=(0, 0, cw, ch))

        # Días header
        for ci, dia in enumerate(dias):
            x0 = time_w + ci * col_w
            cv.create_rectangle(x0, 0, x0 + col_w, head_h, fill=fg_hd, outline="")
            cv.create_text(x0 + col_w//2, head_h//2, text=dia[:3],
                           font=("Helvetica", 8, "bold"), fill=tx_col)

        # Horas
        for hi in range(n_h + 1):
            y = head_h + hi * row_h
            cv.create_line(0, y, cw, y, fill=fg_grd, width=1)
            if hi < n_h:
                cv.create_text(time_w//2, y + row_h//2,
                               text=f"{hora_ini_g + hi:02d}:00",
                               font=("Helvetica", 7), fill=tx_dim)
        for ci in range(len(dias) + 1):
            x = time_w + ci * col_w
            cv.create_line(x, 0, x, ch, fill=fg_grd, width=1)

        def hm(s):
            h, m = map(int, s.split(":"))
            return h + m / 60

        mat_colores = {}
        col_list = self.COLORES_MAT
        for i, cl in enumerate(maestro["clases"]):
            mat_colores.setdefault(cl["materia"], col_list[i % len(col_list)])

        for cl in maestro["clases"]:
            color = mat_colores.get(cl["materia"], C("accent"))
            for dia in cl["dias"]:
                if dia not in dias:
                    continue
                ci = dias.index(dia)
                x0 = time_w + ci * col_w + 1
                yi = hm(cl["hora_ini"]) - hora_ini_g
                yf = hm(cl["hora_fin"]) - hora_ini_g
                y0 = head_h + int(yi * row_h) + 1
                y1 = head_h + int(yf * row_h) - 1
                cv.create_rectangle(x0, y0, x0 + col_w - 2, y1,
                                    fill=color, outline=color)
                label = f"{cl['materia'][:10]}\nGpo {cl['grupo']}"
                cv.create_text(x0 + (col_w-2)//2, (y0+y1)//2,
                               text=label, font=("Helvetica", 7),
                               fill="white", width=col_w-6, justify="center")


# ─────────────────────────────────────────────────────────────────
#  VENTANA PRINCIPAL (sidebar + área de contenido)
# ─────────────────────────────────────────────────────────────────
