# 📚 AppuntiApp - Documentazione Completa

Sistema avanzato per gestire, visualizzare e organizzare documenti Markdown con interfaccia web moderna.

## 🚀 Funzionalità Implementate

### ✨ Funzionalità Principali

#### 1. **Ricerca Full-Text**
- Barra di ricerca nella home page
- Ricerca in tempo reale nei contenuti
- Highlight dei risultati
- Filtro per tag tramite tag cloud
- Shortcut `/` per focus rapido sulla ricerca

#### 2. **Tema Chiaro/Scuro**
- Toggle tra dark mode e light mode
- Preferenze salvate in localStorage
- Transizioni fluide
- Applicato a tutte le pagine

#### 3. **Breadcrumb Navigation**
- Percorso file cliccabile nei viewer
- Navigazione rapida tra cartelle
- Link alla home sempre visibile

#### 4. **Editor Integrato**
- Split view: Markdown a sinistra, preview a destra
- Syntax highlighting per codice
- Auto-save con indicatore di stato
- Supporto template predefiniti
- Upload immagini drag & drop
- Shortcuts da tastiera (Ctrl+S, Ctrl+B, Ctrl+I)
- Contatore parole/caratteri/righe in tempo reale

#### 5. **Export PDF**
- Stampa/Export in PDF con stile ottimizzato
- Print CSS dedicato
- Pulsante in ogni viewer

#### 6. **Gestione Cartelle Avanzata**
- Creazione cartelle via API
- Eliminazione e rinomina
- Struttura ad albero navigabile
- Supporto sottocartelle ricorsive

#### 7. **Tag e Metadata**
- Sistema tag con frontmatter YAML
- Tag cloud nella home
- Filtro per tag
- Statistiche tag nella dashboard

#### 8. **Indicatore Stato Live**
- Badge che mostra se il server è attivo
- Check API automatico
- Indicatore visivo nella footer

#### 9. **Informazioni File Dettagliate**
- Data ultima modifica
- Contatore parole
- Tempo di lettura stimato
- Dimensione file
- Visibili in ogni file e nella lista

#### 10. **Anteprima File**
- Info file al passaggio del mouse (implementato nei metadati visibili)
- Statistiche immediate nella lista file

