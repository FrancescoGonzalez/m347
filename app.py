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

with open("config.json", "r") as f:
    config = json.load(f)
    
container_statuses = {}
setup_running = False
setup_complete = False

@app.route("/")
def index():
    update_container_statuses()
    return render_template("index.html", has_config=True, 
                          setup_running=setup_running, 
                          setup_complete=setup_complete,
                          container_statuses=container_statuses)

@app.route("/files/<student>")
def list_files(student):
    student_dir = os.path.join(config["projects_folder_name"], student)
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
    file_path = os.path.join(config["projects_folder_name"], student, filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({"content": content, "success": True})
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@app.route("/status")
def get_status():
    update_container_statuses()
    
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
    
    thread = threading.Thread(target=run_setup)
    thread.daemon = True
    thread.start()
    
    return jsonify({"success": True, "message": "Setup avviato"})

@app.route("/end_setup", methods=["POST"])
def end_setup():
    global setup_running, setup_complete
    
    setup_running = False
    setup_complete = True
    
    thread = threading.Thread(target=stop_containers)
    thread.daemon = True
    thread.start()
    
    return jsonify({"success": True, "message": "Setup terminato manualmente"})

def stop_containers():
    try:
        print("Arresto dei container Docker in corso...")
        subprocess.run(["docker-compose", "-f", config["docker-compose_path"], "down"], check=True)
        print("Container Docker arrestati con successo")
    except Exception as e:
        print(f"Errore durante l'arresto dei container Docker: {e}")
    finally:
        update_container_statuses()

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
        setup_thread = threading.Thread(target=create_compose.main)
        setup_thread.daemon = True
        setup_thread.start()
        setup_thread.join()
        setup_complete = True
    except Exception as e:
        print(f"Errore durante l'esecuzione dello script: {e}")
    finally:
        setup_running = False
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
                    if name.startswith(config["docker_container_prefix"]):
                        username = name[len(config["docker_container_prefix"]):]
                        
                        if len(username) > 2 and username[-2] == '-' and username[-1].isdigit():
                            username = username[:-2]
                        
                        username = username.lower()
                        
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
    
    containers = get_docker_containers()
    
    students = []
    if os.path.exists(config["projects_folder_name"]):
        students = [s for s in os.listdir(config["projects_folder_name"]) 
                   if os.path.isdir(os.path.join(config["projects_folder_name"], s))]
    
    statuses = {}
    
    for student in students:
        statuses[student] = "inattivo"
    
    for container_name, status in containers.items():
        base_name = re.sub(r'-\d+$', '', container_name)
        
        matching_student = None
        for student in students:
            if student.lower() == base_name.lower():
                matching_student = student
                break
        
        if matching_student:
            statuses[matching_student] = "attivo" if "up" in status.lower() else "inattivo"
        else:
            statuses[base_name] = "attivo" if "up" in status.lower() else "inattivo"
    
    container_statuses = statuses

def status_updater_thread():
    while True:
        update_container_statuses()
        time.sleep(5)

if __name__ == "__main__":
    os.makedirs(config["projects_folder_name"], exist_ok=True)
    
    threading.Thread(target=status_updater_thread, daemon=True).start()
    
    update_container_statuses()
    
    app.run(debug=True, host='0.0.0.0', port=5000)