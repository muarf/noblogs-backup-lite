# noblogs-backup-lite

Backup **completo e autonomo** di qualsiasi blog [NoBlogs](https://noblogs.org), impacchettato in un file ZIP.
## Avvio rapido (1 comando)

| OS | Come avviare |
|---|---|
| Tails / Ubuntu / macOS | Terminale → `./noblogs` |

L'assistente ti chiede lo slug del tuo blog e poi esegue il backup di tutto in `backups/<slug>-noblogs-backup.zip`.
Solo la prima volta, lo strumento installa automaticamente le dipendenze Python (1-2 min).

| Comando | Azione |
|---|---|
| `./noblogs` | Assistente interattivo |
| `./noblogs backup mioblog` | Backup → `backups/mioblog-noblogs-backup.zip` |
| `./noblogs help` | Aiuto |

## Funzionalità

| | |
|---|---|
| **Articoli** | Tutti, tramite feed RSS paginato (contenuto completo) |
| **Pagine** | Pagine statiche tramite WP REST API (paginato) |
| **Media** | Immagini, PDF, audio, video… con rotazione Wayback Machine in caso di 404 |
| **Allegati** | Elementi `<wp:attachment>` nel WXR (media allegati agli articoli) |
| **Archive.org** | Snapshot Wayback + API `wayback/available` |
| **Tema** | Download del tema attivo (WordPress.org, blog originale, archive.org) |
| **Fedeltà** | Sidebar, menu, CSS, colori, banner |
| **Portabile** | `requirements.txt` minimo (requests + beautifulsoup4) |

## Installazione manuale (sviluppatori)

```bash
cd noblogs-backup-lite
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m backup mioblog
```

## Opzioni avanzate

```bash
python3 -m backup mioblog --out-dir ~/backup
python3 -m backup mioblog --base-url https://mirror.example.org
python3 -m backup blog1 blog2 blog3
python3 -m backup blogs.txt
python3 -m backup mioblog --no-wayback
python3 -m backup mioblog --no-media
python3 -m backup mioblog --unpack --keep-uploads
```

## Contenuto del file ZIP

```
mioblog-noblogs-backup.zip
├── wordpress-export.xml      # importazione in WordPress / WordPress.com
├── uploads/                  # tutti i media
├── theme/<theme>/            # tema attivo
├── fidelity.json             # widget, menu, CSS, colori
├── README.md
└── metadata.json
```

L'esportazione può essere re-importata in qualsiasi istanza WordPress (*Strumenti → Importa → WordPress*), e `uploads/` deve essere posizionata in `wp-content/uploads/`.

## Licenza

Ereditata dagli script di migrazione `~/mirroir`. Riutilizza, modifica, condividi.
