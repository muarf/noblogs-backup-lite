"""theme_download.py — Téléchargement du thème WordPress actif.

Stratégie :
1. Miroir git NoBlogs (``github.com/muarf/noblogs-assets``) — thèmes nobles,
   legacy ET officiels WP, récupérés avant la fermeture d'Autistici/Inventati.
   Version exacte du blog, autonome (aucune dépendance à WordPress.org).
2. Thème officiel WP absent du miroir → API WordPress.org.
3. Blog d'origine → crawl du fichier style.css.
4. Fallback → archive.org.

Le résultat est un dossier ``theme/<slug>/`` prêt à être placé dans ``wp-content/themes/``.
"""
from __future__ import annotations

import io
import os
import re
import tempfile
import zipfile
from pathlib import Path

from .i18n import t
from .http import fetch_url

# Thèmes officiels WordPress (connus pour les blogs NoBlogs)
WP_OFFICIAL_THEMES = {
    "twentyten", "twentyeleven", "twentytwelve", "twentythirteen",
    "twentyfourteen", "twentyfifteen", "twentysixteen", "twentyseventeen",
    "twentyeighteen", "twentynineteen", "twentytwenty", "twentytwentyone",
    "twentytwentytwo", "twentytwentythree", "twentytwentyfour",
    "twentytwentyfive",
}

# Miroir git des thèmes/plugins NoBlogs (avant mise hors-ligne d'Autistici).
NOBLOGS_ASSETS_GIT = "https://raw.githubusercontent.com/muarf/noblogs-assets/main"


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

    # 0. Miroir git NoBlogs (thème complet — templates PHP inclus),
    #    pour TOUS les thèmes, y compris les officiels WP : version exacte
    #    du blog, auto-hébergée, pas de dépendance à WordPress.org.
    ok = _download_from_noblogs_git(theme_slug, dest_dir)
    if ok:
        print(t("  [thème] {} téléchargé depuis le miroir NoBlogs Git").format(theme_slug))
        return theme_dir

    # 1. Thème officiel WP absent du miroir → API WordPress.org
    if theme_slug in WP_OFFICIAL_THEMES:
        ok = _download_official(theme_slug, dest_dir)
        if ok:
            print(t("  [thème] {} téléchargé depuis WordPress.org").format(theme_slug))
            return theme_dir

    # 2. Téléchargement direct depuis le blog d'origine (style.css brut)
    ok = _download_from_site(theme_slug, base_url, dest_dir, use_wayback=use_wayback)
    if ok:
        print(t("  [thème] {} téléchargé depuis {}").format(theme_slug, base_url))
        return theme_dir

    # 3. Fallback archive.org
    if use_wayback:
        ok = _download_from_wayback(theme_slug, base_url, dest_dir)
        if ok:
            print(t("  [thème] {} récupéré depuis archive.org").format(theme_slug))
            return theme_dir

    print(t("  [thème] {} introuvable — fallback sur thème standard.").format(theme_slug))
    return None


def _download_from_noblogs_git(theme_slug: str, dest_dir: Path) -> bool:
    """Télécharge un thème depuis le miroir github.com/muarf/noblogs-assets.

    Le thème est présent en entier (style.css + templates PHP) dans
    ``themes/<slug>/``. On privilégie le bundle ZIP mis en cache par
    ``assets.py`` (une seule requête HTTP) ; en dernier recours, on liste
    les fichiers via l'API GitHub et on les télécharge un par un en raw.
    """
    # 1) Bundled ZIP (déjà téléchargé par assets.py, ou download frais)
    from .assets import _bundle_zip

    body = _bundle_zip()
    if body is not None:
        import io as _io
        import zipfile as _zipfile
        try:
            with _zipfile.ZipFile(_io.BytesIO(body)) as zf:
                root = next(
                    (n for n in zf.namelist() if n.endswith(f"themes/{theme_slug}/")),
                    None,
                )
                if root is not None:
                    theme_dir = dest_dir / theme_slug
                    theme_dir.mkdir(parents=True, exist_ok=True)
                    prefix = root
                    count = 0
                    for name in zf.namelist():
                        if name.startswith(prefix) and not name.endswith("/"):
                            rel = name[len(prefix):]
                            target = theme_dir / rel
                            target.parent.mkdir(parents=True, exist_ok=True)
                            target.write_bytes(zf.read(name))
                            count += 1
                    return count > 0
        except Exception:
            pass

    # 2) API GitHub (liste l'arbre puis télécharge en raw)
    api = f"https://api.github.com/repos/muarf/noblogs-assets/git/trees/main?recursive=1"
    st, body = fetch_url(api, timeout=60)
    if st != 200 or not body:
        return False
    import json
    try:
        tree = json.loads(body.decode("utf-8", "replace")).get("tree", [])
    except Exception:
        return False
    prefix = f"themes/{theme_slug}/"
    files = [e["path"] for e in tree if e["type"] == "blob" and e["path"].startswith(prefix)]
    if not files:
        return False
    theme_dir = dest_dir / theme_slug
    theme_dir.mkdir(parents=True, exist_ok=True)
    ok = False
    for path in files:
        raw_url = f"{NOBLOGS_ASSETS_GIT}/{path}"
        st_r, data = fetch_url(raw_url, timeout=60)
        if st_r == 200 and data:
            rel = path[len(prefix):]
            target = theme_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            ok = True
    return ok


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