# 🚀 AppuntiApp - Quick Start Guide

## 📦 Installazione

### 1. Requisiti
- Python 3.7+
- Browser moderno (Chrome, Firefox, Edge)

### 2. Installa Dipendenze
```bash
cd AppuntiApp
python scripts/install_dependencies.py
```

Oppure manualmente:
```bash
pip install flask flask-cors watchdog
```

## 🎯 Avvio Rapido

### Metodo 1: Script Automatico (Windows)
Doppio click su `avvia.bat`

### Metodo 2: Manuale

#### Terminale 1 - Server API
```bash
python scripts/api_server.py
```

#### Terminale 2 - Auto-Watcher (opzionale ma consigliato)
```bash
python scripts/auto_regen_watcher.py
```

#### Terminale 3 - Solo generazione HTML (alternativa senza server)
```bash
python scripts/regenerate_preview.py
```

### 3. Apri Browser
Naviga su: `http://localhost:5000`

## 🎨 Funzionalità Chiave

### 📚 Home Page (`preview.html`)
- **Ricerca full-text**: Premi `/` per cercare
- **Tag cloud**: Click su tag per filtrare
- **Ordinamento**: Nome, data, parole
- **Recent files**: Ultimi 20 file aperti
- **Preferiti**: Sistema stelline

### ✏️ Editor (`editor.html`)
- **Split view**: Markdown + Preview live
- **Shortcuts**:
  - `Ctrl+S` - Salva
  - `Ctrl+B` - Grassetto
  - `Ctrl+I` - Corsivo
- **Template**: 4 template predefiniti
- **Upload**: Drag & drop immagini

### 📊 Statistiche (`stats.html`)
- 4 grafici interattivi
- Top 10 file per parole
- Distribuzione tag
- Attività ultimi 7 giorni
- File per cartella

### 📁 Gestione Cartelle (`folders.html`)
- Crea/rinomina/elimina cartelle
- Vista ad albero
- Link rapidi a file

### 👁️ Viewer (file HTML individuali)
- **TOC automatico**: Sidebar con indice
- **Breadcrumb**: Navigazione gerarchica
- **Info file**: Parole, tempo lettura, dimensione
- **Temi codice**: 5 temi syntax highlighting
- **Export PDF**: Stampa ottimizzata
- **Preferiti**: Segna con stellina
- **Auto-reload**: Aggiornamento automatico ogni 2s

## 🎯 Workflow Consigliato

```
1. Avvia server + watcher
   ↓
2. Apri http://localhost:5000
   ↓
3. Organizza file in cartelle (📁 Cartelle)
   ↓
4. Scrivi/modifica in VS Code o Editor integrato
   ↓
5. Il watcher rileva modifiche e rigenera automaticamente
   ↓
6. Browser ricarica la pagina (auto-reload)
   ↓
7. Consulta statistiche periodicamente
```

## 📂 Organizzazione File

### Struttura Consigliata
```
md/
├── Corso1/
│   ├── 01-introduzione.md
│   ├── 02-capitolo1.md
│   └── 03-capitolo2.md
├── Corso2/
│   └── appunti.md
└── README.md
```

### Frontmatter YAML (opzionale)
```yaml
---
title: Titolo del Documento
tags: [python, tutorial, beginner]
date: 2025-12-02
---

# Contenuto
...
```

## ⌨️ Keyboard Shortcuts

### Home Page
- `/` - Focus ricerca
- `Esc` - Chiudi ricerca
- `Ctrl+N` - Nuovo file

### Editor
- `Ctrl+S` - Salva
- `Ctrl+B` - Grassetto
- `Ctrl+I` - Corsivo

### Viewer
- Scroll fluido per TOC

## 🎨 Temi

### Toggle Tema
Click su 🌙/☀️ in qualsiasi pagina

### Temi Codice (nei viewer)
- Atom One Dark (default)
- GitHub Dark
- Monokai
- Nord
- Dracula

## 🔧 API Endpoints

### File Operations
```
GET    /api/files                    # Albero file/cartelle
GET    /api/file/<path>              # Contenuto + metadata
PUT    /api/file/<path>              # Aggiorna file
DELETE /api/file/<path>              # Elimina file
POST   /api/file/<path>/rename       # Rinomina file
POST   /api/create                   # Crea nuovo file
```

### Folder Operations
```
POST   /api/folder                   # Crea cartella
DELETE /api/folder/<path>            # Elimina cartella
POST   /api/folder/<path>/rename     # Rinomina cartella
```

### Utility
```
GET    /api/search?q=<query>         # Ricerca full-text
GET    /api/stats                    # Statistiche globali
GET    /api/templates                # Lista template
POST   /api/upload-image             # Upload immagine
```

