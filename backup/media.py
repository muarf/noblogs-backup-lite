"""media.py — Téléchargement des médias d'un blog, avec fallback archive.org.

Stratégie pour chaque URL :
1. Téléchargement direct depuis le site d'origine (noblogs.org).
2. Si échec → interrogations du site mort : snapshot Wayback Machine
   ``web.archive.org/web/<timestamp>id_/<url>``.
3. Si échec → API ``archive.org/wayback/available`` pour trouver le snapshot.

Les fichiers déjà présents (>100 octets) sont ignorés (reprisable).
"""
from __future__ import annotations

import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from .i18n import t
from .http import fetch_url

_HTML_ERROR = re.compile(rb"\s*<html", re.I)

# Horodatage « maintenant » pour la Wayback : <AAAA><MM><JJ><HH><MM><SS>
# = snapshot le plus récent à l'instant du backup (plutôt que figé à une date).
def _now_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")


def relative_dest(url: str) -> str:
    """Mappe une URL vers un chemin relatif sous uploads/."""
    m = re.search(r"/files/(.*)$", url)
    if not m:
        m_up = re.search(r"/uploads/(.*)$", url)
        rel = m_up.group(1) if m_up else os.path.basename(url)
    else:
        rel = m.group(1)
    rel = rel.split("?")[0].split("#")[0].lstrip("/")
    # Sécurité : neutraliser toute tentative de sortie du dossier uploads.
    parts = [p for p in rel.split("/") if p not in ("", ".", "..")]
    return "/".join(parts)


def wayback_available(url: str) -> tuple[str | None, str | None]:
    """Interroge l'API Wayback et retourne (snapshot_url, timestamp)."""
    try:
        st, body = fetch_url(f"http://archive.org/wayback/available?url={url}", timeout=30)
        if st == 200 and body:
            import json
            data = json.loads(body.decode("utf-8", "replace"))
            snap = data.get("archived_snapshots", {}).get("closest", {})
            if snap and snap.get("available"):
                return snap.get("url"), snap.get("timestamp")
    except Exception:
        pass
    return None, None


def download_one(url: str, dest: Path, use_wayback: bool = True) -> str:
    """Télécharge une URL dans ``dest``. Retourne un statut textuel."""
    if dest.exists() and dest.stat().st_size > 100:
        return "skipped"
    dest.parent.mkdir(parents=True, exist_ok=True)

    # 1. Téléchargement direct
    st, data = fetch_url(url, timeout=30)
    if st == 200 and len(data) > 100 and not _HTML_ERROR.match(data[:300]):
        dest.write_bytes(data)
        return "direct"

    if not use_wayback:
        return "failed"

    # 2. Fallback Wayback Machine (snapshot le plus récent)
    wb_url = f"https://web.archive.org/web/{_now_timestamp()}id_/{url}"
    st_wb, data_wb = fetch_url(wb_url, timeout=30)
    if st_wb == 200 and len(data_wb) > 100 and not _HTML_ERROR.match(data_wb[:300]):
        dest.write_bytes(data_wb)
        return "wayback"

    # 3. Fallback via l'API archive.org (l'URL exacte du snapshot)
    time.sleep(1)
    snap_url, ts = wayback_available(url)
    if snap_url:
        st_snap, data_snap = fetch_url(snap_url, timeout=60)
        if st_snap == 200 and len(data_snap) > 100 and not _HTML_ERROR.match(data_snap[:300]):
            dest.write_bytes(data_snap)
            return "wayback-api"

    return "failed"


def download_media(
    urls: list[str],
    uploads_dir: Path,
    use_wayback: bool = True,
    workers: int = 6,
    show_progress: bool = True,
) -> dict[str, int]:
    """Télécharge tous les médias vers ``uploads_dir`` en parallèle.

    Retourne un compteur ``{status: n}``.
    """
    results: dict[str, int] = {}
    total = len(urls)
    done = 0

    def dl(u: str) -> str:
        nonlocal done
        dest = uploads_dir / relative_dest(u)
        status = download_one(u, dest, use_wayback=use_wayback)
        if show_progress:
            done += 1
            print(
                t("  [{}/{}] {:<8} {}").format(done, total, status, u),
                flush=True,
            )
        return status

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for status in ex.map(dl, urls):
            results[status] = results.get(status, 0) + 1
    return results