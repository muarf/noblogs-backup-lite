"""wxr.py — Génération d'un export WordPress WXR 1.2 (XML).

Convertit les articles, pages et métadonnées récolés par `scraper.py` en un
fichier `rss` compatible avec l'outil *Outils > Importer > WordPress* de toute
installation WordPress, ainsi qu'avec `wp import` (WP-CLI).
"""
from __future__ import annotations

import html
import re
import unicodedata
from datetime import datetime
from pathlib import Path

from .html_clean import clean_content


def _slugify(title: str) -> str:
    norm = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("utf-8")
    return re.sub(r"[^a-z0-9_-]+", "-", norm.lower()).strip("-")


def generate_wxr(
    slug: str,
    title: str,
    site_url: str,
    posts: list[dict],
    pages: list[dict],
    authors: dict[str, str] | None = None,
    language: str = "fr-FR",
) -> str:
    """Génére le contenu XML WXR 1.2 complet.

    * ``slug``        – identifiant court du blog (utilisé en login d'auteur).
    * ``site_url``    – URL cible de comparaison/remplacement (ex. l'ancien domaine).
    * ``authors``     – mapping login → email optionnel (défaut : admin@exemple.org).
    """
    if authors is None:
        authors = {slug: f"{slug}@backup.noblogs.org"}

    clean_site_url = site_url.rstrip("/")

    xml: list[str] = []
    xml.append('<?xml version="1.0" encoding="UTF-8" ?>')
    xml.append('<rss version="2.0"')
    xml.append('  xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/"')
    xml.append('  xmlns:content="http://purl.org/rss/1.0/modules/content/"')
    xml.append('  xmlns:wfw="http://wellformedweb.org/CommentAPI/"')
    xml.append('  xmlns:dc="http://purl.org/dc/elements/1.1/"')
    xml.append('  xmlns:wp="http://wordpress.org/export/1.2/">')
    xml.append("<channel>")
    xml.append(f"  <title><![CDATA[{clean_content(title)}]]></title>")
    xml.append(f"  <link>{clean_site_url}</link>")
    xml.append(f"  <language>{language}</language>")
    xml.append("  <wp:wxr_version>1.2</wp:wxr_version>")

    for login, email in authors.items():
        xml.append("  <wp:author>")
        xml.append("    <wp:author_id>1</wp:author_id>")
        xml.append(f"    <wp:author_login><![CDATA[{login}]]></wp:author_login>")
        xml.append(f"    <wp:author_email><![CDATA[{email}]]></wp:author_email>")
        xml.append(f"    <wp:author_display_name><![CDATA[{login}]]></wp:author_display_name>")
        xml.append("  </wp:author>")

    used_cats: set[str] = set()
    for p in posts:
        for c in p.get("cats", []):
            used_cats.add(c)
    for c in sorted(used_cats):
        c_slug = _slugify(c)
        xml.append("  <wp:category>")
        xml.append(f"    <wp:term_id>{len(xml) + 10}</wp:term_id>")
        xml.append(f"    <wp:category_nicename><![CDATA[{c_slug}]]></wp:category_nicename>")
        xml.append(f"    <wp:cat_name><![CDATA[{clean_content(c)}]]></wp:cat_name>")
        xml.append("  </wp:category>")

    post_id = 1000
    for p in posts:
        post_id += 1
        pid = p.get("id") or post_id

        raw_date = p.get("date") or ""
        dt_str = "2022-01-01 12:00:00"
        if raw_date:
            try:
                dt = datetime.strptime(raw_date.strip(), "%a, %d %b %Y %H:%M:%S %z")
                dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass

        orig_slug = ""
        link = p.get("link", "")
        if link and "/post/" in link:
            clean_link = link.strip().rstrip("/")
            if clean_link.split("/"):
                orig_slug = clean_link.split("/")[-1]
        p_slug = orig_slug or _slugify(p.get("title", "")) or f"post-{pid}"

        p_title = clean_content(p.get("title", ""))
        content = clean_content(p.get("content", ""))
        xml.append("  <item>")
        xml.append(f"    <title><![CDATA[{p_title}]]></title>")
        xml.append(f"    <link>{link}</link>")
        if raw_date:
            xml.append(f"    <pubDate>{raw_date}</pubDate>")
        xml.append(f"    <dc:creator><![CDATA[{p.get('author', slug)}]]></dc:creator>")
        xml.append(f'    <guid isPermaLink="false">{clean_site_url}/?p={pid}</guid>')
        xml.append("    <description></description>")
        xml.append(f"    <content:encoded><![CDATA[{content}]]></content:encoded>")
        xml.append(f"    <wp:post_id>{pid}</wp:post_id>")
        xml.append(f"    <wp:post_date><![CDATA[{dt_str}]]></wp:post_date>")
        xml.append(f"    <wp:post_date_gmt><![CDATA[{dt_str}]]></wp:post_date_gmt>")
        xml.append("    <wp:post_status><![CDATA[publish]]></wp:post_status>")
        xml.append(f"    <wp:post_name><![CDATA[{p_slug}]]></wp:post_name>")
        xml.append("    <wp:post_type><![CDATA[post]]></wp:post_type>")
        for c in p.get("cats", []):
            c_slug = _slugify(c)
            xml.append(f'    <category domain="category" nicename="{c_slug}"><![CDATA[{clean_content(c)}]]></category>')
        xml.append("  </item>")

    for pg in pages:
        post_id += 1
        pg_slug = pg.get("slug") or _slugify(pg.get("title", "")) or f"page-{post_id}"
        xml.append("  <item>")
        xml.append(f"    <title><![CDATA[{clean_content(pg.get('title', ''))}]]></title>")
        xml.append(f"    <link>{pg.get('url', '')}</link>")
        xml.append(f"    <dc:creator><![CDATA[{slug}]]></dc:creator>")
        xml.append(f'    <guid isPermaLink="false">{clean_site_url}/?page_id={post_id}</guid>')
        xml.append(f"    <content:encoded><![CDATA[{clean_content(pg.get('content', ''))}]]></content:encoded>")
        xml.append(f"    <wp:post_id>{post_id}</wp:post_id>")
        xml.append("    <wp:post_date><![CDATA[2022-01-01 12:00:00]]></wp:post_date>")
        xml.append("    <wp:post_date_gmt><![CDATA[2022-01-01 12:00:00]]></wp:post_date_gmt>")
        xml.append("    <wp:post_status><![CDATA[publish]]></wp:post_status>")
        xml.append(f"    <wp:post_name><![CDATA[{pg_slug}]]></wp:post_name>")
        xml.append("    <wp:post_type><![CDATA[page]]></wp:post_type>")
        xml.append("  </item>")

    xml.append("</channel>")
    xml.append("</rss>")
    return "\n".join(xml)


def write_wxr(path: Path, *args, **kwargs) -> Path:
    """Écrit l'export WXR dans ``path`` et renvoie``path``."""
    path.write_text(generate_wxr(*args, **kwargs), encoding="utf-8")
    return path