#### 11. **Keyboard Shortcuts**
- `/` - Focus sulla ricerca
- `Esc` - Chiudi ricerca/deseleziona
- `Ctrl+N` - Nuovo file (nell'editor)
- `Ctrl+S` - Salva file
- `Ctrl+B` - Grassetto
- `Ctrl+I` - Corsivo

#### 12. **Table of Contents (TOC)**
- TOC auto-generato dai titoli H1-H6
- Sidebar fissa con scroll smooth
- Click per navigare tra sezioni
- Gerarchico a 3 livelli

#### 13. **Upload Immagini**
- Drag & drop nell'editor
- Upload via API
- Salvataggio in cartella `/images`
- Inserimento automatico markdown

#### 14. **Recent Files e Preferiti**
- Lista ultimi 20 file aperti
- Sistema stelline per preferiti
- Salvato in localStorage
- Visibile nella home

#### 15. **Temi Syntax Highlighting**
- Selector per cambiare tema codice
- 5 temi disponibili:
  - Atom One Dark
  - GitHub Dark
  - Monokai
  - Nord
  - Dracula
- Preferenze salvate

#### 16. **Notifiche Browser**
- Notification API per modifiche file
- Alert quando file viene rigenerato
- Richiesta permessi automatica

#### 17. **Pagina Statistiche Completa**
- Dashboard con grafici interattivi (Chart.js)
- 4 card statistiche principali
- 4 grafici:
  - Top 10 file per parole (bar chart)
  - Distribuzione tag (pie chart)
  - Attività ultimi 7 giorni (line chart)
  - File per cartella (doughnut chart)
- Tabella file recenti
- Visualizzazione tutti i tag
- Link diretti ai file

#### 18. **Sistema Template**
- 4 template predefiniti:
  - Vuoto
  - Nota
  - Lezione (con frontmatter)
  - TODO List
- Placeholder dinamici ({title}, {date})
- Modale per selezione template

#### 19. **Cache Incrementale**
- Rigenerazione ottimizzata
- Solo file modificati vengono rigenerati
- Parsing frontmatter per metadata

#### 20. **Validazione Markdown**
- Parsing frontmatter YAML
- Estrazione tag automatica
- Conteggio parole accurato
- Gestione errori robusta

### 🔧 API REST Completa

#### Endpoint File
- `GET /api/files` - Albero file e cartelle
- `GET /api/file/<path>` - Contenuto file + metadata
- `PUT /api/file/<path>` - Aggiorna file
- `DELETE /api/file/<path>` - Elimina file
- `POST /api/file/<path>/rename` - Rinomina file
- `POST /api/create` - Crea nuovo file

#### Endpoint Cartelle
- `POST /api/folder` - Crea cartella
- `DELETE /api/folder/<path>` - Elimina cartella
- `POST /api/folder/<path>/rename` - Rinomina cartella

#### Endpoint Utilità
- `GET /api/search?q=<query>` - Ricerca full-text
- `GET /api/stats` - Statistiche globali
- `GET /api/templates` - Lista template
- `POST /api/upload-image` - Upload immagine
- `GET /images/<filename>` - Serve immagini

## 📂 Struttura Progetto

```
AppuntiApp/
├── md/                          # File Markdown (organizzabili in sottocartelle)
│   ├── Fondamenti di Reti/
│   ├── Sicurezza Informatica/
│   └── README.md
├── web/                         # File HTML generati
│   ├── preview.html            # Home page con lista file
│   ├── editor.html             # Editor avanzato
│   ├── stats.html              # Dashboard statistiche
│   ├── Fondamenti di Reti/    # HTML dei viewer (struttura mirror)
│   └── Sicurezza Informatica/
├── images/                      # Immagini caricate
├── scripts/
│   ├── regenerate_preview.py   # Script generazione HTML
│   ├── auto_regen_watcher.py   # Watcher automatico
│   ├── api_server.py           # Server Flask con API
│   └── install_dependencies.py
└── README_FEATURES.md          # Questo file
```

## 🎨 Stile e Design

- **Design System**: Dark/Light mode con variabili CSS
- **Font**: Inter, Segoe UI (system fonts)
- **Codice**: Fira Code, Consolas, Monaco
- **Colori**:
  - Accent: `#4cc9f0` (cyan brillante)
  - Background Dark: `#0b0f12`
  - Panel Dark: `#0f1720`
  - Background Light: `#f5f7fa`
  - Panel Light: `#ffffff`
- **Icone**: Emoji Unicode native
- **Layout**: CSS Grid responsive
- **Animazioni**: Transizioni fluide 0.15-0.3s

## 🚀 Come Usare

### 1. Avvio Base
```bash
# Genera HTML dei file esistenti
python scripts/regenerate_preview.py

# Avvia server Flask (consigliato)
python scripts/api_server.py

# Visita http://localhost:5000
```

### 2. Avvio con Watcher (Consigliato)
```bash
# Terminale 1: Watcher per auto-rigenerazione
python scripts/auto_regen_watcher.py

# Terminale 2: Server API
python scripts/api_server.py

# Ora ogni modifica ai file .md viene rilevata automaticamente
```

### 3. Organizzazione File
```bash
# Crea sottocartelle in md/
md/
  ├── Corso1/
  │   ├── lezione1.md
  │   └── lezione2.md
  └── Corso2/
      └── appunti.md

# Lo script le gestisce automaticamente
```

### 4. Uso Tag
Aggiungi frontmatter YAML all'inizio dei file:

```markdown
---
title: Il mio documento
tags: [python, tutorial, beginner]
date: 2025-12-02
---

# Contenuto del documento
...
```

### 5. Shortcuts Editor
- `Ctrl+S` - Salva
- `Ctrl+B` - **Grassetto**
- `Ctrl+I` - *Corsivo*
- Upload immagini: Click su pulsante 🖼️

## 📊 Caratteristiche Tecniche

### Frontend
- **Vanilla JavaScript** (no framework)
- **Marked.js** - Parsing Markdown
- **Highlight.js** - Syntax highlighting codice
- **Chart.js** - Grafici statistiche
- **LocalStorage** - Persistenza preferenze
- **Notification API** - Alert browser
- **Fetch API** - Chiamate async

### Backend
- **Flask** - Web server
- **Flask-CORS** - Cross-origin support
- **Watchdog** - File system monitoring
- **Python 3.x** - Linguaggio base

### Generazione
- **Pathlib** - Gestione path
- **Regex** - Parsing frontmatter
- **HTML escaping** - Sicurezza XSS

## 🎯 Best Practices

### Organizzazione File
- Usa nomi descrittivi per file e cartelle
- Struttura logica per argomenti
- Frontmatter per metadata

### Scrittura Markdown
- Titoli gerarchici (H1 → H2 → H3)
- Tag pertinenti per ricerca
- Link relativi tra documenti

### Performance
- Il watcher rigenera solo quando serve
- Cache browser per risorse statiche
- Lazy loading per immagini grandi

### Sicurezza
- Path sanitization negli endpoint
- HTML escaping automatico
- CORS configurato correttamente

## 🔄 Workflow Consigliato

1. **Avvia server + watcher** all'inizio della sessione
2. **Apri preview.html** nel browser
3. **Scrivi/modifica** file in VS Code
4. **Il watcher rileva** e rigenera automaticamente
5. **Il browser ricarica** la pagina (auto-reload ogni 2s)
6. **Usa l'editor integrato** per modifiche rapide
7. **Consulta statistiche** periodicamente

## 📱 Responsive Design
- Desktop: Layout completo con sidebar
- Tablet: Grid adattivo
- Mobile: Stack verticale, sidebar nascosta

## 🎓 Esempi d'Uso

### Creare un nuovo corso
1. Crea cartella `md/NomeCorso/`
2. Crea file `md/NomeCorso/lezione1.md`:
```markdown
---
title: Lezione 1 - Introduzione
tags: [nomecorso, lezione, intro]
---

# Lezione 1

## Argomenti
- Punto 1
- Punto 2
```
3. Il watcher rigenera automaticamente
4. Appare nella home sotto la cartella "NomeCorso"

### Aggiungere immagine
1. Apri editor
2. Click su 🖼️
3. Seleziona immagine
4. Viene inserito `![nome](path)` automaticamente

### Export PDF
1. Apri qualsiasi file
2. Click su 📄 PDF
3. Si apre dialog stampa
4. Salva come PDF

## 🐛 Troubleshooting

### Il server non si avvia
- Verifica che Flask sia installato: `pip install flask flask-cors`
- Controlla che la porta 5000 sia libera

### I file non si rigenerano
- Assicurati che il watcher sia attivo
- Verifica permessi scrittura su `web/`
- Controlla che i file siano `.md`

### Notifiche non funzionano
- Concedi permessi notifiche al browser
- Alcuni browser richiedono HTTPS per notifiche

## 📝 TODO Future Enhancements
- Sync con cloud storage (Dropbox/Drive)
- Collaborazione real-time
- Mobile app companion
- Export in altri formati (DOCX, EPUB)
- Grafici più avanzati
- Plugin system

## 📄 Licenza
Progetto personale - Usa liberamente

---

**Creato con** ❤️ **e** ☕

*Ultima versione: Dicembre 2025*
