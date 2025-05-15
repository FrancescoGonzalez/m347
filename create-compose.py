import random, plistlib, shutil, os

base_port = 8080
base_domain = "172.20.10.4"

def generate_docker_compose(students):
    services = []
    for student in students:
        services.append(f"""
  {str(student['name']).lower()}:
    build: .
    ports: 
      - "{student['port']}:{base_port}"
    volumes:
      - ./projects/{str(student['name']).lower()}:/home/coder/project/
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

        with open(f"./SEBFiles/{student['name'].lower()}.seb", "wb") as f:
            plistlib.dump(config, f)

def main():
    shutil.rmtree("./projects")
    shutil.rmtree("./SEBFiles")
    os.makedirs("./SEBFiles", exist_ok=True)
    os.makedirs("./projects", exist_ok=True)

    number_of_students = int(input("Inserire il numero di studenti che faranno il test: "))

    students = []

    for i in range(number_of_students):
        name = input(f"Inserire il nome dello studente {i + 1}: ")
        password = f"{random.randint(0, 999999):06d}"
        port = base_port + i
        students.append({"name": name, "password": password, "port": port})

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