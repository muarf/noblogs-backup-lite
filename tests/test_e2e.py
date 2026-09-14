"""Test de bout en bout (hors-ligne) : backup complet d'un blog NoBlogs factice.

Démarre un petit serveur HTTP local (< 1 s) qui simule un blog NoBlogs
(homepage, flux RSS, API pages, thème, fichiers médias), puis exécute la
pipeline complète `backup_one` dessus. Aucun réseau externe n'est requis.
"""
from __future__ import annotations

import argparse
import io
import json
import shutil
import tempfile
import threading
import unittest
import xml.etree.ElementTree as ET
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from backup.__main__ import backup_one

JPEG_BYTES = bytes(range(256)) * 4  # > 100 octets, pas du HTML
PDF_BYTES = b"%PDF-1.4\n12345" + b"x" * 200  # > 100 octets, pas du HTML


def _routes(mode: str = "full"):
    """Construit {chemin_requête: body} pour le blog fixture."""
    base_jpeg = f'<img src="http://127.0.0.1:{PORT}/files/2026/01/pic.jpg">'
    base_pdf = f'<a href="http://127.0.0.1:{PORT}/files/2025/12/paper.pdf">PDF</a>'

    def item(pid, slug, title, content, date="Mon, 05 Jan 2026 12:00:00 +0000"):
        guid = f"http://127.0.0.1:{PORT}/?p={pid}" if pid else f"http://127.0.0.1:{PORT}/2026/01/{slug}"
        return f"""
<item>
  <title><![CDATA[{title}]]></title>
  <link>http://127.0.0.1:{PORT}/2026/01/{slug}</link>
  <guid>{guid}</guid>
  <pubDate>{date}</pubDate>
  <dc:creator><![CDATA[{title.lower()}@blog]]></dc:creator>
  <category><![CDATA[Nouvelles]]></category>
  <content:encoded><![CDATA[{content}]]></content:encoded>
</item>"""

    item1 = item(101, "post-1", "Premier billet", f"<p>Bonjour {base_jpeg}.</p>")
    item2 = item(None, "post-2", "Second billet", f"<p>Un <em>PDF</em> : {base_pdf}.</p>")
    item3 = item(103, "post-3", "Troisième billet", "<p>Sans média.</p>")

    rss = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<rss version="2.0"><channel>'
        "<title>Flux</title><link>http://127.0.0.1:{PORT}/</link>"
        + item1 + item2 + item3
        + "</channel></rss>"
    )
    empty_rss = '<?xml version="1.0"?><rss version="2.0"><channel><title>Flux</title></channel></rss>'

    homepage = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Mon Blog Fixture | sous-titre</title>
