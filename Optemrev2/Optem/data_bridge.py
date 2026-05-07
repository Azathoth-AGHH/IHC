import json
import os
import logging
from datetime import datetime

_DIR = os.path.dirname(os.path.abspath(__file__))

# Configuración de logs para rastrear el flujo de datos y errores
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataBridge:
    """
    Gestiona la persistencia de datos (JSON), la integridad de los archivos 
    y la normalización de información proveniente de Teams y SEDUCA.
    """
    def __init__(self, file_key):
        # El nombre del archivo es el hash generado en AuthManager
        self.archivo = os.path.join(_DIR, f"storage_{file_key}.json")
        self._verificar_almacen()

    def _verificar_almacen(self):
        """
        Crea la estructura base del usuario si el archivo no existe.
        """
        if not os.path.exists(self.archivo):
            esquema_inicial = {
                "perfil": {
                    "nombre": "",
                    "racha": 0,
                    "xp": 0,
                    "nivel": "Novato"
                },
                "config": {
                    "estilo": "cristal",
                    "dark_mode": True,
                    "voz_activa": False
                },
                "materias": {}, # {nombre_materia: [calificaciones]}
                "agenda": [],   # Lista de tareas unificadas
                "ultima_sincronizacion": str(datetime.now())
            }
            self.guardar_datos(esquema_inicial)

    def cargar_datos(self):
        """
        Lee el archivo JSON con manejo de excepciones para evitar cierres inesperados.
        """
        try:
            if os.path.exists(self.archivo):
                with open(self.archivo, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Error crítico al leer el archivo de datos: {e}")
            return None

    def guardar_datos(self, data):
        """
        Guarda los datos utilizando un archivo temporal para evitar corrupción 
        si el proceso se interrumpe (Safe-Save).
        """
        temp_file = self.archivo + ".tmp"
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            # Si la escritura fue exitosa, renombramos el temporal al original
            os.replace(temp_file, self.archivo)
            logging.info("Sincronización de datos exitosa.")
            return True
        except IOError as e:
            logging.error(f"Error al escribir en disco: {e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return False

    def unificar_fuentes_externas(self, raw_teams, raw_seduca):
        """
        Lógica de Centralización: Convierte datos de diferentes plataformas 
        a un formato estándar para el Dashboard.
        """
        unificado = []
        
        # Normalización de Teams
        for t in raw_teams:
            unificado.append({
                "id": t.get("id"),
                "titulo": t.get("display_name"),
                "fecha_entrega": t.get("due_date"),
                "plataforma": "Teams",
                "prioridad": 3 # Calculada después en AcademicEngine
            })
            
        # Normalización de SEDUCA
        for s in raw_seduca:
            unificado.append({
                "id": s.get("act_id"),
                "titulo": s.get("nombre_actividad"),
                "fecha_entrega": s.get("fecha_limite"),
                "plataforma": "SEDUCA",
                "prioridad": 3
            })
            
        return sorted(unificado, key=lambda x: x['fecha_entrega'])

    def registrar_log(self, accion):
        """Mantiene un registro de las acciones importantes para auditoría."""
        logging.info(f"Acción de usuario: {accion}")