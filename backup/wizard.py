"""wizard.py — Assistant interactif multi-OS de noblogs-backup.

Point d'entrée unique utilisé par les lanceurs :
* ``./noblogs``            (bash — Tails, Ubuntu, macOS)
* ``noblogs.command``      (double-clic macOS)
* ``noblogs.bat``          (double-clic Windows)

Sous-commandes :
* (rien)                     → assistant interactif complet
* sauvegarder SLUG (ou URL)  → sauvegarde seule
* republier [ZIP]            → guides de republication
* aide                       → aide rapide
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from . import __version__
from .__main__ import backup_one
from .package import human_size

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
DEFAULT_OUT = REPO_ROOT / "backups"

GUIDES = ("GUIDE-MILITANTE.md", "GUIDE-WORDPRESS-COM.md", "GUIDE-LOCAL.md")


def _utf8_console() -> None:
    """Force UTF-8 sur Windows (console cmd) pour éviter les mojibake."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def detect_platform() -> str:
    """Retourne tails / macos / windows / linux."""
    if os.path.exists("/etc/amnesia") or os.getenv("TAILS_VERSION"):
        return "tails"
    if sys.platform == "darwin":
        return "macos"
    if os.name == "nt":
        return "windows"
    return "linux"


def slug_from_input(raw: str) -> str:
    """Extrait le slug depuis un slug court ou une URL complète."""
    raw = (raw or "").strip()
    if raw.startswith(("http://", "https://")):
        raw = raw.split("/")[2]
    raw = raw.split("/")[0].split("?")[0]
    for suffix in (".noblogs.org", ".zvz.fr"):
        if raw.lower().endswith(suffix):
            raw = raw[: -len(suffix)]
    return raw.strip().lower().replace(" ", "")


