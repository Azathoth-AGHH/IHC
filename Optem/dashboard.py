from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk

class OptemDashboard:
    def __init__(self, nombre_usuario="Alejandro"):
        self.ventana = Tk()
        self.ventana.title(f"Optem - Panel de {nombre_usuario}")
        self.ventana.geometry("1100x700")
        self.ventana.config(bg="#f8f9fa")
        
        self.nombre_usuario = nombre_usuario
        self.crear_navegacion()
        self.crear_contenido_principal()
        
        self.ventana.mainloop()

    def crear_navegacion(self):
        sidebar = Frame(self.ventana, bg="#3b71ca", width=200, height=700)
        sidebar.pack(side=LEFT, fill=Y)
        sidebar.pack_propagate(False)

        Label(sidebar, text="OPTEM", font=("Segoe UI", 20, "bold"), 
              bg="#3b71ca", fg="white").pack(pady=30)

        botones = [("🏠 Inicio", True), ("📅 Horario", False), ("📚 Tareas", False), ("⚙️ Ajustes", False)]
        for texto, activo in botones:
            color_fondo = "#2a5298" if activo else "#3b71ca"
            btn = Button(sidebar, text=texto, font=("Segoe UI", 11), bg=color_fondo, 
                         fg="white", bd=0, padx=20, pady=10, anchor="w", cursor="hand2")
            btn.pack(fill=X, pady=2)

    def crear_contenido_principal(self):
        self.area_trabajo = Frame(self.ventana, bg="#f8f9fa")
        self.area_trabajo.pack(side=RIGHT, fill=BOTH, expand=True, padx=30, pady=20)

        header = Frame(self.area_trabajo, bg="#f8f9fa")
        header.pack(fill=X)
        
        Label(header, text=f"¡Bienvenido de nuevo, {self.nombre_usuario}! 👋", 
              font=("Segoe UI", 18, "bold"), bg="#f8f9fa", fg="#333").pack(side=LEFT)
        
        card_proxima = Frame(self.area_trabajo, bg="#e7f0ff", bd=0, highlightthickness=1, highlightbackground="#3b71ca")
        card_proxima.pack(fill=X, pady=20, ipady=15, ipadx=15)
        
        Label(card_proxima, text="PRÓXIMA CLASE EN 10 MINUTOS", font=("Segoe UI", 9, "bold"), 
              bg="#e7f0ff", fg="#3b71ca").pack(anchor=W)
        Label(card_proxima, text="Cálculo Diferencial", font=("Segoe UI", 16, "bold"), 
              bg="#e7f0ff", fg="#333").pack(anchor=W)
        Label(card_proxima, text="Edificio A - Aula 204 | Mtro. Hernández", font=("Segoe UI", 10), 
              bg="#e7f0ff", fg="#555").pack(anchor=W)

        Label(self.area_trabajo, text="Tareas Pendientes", font=("Segoe UI", 14, "bold"), 
              bg="#f8f9fa", fg="#333").pack(anchor=W, pady=(10, 0))
        
        self.crear_tarjeta_tarea("Ensayo de Cálculo", "Hoy 18:00 | SEDUCA")
        self.crear_tarjeta_tarea("Mapa Mental", "Mañana | Teams")

    def crear_tarjeta_tarea(self, titulo, info):
        card = Frame(self.area_trabajo, bg="white", bd=0, highlightthickness=1, highlightbackground="#ddd")
        card.pack(fill=X, pady=5, ipady=10, ipadx=10)
        
        Label(card, text=titulo, font=("Segoe UI", 11, "bold"), bg="white").pack(side=LEFT, padx=10)
        Label(card, text=info, font=("Segoe UI", 9), bg="white", fg="gray").pack(side=LEFT, padx=10)
        
        btn_ia = Button(card, text="✨ Resumen IA", font=("Segoe UI", 9, "bold"), 
                        bg="#f0f7ff", fg="#3b71ca", bd=0, padx=10, cursor="hand2")
        btn_ia.pack(side=RIGHT, padx=10)

if __name__ == "__main__":
    OptemDashboard()