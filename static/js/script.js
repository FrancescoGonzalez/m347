let currentStudent = null;
let currentFile = null;
let autoRefreshInterval = null;
let autoRefreshEnabled = true;
const REFRESH_INTERVAL = 5000;

function refreshStudentList() {
    fetch('/status')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Received student data:', data);
            
            const studentList = document.getElementById('student-list');
            studentList.innerHTML = '';
            
            if (!data || Object.keys(data).length === 0) {
                studentList.innerHTML = '<li class="no-content">Nessuno studente trovato</li>';
                return;
            }
            
            const sortedStudents = Object.keys(data).sort();
            
            for (const student of sortedStudents) {
                const status = data[student];
                console.log(`Creating element for student ${student} with status ${status}`);
                
                const li = document.createElement('li');
                li.className = `student-item status-${status}`;
                li.dataset.student = student;
                
                li.addEventListener('click', function() {
                    selectStudent(student);
                });
                
                const statusIcon = document.createElement('span');
                statusIcon.className = 'status-indicator';
                
                const nameSpan = document.createElement('span');
                nameSpan.className = 'student-name';
                nameSpan.textContent = student;
                
                li.appendChild(statusIcon);
                li.appendChild(nameSpan);
                studentList.appendChild(li);
            }
            
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

function selectStudent(student) {
    currentStudent = student;
    
    document.querySelectorAll('.student-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    const studentItem = document.querySelector(`.student-item[data-student="${student}"]`);
    if (studentItem) {
        studentItem.classList.add('selected');
    }
    
    document.getElementById('current-student').textContent = student;
    
    loadStudentFiles(student);
}

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

function selectFile(filePath, fileName) {
    currentFile = filePath;
    
    document.querySelectorAll('.file-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    const fileItem = document.querySelector(`.file-item[data-path="${filePath}"]`);
    if (fileItem) {
        fileItem.classList.add('selected');
    }
    
    document.getElementById('current-file').textContent = fileName || filePath.split('/').pop();
    
    loadFileContent(filePath);
    
    if (autoRefreshEnabled) {
        startAutoRefresh();
    }
}

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

function startAutoRefresh() {
    stopAutoRefresh();
    
    if (currentFile) {
        autoRefreshInterval = setInterval(() => {
            loadFileContent(currentFile);
        }, REFRESH_INTERVAL);
    }
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

function toggleAutoRefresh() {
    autoRefreshEnabled = !autoRefreshEnabled;
    
    const toggleBtn = document.getElementById('toggle-refresh');
    const statusSpan = document.getElementById('auto-refresh-status');
    
    if (autoRefreshEnabled) {
        toggleBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Disabilita Aggiornamento Automatico';
        toggleBtn.classList.remove('btn-success');
        toggleBtn.classList.add('btn-warning');
        statusSpan.textContent = 'Aggiornamento automatico attivo';
        
        if (currentFile) {
            startAutoRefresh();
        }
    } else {
        toggleBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Abilita Aggiornamento Automatico';
        toggleBtn.classList.remove('btn-warning');
        toggleBtn.classList.add('btn-success');
        statusSpan.textContent = 'Aggiornamento automatico disattivato';
        
        stopAutoRefresh();
    }
}

document.getElementById('start-setup').addEventListener('click', function() {
    document.getElementById('setup-status').textContent = 'Setup in esecuzione...';
    this.disabled = true;
    document.getElementById('end-setup').disabled = false;
    
    fetch('/start', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        console.log(data.message);
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

function checkSetupStatus() {
    fetch('/setup_status')
        .then(response => response.json())
        .then(data => {
            if (data.running) {
                document.getElementById('setup-status').textContent = 'Setup in esecuzione...';
                document.getElementById('end-setup').disabled = false;
                setTimeout(checkSetupStatus, 2000);
            } else {
                if (data.complete) {
                    document.getElementById('setup-status').textContent = 'Setup completato con successo.';
                } else {
                    document.getElementById('setup-status').textContent = 'Setup fallito o interrotto.';
                }
                document.getElementById('start-setup').disabled = false;
                document.getElementById('end-setup').disabled = true;
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

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded');
    
    autoRefreshEnabled = true;
    
    refreshStudentList();
    
    setInterval(refreshStudentList, 5000);
    
    checkSetupStatus();
    
    configureSetupButtons();
});

function configureSetupButtons() {
    const startSetupBtn = document.getElementById('start-setup');
    const endSetupBtn = document.getElementById('end-setup');
    
    startSetupBtn.style.display = 'none';
    endSetupBtn.style.display = 'none';
    
    fetch('/status')
        .then(response => response.json())
        .then(containers => {
            let anyContainerActive = false;
            
            for (const studentName in containers) {
                if (containers[studentName] === "attivo") {
                    anyContainerActive = true;
                    break;
                }
            }
            
            if (anyContainerActive) {
                startSetupBtn.style.display = 'none';
                endSetupBtn.style.display = 'inline-block';
                document.getElementById('setup-status').textContent = 'Docker attivo. Puoi terminare il setup.';
            } else {
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
    
    startSetupBtn.addEventListener('click', function() {
        document.getElementById('setup-status').textContent = 'Setup in esecuzione...';
        startSetupBtn.style.display = 'none';
        endSetupBtn.style.display = 'inline-block';
        
        fetch('/start', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            console.log(data.message);
            checkSetupStatus();
        })
        .catch(error => {
            console.error('Errore nell\'avvio del setup:', error);
            document.getElementById('setup-status').textContent = 'Errore nell\'avvio del setup.';
            startSetupBtn.style.display = 'inline-block';
            endSetupBtn.style.display = 'none';
        });
    });

    endSetupBtn.addEventListener('click', function() {
        fetch('/end_setup', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            console.log(data.message);
            document.getElementById('setup-status').textContent = 'Setup terminato manualmente.';
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

function checkSetupStatus() {
    fetch('/setup_status')
        .then(response => response.json())
        .then(data => {
            const startSetupBtn = document.getElementById('start-setup');
            const endSetupBtn = document.getElementById('end-setup');
            
            if (data.running) {
                document.getElementById('setup-status').textContent = 'Setup in esecuzione...';
                startSetupBtn.style.display = 'none';
                endSetupBtn.style.display = 'inline-block';
                
                setTimeout(checkSetupStatus, 2000);
            } else {
                if (data.complete) {
                    document.getElementById('setup-status').textContent = 'Setup completato con successo.';
                } else {
                    fetch('/status')
                        .then(response => response.json())
                        .then(containers => {
                            let anyContainerActive = false;
                            
                            for (const studentName in containers) {
                                if (containers[studentName] === "attivo") {
                                    anyContainerActive = true;
                                    break;
                                }
                            }
                            
                            if (anyContainerActive) {
                                startSetupBtn.style.display = 'none';
                                endSetupBtn.style.display = 'inline-block';
                                document.getElementById('setup-status').textContent = 'Docker attivo. Puoi terminare il setup.';
                            } else {
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
            document.getElementById('start-setup').style.display = 'inline-block';
            document.getElementById('end-setup').style.display = 'none';
        });
}