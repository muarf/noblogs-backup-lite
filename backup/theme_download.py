"""theme_download.py — Téléchargement du thème WordPress actif.

Stratégie :
1. Si le thème est un thème standard WP (twentyten..twentytwentyone) → API WordPress.org.
2. Si le thème est sur le blog d'origine → crawl du fichier style.css (page style.css裸).
3. Fallback → archive.org.

Le résultat est un dossier ``theme/<slug>/`` prêt à être placé dans ``wp-content/themes/``.
"""
from __future__ import annotations

import io
import os
import re
import tempfile
import zipfile
from pathlib import Path

from .http import fetch_url

# Thèmes officiels WordPress ( connus pour les blogs NoBlogs)
WP_OFFICIAL_THEMES = {
    "twentyten", "twentyeleven", "twentytwelve", "twentythirteen",
    "twentyfourteen", "twentyfifteen", "twentysixteen", "twentyseventeen",
    "twentyeighteen", "twentynineteen", "twentytwenty", "twentytwentyone",
    "twentytwentytwo", "twentytwentythree", "twentytwentyfour",
}


def download_theme(
    theme_slug: str,
    base_url: str,
    dest_dir: Path,
    use_wayback: bool = True,
) -> Path | None:
    """Télécharge le thème dans ``dest_dir/<theme_slug>/``.

    Retourne le chemin du dossier thème si succès, sinon None.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    theme_dir = dest_dir / theme_slug

    # 1. Thème officiel WP → API WordPress.org
    if theme_slug in WP_OFFICIAL_THEMES:
        ok = _download_official(theme_slug, dest_dir)
        if ok:
            print(f"  [thème] {theme_slug} téléchargé depuis WordPress.org")
            return theme_dir

    # 2. Téléchargement direct depuis le blog d'origine (style.css brut)
    ok = _download_from_site(theme_slug, base_url, dest_dir, use_wayback=use_wayback)
    if ok:
        print(f"  [thème] {theme_slug} téléchargé depuis {base_url}")
        return theme_dir

    # 3. Fallback archive.org
    if use_wayback:
        ok = _download_from_wayback(theme_slug, base_url, dest_dir)
        if ok:
            print(f"  [thème] {theme_slug} récupéré depuis archive.org")
            return theme_dir

    print(f"  [thème] {theme_slug} introuvable — fallback sur thème standard.")
    return None


def _download_official(theme_slug: str, dest_dir: Path) -> bool:
    """Télécharge un thème officiel WP depuis l'API WordPress.org."""
    api_url = f"https://api.wordpress.org/themes/info/1.2/?action=theme_information&slug={theme_slug}"
    st, body = fetch_url(api_url, timeout=30)
    if st != 200 or not body:
        return False
    import json
    try:
        info = json.loads(body.decode("utf-8", "replace"))
    except Exception:
        return False
    download_url = info.get("download_link")
    if not download_url:
        return False
    return _extract_zip(download_url, dest_dir)


def _download_from_site(theme_slug: str, base_url: str, dest_dir: Path, use_wayback: bool = True) -> bool:
    """Tente de récupérer style.css (minimum vital) depuis le blog d'origine."""
    urls = [
        f"{base_url}/wp-content/themes/{theme_slug}/style.css",
        f"{base_url}/wp-content/themes/{theme_slug}/index.php",
    ]
    theme_dir = dest_dir / theme_slug
    theme_dir.mkdir(parents=True, exist_ok=True)
    got_any = False
    for url in urls:
        st, data = fetch_url(url, timeout=20)
        if st == 200 and data:
            fname = url.split("/")[-1]
            (theme_dir / fname).write_bytes(data)
            got_any = True
        elif use_wayback:
            wb_url = f"https://web.archive.org/web/2025id_/{url}"
            st_wb, data_wb = fetch_url(wb_url, timeout=30)
            if st_wb == 200 and data_wb and b"<html" not in data_wb[:300].lower():
                fname = url.split("/")[-1]
                (theme_dir / fname).write_bytes(data_wb)
                got_any = True
    return got_any


def _download_from_wayback(theme_slug: str, base_url: str, dest_dir: Path) -> bool:
    """Dernier recours : récupère le dossier thème complet via Wayback."""
    wb_url = f"https://web.archive.org/web/2025id_/{base_url}/wp-content/themes/{theme_slug}/style.css"
    st, data = fetch_url(wb_url, timeout=30)
    if st == 200 and data and b"<html" not in data[:300].lower():
        theme_dir = dest_dir / theme_slug
        theme_dir.mkdir(parents=True, exist_ok=True)
        (theme_dir / "style.css").write_bytes(data)
        return True
    return False


def _extract_zip(url: str, dest_dir: Path) -> bool:
    """Télécharge un ZIP et l'extract dans dest_dir."""
    st, data = fetch_url(url, timeout=60)
    if st != 200 or not data:
        return False
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            zf.extractall(dest_dir)
        return True
    except Exception:
        return False