def _read(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def _banner() -> None:
    print("")
    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║   NoBlogs Backup — sauvegarde & republication        ║")
    print("  ╚══════════════════════════════════════════════════════╝")
    print("")


def _guide(name: str, extracted_dir: str | None) -> str:
    """Retourne le contenu d'un guide (du ZIP si présent, sinon du dépôt)."""
    if extracted_dir:
        p = Path(extracted_dir) / name
        if p.exists():
            return p.read_text(encoding="utf-8")
    src = DOCS_DIR / name
    if src.exists():
        return src.read_text(encoding="utf-8")
    return ""


def _backup_args(slug: str, out_dir: Path, force: bool = False) -> argparse.Namespace:
    return argparse.Namespace(
        base_url=None,
        out_dir=str(out_dir),
        no_wayback=False,
        no_media=False,
        workers=6,
        keep_uploads=True,
        force=force,
        unpack=False,
        slugs=[slug],
    )


def run_backup(slug: str, out_dir: Path, force: bool = False) -> dict:
    """Lance la sauvegarde complète et retourne le résultat de backup_one.

    ``keep_uploads=True`` par défaut : le cache ``backups/<slug>/uploads`` survit,
    donc les médias déjà téléchargés sont réutilisés (skip). ``force=True`` purge
    ce cache pour un re-téléchargement intégral.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nSauvegarde de « {slug} » en cours…\n", flush=True)
    return backup_one(slug, _backup_args(slug, out_dir, force=force))


def _zip_metadata(zip_path: Path) -> dict:
    """Lit metadata.json depuis un ZIP sans le décompresser."""
    try:
        with zipfile.ZipFile(zip_path) as zf:
            return json.loads(zf.read("metadata.json").decode("utf-8"))
    except Exception:
        return {}


def _media_force_prompt() -> bool:
    """Demande : réutiliser les médias (défaut) ou forcer le re-téléchargement."""
    print("")
    print("  Médias déjà téléchargés : réutiliser par défaut, forcer pour re-télécharger.")
    choice = _read("  [r]éutiliser / [f]orcer le re-téléchargement [r] : ").strip().lower()
    return choice.startswith("f")


def _reuse_media_from_zip(zip_path: Path, out_dir: Path, slug: str) -> None:
    """Remplit le cache local ``<out>/<slug>/uploads`` depuis le ZIP existant.

    Sans cela, une « sauvegarde fraîche » re-téléchargerait tout : le cache avait
    été nettoyé à la création du ZIP. La réutilisation permet de ne re-télécharger
    que ce qui a changé (skip des fichiers déjà présents).
    """
    target = out_dir / slug / "uploads"
    if not target.exists():
        try:
            with zipfile.ZipFile(zip_path) as zf:
                names = [n for n in zf.namelist() if n.startswith("uploads/") and not n.endswith("/")]
                if not names:
                    print("  ⚠ Aucun média dans le ZIP (rien à réutiliser).")
                    return
                target.mkdir(parents=True, exist_ok=True)
                for n in names:
                    dest = target / n[len("uploads/"):]
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(n) as src, open(dest, "wb") as out:
                        shutil.copyfileobj(src, out)
            print(f"  Réutilisation de {len(names)} médias depuis le ZIP.")
        except Exception as e:
            print(f"  ⚠ Médias du ZIP non réutilisés : {e}")


def _after_save(zip_file: str) -> int:
    """Menu post-sauvegarde : republication immédiate (ZIP extrait) ou plus tard."""
    if not zip_file or not Path(zip_file).exists():
        print("\n  ✗ Archive introuvable.\n")
        return 1
    print("")
    print("  Sauvegarde terminée !")
    print(f"  Archive : {zip_file}\n")
    extracted = _extract(Path(zip_file))
    try:
        print("  [1]  Republication sur WordPress.com")
        print("  [2]  Republication locale (identique)")
        print("  [3]  Plus tard — j'ai mon .zip")
        print("")
        choice = _read("  Et maintenant ? [1/2/3] : ") or "3"
        if choice == "1":
            show_wpcom(zip_file, extracted)
        elif choice == "2":
            show_local(zip_file, extracted)
        else:
            print(f"  Votre archive : {zip_file}")
            print(f"  Plus tard : python -m backup wizard republier {zip_file}")
    finally:
        shutil.rmtree(extracted, ignore_errors=True)
    return 0


def _existing_backup_menu(slug: str, out_dir: Path, zip_path: Path) -> int:
    """Backup déjà présent : proposer la republication immédiate ou une sauvegarde fraîche."""
    meta = _zip_metadata(zip_path)
    created = (meta.get("created") or "?")[:16].replace("T", " ")
    title = meta.get("title") or slug
    posts = meta.get("posts_count", "?")
    pages = meta.get("pages_count", "?")
    media = meta.get("media_success", "?")
    theme = meta.get("theme") or "?"
    size = human_size(zip_path.stat().st_size)

    print(f"\n  Backup existant : {zip_path.name}")
    print(f"    {title} — {posts} articles, {pages} pages, {media} médias")
    print(f"    créé le {created} — thème {theme} — {size}")
    print("")
    print("  [1]  Republier ce backup  (rapide, aucun réseau)")
    print("  [2]  Sauvegarde fraîche   (re-scrape le blog)")
    print("  [3]  Quitter")
    print("")
    choice = _read("  Votre choix : ") or "1"
    if choice == "1":
        return republish_menu(str(zip_path))
    if choice == "2":
        force = _media_force_prompt()
        if not force:
            _reuse_media_from_zip(zip_path, out_dir, slug)
        result = run_backup(slug, out_dir, force=force)
        if result.get("error"):
            print(f"\n  ✗ Échec de la sauvegarde de « {slug} » : {result['error']}\n")
            return 1
        return _after_save(result.get("zip", ""))
    print("  Au revoir.")
    return 0


# ------------------------------------------------------------------- wizard

def interactive_wizard() -> int:
    _banner()
    plat = detect_platform()
    if plat == "tails":
        pers = Path.home() / "Persistent"
        if pers.is_dir():
            print("  Tails détecté — stockage persistant disponible.")
            print("  Vos sauvegardes survivront au redémarrage.")
            print("  Conseil : placez le dossier dans ~/Persistent")
        else:
            print("  Tails détecté — sauvegardez le .zip sur une clé USB")
            print("  avant d'éteindre (pas de stockage persistant).")
    else:
        print(f"  {plat[0].upper() + plat[1:]} détecté.")
    print("")
    print("  Votre slug NoBlogs : la partie avant .noblogs.org")
    print("  Ex. https://monblog.noblogs.org → monblog")
    print("")
    slug = _read("  Slug de votre blog : ")
    slug = slug_from_input(slug)
    if not slug:
        print("  ✗ Slug vide.")
        return 1
    out_dir = Path(os.getenv("NOBLOGS_OUT", str(DEFAULT_OUT)))
    zip_path = out_dir / f"{slug}-noblogs-backup.zip"

    if zip_path.exists():
        return _existing_backup_menu(slug, out_dir, zip_path)

    result = run_backup(slug, out_dir)
    if result.get("error"):
        print(f"\n  ✗ Échec de la sauvegarde de « {slug} » : {result['error']}\n")
        return 1
    return _after_save(result.get("zip", ""))


# ------------------------------------------------------------- republication

def _resolve_zip(raw: str) -> Path:
    p = Path(os.path.expanduser(raw))
    if not p.exists() and raw:
        rel = REPO_ROOT / raw
        if rel.exists():
            return rel
    return p


def _extract(zip_path: Path) -> str:
    tmp = tempfile.mkdtemp(prefix="noblogs-restore.")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(tmp)
    return tmp


def show_wpcom(zip_path: str, extracted: str | None = None) -> None:
    print(_guide("GUIDE-WORDPRESS-COM.md", extracted))
    if extracted:
        xml = Path(extracted) / "wordpress-export.xml"
        if xml.exists():
            print(f"\n  Fichier à importer sur WordPress.com : {xml}\n")


def show_local(zip_path: str, extracted: str | None = None) -> None:
    print(_guide("GUIDE-LOCAL.md", extracted))
    if extracted:
        restore = Path(extracted) / "restore.sh"
        if restore.exists():
            if detect_platform() == "windows":
                print("\n  Sur Windows, la restauration locale nécessite")
                print("  WSL/Linux ou un VPS. Utilisez plutôt WordPress.com.\n")
            else:
                print("\n  Lancement de l'assistant de restauration locale…\n")
                try:
                    subprocess.run(["bash", str(restore)], cwd=str(extracted), check=False)
                except FileNotFoundError:
                    print("  bash introuvable — lancez ./restore.sh manuellement.")


def republish_menu(zip_path: str | None = None) -> int:
    _banner()
    if not zip_path:
        zip_path = _read("  Chemin vers votre fichier .zip de sauvegarde\n"
                         "  (ex. backups/monblog-noblogs-backup.zip)\n  > ")
    p = _resolve_zip(zip_path or "")
    if not p.exists():
        print(f"  ✗ Fichier introuvable : {p}")
        return 1
    extracted = _extract(p)
    print(f"  Archive décompressée dans {extracted}\n")
    print("  Comment voulez-vous republier ?\n")
    print("  [1]  WordPress.com  (créer un site, importer — le plus simple)")
    print("  [2]  WordPress local (identique à l'original, via restore.sh)")
    print("  [3]  Afficher les guides")
    print("  [q]  Quitter\n")
    choice = _read("  Votre choix : ") or "1"
    if choice == "1":
        show_wpcom(str(p), extracted)
    elif choice == "2":
        show_local(str(p), extracted)
    elif choice == "3":
        for guide in GUIDES:
            print(_guide(guide, extracted))
            print("\n" + "─" * 40 + "\n")
    else:
        print("  Au revoir.")
        shutil.rmtree(extracted, ignore_errors=True)
        return 0
    shutil.rmtree(extracted, ignore_errors=True)
    return 0


# --------------------------------------------------------------------- help

def show_help() -> None:
    _banner()
    print("""  Commandes

    python -m backup wizard                 Assistant interactif (recommandé)
    python -m backup wizard sauvegarder S   Sauvegarde complète → backups/S-noblogs-backup.zip
    python -m backup wizard republier [Z]   Republication WordPress.com ou locale
    python -m backup wizard aide            Cette aide

  Lanceurs « 1 clic »
    ./noblogs            Tails, Ubuntu, macOS (terminal)
    noblogs.command      macOS (double-clic)
    noblogs.bat          Windows (double-clic)

  Prérequis
    Python 3 (auto-installé par le lanceur au premier usage)

  WordPress.com
    Créez un site sur wordpress.com, puis importez wordpress-export.xml
    (guide pas-à-pas inclus dans chaque archive).

  Version """ + __version__ + "\n")


def main(argv: list[str] | None = None) -> int:
    _utf8_console()
    args = list(argv) if argv is not None else sys.argv[1:]
    if not args:
        return interactive_wizard()
    cmd = args[0]
    rest = args[1:]
    if cmd in ("wizard", "start", "interactive"):
        return interactive_wizard()
    if cmd in ("sauvegarder", "backup", "save"):
        force = any(a in ("--force", "-f") for a in rest)
        pos = [a for a in rest if a not in ("--force", "-f")]
        if not pos:
            print("  ✗ Usage : python -m backup wizard sauvegarder SLUG [--force]")
            return 1
        slug = slug_from_input(pos[0])
        if not slug:
            print("  ✗ Slug vide.")
            return 1
        out_dir = Path(os.getenv("NOBLOGS_OUT", str(DEFAULT_OUT)))
        result = run_backup(slug, out_dir, force=force)
        if result.get("error"):
            print(f"  ✗ Échec : {result['error']}")
            return 1
        print(f"\n  Pour republier : python -m backup wizard republier {result['zip']}\n")
        return 0
    if cmd in ("republier", "restore", "publish"):
        return republish_menu(rest[0] if rest else None)
    if cmd in ("aide", "help", "-h", "--help"):
        show_help()
        return 0
    if cmd in ("version", "-V", "--version"):
        print(f"noblogs-backup {__version__}")
        return 0
    print(f"  ✗ Commande inconnue : {cmd}")
    show_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())