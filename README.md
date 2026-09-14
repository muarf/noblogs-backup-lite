# noblogs-backup-lite

Sauvegarde **complète et autonome** de n'importe quel blog [NoBlogs](https://noblogs.org), empaquetée dans un ZIP.
## Démarrage (1 commande, aucune installation)

Copiez-collez une seule de ces commandes dans un terminal :

| OS | Commande |
|---|---|
| Linux / macOS / Tails | `bash -c "$(curl -fsSL https://raw.githubusercontent.com/muarf/noblogs-backup-lite/main/install.sh)"` |
| Linux / macOS (sans curl) | `bash -c "$(wget -qO- https://raw.githubusercontent.com/muarf/noblogs-backup-lite/main/install.sh)"` |
| Windows (PowerShell) | `powershell -NoProfile -ExecutionPolicy Bypass -Command "iwr https://raw.githubusercontent.com/muarf/noblogs-backup-lite/main/install.ps1 -UseBasicParsing \| iex"` |

L'outil est téléchargé, installé dans `~/noblogs-backup-lite` (sous Tails : `~/Persistent/noblogs-backup-lite`), et l'assistant démarre aussitôt. **Sauvegarde directe** d'un blog en une commande :

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/muarf/noblogs-backup-lite/main/install.sh)" -- sauvegarder monblog
```

L'assistant vous demande le slug de votre blog puis sauvegarde tout dans `backups/<slug>-noblogs-backup.zip`.
La première fois seulement, l'outil installe automatiquement les dépendances Python (1 à 2 min).

| Commande | Action |
|---|---|
| `./noblogs` | Assistant interactif |
| `./noblogs sauvegarder monblog` | Sauvegarde → `backups/monblog-noblogs-backup.zip` |
| `./noblogs aide` | Aide |

> **Anonymat** : l'outil n'utilise ni Tor ni proxy (accès HTTPS direct). Pour une sauvegarde anonyme, redémarrez sous [Tails](https://tails.net) : tout le trafic passe alors par Tor.

## Fonctionnalités

| | |
|---|---|
| **Articles** | Tous, via le flux RSS paginé (contenu complet) |
| **Pages** | Pages statiques via l'API WP REST (paginée) |
| **Médias** | Images, PDF, audio, vidéo… avec rotation Wayback Machine en cas de 404 |
| **Pièces jointes** | Items `<wp:attachment>` dans le WXR (médias rattachés aux articles) |
| **Archive.org** | Snapshot Wayback + API `wayback/available` |
| **Thème** | Téléchargement du thème actif — source NoBlogs (miroir `noblogs-assets`), puis WordPress.org, blog d'origine, archive.org |
| **Plugins** | Tous les plugins NoBlogs embarqués dans le ZIP (`plugins/`, `mu-plugins/`, `wplang/`) — issus du miroir NoBlogs |
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
python3 -m backup monblog --no-plugins
python3 -m backup monblog --no-media
python3 -m backup monblog --assets-cache ~/.cache/noblogs
python3 -m backup monblog --unpack --keep-uploads
```

Le paramètre `--assets-cache` évite de re-télécharger le bundle thèmes/plugins
NoBlogs (≈55 Mo) à chaque sauvegarde : premier run → téléchargé puis mis en cache.

## Contenu du ZIP

```
monblog-noblogs-backup.zip
├── wordpress-export.xml      # import WordPress / WordPress.com
├── uploads/                  # tous les médias
├── theme/<theme>/            # thème actif
├── plugins/                  # tous les plugins NoBlogs
├── mu-plugins/               # must-use-plugins de la plateforme
├── wplang/                   # strings de traduction multi-blogs
├── fidelity.json             # widgets, menus, CSS, couleurs
├── README.md
└── metadata.json
```

L'export est réimplantable sur n'importe quelle instance WordPress (*Outils → Importer → WordPress*), et `uploads/` se replacent dans `wp-content/uploads/`.

### Miroir des assets NoBlogs

Le collectif NoBlogs publiait ses thèmes et plugins sur `git.inventati.org`
(l'infrastructure Autistici a été mise hors-ligne en 2026). Un miroir de
préservation est hébergé sur **github.com/muarf/noblogs-assets** (80 thèmes,
42 plugins, mu-plugins, wplang) ; il est utilisé par défaut pour le thème et
les plugins, avec repli automatique sur WordPress.org / blog d'origine /
archive.org.

## Licence

Héritée des scripts de migration `~/mirroir`. Réutilisez, modifiez, partagez.
