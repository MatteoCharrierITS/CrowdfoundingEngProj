"""
regenerate_preview_v2.py
Genera preview.html e viewer HTML avanzati con tutte le funzionalità
"""
from pathlib import Path
import html
import re
import datetime
import json

ROOT = Path(__file__).resolve().parent.parent
MD_DIR = ROOT / 'md'
WEB_DIR = ROOT / 'web'
WEB_DIR.mkdir(exist_ok=True)

# Scansiona ricorsivamente tutti i file .md
md_files = sorted([p for p in MD_DIR.rglob('*.md') if p.is_file()])

# Struttura ad albero per organizzare i file
def build_tree_structure(files, base_dir):
    """Costruisce una struttura ad albero di cartelle e file"""
    tree = {}
    for f in files:
        rel_path = f.relative_to(base_dir)
        parts = rel_path.parts
        current = tree
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]
        if '__files__' not in current:
            current['__files__'] = []
        current['__files__'].append(f)
    return tree

def get_file_stats(file_path):
    """Ottieni statistiche del file"""
    stats = file_path.stat()
    content = file_path.read_text(encoding='utf-8')
    word_count = len(re.findall(r'\b\w+\b', content))
    
    # Parse frontmatter
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
    
    return {
        'modified': stats.st_mtime,
        'size': stats.st_size,
        'word_count': word_count,
        'read_time': max(1, word_count // 200),  # ~200 parole/minuto
        'tags': tags,
        'title': title
    }

def render_tree_html(tree, base_path='', level=0):
    """Renderizza l'albero come HTML con cartelle espandibili"""
    html_parts = []
    indent = '  ' * level
    
    # Prima renderizziamo le cartelle
    folders = sorted([k for k in tree.keys() if k != '__files__'])
    for folder in folders:
        folder_id = f"folder-{hash(base_path + folder) % 100000}"
        html_parts.append(f'{indent}<div class="folder-item">')
        html_parts.append(f'{indent}  <div class="folder-header" onclick="toggleFolder(\'{folder_id}\')">')
        html_parts.append(f'{indent}    <span class="folder-icon">📁</span>')
        html_parts.append(f'{indent}    <span class="folder-name">{html.escape(folder)}</span>')
        html_parts.append(f'{indent}  </div>')
        html_parts.append(f'{indent}  <div class="folder-content" id="{folder_id}">')
        sub_html = render_tree_html(tree[folder], base_path + folder + '/', level + 1)
        html_parts.append(sub_html)
        html_parts.append(f'{indent}  </div>')
        html_parts.append(f'{indent}</div>')
    
    # Poi renderizziamo i file nella cartella corrente
    if '__files__' in tree:
        for f in sorted(tree['__files__'], key=lambda x: x.name):
            rel_path = f.relative_to(MD_DIR)
            viewer_name = str(rel_path.with_suffix('.html')).replace('\\', '/')
            stats = get_file_stats(f)
            
            # Crea attributi data per info aggiuntive
            data_attrs = f'data-words="{stats["word_count"]}" data-readtime="{stats["read_time"]}" data-modified="{stats["modified"]}"'
            
            html_parts.append(f'{indent}<a class="file-item" href="{viewer_name}" {data_attrs}>')
            html_parts.append(f'{indent}  <span class="file-icon">📄</span>')
            html_parts.append(f'{indent}  <span class="file-name">{html.escape(f.name)}</span>')
            html_parts.append(f'{indent}  <span class="file-meta">{stats["word_count"]} parole • {stats["read_time"]} min</span>')
            if stats['tags']:
                tags_html = ' '.join([f'<span class="tag">{html.escape(t)}</span>' for t in stats['tags'][:3]])
                html_parts.append(f'{indent}  <span class="file-tags">{tags_html}</span>')
            html_parts.append(f'{indent}</a>')
    
    return '\n'.join(html_parts)

tree = build_tree_structure(md_files, MD_DIR)

# Genera viewer per ogni file
for md in md_files:
    text = md.read_text(encoding='utf-8')
    text_escaped = text.replace('</script>', r'<\/script>')
    
    rel_path = md.relative_to(MD_DIR)
    viewer_rel_path = rel_path.with_suffix('.html')
    viewer_path = WEB_DIR / viewer_rel_path
    viewer_path.parent.mkdir(parents=True, exist_ok=True)
    
    stats = get_file_stats(md)
    
    # Calcola percorso relativo per tornare alla root
    depth = len(rel_path.parts) - 1
    back_to_root = '../' * depth if depth > 0 else ''
    
    # Breadcrumb
    breadcrumb_parts = ['<a href="' + back_to_root + 'preview.html">Home</a>']
    current_path = ''
    for i, part in enumerate(rel_path.parts[:-1]):
        current_path += part + '/'
        breadcrumb_parts.append(f'<span class="breadcrumb-sep">/</span><span class="breadcrumb-folder">{html.escape(part)}</span>')
    breadcrumb_parts.append(f'<span class="breadcrumb-sep">/</span><span class="breadcrumb-file">{html.escape(md.name)}</span>')
    breadcrumb_html = ''.join(breadcrumb_parts)
    
    modified_date = datetime.datetime.fromtimestamp(stats['modified']).strftime('%d/%m/%Y %H:%M')
    
    viewer_html = f"""<!doctype html>
<html lang="it" data-theme="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📚</text></svg>">
  <title>{html.escape(stats['title'])}</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/atom-one-dark.min.css" id="hljs-theme">
  <style>
    :root[data-theme="dark"]{{--bg:#0b0f12;--panel:#0f1720;--text:#e6eef6;--muted:#98a0ac;--accent:#4cc9f0;--border:rgba(255,255,255,0.07);--hover:rgba(255,255,255,0.05)}}
    :root[data-theme="light"]{{--bg:#f5f7fa;--panel:#ffffff;--text:#1a202c;--muted:#718096;--accent:#0066cc;--border:rgba(0,0,0,0.1);--hover:rgba(0,0,0,0.03)}}
    *{{box-sizing:border-box}}
    body{{background:var(--bg);color:var(--text);font-family:Inter,Segoe UI,Roboto,Arial,sans-serif;margin:0;padding:0;transition:background 0.2s,color 0.2s}}
    .top-bar{{background:var(--panel);border-bottom:1px solid var(--border);padding:12px 24px;position:sticky;top:0;z-index:100;display:flex;align-items:center;justify-content:space-between;gap:12px}}
    .breadcrumb{{font-size:13px;color:var(--muted)}}
    .breadcrumb a{{color:var(--accent);text-decoration:none}}
    .breadcrumb a:hover{{text-decoration:underline}}
    .breadcrumb-sep{{margin:0 6px;opacity:0.5}}
    .breadcrumb-file{{color:var(--text);font-weight:500}}
    .top-actions{{display:flex;gap:8px;align-items:center}}
    .btn{{background:transparent;border:1px solid var(--border);color:var(--text);padding:6px 12px;border-radius:6px;cursor:pointer;font-size:13px;text-decoration:none;display:inline-flex;align-items:center;gap:6px;transition:background 0.15s}}
    .btn:hover{{background:var(--hover)}}
    .theme-toggle{{background:var(--panel);border:1px solid var(--border);border-radius:6px;padding:4px;display:flex;gap:4px}}
    .theme-toggle button{{background:transparent;border:none;padding:4px 8px;border-radius:4px;cursor:pointer;font-size:12px;color:var(--muted);transition:all 0.15s}}
    .theme-toggle button.active{{background:var(--accent);color:white}}
    .wrap{{max-width:1200px;margin:0 auto;padding:24px;display:grid;grid-template-columns:200px 1fr;gap:24px}}
    .sidebar{{position:sticky;top:80px;height:fit-content;max-height:calc(100vh - 120px);overflow-y:auto}}
    .toc{{background:var(--panel);padding:16px;border-radius:12px;border:1px solid var(--border)}}
    .toc h3{{margin:0 0 12px 0;font-size:13px;text-transform:uppercase;letter-spacing:0.5px;color:var(--muted)}}
    .toc ul{{list-style:none;padding:0;margin:0}}
    .toc li{{margin:4px 0}}
    .toc a{{color:var(--text);text-decoration:none;font-size:13px;display:block;padding:4px 8px;border-radius:4px;transition:background 0.15s}}
    .toc a:hover{{background:var(--hover)}}
    .toc li.level-2{{padding-left:12px}}
    .toc li.level-3{{padding-left:24px}}
    .main-content{{min-width:0}}
    .file-meta-box{{background:var(--panel);padding:16px;border-radius:12px;margin-bottom:20px;border:1px solid var(--border);display:flex;flex-wrap:wrap;gap:16px;font-size:13px}}
    .meta-item{{display:flex;align-items:center;gap:6px;color:var(--muted)}}
    .meta-item strong{{color:var(--text)}}
    main{{background:var(--panel);padding:32px;border-radius:12px;border:1px solid var(--border);box-shadow:0 4px 12px rgba(0,0,0,0.1)}}
    main h1,main h2,main h3,main h4,main h5,main h6{{color:var(--text);margin-top:24px;margin-bottom:12px}}
    main h1{{font-size:32px;border-bottom:2px solid var(--border);padding-bottom:12px}}
    main h2{{font-size:24px}}
    main h3{{font-size:20px}}
    main p,main li{{line-height:1.7;color:var(--text)}}
    main ul,main ol{{margin-left:1.5em}}
    main pre{{background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:16px;overflow-x:auto}}
    main code{{background:var(--bg);padding:2px 6px;border-radius:4px;font-size:0.9em;border:1px solid var(--border)}}
    main pre code{{background:transparent;padding:0;border:none}}
    main table{{border-collapse:collapse;width:100%;margin:16px 0}}
    main th,main td{{border:1px solid var(--border);padding:8px 12px;text-align:left}}
    main th{{background:var(--bg);font-weight:600}}
    main blockquote{{border-left:4px solid var(--accent);padding-left:16px;margin:16px 0;color:var(--muted);font-style:italic}}
    main a{{color:var(--accent);text-decoration:none}}
    main a:hover{{text-decoration:underline}}
    main img{{max-width:100%;height:auto;border-radius:8px;margin:16px 0}}
    footer{{text-align:center;color:var(--muted);margin-top:32px;font-size:13px;padding:24px}}
    .tag{{background:var(--accent);color:white;padding:2px 8px;border-radius:12px;font-size:11px;display:inline-block}}
    @media print{{.top-bar,.sidebar,.top-actions{{display:none}}.wrap{{grid-template-columns:1fr}}}}
    @media (max-width:900px){{.wrap{{grid-template-columns:1fr}}.sidebar{{display:none}}}}
  </style>
</head>
<body>
  <div class="top-bar">
    <div class="breadcrumb">{breadcrumb_html}</div>
    <div class="top-actions">
      <div class="theme-toggle">
        <button onclick="setTheme('dark')" data-theme="dark" class="active">🌙</button>
        <button onclick="setTheme('light')" data-theme="light">☀️</button>
      </div>
      <select id="hljs-selector" class="btn" onchange="changeCodeTheme(this.value)">
        <option value="atom-one-dark">Atom One Dark</option>
        <option value="github-dark">GitHub Dark</option>
        <option value="monokai">Monokai</option>
        <option value="nord">Nord</option>
        <option value="dracula">Dracula</option>
      </select>
      <a href="{back_to_root}editor.html?file={str(rel_path).replace(chr(92), '/')}" class="btn">✏️ Modifica</a>
      <button onclick="exportPDF()" class="btn">📄 PDF</button>
      <button onclick="toggleFavorite()" class="btn" id="fav-btn">⭐</button>
    </div>
  </div>

  <div class="wrap">
    <aside class="sidebar">
      <div class="toc">
        <h3>Contenuti</h3>
        <ul id="toc-list"></ul>
      </div>
    </aside>

    <div class="main-content">
      <div class="file-meta-box">
        <div class="meta-item">📅 Modificato: <strong>{modified_date}</strong></div>
        <div class="meta-item">📝 Parole: <strong>{stats['word_count']}</strong></div>
        <div class="meta-item">⏱️ Lettura: <strong>{stats['read_time']} min</strong></div>
        <div class="meta-item">💾 Dimensione: <strong>{stats['size']} bytes</strong></div>
      </div>
      
      <main id="content">Caricamento…</main>
    </div>
  </div>

  <footer>
    File sorgente: <code>{html.escape(str(rel_path))}</code>
  </footer>

  <script id="md-content" type="text/plain">{text_escaped}</script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/5.1.1/marked.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
  <script>
    // Gestione tema
    function setTheme(theme) {{
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem('theme', theme);
      document.querySelectorAll('.theme-toggle button').forEach(b => {{
        b.classList.toggle('active', b.dataset.theme === theme);
      }});
    }}
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);

    // Gestione code theme
    function changeCodeTheme(theme) {{
      const link = document.getElementById('hljs-theme');
      link.href = `https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/${{theme}}.min.css`;
      localStorage.setItem('codeTheme', theme);
    }}
    const savedCodeTheme = localStorage.getItem('codeTheme') || 'atom-one-dark';
    document.getElementById('hljs-selector').value = savedCodeTheme;
    changeCodeTheme(savedCodeTheme);

    // Render markdown
    const md = document.getElementById('md-content').textContent;
    const content = document.getElementById('content');
    marked.setOptions({{ headerIds: true, mangle: false }});
    content.innerHTML = marked.parse(md);
    document.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el));

    // Genera TOC
    const headers = content.querySelectorAll('h1, h2, h3');
    const tocList = document.getElementById('toc-list');
    headers.forEach(h => {{
      const li = document.createElement('li');
      li.className = 'level-' + h.tagName.substring(1);
      const a = document.createElement('a');
      a.textContent = h.textContent;
      a.href = '#' + h.id;
      a.onclick = (e) => {{
        e.preventDefault();
        h.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      }};
      li.appendChild(a);
      tocList.appendChild(li);
    }});

    // Favoriti
    function toggleFavorite() {{
      const path = '{str(rel_path).replace(chr(92), '/')}';
      let favs = JSON.parse(localStorage.getItem('favorites') || '[]');
      const index = favs.indexOf(path);
      if (index > -1) {{
        favs.splice(index, 1);
        document.getElementById('fav-btn').textContent = '⭐';
      }} else {{
        favs.push(path);
        document.getElementById('fav-btn').textContent = '⭐✨';
      }}
      localStorage.setItem('favorites', JSON.stringify(favs));
    }}
    const path = '{str(rel_path).replace(chr(92), '/')}';
    const favs = JSON.parse(localStorage.getItem('favorites') || '[]');
    if (favs.includes(path)) {{
      document.getElementById('fav-btn').textContent = '⭐✨';
    }}

    // Export PDF
    function exportPDF() {{
      window.print();
    }}

    // Recent files
    let recent = JSON.parse(localStorage.getItem('recentFiles') || '[]');
    recent = recent.filter(r => r !== path);
    recent.unshift(path);
    recent = recent.slice(0, 20);
    localStorage.setItem('recentFiles', JSON.stringify(recent));

    // Auto-reload
    let lastCheck = Date.now();
    setInterval(() => {{
      fetch(location.href, {{method: 'HEAD', cache: 'no-cache'}})
        .then(res => {{
          const lastMod = res.headers.get('last-modified');
          if (lastMod && new Date(lastMod).getTime() > lastCheck) {{
            if (Notification.permission === 'granted') {{
              new Notification('File aggiornato', {{body: '{html.escape(md.name)}'}});
            }}
            location.reload();
          }}
        }}).catch(() => {{}});
    }}, 2000);

    // Chiedi permesso notifiche
    if (Notification.permission === 'default') {{
      Notification.requestPermission();
    }}
  </script>
</body>
</html>"""

    viewer_path.write_text(viewer_html, encoding='utf-8')
    print(f'Generato viewer: {viewer_rel_path}')

# Genera preview.html avanzato
if md_files:
    links_html = render_tree_html(tree)
else:
    links_html = '<div class="empty">Nessun file .md trovato</div>'

# Colleziona tutti i tag
all_tags = {}
for md in md_files:
    stats = get_file_stats(md)
    for tag in stats['tags']:
        all_tags[tag] = all_tags.get(tag, 0) + 1

tags_cloud = ' '.join([f'<span class="tag-cloud-item" data-count="{count}">{html.escape(tag)}</span>' 
                        for tag, count in sorted(all_tags.items(), key=lambda x: x[1], reverse=True)[:20]])

preview_html = f"""<!doctype html>
<html lang="it" data-theme="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📚</text></svg>">
  <title>Documenti Markdown - AppuntiApp</title>
  <style>
    :root[data-theme="dark"]{{--bg:#0b0f12;--panel:#0f1720;--text:#e6eef6;--muted:#98a0ac;--accent:#4cc9f0;--border:rgba(255,255,255,0.07);--hover:rgba(255,255,255,0.05)}}
    :root[data-theme="light"]{{--bg:#f5f7fa;--panel:#ffffff;--text:#1a202c;--muted:#718096;--accent:#0066cc;--border:rgba(0,0,0,0.1);--hover:rgba(0,0,0,0.03)}}
    *{{box-sizing:border-box}}
    body{{background:var(--bg);color:var(--text);font-family:Inter,Segoe UI,Roboto,Arial,sans-serif;margin:0;padding:28px;transition:background 0.2s,color 0.2s}}
    .wrap{{max-width:1200px;margin:0 auto}}
    header{{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}}
    h1{{font-size:28px;margin:0}}
    .meta{{color:var(--muted);font-size:13px}}
    .header-actions{{display:flex;gap:8px;align-items:center}}
    .btn{{background:transparent;border:1px solid var(--border);color:var(--text);padding:8px 14px;border-radius:8px;cursor:pointer;font-size:13px;text-decoration:none;transition:background 0.15s}}
    .btn:hover{{background:var(--hover)}}
    .theme-toggle{{background:var(--panel);border:1px solid var(--border);border-radius:6px;padding:4px;display:flex;gap:4px}}
    .theme-toggle button{{background:transparent;border:none;padding:4px 8px;border-radius:4px;cursor:pointer;font-size:12px;color:var(--muted);transition:all 0.15s}}
    .theme-toggle button.active{{background:var(--accent);color:white}}
    .search-box{{margin-top:20px;background:var(--panel);padding:16px;border-radius:12px;border:1px solid var(--border)}}
    .search-input{{width:100%;padding:12px;background:var(--bg);border:1px solid var(--border);border-radius:8px;color:var(--text);font-size:14px}}
    .search-input:focus{{outline:none;border-color:var(--accent)}}
    .filters{{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap}}
    .filter-btn{{padding:6px 12px;background:var(--bg);border:1px solid var(--border);border-radius:6px;cursor:pointer;font-size:12px;color:var(--text);transition:all 0.15s}}
    .filter-btn:hover{{background:var(--hover)}}
    .filter-btn.active{{background:var(--accent);color:white;border-color:var(--accent)}}
    .tags-cloud{{margin-top:12px;display:flex;flex-wrap:wrap;gap:8px}}
    .tag-cloud-item{{padding:4px 10px;background:var(--panel);border:1px solid var(--border);border-radius:12px;font-size:11px;cursor:pointer;transition:all 0.15s}}
    .tag-cloud-item:hover{{background:var(--accent);color:white}}
    main{{margin-top:20px;display:grid;grid-template-columns:340px 1fr;gap:20px}}
    .panel{{background:var(--panel);padding:20px;border-radius:12px;border:1px solid var(--border)}}
    .list{{overflow-y:auto;max-height:calc(100vh - 300px)}}
    .list h3{{margin:0 0 16px 0;color:var(--accent);font-size:16px}}
    .folder-item{{margin-bottom:4px}}
    .folder-header{{display:flex;align-items:center;gap:8px;padding:8px 10px;cursor:pointer;border-radius:8px;transition:background 0.15s;font-weight:500}}
    .folder-header:hover{{background:var(--hover)}}
    .folder-icon{{font-size:16px}}
    .folder-name{{font-size:14px}}
    .folder-content{{margin-left:20px;display:none;margin-top:6px}}
    .folder-content.open{{display:block}}
    .file-item{{display:flex;flex-direction:column;gap:4px;color:var(--text);text-decoration:none;padding:10px;border-radius:8px;margin-bottom:4px;border:1px solid var(--border);transition:all 0.15s;position:relative}}
    .file-item:hover{{background:var(--hover);border-color:var(--accent);transform:translateX(4px)}}
    .file-item-header{{display:flex;align-items:center;gap:8px}}
    .file-icon{{font-size:16px}}
    .file-name{{font-size:13px;font-weight:500;flex:1}}
    .file-meta{{font-size:11px;color:var(--muted);margin-top:2px}}
    .file-tags{{display:flex;gap:4px;margin-top:6px;flex-wrap:wrap}}
    .tag{{background:var(--accent);color:white;padding:2px 8px;border-radius:10px;font-size:10px}}
    .side-panel h3{{margin:0 0 16px 0;color:var(--accent);font-size:16px}}
    .tabs{{display:flex;gap:4px;margin-bottom:16px;border-bottom:1px solid var(--border)}}
    .tab{{padding:10px 16px;cursor:pointer;border-bottom:2px solid transparent;transition:all 0.15s;font-size:13px}}
    .tab:hover{{color:var(--accent)}}
    .tab.active{{border-bottom-color:var(--accent);color:var(--accent);font-weight:500}}
    .tab-content{{display:none}}
    .tab-content.active{{display:block}}
    .recent-item,.fav-item{{display:flex;align-items:center;gap:8px;padding:8px;border-radius:6px;margin-bottom:4px;border:1px solid var(--border);font-size:13px;color:var(--text);text-decoration:none;transition:background 0.15s}}
    .recent-item:hover,.fav-item:hover{{background:var(--hover)}}
    .stats-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:16px}}
    .stat-box{{background:var(--bg);padding:12px;border-radius:8px;border:1px solid var(--border)}}
    .stat-label{{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:0.5px}}
    .stat-value{{font-size:20px;font-weight:600;color:var(--text);margin-top:4px}}
    footer{{text-align:center;color:var(--muted);margin-top:32px;font-size:13px}}
    .empty{{color:var(--muted);font-size:14px;text-align:center;padding:40px}}
    .no-results{{display:none;text-align:center;padding:40px;color:var(--muted)}}
    @media (max-width:900px){{main{{grid-template-columns:1fr}}.side-panel{{order:-1}}}}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <div>
        <h1>📚 AppuntiApp</h1>
        <div class="meta">{len(md_files)} documenti • {html.escape(ROOT.name)}</div>
      </div>
      <div class="header-actions">
        <div class="theme-toggle">
          <button onclick="setTheme('dark')" data-theme="dark" class="active">🌙</button>
          <button onclick="setTheme('light')" data-theme="light">☀️</button>
        </div>
        <a href="folders.html" class="btn">📁 Cartelle</a>
        <a href="stats.html" class="btn">📊 Statistiche</a>
        <a href="logs.html" class="btn">📋 Log Server</a>
        <a href="editor.html" class="btn">✨ Nuovo File</a>
      </div>
    </header>

    <div class="search-box">
      <input type="text" class="search-input" id="search-input" placeholder="🔍 Cerca nei documenti... (premi / per focus)">
      <div class="filters">
        <button class="filter-btn active" onclick="sortBy('name')">📝 Nome</button>
        <button class="filter-btn" onclick="sortBy('date')">📅 Data</button>
        <button class="filter-btn" onclick="sortBy('words')">📊 Parole</button>
        <button class="filter-btn" onclick="showAll()">🗂️ Tutti</button>
      </div>
      <div class="tags-cloud">{tags_cloud if tags_cloud else ''}</div>
    </div>

    <main>
      <aside class="panel list" id="file-list">
        <h3>📂 Documenti</h3>
{links_html}
      </aside>

      <section class="panel side-panel">
        <div class="tabs">
          <div class="tab active" onclick="switchTab('recent')">🕒 Recenti</div>
          <div class="tab" onclick="switchTab('favorites')">⭐ Preferiti</div>
          <div class="tab" onclick="switchTab('stats')">📊 Info</div>
        </div>

        <div class="tab-content active" id="recent-tab">
          <div id="recent-list"></div>
        </div>

        <div class="tab-content" id="favorites-tab">
          <div id="fav-list"></div>
        </div>

        <div class="tab-content" id="stats-tab">
          <div class="stats-grid">
            <div class="stat-box">
              <div class="stat-label">File totali</div>
              <div class="stat-value">{len(md_files)}</div>
            </div>
            <div class="stat-box">
              <div class="stat-label">Cartelle</div>
              <div class="stat-value" id="folder-count">-</div>
            </div>
          </div>
          <a href="stats.html" class="btn" style="display:block;text-align:center">Vedi tutte le statistiche →</a>
        </div>
      </section>
    </main>

    <div class="no-results" id="no-results">
      <p>Nessun risultato trovato</p>
    </div>

    <footer>
      Generato automaticamente • <span id="live-indicator">🔴 Offline</span>
    </footer>
  </div>

  <script>
    // Gestione tema
    function setTheme(theme) {{
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem('theme', theme);
      document.querySelectorAll('.theme-toggle button').forEach(b => {{
        b.classList.toggle('active', b.dataset.theme === theme);
      }});
    }}
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);

    // Keyboard shortcuts
    document.addEventListener('keydown', e => {{
      if (e.key === '/' && e.target.tagName !== 'INPUT') {{
        e.preventDefault();
        document.getElementById('search-input').focus();
      }}
      if (e.key === 'Escape') {{
        document.getElementById('search-input').blur();
        document.getElementById('search-input').value = '';
        filterFiles('');
      }}
      if (e.key === 'n' && e.ctrlKey) {{
        e.preventDefault();
        window.location.href = 'editor.html';
      }}
    }});

    // Ricerca
    const searchInput = document.getElementById('search-input');
    let searchTimeout;
    searchInput.addEventListener('input', e => {{
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => filterFiles(e.target.value), 300);
    }});

    function filterFiles(query) {{
      query = query.toLowerCase();
      const items = document.querySelectorAll('.file-item');
      let visibleCount = 0;
      
      items.forEach(item => {{
        const text = item.textContent.toLowerCase();
        const match = text.includes(query);
        item.style.display = match ? '' : 'none';
        if (match) visibleCount++;
      }});

      document.getElementById('no-results').style.display = visibleCount === 0 ? 'block' : 'none';
      document.getElementById('file-list').style.display = visibleCount === 0 ? 'none' : 'block';
    }}

    // Tag cloud
    document.querySelectorAll('.tag-cloud-item').forEach(tag => {{
      tag.addEventListener('click', () => {{
        searchInput.value = tag.textContent;
        filterFiles(tag.textContent);
      }});
    }});

    // Folders toggle
    function toggleFolder(id) {{
      const folder = document.getElementById(id);
      if (folder) folder.classList.toggle('open');
    }}

    // Espandi tutte le cartelle all'avvio
    document.querySelectorAll('.folder-content').forEach(f => f.classList.add('open'));

    // Ordinamento
    function sortBy(type) {{
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      event.target.classList.add('active');
      
      const items = Array.from(document.querySelectorAll('.file-item'));
      items.sort((a, b) => {{
        if (type === 'name') return a.querySelector('.file-name').textContent.localeCompare(b.querySelector('.file-name').textContent);
        if (type === 'date') return parseFloat(b.dataset.modified) - parseFloat(a.dataset.modified);
        if (type === 'words') return parseInt(b.dataset.words) - parseInt(a.dataset.words);
        return 0;
      }});
      
      // Riattacca al DOM (semplificato - in produzione serve logica più complessa per cartelle)
      // Per ora lasciamo l'ordinamento base
    }}

    function showAll() {{
      searchInput.value = '';
      filterFiles('');
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      event.target.classList.add('active');
    }}

    // Tabs
    function switchTab(tab) {{
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
      event.target.classList.add('active');
      document.getElementById(tab + '-tab').classList.add('active');
    }}

    // Recenti e Preferiti
    function loadRecents() {{
      const recent = JSON.parse(localStorage.getItem('recentFiles') || '[]');
      const container = document.getElementById('recent-list');
      if (recent.length === 0) {{
        container.innerHTML = '<div class="empty">Nessun file recente</div>';
        return;
      }}
      container.innerHTML = recent.slice(0, 10).map(path => 
        `<a href="${{path.replace(/\\.md$/, '.html')}}" class="recent-item">
          <span>📄</span>
          <span>${{path.split('/').pop()}}</span>
        </a>`
      ).join('');
    }}

    function loadFavorites() {{
      const favs = JSON.parse(localStorage.getItem('favorites') || '[]');
      const container = document.getElementById('fav-list');
      if (favs.length === 0) {{
        container.innerHTML = '<div class="empty">Nessun preferito</div>';
        return;
      }}
      container.innerHTML = favs.map(path => 
        `<a href="${{path.replace(/\\.md$/, '.html')}}" class="fav-item">
          <span>⭐</span>
          <span>${{path.split('/').pop()}}</span>
        </a>`
      ).join('');
    }}

    loadRecents();
    loadFavorites();

    // Conta cartelle
    const folderCount = document.querySelectorAll('.folder-item').length;
    document.getElementById('folder-count').textContent = folderCount;

    // Check server live
    fetch('/api/files')
      .then(() => {{
        document.getElementById('live-indicator').innerHTML = '🟢 Live';
      }})
      .catch(() => {{}});
  </script>
</body>
</html>"""

preview_path = WEB_DIR / 'preview.html'
preview_path.write_text(preview_html, encoding='utf-8')
print('Generato indice avanzato: preview.html')
print('Operazione completata.')
