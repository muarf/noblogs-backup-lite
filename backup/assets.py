"""assets.py — Les thèmes, plugins et mu-plugins NoBlogs emportés dans le backup.

Le collectif NoBlogs/Varia publie son `wp-content` (thèmes, plugins, mu-plugins)
sur `git.inventati.org` ; l'infrastructure Autistici a été mise hors-ligne en
2026. Un miroir de sauvegarde est hébergé sur GitHub (`muarf/noblogs-assets`).

Ce module télécharge ce bundle compacté (une seule requête HTTP), le met en
cache local, et le restitue sous forme de dossier ``plugins/``, ``mu-plugins/``,
``themes/<slug>/`` ou ``wplang/``.
"""
from __future__ import annotations

import io
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

from .http import fetch_url

# Miroir git des thèmes/plugins NoBlogs (avant mise hors-ligne d'Autistici).
NOBLOGS_ASSETS_URL = "https://codeload.github.com/muarf/noblogs-assets/zip/refs/heads/main"

# Liste fixe de plugins NoBlogs toujours incluse dans le ZIP de sauvegarde.
# Liste exhaustive des plugins de la plateforme (issue de noblogs-wp + ai-*).
NOBLOGS_PLUGINS = [
    "akismet", "autopost-to-mastodon", "bogo", "buddypress-ai-plugin",
    "buddypress", "classic-editor", "creative-commons-license-widget",
    "disable-comments", "dvk-social-sharing", "eu-compliance", "event-list",
    "exclude-plugins", "feedwordpress", "footnotation", "i-love-xm24-ribbon",
    "mathjax-latex", "nextgen-gallery", "nofollow-free", "nospam",
    "oembed-provider", "pubsubhubbub", "rss-license", "simply-exclude",
    "soundcloud-shortcode", "squat-radar-calendar-integration", "two-factor",
    "video-sidebar-widgets", "wordpress-ai-privacy-plugin", "wordpress-importer",
    "wp-footnotes", "wp-piwik", "wp-recaptcha-bp", "wp-statusnet",
    "wp-super-cache", "wp-syntax", "wp2pgpmail", "wpmu-custom-css",
    "ai-buddypress-plugin", "ai-global-activity", "ai-authenticate-rest-api",
    "ai-simplesitestats", "login-limiter",
]

_cache_dir: Path | None = None


def set_cache_dir(path: Path | None) -> None:
    """Permet de rediriger le cache du bundle en cas de test (None = reset)."""
    global _cache_dir
    _cache_dir = Path(path) if path is not None else None


def _bundle_zip() -> bytes | None:
    """Télécharge (ou réutilise en cache) le bundle compacté des assets NoBlogs."""
    if _cache_dir is not None and (_cache_dir / "noblogs-assets.zip").exists():
        return (_cache_dir / "noblogs-assets.zip").read_bytes()
    st, body = fetch_url(NOBLOGS_ASSETS_URL, timeout=180)
    if st != 200 or not body:
        return None
    if _cache_dir is not None:
        _cache_dir.mkdir(parents=True, exist_ok=True)
        (_cache_dir / "noblogs-assets.zip").write_bytes(body)
    return body


def _extract(
    bundle_dir: Path,
    source: str,
    dest_dir: Path,
    slugs: list[str] | None = None,
) -> int:
    """Extrait ``source`` (plugins/, mu-plugins/, themes/, wplang/) du bundle.

    Retourne le nombre de dossiers extraits.
    """
    src_root = bundle_dir / source
    if not src_root.exists():
        return 0
    items = [d for d in src_root.iterdir() if d.is_dir()]
    if slugs is not None:
        items = [d for d in items if d.name in slugs]
    dest_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for d in items:
        target = dest_dir / d.name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(d, target)
        count += 1
    return count


