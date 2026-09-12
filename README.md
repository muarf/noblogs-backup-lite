# noblogs-backup

Sauvegarde **complète et autonome** de n'importe quel blog [NoBlogs](https://noblogs.org), avec republication sur **WordPress.com** ou **WordPress local**.

## Démarrage militant (1 commande / 1 clic)

| OS | Comment lancer |
|---|---|
| Tails / Ubuntu / macOS | Terminal → `./noblogs` |
| macOS | Double-clic sur `noblogs.command` |
| Windows | Double-clic sur `noblogs.bat` |

L'assistant vous guide : slug → sauvegarde → republication WordPress.com ou locale.
La première fois, l'outil installe automatiquement Python dépendances (1 à 2 min).

> Pour un .exe Windows sans Python installé : `./noblogs distrib` (à venir).

| Commande | Action |
|---|---|
| `./noblogs` | Assistant interactif |
| `./noblogs sauvegarder monblog` | Sauvegarde → `backups/monblog-noblogs-backup.zip` |
| `./noblogs republier backups/monblog-noblogs-backup.zip` | Guide WordPress.com ou restauration locale |
| `./noblogs aide` | Aide |

Guides détaillés : [`docs/GUIDE-MILITANTE.md`](docs/GUIDE-MILITANTE.md)

---

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
| **WordPress.com** | Export WXR + guide pas-à-pas inclus dans le ZIP |
| **Local identique** | `./restore.sh` → médias + thème + WXR + fidélité |
| **Portable** | `requirements.txt` minimal (requests + beautifulsoup4) |

> **À venir** : export statique Hugo (miroir `.onion` / GDrive) — voir infrastructure `mirroir` sur bigarm.

---

## Installation manuelle (développeur·euses)

```bash
cd noblogs-backup
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
├── restore.sh                # restauration locale identique
├── restore_parity.php
├── GUIDE-MILITANTE.md
├── GUIDE-WORDPRESS-COM.md
├── GUIDE-LOCAL.md
├── README.md
└── metadata.json
```

## Restauration locale

```bash
unzip monblog-noblogs-backup.zip && cd monblog-noblogs-backup
./restore.sh
```

Ou via l'outil : `./noblogs republier backups/monblog-noblogs-backup.zip`

## Republication WordPress.com

1. Créez un site sur [wordpress.com](https://wordpress.com)
2. **Outils → Importer → WordPress**
3. Uploadez `wordpress-export.xml` (cochez *Télécharger les pièces jointes*)

Guide complet dans chaque archive : `GUIDE-WORDPRESS-COM.md`

## Licence

Héritée des scripts de migration `~/mirroir`. Réutilisez, modifiez, partagez.
