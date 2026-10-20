"""Login-file checks and token-container errors. Dummy credentials only."""

from __future__ import annotations

import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from chatgpt_dot.api import AuthError, load_auth
from chatgpt_dot.cli import main
from chatgpt_dot.platform import LoginFileError, _require_usable_login, open_auth_file

_LOGIN = {
    "auth_mode": "chatgpt",
    "tokens": {"access_token": "fake-token", "account_id": "account_example"},
}


def _write_login(path: Path, payload: object = _LOGIN, mode: int = 0o600) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    path.chmod(mode)
    return path


class TokenContainerTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.auth = Path(tmp.name) / "auth.json"

    def test_missing_tokens_still_reports_no_access_token(self):
        _write_login(self.auth, {"auth_mode": "chatgpt"})
        with self.assertRaises(AuthError) as caught:
            load_auth(self.auth)
        self.assertIn("auth file has no access token", str(caught.exception))

    def test_null_tokens_still_reports_no_access_token(self):
        _write_login(self.auth, {"auth_mode": "chatgpt", "tokens": None})
        with self.assertRaises(AuthError) as caught:
            load_auth(self.auth)
        self.assertIn("auth file has no access token", str(caught.exception))

    def test_malformed_tokens_are_auth_errors(self):
        for tokens in ([], "not-an-object", 1, True):
            with self.subTest(tokens=tokens):
                _write_login(self.auth, {"auth_mode": "chatgpt", "tokens": tokens})
                with self.assertRaises(AuthError) as caught:
                    load_auth(self.auth)
                message = str(caught.exception)
                self.assertIn("tokens", message)
                self.assertNotIn("Traceback", message)
                self.assertNotIn(str(self.auth), message)

    def test_valid_private_login_still_loads(self):
        _write_login(self.auth)
        self.assertEqual(load_auth(self.auth), ("fake-token", "account_example"))

    def test_windows_does_not_refuse_group_readable_mode(self):
        _write_login(self.auth, mode=0o644)
        info = os.stat(self.auth)
        with mock.patch("chatgpt_dot.platform.os.name", "nt"):
            _require_usable_login(info)


@unittest.skipUnless(os.name == "posix", "POSIX credential-descriptor checks")
class CredentialFileTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.auth = _write_login(self.root / "auth.json")

    def test_group_or_other_access_is_rejected(self):
        for mode in (0o644, 0o640, 0o604, 0o662):
            with self.subTest(mode=oct(mode)):
                self.auth.chmod(mode)
                with self.assertRaises(AuthError) as caught:
                    load_auth(self.auth)
                message = str(caught.exception)
                self.assertIn("group or other", message)
                self.assertIn("600", message)
                self.assertNotIn(str(self.root), message)

    def test_owner_only_modes_still_load(self):
        for mode in (0o600, 0o400, 0o700):
            with self.subTest(mode=oct(mode)):
                self.auth.chmod(mode)
                self.assertEqual(load_auth(self.auth), ("fake-token", "account_example"))

    def test_final_component_symlink_is_rejected(self):
        link = self.root / "link.json"
        link.symlink_to(self.auth)
        with self.assertRaises(AuthError) as caught:
            load_auth(link)
        message = str(caught.exception)
        self.assertIn("symbolic link", message)
        self.assertNotIn(str(self.root), message)

    def test_windows_rejects_symlink_before_open(self):
        link = self.root / "link.json"
        link.symlink_to(self.auth)
        with mock.patch("chatgpt_dot.platform.os.name", "nt"):
            with self.assertRaises(LoginFileError) as caught:
                open_auth_file(link)
        self.assertIn("symbolic link", str(caught.exception))

    def test_other_owner_is_rejected(self):
        with mock.patch("os.getuid", return_value=os.getuid() + 1):
            with self.assertRaises(AuthError) as caught:
                load_auth(self.auth)
        message = str(caught.exception)
        self.assertIn("owned by the current user", message)
        self.assertNotIn(str(self.root), message)

    def test_directory_is_rejected(self):
        folder = self.root / "auth-dir"
        folder.mkdir(mode=0o700)
        with self.assertRaises(AuthError) as caught:
            load_auth(folder)
        self.assertIn("regular file", str(caught.exception))

    def test_fifo_is_rejected_without_blocking(self):
        fifo = self.root / "fifo.json"
        os.mkfifo(fifo, 0o600)
        self.assertTrue(stat.S_ISFIFO(fifo.stat().st_mode))
        script = (
            "import sys\n"
            "from chatgpt_dot.api import AuthError, load_auth\n"
            "try:\n"
            "    load_auth(sys.argv[1])\n"
            "except AuthError as exc:\n"
            "    print(exc)\n"
            "    raise SystemExit(0)\n"
            "raise SystemExit(2)\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script, str(fifo)],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
            cwd=str(Path(__file__).resolve().parents[1]),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("regular file", result.stdout)
        self.assertNotIn(str(self.root), result.stdout)

    def test_cli_shared_mode_exits_2_without_api(self):
        self.auth.chmod(0o644)
        err = io.StringIO()
        with (
            mock.patch("chatgpt_dot.api._urlopen", side_effect=AssertionError("network")),
            mock.patch("sys.stderr", err),
        ):
            code = main(["--auth", str(self.auth), "list"])
        self.assertEqual(code, 2)
        text = err.getvalue()
        self.assertIn("group or other", text)
        self.assertNotIn("Traceback", text)
        self.assertNotIn(str(self.root), text)
        self.assertNotIn("fake-token", text)
