"""package.py — Emballage de la sauvegarde en ZIP autonome complet.

Produit une archive qui contient tout le blog NoBlogs :
* ``wordpress-export.xml``  – export WXR 1.2 (articles, pages, catégories)
* ``uploads/``              – tous les médias
* ``theme/<theme>/``        – le thème WordPress actif
* ``plugins/``, ``mu-plugins/``, ``wplang/`` — les plugins NoBlogs
* ``fidelity.json``         – sidebars, menus, CSS, couleurs, header image
* ``README.md``, ``metadata.json``
"""
from __future__ import annotations

import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from .i18n import t


def human_size(num: int) -> str:
    for unit in ["o", "Ko", "Mo", "Go", "To"]:
        if num < 1024:
            return f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} To"


def _write_readme(
    stage: Path,
    slug: str,
    original_url: str,
    has_fidelity: bool,
    has_theme: bool,
    has_plugins: bool = False,
) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    fidelity_note = ""
    if has_fidelity:
        fidelity_note = t("- **`fidelity.json`** — sidebars, menus, CSS personnalisé, couleurs, bannière (fidélité visuelle).\n")
    theme_note = ""
    if has_theme:
        theme_note = t("- **`theme/`** — le thème WordPress actif du blog original.\n")
    plugins_note = ""
    if has_plugins:
        plugins_note = t("- **`plugins/`** — les plugins NoBlogs (nospam, classic-editor, …), avec `mu-plugins/` et `wplang/`.\n")

    readme_text = t("""# Sauvegarde NoBlogs — {slug}

Export complet du blog **{slug}**, réalisé le {now}.
Source : {original_url}

## Contenu
* **`wordpress-export.xml`** — export WXR 1.2 (articles, pages, catégories), compatible WordPress.
* **`uploads/`** — tous les médias, avec la structure de dossiers de l'original.
{fidelity_note}{theme_note}{plugins_note}* **`metadata.json`** — informations sur la sauvegarde.

L'export Wordpress est réimplantable sur n'importe quelle instance WordPress
(*Outils > Importer > WordPress*), et `uploads/` se replacent dans
`wp-content/uploads/`.
""").format(
        slug=slug,
        now=now,
        original_url=original_url,
        fidelity_note=fidelity_note,
        theme_note=theme_note,
        plugins_note=plugins_note
    )
    (stage / "README.md").write_text(readme_text, encoding="utf-8")


def package_backup(
    slug: str,
    exports_dir: Path,
    wxr_path: Path,
    uploads_dir: Path,
    original_url: str,
    title: str | None = None,
    theme: str | None = None,
    posts_count: int = 0,
    pages_count: int = 0,
    media_stats: dict | None = None,
    fidelity: dict | None = None,
    theme_dir: Path | None = None,
    plugins_dir: Path | None = None,
    mu_plugins_dir: Path | None = None,
    wplang_dir: Path | None = None,
) -> Path:
    """Crée l'archive ZIP finale et retourne son chemin."""
    media_stats = media_stats or {}
    fidelity = fidelity or {}
    exports_dir.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f"noblogs_backup_{slug}_"))
    zip_file = exports_dir / f"{slug}-noblogs-backup.zip"
    try:
        # 1. WXR
        (stage / "wordpress-export.xml").write_bytes(wxr_path.read_bytes())

        # 2. Médias
        if uploads_dir.exists() and any(uploads_dir.iterdir()):
            shutil.copytree(uploads_dir, stage / "uploads", dirs_exist_ok=True)

        # 3. Thème
        has_theme = False
        if theme_dir is not None and theme_dir.exists() and any(theme_dir.iterdir()):
            shutil.copytree(theme_dir, stage / "theme" / theme_dir.name, dirs_exist_ok=True)
            has_theme = True

        # 3bis. Plugins NoBlogs + mu-plugins + wplang
        if plugins_dir is not None and plugins_dir.exists() and any(plugins_dir.iterdir()):
            shutil.copytree(plugins_dir, stage / "plugins", dirs_exist_ok=True)
        if mu_plugins_dir is not None and mu_plugins_dir.exists() and any(mu_plugins_dir.iterdir()):
            shutil.copytree(mu_plugins_dir, stage / "mu-plugins", dirs_exist_ok=True)
        if wplang_dir is not None and wplang_dir.exists() and any(wplang_dir.iterdir()):
            shutil.copytree(wplang_dir, stage / "wplang", dirs_exist_ok=True)

        # 4. Fidélité : JSON + scripts + médias fidélité
        has_fidelity = bool(fidelity)
        media_src = wxr_path.parent / "fidelity_media"
        if fidelity:
            (stage / "fidelity.json").write_text(
                __import__("json").dumps(fidelity, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            if media_src.exists() and any(media_src.iterdir()):
                shutil.copytree(media_src, stage / "fidelity_media", dirs_exist_ok=True)

        # 5. README + métadonnées
        has_plugins = bool(plugins_dir and plugins_dir.exists() and any(plugins_dir.iterdir()))
        _write_readme(stage, slug, original_url, has_fidelity, has_theme, has_plugins=has_plugins)

        media_success = sum(v for k, v in media_stats.items() if k not in ("failed", "urls"))
        (stage / "metadata.json").write_text(
            __import__("json").dumps(
                {
                    "slug": slug,
                    "title": title,
                    "theme": theme,
                    "original_url": original_url,
                    "created": datetime.now().isoformat(),
                    "posts_count": posts_count,
                    "pages_count": pages_count,
                    "media": media_stats,
                    "media_success": media_success,
                    "fidelity": bool(fidelity),
                    "theme_bundled": has_theme,
                    "plugins_bundled": has_plugins,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        # 6. Compression ZIP
        if zip_file.exists():
            zip_file.unlink()
        with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for f in sorted(stage.rglob("*")):
                if f.is_file():
                    zf.write(f, f.relative_to(stage))
        return zip_file
    finally:
        shutil.rmtree(stage, ignore_errors=True)