import os, time, re, ctypes, struct, threading, subprocess, psutil
import pvporcupine, pyaudio, speech_recognition as sr, pyautogui
import tkinter as tk
from PIL import Image, ImageTk
import win32con, win32gui
from pywinauto import Application
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import pyttsx3

from spotify_api import SpotifyAPI
from comandos import comandos
from logger import log_request

from estructura import mostrar_estructura_directorio
from dotenv import load_dotenv

load_dotenv() 
#ACCESS_KEY
ACCESS_KEY = os.getenv("ACCESS_KEY")
spotify_api = SpotifyAPI()


STOPWORDS = {"please", "por favor", "ahora", "ya", "un", "una", "el", "la", "los", "las", "porfa"}

def limpiar_comando(texto):
    palabras = texto.strip().lower().split()
    palabras_filtradas = [p for p in palabras if p not in STOPWORDS]
    return " ".join(palabras_filtradas)

# -------------------- VOZ --------------------
def hablar(texto):
    engine = pyttsx3.init()
    engine.say(texto)
    engine.runAndWait()

# -------------------- GUI --------------------
class TereGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", "pink")
        self.root.geometry("+50+50")
        self.root.configure(bg="pink")
        self.label = tk.Label(self.root, bg="pink")
        self.label.pack()
        self.cargar_imagen("dormida.png")
        self._hacer_no_clickeable()

    def cargar_imagen(self, nombre):
        img = Image.open(f"img/{nombre}")
        img = img.resize((200, 200), Image.Resampling.LANCZOS)
        self.imgtk = ImageTk.PhotoImage(img)
        self.label.config(image=self.imgtk)

    def _hacer_no_clickeable(self):
        self.root.update_idletasks()
        hwnd = win32gui.FindWindow(None, self.root.title())
        estilo = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, estilo | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)

    def cambiar_estado(self, estado):
        self.cargar_imagen(f"{estado}.png")

    def iniciar(self):
        self.root.mainloop()

# -------------------- UTILIDADES --------------------
def ajustar_volumen(porcentaje):
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volumen = cast(interface, POINTER(IAudioEndpointVolume))
    porcentaje = max(0.0, min(1.0, porcentaje / 100))
    volumen.SetMasterVolumeLevelScalar(porcentaje, None)

def cerrar_programa(nombre_proceso, nombre_amigable):
    try:
        cerrado = False
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] and proc.info['name'].lower() == nombre_proceso.lower():
                psutil.Process(proc.info['pid']).terminate()
                cerrado = True
        hablar(f"Se cerró {nombre_amigable}" if cerrado else f"{nombre_amigable} no estaba abierto")
    except Exception as e:
        print(f"❌ Error al cerrar {nombre_amigable}: {e}")
        hablar(f"No pude cerrar {nombre_amigable}")

def spotify_esta_abierto():
    return any('spotify' in proc.info['name'].lower() for proc in psutil.process_iter(['name']) if proc.info['name'])

def esperar_hasta_que_spotify_cargue(timeout=10):
    for _ in range(timeout):
        if spotify_esta_abierto():
            return True
        time.sleep(1)
    return False

def enviar_play_pause():
    VK_MEDIA_PLAY_PAUSE = 0xB3
    ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
    ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 2, 0)

def cerrar_spotify():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] and 'spotify' in proc.info['name'].lower():
            psutil.Process(proc.info['pid']).terminate()

