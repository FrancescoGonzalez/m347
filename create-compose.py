import csv
import random, plistlib, shutil, os

base_port = 8080
base_domain = "172.20.10.4"

def generate_docker_compose(students):
    services = []
    for student in students:
        services.append(f"""
  {str(student['name'])}:
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
            students.append({"name": username, "password": password, "port": port})

    docker_compose = generate_docker_compose(students)
    
    with open("docker-compose.yaml", "w") as file:
        file.write(docker_compose)
    
    print("File 'docker-compose.yaml' generato con successo!")

    generate_seb_files(students)

    print("SEB files generati con successo!")

    print(students)

    print("Per avviare il tutto eseguire 'docker-compose up --build'")

if __name__ == "__main__":
    main()


### TODO
# usare flask per fare interfaccia web
# implementare csv per inserimento allievi - FATTO
# inviare .seb via main
# Implementare OTP (tirar giu il container quando si esce)