<link rel="stylesheet" href="http://127.0.0.1:{PORT}/wp-content/themes/fixturetheme/style.css">
</head><body class="blog home wp-theme-fixturetheme">
<header><a class="custom-logo-link" href="/"><img src="http://127.0.0.1:{PORT}/files/2025/logo.png"></a>
<h1 class="site-title">Mon Blog Fixture</h1>
<p class="site-description">La tagline du blog</p></header>
<style id="wp-custom-css">.post {{ margin: 0 0 40px; }} a:visited {{ color: black; }}</style>
<nav><ul class="menu"><li><a href="/a-propos">À propos</a>
<ul class="sub-menu"><li><a href="/contact">Contact</a></li></ul></li></ul></nav>
<div id="secondary"><div class="widget widget_search"><form class="search-form"></form></div>
<div class="widget widget_custom_html"><div class="textwidget"><p>Un widget texte</p></div></div></div>
<article class="post"><p>Dernier billet demo.</p></article>
</body></html>"""

    pages_json = json.dumps([{
        "title": {"rendered": "À propos"},
        "link": f"http://127.0.0.1:{PORT}/a-propos",
        "slug": "a-propos",
        "content": {"rendered": "<p>Une page statique.</p>"},
        "date": "2021-05-01T14:22:00",
    }])

    routes = {
        "/": homepage,
        "/?feed=rss2": rss,
        "/?feed=rss2&paged=2": empty_rss,
        "/feed/": rss,
        "/wp-json/wp/v2/pages?per_page=100&page=1": pages_json,
        "/wp-content/themes/fixturetheme/style.css": "/* Theme fixture */ body { color: #333; }",
        "/wp-content/themes/fixturetheme/index.php": "<?php /* theme */ ?>",
        "/files/2026/01/pic.jpg": JPEG_BYTES,
        "/files/2025/12/paper.pdf": PDF_BYTES,
        "/files/2025/logo.png": JPEG_BYTES,
    }
    if mode == "empty":
        routes["/?feed=rss2"] = empty_rss
        routes["/feed/"] = empty_rss
        # Blog mort : plus de pages API, plus de thème, plus de médias.
        routes.pop("/wp-json/wp/v2/pages?per_page=100&page=1", None)
        routes.pop("/wp-content/themes/fixturetheme/style.css", None)
        routes.pop("/files/2026/01/pic.jpg", None)
    return routes


PORT: int | None = None  # rempli au démarrage du serveur


def serve(mode: str = "full"):
    """Context manager : rend (base_url, fermeture)."""
    global PORT
    routes = _routes(mode)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = routes.get(self.path)
            if body is None:
                self.send_response(404)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if isinstance(body, str):
                body = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    PORT = server.server_address[1]
    routes = _routes(mode)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://127.0.0.1:{PORT}"
    finally:
        server.shutdown()


import contextlib

_exit = contextlib.contextmanager(serve)

_PORT_FIX = None


def _args(out_dir, base_url, no_media=False, unpack=True):
    return argparse.Namespace(
        base_url=base_url,
        out_dir=out_dir,
        no_wayback=True,
        no_plugins=True,
        assets_cache=None,
        no_media=no_media,
        workers=4,
        keep_uploads=False,
        force=True,
        unpack=unpack,
        slugs=["fixture"],
    )


class TestEndToEnd(unittest.TestCase):
    def _run(self, mode="full", no_media=False):
        """Exécute le backup et retourne (result, contenu du ZIP en octets)."""
        with _exit(mode) as base, tempfile.TemporaryDirectory() as tmp:
            out_dir = str(Path(tmp) / "backups")
            args = _args(out_dir, base, no_media=no_media)
            result = backup_one("fixture", args)
            zip_bytes = b""
            if result.get("zip"):
                zip_path = Path(result["zip"])
                zip_bytes = zip_path.read_bytes() if zip_path.exists() else b""
            return result, zip_bytes

    def test_full_backup_offline(self):
        result, zip_bytes = self._run()
        self.assertNotIn("error", result, result)
        self.assertGreater(len(zip_bytes), 1000)

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = set(zf.namelist())
            self.assertIn("wordpress-export.xml", names)
            self.assertIn("fidelity.json", names)
            self.assertIn("metadata.json", names)
            self.assertIn("uploads/2026/01/pic.jpg", names)
            self.assertIn("uploads/2025/12/paper.pdf", names)
            self.assertIn("theme/fixturetheme/style.css", names)
            self.assertIn("theme/fixturetheme/index.php", names)

            root = ET.fromstring(zf.read("wordpress-export.xml"))
            items = root.findall(".//item")
            wp = "{http://wordpress.org/export/1.2/}"
            types = [it.find(f"{wp}post_type").text for it in items]
            self.assertEqual(types.count("post"), 3)
            self.assertEqual(types.count("page"), 1)
            self.assertEqual(types.count("attachment"), 3)  # pic.jpg + paper.pdf + logo.png
            attach_urls = [
                it.find(f"{wp}attachment_url").text
                for it in items if it.find(f"{wp}post_type").text == "attachment"
            ]
            self.assertIn(f"http://127.0.0.1:{PORT}/files/2026/01/pic.jpg", attach_urls)

            fidelity = json.loads(zf.read("fidelity.json"))
            self.assertEqual(fidelity["theme"], "fixturetheme")
            self.assertEqual(fidelity["tagline"], "La tagline du blog")
            self.assertTrue(fidelity["custom_css"])

            meta = json.loads(zf.read("metadata.json"))
            self.assertEqual(meta["slug"], "fixture")
            self.assertEqual(meta["posts_count"], 3)
            self.assertEqual(meta["media"]["direct"], 3)  # pic + pdf + logo

    def test_media_skip_flag(self):
        result, zip_bytes = self._run(no_media=True)
        self.assertNotIn("error", result, result)
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            self.assertNotIn("uploads/2026/01/pic.jpg", zf.namelist())

    def test_empty_blog_returns_error(self):
        result, _ = self._run(mode="empty")
        self.assertEqual(result.get("error"), "empty")


if __name__ == "__main__":
    unittest.main()