# -------------------- COMANDOS --------------------
def ejecutar_comando(comando, tere_gui):
    print("🧠 Comando recibido (original):", comando)
    comando_limpio = limpiar_comando(comando)
    print("🧹 Comando limpio:", comando_limpio)

    # Ya no llamar aquí log_request, se hará según resultado

    
    if comando_limpio in comandos:
        ruta, usar_shell, nombre_programa, proceso = comandos[comando_limpio]
        try:
            if usar_shell:
                subprocess.Popen(" ".join(ruta), shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen(ruta, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            hablar(f"{nombre_programa} abierto")
            log_request(comando_limpio, "success")
        except Exception as e:
            print(f"❌ Error al ejecutar {nombre_programa}: {e}")
            hablar(f"No se pudo abrir {nombre_programa}")
            log_request(comando_limpio, "failed")
        tere_gui.cambiar_estado("ejecutando")
        tere_gui.root.after(3000, lambda: tere_gui.cambiar_estado("dormida"))
        return

    #ESTRUCTURA

    elif "estructura" in comando_limpio:
        hablar("Por favor, dime la ubicación del proyecto.")
        mostrar_estructura_directorio()
    #ESTRUCTURA

    elif comando_limpio.startswith("cerrar "):
        nombre = comando_limpio.replace("cerrar ", "").strip()
        for clave, (ruta, shell, nombre_amigable, proceso) in comandos.items():
            if clave.endswith(nombre):
                cerrar_programa(proceso, nombre_amigable)
                log_request(comando_limpio, "success")
                tere_gui.cambiar_estado("ejecutando")
                tere_gui.root.after(3000, lambda: tere_gui.cambiar_estado("dormida"))
                return
        hablar(f"No sé cómo cerrar {nombre}")
        log_request(comando_limpio, "failed")
        return
    import sys
    # Aquí similar para comandos especiales, con éxito o fallo
    if any(p in comando_limpio for p in ["apagar roxana", "cierra roxana", "roxana cierra"]):
        log_request(comando_limpio, "success")
        tere_gui.cambiar_estado("ejecutando")
        hablar(f"Apagando Roxana")
        print("🛑 Cerrando Roxana por comando de voz.")
        log_request(comando_limpio, "success")
        os._exit(0)  # o usa os._exit(0) si estás fuera de VSCode
        
    if any(palabra in comando_limpio for palabra in ["duerme", "vete", "descansa"]):
        log_request(comando_limpio, "success")
        tere_gui.root.withdraw()
        return
    elif "despierta" in comando_limpio or "vuelve" in comando_limpio:
        log_request(comando_limpio, "success")
        tere_gui.root.deiconify()
        tere_gui.cambiar_estado("dormida")
        return
    elif comando_limpio.startswith("pon "):
        consulta = comando_limpio.replace("pon", "").strip()
        log_request(comando_limpio, "success")
        threading.Thread(target=reproducir_en_spotify, args=(consulta, tere_gui), daemon=True).start()
        return
    elif "stop" in comando_limpio or "play" in comando_limpio:
        log_request(comando_limpio, "success")
        enviar_play_pause()
        cerrar_spotify()
        tere_gui.root.deiconify()
        tere_gui.cambiar_estado("dormida")
        return
    elif re.match(r"volumen al \d{1,3}", comando_limpio):
        match = re.search(r"volumen al (\d{1,3})", comando_limpio)
        if match:
            nivel = int(match.group(1))
            nivel = max(0, min(nivel, 100))
            ajustar_volumen(nivel)
            log_request(comando_limpio, "success")
            tere_gui.cambiar_estado("ejecutando")
            tere_gui.root.after(2000, lambda: tere_gui.cambiar_estado("dormida"))
            return

    # Comando para actualizar comandos
    if comando in ["roxana update", "roxana actualizate","update roxana"]:
        hablar("Actualizando comandos, espera un momento.")
        tere_gui.cambiar_estado("ejecutando")
        print("🔄 Iniciando actualización de comandos...")

        try:
            subprocess.run(["python", "generar_comandos.py"], check=True)
            
            hablar("Comandos actualizados correctamente. Reiniciando Roxana.")
            print("✅ Comandos actualizados correctamente.")
        except subprocess.CalledProcessError as e:
            
            print(f"❌ Error al actualizar comandos: {e}")
            hablar("No pude actualizar los comandos.")
            tere_gui.cambiar_estado("error")
            tere_gui.root.after(3000, lambda: tere_gui.cambiar_estado("dormida"))
            return

        log_request(comando_limpio, "success")
        
        # Reiniciar Roxana
        ruta_python = os.sys.executable
        ruta_script = os.path.abspath(__file__)
        print(f"🔄 Reiniciando: {ruta_python} {ruta_script}")

        try:
            subprocess.Popen([ruta_python, ruta_script])
            print("✅ Nuevo proceso Roxana lanzado.")
        except Exception as e:
            print(f"❌ Error lanzando nuevo proceso: {e}")
            hablar("No pude reiniciar Roxana.")

        print("❌ Cerrando proceso actual.")
        os._exit(0)


    # Si no entró en ninguno, comando no reconocido:
    log_request(comando_limpio, "failed")
    tere_gui.cambiar_estado("error")
    tere_gui.root.after(3000, lambda: tere_gui.cambiar_estado("dormida"))



# -------------------- SPOTIFY --------------------
def reproducir_en_spotify(consulta, tere_gui):
    tere_gui.cambiar_estado("ejecutando")
    url = spotify_api.buscar_uri(consulta)
    if not url:
        print("❌ No se encontró la canción en Spotify.")
        tere_gui.cambiar_estado("error")
        return

    try:
        if not spotify_esta_abierto():
            subprocess.Popen(r'"C:\Users\TCP\AppData\Roaming\Spotify\Spotify.exe"')
            if not esperar_hasta_que_spotify_cargue():
                tere_gui.cambiar_estado("error")
                return
        else:
            enviar_play_pause()

        os.startfile(url)
        time.sleep(2)
        pyautogui.hotkey('win', 'down')  # Minimiza
        print(f"🎵 Reproduciendo: {consulta}")
    except Exception as e:
        print(f"❌ Error: {e}")
        tere_gui.cambiar_estado("error")
    finally:
        tere_gui.root.after(3000, lambda: tere_gui.cambiar_estado("dormida"))

# -------------------- ESCUCHAR --------------------
def escuchar_comando(tere_gui):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        tere_gui.cambiar_estado("escuchando")
        audio = r.listen(source, timeout=5, phrase_time_limit=5)
    try:
        comando = r.recognize_google(audio, language="es-ES").lower()
        ejecutar_comando(comando, tere_gui)
    except:
        tere_gui.cambiar_estado("error")
        tere_gui.root.after(3000, lambda: tere_gui.cambiar_estado("dormida"))

def detectar_roxana(tere_gui):
    porcupine = pvporcupine.create(
        access_key=ACCESS_KEY,
        keyword_paths=["wakeword/roxana_windows.ppn"],
        model_path="model/porcupine_params_es.pv"
    )
    pa = pyaudio.PyAudio()
    stream = pa.open(rate=porcupine.sample_rate, channels=1,
                     format=pyaudio.paInt16, input=True,
                     frames_per_buffer=porcupine.frame_length)

    try:
        while True:
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            if porcupine.process(pcm) >= 0:
                threading.Thread(target=escuchar_comando, args=(tere_gui,), daemon=True).start()
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        porcupine.delete()

# -------------------- MAIN --------------------
def main():
    tere_gui = TereGUI()
    threading.Thread(target=detectar_roxana, args=(tere_gui,), daemon=True).start()
    tere_gui.iniciar()

if __name__ == "__main__":
    main()
