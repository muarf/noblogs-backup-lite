# noblogs-backup-lite

Sauvegarde **complète et autonome** de n'importe quel blog [NoBlogs](https://noblogs.org), empaquetée dans un ZIP.
## Démarrage (1 commande)

| OS | Comment lancer |
|---|---|
| Tails / Ubuntu / macOS | Terminal → `./noblogs` |

L'assistant vous demande le slug de votre blog puis sauvegarde tout dans `backups/<slug>-noblogs-backup.zip`.
La première fois seulement, l'outil installe automatiquement les dépendances Python (1 à 2 min).

| Commande | Action |
|---|---|
| `./noblogs` | Assistant interactif |
| `./noblogs sauvegarder monblog` | Sauvegarde → `backups/monblog-noblogs-backup.zip` |
| `./noblogs aide` | Aide |

## Fonctionnalités

| | |
|---|---|
| **Articles** | Tous, via le flux RSS paginé (contenu complet) |
| **Pages** | Pages statiques via l'API WP REST (paginée) |
| **Médias** | Images, PDF, audio, vidéo… avec rotation Wayback Machine en cas de 404 |
| **Pièces jointes** | Items `<wp:attachment>` dans le WXR (médias rattachés aux articles) |
| **Archive.org** | Snapshot Wayback + API `wayback/available` |
| **Thème** | Téléchargement du thème actif (WordPress.org, blog d'origine, archive.org) |
| **Fidélité** | Sidebars, menus, CSS, couleurs, bannière |
| **Portable** | `requirements.txt` minimal (requests + beautifulsoup4) |

## Installation manuelle (développeur·euses)

```bash
cd noblogs-backup-lite
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m backup monblog
```

## Options avancées

```bash
python3 -m backup monblog --out-dir ~/sauvegardes
python3 -m backup monblog --base-url https://mirror.example.org
python3 -m backup blog1 blog2 blog3
python3 -m backup blogs.txt
python3 -m backup monblog --no-wayback
python3 -m backup monblog --no-media
python3 -m backup monblog --unpack --keep-uploads
```

## Contenu du ZIP

```
monblog-noblogs-backup.zip
├── wordpress-export.xml      # import WordPress / WordPress.com
├── uploads/                  # tous les médias
├── theme/<theme>/            # thème actif
├── fidelity.json             # widgets, menus, CSS, couleurs
├── README.md
└── metadata.json
```

L'export est réimplantable sur n'importe quelle instance WordPress (*Outils → Importer → WordPress*), et `uploads/` se replacent dans `wp-content/uploads/`.

## Licence

Héritée des scripts de migration `~/mirroir`. Réutilisez, modifiez, partagez.
