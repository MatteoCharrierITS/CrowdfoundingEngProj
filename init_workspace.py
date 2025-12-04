"""
init_workspace.py

Organizza la cartella del progetto in questa struttura:
- app/        (opzionale: riservata all'app se serve)
- web/        (contiene le pagine .html pubbliche: preview.html, viewer.html, ecc.)
- scripts/    (contiene gli script Python/PowerShell per generare/guardare)
- md/         (contiene i file .md sorgente)

Cosa fa:
- crea le cartelle se non esistono
- sposta i file esistenti nelle cartelle appropriate
- crea/aggiorna `scripts/regenerate_preview.py` e `scripts/auto_regen_watcher.py`
- crea `project.code-workspace` con le 4 cartelle (per aprire in VSCode pulito)
- avvia un semplice server HTTP che serve la cartella `web/` e apre `preview.html` nel browser
- prova ad aprire il workspace in VS Code se il comando `code` è disponibile

Esegui:
  python init_workspace.py

Nota: lo script non richiede privilegi admin. Controlla output e conferma prima di sovrascrivere file.
"""
from pathlib import Path
import shutil
import os
import http.server
import socketserver
import webbrowser
import subprocess
import sys
import time
import threading

ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / 'app'
WEB_DIR = ROOT / 'web'
SCRIPTS_DIR = ROOT / 'scripts'
MD_DIR = ROOT / 'md'

# Check and install dependencies
def check_and_install_dependencies():
    """Controlla se le dipendenze sono installate e le installa se necessario."""
    dependencies = ['flask', 'flask_cors', 'watchdog']
    missing = []
    
    print('Controllo dipendenze...')
    for dep in dependencies:
        try:
            __import__(dep)
            print(f'  ✅ {dep} già installato')
        except ImportError:
            print(f'  ❌ {dep} mancante')
            missing.append(dep)
    
    if missing:
        print(f'\n📦 Installazione di {len(missing)} dipendenze mancanti...')
        for package in missing:
            print(f'\nInstallazione di {package}...')
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package], 
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f'  ✅ {package} installato con successo')
            except subprocess.CalledProcessError as e:
                print(f'  ⚠️  Errore nell\'installazione di {package}: {e}')
        print('\n✨ Installazione dipendenze completata!\n')
    else:
        print('✅ Tutte le dipendenze sono già installate\n')

check_and_install_dependencies()

print('Inizializzazione workspace...')
for d in (APP_DIR, WEB_DIR, SCRIPTS_DIR, MD_DIR):
    d.mkdir(exist_ok=True)
    print(f'  - assicurata cartella: {d.name}')

# Move files by extension
moved = []
# HTML files -> web (except some generator html we might want to keep)
for p in ROOT.glob('*.html'):
    # skip workspace file if exists
    if p.name in ('project.code-workspace',):
        continue
    target = WEB_DIR / p.name
    if p.samefile(target) if target.exists() else False:
        continue
    print(f'Muovo {p.name} -> {target}')
    shutil.move(str(p), str(target))
    moved.append(p.name)

# Markdown files -> md
for p in ROOT.glob('*.md'):
    target = MD_DIR / p.name
    if p.samefile(target) if target.exists() else False:
        continue
    print(f'Muovo {p.name} -> {target}')
    shutil.move(str(p), str(target))
    moved.append(p.name)

# Scripts and json/requirements -> scripts
for ext in ('*.py','*.ps1','package.json','requirements.txt'):
    for p in ROOT.glob(ext):
        # do not move this init script
        if p.name == Path(__file__).name:
            continue
        # skip files already in scripts
        target = SCRIPTS_DIR / p.name
        if p.samefile(target) if target.exists() else False:
            continue
        print(f'Muovo {p.name} -> {target}')
        shutil.move(str(p), str(target))
        moved.append(p.name)

# Create a simple workspace file for VSCode listing only the 4 folders
workspace = {
    "folders": [
        {"path": "app"},
        {"path": "web"},
        {"path": "scripts"},
        {"path": "md"}
    ],
    "settings": {}
}
import json
workspace_path = ROOT / 'project.code-workspace'
with workspace_path.open('w', encoding='utf-8') as f:
    json.dump(workspace, f, indent=2)
print(f'Creato workspace: {workspace_path.name}')

