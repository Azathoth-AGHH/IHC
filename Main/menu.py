from tkinter import*
ventana=Tk()

menu=Menu (ventana)
ventana.config(menu=menu)

File=Menu (menu, tearoff=0)
File.add_command (label="New project.")
File.add_command (label="open")
File.add_command (label="safe")
File.add_separator()
File.add_command (label="Exit")

Edit=Menu (menu, tearoff=0)
Edit.add_command(label="copy")
Edit.add_command(label="cut")
Edit.add_command(label="Paste")
Help=Menu (menu, tearoff=0)
Help.add_command(label="Help")
Help.add_separator()
Help.add_command(label="About")

menu.add_cascade(label="File", menu=File)
menu.add_cascade(label="Edit", menu=Edit)
menu.add_cascade(label="Help", menu=Help)

ventana.mainloop()