# Republication sur WordPress.com

**Objectif** : remettre en ligne votre blog NoBlogs sur WordPress.com avec le minimum d'étapes.

> WordPress.com ne permet pas d'installer n'importe quel thème ni tous les widgets custom.  
> **Le contenu (articles, pages, images) sera fidèle.** L'apparence sera proche — vous pourrez ajuster le thème dans l'interface.

---

## Avant de commencer

- [ ] Votre fichier `wordpress-export.xml` (dans le ZIP décompressé)
- [ ] Une connexion Internet
- [ ] 20 à 30 minutes

---

## Étape 1 — Créer votre site WordPress.com

1. Allez sur **https://wordpress.com** et cliquez **Commencer**.
2. Créez un compte (e-mail ou compte existant).
3. Choisissez un **nom de site** (ex. `monblog.wordpress.com`).
4. Sélectionnez le forfait **Gratuit** ou **Personnel** — le forfait **Personnel** (ou supérieur) est nécessaire pour l'import WordPress complet.
5. Passez les questions de personnalisation (vous pourrez tout modifier après).

---

## Étape 2 — Installer l'importeur WordPress

1. Dans le **tableau de bord** de votre site, menu gauche : **Outils → Importer**.
2. Cliquez sur **WordPress** → **Installer l'importateur** (si proposé) → **Activer et lancer l'importateur**.

> Si « Importer → WordPress » n'apparaît pas, votre forfait ne permet peut-être pas l'import. Passez au forfait **Personnel** (environ 4 €/mois) ou utilisez la republication **locale** (guide GUIDE-LOCAL.md).

---

## Étape 3 — Importer votre sauvegarde

1. Cliquez **Choisir un fichier** et sélectionnez **`wordpress-export.xml`**.
2. Cochez **Télécharger et importer les pièces jointes** (important pour les images).
3. Cliquez **Continuer**.
4. Pour **Attribution des auteurs** : choisissez votre compte ou « Créer un nouvel utilisateur ».
5. Cochez **Télécharger et importer les pièces jointes** une dernière fois si demandé.
6. Cliquez **Envoyer**.

L'import peut prendre plusieurs minutes selon la taille du blog.

---

## Étape 4 — Vérifier les images

1. Ouvrez quelques articles et vérifiez que les images s'affichent.
2. Si des images manquent :
   - Votre blog NoBlogs d'origine était peut-être déjà hors ligne au moment de la sauvegarde ;
   - Relancez une sauvegarde **tant que le blog est encore en ligne**, puis réimportez ;
   - Ou utilisez la republication **locale** (100 % des médias inclus dans le ZIP).

---

## Étape 5 — Choisir un thème proche

1. **Apparence → Thèmes**.
2. Cherchez le thème de votre ancien blog (indiqué dans `metadata.json`, champ `theme`).
3. Thèmes courants sur NoBlogs : Twenty Sixteen, Twenty Fifteen, Twenty Ten — disponibles sur WordPress.com.

---

## Étape 6 — Menu et pages d'accueil

1. **Apparence → Menus** — recréez votre menu (titres dans `fidelity.json` → `menu_items`).
2. **Réglages → Lecture** — définissez la page d'accueil si vous aviez une page statique.

---

## Récapitulatif

| Élément | WordPress.com |
|---|---|
| Articles | Importés |
| Pages | Importées |
| Images | Importées (si blog en ligne à la sauvegarde) |
| Thème exact | À choisir manuellement (proche) |
| Widgets sidebar | À recréer manuellement |
| URL | `votresite.wordpress.com` ou domaine personnalisé |

**Besoin d'une copie 100 % identique ?** → Guide **GUIDE-LOCAL.md** ou `./noblogs republier …` → option locale.
