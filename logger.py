from datetime import datetime

def log_update(update_code: str):
    now = datetime.now()
    timestamp = now.strftime("%d/%m/%Y, %H:%M:%S")
    line = f"update, {timestamp}, {update_code}\n"
    
    with open("roxana_update_log.txt", "a", encoding="utf-8") as f_update, \
         open("roxana_log.txt", "a", encoding="utf-8") as f_log:
        f_update.write(line)
        f_log.write(line)

def log_request(action: str, status: str = ""):
    # Si status viene vacío, no lo pone, sino lo añade después de la acción
    now = datetime.now()
    timestamp = now.strftime("%d/%m/%Y, %H:%M:%S")

    if status:
        line = f"request, {timestamp}, {action}, {status}\n"
    else:
        line = f"request, {timestamp}, {action}\n"
    
    with open("roxana_request_log.txt", "a", encoding="utf-8") as f_request, \
         open("roxana_log.txt", "a", encoding="utf-8") as f_log:
        f_request.write(line)
        f_log.write(line)

