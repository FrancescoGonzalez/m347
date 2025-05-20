import csv
from email.message import EmailMessage
import random, plistlib, shutil, os
import subprocess
import threading
import re
import time
import smtplib

base_port = 8080
base_domain = "localhost"
admin_email = "francibgonza21@gmail.com"
emergency_user = True

sender_mail = "CPLocarnoJavaBot@gmail.com"
sender_pwd = "dmdc opoo ltem qzga"

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
    msg['From'] = admin_email
    msg['To'] = student['email']

    with open(f"./SEBFiles/{student['username']}.seb", "rb") as f:
        file_data = f.read()
        file_name = f"{student['username']}.seb"
        msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)

    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.ehlo()
    s.starttls()
    s.login(sender_mail, sender_pwd)
    s.sendmail(admin_email, [student['email']], msg.as_string())
    s.quit()

def generate_docker_compose(students):
    services = []
    for student in students:
        services.append(f"""
  {str(student['username']).lower()}:
    build: .
    ports: 
      - "{student['port']}:{base_port}"
    volumes:
      - ./projects/{str(student['username'])}:/home/coder/project/
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

        with open(f"./SEBFiles/{student['username']}.seb", "wb") as f:
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
            classe = str(row.get("class", ""))
            nome = str(row.get("name", "")).capitalize()
            cognome = str(row.get("surname", "")).capitalize()
            username = classe + "_" + nome + cognome
            password = f"{random.randint(0, 999999):06d}"
            port = base_port + i
            students.append({"name": nome, "surname": cognome, "username": username, "password": password, "port": port, "email": str(row.get("email", ""))})
    
    if (emergency_user): students.append({"name": "emergency", "surname": "user", "username": "emergency_user", "password": f"{random.randint(0, 999999):06d}", "port": "8079", "email": admin_email})

    docker_compose = generate_docker_compose(students)
    
    with open("docker-compose.yaml", "w") as file:
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


### TODO
# usare flask per fare interfaccia web
# inviare .seb via mail