#!/usr/bin/env python3
"""Focused local tests for preview publishing and serving."""

import json
import contextlib
import io
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock
from urllib.error import HTTPError
from urllib.request import urlopen

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import create_preview
import clean_previews
from preview_server import PreviewServer


ID_RE = re.compile(r"^[0-9a-f]{16}$")


class InfrastructureTests(unittest.TestCase):
    @mock.patch("create_preview.subprocess.run")
    @mock.patch("create_preview.local_health_ok", return_value=True)
    def test_healthy_server_is_reused(self, health, run):
        create_preview.ensure_preview_server()
        health.assert_called_once()
        run.assert_not_called()

    @mock.patch("create_preview.time.sleep")
    @mock.patch("create_preview.local_health_ok", side_effect=[False, True])
    @mock.patch("create_preview.subprocess.run")
    def test_stopped_server_is_started_and_health_checked(self, run, health, sleep):
        run.return_value = subprocess.CompletedProcess([], 0, "{}\n", "")
        create_preview.ensure_preview_server()
        self.assertEqual(run.call_count, 1)
        self.assertIn("start_preview_server.py", " ".join(run.call_args.args[0]))
        self.assertEqual(health.call_count, 2)

    @mock.patch("create_preview.subprocess.run")
    def test_missing_funnel_is_reestablished_and_verified(self, run):
        run.side_effect = [
            subprocess.CompletedProcess([], 0, "No serve config\n", ""),
            subprocess.CompletedProcess([], 0, "", ""),
            subprocess.CompletedProcess([], 0, "https://preview.example.test (Funnel on)\n|-- / proxy http://127.0.0.1:8080\n", ""),
        ]
        create_preview.ensure_funnel("https://preview.example.test")
        self.assertEqual(run.call_count, 3)
        self.assertEqual(run.call_args_list[1].args[0][-4:], ["funnel", "--bg", "--yes", "8080"])


