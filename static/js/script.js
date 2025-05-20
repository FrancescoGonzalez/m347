// Variabili globali
let currentStudent = null;
let currentFile = null;
let autoRefreshInterval = null;
let autoRefreshEnabled = true;
const REFRESH_INTERVAL = 5000; // 5 secondi

// Aggiorna la lista degli studenti
function refreshStudentList() {
    fetch('/status')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Received student data:', data); // Per debugging
            
            const studentList = document.getElementById('student-list');
            studentList.innerHTML = '';
            
            if (!data || Object.keys(data).length === 0) {
                studentList.innerHTML = '<li class="no-content">Nessuno studente trovato</li>';
                return;
            }
            
            // Ordina gli studenti alfabeticamente
            const sortedStudents = Object.keys(data).sort();
            
            for (const student of sortedStudents) {
                const status = data[student];
                console.log(`Creating element for student ${student} with status ${status}`); // Per debugging
                
                const li = document.createElement('li');
                li.className = `student-item status-${status}`;
                li.dataset.student = student;
                
                // Rendi l'intero elemento li cliccabile
                li.addEventListener('click', function() {
                    selectStudent(student);
                });
                
                // Aggiungi l'indicatore di stato e il nome dello studente
                const statusIcon = document.createElement('span');
                statusIcon.className = 'status-indicator';
                
                const nameSpan = document.createElement('span');
                nameSpan.className = 'student-name';
                nameSpan.textContent = student;
                
                // Costruisci l'elemento
                li.appendChild(statusIcon);
                li.appendChild(nameSpan);
                studentList.appendChild(li);
            }
            
            // Se l'utente aveva selezionato uno studente, mantieni la selezione
            if (currentStudent) {
                const selectedItem = document.querySelector(`.student-item[data-student="${currentStudent}"]`);
                if (selectedItem) {
                    selectedItem.classList.add('selected');
                }
            }
        })
        .catch(error => {
            console.error('Errore nel recupero degli studenti:', error);
            document.getElementById('student-list').innerHTML = 
                '<li class="no-content">Errore nel caricamento degli studenti: ' + error.message + '</li>';
        });
}

// Seleziona uno studente e carica i suoi file
function selectStudent(student) {
    currentStudent = student;
    
    // Aggiorna la UI per mostrare lo studente selezionato
    document.querySelectorAll('.student-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    const studentItem = document.querySelector(`.student-item[data-student="${student}"]`);
    if (studentItem) {
        studentItem.classList.add('selected');
    }
    
    document.getElementById('current-student').textContent = student;
    
    // Carica i file dello studente
    loadStudentFiles(student);
}

// Carica i file di uno studente
function loadStudentFiles(student) {
    fetch(`/files/${student}`)
        .then(response => response.json())
        .then(data => {
            const fileList = document.getElementById('file-list');
            fileList.innerHTML = '';
            
            if (!data || data.error || data.length === 0) {
                fileList.innerHTML = '<li class="no-content">Nessun file trovato</li>';
                return;
            }
            
            data.forEach(file => {
                const li = document.createElement('li');
                li.className = 'file-item';
                li.textContent = file.path;
                li.dataset.path = file.full_path;
                
                li.addEventListener('click', function() {
                    selectFile(file.full_path, file.name);
                });
                
                fileList.appendChild(li);
            });
        })
        .catch(error => {
            console.error('Errore nel recupero dei file:', error);
            document.getElementById('file-list').innerHTML = 
                '<li class="no-content">Errore nel caricamento dei file</li>';
        });
}

// Seleziona un file e mostra il suo contenuto
function selectFile(filePath, fileName) {
    currentFile = filePath;
    
    // Aggiorna la UI per mostrare il file selezionato
    document.querySelectorAll('.file-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    const fileItem = document.querySelector(`.file-item[data-path="${filePath}"]`);
    if (fileItem) {
        fileItem.classList.add('selected');
    }
    
    document.getElementById('current-file').textContent = fileName || filePath.split('/').pop();
    
    // Carica il contenuto del file
    loadFileContent(filePath);
    
    // Imposta il refresh automatico per questo file solo se abilitato
    if (autoRefreshEnabled) {
        startAutoRefresh();
    }
}

// Carica il contenuto di un file
function loadFileContent(filePath) {
    fetch(`/content/${filePath}`)
        .then(response => response.json())
        .then(data => {
            const contentDisplay = document.getElementById('file-content-display');
            
            if (data.success && data.content) {
                contentDisplay.textContent = data.content;
                contentDisplay.classList.remove('no-content');
            } else {
                contentDisplay.textContent = 'Errore nel caricamento del contenuto';
                contentDisplay.classList.add('no-content');
            }
        })
        .catch(error => {
            console.error('Errore nel recupero del contenuto:', error);
            document.getElementById('file-content-display').textContent = 'Errore nel caricamento del contenuto';
            document.getElementById('file-content-display').classList.add('no-content');
        });
}

// Avvia il refresh automatico per il file corrente
function startAutoRefresh() {
    // Cancella qualsiasi intervallo precedente
    stopAutoRefresh();
    
    // Imposta un nuovo intervallo solo se c'è un file selezionato
    if (currentFile) {
        autoRefreshInterval = setInterval(() => {
            loadFileContent(currentFile);
        }, REFRESH_INTERVAL);
    }
}

// Ferma il refresh automatico
function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// Attiva/disattiva l'aggiornamento automatico
function toggleAutoRefresh() {
    autoRefreshEnabled = !autoRefreshEnabled;
    
    const toggleBtn = document.getElementById('toggle-refresh');
    const statusSpan = document.getElementById('auto-refresh-status');
    
    if (autoRefreshEnabled) {
        toggleBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Disabilita Aggiornamento Automatico';
        toggleBtn.classList.remove('btn-success');
        toggleBtn.classList.add('btn-warning');
        statusSpan.textContent = 'Aggiornamento automatico attivo';
        
        // Riavvia l'aggiornamento automatico se c'è un file selezionato
        if (currentFile) {
            startAutoRefresh();
        }
    } else {
        toggleBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Abilita Aggiornamento Automatico';
        toggleBtn.classList.remove('btn-warning');
        toggleBtn.classList.add('btn-success');
        statusSpan.textContent = 'Aggiornamento automatico disattivato';
        
        // Ferma l'aggiornamento automatico se è attivo
        stopAutoRefresh();
    }
}

// Sostituisci gli event listener per i pulsanti
document.getElementById('start-setup').addEventListener('click', function() {
    // Aggiorna lo stato del setup
    document.getElementById('setup-status').textContent = 'Setup in esecuzione...';
    this.disabled = true;
    document.getElementById('end-setup').disabled = false;
    
    fetch('/start', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        console.log(data.message);
        // Inizia a controllare lo stato del setup
        checkSetupStatus();
    })
    .catch(error => {
        console.error('Errore nell\'avvio del setup:', error);
        document.getElementById('setup-status').textContent = 'Errore nell\'avvio del setup.';
        document.getElementById('start-setup').disabled = false;
    });
});

document.getElementById('end-setup').addEventListener('click', function() {
    fetch('/end_setup', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        console.log(data.message);
        document.getElementById('setup-status').textContent = 'Setup terminato manualmente.';
        document.getElementById('start-setup').disabled = false;
        document.getElementById('end-setup').disabled = false;
        refreshStudentList();
    })
    .catch(error => {
        console.error('Errore nella terminazione del setup:', error);
        document.getElementById('setup-status').textContent = 'Errore nella terminazione del setup.';
    });
});

