import os
import tkinter as tk
from tkinter import messagebox

def generar_arbol_directorio(ruta, nivel=0):
    estructura = ""
    espacios = "  " * nivel
    try:
        carpetas_y_archivos = sorted(os.listdir(ruta))
    except Exception as e:
        return f"❌ Error al acceder a la ruta: {e}"

    for nombre in carpetas_y_archivos:
        ruta_completa = os.path.join(ruta, nombre)
        if os.path.isdir(ruta_completa):
            estructura += f"{espacios}- {nombre}/\n"
            estructura += generar_arbol_directorio(ruta_completa, nivel + 1)
        else:
            estructura += f"{espacios}- {nombre}\n"
    return estructura

def guardar_estructura_txt(estructura):
    escritorio = os.path.join(os.path.expanduser("~"), "Desktop")
    archivo_salida = os.path.join(escritorio, "estructura_proyecto.txt")
    try:
        with open(archivo_salida, "w", encoding="utf-8") as archivo:
            archivo.write(estructura)
        messagebox.showinfo("✅ Éxito", f"Estructura guardada en:\n{archivo_salida}")
    except Exception as e:
        messagebox.showerror("❌ Error", f"No se pudo guardar el archivo:\n{e}")

def mostrar_estructura_directorio():
    def generar():
        ruta = entry.get()
        estructura = generar_arbol_directorio(ruta)
        text.delete(1.0, tk.END)
        text.insert(tk.END, estructura)
        guardar_estructura_txt(estructura)

    ventana = tk.Toplevel()
    ventana.title("Generador de estructura de proyecto")
    ventana.geometry("600x400")

    entry = tk.Entry(ventana, width=60)
    entry.pack(pady=10)
    entry.focus()

    boton = tk.Button(ventana, text="Generar estructura", command=generar)
    boton.pack(pady=5)

    text = tk.Text(ventana, wrap=tk.WORD)
    text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
