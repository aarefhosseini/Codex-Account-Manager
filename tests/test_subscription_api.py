"""Local HTTP contract tests, with an isolated CODEX_HOME and fake credentials."""

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path


class SubscriptionApiTests(unittest.TestCase):
    def test_purchase_dates_roundtrip_and_invalid_input_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            profile = home / "account-profiles/work"
            profile.mkdir(parents=True)
            (profile / "auth.json").write_text(json.dumps({"tokens": {"account_id": "fake", "access_token": "fake"}}))
            (profile / "meta.json").write_text(json.dumps({"name": "work", "saved_at": "2026-09-01"}))
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            process = subprocess.Popen(
                [sys.executable, "-m", "codex_account_manager", "ui", "--host", "127.0.0.1", "--port", str(port), "--no-open", "--foreground"],
                env={**os.environ, "CODEX_HOME": str(home)}, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            try:
                info_path = home / "ui-service/service.json"
                for _ in range(100):
                    if info_path.exists():
                        break
                    if process.poll() is not None:
                        self.fail("Isolated UI backend stopped before startup")
                    time.sleep(0.05)
                info = json.loads(info_path.read_text())
                base = f"http://127.0.0.1:{port}"
                def request(path, body=None, token=True):
                    req = urllib.request.Request(base + path,
                        data=json.dumps(body).encode() if body is not None else None,
                        headers={"Content-Type": "application/json", **({"X-Codex-Token": info["token"]} if token else {})})
                    with urllib.request.urlopen(req, timeout=3) as response:
                        return json.load(response)["data"]
                result = request("/api/local/subscription", {"name": "work", "purchased_at": "2026-10-25"})
                self.assertEqual(result["subscription"]["expires_at"], "2026-11-24")
                row = request("/api/list")["profiles"][0]
                self.assertEqual(row["subscription"]["purchased_at"], "2026-10-25")
                self.assertEqual(row["saved_at"], "2026-09-01")
                for body in ({"name": "work", "purchased_at": "2026-02-30"}, {"name": "../escape", "purchased_at": "2026-10-25"}):
                    with self.assertRaises(urllib.error.HTTPError) as error:
                        request("/api/local/subscription", body)
                    self.assertEqual(error.exception.code, 400)
                    error.exception.close()
                with self.assertRaises(urllib.error.HTTPError) as error:
                    request("/api/local/subscription", {"name": "work", "purchased_at": None}, token=False)
                self.assertEqual(error.exception.code, 403)
                error.exception.close()
                cleared = request("/api/local/subscription", {"name": "work", "purchased_at": None})
                self.assertEqual(cleared["subscription"]["status"], "unknown")
            finally:
                process.terminate()
                process.wait(timeout=5)
