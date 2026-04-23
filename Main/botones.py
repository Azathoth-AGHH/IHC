from tkinter import *

def lenguajes():
    c = selC.get()
    cc = selCC.get()
    java = selJava.get()
    php = selPHP.get()
    pyton = selPy.get()

    print("Valor de C:", c)
    print("Valor de CC:", cc)
    print("Valor de Java:", java)
    print("Valor de PHP:", php)
    print("Valor de Python:", pyton)

    cadena = ""
    if c == 1:
        cadena = cadena + "C "
    if cc == 1:
        cadena = cadena + "C++ "
    if java == 1:
        cadena = cadena + "Java "
    if php == 1:
        cadena = cadena + "PHP "
    if pyton == 1:
        cadena = cadena + "Python "


ventana = Tk()
ventana.title("Selector de Lenguajes")
ventana.geometry("300x400")

selC = IntVar()
selCC = IntVar()
selJava = IntVar()
selPHP = IntVar()
selPy = IntVar()

Label(ventana, text="Que lenguaje de programacion conoces:", font=("Arial", 12)).pack(pady=10)

Checkbutton(ventana, text="C", variable=selC).pack(anchor=W, padx=20)
Checkbutton(ventana, text="C++", variable=selCC).pack(anchor=W, padx=20)
Checkbutton(ventana, text="Java", variable=selJava).pack(anchor=W, padx=20)
Checkbutton(ventana, text="PHP", variable=selPHP).pack(anchor=W, padx=20)
Checkbutton(ventana, text="Python", variable=selPy).pack(anchor=W, padx=20)

btn = Button(ventana, text="Cuales seleccionaste", command=lenguajes)
btn.pack(pady=20)

ventana.mainloop()