from flask import Flask, jsonify, request, send_from_directory, abort
from pathlib import Path
from flask_cors import CORS
import os
import datetime
import subprocess
import sys
import json
import re
import shutil

ROOT = Path(__file__).resolve().parent.parent
MD_DIR = ROOT / 'md'
WEB_DIR = ROOT / 'web'
LOG_DIR = ROOT / 'logs'
MD_DIR.mkdir(exist_ok=True)
WEB_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path='')
CORS(app)

# Cache per file stats
FILE_CACHE = {}

# Logging personalizzato
import logging
from logging.handlers import RotatingFileHandler

API_LOG_FILE = LOG_DIR / 'api_server.log'

# Configura logger
api_logger = logging.getLogger('api_server')
api_logger.setLevel(logging.INFO)
api_logger.handlers.clear()  # Rimuovi handler esistenti

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(message)s'))
api_logger.addHandler(console_handler)

# File handler
file_handler = RotatingFileHandler(str(API_LOG_FILE), maxBytes=1024*1024, backupCount=3, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
api_logger.addHandler(file_handler)

def build_file_tree(base_path):
    """Costruisce una struttura ad albero di cartelle e file"""
    tree = {'type': 'folder', 'name': base_path.name, 'children': []}
    
    def add_to_tree(node, path_parts, file_obj):
        if not path_parts:
            return
        
        part = path_parts[0]
        remaining = path_parts[1:]
        
        if remaining:  # È una cartella
            # Cerca se la cartella esiste già
            folder_node = None
            for child in node['children']:
                if child['type'] == 'folder' and child['name'] == part:
                    folder_node = child
                    break
            
            if not folder_node:
                folder_node = {'type': 'folder', 'name': part, 'children': []}
                node['children'].append(folder_node)
            
            add_to_tree(folder_node, remaining, file_obj)
        else:  # È un file
            node['children'].append({
                'type': 'file',
                'name': part,
                'path': str(file_obj.relative_to(MD_DIR)).replace('\\', '/')
            })
    
    # Trova tutti i file .md ricorsivamente
    md_files = sorted([f for f in base_path.rglob('*.md') if f.is_file()])
    
    for md_file in md_files:
        rel_path = md_file.relative_to(base_path)
        add_to_tree(tree, rel_path.parts, md_file)
    
    # Ordina ricorsivamente
    def sort_tree(node):
        if node['type'] == 'folder' and 'children' in node:
            node['children'].sort(key=lambda x: (x['type'] == 'file', x['name']))
            for child in node['children']:
                sort_tree(child)
    
    sort_tree(tree)
    return tree

@app.route('/api/files')
def list_files():
    api_logger.info('Richiesta lista file')
    tree = build_file_tree(MD_DIR)
    return jsonify(tree)

@app.route('/api/create', methods=['POST'])
def create_file():
    data = request.get_json() or {}
    name = data.get('name')
    folder = data.get('folder', '')  # Supporto per sottocartelle
    content = data.get('content', '')
    if not name:
        ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        name = f'nuovo-{ts}.md'
    
    # Sanitize name per sicurezza
    name = os.path.basename(name)
    if not name.lower().endswith('.md'):
        name = name + '.md'
    
    # Gestisci sottocartelle
    if folder:
        # Rimuovi caratteri pericolosi dal path della cartella
        folder = folder.replace('..', '').strip('/\\')
        dest = MD_DIR / folder / name
    else:
        dest = MD_DIR / name
    
    if dest.exists():
        api_logger.warning(f'Tentativo di creare file già esistente: {name}')
        return jsonify({'error': 'exists', 'name': name}), 409
    
    # Crea le sottocartelle se necessario
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        dest.write_text(content or f'# {name}\n\n', encoding='utf-8')
        api_logger.info(f'✓ File creato: {name} (cartella: {folder or "root"})')
        # Try to run the generator script to create the viewer immediately
        gen = Path(__file__).resolve().parent / 'regenerate_preview.py'
        result = None
        if gen.is_file():
            try:
                cmd = [sys.executable, str(gen)]
                proc = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                result = {'returncode': proc.returncode, 'stdout': proc.stdout, 'stderr': proc.stderr}
            except Exception as e:
                result = {'error': 'generator_failed', 'msg': str(e)}
        return jsonify({'ok': True, 'name': name, 'generator': result}), 201
    except Exception as e:
        return jsonify({'error': 'write_failed', 'msg': str(e)}), 500

@app.route('/<path:path>')
def static_proxy(path):
    # serve static files from web/ (supporta sottocartelle)
    try:
        return send_from_directory(str(WEB_DIR), path)
    except Exception:
        abort(404)

@app.route('/')
def index():
    return send_from_directory(str(WEB_DIR), 'preview.html')

@app.route('/api/file/<path:filepath>', methods=['GET'])
def get_file_content(filepath):
    """Ottieni il contenuto di un file specifico"""
    api_logger.info(f'Richiesta lettura file: {filepath}')
    try:
        file_path = MD_DIR / filepath
        if not file_path.exists() or not file_path.is_file():
            api_logger.warning(f'File non trovato: {filepath}')
            return jsonify({'error': 'file_not_found'}), 404
        
        content = file_path.read_text(encoding='utf-8')
        stats = file_path.stat()
        
        # Parse frontmatter YAML se presente
        tags = []
        title = file_path.stem
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if frontmatter_match:
            fm = frontmatter_match.group(1)
            tags_match = re.search(r'tags:\s*\[(.*?)\]', fm)
            if tags_match:
                tags = [t.strip().strip('"\'') for t in tags_match.group(1).split(',')]
            title_match = re.search(r'title:\s*(.+)', fm)
            if title_match:
                title = title_match.group(1).strip().strip('"\'')
        
        # Conta parole
        word_count = len(re.findall(r'\b\w+\b', content))
        
        return jsonify({
            'content': content,
            'name': file_path.name,
            'path': filepath,
            'size': stats.st_size,
            'modified': stats.st_mtime,
            'created': stats.st_ctime,
            'word_count': word_count,
            'tags': tags,
            'title': title
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/file/<path:filepath>', methods=['PUT'])
def update_file(filepath):
    """Aggiorna il contenuto di un file"""
    try:
        data = request.get_json() or {}
        content = data.get('content', '')
        
        file_path = MD_DIR / filepath
        if not file_path.exists():
            api_logger.warning(f'Tentativo di aggiornare file inesistente: {filepath}')
            return jsonify({'error': 'file_not_found'}), 404
        
        file_path.write_text(content, encoding='utf-8')
        api_logger.info(f'✓ File aggiornato: {filepath}')
        
        # Rigenera HTML
        gen = Path(__file__).resolve().parent / 'regenerate_preview.py'
        if gen.is_file():
            subprocess.run([sys.executable, str(gen)], check=False)
        
        return jsonify({'ok': True, 'path': filepath})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/file/<path:filepath>', methods=['DELETE'])
def delete_file(filepath):
    """Elimina un file"""
    api_logger.info(f'Richiesta eliminazione file: {filepath}')
    try:
        file_path = MD_DIR / filepath
        if not file_path.exists():
            api_logger.warning(f'File da eliminare non trovato: {filepath}')
            return jsonify({'error': 'file_not_found'}), 404
        
        file_path.unlink()
        api_logger.info(f'✓ File eliminato: {filepath}')
        
        # Elimina anche l'HTML corrispondente
        html_path = WEB_DIR / Path(filepath).with_suffix('.html')
        if html_path.exists():
            html_path.unlink()
        
        # Rigenera preview
        gen = Path(__file__).resolve().parent / 'regenerate_preview.py'
        if gen.is_file():
            subprocess.run([sys.executable, str(gen)], check=False)
        
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/file/<path:filepath>/rename', methods=['POST'])
def rename_file(filepath):
    """Rinomina un file"""
    try:
        data = request.get_json() or {}
        new_name = data.get('new_name', '')
        
        if not new_name:
            return jsonify({'error': 'new_name required'}), 400
        
        file_path = MD_DIR / filepath
        if not file_path.exists():
            return jsonify({'error': 'file_not_found'}), 404
        
        # Sanitize
        new_name = os.path.basename(new_name)
        if not new_name.lower().endswith('.md'):
            new_name += '.md'
        
        new_path = file_path.parent / new_name
        if new_path.exists():
            return jsonify({'error': 'name_exists'}), 409
        
        file_path.rename(new_path)
        
        # Rigenera tutto
        gen = Path(__file__).resolve().parent / 'regenerate_preview.py'
        if gen.is_file():
            subprocess.run([sys.executable, str(gen)], check=False)
        
        return jsonify({'ok': True, 'new_path': str(new_path.relative_to(MD_DIR))})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/file/<path:filepath>/move', methods=['POST'])
def move_file(filepath):
    """Sposta un file in un'altra cartella"""
    try:
        data = request.get_json() or {}
        destination = data.get('destination', '')
        
        file_path = MD_DIR / filepath
        if not file_path.exists():
            return jsonify({'error': 'file_not_found'}), 404
        
        # Determina percorso destinazione
        if destination:
            destination = destination.replace('..', '').strip('/\\')
            dest_folder = MD_DIR / destination
            if not dest_folder.exists() or not dest_folder.is_dir():
                return jsonify({'error': 'destination_not_found'}), 404
        else:
            dest_folder = MD_DIR
        
        # Nuovo percorso
        new_path = dest_folder / file_path.name
        if new_path.exists():
            return jsonify({'error': 'file_exists_in_destination'}), 409
        
        # Sposta file
        shutil.move(str(file_path), str(new_path))
        
        # Elimina vecchio HTML
        old_html = WEB_DIR / Path(filepath).with_suffix('.html')
        if old_html.exists():
            old_html.unlink()
        
        # Rigenera tutto
        gen = Path(__file__).resolve().parent / 'regenerate_preview.py'
        if gen.is_file():
            subprocess.run([sys.executable, str(gen)], check=False)
        
        return jsonify({'ok': True, 'new_path': str(new_path.relative_to(MD_DIR))})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/folder', methods=['POST'])
def create_folder():
    """Crea una nuova cartella"""
    try:
        data = request.get_json() or {}
        folder_path = data.get('path', '')
        
        if not folder_path:
            return jsonify({'error': 'path required'}), 400
        
        # Sanitize
        folder_path = folder_path.replace('..', '').strip('/\\')
        full_path = MD_DIR / folder_path
        
        if full_path.exists():
            return jsonify({'error': 'folder_exists'}), 409
        
        full_path.mkdir(parents=True, exist_ok=True)
        
        return jsonify({'ok': True, 'path': folder_path})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/folder/<path:folderpath>', methods=['DELETE'])
def delete_folder(folderpath):
    """Elimina una cartella e il suo contenuto"""
    try:
        folder_path = MD_DIR / folderpath
        
        if not folder_path.exists() or not folder_path.is_dir():
            return jsonify({'error': 'folder_not_found'}), 404
        
        shutil.rmtree(folder_path)
        
        # Elimina anche la cartella HTML corrispondente
        html_folder = WEB_DIR / folderpath
        if html_folder.exists():
            shutil.rmtree(html_folder)
        
        # Rigenera preview
        gen = Path(__file__).resolve().parent / 'regenerate_preview.py'
        if gen.is_file():
            subprocess.run([sys.executable, str(gen)], check=False)
        
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/folder/<path:folderpath>/rename', methods=['POST'])
def rename_folder(folderpath):
    """Rinomina una cartella"""
    try:
        data = request.get_json() or {}
        new_name = data.get('new_name', '')
        
        if not new_name:
            return jsonify({'error': 'new_name required'}), 400
        
        folder_path = MD_DIR / folderpath
        if not folder_path.exists() or not folder_path.is_dir():
            return jsonify({'error': 'folder_not_found'}), 404
        
        # Sanitize
        new_name = os.path.basename(new_name.replace('..', '').strip('/\\'))
        new_path = folder_path.parent / new_name
        
        if new_path.exists():
            return jsonify({'error': 'name_exists'}), 409
        
        folder_path.rename(new_path)
        
        # Rigenera tutto
        gen = Path(__file__).resolve().parent / 'regenerate_preview.py'
        if gen.is_file():
            subprocess.run([sys.executable, str(gen)], check=False)
        
        return jsonify({'ok': True, 'new_path': str(new_path.relative_to(MD_DIR))})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search_files():
    """Cerca nei file"""
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify({'results': []})
    
    api_logger.info(f'Ricerca: "{query}"')
    
    results = []
    for md_file in MD_DIR.rglob('*.md'):
        try:
            content = md_file.read_text(encoding='utf-8')
            if query in content.lower() or query in md_file.name.lower():
                # Trova contesto
                lines = content.split('\n')
                matches = []
                for i, line in enumerate(lines):
                    if query in line.lower():
                        start = max(0, i - 1)
                        end = min(len(lines), i + 2)
                        context = '\n'.join(lines[start:end])
                        matches.append({
                            'line': i + 1,
                            'context': context[:200]
                        })
                        if len(matches) >= 3:
                            break
                
                results.append({
                    'path': str(md_file.relative_to(MD_DIR)).replace('\\', '/'),
                    'name': md_file.name,
                    'matches': matches
                })
        except:
            pass
    
    return jsonify({'results': results})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Ottieni statistiche globali"""
    try:
        all_files = list(MD_DIR.rglob('*.md'))
        total_files = len(all_files)
        total_words = 0
        total_size = 0
        tags_counter = {}
        recent_files = []
        
        for f in all_files:
            try:
                stats = f.stat()
                content = f.read_text(encoding='utf-8')
                word_count = len(re.findall(r'\b\w+\b', content))
                total_words += word_count
                total_size += stats.st_size
                
                # Parse tags
                frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                if frontmatter_match:
                    fm = frontmatter_match.group(1)
                    tags_match = re.search(r'tags:\s*\[(.*?)\]', fm)
                    if tags_match:
                        tags = [t.strip().strip('"\'') for t in tags_match.group(1).split(',')]
                        for tag in tags:
                            tags_counter[tag] = tags_counter.get(tag, 0) + 1
                
                recent_files.append({
                    'path': str(f.relative_to(MD_DIR)).replace('\\', '/'),
                    'name': f.name,
                    'modified': stats.st_mtime,
                    'word_count': word_count
                })
            except:
                pass
        
        # Ordina per data modifica
        recent_files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'total_files': total_files,
            'total_words': total_words,
            'total_size': total_size,
            'tags': tags_counter,
            'recent_files': recent_files[:10]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/templates', methods=['GET'])
def get_templates():
    """Ottieni lista template disponibili"""
    templates = {
        'blank': {'name': 'Vuoto', 'content': '# Nuovo documento\n\n'},
        'note': {
            'name': 'Nota',
            'content': '---\ntags: []\n---\n\n# {title}\n\n## Note\n\n'
        },
        'lecture': {
            'name': 'Lezione',
            'content': '---\ntags: [lezione]\ndata: {date}\n---\n\n# {title}\n\n## Argomenti\n\n## Note\n\n## Riferimenti\n\n'
        },
        'todo': {
            'name': 'TODO List',
            'content': '---\ntags: [todo]\n---\n\n# TODO: {title}\n\n- [ ] Task 1\n- [ ] Task 2\n- [ ] Task 3\n\n'
        }
    }
    return jsonify(templates)

@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    """Upload di un'immagine"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'no_file'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'empty_filename'}), 400
        
        # Crea cartella images se non esiste
        images_dir = ROOT / 'images'
        images_dir.mkdir(exist_ok=True)
        
        # Salva con nome sicuro
        filename = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-') + file.filename
        filepath = images_dir / filename
        file.save(filepath)
        
        return jsonify({
            'ok': True,
            'url': f'/images/{filename}',
            'filename': filename
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve immagini"""
    images_dir = ROOT / 'images'
    return send_from_directory(str(images_dir), filename)

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Ottieni i log dei server"""
    try:
        logs_data = {'api': [], 'watcher': []}
        
        # Leggi log API server
        if API_LOG_FILE.exists():
            with open(API_LOG_FILE, 'r', encoding='utf-8') as f:
                for line in f.readlines()[-100:]:  # Ultimi 100 messaggi
                    if line.strip():
                        parts = line.strip().split(' - ', 2)
                        if len(parts) >= 3:
                            logs_data['api'].append({
                                'timestamp': parts[0],
                                'level': parts[1],
                                'message': parts[2]
                            })
        
        # Leggi log Watcher
        watcher_log = LOG_DIR / 'watcher.log'
        if watcher_log.exists():
            with open(watcher_log, 'r', encoding='utf-8') as f:
                for line in f.readlines()[-100:]:
                    if line.strip():
                        parts = line.strip().split(' - ', 2)
                        if len(parts) >= 3:
                            logs_data['watcher'].append({
                                'timestamp': parts[0],
                                'level': parts[1],
                                'message': parts[2]
                            })
        
        return jsonify(logs_data)
    except Exception as e:
        return jsonify({'error': str(e), 'api': [], 'watcher': []}), 500

@app.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    """Pulisci tutti i log"""
    try:
        # Chiudi e riapri i file handler per svuotare i file
        for handler in api_logger.handlers:
            if isinstance(handler, RotatingFileHandler):
                handler.close()
                api_logger.removeHandler(handler)
        
        # Svuota i file di log
        if API_LOG_FILE.exists():
            API_LOG_FILE.write_text('', encoding='utf-8')
        
        watcher_log = LOG_DIR / 'watcher.log'
        if watcher_log.exists():
            watcher_log.write_text('', encoding='utf-8')
        
        # Ricrea il file handler per API
        new_handler = RotatingFileHandler(str(API_LOG_FILE), maxBytes=1024*1024, backupCount=3, encoding='utf-8')
        new_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        api_logger.addHandler(new_handler)
        
        api_logger.info('Log cancellati')
        
        return jsonify({'ok': True})
    except Exception as e:
        api_logger.error(f'Errore pulizia log: {str(e)}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Salva PID per permettere terminazione pulita
    import os
    pid_file = ROOT / 'api_server.pid'
    pid_file.write_text(str(os.getpid()))
    
    api_logger.info('=== API Server avviato su http://localhost:5000 ===')
    print(f'Serving web/ and API on http://localhost:5000')
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        api_logger.info('Server Flask terminato')
        # Rimuovi file PID alla chiusura
        if pid_file.exists():
            pid_file.unlink()
