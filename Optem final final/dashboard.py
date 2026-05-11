# ╔══════════════════════════════════════════════════════════════════╗
# ║  dashboard.py — Módulo de métricas y resumen general             ║
# ╚══════════════════════════════════════════════════════════════════╝
"""
Dashboard de métricas del usuario. Proporciona un resumen consolidado
de XP, racha, actividades pendientes y progreso del ciclo académico.
"""
from datetime import datetime


class DashboardMetrics:
    """Calcula y expone las métricas clave para la vista de inicio."""

    def __init__(self, datos: dict):
        """
        :param datos: dict completo cargado por DataBridge (perfil, actividades, etc.)
        """
        self._datos = datos or {}

    # ── Perfil ────────────────────────────────────────────────────
    @property
    def xp(self) -> int:
        return int(self._datos.get("perfil", {}).get("xp", 0))

    @property
    def nivel(self) -> str:
        return self._datos.get("perfil", {}).get("nivel", "Novato")

    @property
    def racha(self) -> int:
        raw = self._datos.get("perfil", {}).get("racha", 0)
        return int(str(raw).replace("🔥", "").strip() or 0)

    # ── Actividades ───────────────────────────────────────────────
    def actividades_hoy(self, lista: list) -> list:
        """Filtra actividades cuya fecha coincide con hoy."""
        hoy = datetime.now().strftime("%Y-%m-%d")
        return [a for a in lista if a.get("fecha") == hoy]

    def pendientes(self, lista: list) -> list:
        """Devuelve actividades no marcadas como entregadas."""
        return [a for a in lista if not a.get("entregado", False)]

    # ── Resumen rápido ────────────────────────────────────────────
    def resumen(self, lista: list) -> dict:
        """Diccionario listo para renderizar en la vista de inicio."""
        return {
            "xp": self.xp,
            "nivel": self.nivel,
            "racha": self.racha,
            "hoy": len(self.actividades_hoy(lista)),
            "pendientes": len(self.pendientes(lista)),
        }
