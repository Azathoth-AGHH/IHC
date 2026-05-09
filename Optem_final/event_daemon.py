import time
import logging
from datetime import datetime, timedelta

class EventDaemon:
    """
    Monitor de eventos en tiempo real. 
    Gestiona notificaciones proactivas, alertas de urgencia y 
    disparadores de automatización para servicios de la UAEMéx.
    """
    _FORMATOS_FECHA = ("%Y-%m-%d %H:%M", "%Y-%m-%d")

    def __init__(self, agenda_usuario):
        self.agenda = agenda_usuario # Lista de tareas unificadas
        self.notificaciones_activas = []
        self.intervalo_chequeo = 60  # Segundos entre cada revisión

    @classmethod
    def _parsear_fecha(cls, texto):
        """Parsea fecha con o sin hora; retorna datetime o None."""
        for fmt in cls._FORMATOS_FECHA:
            try:
                return datetime.strptime(texto, fmt)
            except (ValueError, TypeError):
                continue
        logging.warning("EventDaemon: formato de fecha no reconocido: %r", texto)
        return None

    def monitorear_proximidad(self):
        """
        Escanea la agenda y determina qué eventos requieren atención inmediata.
        Clasifica las alertas según el tiempo restante.
        """
        alertas = []
        ahora = datetime.now()

        for evento in self.agenda:
            try:
                fecha_entrega = self._parsear_fecha(evento['fecha_entrega'])
                if fecha_entrega is None:
                    continue
                diferencia = fecha_entrega - ahora

                # Lógica de Alertas en Cascada
                if timedelta(0) < diferencia <= timedelta(minutes=15):
                    alertas.append({
                        "id": evento['id'],
                        "tipo": "URGENTE",
                        "msj": f"¡Últimos minutos! Entrega de {evento['titulo']} pronto.",
                        "accion_sugerida": "abrir_subida_rapida"
                    })
                elif timedelta(minutes=15) < diferencia <= timedelta(hours=1):
                    alertas.append({
                        "id": evento['id'],
                        "tipo": "PREPARACION",
                        "msj": f"Recordatorio: Tienes '{evento['titulo']}' en una hora.",
                        "accion_sugerida": "revisar_archivo"
                    })
            except KeyError as e:
                logging.warning("EventDaemon.monitorear_proximidad: campo faltante %s en evento %r", e, evento.get('id'))
                continue

        return alertas

    def verificar_inicio_clase(self, horario_clases):
        """
        Lógica de Automatización: Detecta si una clase está por comenzar 
        para sugerir la apertura automática del enlace de Teams.
        """
        ahora_hora = datetime.now().strftime("%H:%M")
        
        for clase in horario_clases:
            if clase['inicio'] == ahora_hora:
                return {
                    "tipo": "AUTOMATIZACION",
                    "msj": f"Iniciando sesión de {clase['materia']}...",
                    "url": clase.get("enlace_teams", "https://teams.microsoft.com")
                }
        return None

    def calcular_tiempo_restante_str(self, fecha_objetivo):
        """Devuelve un formato amigable de cuánto falta para una entrega."""
        objetivo = self._parsear_fecha(fecha_objetivo)
        if objetivo is None:
            return "Fecha no válida"
        diferencia = objetivo - datetime.now()
        
        if diferencia.days > 0:
            return f"Faltan {diferencia.days} días"
        
        horas, rem = divmod(diferencia.seconds, 3600)
        minutos, _ = divmod(rem, 60)
        return f"Faltan {horas}h {minutos}m"