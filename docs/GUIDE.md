# Guide — Sauvegarder son blog NoBlogs

**3 étapes.**

---

## Étape 1 — Télécharger l'outil

Sur **Ubuntu** ou **macOS**, ouvrez un terminal dans le dossier `noblogs-backup-lite` :

```bash
./noblogs
```

Sur **Tails** : Applications → Terminal, allez dans le dossier (de préférence sur votre **stockage persistant** ou une clé USB) :

```bash
cd ~/Persistent/noblogs-backup-lite   # ou le chemin de votre clé
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

## Étape 3 — Garder votre sauvegarde au chaud

Le `.zip` est **votre sauvegarde complète** : articles, pages, médias, thème, fidélité visuelle.

Copiez-le sur plusieurs supports (clé USB, disque chiffré, cloud) et rangez une copie chez une autre personne du collectif. Vous pourrez ensuite le réimporter sur n'importe quel WordPress (*Outils → Importer → WordPress*).

---

## Questions fréquentes

**Mon blog est déjà mort, ça marche ?**  
Oui. L'outil récupère les articles via archive.org quand c'est possible.

**Je n'ai rien compris au terminal.**  
Demandez à quelqu'un de votre collectif de lancer `./noblogs` pour vous — une seule personne technique peut sauvegarder tout le groupe (fichier `.txt` de slugs : `./noblogs sauvegarder liste.txt`).

**Sur Tails, mes fichiers disparaissent au redémarrage ?**  
Oui, sauf si vous activez le stockage persistant ou copiez le `.zip` sur une clé USB **avant** d'éteindre.

