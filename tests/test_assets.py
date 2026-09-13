"""Tests unitaires des assets NoBlogs (thèmes/plugins) et de l'embarquement ZIP.

Aucun réseau requis : on fabrique un bundle ZIP factice dans un dossier cache.
"""
from __future__ import annotations

import io
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from backup.assets import (
    NOBLOGS_PLUGINS,
    _bundle_zip,
    bundle_plugins,
    set_cache_dir,
)
from backup.package import human_size
from backup.package import package_backup


def _make_fake_bundle(cache: Path) -> bytes:
    """Construit un ZIP mimant la structure noblogs-assets-main/…"""
    buf = io.BytesIO()
    root = "noblogs-assets-main"
    entries = {
        f"{root}/plugins/{p}/{p}.php": b"<?php // %s ?>" % p.encode()
        for p in NOBLOGS_PLUGINS
    }
    entries.update({
        f"{root}/mu-plugins/ai-common.php": b"<?php // common ?>",
        f"{root}/mu-plugins/disable-emojis.php": b"<?php // emoji ?>",
        f"{root}/themes/minimalism/style.css": b"/* minimalism */",
        f"{root}/themes/minimalism/header.php": b"<?php // header ?>",
        f"{root}/wplang/src/Wplang.php": b"<?php // wplang ?>",
    })
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    body = buf.getvalue()
    cache.mkdir(parents=True, exist_ok=True)
    (cache / "noblogs-assets.zip").write_bytes(body)
    return body


class TestAssetsBundle(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="test_assets_"))
        self.cache = self.tmp / "cache"
        _make_fake_bundle(self.cache)
        set_cache_dir(self.cache)

    def tearDown(self):
        set_cache_dir(None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_bundle_zip_cached(self):
        body1 = _bundle_zip()
        body2 = _bundle_zip()
        self.assertEqual(body1, body2)
        self.assertGreater(len(body1), 0)

    def test_bundle_plugins_selected(self):
        plugins_dir = bundle_plugins(
            slugs=["nospam", "classic-editor"],
            dest_dir=self.tmp / "stage",
        )
        self.assertIsNotNone(plugins_dir)
        for name in ("nospam", "classic-editor"):
            self.assertTrue((plugins_dir / name).is_dir(), name)

    def test_bundle_plugins_default_list(self):
        plugins_dir = bundle_plugins(dest_dir=self.tmp / "stage")
        self.assertIsNotNone(plugins_dir)
        for name in ("nospam", "classic-editor", "buddypress", "akismet"):
            self.assertTrue((plugins_dir / name).is_dir(), name)

    def test_plugin_list_has_core_names(self):
        for name in ("nospam", "classic-editor", "buddypress", "disable-comments"):
            self.assertIn(name, NOBLOGS_PLUGINS)

    def test_bundle_plugins_uses_cache(self):
        p1 = bundle_plugins(dest_dir=self.tmp / "a")
        p2 = bundle_plugins(dest_dir=self.tmp / "b")
        files1 = sorted(f.name for f in (p1 / "nospam").iterdir())
        files2 = sorted(f.name for f in (p2 / "nospam").iterdir())
        self.assertEqual(files1, files2)


class TestPackagePlugins(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="test_pkg_"))
        self.cache = self.tmp / "cache"
        _make_fake_bundle(self.cache)
        set_cache_dir(self.cache)
        self.exports = self.tmp / "exports"
        self.stage = self.tmp / "stage"
        self.stage.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        set_cache_dir(None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _minimal_assets(self):
        wxr = self.stage / "wordpress-export.xml"
        wxr.write_text("<rss/>", encoding="utf-8")
        uploads = self.stage / "uploads"
        uploads.mkdir()
        (uploads / "a.jpg").write_bytes(b"12345")
        plugins_dir = bundle_plugins(dest_dir=self.stage)
        self.assertIsNotNone(plugins_dir)
        return wxr, uploads, plugins_dir

    def test_package_backup_embeds_plugins(self):
        wxr, uploads, plugins_dir = self._minimal_assets()
        zip_path = package_backup(
            slug="fixture",
            exports_dir=self.exports,
            wxr_path=wxr,
            uploads_dir=uploads,
            original_url="http://127.0.0.1:1",
            plugins_dir=plugins_dir,
        )
        with zipfile.ZipFile(zip_path) as zf:
            names = set(zf.namelist())
            self.assertIn("plugins/nospam/nospam.php", names)
            self.assertIn("plugins/classic-editor/classic-editor.php", names)
            self.assertIn("metadata.json", names)
            meta = zipfile.ZipFile(zip_path).read("metadata.json").decode("utf-8")
            self.assertIn('"plugins_bundled": true', meta)

    def test_package_backup_without_plugins(self):
        wxr = self.stage / "wordpress-export.xml"
        wxr.write_text("<rss/>", encoding="utf-8")
        uploads = self.stage / "uploads"
        uploads.mkdir()
        zip_path = package_backup(
            slug="fixture2",
            exports_dir=self.exports,
            wxr_path=wxr,
            uploads_dir=uploads,
            original_url="http://127.0.0.1:1",
        )
        with zipfile.ZipFile(zip_path) as zf:
            names = set(zf.namelist())
            self.assertNotIn("plugins/nospam/nospam.php", names)
            meta = json.loads(zipfile.ZipFile(zip_path).read("metadata.json").decode("utf-8"))
            self.assertFalse(meta["plugins_bundled"])

    def test_readme_mentions_plugins(self):
        wxr, uploads, plugins_dir = self._minimal_assets()
        zip_path = package_backup(
            slug="fixture",
            exports_dir=self.exports,
            wxr_path=wxr,
            uploads_dir=uploads,
            original_url="http://127.0.0.1:1",
            plugins_dir=plugins_dir,
        )
        with zipfile.ZipFile(zip_path) as zf:
            readme = zf.read("README.md").decode("utf-8")
            self.assertIn("plugins/", readme)


if __name__ == "__main__":
    unittest.main()