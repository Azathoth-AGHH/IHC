# ╔══════════════════════════════════════════════════════════════════╗
# ║  ui_components.py — Componentes base reutilizables de la UI      ║
# ╚══════════════════════════════════════════════════════════════════╝
import customtkinter as ctk
from ui_theme import C, FS

class Card(ctk.CTkFrame):
    def __init__(self, parent, **kw):
        kw.setdefault("fg_color", C("surface"))
        kw.setdefault("corner_radius", 18)
        super().__init__(parent, **kw)

class Btn(ctk.CTkButton):
    def __init__(self, parent, **kw):
        kw.setdefault("fg_color",    C("accent"))
        kw.setdefault("hover_color", C("accent_dark"))
        kw.setdefault("text_color",  "#FFFFFF")
        kw.setdefault("corner_radius", 12)
        kw.setdefault("height", 42)
        kw.setdefault("font", ("Helvetica", FS("body"), "bold"))
        super().__init__(parent, **kw)

class BtnOutline(ctk.CTkButton):
    def __init__(self, parent, **kw):
        kw.setdefault("fg_color",    "transparent")
        kw.setdefault("hover_color", C("accent_bg"))
        kw.setdefault("text_color",  C("accent"))
        kw.setdefault("border_color", C("accent"))
        kw.setdefault("border_width", 2)
        kw.setdefault("corner_radius", 12)
        kw.setdefault("height", 42)
        kw.setdefault("font", ("Helvetica", FS("body"), "bold"))
        super().__init__(parent, **kw)

class SectionHeader(ctk.CTkFrame):
    """Encabezado de sección con título, subtítulo y acento decorativo."""
    def __init__(self, parent, titulo, subtitulo="", icono="", **kw):
        kw.setdefault("fg_color", "transparent")
        super().__init__(parent, **kw)
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x")
        if icono:
            ctk.CTkLabel(row, text=icono, font=("Helvetica", 22),
                         width=32).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(row, text=titulo,
            font=("Helvetica", FS("h2"), "bold"),
            text_color=C("text"), anchor="w").pack(side="left")
        ctk.CTkFrame(self, fg_color=C("accent"), height=3,
                     corner_radius=2).pack(fill="x", pady=(4, 0))
        if subtitulo:
            ctk.CTkLabel(self, text=subtitulo,
                font=("Helvetica", FS("small")),
                text_color=C("text2"), anchor="w").pack(fill="x", pady=(4, 0))

class StatBadge(ctk.CTkFrame):
    """Tarjeta compacta de estadística: ícono + valor + etiqueta."""
    def __init__(self, parent, icono, valor, etiqueta, color=None, **kw):
        color = color or C("accent")
        kw.setdefault("fg_color", C("surface"))
        kw.setdefault("corner_radius", 14)
        super().__init__(parent, **kw)
        ctk.CTkLabel(self, text=icono,
            font=("Helvetica", 24)).pack(pady=(12, 2))
        ctk.CTkLabel(self, text=str(valor),
            font=("Helvetica", FS("h2"), "bold"),
            text_color=color).pack()
        ctk.CTkLabel(self, text=etiqueta,
            font=("Helvetica", FS("small")),
            text_color=C("text2")).pack(pady=(0, 12))

class EventoRow(ctk.CTkFrame):
    """Fila de evento con color de prioridad y datos básicos."""
    _PRIO_COL = {1: "#C94A3A", 2: "#C18D52", 3: "#5A8F76", 4: "#96CDB0"}

    def __init__(self, parent, evento, on_click=None, **kw):
        kw.setdefault("fg_color", C("surface"))
        kw.setdefault("corner_radius", 10)
        super().__init__(parent, **kw)
        prio  = evento.get("prioridad", 3)
        color = self._PRIO_COL.get(prio, C("text3"))
        ctk.CTkFrame(self, fg_color=color, width=4,
                     corner_radius=2).pack(side="left", fill="y", padx=(0, 8))
        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, pady=6)
        ctk.CTkLabel(info, text=evento.get("titulo", ""),
            font=("Helvetica", FS("body"), "bold"),
            text_color=C("text"), anchor="w").pack(fill="x")
        meta = f'{evento.get("categoria", "")}  ·  {evento.get("fecha", "")}  {evento.get("hora_inicio", "")}'
        ctk.CTkLabel(info, text=meta,
            font=("Helvetica", FS("small")),
            text_color=C("text2"), anchor="w").pack(fill="x")
        if on_click:
            self.bind("<Button-1>", lambda e: on_click(evento))
            info.bind("<Button-1>", lambda e: on_click(evento))
