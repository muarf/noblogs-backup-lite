# Guide — Sauvegarder son blog

**3 étapes.**

---

## Étape 1 — Lancer l'outil

L'outil installe automatiquement ce dont il a besoin la première fois (1 à 2 minutes) et ne nécessite aucune compétence technique particulière.

### Sur Windows
1. Ouvrez le dossier `noblogs-backup-lite`
2. Double-cliquez sur le fichier `noblogs.bat`

### Sur macOS
1. Ouvrez l'application **Terminal** (dans Applications → Utilitaires)
2. Glissez-déposez le fichier `noblogs` (qui est dans le dossier `noblogs-backup-lite`) dans la fenêtre du terminal
3. Appuyez sur la touche **Entrée** (Retour)

### Sur Ubuntu / Linux
Ouvrez un terminal dans le dossier `noblogs-backup-lite` :
```bash
./noblogs
```

### Sur Tails
Allez dans **Applications → Utilitaires → Terminal**, puis allez dans le dossier (de préférence sur votre **stockage persistant** ou une clé USB) :
```bash
cd ~/Persistent/noblogs-backup-lite   # ou le chemin de votre clé
./noblogs
```

---

## Étape 2 — Sauvegarder

L'assistant vous demande l'adresse de votre blog (ou juste son "slug", la première partie de l'adresse).

| Votre blog | Ce que vous pouvez entrer |
|---|---|
| `https://monblog.noblogs.org` | `monblog` ou `https://monblog.noblogs.org` |
| `https://actforfree.noblogs.org` | `actforfree` |

Attendez la fin de l'opération. Vous obtiendrez un fichier dans le dossier `backups` :
```text
backups/monblog-noblogs-backup.zip
```

**Copiez ce fichier `.zip` sur une clé USB ou un cloud chiffré.** C'est votre sauvegarde complète.

---

## Étape 3 — Garder votre sauvegarde au chaud

Le `.zip` est **votre sauvegarde complète** : articles, pages, médias, thème, fidélité visuelle.

Copiez-le sur plusieurs supports (clé USB, disque chiffré, cloud) et rangez une copie chez une autre personne du collectif. Vous pourrez ensuite le réimporter sur n'importe quel WordPress (*Outils → Importer → WordPress*).

---

## Questions fréquentes

**Mon blog est déjà mort, ça marche ?**  
Oui. L'outil récupère les articles et médias via archive.org quand c'est possible.

**Je veux sauvegarder plusieurs blogs d'un coup.**
Créez un fichier texte `liste.txt` avec une adresse par ligne. Ouvrez un terminal et tapez : `./noblogs sauvegarder liste.txt` (ou utilisez la ligne de commande sur Windows avec `python -m backup liste.txt`).

**Sur Tails, mes fichiers disparaissent au redémarrage ?**  
Oui, sauf si vous activez le stockage persistant ou si vous copiez le fichier `.zip` sur une clé USB **avant** d'éteindre l'ordinateur.