## 🐛 Troubleshooting

### Problema: Server non si avvia
**Soluzione**: 
- Verifica che Flask sia installato: `pip install flask flask-cors`
- Controlla che la porta 5000 sia libera
- Su Windows: `netstat -ano | findstr :5000`

### Problema: File non si rigenerano
**Soluzione**:
- Assicurati che il watcher sia attivo
- Verifica permessi scrittura su cartella `web/`
- Controlla che i file siano `.md`
- Rigenera manualmente: `python scripts/regenerate_preview.py`

### Problema: Notifiche non funzionano
**Soluzione**:
- Concedi permessi notifiche al browser
- Chrome: Impostazioni → Privacy → Notifiche
- Alcuni browser richiedono HTTPS

### Problema: Immagini non si caricano
**Soluzione**:
- Crea cartella `images/` nella root se non esiste
- Verifica permessi scrittura
- Usa path relativi: `![alt](../images/foto.jpg)`

### Problema: CSS/JS non caricano
**Soluzione**:
- Svuota cache browser: `Ctrl+Shift+R`
- Verifica che i CDN siano raggiungibili
- Controlla console browser per errori

## 📱 Mobile/Tablet

Il design è responsive ma ottimizzato per desktop. Su mobile:
- La sidebar TOC è nascosta
- Il layout diventa single-column
- Touch gestures disponibili

## 🔒 Sicurezza

### Best Practices
- ✅ Path sanitization implementato
- ✅ HTML escaping automatico
- ✅ CORS configurato
- ⚠️ Non esporre il server su Internet (solo localhost)
- ⚠️ Non usare in produzione senza autenticazione

## 📊 Statistiche Sistema

### Metriche Disponibili
- Totale file
- Totale parole
- Dimensione totale
- Media parole per file
- Distribuzione tag
- Attività ultimi 7 giorni
- File più lunghi
- File recenti

## 🎓 Esempi Pratici

### Creare un nuovo corso
```bash
1. Apri http://localhost:5000
2. Click "📁 Cartelle"
3. Click "➕ Nuova Cartella"
4. Nome: "Corso Python"
5. Click "Crea"
```

### Scrivere una nuova lezione
```bash
1. Apri http://localhost:5000
2. Click "✨ Nuovo File"
3. Scegli template "Lezione"
4. Inserisci titolo
5. Scrivi contenuto
6. Ctrl+S per salvare
```

### Organizzare file esistenti
```bash
1. Apri "📁 Cartelle"
2. Crea struttura cartelle desiderata
3. Sposta file via drag & drop (o rinomina con path)
```

### Export in PDF
```bash
1. Apri qualsiasi file
2. Click "📄 PDF"
3. Nel dialog stampa scegli "Salva come PDF"
4. Salva dove preferisci
```

## 🔄 Aggiornamenti

### Rigenerare tutti i file
```bash
python scripts/regenerate_preview.py
```

### Aggiornare uno specifico file
Modifica il file .md, il watcher lo rileverà automaticamente

### Pulire cache
```bash
# Elimina tutti gli HTML generati
rm -rf web/*.html web/**/*.html
# Rigenera
python scripts/regenerate_preview.py
```

## 💡 Tips & Tricks

### 1. Uso Tag Efficace
```markdown
---
tags: [corso-python, lezione, base]
---
```
Poi usa la tag cloud per filtrare

### 2. Link Interni
```markdown
Vedi [altra lezione](./lezione2.md)
```

### 3. Immagini Locali
```markdown
![Diagram](../images/diagram.png)
```

### 4. Tabelle Markdown
```markdown
| Col1 | Col2 |
|------|------|
| A    | B    |
```

### 5. Code Blocks
```markdown
\`\`\`python
def hello():
    print("Hello World")
\`\`\`
```

### 6. Math (se supportato da browser)
```markdown
Inline: $E = mc^2$

Block:
$$
\frac{-b \pm \sqrt{b^2-4ac}}{2a}
$$
```

## 📝 Prossimi Miglioramenti (TODO)

- [ ] Sync cloud (Dropbox/Drive)
- [ ] Collaborazione real-time
- [ ] Mobile app
- [ ] Plugin system
- [ ] Export DOCX/EPUB
- [ ] Git integration avanzata
- [ ] Search con fuzzy matching
- [ ] Grafici più avanzati

## 📄 Licenza

Progetto personale - Usa liberamente

## 🆘 Supporto

Per problemi o domande:
1. Controlla questa documentazione
2. Leggi `README_FEATURES.md` per dettagli
3. Controlla console browser per errori
4. Verifica log terminale del server

---

**Buon lavoro con AppuntiApp!** 📚✨

*Versione: 2.0 - Dicembre 2025*
