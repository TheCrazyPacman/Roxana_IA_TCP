import os
import win32com.client
import re
from logger import log_update, log_request

# Rutas comunes de accesos directos
RUTAS = [
    os.path.join(os.environ["PROGRAMDATA"], r"Microsoft\Windows\Start Menu\Programs"),
    os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs"),
]

# Ruta específica de accesos directos de Steam
STEAM_SHORTCUTS_PATH = r"C:\Users\TCP\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Steam"

def limpiar_nombre(nombre):
    # Quita todo lo que no sea letra o número
    return re.sub(r'[^a-z0-9]', '', nombre.lower())

def limpiar_comando(frase):
    frase = frase.strip().lower()
    if frase.endswith(" please"):
        frase = frase[:-7]
    elif frase.endswith(" por favor"):
        frase = frase[:-10]
    return frase.strip()

def resolver_lnk(lnk_path):
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(lnk_path)
    target = shortcut.Targetpath
    args = shortcut.Arguments
    if args:
        return [target] + args.split()
    else:
        return [target]

def leer_url_file(url_path):
    # Lee un archivo .url y devuelve la URL si es steam://...
    try:
        with open(url_path, "r", encoding="utf-8") as f:
            for linea in f:
                if linea.strip().lower().startswith("url=steam://"):
                    url = linea.strip()[4:]  # quitar "URL="
                    return url
    except Exception as e:
        print(f"❌ Error leyendo URL: {url_path} ({e})")
    return None

def detectar_accesos_directos_steam(ruta):
    comandos = {}
    for archivo in os.listdir(ruta):
        ruta_completa = os.path.join(ruta, archivo)
        nombre = os.path.splitext(archivo)[0].lower()
        nombre_limpio = limpiar_nombre(nombre)

        if archivo.endswith(".lnk"):
            try:
                ruta_objetivo = resolver_lnk(ruta_completa)
                if ruta_objetivo[0].startswith("steam://"):
                    comando_original = f"open {nombre}"
                    comandos[comando_original] = (ruta_objetivo, True, nombre.title(), ruta_objetivo[0])
                    if nombre_limpio != nombre:
                        comando_limpio = f"open {nombre_limpio}"
                        comandos[comando_limpio] = (ruta_objetivo, True, nombre.title(), ruta_objetivo[0])
            except Exception as e:
                print(f"❌ Error en acceso Steam .lnk: {ruta_completa} ({e})")
        elif archivo.endswith(".url"):
            url = leer_url_file(ruta_completa)
            if url and url.startswith("steam://rungameid/"):
                comando_original = f"open {nombre}"
                comandos[comando_original] = (["start", url], True, nombre.title(), url)
                if nombre_limpio != nombre:
                    comando_limpio = f"open {nombre_limpio}"
                    comandos[comando_limpio] = (["start", url], True, nombre.title(), url)
    return comandos

def obtener_accesos():
    accesos = []
    for ruta in RUTAS:
        for root, dirs, files in os.walk(ruta):
            for file in files:
                if file.endswith(".lnk"):
                    accesos.append(os.path.join(root, file))
    return accesos

def generar_comandos():
    accesos = obtener_accesos()
    comandos = {}

    # Comandos del sistema
    comandos["apagar pc"] = (["shutdown", "/s", "/t", "0"], True, "Apagar PC", "shutdown.exe")
    comandos["restart pc"] = (["shutdown", "/r", "/t", "0"], True, "Reiniciar PC", "shutdown.exe")
    comandos["reiniciar pc"] = (["shutdown", "/r", "/t", "0"], True, "Reiniciar PC", "shutdown.exe")

    # Comandos de accesos directos normales (.lnk)
    for acceso in accesos:
        try:
            ruta_ejecutable_con_args = resolver_lnk(acceso)
            ruta_ejecutable = ruta_ejecutable_con_args[0]
            nombre = os.path.splitext(os.path.basename(acceso))[0].lower()
            nombre_limpio = limpiar_nombre(nombre)
            nombre_exe = os.path.basename(ruta_ejecutable)

            # Genera comando con nombre original
            clave_original = f"open {nombre}"
            if ruta_ejecutable.startswith("steam://"):
                comandos[clave_original] = (ruta_ejecutable_con_args, True, nombre.title(), ruta_ejecutable)
            elif ruta_ejecutable.endswith(".exe"):
                comandos[clave_original] = (ruta_ejecutable_con_args, False, nombre.title(), nombre_exe)

            # Si el nombre limpio es diferente, genera comando adicional
            if nombre_limpio != nombre:
                clave_limpia = f"open {nombre_limpio}"
                if ruta_ejecutable.startswith("steam://"):
                    comandos[clave_limpia] = (ruta_ejecutable_con_args, True, nombre.title(), ruta_ejecutable)
                elif ruta_ejecutable.endswith(".exe"):
                    comandos[clave_limpia] = (ruta_ejecutable_con_args, False, nombre.title(), nombre_exe)

        except Exception as e:
            print(f"❌ No se pudo procesar: {acceso} ({e})")

    # Accesos directos de juegos Steam (.lnk y .url)
    if os.path.exists(STEAM_SHORTCUTS_PATH):
        comandos_steam = detectar_accesos_directos_steam(STEAM_SHORTCUTS_PATH)
        # Solo agregamos los comandos que empiezan con "open"
        for k, v in list(comandos_steam.items()):
            if k.startswith("open "):
                comandos[k] = v

    return comandos

def guardar_comandos(comandos_dict, archivo="comandos.py"):
    with open(archivo, "w", encoding="utf-8") as f:
        f.write("# Archivo generado automáticamente\n")
        f.write("comandos = {\n")
        for clave, valor in sorted(comandos_dict.items()):
            f.write(f'    "{clave}": {valor},\n')
        f.write("}\n")

if __name__ == "__main__":
    cmds = generar_comandos()
    log_update(len(cmds))  # Mejor aquí, antes de guardar
    guardar_comandos(cmds)
    print(f"✅ Se generaron {len(cmds)} comandos en comandos.py")

