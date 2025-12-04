@echo off
echo ========================================
echo    AppuntiApp - Avvio Rapido
echo ========================================
echo.

REM Verifica Python
echo [1/4] Verifico Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRORE] Python non trovato!
    echo.
    echo Installazione Python in corso...
    winget install Python.Python.3.12 -e --silent
    if errorlevel 1 (
        echo [ERRORE] Installazione fallita. Installa Python manualmente da python.org
        pause
        exit /b 1
    )
    echo Python installato! Riavvia questo script.
    pause
    exit /b 0
)
echo [OK] Python trovato

REM Verifica dipendenze Python
echo.
echo [2/4] Verifico dipendenze Python...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [WARN] Flask non trovato, installazione in corso...
    pip install flask flask-cors watchdog
    if errorlevel 1 (
        echo [ERRORE] Installazione dipendenze fallita
        pause
        exit /b 1
    )
    echo [OK] Dipendenze installate
) else (
    echo [OK] Flask trovato
)

python -c "import watchdog" >nul 2>&1
if errorlevel 1 (
    echo [WARN] Watchdog non trovato, installazione in corso...
    pip install watchdog
)

REM Genera HTML iniziali
echo.
echo [3/4] Genero file HTML...
python scripts\regenerate_preview.py >nul 2>&1
echo [OK] File HTML generati

REM Avvia servizi
echo.
echo [4/4] Avvio servizi...

REM Pulisci vecchi file PID se esistono
del api_server.pid >nul 2>&1
del watcher.pid >nul 2>&1

REM Verifica che nessun altro processo stia usando la porta 5000
netstat -ano | find ":5000" | find "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [WARN] Porta 5000 gia in uso, termino i processi esistenti...
    for /f "tokens=5" %%a in ('netstat -ano ^| find ":5000" ^| find "LISTENING"') do taskkill /PID %%a /F >nul 2>&1
    timeout /t 1 /nobreak >nul
)

start "AppuntiApp-API" cmd /k "cd /d "%~dp0" && python scripts\api_server.py || pause"
echo Attendo avvio API server...
timeout /t 3 /nobreak >nul

REM Verifica che il server API sia effettivamente partito
set API_READY=0
for /L %%i in (1,1,10) do (
    netstat -ano | find ":5000" | find "LISTENING" >nul 2>&1
    if not errorlevel 1 (
        set API_READY=1
        goto API_STARTED
    )
    timeout /t 1 /nobreak >nul
)
:API_STARTED

if %API_READY%==0 (
    echo [ERRORE] Server API non avviato correttamente!
    echo Controlla la finestra "AppuntiApp-API" per i dettagli dell'errore
    pause
    exit /b 1
)
echo [OK] API Server avviato sulla porta 5000

start "AppuntiApp-Watcher" cmd /k "cd /d "%~dp0" && python scripts\auto_regen_watcher.py || pause"
echo Attendo avvio Watcher...
timeout /t 2 /nobreak >nul
echo [OK] Watcher avviato

REM Ottieni PID del processo browser che verrà aperto
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq chrome.exe" /FO LIST ^| find "PID:"') do set CHROME_COUNT_BEFORE=%%i
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq msedge.exe" /FO LIST ^| find "PID:"') do set EDGE_COUNT_BEFORE=%%i
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq firefox.exe" /FO LIST ^| find "PID:"') do set FIREFOX_COUNT_BEFORE=%%i

REM Apri browser
start http://localhost:5000
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo   Tutto pronto!
echo ========================================
echo.
echo Server in esecuzione su: http://localhost:5000
echo.
echo CHIUDENDO IL BROWSER, I PROCESSI SI TERMINERANNO AUTOMATICAMENTE
echo Oppure premi Ctrl+C per fermare manualmente
echo.

REM Aspetta che il browser si connetta
set CONNECTED=0
:WAIT_CONNECTION
timeout /t 2 /nobreak >nul 2>&1
netstat -ano | find "5000" | find "ESTABLISHED" >nul 2>&1
if not errorlevel 1 (
    set CONNECTED=1
    echo [INFO] Browser connesso al server
    goto START_MONITOR
)
REM Timeout dopo 30 secondi se non si connette
set /a WAIT_COUNT+=1
if %WAIT_COUNT% LSS 15 goto WAIT_CONNECTION

:START_MONITOR
REM Monitora usando un approccio basato su richieste HTTP recenti
set LAST_REQUEST_TIME=0
set NO_REQUEST_COUNT=0

:MONITOR
timeout /t 5 /nobreak >nul 2>&1

REM Conta le connessioni ESTABLISHED correnti
for /f %%c in ('netstat -ano ^| find "5000" ^| find "ESTABLISHED" ^| find /C /V ""') do set CURRENT_CONN=%%c

REM Se ci sono connessioni attive, resetta il contatore
if not "%CURRENT_CONN%"=="0" (
    set NO_REQUEST_COUNT=0
    goto MONITOR
)

REM Nessuna connessione attiva, incrementa contatore
set /a NO_REQUEST_COUNT+=1

REM Attendi 8 controlli senza connessioni (40 secondi)
if %NO_REQUEST_COUNT% LSS 8 (
    goto MONITOR
)

echo.
echo [INFO] Nessuna attivita per 40 secondi. Chiusura processi...

REM Verifica finale: controlla se il server è ancora in ascolto
netstat -ano | find ":5000" | find "LISTENING" >nul 2>&1
if errorlevel 1 (
    REM Server non in ascolto, probabilmente crashato
    echo.
    echo [WARN] Server non piu in ascolto. Uscita...
    exit /b 0
)

echo.
echo Nessuna connessione attiva per 30 secondi. Chiusura processi...
        
        REM Usa file PID se esistono
        if exist api_server.pid (
            for /f %%p in (api_server.pid) do taskkill /PID %%p /F /T >nul 2>&1
            del api_server.pid >nul 2>&1
        )
        if exist watcher.pid (
            for /f %%p in (watcher.pid) do taskkill /PID %%p /F /T >nul 2>&1
            del watcher.pid >nul 2>&1
        )
        
        REM Metodo alternativo: cerca per command line
        for /f "tokens=2" %%i in ('wmic process where "CommandLine like '%%api_server.py%%'" get ProcessId 2^>nul ^| find /V "ProcessId"') do (
            taskkill /PID %%i /F /T >nul 2>&1
        )
        for /f "tokens=2" %%i in ('wmic process where "CommandLine like '%%auto_regen_watcher.py%%'" get ProcessId 2^>nul ^| find /V "ProcessId"') do (
            taskkill /PID %%i /F /T >nul 2>&1
        )
        
        REM Fallback: termina finestre cmd
        taskkill /FI "WINDOWTITLE eq AppuntiApp-API*" /F /T >nul 2>&1
        taskkill /FI "WINDOWTITLE eq AppuntiApp-Watcher*" /F /T >nul 2>&1
        
        echo Processi terminati.
        timeout /t 2 /nobreak >nul
        exit /b 0
    )
)
goto MONITOR
