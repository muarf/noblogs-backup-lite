"""http.py — Récupération de contenu HTTP robuste.

Contient la logique de fetch (headers, retries, délais) utilisée par le
scraper et le téléchargeur de médias. Évite la dépendance à des proxies Tor :
utile pour archive.org, la Wayback Machine et le site d'origine.
"""
from __future__ import annotations

import random
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

UA = "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"

_session = None


def _get_session() -> requests.Session:
    """Session partagée avec retry automatique sur les erreurs réseau."""
    global _session
    if _session is None:
        retry = Retry(
            total=5,
            connect=5,
            read=5,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=frozenset(["GET", "HEAD"]),
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=16, pool_maxsize=16)
        _session = requests.Session()
        _session.mount("https://", adapter)
        _session.mount("http://", adapter)
    return _session


def fetch_url(url: str, timeout: float = 30) -> tuple[int, bytes]:
    """Retourne (status_code, body_binary). (0, b"") en cas d'échec final."""
    try:
        r = _get_session().get(
            url,
            headers={"User-Agent": UA, "Accept": "*/*"},
            timeout=timeout,
        )
        return r.status_code, r.content
    except Exception:
        return 0, b""


def fetch_url_with_retries(
    url: str, timeout: float = 30, retries: int = 3, min_delay: float = 0.5
) -> tuple[int, bytes]:
    """Comme fetch_url mais avec retries manuels et backoff aléatoire."""
    for attempt in range(retries):
        st, body = fetch_url(url, timeout=timeout)
        if st == 200:
            return st, body
        if attempt < retries - 1:
            time.sleep(min_delay * (1 + attempt) + random.uniform(0, 0.5))
    return st, body