class PublisherTests(unittest.TestCase):
    def run_publisher(self, source: Path, store: Path, base_url: str | None):
        env = os.environ.copy()
        env["HERMES_PREVIEWS_DIR"] = str(store)
        if base_url is None:
            env.pop("PREVIEW_BASE_URL", None)
        else:
            env["PREVIEW_BASE_URL"] = base_url
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch.dict(os.environ, env, clear=True),
            mock.patch.object(sys, "argv", [str(Path(create_preview.__file__)), str(source)]),
            mock.patch.object(create_preview, "PREVIEWS_DIR", str(store)),
            mock.patch.object(create_preview, "BASE_URL_FILE", str(store.parent / "preview-base-url.txt")),
            mock.patch.object(create_preview, "ensure_preview_server"),
            mock.patch.object(create_preview, "ensure_funnel"),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            returncode = create_preview.main()
        return subprocess.CompletedProcess([], returncode, stdout.getvalue(), stderr.getvalue())

    def test_html_file_publish_uses_opaque_id_and_https_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "secret-project-name.html"
            source.write_text("<h1>hello</h1>", encoding="utf-8")
            result = self.run_publisher(source, root / "store", "https://preview.example.test")
            self.assertEqual(result.returncode, 0, result.stderr)
            url = result.stdout.strip()
            preview_id = url.removeprefix("https://preview.example.test/preview/").rstrip("/")
            self.assertRegex(preview_id, ID_RE)
            self.assertNotIn("secret-project-name", url)
            destination = root / "store" / preview_id
            self.assertEqual((destination / "index.html").read_text(encoding="utf-8"), "<h1>hello</h1>")
            metadata = json.loads((destination / ".preview_meta.json").read_text(encoding="utf-8"))
            self.assertEqual(set(metadata), {"created_at"})

    def test_directory_publish_copies_relative_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site = root / "site"
            (site / "assets").mkdir(parents=True)
            (site / "index.html").write_text('<link href="assets/app.css">', encoding="utf-8")
            (site / "assets" / "app.css").write_text("body{}", encoding="utf-8")
            result = self.run_publisher(site, root / "store", "https://preview.example.test/base")
            self.assertEqual(result.returncode, 0, result.stderr)
            preview_id = result.stdout.strip().split("/preview/")[1].rstrip("/")
            self.assertEqual((root / "store" / preview_id / "assets" / "app.css").read_text(), "body{}")
            self.assertTrue(result.stdout.startswith("https://preview.example.test/base/preview/"))

    def test_persisted_external_base_url_is_returned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = root / "store"
            source = root / "index.html"
            source.write_text("ok", encoding="utf-8")
            (root / "preview-base-url.txt").write_text("https://funnel.example.test/\n", encoding="utf-8")
            result = self.run_publisher(source, store, None)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertRegex(result.stdout.strip(), r"^https://funnel\.example\.test/preview/[0-9a-f]{16}/$")

    def test_rejects_insecure_or_credentialed_base_urls_without_publishing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "index.html"
            source.write_text("ok", encoding="utf-8")
            for base in ("http://preview.example.test", "<REDACTED_SECRET> "https://preview.example.test/?token=x"):
                store = root / secretsafe(base)
                result = self.run_publisher(source, store, base)
                self.assertEqual(result.returncode, 1)
                self.assertFalse(store.exists() and any(store.iterdir()))

    def test_rejects_unsafe_railway_domain_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "index.html"
            source.write_text("ok", encoding="utf-8")
            env = os.environ.copy()
            env["RAILWAY_PUBLIC_DOMAIN"] = "user:pass@example.test/?token=x"
            with mock.patch.dict(os.environ, env, clear=True):
                result = self.run_publisher(source, root / "store", None)
            self.assertEqual(result.returncode, 1)
            self.assertIn("RAILWAY_PUBLIC_DOMAIN fallback", result.stderr)

    def test_mocked_reparse_point_is_rejected_and_partial_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site = root / "site"
            site.mkdir()
            (site / "index.html").write_text("ok", encoding="utf-8")
            (site / "unsafe").write_text("outside", encoding="utf-8")
            real_check = create_preview.is_link_or_reparse

            def mocked_check(path):
                return Path(path).name == "unsafe" or real_check(path)

            with mock.patch.object(create_preview, "is_link_or_reparse", side_effect=mocked_check):
                result = self.run_publisher(site, root / "store", "https://preview.example.test")
            self.assertEqual(result.returncode, 1)
            self.assertIn("link or reparse point", result.stderr)
            self.assertEqual(list((root / "store").iterdir()), [])

    def test_copy_failure_removes_partial_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "index.html"
            source.write_text("ok", encoding="utf-8")
            with mock.patch("create_preview.shutil.copy2", side_effect=OSError("copy failed")):
                result = self.run_publisher(source, root / "store", "https://preview.example.test")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(list((root / "store").iterdir()), [])


def secretsafe(value: str) -> str:
    return str(abs(hash(value)))


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.preview_id = "0123456789abcdef"
        preview = self.root / self.preview_id
        (preview / "assets").mkdir(parents=True)
        (preview / "index.html").write_text("INDEX", encoding="utf-8")
        (preview / "assets" / "app.css").write_text("CSS", encoding="utf-8")
        (preview / ".preview_meta.json").write_text('{"created_at": 0}', encoding="utf-8")
        (preview / "empty").mkdir()
        self.server = PreviewServer(("127.0.0.1", 0), self.root)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.tmp.cleanup()

    def request(self, path: str):
        try:
            with urlopen(self.base + path) as response:
                return response.status, response.read(), dict(response.headers)
        except HTTPError as error:
            return error.code, error.read(), dict(error.headers)

    def test_index_asset_head_and_missing_resource(self):
        status, body, _ = self.request(f"/preview/{self.preview_id}/")
        self.assertEqual((status, body), (200, b"INDEX"))
        status, body, headers = self.request(f"/preview/{self.preview_id}/assets/app.css")
        self.assertEqual((status, body), (200, b"CSS"))
        self.assertIn("text/css", headers["Content-Type"])
        self.assertEqual(self.request(f"/preview/{self.preview_id}/missing.js")[0], 404)

    def test_malformed_ids_traversal_metadata_and_listings_are_blocked(self):
        blocked = (
            "/preview/not-an-id/",
            "/preview/0123456789ABCDEf/",
            f"/preview/{self.preview_id}/../index.html",
            f"/preview/{self.preview_id}/%2e%2e/index.html",
            f"/preview/{self.preview_id}/..%5coutside",
            f"/preview/{self.preview_id}/.preview_meta.json",
            f"/preview/{self.preview_id}/empty/",
            "/preview/",
            "/",
        )
        for path in blocked:
            with self.subTest(path=path):
                status, body, _ = self.request(path)
                self.assertEqual(status, 404)
                self.assertNotIn(str(self.root).encode(), body)


class CleanupCompatibilityTests(unittest.TestCase):
    def test_timestamp_only_metadata_preserves_seven_day_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            expired = root / "deadbeefdeadbeef"
            expired.mkdir()
            (expired / ".preview_meta.json").write_text(
                json.dumps({"created_at": clean_previews.time.time() - clean_previews.RETENTION_SECONDS - 1}),
                encoding="utf-8",
            )
            original_store = clean_previews.PREVIEWS_DIR
            clean_previews.PREVIEWS_DIR = str(root)
            try:
                clean_previews.main()
            finally:
                clean_previews.PREVIEWS_DIR = original_store
            self.assertFalse(expired.exists())


if __name__ == "__main__":
    unittest.main()