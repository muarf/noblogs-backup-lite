"""html_clean.py — Nettoyage de fragments HTML récupérés des blogs."""

from __future__ import annotations

import html
import re
import unicodedata


def clean_content(s: str) -> str:
    """Nettoie un fragment HTML : CDATA, entités doublement encodées,
    normalisation Unicode et guillemets droits."""
    if not s:
        return ""
    s = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", s, flags=re.S)
    s = html.unescape(html.unescape(s))
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\u201c", '"').replace("\u201d", '"')
    s = s.replace("\u2018", "'").replace("\u2019", "'")
    return s


def grab_balanced(html_src: str, marker: str) -> str | None:
    """Extrait la plus grande région <div class="...marker..."> ... </div>
    correctement équilibrée."""
    region = None
    for m in re.finditer(r'<div[^>]*class="[^"]*' + marker + r'[^"]*"[^>]*>', html_src):
        sub = html_src[m.end():]
        depth = 0
        for mm in re.finditer(r"<(/?)\s*div[^>]*>", sub):
            tag = mm.group(0)
            if tag.startswith("</"):
                depth -= 1
            elif not tag.rstrip().endswith("/>"):
                depth += 1
            if depth <= 0:
                cand = sub[:mm.start()].rstrip()
                if not region or len(cand) > len(region):
                    region = cand
                break
    return region