// Controlla lo stato del setup
function checkSetupStatus() {
    fetch('/setup_status')
        .then(response => response.json())
        .then(data => {
            if (data.running) {
                document.getElementById('setup-status').textContent = 'Setup in esecuzione...';
                document.getElementById('end-setup').disabled = false;
                // Controlla di nuovo dopo un intervallo
                setTimeout(checkSetupStatus, 2000);
            } else {
                if (data.complete) {
                    document.getElementById('setup-status').textContent = 'Setup completato con successo.';
                } else {
                    document.getElementById('setup-status').textContent = 'Setup fallito o interrotto.';
                }
                document.getElementById('start-setup').disabled = false;
                document.getElementById('end-setup').disabled = true;
                // Aggiorna la lista degli studenti
                refreshStudentList();
            }
        })
        .catch(error => {
            console.error('Errore nel controllo dello stato del setup:', error);
            document.getElementById('setup-status').textContent = 'Errore nel controllo dello stato.';
            document.getElementById('start-setup').disabled = false;
            document.getElementById('end-setup').disabled = true;
        });
}

// Modifica la funzione di inizializzazione alla fine del file
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded');
    
    // Abilita l'aggiornamento automatico all'avvio
    autoRefreshEnabled = true;
    
    // Carica la lista degli studenti all'avvio
    refreshStudentList();
    
    // Imposta l'aggiornamento periodico della lista degli studenti
    setInterval(refreshStudentList, 5000); // Cambiato a 5 secondi per avere aggiornamenti più frequenti
    
    // Aggiungi l'event listener per il refresh manuale
    document.getElementById('refresh-students').addEventListener('click', function() {
        console.log('Manual refresh triggered');
        refreshStudentList();
    });
    
    // Verifica lo stato iniziale del setup
    checkSetupStatus();
    
    // Configura i toggle button per il setup
    configureSetupButtons();
});

