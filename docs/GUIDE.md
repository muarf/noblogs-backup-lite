# Guide — Sauvegarder son blog

**3 étapes.**

---

## Étape 1 — Lancer l'outil

L'outil s'installe et se lance en **une seule commande** (rien à télécharger à la main). Il installe automatiquement ce dont il a besoin la première fois (1 à 2 minutes) et ne nécessite aucune compétence technique particulière.

### Le plus simple — 1 commande

Ouvrez un terminal et copiez-collez **une** de ces commandes :

**Linux / macOS / Tails :**
```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/muarf/noblogs-backup-lite/main/install.sh)"
```

*(Sans curl ? Utilisez la variante wget :)*
```bash
bash -c "$(wget -qO- https://raw.githubusercontent.com/muarf/noblogs-backup-lite/main/install.sh)"
```

**Windows — PowerShell :**
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "iwr https://raw.githubusercontent.com/muarf/noblogs-backup-lite/main/install.ps1 -UseBasicParsing | iex"
```

L'outil est installé dans `~/noblogs-backup-lite` (sous Tails, dans votre **stockage persistant** : `~/Persistent/noblogs-backup-lite`) et l'assistant démarre.

### Déjà téléchargé (méthode manuelle)

**Windows** : double-cliquez sur `noblogs.bat`.
**macOS / Linux / Tails** : ouvrez un terminal dans le dossier `noblogs-backup-lite` puis `./noblogs`.

> **Anonymat** : l'outil n'utilise ni Tor ni proxy (accès HTTPS direct). Pour une sauvegarde anonyme, faites-le depuis **Tails** : tout le trafic passe alors par Tor.

---

## Étape 2 — Sauvegarder

L'assistant vous demande l'adresse de votre blog (ou juste son "slug", la première partie de l'adresse).

| Votre blog | Ce que vous pouvez entrer |
|---|---|
| `https://monblog.noblogs.org` | `monblog` ou `https://monblog.noblogs.org` |
| `https://actforfree.noblogs.org` | `actforfree` |

**Encore plus rapide** — installez *et* sauvegardez en une seule commande en ajoutant le blog :

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/muarf/noblogs-backup-lite/main/install.sh)" -- sauvegarder monblog
```

Attendez la fin de l'opération. Vous obtiendrez un fichier dans le dossier `backups` :
```text
backups/monblog-noblogs-backup.zip
```

**Copiez ce fichier `.zip` sur une clé USB ou un cloud chiffré.** C'est votre sauvegarde complète.

---

## Étape 3 — Garder votre sauvegarde au chaud

Le `.zip` est **votre sauvegarde complète** : articles, pages, médias, thème, plugins NoBlogs et fidélité visuelle.

Copiez-le sur plusieurs supports (clé USB, disque chiffré, cloud) et rangez une copie chez une autre personne du collectif. Vous pourrez ensuite le réimporter sur n'importe quel WordPress (*Outils → Importer → WordPress*). Il contient aussi les plugins et le thème du blog original, prêts à être réinstallés auprès de votre hébergeur.

---

## Questions fréquentes

**Mon blog est déjà mort, ça marche ?**  
Oui. L'outil récupère les articles et médias via archive.org quand c'est possible.

**Je veux sauvegarder plusieurs blogs d'un coup.**
Créez un fichier texte `liste.txt` avec une adresse par ligne. Ouvrez un terminal et tapez : `./noblogs sauvegarder liste.txt` (ou utilisez la ligne de commande sur Windows avec `python -m backup liste.txt`).

**Sur Tails, mes fichiers disparaissent au redémarrage ?**  
Oui, sauf si vous activez le stockage persistant ou si vous copiez le fichier `.zip` sur une clé USB **avant** d'éteindre l'ordinateur.

**Sous Tails, j'ai une erreur « python3-venv » / module venv manquant ?**
Rien à faire : Python 3 est déjà présent, et l'outil crée tout seul son
environnement **sans sudo ni mot de passe d'administration**. La première
fois seulement, il installe `pip` dans un dossier de votre espace personnel
(1 à 2 min). Si vous préférez passer par sudo, définissez un **mot de passe
d'administration** à l'écran de bienvenue de Tails puis tapez :
```bash
sudo apt install python3-venv
```
Sur Ubuntu (qui inclut `python3-venv`), tout fonctionne déjà sans commande supplémentaire.
