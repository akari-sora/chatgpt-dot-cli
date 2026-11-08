from email.message import Message
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import urllib.error
import urllib.parse
import urllib.response

from chatgpt_dot.cli import main


class SendAttachTests(unittest.TestCase):
    def run_cli(self, argv, files, fail_upload=None):
        calls = []

        def transport(handler, http_class, req, **kwargs):
            path = urllib.parse.urlsplit(req.full_url).path.removeprefix("/backend-api")
            calls.append((req.get_method(), path, req.data, req.headers.get("Content-type")))
            if path.endswith("/files") and sum(1 for c in calls if c[1].endswith("/files")) == fail_upload:
                body = io.BytesIO(json.dumps({"detail": "Too Many Requests"}).encode())
                raise urllib.error.HTTPError(req.full_url, 429, "Too Many Requests", Message(), body)
            payloads = {
                "/tbo": {"items": [{"id": "dot_example", "display_name": "Example"}]},
                "/tbo/dot_example/messaging-room": {"messaging_room_id": "room_example"},
                "/messaging/rooms/room_example/files": {"id": "CalpicoFile_1", "file_id": "CalpicoFile_1", "status": "UPLOADED"},
                "/messaging/rooms/room_example/messages": {"id": "message_example"},
            }
            response = urllib.response.addinfourl(io.BytesIO(json.dumps(payloads[path]).encode()), Message(), req.full_url, 200)
            response.msg = "OK"
            return response

        with tempfile.TemporaryDirectory() as tmp:
            auth = Path(tmp) / "auth.json"
            auth.write_text(json.dumps({"auth_mode": "chatgpt", "tokens": {"access_token": "test-access", "account_id": "acct"}}))
            auth.chmod(0o600)
            paths = []
            for name, data in files:
                path = Path(tmp) / name
                path.write_bytes(data)
                paths.append(str(path))
            args = ["--auth", str(auth), *argv]
            for p in paths:
                args += ["--attach", p]
            with mock.patch("urllib.request.AbstractHTTPHandler.do_open", transport), \
                    mock.patch("sys.stdin", io.TextIOWrapper(io.BytesIO(b"unzip it"))), \
                    mock.patch("sys.stdout", io.StringIO()), mock.patch("sys.stderr", io.StringIO()) as err:
                code = main(args)
            return code, calls, err.getvalue()

    def test_files_upload_first_then_one_message_carries_their_ids(self):
        code, calls, err = self.run_cli(["send", "--stdin"], [("bundle.zip", b"PK\x03\x04zip")])
        self.assertEqual(code, 0, err)
        paths = [c[1] for c in calls]
        self.assertLess(paths.index("/messaging/rooms/room_example/files"), paths.index("/messaging/rooms/room_example/messages"))
        upload = next(c for c in calls if c[1].endswith("/files"))
        self.assertIn("multipart/form-data", upload[3])
        self.assertIn(b'filename="bundle.zip"', upload[2])
        sent = json.loads(next(c for c in calls if c[1].endswith("/messages"))[2])
        self.assertEqual(sent["content"]["attachments"], [{"type": "file", "file_id": "CalpicoFile_1"}])
        self.assertEqual(sent["content"]["text"], "unzip it")
        self.assertEqual(sent["request_id"], sent["idempotency_token"])
        self.assertIsInstance(sent["timezone_offset_min"], int)

    def test_signed_file_links_are_not_printed(self):
        from chatgpt_dot.api import redact

        shown = redact({"attachments": [{"file": {"download_url": "https://x.example/raw?sig=abc", "name": "b.zip"}}]})
        self.assertEqual(shown["attachments"][0]["file"], {"download_url": "***", "name": "b.zip"})

    def test_a_failed_upload_says_which_files_already_went_up_and_sends_no_message(self):
        code, calls, err = self.run_cli(["send", "--stdin"], [("a.zip", b"PK a"), ("b.zip", b"PK b")], fail_upload=2)
        self.assertEqual(code, 3)
        self.assertFalse(any(c[1].endswith("/messages") for c in calls))
        self.assertIn("429", err)
        self.assertIn("no message was sent", err)
        self.assertIn("1 of 2 files", err)
        code, calls, err = self.run_cli(["send", "--stdin"], [("a.zip", b"PK a")], fail_upload=1)
        self.assertEqual(code, 3)
        self.assertIn("no message was sent", err)
        self.assertNotIn("of 1 file", err)

    def test_a_missing_file_sends_nothing(self):
        code, calls, err = self.run_cli(["send", "--stdin", "--attach", "/nonexistent/x.zip"], [])
        self.assertEqual(code, 2)
        self.assertEqual(calls, [])
        self.assertIn("--attach needs a regular file", err)


if __name__ == "__main__":
    unittest.main()
