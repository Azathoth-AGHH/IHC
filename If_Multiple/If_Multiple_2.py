edad = int(input("Ingresa tu edad: "))

if edad < 0:
    print("Edad inválida")
elif edad <= 12:
    print("Eres un niño")
elif edad <= 17:
    print("Eres un adolescente")
elif edad <= 64:
    print("Eres un adulto")
else:
    print("Eres un adulto mayor")