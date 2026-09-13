"""__main__.py — Point d'entrée CLI de noblogs-backup.

Usage :
    python -m backup <slug> [--base-url URL] [--out-dir DIR] [--no-wayback]
                       [--no-media] [--workers N] [--force]
"""
from __future__ import annotations

import argparse
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import __version__
from .fidelity import extract_fidelity
from .media import download_media
from .package import human_size, package_backup
from .scraper import NoblogsScraper, ScrapedBlog
from .theme_download import download_theme


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="noblogs-backup",
        description="Sauvegarde complète et autonome d'un blog NoBlogs (articles, pages, médias), "
                    "avec récupération automatique des médias disparus via archive.org.",
        epilog="Exemples :\n"
               "  python -m backup monblog\n"
               "  python -m backup monblog --out-dir ~/mes-sauvegardes\n"
               "  python -m backup monblog --base-url https://mirror.example.org",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("slugs", nargs="*", help="Slug(s) de blog, ex. monblog (ou fichier .txt liste).")
    p.add_argument("--base-url", "-b", help="URL de base alternative (défaut https://<slug>.noblogs.org).")
    p.add_argument("--out-dir", "-o", default="backups", help="Dossier de sortie des ZIP (défaut : ./backups).")
    p.add_argument("--no-wayback", action="store_true", help="Désactiver la récupération via archive.org / Wayback.")
    p.add_argument("--no-plugins", action="store_true", help="Ne pas embarquer les plugins NoBlogs dans le ZIP.")
    p.add_argument("--no-media", action="store_true", help="Ne pas télécharger les médias.")
    p.add_argument("--workers", "-j", type=int, default=6, help="Téléchargements médias simultanés (défaut 6).")
    p.add_argument("--keep-uploads", action="store_true", help="Conserver le dossier uploads à côté du ZIP.")
    p.add_argument("--force", action="store_true", help="Effacer et re-télécharger le dossier uploads existant.")
    p.add_argument("--unpack", action="store_true", help="Préserver le contenu déployé (uploads/ + XML) dans <out-dir>/<slug>/.")
    p.add_argument("--assets-cache", metavar="DIR", help="Dossier de cache du bundle thèmes/plugins (évite de re-télécharger).")
    p.add_argument("--version", action="version", version=f"noblogs-backup {__version__}")
    return p.parse_args(argv)


def _slug_from_arg(arg: str) -> str:
    arg = arg.strip()
    if arg.startswith(("http://", "https://")):
        host = arg.split("/")[2]
        return host.split(".")[0].strip().lower()
    return arg.strip().lower()


