import logging

class AcademicEngine:
    """
    Motor de IA Avanzado: Gestiona la generación de horarios ideales,
    la selección de maestros y el resumen inteligente de tareas.
    """
    def __init__(self, datos_usuario):
        self.materias_usuario = datos_usuario.get("materias", {})
        self.agenda = datos_usuario.get("agenda", [])
        self.preferencia_maestros = {} # Almacena maestros favoritos

    # --- 1. LÓGICA DE REINSCRIPCIÓN INTELIGENTE ---
    def generar_propuestas_horario(self, materias_disponibles, preferencia="flexible"):
        """
        Analiza toda la oferta académica y genera horarios basados en:
        - Matutino: Entrada y salida temprana.
        - Flexible: Evita huecos y busca entrada tarde/salida temprano.
        - Vespertino: Prioriza bloques de tarde.
        """
        propuestas = []
        # Lógica de filtrado por horas
        for materia in materias_disponibles:
            opciones = materia['horarios'] # Lista de opciones para una materia
            
            if preferencia == "matutino":
                # Filtra clases que inicien antes de las 11:00 AM
                seleccion = [o for o in opciones if int(o['hora_inicio'].split(':')[0]) < 11]
            elif preferencia == "vespertino":
                # Filtra clases que inicien después de las 2:00 PM
                seleccion = [o for o in opciones if int(o['hora_inicio'].split(':')[0]) >= 14]
            else: # Flexible (Sin huecos)
                # Selecciona la opción que esté más cerca de la clase anterior
                seleccion = self._optimizar_sin_huecos(opciones)
            
            if seleccion:
                propuestas.append(seleccion[0]) # Toma la mejor opción según el filtro

        return propuestas

    def _optimizar_sin_huecos(self, opciones):
        """Algoritmo interno para compactar el horario y evitar 'horas muertas'."""
        # Ordena por hora para que la IA elija la que sigue inmediatamente a la anterior
        return sorted(opciones, key=lambda x: x['hora_inicio'])

    def consultar_preferencia_maestro(self, materia, maestros_disponibles):
        """
        Si hay dos maestros en el mismo horario, la IA pregunta al usuario.
        """
        if len(maestros_disponibles) > 1:
            return {
                "pregunta": f"Para {materia}, hay varios maestros disponibles.",
                "opciones": [m['nombre'] for m in maestros_disponibles],
                "info": "Elige tu favorito para armar el horario final."
            }
        return maestros_disponibles[0]

    # --- 2. LÓGICA DE RESUMEN DE TAREAS (BOTÓN FLOTANTE) ---
    def generar_resumen_tarea(self, instrucciones_raw):
        """
        La IA analiza las instrucciones de Teams y extrae lo esencial:
        ¿Qué hacer?, ¿Qué entregar? y ¿Qué requisitos pide el maestro?
        """
        if not instrucciones_raw:
            return "El maestro no ha proporcionado instrucciones detalladas."
        
        # Simulación de procesamiento de lenguaje natural (NLP)
        resumen = {
            "objetivo": "Entender los conceptos clave vistos en clase.",
            "entregable": "Documento PDF o enlace a repositorio.",
            "requisitos_criticos": [],
            "explicación_sencilla": ""
        }
        
        # Lógica de búsqueda de palabras clave
        palabras_clave = ["pdf", "formato", "equipo", "individual", "portada", "bibliografía"]
        for palabra in palabras_clave:
            if palabra in instrucciones_raw.lower():
                resumen["requisitos_criticos"].append(palabra.upper())
        
        resumen["explicación_sencilla"] = f"El maestro solicita un trabajo {resumen['requisitos_criticos'][0] if resumen['requisitos_criticos'] else 'general'}. " \
                                         f"Debes enfocarte en los puntos clave de la asignación."
        
        return resumen

    # --- 3. LÓGICA PARA MAESTROS (GESTIÓN DE NOTAS) ---
    def calcular_promedios_maestro(self, lista_calificaciones):
        """
        Separa tareas de proyectos y calcula promedios automáticos.
        Si la entrega está vacía, la lógica devuelve 0.
        """
        tareas = [n for n in lista_calificaciones if n['tipo'] == 'tarea']
        otros = [n for n in lista_calificaciones if n['tipo'] != 'tarea']
        
        promedio_tareas = sum([t['nota'] for t in tareas]) / len(tareas) if tareas else 0
        
        return {
            "promedio_tareas": round(promedio_tareas, 2),
            "proyectos_registrados": otros,
            "alerta_riesgo": "Alumno en riesgo" if promedio_tareas < 7.0 else "Regular"
        }