// Aggiungi questa nuova funzione per configurare i pulsanti
// Aggiungi questa nuova funzione per configurare i pulsanti
function configureSetupButtons() {
    const startSetupBtn = document.getElementById('start-setup');
    const endSetupBtn = document.getElementById('end-setup');
    
    // Inizialmente nascondiamo entrambi i pulsanti fino a quando non verifichiamo lo stato
    startSetupBtn.style.display = 'none';
    endSetupBtn.style.display = 'none';
    
    // Verifica immediatamente lo stato dei container per determinare quale pulsante mostrare
    fetch('/status')
        .then(response => response.json())
        .then(containers => {
            let anyContainerActive = false;
            
            // Verifica se c'è almeno un container attivo
            for (const studentName in containers) {
                if (containers[studentName] === "attivo") {
                    anyContainerActive = true;
                    break;
                }
            }
            
            if (anyContainerActive) {
                // Se ci sono container attivi, mostra il pulsante per terminare
                startSetupBtn.style.display = 'none';
                endSetupBtn.style.display = 'inline-block';
                document.getElementById('setup-status').textContent = 'Docker attivo. Puoi terminare il setup.';
            } else {
                // Altrimenti mostra il pulsante per avviare
                startSetupBtn.style.display = 'inline-block';
                endSetupBtn.style.display = 'none';
                document.getElementById('setup-status').textContent = 'Docker non attivo. Puoi avviare il setup.';
            }
        })
        .catch(error => {
            console.error('Errore nel controllo dei container:', error);
            document.getElementById('setup-status').textContent = 'Errore nel controllo dello stato di Docker.';
            // In caso di errore, mostriamo il pulsante di avvio per sicurezza
            startSetupBtn.style.display = 'inline-block';
            endSetupBtn.style.display = 'none';
        });
    
    // Modifica l'event listener per "Avvia setup"
    startSetupBtn.addEventListener('click', function() {
        document.getElementById('setup-status').textContent = 'Setup in esecuzione...';
        // Nascondi il pulsante "Avvia" e mostra "Termina"
        startSetupBtn.style.display = 'none';
        endSetupBtn.style.display = 'inline-block';
        
        fetch('/start', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            console.log(data.message);
            // Inizia a controllare lo stato del setup
            checkSetupStatus();
        })
        .catch(error => {
            console.error('Errore nell\'avvio del setup:', error);
            document.getElementById('setup-status').textContent = 'Errore nell\'avvio del setup.';
            // In caso di errore, ripristina i pulsanti
            startSetupBtn.style.display = 'inline-block';
            endSetupBtn.style.display = 'none';
        });
    });

    // Modifica l'event listener per "Termina setup"
    endSetupBtn.addEventListener('click', function() {
        fetch('/end_setup', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            console.log(data.message);
            document.getElementById('setup-status').textContent = 'Setup terminato manualmente.';
            // Nascondi il pulsante "Termina" e mostra "Avvia"
            startSetupBtn.style.display = 'inline-block';
            endSetupBtn.style.display = 'none';
            refreshStudentList();
        })
        .catch(error => {
            console.error('Errore nella terminazione del setup:', error);
            document.getElementById('setup-status').textContent = 'Errore nella terminazione del setup.';
        });
    });
}

// Modifica la funzione che controlla lo stato del setup
function checkSetupStatus() {
    fetch('/setup_status')
        .then(response => response.json())
        .then(data => {
            const startSetupBtn = document.getElementById('start-setup');
            const endSetupBtn = document.getElementById('end-setup');
            
            if (data.running) {
                document.getElementById('setup-status').textContent = 'Setup in esecuzione...';
                // Mostra solo il pulsante per terminare
                startSetupBtn.style.display = 'none';
                endSetupBtn.style.display = 'inline-block';
                
                // Controlla di nuovo dopo un intervallo
                setTimeout(checkSetupStatus, 2000);
            } else {
                if (data.complete) {
                    document.getElementById('setup-status').textContent = 'Setup completato con successo.';
                } else {
                    // Verifichiamo se ci sono container attivi per determinare quale pulsante mostrare
                    fetch('/status')
                        .then(response => response.json())
                        .then(containers => {
                            let anyContainerActive = false;
                            
                            // Verifica se c'è almeno un container attivo
                            for (const studentName in containers) {
                                if (containers[studentName] === "attivo") {
                                    anyContainerActive = true;
                                    break;
                                }
                            }
                            
                            if (anyContainerActive) {
                                // Se ci sono container attivi, mostra il pulsante per terminare
                                startSetupBtn.style.display = 'none';
                                endSetupBtn.style.display = 'inline-block';
                                document.getElementById('setup-status').textContent = 'Docker attivo. Puoi terminare il setup.';
                            } else {
                                // Altrimenti mostra il pulsante per avviare
                                startSetupBtn.style.display = 'inline-block';
                                endSetupBtn.style.display = 'none';
                                document.getElementById('setup-status').textContent = 'Docker non attivo. Puoi avviare il setup.';
                            }
                        })
                        .catch(error => {
                            console.error('Errore nel controllo dei container:', error);
                            document.getElementById('setup-status').textContent = 'Errore nel controllo dello stato di Docker.';
                            startSetupBtn.style.display = 'inline-block';
                            endSetupBtn.style.display = 'none';
                        });
                }
            }
        })
        .catch(error => {
            console.error('Errore nel controllo dello stato del setup:', error);
            document.getElementById('setup-status').textContent = 'Errore nel controllo dello stato.';
            // In caso di errore, mostriamo il pulsante di avvio per sicurezza
            document.getElementById('start-setup').style.display = 'inline-block';
            document.getElementById('end-setup').style.display = 'none';
        });
}