def backup_one(slug: str, args: argparse.Namespace) -> dict:
    print(f"\n=== Sauvegarde de {slug} ===", flush=True)
    out_root = Path(args.out_dir).expanduser()
    out_root.mkdir(parents=True, exist_ok=True)

    if getattr(args, "assets_cache", None):
        from .assets import set_cache_dir
        set_cache_dir(Path(args.assets_cache).expanduser())

    scraper = NoblogsScraper(slug, base_url=args.base_url)
    scraped: ScrapedBlog = scraper.scrape_all()
    posts = scraped.posts
    pages = scraped.pages
    print(f"  {len(posts)} articles, {len(pages)} pages", flush=True)

    if not posts and not pages:
        print(
            f"\n  ❌ ERREUR : aucun contenu trouvé pour « {slug} ».\n"
            f"     Vérifiez le slug (ex. monblog pour monblog.noblogs.org).\n"
            f"     Astuce : si le blog est mort, la récupération archive.org est\n"
            f"     activée par défaut — ne lancez pas avec --no-wayback.",
            flush=True,
        )
        return {"slug": slug, "zip": "", "size": "", "error": "empty"}

    # --- médias
    uploads_dir = out_root / slug / "uploads"
    media_stats: dict = {"urls": 0, "direct": 0, "wayback": 0, "wayback-api": 0, "failed": 0, "skipped": 0}
    if not args.no_media:
        print("Extraction des URLs de médias…", flush=True)
        media_urls = scraper.extract_all_media(posts, pages)
        print(f"  {len(media_urls)} médias détectés", flush=True)
        if media_urls:
            if args.force and uploads_dir.exists():
                shutil.rmtree(uploads_dir)
            media_stats = download_media(
                media_urls,
                uploads_dir,
                use_wayback=not args.no_wayback,
                workers=args.workers,
            )
            success = sum(v for k, v in media_stats.items() if k != "failed")
            print(f"  Médias : {success} ok / {media_stats.get('failed', 0)} échecs", flush=True)
            media_stats["urls"] = len(media_urls)
    else:
        print("Téléchargement des médias désactivé (--no-media).", flush=True)
        uploads_dir.mkdir(parents=True, exist_ok=True)

    # --- WXR (+ pièces jointes pour les médias téléchargés)
    print("Génération de l'export WXR 1.2…", flush=True)
    stage_dir = out_root / slug
    stage_dir.mkdir(parents=True, exist_ok=True)
    from .media import relative_dest
    from .wxr import write_wxr
    attachments = []
    if not args.no_media and media_urls:
        for u in media_urls:
            rel = relative_dest(u)
            local = uploads_dir / rel
            if local.exists() and local.stat().st_size > 0:
                attachments.append({
                    "url": u,
                    "path": rel,
                    "title": rel.split("/")[-1],
                })
    wxr_path = write_wxr(
        stage_dir / "wordpress-export.xml",
        slug=slug,
        title=scraped.title,
        site_url=scraped.base_url,
        posts=posts,
        pages=pages,
        attachments=attachments,
    )

    # --- Fidélité visuelle (theme, sidebars, menus, CSS, couleurs, bannière)
    print("Extraction de la fidélité visuelle (widgets, menus, CSS, couleurs)…", flush=True)
    fidelity = extract_fidelity(slug, scraped.base_url, scraped.theme, stage_dir)
    if fidelity.get("error"):
        print(f"  Fidélité partielle : {fidelity['error']}", flush=True)

    # --- Téléchargement du thème
    print("Téléchargement du thème…", flush=True)
    theme_dir = None
    theme_slug = fidelity.get("theme") or scraped.theme
    if theme_slug:
        theme_dir = download_theme(
            theme_slug,
            scraped.base_url,
            stage_dir / "theme",
            use_wayback=not args.no_wayback,
        )

    # --- Plugins NoBlogs + mu-plugins + wplang (miroir github.com/muarf/noblogs-assets)
    from .assets import bundle_mu_plugins, bundle_plugins, bundle_wplang

    plugins_dir = None
    mu_plugins_dir = None
    wplang_dir = None
    if not args.no_plugins:
        print("Embarquement des plugins NoBlogs…", flush=True)
        plugins_dir = bundle_plugins(dest_dir=stage_dir)
        mu_plugins_dir_path = Path(stage_dir) / "mu-plugins"
        mu_plugins_dir_path.mkdir(parents=True, exist_ok=True)
        if bundle_mu_plugins(dest_dir=mu_plugins_dir_path):
            mu_plugins_dir = mu_plugins_dir_path
        wplang_dir = bundle_wplang(dest_dir=Path(stage_dir) / "wplang")
        if plugins_dir is not None:
            print(f"  {len(list(plugins_dir.iterdir()))} plugins embarqués", flush=True)

    # --- ZIP
    zip_file = package_backup(
        slug=slug,
        exports_dir=out_root,
        wxr_path=wxr_path,
        uploads_dir=stage_dir / "uploads",
        original_url=scraped.base_url,
        title=fidelity.get("title") or scraped.title,
        theme=theme_slug,
        posts_count=len(posts),
        pages_count=len(pages),
        media_stats=media_stats,
        fidelity=fidelity,
        theme_dir=theme_dir,
        plugins_dir=plugins_dir,
        mu_plugins_dir=mu_plugins_dir,
        wplang_dir=wplang_dir,
    )
    size = human_size(zip_file.stat().st_size)

    if not args.keep_uploads:
        shutil.rmtree(stage_dir / "uploads", ignore_errors=True)
    if not args.unpack:
        for sub in ("fidelity_media", "theme", "plugins", "mu-plugins", "wplang"):
            shutil.rmtree(stage_dir / sub, ignore_errors=True)
        for f in stage_dir.iterdir():
            if f.name != "uploads":
                if f.is_dir():
                    shutil.rmtree(f, ignore_errors=True)
                else:
                    f.unlink(missing_ok=True)

    print(f"  ✅ Archive créée : {zip_file} ({size})", flush=True)
    return {"slug": slug, "zip": str(zip_file), "size": size}


def main(argv: list[str] | None = None) -> int:
    args_list = list(argv) if argv is not None else sys.argv[1:]
    if args_list and args_list[0] == "wizard":
        from . import wizard
        return wizard.main(args_list[1:])

    args = parse_args(args_list)
    if not args.slugs:
        print("Erreur : au moins un slug est requis.", file=sys.stderr)
        print("Usage : python -m backup <slug> [options]", file=sys.stderr)
        return 2

    slugs: list[str] = []
    for arg in args.slugs:
        if arg.endswith(".txt") and Path(arg).exists():
            slugs.extend(_slug_from_arg(line) for line in Path(arg).read_text().splitlines() if line.strip())
        else:
            slugs.append(_slug_from_arg(arg))

    results = []
    if len(slugs) > 1:
        with ThreadPoolExecutor(max_workers=min(len(slugs), 3)) as ex:
            for result in ex.map(lambda s: backup_one(s, args), slugs):
                results.append(result)
    else:
        results.append(backup_one(slugs[0], args))

    print("\n=== BILAN ===")
    failed = False
    for r in results:
        if r.get("error"):
            print(f"  ❌ {r['slug']}: ÉCHEC — {r['error']}")
            failed = True
        else:
            print(f"  ✅ {r['slug']}: {r['zip']} ({r['size']})")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())