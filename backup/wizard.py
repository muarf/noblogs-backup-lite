"""wizard.py — Assistant interactif minimal de noblogs-backup-lite.

Point d'entrée unique utilisé par ``./noblogs`` :
* ``./noblogs``            → assistant interactif (sauvegarde seule)
* ``./noblogs sauvegarder S`` → sauvegarde directe
* ``./noblogs aide``           → aide rapide
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path

from . import __version__
from .__main__ import backup_one
from .package import human_size

DEFAULT_OUT = Path(__file__).resolve().parent.parent / "backups"


def _utf8_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def detect_platform() -> str:
    if os.path.exists("/etc/amnesia") or os.getenv("TAILS_VERSION"):
        return "tails"
    if sys.platform == "darwin":
        return "macos"
    if os.name == "nt":
        return "windows"
    return "linux"


from urllib.parse import urlparse

def slug_from_input(raw: str) -> str:
    raw = (raw or "").strip()
    if raw.startswith(("http://", "https://")):
        raw = urlparse(raw).netloc
    raw = raw.split("/")[0].split("?")[0]
    # Strip common domains if present, otherwise just use the first part of the domain as slug
    raw = raw.lower()
    for suffix in (".noblogs.org", ".wordpress.com"):
        if raw.endswith(suffix):
            raw = raw[: -len(suffix)]
            break
    if "." in raw:
        raw = raw.split(".")[0]
    return raw.strip().replace(" ", "")


def _read(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def _banner() -> None:
    print("")
    print("  ╔═══════════════════════════════════════════════╗")
    print("  ║   NoBlogs Backup — sauvegarde                 ║")
    print("  ╚═══════════════════════════════════════════════╝")
    print("")


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
    """Lance la sauvegarde complète et retourne le résultat de backup_one."""
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nSauvegarde de « {slug} » en cours…\n", flush=True)
    return backup_one(slug, _backup_args(slug, out_dir, force=force))


def _zip_metadata(zip_path: Path) -> dict:
    try:
        with zipfile.ZipFile(zip_path) as zf:
            return json.loads(zf.read("metadata.json").decode("utf-8"))
    except Exception:
        return {}


def _media_force_prompt() -> bool:
    print("")
    print("  Médias déjà téléchargés : réutiliser par défaut, forcer pour re-télécharger.")
    choice = _read("  [r]éutiliser / [f]orcer le re-téléchargement [r] : ").strip().lower()
    return choice.startswith("f")


def _reuse_media_from_zip(zip_path: Path, out_dir: Path, slug: str) -> None:
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


def _existing_backup_menu(slug: str, out_dir: Path, zip_path: Path) -> int:
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
    print("  [1]  Sauvegarde fraîche (re-scrape le blog)")
    print("  [2]  Quitter")
    print("")
    choice = _read("  Votre choix : ") or "1"
    if choice == "1":
        force = _media_force_prompt()
        if not force:
            _reuse_media_from_zip(zip_path, out_dir, slug)
        result = run_backup(slug, out_dir, force=force)
        if result.get("error"):
            print(f"\n  ✗ Échec de la sauvegarde de « {slug} » : {result['error']}\n")
            return 1
        zip_file = result.get("zip", "")
        if zip_file and Path(zip_file).exists():
            print(f"\n  Sauvegarde terminée !\n  Archive : {zip_file}\n")
        return 0
    print("  Au revoir.")
    return 0


def interactive_wizard() -> int:
    _banner()
    plat = detect_platform()
    if plat == "tails":
        pers = Path.home() / "Persistent"
        if pers.is_dir():
            print("  Tails détecté — stockage persistant disponible.")
            print("  Vos sauvegardes survivront au redémarrage.")
        else:
            print("  Tails détecté — sauvegardez le .zip sur une clé USB")
            print("  avant d'éteindre (pas de stockage persistant).")
    else:
        print(f"  {plat[0].upper() + plat[1:]} détecté.")
    print("")
    print("  Le slug de votre blog : la première partie de l'adresse")
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
    zip_file = result.get("zip", "")
    if zip_file and Path(zip_file).exists():
        print(f"\n  Sauvegarde terminée !\n  Archive : {zip_file}\n")
    return 0


def show_help() -> None:
    _banner()
    print(f"""  Commandes

    ./noblogs                      Assistant interactif
    ./noblogs sauvegarder SLUG     Sauvegarde complète → backups/SLUG-noblogs-backup.zip
    ./noblogs aide                 Cette aide

  Prérequis
    Python 3 (auto-installé par le lanceur au premier usage)

  Version {__version__}
""")


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
            print("  ✗ Usage : ./noblogs sauvegarder SLUG [--force]")
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
        zip_file = result.get("zip", "")
        if zip_file and Path(zip_file).exists():
            print(f"\n  Sauvegarde terminée !\n  Archive : {zip_file}\n")
        return 0
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
    sys.exit(main())