def bundle_plugins(slugs: list[str] | None = None, dest_dir: Path | None = None) -> Path | None:
    """Retourne le dossier ``plugins/`` (cache ou extraction du bundle).

    Si ``dest_dir`` est fourni, les plugins y sont extraits et le dossier est
    retourné. Sinon, on crée/sert un cache temporel persistant.
    """
    supported = set(NOBLOGS_PLUGINS)
    wanted = [s for s in (slugs or NOBLOGS_PLUGINS) if s in supported]
    if not wanted:
        return None
    if dest_dir is None:
        if _cache_dir is not None:
            dest_dir = _cache_dir / "plugins"
        else:
            dest_dir = Path(tempfile.mkdtemp(prefix="noblogs_assets_")) / "plugins"
    dest_dir = Path(dest_dir)
    plugins_dir = dest_dir if dest_dir.name == "plugins" else dest_dir / "plugins"
    if all((plugins_dir / s).is_dir() for s in wanted):
        return plugins_dir
    body = _bundle_zip()
    if body is None:
        return None
    with tempfile.TemporaryDirectory(prefix="noblogs_assets_extract_") as tmp:
        with zipfile.ZipFile(io.BytesIO(body)) as zf:
            zf.extractall(tmp)
        root = Path(tmp)
        bundle_dir = next(d for d in root.iterdir() if d.is_dir())
        _extract(bundle_dir, "plugins", plugins_dir, wanted)
    if all((plugins_dir / s).is_dir() for s in wanted):
        return plugins_dir
    return None


def bundle_mu_plugins(dest_dir: Path | None = None) -> list[Path]:
    """Extrait les mu-plugins (fichiers PHP/CSS/JS) dans ``dest_dir``."""
    if dest_dir is None:
        if _cache_dir is not None:
            dest_dir = _cache_dir / "mu-plugins"
        else:
            dest_dir = Path(tempfile.mkdtemp(prefix="noblogs_assets_")) / "mu-plugins"
    dest_dir = Path(dest_dir)
    if any(dest_dir.glob("*")):
        return sorted(p for p in dest_dir.iterdir() if p.is_file())
    body = _bundle_zip()
    if body is None:
        return []
    with tempfile.TemporaryDirectory(prefix="noblogs_assets_extract_") as tmp:
        with zipfile.ZipFile(io.BytesIO(body)) as zf:
            zf.extractall(tmp)
        root = Path(tmp)
        bundle_dir = next(d for d in root.iterdir() if d.is_dir())
        src = bundle_dir / "mu-plugins"
        dest_dir.mkdir(parents=True, exist_ok=True)
        if src.exists():
            for f in src.iterdir():
                if f.is_file():
                    shutil.copy2(f, dest_dir / f.name)
    return sorted(p for p in dest_dir.iterdir() if p.is_file())


def bundle_wplang(dest_dir: Path | None = None) -> Path | None:
    """Extrait ``wplang/`` (strings de traduction multi-blogs)."""
    if dest_dir is None:
        if _cache_dir is not None:
            dest_dir = _cache_dir / "wplang"
        else:
            dest_dir = Path(tempfile.mkdtemp(prefix="noblogs_assets_")) / "wplang"
    dest_dir = Path(dest_dir)
    if dest_dir.exists() and any(dest_dir.iterdir()):
        return dest_dir
    body = _bundle_zip()
    if body is None:
        return None
    with tempfile.TemporaryDirectory(prefix="noblogs_assets_extract_") as tmp:
        with zipfile.ZipFile(io.BytesIO(body)) as zf:
            zf.extractall(tmp)
        root = Path(tmp)
        bundle_dir = next(d for d in root.iterdir() if d.is_dir())
        src = bundle_dir / "wplang"
        if not src.exists():
            return None
        shutil.copytree(src, dest_dir)
    return dest_dir


def list_available_plugins() -> list[str]:
    """Plugins réellement présents dans le bundle (ou la liste fixe)."""
    with tempfile.TemporaryDirectory(prefix="noblogs_assets_list_") as tmp:
        found = bundle_plugins(dest_dir=Path(tmp))
    if found is not None:
        return sorted(d.name for d in found.iterdir() if d.is_dir())
    return NOBLOGS_PLUGINS