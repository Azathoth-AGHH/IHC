import logging

class ProductivityManager:
    """
    Gestiona la gamificación (XP/Rachas), el filtrado de notificaciones por prioridad 
    y la lógica del Widget de escritorio exclusivo para Windows.
    """
    def __init__(self, datos_perfil, modo_notificaciones="prioridad"):
        self.perfil = datos_perfil  # Incluye racha, xp y nivel
        # Modos de notificación: 'frecuente', 'prioridad', 'apagado'
        self.modo_notificaciones = modo_notificaciones 
        self.niveles_xp = {
            "Novato": 0,
            "Intermedio": 1000,
            "Avanzado": 3000,
            "Experto": 6000
        }

    # --- 1. GESTIÓN DE NOTIFICACIONES (FILTRO DE PRIORIDAD) ---
    def validar_notificacion(self, tipo_alerta):
        """
        Determina si se muestra la alerta según la configuración elegida por el usuario.
        Resuelve la saturación de avisos de SEDUCA o tareas no urgentes.
        """
        if self.modo_notificaciones == "apagado":
            return False
        
        if self.modo_notificaciones == "prioridad":
            # Solo permite avisos críticos (clases en 1 min o tareas por vencer)
            alertas_criticas = ['CLASE_INMINENTE', 'TAREA_URGENTE', 'SISTEMA_CRITICO']
            return tipo_alerta in alertas_criticas
        
        # En modo 'frecuente', se muestran todas las notificaciones
        return True

    # --- 2. LÓGICA DEL WIDGET DE ESCRITORIO (RECUADRO DE 1 HORA) ---
    def obtener_estado_widget(self, horario_dia, hora_actual):
        """
        Lógica para el widget de Windows. Si son las 11:51, busca la actividad 
        del bloque de 11:00 a 12:00 para mostrarla en el rectángulo principal.
        """
        try:
            # Extraemos la hora actual (ej. de "11:51" obtenemos 11)
            h_actual = int(hora_actual.split(':')[0])
            
            for bloque in horario_dia:
                h_inicio = int(bloque['hora_inicio'].split(':')[0])
                h_fin = int(bloque['hora_fin'].split(':')[0])
                
                # Verifica si la hora actual cae dentro del rango de la materia
                if h_inicio <= h_actual < h_fin:
                    return {
                        "estado": "OCUPADO",
                        "titulo": bloque['materia'],
                        "maestro": bloque['maestro'],
                        "info": f"{bloque['hora_inicio']} - {bloque['hora_fin']}",
                        "color": "#004A2E" # Verde institucional
                    }
            
            return {
                "estado": "LIBRE", 
                "titulo": "Sin pendientes", 
                "info": "Hora libre o sin clases",
                "color": "#AFAFAF"
            }
        except Exception:
            return {"estado": "ERROR", "titulo": "Error de datos", "info": "Sincroniza horario"}

    # --- 3. GAMIFICACIÓN Y SISTEMA DE NIVELES ---
    def registrar_entrega_exitosa(self, puntual, dificultad="media"):
        """
        Calcula la racha y los puntos XP. 
        Aplica bonos por constancia cada 5 días de racha.
        """
        pesos = {"baja": 50, "media": 100, "alta": 200}
        puntos_base = pesos.get(dificultad, 100)
        
        if puntual:
            self.perfil["racha"] += 1
            # Bono: +10% de XP por cada bloque de 5 días de racha
            bono_multiplicador = 1 + (self.perfil["racha"] // 5) * 0.1
            xp_ganada = int(puntos_base * bono_multiplicador)
            self.perfil["xp"] += xp_ganada
            
            # Actualizar el rango del perfil
            self.perfil["nivel"] = self._evaluar_rango()
            
            return {
                "status": "success", 
                "xp_ganada": xp_ganada, 
                "nueva_racha": self.perfil["racha"],
                "rango": self.perfil["nivel"]
            }
        else:
            # Si no es puntual, la racha se pierde
            self.perfil["racha"] = 0
            return {"status": "reset", "msj": "Racha reiniciada"}

    def _evaluar_rango(self):
        """Calcula el nombre del rango según los puntos acumulados."""
        xp = self.perfil["xp"]
        if xp >= 6000: return "Experto"
        if xp >= 3000: return "Avanzado"
        if xp >= 1000: return "Intermedio"
        return "Novato"