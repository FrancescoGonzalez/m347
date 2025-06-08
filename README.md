# M347 - Java Test Environment Manager

Sistema di gestione per ambienti di test Java con Docker e Safe Exam Browser (SEB), progettato per gestire test di programmazione in ambiente controllato.

## Panoramica

Questo progetto automatizza la creazione e gestione di ambienti di sviluppo Java containerizzati per studenti, con:
- **Generazione automatica** di container Docker personalizzati
- **Invio automatico di email** con file SEB configurati
- **Interfaccia web** per monitoraggio e controllo
- **Download di progetti** per la correzione
- **Gestione sicura** tramite Safe Exam Browser

## Struttura del Progetto

```
m347/
├── app.py                          # Server Flask principale
├── create_compose.py               # Generatore ambiente test
├── config.json                     # Configurazione
├── Students.csv                    # Database studenti
├── dockerfile                      # Immagine Docker base
├── docker-compose.yaml             # Generato automaticamente
├── templates/
│   ├── index.html                  # Interfaccia admin
│   └── SEBSettingsTemplate.seb     # Template SEB
├── static/
│   ├── css/styles.css              # Stili
│   └── js/script.js                # JavaScript
├── projects/                       # Cartelle studenti (generate)
└── SEBFiles/                       # File SEB (generati)
```

## Configurazione

### 1. Modifica `config.json`

```json
{
  "sender_mail": "TUA_EMAIL_BOT@gmail.com",
  "sender_app_pwd": "TUA_APP_PASSWORD_GMAIL",
  
  "emergency_user": true,
  "admin_email": "TUA_EMAIL_ADMIN@gmail.com",
  
  "base_domain": "INDIRIZZO_IP",
  "base_port": 8080,
  
  "SEB_folder_name": "./SEBFiles",
  "projects_folder_name": "./projects",
  "Students.csv_path": "./Students.csv",
  "docker-compose_path": "./docker-compose.yaml",
  "docker_container_prefix": "NOMECARTELLA-"
}
```

**Per favore fai in modo di controllare tutti i parametri, se no l'applicazione non funzionerà**

Controllare con maggiore attenzione i **primi sei** parametri e **l'ultimo**

### 2. Configura `Students.csv`

**Formato richiesto:**
- **`class`**: Classe dello studente
- **`name`**: Nome (sarà capitalizzato automaticamente)
- **`surname`**: Cognome (sarà capitalizzato automaticamente)  
- **`email`**: Email per ricevere file SEB

## Installazione e Avvio

### Prerequisiti

- Python
- Flask
- Docker

### Avvio dell'Applicazione

Dopo aver configurato il `config.json` e `Students.csv`, avviare tramite python il file `app.py`

Il server sarà disponibile su: **http://localhost:5000**

## Note per l'Utilizzo

### Best Practices
1. **Test preliminare**: Prova sempre il setup prima del test reale
2. **Controllo email**: Verifica che le email arrivino correttamente

### Limitazioni
- **Dipendenza da Docker**: Richiede Docker funzionante
- **Rete locale**: Studenti devono essere sulla stessa rete
- **Safe Exam Browser**: Studenti devono averlo installato
- **Gmail**: Dipende dalla configurazione email Google
