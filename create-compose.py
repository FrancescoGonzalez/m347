import csv
import random, plistlib, shutil, os
import subprocess
import threading
import re
import time

base_port = 8080
base_domain = "localhost"
admin_email = "francibgonza21@gmail.com"
emergency_user = True

def generate_docker_compose(students):
    services = []
    for student in students:
        services.append(f"""
  {str(student['name']).lower()}:
    build: .
    ports: 
      - "{student['port']}:{base_port}"
    volumes:
      - ./projects/{str(student['name'])}:/home/coder/project/
    environment:
      EXTENSIONS_GALLERY: "null"
      PASSWORD: "{student['password']}"
        """)
    return "services:\n" + "\n".join(services)

def generate_seb_files(students):
    with open("./SEBSettingsTemplate.seb", "rb") as f:
        seb_template = plistlib.load(f)

    for student in students:
        config = seb_template.copy()

        new_url = f"http://{base_domain}:{student['port']}"
        config["startURL"] = new_url

        with open(f"./SEBFiles/{student['name']}.seb", "wb") as f:
            plistlib.dump(config, f)

def monitor_logs_and_shutdown():
    pattern = re.compile(r"^([a-zA-Z0-9_\-]+)\s+\|\s+.*\[ManagementConnection\] The client has disconnected")
    checked = set()
    while True:
        proc = subprocess.Popen(
            ["docker-compose", "logs", "--tail=100"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        for line in proc.stdout:
            match = pattern.search(line)
            if match:
                container = match.group(1)
                if container not in checked:
                    print(f"Disconnessione rilevata per {container}, arresto container...")
                    subprocess.run(["docker", "stop", f"progettofinale-{container}"])
                    checked.add(container)
        proc.stdout.close()
        proc.wait()
        time.sleep(5)

def main():
    shutil.rmtree("./projects")
    shutil.rmtree("./SEBFiles")
    os.makedirs("./SEBFiles", exist_ok=True)
    os.makedirs("./projects", exist_ok=True)

    students = []

    with open("Students.csv", newline='', encoding="utf-8") as csvfile:
        for i, row in enumerate(csv.DictReader(csvfile)):
            classe = str(row.get("classe", ""))
            nome = str(row.get("nome", "")).capitalize()
            cognome = str(row.get("cognome", "")).capitalize()
            username = classe + "_" + nome + cognome
            password = f"{random.randint(0, 999999):06d}"
            port = base_port + i
            students.append({"name": username, "password": password, "port": port, "email": str(row.get("email", ""))})
    
    if (emergency_user): students.append({"name": "emergency_user", "password": f"{random.randint(0, 999999):06d}", "port": "8079", "email": admin_email})

    docker_compose = generate_docker_compose(students)
    
    with open("docker-compose.yaml", "w") as file:
        file.write(docker_compose)
    
    print("File 'docker-compose.yaml' generato con successo!")

    generate_seb_files(students)

    print("SEB files generati con successo!")

    print(students)

    # Avvia il thread che monitora i log
    t = threading.Thread(target=monitor_logs_and_shutdown, daemon=True)
    t.start()

    # Avvia docker-compose up --build
    print("Avvio dei container con 'docker-compose up --build'...")
    subprocess.run(["docker-compose", "up", "--build"])

if __name__ == "__main__":
    main()


### TODO
# usare flask per fare interfaccia web
# inviare .seb via mail