while True:
    nombre = input("Ingresa el nombre del alumno: ")
    promedio = float(input("Ingresa el promedio del alumno: "))

    if promedio >= 70:
        print(f"{nombre} está APROBADO")
    else:
        print(f"{nombre} está REPROBADO")

    respuesta = input("¿Deseas capturar otro alumno? (SI/NO): ").upper()

    if respuesta == "NO":
        print("Programa finalizado.")
        break