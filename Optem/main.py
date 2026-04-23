import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import time
from login import OptemLogin

class OptemSplash:
    def __init__(self):
        self.splash = tk.Tk()
        self.splash.overrideredirect(True) 
        self.splash.config(bg="#FFFFFF")
        
        self.ancho_s, self.alto_s = 500, 450
        ancho_p = self.splash.winfo_screenwidth()
        alto_p = self.splash.winfo_screenheight()
        x = (ancho_p // 2) - (self.ancho_s // 2)
        y = (alto_p // 2) - (self.alto_s // 2)
        self.splash.geometry(f"{self.ancho_s}x{self.alto_s}+{x}+{y}")

        self.preparar_piezas()
        self.iniciar_animacion()
        
        self.splash.mainloop()

    def preparar_piezas(self):
        img = Image.open("logo_optem.png").convert("RGBA")
        img = img.resize((160, 160), Image.Resampling.LANCZOS)
        w, h = img.size
        mid_w, mid_h = w // 2, h // 2

        coords = [
            (0, 0, mid_w, mid_h),       
            (mid_w, 0, w, mid_h),      
            (0, mid_h, mid_w, h),    
            (mid_w, mid_h, w, h)        
        ]

        self.piezas_labels = []
        self.fotos = [] 

        for i in range(4):
            crop = img.crop(coords[i])
            foto = ImageTk.PhotoImage(crop)
            self.fotos.append(foto)
            lbl = tk.Label(self.splash, image=foto, bg="#FFFFFF", bd=0)
            self.piezas_labels.append(lbl)

        self.lbl_texto = tk.Label(self.splash, text="Sincronizando éxito universitario...", 
                                  font=("Segoe UI", 11, "italic"), bg="#FFFFFF", fg="#3b71ca")
        
        self.progress = ttk.Progressbar(self.splash, orient=tk.HORIZONTAL, length=300, mode='determinate')

    def iniciar_animacion(self):
        centro_x = self.ancho_s // 2
        centro_y = self.alto_s // 2 - 50
        pw, ph = 80, 80 

        pos_ini = [
            (centro_x - 150, centro_y - 150), 
            (centro_x + 150, centro_y - 150), 
            (centro_x - 150, centro_y + 150), 
            (centro_x + 150, centro_y + 150)  
        ]
        
        pos_fin = [
            (centro_x - pw, centro_y - ph),
            (centro_x, centro_y - ph),
            (centro_x - pw, centro_y),
            (centro_x, centro_y)
        ]

        pasos = 30
        for i in range(pasos + 1):
            ratio = i / pasos
            for j in range(4):
                curr_x = pos_ini[j][0] + (pos_fin[j][0] - pos_ini[j][0]) * ratio
                curr_y = pos_ini[j][1] + (pos_fin[j][1] - pos_ini[j][1]) * ratio
                self.piezas_labels[j].place(x=curr_x, y=curr_y)
            
            self.splash.update()
            time.sleep(0.02)

        self.lbl_texto.place(x=centro_x, y=centro_y + 120, anchor=tk.CENTER)
        self.progress.place(x=centro_x, y=centro_y + 150, anchor=tk.CENTER)
        
        for k in range(101):
            self.progress['value'] = k
            self.splash.update()
            time.sleep(0.015)

        self.splash.after(800, self.finalizar)

    def finalizar(self):
        self.splash.destroy()
        app = OptemLogin()
        app.ventana.mainloop()

if __name__ == "__main__":
    OptemSplash()