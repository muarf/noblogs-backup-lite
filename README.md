# noblogs-backup

Sauvegarde **complète et autonome** de n'importe quel blog [NoBlogs](https://noblogs.org) (WordPress), déployable sur n'importe quelle installation WordPress.

Pour chaque blog : articles, pages, catégories, **le thème actif**, **les widgets de sidebar**, **le menu de navigation**, **le CSS personnalisé**, **les couleurs et la bannière d'en-tête** — et **tous les médias**, y compris ceux disparus, récupérés automatiquement via **archive.org / Wayback Machine** quand le blog est mort ou que les fichiers sont perdus.

Le résultat est un **ZIP autonome** (`<slug>-noblogs-backup.zip`) qui peut :
* être **ré-importé tel quel** via l'interface WordPress (Outils → Importer),
* être **restauré à l'identique** en une commande (`./restore.sh` → thème + sidebars + menus + CSS + couleurs + médias),

## Fonctionnalités

| | |
|---|---|
| **Articles** | Tous, via le flux RSS paginé (contenu complet) |
| **Pages** | Pages statiques via l'API WP REST |
| **Médias** | Images, PDF, audio, vidéo… avec rotation Wayback Machine en cas de 404 |
| **Archive.org** | Deux mécanismes : snapshot `id_` le plus récent, puis API `wayback/available` |
| **Thème** | Téléchargement du thème actif (WordPress.org API, blog d'origine, ou archive.org) |
| **Fidélité** | Sidebars/widgets, menu de navigation, CSS custom, couleurs, logo, bannière, fond |
| **Restore 1-commande** | `./restore.sh` → médias + thème + WXR + URLs + fidélité + `<!--more-->` |
| **Portable** | `requirements.txt` minimal (requests + beautifulsoup4) |
| **Déployable** | L'import WXR fonctionne dans toute interface WordPress + script WP-CLI |

## Installation

```bash
cd noblogs-backup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Utilisation

```bash
# Sauvegarde complète (médias inclus)
python3 -m backup monblog

# Dossier de sortie personnalisé
python3 -m backup monblog --out-dir ~/sauvegardes-noblogs

# Blog derrière un domaine miroir / .onion
python3 -m backup monblog --base-url https://mirror.example.org

# Plusieurs blogs (parallélisme léger)
python3 -m backup blog1 blog2 blog3

# Liste de blogs dans un fichier .txt
python3 -m backup blogs.txt

# Blog entièrement mort : activer la récupération archive.org (défaut : activée)
python3 -m backup monblog --no-wayback   # pour la désactiver

# Désactiver les médias (export texte seul)
python3 -m backup monblog --no-media

# Conserver uploads/ + XML en clair à côté du ZIP
python3 -m backup monblog --unpack --keep-uploads
```

## Sortie

```
backups/
├── monblog-noblogs-backup.zip   # archive autonome complète
└── monblog/                     # contenu déployé (si --unpack)
    ├── wordpress-export.xml
    ├── fidelity.json
    ├── theme/…
    └── uploads/…
```

Contenu du ZIP :

```
monblog-noblogs-backup.zip
├── wordpress-export.xml   # export WXR 1.2 (Outils > Importer > WordPress)
├── uploads/               # médias → wp-content/uploads
├── theme/<theme>/         # thème WordPress actif du blog original
├── fidelity.json          # sidebars, menus, CSS, couleurs, bannière, fond
├── restore.sh             # restauration complète en une commande
├── restore_parity.php     # application de la fidélité via WP-CLI
├── README.md
└── metadata.json
```

## Restauration

**Restauration complète (recommandé)** — thème, sidebars, menus, CSS, couleurs, médias, articles :
```bash
unzip monblog-noblogs-backup.zip && cd monblog-noblogs-backup
WP=/var/www/html URL=https://monsite.org ./restore.sh
```

**Interface WordPress seule** (articles + pages + médias, sans fidélité) :
1. Ouvrez **Outils > Importer > WordPress** (installez l'extension si demandé).
2. Importez `wordpress-export.xml` avec l'option *« Télécharger et importer les fichiers joints »*.
3. Copiez `uploads/` dans `wp-content/uploads/`, puis `theme/*` dans `wp-content/themes/` et activez le thème.
4. Appliquez la fidélité (widgets, menus, CSS) : `wp eval-file restore_parity.php`.

## Remarques

- Les fichiers déjà téléchargés sont ignorés (script re-exécutable, résilient aux coupures réseau).
- La récupération archive.org est *best-effort* : les URL introuvables partout sont recensées dans `metadata.json` (`media.failed`).
- Aucun compte, aucune clé API, aucun service requis. Code 100 % autohébergeable.

## Licence

Héritée des scripts de migration `~/mirroir` (projet de miroir des blogs NoBlogs). Réutilisez, modifiez, partagez.