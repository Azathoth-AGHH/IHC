from tkinter import *

ventana = Tk()
ventana.geometry('600x600')
ventana.config(bg='white')
ventana.title('VENTANA PRINCIPAL')
ventana.resizable(width=False, height=False)

imagenP = PhotoImage(file='Interfaz/python.gif')

lblImagen = Label(ventana, image=imagenP)
lblImagen.place(x=100, y=100)

ventana.mainloop()