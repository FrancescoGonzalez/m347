from flask import Flask, render_template, send_from_directory, jsonify, request
import os
import json
import subprocess
import threading
import time
import re
import shutil
import create_compose

app = Flask(__name__)

STUDENT_DIR = "./projects"
CONFIG_FILE = "config.json" 
CREATE_SCRIPT = "create-compose.py"  # Il nome dello script principale
DOCKER_CONTAINER_PREFIX = "progettofinale-"

# Variabili globali
container_statuses = {}
setup_running = False
setup_complete = False

@app.route("/")
def index():
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            has_config = True
    except:
        has_config = False

    # Assicurati che i container siano aggiornati prima di renderizzare la pagina
    update_container_statuses()
    
    return render_template("index.html", has_config=has_config, 
                          setup_running=setup_running, 
                          setup_complete=setup_complete,
                          container_statuses=container_statuses)

@app.route("/files/<student>")
def list_files(student):
    student_dir = os.path.join(STUDENT_DIR, student)
    if not os.path.isdir(student_dir):
        return jsonify({"error": "Studente non trovato"}), 404
    
    files = []
    for root, dirs, filenames in os.walk(student_dir):
        rel_path = os.path.relpath(root, student_dir)
        rel_path = "" if rel_path == "." else rel_path
        
        for f in filenames:
            file_path = os.path.join(rel_path, f)
            files.append({
                "name": f,
                "path": file_path,
                "full_path": os.path.join(student, file_path)
            })
    
    return jsonify(files)

@app.route("/content/<student>/<path:filename>")
def get_file_content(student, filename):
    file_path = os.path.join(STUDENT_DIR, student, filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({"content": content, "success": True})
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@app.route("/status")
def get_status():
    update_container_statuses()
    
    # Crea un nuovo dizionario solo con chiavi lowercase per evitare duplicati
    normalized_statuses = {}
    for name, status in container_statuses.items():
        normalized_statuses[name.lower()] = status
    
    return jsonify(normalized_statuses)

@app.route("/start", methods=["POST"])
def start_setup():
    global setup_running, setup_complete
    
    if setup_running:
        return jsonify({"success": False, "message": "Setup già in esecuzione"}), 400
    
    setup_running = True
    setup_complete = False
    
    # Avvia il processo in un thread separato
    thread = threading.Thread(target=run_setup)
    thread.daemon = True
    thread.start()
    
    return jsonify({"success": True, "message": "Setup avviato"})

@app.route("/end_setup", methods=["POST"])
def end_setup():
    global setup_running, setup_complete
    
    # Rimuoviamo questa condizione per permettere di terminare in qualsiasi momento
    # if not setup_running:
    #     return jsonify({"success": False, "message": "Nessun setup in esecuzione"}), 400
    
    setup_running = False
    setup_complete = True
    
    # Qui puoi aggiungere un comando per terminare il setup se necessario
    # Ad esempio: subprocess.run(["docker-compose", "down"])
    
    return jsonify({"success": True, "message": "Setup terminato manualmente"})

@app.route("/setup_status")
def setup_status():
    return jsonify({
        "running": setup_running,
        "complete": setup_complete 
    })

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

def run_setup():
    global setup_running, setup_complete, container_statuses
    
    try:
        # Run create_compose.main() in a separate thread
        setup_thread = threading.Thread(target=create_compose.main)
        setup_thread.daemon = True
        setup_thread.start()
        setup_thread.join()  # Wait for it to complete
        setup_complete = True
    except Exception as e:
        print(f"Errore durante l'esecuzione dello script: {e}")
    finally:
        setup_running = False
        # Aggiorna lo stato dei container
        update_container_statuses()

def get_docker_containers():
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}},{{.Status}}"],
            capture_output=True, 
            text=True, 
            check=True
        )
        containers = {}
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split(',', 1)
                if len(parts) == 2:
                    name, status = parts
                    if name.startswith(DOCKER_CONTAINER_PREFIX):
                        username = name[len(DOCKER_CONTAINER_PREFIX):]
                        
                        # Rimuovi il suffisso numerico se presente (es: -1, -2, ecc.)
                        if len(username) > 2 and username[-2] == '-' and username[-1].isdigit():
                            username = username[:-2]
                        
                        # Converti tutto in lowercase per evitare duplicati dovuti a capitalizzazione
                        username = username.lower()
                        
                        # Se abbiamo già un container con questo nome, dai priorità allo stato "up"
                        if username in containers:
                            if "up" not in containers[username].lower() and "up" in status.lower():
                                containers[username] = status
                        else:
                            containers[username] = status
        return containers
    except Exception as e:
        print(f"Errore nel recupero dei container Docker: {e}")
        return {}

def update_container_statuses():
    global container_statuses
    
    # Ottieni lo stato dei container Docker
    containers = get_docker_containers()
    
    # Check students directories
    students = []
    if os.path.exists(STUDENT_DIR):
        students = [s for s in os.listdir(STUDENT_DIR) if os.path.isdir(os.path.join(STUDENT_DIR, s))]
    
    # Crea un dizionario per tenere traccia dei nomi base e dei loro stati
    base_containers = {}
    
    # Per ogni container, determina il nome base (senza suffissi come -1)
    for container_name, status in containers.items():
        # Rimuovi suffissi come -1, -2, ecc.
        base_name = re.sub(r'-\d+$', '', container_name)
        
        # Se c'è già un container con questo nome base, usa quello con lo stato "up" se disponibile
        if base_name in base_containers:
            existing_status = base_containers[base_name]
            # Se il container esistente non è attivo ma questo sì, sostituiscilo
            if "up" not in existing_status.lower() and "up" in status.lower():
                base_containers[base_name] = status
        else:
            base_containers[base_name] = status
    
    # Aggiorna lo stato per ogni studente
    statuses = {}
    
    # Aggiungi tutti gli studenti con directory
    for student in students:
        added = False
        # Verifica se esiste un container con nome base che corrisponde a questo studente
        # (case insensitive)
        for base_name in base_containers:
            if base_name.lower() == student.lower():
                status = base_containers[base_name]
                statuses[student] = "attivo" if "up" in status.lower() else "inattivo"
                added = True
                break
        
        # Se non è stato trovato un container corrispondente
        if not added:
            statuses[student] = "inattivo"
    
    # Aggiungi container che potrebbero non avere directory
    for base_name, status in base_containers.items():
        # Verifica se questo container è già stato associato a uno studente
        if not any(student.lower() == base_name.lower() for student in students):
            statuses[base_name] = "attivo" if "up" in status.lower() else "inattivo"
    
    container_statuses = statuses

# Avvia un thread per aggiornare periodicamente lo stato dei container
def status_updater_thread():
    while True:
        update_container_statuses()
        time.sleep(5)  # Aggiorna ogni 5 secondi

if __name__ == "__main__":
    # Assicurati che la cartella projects esista
    os.makedirs(STUDENT_DIR, exist_ok=True)
    
    # Avvia il thread di aggiornamento dello stato
    threading.Thread(target=status_updater_thread, daemon=True).start()
    
    # Inizializza lo stato dei container all'avvio
    update_container_statuses()
    
    app.run(debug=True, host='0.0.0.0', port=5000)