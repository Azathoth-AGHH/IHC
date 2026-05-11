# ╔══════════════════════════════════════════════════════════════════╗
# ║  dialogs.py — Diálogos: Actividad, Comandos de Voz, Lector       ║
# ╚══════════════════════════════════════════════════════════════════╝
import time, threading, uuid, os, logging
import customtkinter as ctk
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox as _msgbox
from ui_theme import C, FS, PREFS
from ui_components import Btn, BtnOutline
from local_db import CATEGORIAS_PERSONAL
from academic_engine import AcademicEngine


# ─────────────────────────────────────────────────────────────────
#  EXPORTADOR PDF — genera PDFs sin dependencias externas pesadas
#  Usa reportlab si está instalado, si no genera HTML imprimible.
# ─────────────────────────────────────────────────────────────────
class ExportadorPDF:
    """
    Exporta agenda o reportes a PDF.
    - Con reportlab: genera PDF nativo.
    - Sin reportlab: genera HTML elegante listo para imprimir/guardar como PDF.
    Siempre muestra diálogo de guardado para que el usuario elija ruta.
    """

    LOGO_ICO = "📄"

    @staticmethod
    def _tiene_reportlab() -> bool:
        try:
            import reportlab  # noqa
            return True
        except ImportError:
            return False

    # ── API pública ───────────────────────────────────────────────
    @classmethod
    def exportar_agenda(cls, actividades: list, titulo: str = "Mi Agenda", parent=None):
        """
        actividades: lista de dicts con keys: titulo, fecha, hora, categoria, descripcion.
        """
        if cls._tiene_reportlab():
            cls._agenda_reportlab(actividades, titulo, parent)
        else:
            cls._agenda_html(actividades, titulo, parent)

    @classmethod
    def exportar_reporte(cls, materias: list, titulo: str = "Reporte Académico", parent=None):
        """
        materias: lista de dicts con keys: nombre, promedio, alumnos, riesgo.
        """
        if cls._tiene_reportlab():
            cls._reporte_reportlab(materias, titulo, parent)
        else:
            cls._reporte_html(materias, titulo, parent)

    # ── Generadores HTML (sin dependencias externas) ──────────────
    @classmethod
    def _agenda_html(cls, actividades, titulo, parent):
        ruta = filedialog.asksaveasfilename(
            parent=parent,
            title="Guardar agenda como…",
            defaultextension=".html",
            filetypes=[("HTML imprimible (PDF)", "*.html"), ("Todos", "*.*")],
            initialfile=f"agenda_{datetime.now().strftime('%Y%m%d')}.html",
        )
        if not ruta:
            return

        filas = ""
        for a in actividades:
            titulo_a  = a.get("titulo", "Sin título")
            fecha     = a.get("fecha", "")
            hora      = a.get("hora", "")
            cat       = a.get("categoria", "")
            desc      = a.get("descripcion", "")
            filas += (
                f"<tr><td>{titulo_a}</td><td>{fecha}</td>"
                f"<td>{hora}</td><td>{cat}</td><td>{desc}</td></tr>\n"
            )

        html = cls._html_base(titulo, f"""
        <table>
          <thead>
            <tr><th>Actividad</th><th>Fecha</th><th>Hora</th>
                <th>Categoría</th><th>Descripción</th></tr>
          </thead>
          <tbody>{filas or '<tr><td colspan="5">Sin actividades registradas</td></tr>'}</tbody>
        </table>
        <p class="footer">Generado por OPTEM · UAEMéx · {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
        """)

        with open(ruta, "w", encoding="utf-8") as f:
            f.write(html)

        cls._abrir_y_avisar(ruta, parent)

    @classmethod
    def _reporte_html(cls, materias, titulo, parent):
        ruta = filedialog.asksaveasfilename(
            parent=parent,
            title="Guardar reporte como…",
            defaultextension=".html",
            filetypes=[("HTML imprimible (PDF)", "*.html"), ("Todos", "*.*")],
            initialfile=f"reporte_{datetime.now().strftime('%Y%m%d')}.html",
        )
        if not ruta:
            return

        filas = ""
        for m in materias:
            nombre  = m.get("nombre", "")
            prom    = m.get("promedio", 0)
            alumnos = m.get("alumnos", 0)
            riesgo  = m.get("riesgo", 0)
            color   = "#2e7d32" if prom >= 80 else "#f57f17" if prom >= 70 else "#c62828"
            filas += (
                f'<tr><td>{nombre}</td>'
                f'<td style="color:{color};font-weight:bold">{prom}</td>'
                f'<td>{alumnos}</td>'
                f'<td style="color:#f57f17">{riesgo}</td>'
                f'<td style="color:#2e7d32">{alumnos - riesgo}</td></tr>\n'
            )

        html = cls._html_base(titulo, f"""
        <table>
          <thead>
            <tr><th>Materia</th><th>Promedio</th><th>Alumnos</th>
                <th>En riesgo</th><th>Regulares</th></tr>
          </thead>
          <tbody>{filas or '<tr><td colspan="5">Sin datos</td></tr>'}</tbody>
        </table>
        <p class="footer">Generado por OPTEM · UAEMéx · {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
        """)

        with open(ruta, "w", encoding="utf-8") as f:
            f.write(html)

        cls._abrir_y_avisar(ruta, parent)

    @staticmethod
    def _html_base(titulo: str, cuerpo: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{titulo}</title>
<style>
  @page {{ margin: 20mm; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #1a1a2e;
          background: #fff; margin: 0; padding: 24px; }}
  h1   {{ color: #2e7d32; border-bottom: 3px solid #2e7d32;
          padding-bottom: 8px; font-size: 24px; }}
  h2   {{ color: #555; font-size: 14px; font-weight: normal; margin-top: -8px; }}
  table{{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 13px; }}
  th   {{ background: #2e7d32; color: #fff; padding: 10px 12px; text-align: left; }}
  td   {{ padding: 8px 12px; border-bottom: 1px solid #e0e0e0; }}
  tr:nth-child(even) td {{ background: #f9fbe7; }}
  .footer {{ margin-top: 32px; font-size: 11px; color: #888;
             border-top: 1px solid #ddd; padding-top: 8px; }}
  @media print {{
    body {{ padding: 0; }}
    button {{ display: none; }}
  }}
</style>
</head>
<body>
<h1>🎓 {titulo}</h1>
<h2>OPTEM · Agenda Virtual Inteligente · UAEMéx</h2>
{cuerpo}
<script>window.onload = function(){{ window.print && window.print(); }}</script>
</body>
</html>"""

    @staticmethod
    def _abrir_y_avisar(ruta: str, parent):
        """Abre el archivo con el programa predeterminado y muestra confirmación."""
        import subprocess, sys
        try:
            if sys.platform.startswith("win"):
                os.startfile(ruta)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", ruta])
            else:
                subprocess.Popen(["xdg-open", ruta])
        except Exception:
            pass
        _msgbox.showinfo(
            "✅ Exportado",
            f"Archivo guardado en:\n{ruta}\n\n"
            "Se abrirá en tu navegador. Usa Ctrl+P para imprimir o guardar como PDF.",
            parent=parent,
        )

    # ── Generadores reportlab (si está instalado) ─────────────────
    @classmethod
    def _agenda_reportlab(cls, actividades, titulo, parent):
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        ruta = filedialog.asksaveasfilename(
            parent=parent, title="Guardar agenda PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"agenda_{datetime.now().strftime('%Y%m%d')}.pdf",
        )
        if not ruta:
            return

        doc = SimpleDocTemplate(ruta, pagesize=A4)
        estilos = getSampleStyleSheet()
        historia = [
            Paragraph(f"<b>{titulo}</b>", estilos["Title"]),
            Paragraph(f"OPTEM · UAEMéx · {datetime.now().strftime('%d/%m/%Y')}", estilos["Normal"]),
            Spacer(1, 20),
        ]

        data = [["Actividad", "Fecha", "Hora", "Categoría", "Descripción"]]
        for a in actividades:
            data.append([
                a.get("titulo", ""), a.get("fecha", ""),
                a.get("hora", ""), a.get("categoria", ""),
                a.get("descripcion", "")[:40],
            ])
        if len(data) == 1:
            data.append(["Sin actividades", "", "", "", ""])

        tabla = Table(data, repeatRows=1)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2e7d32")),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fbe7")]),
            ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("FONTSIZE",   (0, 0), (-1, -1), 9),
            ("PADDING",    (0, 0), (-1, -1), 6),
        ]))
        historia.append(tabla)
        doc.build(historia)
        cls._abrir_y_avisar(ruta, parent)

    @classmethod
    def _reporte_reportlab(cls, materias, titulo, parent):
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        ruta = filedialog.asksaveasfilename(
            parent=parent, title="Guardar reporte PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"reporte_{datetime.now().strftime('%Y%m%d')}.pdf",
        )
        if not ruta:
            return

        doc = SimpleDocTemplate(ruta, pagesize=A4)
        estilos = getSampleStyleSheet()
        historia = [
            Paragraph(f"<b>{titulo}</b>", estilos["Title"]),
            Paragraph(f"OPTEM · UAEMéx · {datetime.now().strftime('%d/%m/%Y')}", estilos["Normal"]),
            Spacer(1, 20),
        ]

        data = [["Materia", "Promedio", "Alumnos", "En riesgo", "Regulares"]]
        for m in materias:
            prom = m.get("promedio", 0)
            alumnos = m.get("alumnos", 0)
            riesgo = m.get("riesgo", 0)
            data.append([m.get("nombre", ""), str(prom), str(alumnos), str(riesgo), str(alumnos - riesgo)])

        tabla = Table(data, repeatRows=1)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2e7d32")),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fbe7")]),
            ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("FONTSIZE",   (0, 0), (-1, -1), 10),
            ("PADDING",    (0, 0), (-1, -1), 7),
        ]))
        historia.append(tabla)
        doc.build(historia)
        cls._abrir_y_avisar(ruta, parent)

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
    - Navega widget a widget con ↑/↓  (← → también)
    - Tab/Shift+Tab: avanza/retrocede rápido saltando 5 elementos
    - PageDown/PageUp: saltar al inicio/fin de la sección actual
    - Enter / Espacio: activan el elemento enfocado
    - Escape: anuncia posición actual sin moverse
    - Resalta visualmente el elemento con borde cyan
    - Describe con detalle qué hace cada botón/campo
    - No se queda atascado: siempre avanza circularmente
    - Re-escanea automáticamente al cambiar de panel
    """

    _instancia = None   # singleton por ventana

    TIPOS_ENFOCABLES = (
        ctk.CTkButton, ctk.CTkSwitch, ctk.CTkCheckBox,
        ctk.CTkRadioButton, ctk.CTkOptionMenu, ctk.CTkEntry,
    )

    # Mapeo de textos comunes → descripciones habladas más claras
    _DESC_BOTONES = {
        "◀": "Botón anterior, retroceder",
        "▶": "Botón siguiente, avanzar",
        "▲": "Subir",
        "▼": "Bajar",
        "✕": "Cerrar ventana",
        "✓": "Confirmar",
        "✗": "Cancelar",
        "➤": "Enviar",
        "🎙": "Abrir comandos de voz",
        "🔔": "Notificaciones",
        "🤖": "Asistente de inteligencia artificial",
        "+": "Agregar nuevo elemento",
        "−": "Eliminar elemento",
        "💾": "Guardar",
        "📥": "Exportar PDF",
        "📄": "Exportar a PDF",
    }

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
    def rescanear_panel(cls, delay_ms: int = 350, nombre_panel: str = ""):
        """Limpia cursor/resaltado y re-escanea la UI tras cambiar de panel."""
        inst = cls._instancia
        if inst is None or not getattr(inst, "_activo", False):
            return
        inst._idx = 0
        if inst._resaltado:
            try:
                if inst._resaltado.winfo_exists():
                    inst._resaltado.configure(border_width=0)
            except Exception:
                pass
            inst._resaltado = None
        if getattr(inst, "_cursor_lbl", None):
            try:
                if inst._cursor_lbl.winfo_exists():
                    inst._cursor_lbl.destroy()
            except Exception:
                pass
            inst._cursor_lbl = None
        if nombre_panel:
            try:
                inst._hablar(f"Navegando a {nombre_panel}")
            except Exception:
                pass
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
                    msg = (
                        "Lector de pantalla activado. "
                        "Usa las flechas arriba y abajo para navegar elemento a elemento. "
                        "Tab para saltar de 5 en 5. "
                        "Inicio y Fin para ir al primer o último elemento. "
                        "Enter o Espacio para activar. "
                        "Escape para saber dónde estás."
                    )
                    self._hablar(msg)
                    for delay in (600, 1400):
                        self._root.after(delay, lambda m=msg: self._hablar(m))
                    self._root.after(2400, lambda: self._enfocar(self._idx))
                else:
                    self._enfocar(self._idx)
            else:
                if anunciar_activacion:
                    self._hablar("Lector de pantalla activado. No se encontraron elementos interactivos.")
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
            ("<Down>",      self._siguiente),
            ("<Right>",     self._siguiente),
            ("<Up>",        self._anterior),
            ("<Left>",      self._anterior),
            ("<Tab>",       self._saltar_adelante),
            ("<Shift-Tab>", self._saltar_atras),
            ("<Next>",      self._ir_al_final),      # PageDown
            ("<Prior>",     self._ir_al_inicio),     # PageUp
            ("<Return>",    self._activar),
            ("<space>",     self._activar),
            ("<Escape>",    self._anunciar_posicion),
        ]
        self._prev_handlers = {}

        def _make_handler(fn):
            def handler(e):
                w = e.widget
                try:
                    if isinstance(w, (tk.Entry, tk.Text)):
                        return
                    cls = w.__class__.__name__
                    if cls in ("Entry", "Text"):
                        return
                except Exception:
                    pass
                # Siempre ejecutar — nunca bloquearse
                try:
                    fn()
                except Exception:
                    pass
                return "break"
            return handler

        for key, fn in bindings:
            try:
                prev = root.bind_all(key)
                self._prev_handlers[key] = prev if prev else ""
            except Exception:
                self._prev_handlers[key] = ""
            h = _make_handler(fn)
            root.bind_all(key, h)
            self._bindings.append((key, h))

    def _siguiente(self):
        if not self._elementos:
            self._escanear(); return
        self._idx = (self._idx + 1) % len(self._elementos)
        self._enfocar(self._idx)

    def _anterior(self):
        if not self._elementos:
            self._escanear(); return
        self._idx = (self._idx - 1) % len(self._elementos)
        self._enfocar(self._idx)

    def _saltar_adelante(self):
        """Salta 5 elementos hacia adelante (Tab)."""
        if not self._elementos:
            self._escanear(); return
        self._idx = (self._idx + 5) % len(self._elementos)
        self._enfocar(self._idx)

    def _saltar_atras(self):
        """Salta 5 elementos hacia atrás (Shift+Tab)."""
        if not self._elementos:
            self._escanear(); return
        self._idx = (self._idx - 5) % len(self._elementos)
        self._enfocar(self._idx)

    def _ir_al_inicio(self):
        """PageUp — va al primer elemento."""
        if not self._elementos:
            return
        self._idx = 0
        self._enfocar(self._idx)
        self._hablar("Inicio de la página")

    def _ir_al_final(self):
        """PageDown — va al último elemento."""
        if not self._elementos:
            return
        self._idx = len(self._elementos) - 1
        self._enfocar(self._idx)
        self._hablar("Fin de la página")

    def _anunciar_posicion(self):
        """Escape — anuncia posición actual sin moverse."""
        if not self._elementos:
            self._hablar("Sin elementos interactivos en esta pantalla"); return
        texto = self._leer_widget(self._elementos[self._idx])
        self._hablar(f"Estás en: {texto}. Posición {self._idx + 1} de {len(self._elementos)}")

    def _enfocar(self, idx):
        # Quitar resaltado anterior de forma segura
        if self._resaltado:
            try:
                w = self._resaltado
                if hasattr(w, "configure") and w.winfo_exists():
                    w.configure(border_width=0)
            except Exception:
                pass
            self._resaltado = None
        # Quitar indicador de cursor anterior
        if hasattr(self, "_cursor_lbl") and self._cursor_lbl:
            try:
                if self._cursor_lbl.winfo_exists():
                    self._cursor_lbl.destroy()
            except Exception:
                pass
            self._cursor_lbl = None

        # Si la lista está vacía o el widget ya no existe, re-escanear
        if not self._elementos:
            return
        # Verificar que el widget en idx siga existiendo
        widget = self._elementos[idx]
        try:
            if not widget.winfo_exists():
                # Re-escanear y reintentar desde el inicio
                self._escanear()
                return
        except Exception:
            self._escanear()
            return

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
                wy = widget.winfo_rooty() - self._root.winfo_rooty() - 22
                lbl.place(x=max(0, wx), y=max(0, wy))
                self._cursor_lbl = lbl
            except Exception:
                self._cursor_lbl = None
        except Exception:
            pass

        # Intentar hacer scroll para que sea visible en scrollable frames
        try:
            widget.update_idletasks()
            # Buscar el CTkScrollableFrame más cercano y hacer scroll
            parent = widget.master
            for _ in range(8):
                if parent is None:
                    break
                if isinstance(parent, ctk.CTkScrollableFrame):
                    try:
                        # Calcular posición relativa y hacer scroll
                        wy_rel = widget.winfo_rooty() - parent.winfo_rooty()
                        ph = parent.winfo_height()
                        if ph > 0:
                            frac = max(0.0, min(1.0, (wy_rel - 40) / max(1, ph)))
                            parent._parent_canvas.yview_moveto(frac)
                    except Exception:
                        pass
                    break
                parent = getattr(parent, "master", None)
        except Exception:
            pass

        # Leer en voz alta
        texto = self._leer_widget(widget)
        tipo  = self._tipo_widget(widget)
        pos   = f"{idx + 1} de {len(self._elementos)}"
        self._hablar(f"{tipo}: {texto}. {pos}")

    def _tipo_widget(self, widget) -> str:
        """Devuelve el tipo de widget en español para el anuncio de voz."""
        tipos = {
            "CTkButton":      "Botón",
            "CTkSwitch":      "Interruptor",
            "CTkCheckBox":    "Casilla de verificación",
            "CTkRadioButton": "Opción de selección",
            "CTkOptionMenu":  "Menú desplegable",
            "CTkEntry":       "Campo de texto",
        }
        return tipos.get(widget.__class__.__name__, "Control")

    def _contexto_padre(self, widget, niveles=1) -> str:
        """Busca texto de label en el frame padre (contexto del switch/botón)."""
        padre = widget.master
        for _ in range(niveles):
            if padre is None:
                break
            for child in padre.winfo_children():
                if child is widget:
                    continue
                try:
                    ct = child.cget("text")
                    if ct and str(ct).strip() and len(str(ct).strip()) > 1:
                        return str(ct).strip()
                except Exception:
                    pass
            padre = getattr(padre, "master", None)
        return ""

    def _leer_widget(self, widget):
        """Extrae texto descriptivo del widget para leerlo en voz alta."""
        # 1. Atributo personalizado _lector_desc tiene prioridad
        desc = getattr(widget, "_lector_desc", None)
        if desc:
            return str(desc)

        # 2. El widget tiene texto propio
        try:
            t = widget.cget("text")
            if t and str(t).strip():
                texto = str(t).strip()
                # Buscar en mapa de descripciones para iconos/símbolos
                if texto in self._DESC_BOTONES:
                    return self._DESC_BOTONES[texto]
                # Texto muy corto (emoji/símbolo): buscar contexto en padre
                if len(texto) <= 4:
                    contexto = self._contexto_padre(widget)
                    if contexto:
                        if isinstance(widget, ctk.CTkSwitch):
                            estado = "activado" if widget.get() else "desactivado"
                            return f"{contexto}, {estado}"
                        return f"{contexto}: {texto}"
                # Para switches con texto indicar estado
                if isinstance(widget, ctk.CTkSwitch):
                    estado = "activado" if widget.get() else "desactivado"
                    contexto = self._contexto_padre(widget)
                    desc_sw = contexto if contexto else texto
                    return f"{desc_sw}, {estado}"
                return texto
        except Exception:
            pass

        # 3. Switch sin texto: buscar label en padre/abuelo
        if isinstance(widget, ctk.CTkSwitch):
            contexto = self._contexto_padre(widget, niveles=2)
            estado = "activado" if widget.get() else "desactivado"
            return f"{contexto or 'Opción'}, {estado}"

        # 4. CTkEntry: leer contenido o placeholder
        if isinstance(widget, ctk.CTkEntry):
            try:
                contenido = widget.get()
                if contenido.strip():
                    return f"contiene: {contenido.strip()}"
                ph = widget.cget("placeholder_text")
                if ph:
                    return f"placeholder: {ph}"
            except Exception:
                pass
            return "campo vacío"

        # 5. Buscar texto en hijos directos
        try:
            for child in widget.winfo_children():
                try:
                    ct = child.cget("text")
                    if ct and str(ct).strip():
                        t2 = str(ct).strip()
                        return self._DESC_BOTONES.get(t2, t2)
                except Exception:
                    pass
        except Exception:
            pass

        # 6. Fallback: tipo de widget
        return self._tipo_widget(widget)

    def _activar(self):
        if not self._elementos or self._idx >= len(self._elementos):
            self._escanear(); return
        widget = self._elementos[self._idx]
        try:
            if isinstance(widget, ctk.CTkButton):
                widget.invoke()
                # Re-escanear tras presionar botón (puede cambiar el panel)
                self._root.after(500, self._escanear)
            elif isinstance(widget, ctk.CTkSwitch):
                widget.toggle()
                # Anunciar nuevo estado
                texto = self._leer_widget(widget)
                self._hablar(texto)
            elif isinstance(widget, ctk.CTkCheckBox):
                widget.toggle()
                estado = "marcado" if widget.get() else "desmarcado"
                self._hablar(f"{self._leer_widget(widget)}, {estado}")
            elif isinstance(widget, ctk.CTkRadioButton):
                widget.invoke()
                self._hablar(f"Seleccionado: {self._leer_widget(widget)}")
            elif isinstance(widget, ctk.CTkEntry):
                widget.focus_set()
                self._hablar("Campo de texto activo, escribe tu valor")
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
    """
    Panel de comandos de voz con:
    - Comandos ampliados organizados por categoría
    - Clic directo en cualquier comando para ejecutarlo sin hablar
    - Transcripción en tiempo real
    - Reconocimiento robusto con normalización de tildes
    """

    # ── Comandos comunes a ambos roles ────────────────────────────
    COMANDOS_COMUNES = {
        "inicio":          ("Inicio",  "Ir a la pantalla de inicio"),
        "ir a inicio":     ("Inicio",  "Ir a inicio"),
        "regresar":        ("Inicio",  "Regresar al inicio"),
        "ajustes":         ("Ajustes", "Abrir configuración"),
        "configuracion":   ("Ajustes", "Abrir configuración"),
        "configuración":   ("Ajustes", "Abrir configuración"),
        "opciones":        ("Ajustes", "Abrir ajustes"),
        "preferencias":    ("Ajustes", "Abrir preferencias"),
        "settings":        ("Ajustes", "Abrir configuración"),
    }

    # ── Solo Estudiante ───────────────────────────────────────────
    COMANDOS_EST = {
        # Agenda
        "agenda":              ("Mi Agenda",   "Ver agenda semanal"),
        "mi agenda":           ("Mi Agenda",   "Abrir mi agenda"),
        "ver agenda":          ("Mi Agenda",   "Ver agenda"),
        "calendario":          ("Mi Agenda",   "Abrir calendario"),
        "semana":              ("Mi Agenda",   "Ver semana actual"),
        "hoy":                 ("Mi Agenda",   "Ver actividades de hoy"),
        "dia de hoy":          ("Mi Agenda",   "Ver actividades de hoy"),
        "mañana":              ("Mi Agenda",   "Ver agenda"),
        # Actividades
        "actividades":         ("Actividades", "Ver actividades y tareas"),
        "tareas":              ("Actividades", "Ver tareas pendientes"),
        "mis actividades":     ("Actividades", "Ver mis actividades"),
        "mis tareas":          ("Actividades", "Ver mis tareas"),
        "pendientes":          ("Actividades", "Ver pendientes"),
        "entregas":            ("Actividades", "Ver entregas"),
        "deberes":             ("Actividades", "Ver tareas"),
        "trabajos":            ("Actividades", "Ver trabajos pendientes"),
        # Pomodoro
        "pomodoro":            ("Pomodoro",    "Iniciar temporizador Pomodoro"),
        "temporizador":        ("Pomodoro",    "Abrir temporizador"),
        "timer":               ("Pomodoro",    "Abrir timer"),
        "concentrarme":        ("Pomodoro",    "Modo concentración"),
        "estudiar":            ("Pomodoro",    "Iniciar sesión de estudio"),
        "enfoque":             ("Pomodoro",    "Modo enfoque"),
        "concentracion":       ("Pomodoro",    "Iniciar concentración"),
        "concentración":       ("Pomodoro",    "Iniciar concentración"),
        "modo estudio":        ("Pomodoro",    "Activar modo estudio"),
        # Logros
        "logros":              ("Logros",      "Ver logros y progreso"),
        "mis logros":          ("Logros",      "Ver mis logros"),
        "estadisticas":        ("Logros",      "Ver estadísticas"),
        "estadísticas":        ("Logros",      "Ver estadísticas"),
        "progreso":            ("Logros",      "Ver mi progreso"),
        "puntos":              ("Logros",      "Ver puntos XP"),
        "xp":                  ("Logros",      "Ver experiencia acumulada"),
        "nivel":               ("Logros",      "Ver mi nivel"),
        "racha":               ("Logros",      "Ver mi racha"),
        "logros academicos":   ("Logros",      "Ver logros académicos"),
        "logros académicos":   ("Logros",      "Ver logros académicos"),
        # Reinscripción
        "reinscripcion":       ("Reinscripción", "Ver reinscripción"),
        "reinscripción":       ("Reinscripción", "Ver reinscripción"),
        "inscripcion":         ("Reinscripción", "Ver inscripción"),
        "inscripción":         ("Reinscripción", "Ver inscripción"),
        "materias":            ("Reinscripción", "Ver mis materias"),
        "inscribirme":         ("Reinscripción", "Abrir reinscripción"),
    }

    # ── Solo Administrativo ───────────────────────────────────────
    COMANDOS_ADM = {
        # Tareas globales
        "tareas globales":     ("Tareas globales", "Gestionar tareas globales"),
        "tareas":              ("Tareas globales", "Ver tareas"),
        "global":              ("Tareas globales", "Ver tareas globales"),
        "crear tarea":         ("Tareas globales", "Crear nueva tarea"),
        "nueva tarea":         ("Tareas globales", "Crear nueva tarea"),
        "asignar tarea":       ("Tareas globales", "Asignar tarea a alumnos"),
        # Reportes
        "reportes":            ("Reportes",        "Ver reportes académicos"),
        "ver reportes":        ("Reportes",        "Abrir reportes"),
        "reporte":             ("Reportes",        "Ver reporte"),
        "estadisticas":        ("Reportes",        "Ver estadísticas"),
        "estadísticas":        ("Reportes",        "Ver estadísticas"),
        "analisis":            ("Reportes",        "Ver análisis"),
        "análisis":            ("Reportes",        "Ver análisis académico"),
        "exportar":            ("Reportes",        "Exportar reporte a PDF"),
        # Alumnos
        "alumnos":             ("Alumnos",         "Gestionar alumnos"),
        "ver alumnos":         ("Alumnos",         "Ver listado de alumnos"),
        "estudiantes":         ("Alumnos",         "Ver estudiantes"),
        "lista alumnos":       ("Alumnos",         "Ver lista de alumnos"),
        "buscar alumno":       ("Alumnos",         "Buscar alumno"),
        "listado":             ("Alumnos",         "Ver listado de alumnos"),
        # Horarios
        "horarios":            ("Horarios",        "Ver horarios de clases"),
        "ver horarios":        ("Horarios",        "Abrir horarios"),
        "horario":             ("Horarios",        "Ver horario"),
        "cronograma":          ("Horarios",        "Ver cronograma"),
        # Clases
        "clases":              ("Clases",          "Gestionar clases"),
        "ver clases":          ("Clases",          "Ver clases"),
        "clase":               ("Clases",          "Ver clases"),
        "materias":            ("Clases",          "Ver materias"),
        "grupos":              ("Clases",          "Ver grupos de clases"),
    }

    # ── Categorías para mostrar en UI ─────────────────────────────
    _CATS_EST = {
        "📅 Agenda":          ["agenda","mi agenda","ver agenda","semana","hoy","calendario"],
        "📋 Actividades":     ["actividades","tareas","mis tareas","pendientes","entregas","trabajos"],
        "⏱ Pomodoro":        ["pomodoro","temporizador","estudiar","concentrarme","modo estudio"],
        "⭐ Logros":          ["logros","mis logros","estadísticas","progreso","xp","racha","nivel"],
        "🏫 Reinscripción":  ["reinscripcion","inscripcion","materias","inscribirme"],
        "⚙️ General":         ["inicio","ajustes","configuracion","opciones"],
    }
    _CATS_ADM = {
        "📋 Tareas":          ["tareas globales","nueva tarea","crear tarea","asignar tarea"],
        "📊 Reportes":        ["reportes","ver reportes","estadísticas","análisis","exportar"],
        "👥 Alumnos":         ["alumnos","ver alumnos","estudiantes","buscar alumno"],
        "🗓 Horarios":        ["horarios","ver horarios","horario","cronograma"],
        "📚 Clases":          ["clases","ver clases","materias","grupos"],
        "⚙️ General":         ["inicio","ajustes","configuracion","opciones"],
    }

    def __init__(self, parent, on_cmd, rol="Estudiante"):
        super().__init__(parent)
        self.on_cmd      = on_cmd
        self.rol         = rol
        self._escuchando = False
        self._hilo_voz   = None

        self.COMANDOS = dict(self.COMANDOS_COMUNES)
        if rol == "Administrativo":
            self.COMANDOS.update(self.COMANDOS_ADM)
            self._cats = self._CATS_ADM
        else:
            self.COMANDOS.update(self.COMANDOS_EST)
            self._cats = self._CATS_EST

        self.title("🎙  Comandos de voz")
        self.geometry("540x660")
        self.resizable(True, True)
        self.minsize(460, 520)
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
        # ── Header ───────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color=C("accent"), corner_radius=0, height=72)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="🎙  Comandos de Voz",
            font=("Helvetica", FS("h2"), "bold"), text_color="white"
            ).place(relx=.5, rely=.5, anchor="center")

        body = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                       scrollbar_button_color=C("accent"))
        body.pack(fill="both", expand=True, padx=18, pady=10)

        # Aviso si faltan libs
        if not self._libs_ok:
            warn = ctk.CTkFrame(body, fg_color=C("surface"), corner_radius=14)
            warn.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(warn, text="⚠️  Instala las bibliotecas para usar voz",
                font=("Helvetica", FS("body"), "bold"), text_color=C("amber")).pack(pady=(16, 4))
            ctk.CTkLabel(warn,
                text="pip install SpeechRecognition pyaudio",
                font=("Helvetica", FS("small")), text_color=C("text")).pack(padx=20, pady=(0, 16))

        # Rol e instrucción
        rol_icon = "🏛️" if self.rol == "Administrativo" else "🎓"
        ctk.CTkLabel(body, text=f"{rol_icon}  Modo: {self.rol}  ·  Haz clic en un comando para ejecutarlo directamente",
            font=("Helvetica", FS("small")), text_color=C("text2")).pack(anchor="w", pady=(0, 8))

        # Estado + botón mic
        self.lbl_estado = ctk.CTkLabel(body,
            text="🔴  Listo" if self._libs_ok else "🔴  Sin micrófono",
            font=("Helvetica", FS("body"), "bold"), text_color=C("text"))
        self.lbl_estado.pack()

        self.lbl_transcripcion = ctk.CTkLabel(body, text="",
            font=("Helvetica", FS("small")), text_color=C("text3"),
            wraplength=460, justify="center")
        self.lbl_transcripcion.pack(pady=(2, 4))

        self.btn_mic = Btn(body, text="🎙  Escuchar comando", width=220, height=50,
            fg_color=C("accent") if self._libs_ok else C("border"),
            command=self._escuchar if self._libs_ok else lambda: None)
        self.btn_mic.pack(pady=(0, 6))

        self.lbl_resultado = ctk.CTkLabel(body, text="",
            font=("Helvetica", FS("body")), text_color=C("text2"),
            wraplength=440, justify="center")
        self.lbl_resultado.pack(pady=(0, 10))

        ctk.CTkFrame(body, fg_color=C("border"), height=1).pack(fill="x", pady=(0, 10))

        # ── Comandos por categoría ────────────────────────────────
        ctk.CTkLabel(body, text="📋  Comandos disponibles  —  haz clic para ejecutar",
            font=("Helvetica", FS("body"), "bold"), text_color=C("text")).pack(anchor="w", pady=(0, 8))

        for cat_nombre, claves in self._cats.items():
            cmds = [(c, self.COMANDOS[c]) for c in claves if c in self.COMANDOS]
            if not cmds:
                continue
            # Cabecera de categoría
            cat_hdr = ctk.CTkFrame(body, fg_color=C("surface"), corner_radius=10)
            cat_hdr.pack(fill="x", pady=(0, 4))
            ctk.CTkLabel(cat_hdr, text=f"  {cat_nombre}  ({len(cmds)})",
                font=("Helvetica", FS("small"), "bold"), text_color=C("text"),
                anchor="w").pack(fill="x", padx=8, pady=(8, 4))

            for clave, (tab, desc) in cmds:
                row = ctk.CTkFrame(cat_hdr, fg_color=C("surface2"), corner_radius=6)
                row.pack(fill="x", padx=8, pady=2)
                # Botón clic-para-ejecutar
                ctk.CTkButton(row, text=f"«{clave}»",
                    font=("Helvetica", FS("small"), "bold"), text_color=C("accent"),
                    fg_color="transparent", hover_color=C("accent_bg"),
                    anchor="w", width=170, height=28,
                    command=lambda t=tab: self._ejecutar_directo(t),
                ).pack(side="left", padx=(6, 0), pady=3)
                ctk.CTkLabel(row, text=f"→ {desc}",
                    font=("Helvetica", FS("small")), text_color=C("text3"),
                    anchor="w").pack(side="left", padx=6)
            ctk.CTkFrame(body, fg_color="transparent", height=2).pack()

        ctk.CTkFrame(body, fg_color="transparent", height=6).pack()
        BtnOutline(self, text="Cerrar", width=120, command=self.destroy).pack(pady=(0, 14))

    def _ejecutar_directo(self, tab: str):
        """Ejecuta un comando directamente al hacer clic (sin usar voz)."""
        try:
            self.grab_release()
        except Exception:
            pass
        try:
            self.on_cmd(tab)
        except Exception:
            pass
        try:
            self.after(80, self.destroy)
        except Exception:
            pass

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
        if self._hilo_voz and self._hilo_voz.is_alive():
            self.after(120, self._poll_estado)

    def _actualizar_transcripcion(self, texto):
        try:
            self.lbl_transcripcion.configure(text=f"✍️  {texto}")
            self.update_idletasks()
        except Exception:
            pass

    def _reconocer_hilo(self):
        try:
            import speech_recognition as sr
            rec = sr.Recognizer()
            rec.energy_threshold = 300
            rec.dynamic_energy_threshold = True
            rec.pause_threshold = 0.6

            with sr.Microphone() as src:
                rec.adjust_for_ambient_noise(src, duration=0.3)
                self.after(0, lambda: self.lbl_transcripcion.configure(text="🎤 Habla ahora…"))
                try:
                    audio = rec.listen(src, timeout=7, phrase_time_limit=6)
                except sr.WaitTimeoutError:
                    self.after(0, lambda: self._fin_reconocimiento(
                        "⏱  Sin respuesta. Intenta de nuevo.", C("amber"), None))
                    return

            self.after(0, lambda: self.lbl_transcripcion.configure(text="⏳ Procesando…"))
            try:
                texto = rec.recognize_google(audio, language="es-MX").lower()
            except sr.UnknownValueError:
                self.after(0, lambda: self._fin_reconocimiento(
                    "❓ No se entendió. Habla más claro.", C("amber"), None))
                return
            except sr.RequestError as e:
                self.after(0, lambda err=e: self._fin_reconocimiento(
                    f"⚠  Sin conexión: {err}", C("red"), None))
                return

            # Efecto de escritura gradual
            def _escribir(tc, pos=0):
                try:
                    self.lbl_transcripcion.configure(text=f"✍️  {tc[:pos+1]}")
                    if pos + 1 < len(tc):
                        self.after(28, lambda: _escribir(tc, pos + 1))
                except Exception:
                    pass
            self.after(0, lambda t=texto: _escribir(t))

            # Normalizar: sin tildes, minúsculas
            import unicodedata
            def _norm(s):
                return ''.join(
                    c for c in unicodedata.normalize('NFD', s.lower())
                    if unicodedata.category(c) != 'Mn')

            texto_norm = _norm(texto)
            encontrado_tab = None
            mejor_clave = ""
            for clave, (tab, _) in self.COMANDOS.items():
                cn = _norm(clave)
                if cn in texto_norm and len(cn) > len(mejor_clave):
                    encontrado_tab = tab
                    mejor_clave = cn

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
                    self.grab_release()
                except Exception:
                    pass
                try:
                    self.on_cmd(t)
                except Exception:
                    pass
                try:
                    self.after(80, self.destroy)
                except Exception:
                    pass
            self.after(600, _navegar)


# ─────────────────────────────────────────────────────────────────
#  PANEL: AJUSTES
# ─────────────────────────────────────────────────────────────────
