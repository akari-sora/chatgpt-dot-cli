import contextlib
from email.message import Message
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import urllib.parse
import urllib.response

from chatgpt_dot.api import ApiError, send_message
from chatgpt_dot.cli import main


class SendValidationTests(unittest.TestCase):
    def run_send(self, text, dot_id=None):
        calls = []

        def transport(handler, http_class, req, **kwargs):
            path = urllib.parse.urlsplit(req.full_url).path.removeprefix("/backend-api")
            calls.append((req.get_method(), path, req.data))
            payloads = {
                "/tbo": {"items": [{"id": "dot_example", "display_name": "Example"}]},
                "/tbo/dot_example/messaging-room": {"messaging_room_id": "room_example"},
                "/messaging/rooms/room_example/messages": {"id": "message_example"},
            }
            response = urllib.response.addinfourl(
                io.BytesIO(json.dumps(payloads[path]).encode("utf-8")),
                Message(), req.full_url, 200,
            )
            response.msg = "OK"
            return response

        with tempfile.TemporaryDirectory() as tmp:
            auth = Path(tmp) / "auth.json"
            auth.write_text(json.dumps({
                "auth_mode": "chatgpt",
                "tokens": {"access_token": "fake-token", "account_id": "account_example"},
            }), encoding="utf-8")
            auth.chmod(0o600)
            argv = ["--auth", str(auth), "send"]
            if dot_id:
                argv += ["--dot-id", dot_id]
            out, err = io.StringIO(), io.StringIO()
            with (
                mock.patch("urllib.request.AbstractHTTPHandler.do_open", transport),
                contextlib.redirect_stdout(out),
                contextlib.redirect_stderr(err),
            ):
                code = main(argv + ["--", text])
        return code, out.getvalue(), err.getvalue(), calls

    def test_cli_blank_text_never_fetches_or_creates_room(self):
        for text, dot_id in (("   ", None), ("", None), ("\n\t ", "dot_example")):
            with self.subTest(text=text, dot_id=dot_id):
                code, out, err, calls = self.run_send(text, dot_id)
                self.assertEqual((code, out, err), (3, "", "message text is empty\n"))
                self.assertEqual(calls, [])

    def test_valid_text_creates_room_then_sends_unchanged_text(self):
        code, out, err, calls = self.run_send(" hello ")
        self.assertEqual((code, out, err), (0, "sent to Example\n", ""))
        self.assertEqual([(method, path) for method, path, _ in calls], [
            ("GET", "/tbo"),
            ("POST", "/tbo/dot_example/messaging-room"),
            ("POST", "/messaging/rooms/room_example/messages"),
        ])
        body = json.loads(calls[-1][2])
        self.assertEqual(body["content"]["text"], " hello ")
        self.assertEqual(body["request_id"], body["idempotency_token"])

    def test_api_rejects_invalid_text_before_post(self):
        for text in ("", "\t ", None, 1):
            with self.subTest(text=text), mock.patch("chatgpt_dot.api.post_json") as post:
                with self.assertRaisesRegex(ApiError, "^message text is empty$"):
                    send_message("fake-token", "account_example", "room_example", text)
                post.assert_not_called()

    def test_mcp_blank_text_rejects_before_auth_and_cache_clear(self):
        from chatgpt_dot.mcp_server import dot_send

        for text in ("", " \t\n", None, 1):
            with (
                self.subTest(text=text),
                mock.patch("chatgpt_dot.mcp_server.load_auth", return_value=("fake-token", "account_example")) as auth,
                mock.patch("chatgpt_dot.mcp_server._listed_dot", return_value={"id": "dot_example"}) as listed,
                mock.patch("chatgpt_dot.mcp_server.ensure_room", return_value="room_example") as room,
                mock.patch("chatgpt_dot.mcp_server.clear_dots_cache") as clear,
            ):
                with self.assertRaisesRegex(ApiError, "^message text is empty$"):
                    dot_send(text)
                auth.assert_not_called()
                listed.assert_not_called()
                room.assert_not_called()
                clear.assert_not_called()
