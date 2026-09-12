"""scraper.py — Aspiration complète d'un blog NoBlogs.

Récupère la liste d'articles via le flux RSS paginé, le contenu complet de
chaque article, les pages statiques (via l'API REST de WordPress) et extrait
toutes les URLs de médias à télécharger.
"""
from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from bs4 import BeautifulSoup

from .html_clean import clean_content, grab_balanced
from .http import fetch_url


@dataclass
class BlogMeta:
    slug: str
    title: str
    theme: str
    base_url: str


@dataclass
class ScrapedBlog:
    slug: str
    title: str
    theme: str
    base_url: str
    posts: list[dict] = field(default_factory=list)
    pages: list[dict] = field(default_factory=list)
    media_urls: list[str] = field(default_factory=list)


class NoblogsScraper:
    """Aspire un blog NoBlogs.

    * ``slug``     – nom court (ex. ``monblog``).
    * ``base_url`` – optionnel. Si absent, ``https://<slug>.noblogs.org``.
    """

    def __init__(self, slug: str, base_url: str | None = None):
        self.slug = slug
        self.base_url = (base_url or f"https://{slug}.noblogs.org").rstrip("/")

    # ---------------------------------------------------------------- scrape

    def scrape_all(self) -> ScrapedBlog:
        meta = self.detect_meta()
        posts = self.scrape_feed()
        print(f"  {len(posts)} articles trouvés dans le flux RSS", flush=True)
        posts = self.scrape_post_contents(posts)
        pages = self.scrape_pages()
        print(f"  {len(pages)} pages statiques trouvées", flush=True)
        return ScrapedBlog(
            slug=self.slug,
            title=meta["title"],
            theme=meta["theme"],
            base_url=self.base_url,
            posts=posts,
            pages=pages,
        )

    # ------------------------------------------------------------ métadonnées

    def detect_meta(self) -> dict:
        title = self.slug
        theme = "twentysixteen"
        st, body = fetch_url(f"{self.base_url}/")
        if st == 200:
            try:
                soup = BeautifulSoup(body, "html.parser")
            except Exception:
                soup = None
            if soup:
                if soup.title and soup.title.string:
                    raw_t = soup.title.string.strip()
                    title = clean_content(re.split(r"\s+[\u2013\u2014|-]\s+|\s+\u00bb\s+", raw_t)[0].strip())
                for link in soup.find_all("link", rel="stylesheet"):
                    href = link.get("href", "")
                    m = re.search(r"/wp-content/themes/([^/]+)/", href)
                    if m:
                        theme = m.group(1)
                        break
        print(f"  Titre : {title!r}, thème : {theme!r}", flush=True)
        return {"title": title, "theme": theme}

    # ---------------------------------------------------------------- articles

    def scrape_feed(self, max_pages: int = 200) -> list[dict]:
        """Parcourt le flux RSS paginé et récupère les métadonnées de chaque
        article."""
        items: list[dict] = []
        seen: set[str] = set()
        for paged in range(1, max_pages + 1):
            url = f"{self.base_url}/?feed=rss2&paged={paged}" if paged > 1 else f"{self.base_url}/?feed=rss2"
            st, b = fetch_url(url)
            if st != 200 or not b:
                if paged == 1:
                    st, b = fetch_url(f"{self.base_url}/feed/")
                if st != 200 or not b:
                    break
            xml_str = b.decode("utf-8", "replace")
            page_items: list[dict] = []
            for it in re.findall(r"<item>(.*?)</item>", xml_str, re.S):
                t_m = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", it, re.S)
                l_m = re.search(r"<link>(.*?)</link>", it, re.S)
                c_m = re.search(r"<dc:creator><!\[CDATA\[(.*?)\]\]>", it, re.S)
                d_m = re.search(r"<pubDate>(.*?)</pubDate>", it, re.S)
                g_m = re.search(r"<guid[^>]*>(.*?)</guid>", it, re.S)
                link = l_m.group(1).strip() if l_m else ""
                if not link or link in seen:
                    continue
                seen.add(link)
                guid = g_m.group(1).strip() if g_m else ""
                post_id = None
                m_id = re.search(r"\?p=(\d+)", guid)
                if m_id:
                    post_id = int(m_id.group(1))
                cats = [clean_content(c) for c in re.findall(r"<category>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</category>", it, re.S)]
                content_enc = re.search(r"<content:encoded><!\[CDATA\[(.*?)\]\]></content:encoded>", it, re.S)
                page_items.append({
                    "id": post_id,
                    "title": clean_content(t_m.group(1)) if t_m else "",
                    "link": link,
                    "guid": guid,
                    "author": c_m.group(1) if c_m else self.slug,
                    "date": d_m.group(1) if d_m else "",
                    "cats": cats,
                    "content_encoded": content_enc.group(1) if content_enc else None,
                })
            if not page_items:
                break
            items.extend(page_items)
            print(f"  page {paged}: +{len(page_items)} articles (total: {len(items)})", flush=True)
        return items

    def scrape_post_contents(self, posts_meta: list[dict]) -> list[dict]:
        """Récupère le contenu complet de chaque article (8 titulaires
        simultanés). Les articles avec ``content_encoded`` présent sont
        réutilisés sans fetch."""
        def fetch_post(p: dict) -> dict:
            if p.get("content_encoded"):
                p["content"] = clean_content(p["content_encoded"])
                return p
            st, b = fetch_url(p["link"])
            if st != 200 or not b:
                p["content"] = ""
                return p
            html_src = b.decode("utf-8", "replace")
            soup = BeautifulSoup(html_src, "html.parser")
            content_elem = (
                soup.find("div", class_=lambda c: c and "entry-content" in c.split()) or
                soup.find("div", class_=lambda c: c and "post-content" in c.split()) or
                soup.find("div", class_=lambda c: c and "entry" in c.split()) or
                soup.find("article") or
                soup.find("div", class_=lambda c: c and "post" in c.split())
            )
            if content_elem:
                for tag in content_elem(["script", "style", "form", "nav"]):
                    tag.decompose()
                content = "".join(str(c) for c in content_elem.contents).strip()
            else:
                raw = (
                    grab_balanced(html_src, "entry-content")
                    or grab_balanced(html_src, "entry")
                    or grab_balanced(html_src, "post")
                    or ""
                )
                content = raw.strip()
            p["content"] = clean_content(content)
            return p

        with ThreadPoolExecutor(max_workers=8) as ex:
            return [p for p in ex.map(fetch_post, posts_meta)]

    # ------------------------------------------------------------- pages

    def scrape_pages(self, max_pages: int = 20) -> list[dict]:
        """Récupère les pages statiques via l'API REST WP.

        Parcourt la pagination (par lots de 100) jusqu'à ``max_pages`` pages
        pour ne pas perdre les >100 pages. Retourne une liste vide si erreur.
        """
        out: list[dict] = []
        for page in range(1, max_pages + 1):
            url = f"{self.base_url}/wp-json/wp/v2/pages?per_page=100&page={page}"
            st, b = fetch_url(url)
            if st != 200 or not b:
                break
            try:
                data = json.loads(b.decode("utf-8", "replace"))
            except Exception:
                break
            if not isinstance(data, list) or not data:
                break
            out.extend(
                {
                    "title": pg.get("title", {}).get("rendered", ""),
                    "url": pg.get("link", ""),
                    "slug": pg.get("slug", ""),
                    "content": pg.get("content", {}).get("rendered", ""),
                    "date": pg.get("date", ""),
                }
                for pg in data
            )
            if len(data) < 100:
                break
        return out

    # -------------------------------------------------------------- médias

    def extract_all_media(self, posts: list[dict], pages: list[dict]) -> list[str]:
        """Collecte toutes les URLs de médias appartenant au blog.

        Retient : toute URL en ``/files/`` ou ``/uploads/``, plus tout fichier
        médiatique pointant vers ``<slug>.noblogs.org``.
        """
        urls: set[str] = set()
        glob = re.compile(r"https?://[^\s\"'<>]+\.(?:jpg|jpeg|png|gif|svg|webp|pdf|mp3|ogg|mp4|webm)", re.I)
        own_files = re.compile(rf"https?://[^\s\"'<>]*/files/[^\s\"'<>]+", re.I)

        candidates: list[str] = []
        for p in posts:
            candidates.append(p.get("content", ""))
        for pg in pages:
            candidates.append(pg.get("content", ""))

        for text in candidates:
            for m in own_files.finditer(text):
                urls.add(m.group(0))
            for m in glob.finditer(text):
                if self.slug + ".noblogs.org" in m.group(0) or "/files/" in m.group(0) or "/uploads/" in m.group(0):
                    urls.add(m.group(0))

        st, b = fetch_url(f"{self.base_url}/")
        if st == 200 and b:
            home_html = b.decode("utf-8", "replace")
            for m in own_files.finditer(home_html):
                urls.add(m.group(0))
            for m in glob.finditer(home_html):
                if self.slug + ".noblogs.org" in m.group(0) or "/files/" in m.group(0) or "/uploads/" in m.group(0):
                    urls.add(m.group(0))
        return sorted(urls)