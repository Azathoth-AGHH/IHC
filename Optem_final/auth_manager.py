import re
import hashlib
import time

class AuthManager:
    """
    Gestiona la seguridad, validación de correos institucionales UAEMéx 
    y el control de sesiones para evitar accesos no autorizados.
    """
    def __init__(self):
        # Expresión regular para dominios oficiales de la UAEMéx
        self.pattern_institucional = r'^[a-zA-Z0-9._%+-]+@(alumno\.uaemex\.mx|uaemex\.mx)$'
        self.session_token = None
        self.last_activity = 0
        self.timeout_duration = 1800  # 30 minutos en segundos para auto-cierre

    def validar_correo(self, correo):
        """
        Verifica que el correo cumpla con el formato institucional.
        """
        if re.match(self.pattern_institucional, correo):
            return True
        return False

    def generar_llave_archivo(self, num_cuenta):
        """
        Crea un hash único basado en el número de cuenta para cifrar 
        simbólicamente el nombre del archivo de datos.
        """
        # Usamos SHA-256 para que el nombre del archivo no sea el número de cuenta real
        hash_obj = hashlib.sha256(num_cuenta.encode())
        return hash_obj.hexdigest()[:16]

    def iniciar_sesion(self, correo, num_cuenta):
        """
        Lógica de entrada: Valida credenciales y genera un token de sesión.
        """
        if self.validar_correo(correo) and len(num_cuenta) >= 7:
            self.session_token = hashlib.md5(f"{correo}{time.time()}".encode()).hexdigest()
            self.last_activity = time.time()
            return {
                "status": "success",
                "token": self.session_token,
                "file_key": self.generar_llave_archivo(num_cuenta)
            }
        return {"status": "error", "message": "Credenciales institucionales inválidas."}

    def verificar_expiracion(self):
        """
        Lógica de protección: Si pasan 30 min sin actividad, cierra la sesión.
        """
        if self.session_token and (time.time() - self.last_activity) > self.timeout_duration:
            self.cerrar_sesion()
            return True # Sesión expirada
        return False

    def registrar_actividad(self):
        """Actualiza el tiempo de la última interacción para mantener la sesión activa."""
        self.last_activity = time.time()

    def cerrar_sesion(self):
        """Limpia los rastros de la sesión actual."""
        self.session_token = None
        self.last_activity = 0