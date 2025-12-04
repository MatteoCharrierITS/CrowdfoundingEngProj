"""
auto_regen_watcher.py
Guarda la cartella md/ e invoca scripts/regenerate_preview.py quando cambiano i file.
"""
import time
import threading
import subprocess
import sys
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except Exception:
    print('watchdog non installato. Installa con: python -m pip install watchdog')
    raise

ROOT = Path(__file__).resolve().parent.parent
MD_DIR = ROOT / 'md'
LOG_DIR = ROOT / 'logs'
SCRIPT = ROOT / 'scripts' / 'regenerate_preview.py'
CMD = f'"{sys.executable}" "{SCRIPT.as_posix()}"'

# Setup logging
LOG_DIR.mkdir(exist_ok=True)
WATCHER_LOG_FILE = LOG_DIR / 'watcher.log'

watcher_logger = logging.getLogger('watcher')
watcher_logger.setLevel(logging.INFO)
watcher_logger.handlers.clear()  # Rimuovi handler esistenti

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(message)s'))
watcher_logger.addHandler(console_handler)

# File handler
file_handler = RotatingFileHandler(str(WATCHER_LOG_FILE), maxBytes=1024*1024, backupCount=3, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
watcher_logger.addHandler(file_handler)

class DebouncedHandler(FileSystemEventHandler):
    def __init__(self, action, delay=0.25):
        super().__init__()
        self.action = action
        self.delay = delay
        self._timer = None
        self._lock = threading.Lock()

    def _schedule(self):
        with self._lock:
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(self.delay, self._run_action)
            self._timer.daemon = True
            self._timer.start()

    def _run_action(self):
        try:
            self.action()
        except Exception as e:
            print(f'Errore durante l''azione: {e}')

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith('.md'):
            msg = f'File creato: {Path(event.src_path).name}'
            print(msg)
            watcher_logger.info(msg)
            self._schedule()

    def on_deleted(self, event):
        if not event.is_directory and event.src_path.lower().endswith('.md'):
            msg = f'File eliminato: {Path(event.src_path).name}'
            print(msg)
            watcher_logger.info(msg)
            self._schedule()

    def on_modified(self, event):
        if not event.is_directory and event.src_path.lower().endswith('.md'):
            msg = f'File modificato: {Path(event.src_path).name}'
            print(msg)
            watcher_logger.info(msg)
            self._schedule()


def run_command(cmd):
    watcher_logger.info('Rigenerazione HTML in corso...')
    print(f'Eseguo: {cmd}')
    try:
        completed = subprocess.run(cmd, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if completed.returncode == 0:
            watcher_logger.info('✓ HTML rigenerato con successo')
        else:
            watcher_logger.error(f'Errore rigenerazione (exit code: {completed.returncode})')
        if completed.stdout:
            print(completed.stdout)
        if completed.stderr:
            print(completed.stderr, file=sys.stderr)
            watcher_logger.error(completed.stderr)
    except Exception as e:
        msg = f'Errore esecuzione comando: {e}'
        print(msg, file=sys.stderr)
        watcher_logger.error(msg)


def main():
    # Salva PID per permettere terminazione pulita
    import os
    pid_file = ROOT / 'watcher.pid'
    pid_file.write_text(str(os.getpid()))
    
    def action():
        run_command(CMD)

    event_handler = DebouncedHandler(action, delay=0.25)
    observer = Observer()
    observer.schedule(event_handler, str(MD_DIR), recursive=True)
    observer.start()

    try:
        msg = 'In ascolto di cambiamenti su md/** (ricorsivo). Premere Ctrl+C per terminare.'
        print(msg)
        watcher_logger.info('=== File Watcher avviato - Monitoraggio cartella md/ ===')
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('Interruzione richiesta, fermo watcher...')
        watcher_logger.info('Watcher terminato dall\'utente')
    finally:
        observer.stop()
        observer.join()
        # Rimuovi file PID alla chiusura
        if pid_file.exists():
            pid_file.unlink()
        watcher_logger.info('Watcher arrestato')

if __name__ == '__main__':
    main()
