import csv
from email.message import EmailMessage
import random, plistlib, shutil, os
import subprocess
import threading
import re
import time
import smtplib
import json

with open("config.json", "r") as f:
    config = json.load(f)

def send_mail(student):
    email_body = f"""\
                Buongiorno {student['name']} {student['surname']},  
                in allegato trova il file necessario per accedere al test tramite Safe Exam Browser.

                File allegato: {student['username']}.seb  
                Codice di accesso: {student['password']}

                Una volta aperto il file .seb, l’ambiente d’esame sarà attivato.  
                Attenzione: uscire dal Safe Exam Browser comporta l’annullamento immediato del tentativo.

                Cordiali saluti,  
                CPLocarno Java Bot

                p.s.: Questa mail è automatizzata, se qualcosa non va dirlo immediatamente al professore.
                """

    msg = EmailMessage()
    msg.set_content(email_body)
    msg['Subject'] = f'Java enviroment for test - {student['name']} {student['surname']}'
    msg['From'] = config["admin_email"]
    msg['To'] = student['email']

    with open(f"./SEBFiles/{student['username']}.seb", "rb") as f:
        file_data = f.read()
        file_name = f"{student['username']}.seb"
        msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)

    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.ehlo()
    s.starttls()
    s.login(config["sender_mail"], config["sender_app_pwd"])
    s.sendmail(config["sender_mail"], [student['email']], msg.as_string())
    s.quit()

def generate_docker_compose(students):
    services = []
    for student in students:
        services.append(f"""
  {str(student['username']).lower()}:
    build: .
    ports: 
      - "{student['port']}:{config["base_port"]}"
    volumes:
      - ./projects/{str(student['username'])}:/home/coder/project/
    environment:
      EXTENSIONS_GALLERY: "null"
      PASSWORD: "{student['password']}"
        """)
    return "services:\n" + "\n".join(services)

def generate_seb_files(students):
    with open("./templates/SEBSettingsTemplate.seb", "rb") as f:
        seb_template = plistlib.load(f)

    for student in students:
        seb_file = seb_template.copy()

        new_url = f"http://{config["base_domain"]}:{student['port']}"
        seb_file["startURL"] = new_url

        with open(f"./SEBFiles/{student['username']}.seb", "wb") as f:
            plistlib.dump(seb_file, f)

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
                    subprocess.run(["docker", "stop", f"{config["docker_container_prefix"]}{container}"])
                    checked.add(container)
        proc.stdout.close()
        proc.wait()
        time.sleep(5)

def main():
    for directory in [config["SEB_folder_name"], config["projects_folder_name"]]:
        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.makedirs(directory, exist_ok=True)

    students = []

    with open(config["Students.csv_path"], newline='', encoding="utf-8") as csvfile:
        for i, row in enumerate(csv.DictReader(csvfile)):
            classe = str(row.get("class", ""))
            nome = str(row.get("name", "")).capitalize()
            cognome = str(row.get("surname", "")).capitalize()
            username = classe + "_" + nome + cognome
            password = f"{random.randint(0, 999999):06d}"
            port = config["base_port"] + i
            students.append({"name": nome, "surname": cognome, "username": username, "password": password, "port": port, "email": str(row.get("email", ""))})
    
    if (config["emergency_user"]): students.append({"name": "emergency", "surname": "user", "username": "emergency_user", "password": f"{random.randint(0, 999999):06d}", "port": "8079", "email": config["admin_email"]})

    docker_compose = generate_docker_compose(students)
    
    with open(config["docker-compose_path"], "w") as file:
        file.write(docker_compose)
    
    print("File 'docker-compose.yaml' generato con successo!")

    generate_seb_files(students)

    print("SEB files generati con successo!")

    for student in students:
        send_mail(student=student)

    print(students)

    t = threading.Thread(target=monitor_logs_and_shutdown, daemon=True)
    t.start()

    print("Avvio dei container con 'docker-compose up --build'...")
    subprocess.run(["docker-compose", "up", "--build"])

if __name__ == "__main__":
    main()
