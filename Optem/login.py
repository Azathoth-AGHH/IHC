from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk
from dashboard import OptemDashboard

class OptemLogin:
    def __init__(self):
        self.ventana = Tk()
        self.ventana.title("Optem - Sincronizando tu éxito")
        
        ancho_ventana = 650
        alto_ventana = 650
        self.ventana.geometry(f"{ancho_ventana}x{alto_ventana}")
        self.ventana.config(bg="#FFFFFF")
        self.ventana.resizable(False, False)

        self.correo_var = StringVar()
        self.cuenta_var = StringVar()

        self.crear_interfaz()

    def crear_interfaz(self):
        main_frame = Frame(self.ventana, bg="#FFFFFF")
        main_frame.place(relx=0.5, rely=0.5, anchor=CENTER)

        try:
            self.img_logo = Image.open("logo_optem.png") 
            self.img_logo = self.img_logo.resize((120, 90), Image.Resampling.LANCZOS) 
            self.logo_render = ImageTk.PhotoImage(self.img_logo)
            
            self.lbl_logo = Label(main_frame, image=self.logo_render, bg="#FFFFFF")
            self.lbl_logo.pack(pady=(0, 5)) 
        except Exception as e:
            Label(main_frame, text="OPTEM", font=("Segoe UI", 28, "bold"), 
                  bg="#FFFFFF", fg="#3b71ca").pack(pady=(0, 10))
        
        Label(main_frame, text="¡Hola! 🎓", font=("Segoe UI", 14), 
              bg="#FFFFFF", fg="#555").pack(pady=(0, 25))

        Label(main_frame, text="Correo Institucional", bg="#FFFFFF", 
              font=("Segoe UI", 10, "bold"), fg="#333").pack(anchor=W)
        
        self.entry_correo = Entry(main_frame, textvariable=self.correo_var, 
                                 font=("Segoe UI", 12), width=35, bd=0, 
                                 highlightthickness=1, highlightbackground="#ccc")
        self.entry_correo.pack(pady=(5, 2))
        
        Label(main_frame, text="ejemplo@alumno.uaemex.mx", bg="#FFFFFF", 
              fg="#999", font=("Segoe UI", 8)).pack(anchor=W, pady=(0, 15))

        Label(main_frame, text="Número de Cuenta", bg="#FFFFFF", 
              font=("Segoe UI", 10, "bold"), fg="#333").pack(anchor=W)
        
        self.entry_cuenta = Entry(main_frame, textvariable=self.cuenta_var, 
                                 font=("Segoe UI", 12), width=35, show="●", bd=0, 
                                 highlightthickness=1, highlightbackground="#ccc")
        self.entry_cuenta.pack(pady=(5, 30))

        self.btn_ingresar = Button(main_frame, text="INICIAR SESIÓN", command=self.validar_acceso,
                                   bg="#3b71ca", fg="white", font=("Segoe UI", 11, "bold"),
                                   width=30, height=2, bd=0, cursor="hand2",
                                   activebackground="#2a5298", activeforeground="white")
        self.btn_ingresar.pack()
        
        self.btn_ingresar.bind("<Enter>", lambda e: self.btn_ingresar.config(bg="#2a5298"))
        self.btn_ingresar.bind("<Leave>", lambda e: self.btn_ingresar.config(bg="#3b71ca"))

    def validar_acceso(self):
        correo = self.correo_var.get()
        cuenta = self.cuenta_var.get()

        if not correo.endswith("@alumno.uaemex.mx"):
            messagebox.showwarning("Dato Incorrecto", "Por favor ingresa tu correo institucional de la UAEMéx.")
            return

        if len(cuenta) < 7 or not cuenta.isdigit():
            messagebox.showwarning("Dato Incorrecto", "El número de cuenta debe ser de al menos 7 dígitos.")
            return

        messagebox.showinfo("Éxito", "Identidad verificada correctamente.\nSincronizando con Teams y SEDUCA...")
        
        self.ventana.destroy()
        OptemDashboard("Jose")

if __name__ == "__main__":
    app = OptemLogin()
    app.ventana.mainloop()