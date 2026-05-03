class ConfigManager:
    """
    Controlador de Estilos y Experiencia de Usuario (UX).
    Gestiona la apariencia visual (Cristal vs Sólido), el modo oscuro 
    y la adaptabilidad de la interfaz según las preferencias del usuario.
    """
    def __init__(self, config_datos):
        # Recibe la sección 'config' del JSON del usuario
        self.config = config_datos

    def obtener_paquete_estilos(self):
        """
        Devuelve un diccionario de propiedades visuales que la interfaz 
        debe aplicar para cumplir con la petición de 'Modo Sólido'.
        """
        tipo_visual = self.config.get("estilo", "cristal")
        es_oscuro = self.config.get("dark_mode", True)

        if tipo_visual == "solido":
            return self._generar_estilo_solido(es_oscuro)
        
        return self._generar_estilo_cristal(es_oscuro)

    def _generar_estilo_solido(self, es_oscuro):
        """Define una interfaz con colores planos y alta legibilidad."""
        return {
            "tipo": "solido",
            "bg_principal": "#1E1E1E" if es_oscuro else "#F5F5F5",
            "bg_paneles": "#2D2D2D" if es_oscuro else "#FFFFFF",
            "opacidad": 1.0,
            "blur": 0,
            "borde": "1px solid #444444" if es_oscuro else "1px solid #D1D1D1",
            "texto": "#FFFFFF" if es_oscuro else "#333333",
            "sombra": "0px 4px 10px rgba(0,0,0,0.3)"
        }

    def _generar_estilo_cristal(self, es_oscuro):
        """Define la estética Glassmorphism original de Optem."""
        return {
            "tipo": "cristal",
            "bg_principal": "transparent", # Depende del fondo de pantalla
            "bg_paneles": "rgba(45, 45, 45, 0.7)" if es_oscuro else "rgba(255, 255, 255, 0.6)",
            "opacidad": 0.7,
            "blur": 25, # Efecto de desenfoque de fondo
            "borde": "1px solid rgba(255, 255, 255, 0.2)",
            "texto": "#FFFFFF" if es_oscuro else "#222222",
            "sombra": "none"
        }

    def alternar_modo_visual(self):
        """Cambia entre Cristal y Sólido y guarda la preferencia."""
        actual = self.config.get("estilo", "cristal")
        nueva = "solido" if actual == "cristal" else "cristal"
        self.config["estilo"] = nueva
        return nueva

    def ajustar_accesibilidad(self, nivel_contraste):
        """
        Ajusta dinámicamente el grosor de las fuentes o el tamaño de 
        iconos para usuarios con debilidad visual.
        """
        if nivel_contraste == "alto":
            return {"font_weight": "bold", "icon_size": "large"}
        return {"font_weight": "normal", "icon_size": "medium"}