import os
import hashlib
from datetime import datetime

class ValidatorEngine:
    """
    Motor de Validación y Gestión de Resultados.
    Separa la lógica de Tareas de la de Proyectos y asegura que 
    el maestro reciba todo en orden y sin duplicados.
    """
    def __init__(self):
        self.formatos_validos = {'.pdf', '.zip', '.rar', '.docx'}
        self.limite_mb = 20

    # --- 1. LÓGICA DE GESTIÓN DE CALIFICACIONES (MAESTRO) ---
    def procesar_calificaciones_grupo(self, lista_entregas):
        """
        Organiza las notas en dos listas: Tareas (promediables) 
        y Proyectos/Exámenes (registros independientes).
        """
        resultado = {
            "tareas": {"lista": [], "promedio": 0},
            "especiales": [] # Proyectos, Exámenes, etc.
        }

        notas_tareas = []
        for entrega in lista_entregas:
            # Si no hay entrega al cierre, la calificación es 0
            calificacion = entrega.get("nota", 0) if entrega.get("enviado") else 0
            
            registro = {
                "alumno": entrega["nombre_alumno"],
                "pago_requisitos": entrega.get("cumple_ia", False),
                "nota": calificacion
            }

            if entrega["categoria"] == "tarea":
                resultado["tareas"]["lista"].append(registro)
                notas_tareas.append(calificacion)
            else:
                # Proyectos o Exámenes se guardan por separado
                resultado["especiales"].append({
                    "tipo": entrega["categoria"],
                    "alumno": entrega["nombre_alumno"],
                    "nota": calificacion
                })

        # Cálculo de promedio automático de tareas
        if notas_tareas:
            resultado["tareas"]["promedio"] = round(sum(notas_tareas) / len(notas_tareas), 2)
        
        return resultado

    # --- 2. LÓGICA DE INTEGRIDAD Y PLAGIO ---
    def validar_y_firmar(self, ruta_archivo):
        """
        Valida requisitos técnicos y genera una firma digital (Hash).
        Esto ayuda al maestro a detectar si dos alumnos mandaron el mismo archivo.
        """
        if not os.path.exists(ruta_archivo):
            return {"status": "error", "msj": "Archivo no encontrado."}

        # Validación de peso y formato
        size_mb = os.path.getsize(ruta_archivo) / (1024 * 1024)
        ext = os.path.splitext(ruta_archivo)[1].lower()

        if ext not in self.formatos_validos:
            return {"status": "error", "msj": f"Formato {ext} no permitido."}
        if size_mb > self.limite_mb:
            return {"status": "error", "msj": "El archivo supera los 20MB."}

        # Generación de huella digital SHA-256
        hash_hash = hashlib.sha256()
        with open(ruta_archivo, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_hash.update(chunk)
        
        return {"status": "success", "hash": hash_hash.hexdigest()}

    # --- 3. LÓGICA DE ESTADO DE ENTREGA ---
    def verificar_estatus_alumno(self, entrega):
        """
        Determina si el alumno solo 'vio' la tarea o si realmente 
        cumplió con el envío antes de la fecha límite.
        """
        ahora = datetime.now()
        deadline = datetime.strptime(entrega['fecha_limite'], "%Y-%m-%d %H:%M")

        if not entrega['enviado'] and ahora > deadline:
            return "NO_ENTREGADO_CERRADO" # Aquí el maestro pone el 0
        if not entrega['enviado']:
            return "SOLO_VISTO"
        return "ENTREGADO"