# Write scripts/regenerate_preview.py (overwrites if exists)
regenerate_code = r'''"""
regenerate_preview.py
Genera preview.html e viewer HTML nella cartella web/ leggendo i .md dalla cartella md/.
"""
from pathlib import Path
import html

ROOT = Path(__file__).resolve().parent.parent
MD_DIR = ROOT / 'md'
WEB_DIR = ROOT / 'web'
WEB_DIR.mkdir(exist_ok=True)

md_files = sorted([p for p in MD_DIR.iterdir() if p.is_file() and p.suffix.lower()=='.md'])

links = []
for md in md_files:
    text = md.read_text(encoding='utf-8')
    text_escaped = text.replace('</script>', r'<\/script>')
    viewer_name = md.with_suffix('.html').name
    viewer_path = WEB_DIR / viewer_name

    viewer_html = """<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>%%TITLE%%</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/atom-one-dark.min.css">
  <style>
    :root{--bg:#0b0f12;--panel:#0f1720;--text:#e6eef6;--muted:#98a0ac;--accent:#4cc9f0}
    body{background:var(--bg);color:var(--text);font-family:Inter,Segoe UI,Roboto,Arial,Helvetica Neue,sans-serif;margin:0;padding:28px}
    .wrap{max-width:900px;margin:0 auto}
    header{display:flex;align-items:center;gap:12px}
    a.button{background:transparent;border:1px solid rgba(255,255,255,0.07);color:var(--text);padding:8px 12px;border-radius:8px;text-decoration:none}
    .title{font-size:18px;font-weight:600}
    .meta{color:var(--muted);font-size:13px}
    main{background:var(--panel);padding:24px;border-radius:12px;margin-top:18px;box-shadow:0 6px 18px rgba(0,0,0,0.6)}
    h1,h2,h3{color:var(--text)}
    p,li{color:var(--text)}
    ul{margin-left:1.2em}
    pre, code{background:#011217;color:#d6e9f6;padding:8px;border-radius:6px;overflow:auto}
    footer{color:var(--muted);margin-top:18px;font-size:13px}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <a class="button" href="preview.html">← Indietro</a>
      <div>
        <div class="title">%%FILENAME%%</div>
        <div class="meta">Generato da regenerate_preview.py</div>
      </div>
    </header>

    <main id="content">Caricamento…</main>

    <footer>File sorgente: <code>%%FILENAME%%</code></footer>
  </div>

  <script id="md-content" type="text/plain">
%%MD_TEXT%%
  </script>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/5.1.1/marked.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
  <script>
    (function(){
      const md = document.getElementById('md-content').textContent;
      const content = document.getElementById('content');
      marked.setOptions({ headerIds: true, mangle: false });
      content.innerHTML = marked.parse(md);
      document.querySelectorAll('pre code').forEach((el)=>hljs.highlightElement(el));
    })();
    
    // Auto-reload: controlla ogni 2 secondi se la pagina è cambiata
    (function autoReload(){
      let lastCheck = Date.now();
      setInterval(function(){
        fetch(location.href, {method: 'HEAD', cache: 'no-cache'})
          .then(function(res){
            const lastMod = res.headers.get('last-modified');
            if(lastMod){
              const modTime = new Date(lastMod).getTime();
              if(modTime > lastCheck){
                console.log('Pagina aggiornata, ricarico...');
                location.reload();
              }
            }
          })
          .catch(function(){});
      }, 2000);
    })();
  </script>
</body>
</html>"""

    viewer_html = viewer_html.replace('%%MD_TEXT%%', text_escaped)
    viewer_html = viewer_html.replace('%%TITLE%%', html.escape(md.stem))
    viewer_html = viewer_html.replace('%%FILENAME%%', html.escape(md.name))

    viewer_path.write_text(viewer_html, encoding='utf-8')
    print(f'Generato viewer: {viewer_name}')
    links.append(f'<a href="{viewer_name}">{html.escape(md.name)}</a>')

# generate preview.html
if links:
    links_html = '\n'.join(links)
else:
    links_html = '<div class="empty">Nessun file .md trovato</div>'

preview_html = """<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Documenti Markdown - Preview</title>
  <style>
    :root{--bg:#0b0f12;--panel:#0f1720;--text:#e6eef6;--muted:#98a0ac;--accent:#4cc9f0}
    body{background:var(--bg);color:var(--text);font-family:Inter,Segoe UI,Roboto,Arial,Helvetica Neue,sans-serif;margin:0;padding:28px}
    .wrap{max-width:1000px;margin:0 auto}
    header{display:flex;align-items:center;justify-content:space-between;gap:12px}
    h1{font-size:22px;margin:0}
    .meta{color:var(--muted);font-size:13px}
    main{margin-top:18px;display:grid;grid-template-columns:300px 1fr;gap:18px}
    .panel{background:var(--panel);padding:18px;border-radius:12px}
    .list a{display:block;color:var(--text);text-decoration:none;padding:8px;border-radius:8px;margin-bottom:6px;border:1px solid rgba(255,255,255,0.03)}
    .list a:hover{background:rgba(255,255,255,0.02)}
    footer{color:var(--muted);margin-top:20px;font-size:13px}
    .empty{color:var(--muted);font-size:14px}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <div>
        <h1>Documenti Markdown</h1>
        <div class="meta">Cartella: <code>%%ROOT_NAME%%</code></div>
      </div>
      <div class="meta">Tema: Scuro • Click su un file per aprirlo</div>
    </header>

    <main>
      <aside class="panel list">
        <h3 style="margin-top:0;color:var(--accent)">Elenco file</h3>
%%LINKS_HTML%%
      </aside>

      <section class="panel">
        <h3 style="margin-top:0;color:var(--accent)">Istruzioni</h3>
        <p class="empty">Clicca su un file nell'elenco per aprire la versione completa. Esegui questo script ogni volta che aggiungi o modifichi file se non vuoi usare un server locale.</p>
      </section>
    </main>

    <footer>
      Pagina generata automaticamente da <code>regenerate_preview.py</code>
    </footer>
  </div>
</body>
</html>"""

preview_html = preview_html.replace('%%LINKS_HTML%%', links_html)
preview_html = preview_html.replace('%%ROOT_NAME%%', html.escape(ROOT.name))

preview_path = WEB_DIR / 'preview.html'
preview_path.write_text(preview_html, encoding='utf-8')
print('Generato indice: preview.html')
print('Operazione completata.')
'''

