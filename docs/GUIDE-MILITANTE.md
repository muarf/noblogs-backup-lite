# Guide militant·e — Sauvegarder son blog NoBlogs

**3 étapes. Pas de jargon.**

---

## Étape 1 — Télécharger l'outil

Sur **Ubuntu** ou **macOS**, ouvrez un terminal dans le dossier `noblogs-backup` :

```bash
./noblogs
```

Sur **Tails** : Applications → Terminal, allez dans le dossier (de préférence sur votre **stockage persistant** ou une clé USB) :

```bash
cd ~/Persistent/noblogs-backup   # ou le chemin de votre clé
./noblogs
```

> La première fois, l'outil installe automatiquement ce dont il a besoin (1 à 2 minutes).

---

## Étape 2 — Sauvegarder

L'assistant vous demande votre **slug** : c'est le nom avant `.noblogs.org`.

| Votre blog | Slug à entrer |
|---|---|
| `https://monblog.noblogs.org` | `monblog` |
| `https://actforfree.noblogs.org` | `actforfree` |

Attendez la fin. Vous obtenez un fichier :

```
backups/monblog-noblogs-backup.zip
```

**Copiez ce fichier sur une clé USB ou un cloud chiffré.** C'est votre sauvegarde complète.

---

## Étape 3 — Republier (quand vous en avez besoin)

```bash
./noblogs republier backups/monblog-noblogs-backup.zip
```

Choisissez :

- **[1] WordPress.com** — le plus simple : créez un compte, importez le fichier XML
- **[2] WordPress local** — reproduction à l'identique (thème, menus, images)

Les guides détaillés sont **dans le ZIP** et s'affichent automatiquement.

---

## Questions fréquentes

**Mon blog est déjà mort, ça marche ?**  
Oui. L'outil récupère les articles via archive.org quand c'est possible.

**Je n'ai rien compris au terminal.**  
Demandez à quelqu'un de votre collectif de lancer `./noblogs` pour vous — une seule personne technique peut sauvegarder tout le groupe (fichier `.txt` de slugs : `./noblogs sauvegarder liste.txt`).

**Sur Tails, mes fichiers disparaissent au redémarrage ?**  
Oui, sauf si vous activez le stockage persistant ou copiez le `.zip` sur une clé USB **avant** d'éteindre.

**Et le miroir statique (Hugo) ?**  
Prévu pour une prochaine version — pour l'instant, WordPress.com ou local.