scripts_regenerate = SCRIPTS_DIR / 'regenerate_preview.py'
with scripts_regenerate.open('w', encoding='utf-8') as f:
    f.write(regenerate_code)
print(f'Creato/aggiornato: {scripts_regenerate.relative_to(ROOT)}')

# Write scripts/auto_regen_watcher.py
watcher_code = r'''"""
auto_regen_watcher.py
Guarda la cartella md/ e invoca scripts/regenerate_preview.py quando cambiano i file.
"""
import time
import threading
import subprocess
import sys
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except Exception:
    print('watchdog non installato. Installa con: python -m pip install watchdog')
    raise

ROOT = Path(__file__).resolve().parent.parent
MD_DIR = ROOT / 'md'
SCRIPT = ROOT / 'scripts' / 'regenerate_preview.py'
CMD = f'"{sys.executable}" "{SCRIPT.as_posix()}"'

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
            print(f'Creato: {event.src_path}')
            self._schedule()

    def on_deleted(self, event):
        if not event.is_directory and event.src_path.lower().endswith('.md'):
            print(f'Cancellato: {event.src_path}')
            self._schedule()

    def on_modified(self, event):
        if not event.is_directory and event.src_path.lower().endswith('.md'):
            print(f'Modificato: {event.src_path}')
            self._schedule()


def run_command(cmd):
    print(f'Eseguo: {cmd}')
    try:
        completed = subprocess.run(cmd, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if completed.stdout:
            print(completed.stdout)
        if completed.stderr:
            print(completed.stderr, file=sys.stderr)
    except Exception as e:
        print(f'Errore esecuzione comando: {e}', file=sys.stderr)


def main():
    def action():
        run_command(CMD)

    event_handler = DebouncedHandler(action, delay=0.25)
    observer = Observer()
    observer.schedule(event_handler, str(MD_DIR), recursive=False)
    observer.start()

    try:
        print('In ascolto di cambiamenti su md/*. Premere Ctrl+C per terminare.')
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('Interruzione richiesta, fermo watcher...')
    finally:
        observer.stop()
        observer.join()

if __name__ == '__main__':
    main()
'''

scripts_watcher = SCRIPTS_DIR / 'auto_regen_watcher.py'
with scripts_watcher.open('w', encoding='utf-8') as f:
    f.write(watcher_code)
print(f'Creato/aggiornato: {scripts_watcher.relative_to(ROOT)}')

# Try to open the workspace in VSCode (if `code` command available)
try:
    subprocess.run(['code', str(workspace_path)], check=False)
    print('Tentativo di aprire VSCode workspace (se `code` è nel PATH).')
except Exception:
    print('Non ho potuto aprire VSCode automaticamente (comando `code` non disponibile).')

# Start a simple HTTP server to serve web/ and open preview.html
PORT = 8000
os.chdir(WEB_DIR)
print(f'Avvio server HTTP su http://localhost:{PORT}/preview.html')
handler = http.server.SimpleHTTPRequestHandler
httpd = socketserver.TCPServer(('', PORT), handler)

# open browser in a separate thread after a small delay
def open_browser():
    time.sleep(1)
    webbrowser.open(f'http://localhost:{PORT}/preview.html')

threading.Thread(target=open_browser, daemon=True).start()

# Start helper services (api_server and watcher) as subprocesses so they run alongside the HTTP server.
child_procs = []
try:
    api_script = SCRIPTS_DIR / 'api_server.py'
    watcher_script = SCRIPTS_DIR / 'auto_regen_watcher.py'
    creationflags = getattr(subprocess, 'CREATE_NEW_CONSOLE', 0)

    if api_script.exists():
        try:
            print(f'Avvio API server: {api_script}')
            p = subprocess.Popen([sys.executable, str(api_script)], cwd=str(ROOT), creationflags=creationflags)
            child_procs.append(p)
        except Exception as e:
            print(f'Impossibile avviare api_server.py: {e}')

    if watcher_script.exists():
        try:
            print(f'Avvio watcher: {watcher_script}')
            p = subprocess.Popen([sys.executable, str(watcher_script)], cwd=str(ROOT), creationflags=creationflags)
            child_procs.append(p)
        except Exception as e:
            print(f'Impossibile avviare auto_regen_watcher.py: {e}')
except Exception as _:
    # non critico: segui comunque con il server principale
    pass

try:
    httpd.serve_forever()
except KeyboardInterrupt:
    print('Server interrotto dall\'utente.')
    httpd.shutdown()
    # terminate child processes we spawned
    for cp in child_procs:
        try:
            print(f'Termino processo figlio (pid={cp.pid})')
            cp.terminate()
        except Exception:
            pass
    sys.exit(0)
