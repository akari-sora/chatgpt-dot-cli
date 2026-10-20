import inspect
import io
import typing
import unittest
from unittest import mock

from chatgpt_dot.cli import main


DEPRECATED = "chatgpt-dot-cli: warning: positional send text is deprecated; use --stdin\n"


class SendStdinTests(unittest.TestCase):
    def invoke(self, argv, *, stdin=""):
        out, err = io.StringIO(), io.StringIO()
        seen = {}

        def fake_send(access, account, room, text):
            seen["text"] = text
            return {"id": "message_example"}

        with (
            mock.patch("chatgpt_dot.cli.load_auth", return_value=("tok", "acct")) as auth,
            mock.patch(
                "chatgpt_dot.cli.resolve_dot",
                return_value={"id": "dot_example", "display_name": "Example"},
            ) as resolve,
            mock.patch("chatgpt_dot.cli.ensure_room", return_value="room_example") as room,
            mock.patch("chatgpt_dot.cli.send_message", side_effect=fake_send) as send,
            mock.patch("sys.stdout", out),
            mock.patch("sys.stderr", err),
            mock.patch("sys.stdin", io.StringIO(stdin)),
        ):
            try:
                code = main(argv)
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue(), err.getvalue(), seen, auth, resolve, room, send

    def test_stdin_sends_unchanged_text_without_deprecation(self):
        code, out, err, seen, auth, resolve, room, send = self.invoke(
            ["send", "--stdin"],
            stdin=" hello \nsecond line",
        )
        self.assertEqual((code, out, err), (0, "sent to Example\n", ""))
        self.assertEqual(seen["text"], " hello \nsecond line")
        auth.assert_called_once()
        resolve.assert_called_once()
        room.assert_called_once()
        send.assert_called_once()

    def test_stdin_json_prints_payload_not_deprecation(self):
        code, out, err, seen, *_ = self.invoke(["send", "--json", "--stdin"], stdin="hello")
        self.assertEqual((code, err, seen["text"]), (0, "", "hello"))
        self.assertIn('"id": "message_example"', out)

    def test_stdin_blank_rejects_before_network(self):
        for text in ("", "   ", "\n\t "):
            with self.subTest(text=repr(text)):
                code, out, err, seen, auth, resolve, room, send = self.invoke(
                    ["send", "--stdin"],
                    stdin=text,
                )
                self.assertEqual((code, out, err), (3, "", "message text is empty\n"))
                self.assertEqual(seen, {})
                auth.assert_called_once()
                resolve.assert_not_called()
                room.assert_not_called()
                send.assert_not_called()

    def test_positional_text_still_sends_and_warns(self):
        code, out, err, seen, *_ = self.invoke(["send", "--", "hello"])
        self.assertEqual((code, out, err, seen["text"]), (0, "sent to Example\n", DEPRECATED, "hello"))

    def test_positional_and_stdin_rejected_before_auth(self):
        code, out, err, seen, auth, resolve, room, send = self.invoke(
            ["send", "--stdin", "hello"],
            stdin="from-stdin",
        )
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("send cannot use --stdin with positional text", err)
        self.assertEqual(seen, {})
        auth.assert_not_called()
        resolve.assert_not_called()
        room.assert_not_called()
        send.assert_not_called()

    def test_missing_text_and_stdin_rejected_before_auth(self):
        code, out, err, seen, auth, resolve, room, send = self.invoke(["send"], stdin="ignored")
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("send requires message text or --stdin", err)
        self.assertEqual(seen, {})
        auth.assert_not_called()
        resolve.assert_not_called()
        room.assert_not_called()
        send.assert_not_called()

    def test_stdin_read_failure_does_not_echo_exception(self):
        class Broken(io.StringIO):
            def read(self, *args, **kwargs):
                raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "bad")

        out, err = io.StringIO(), io.StringIO()
        with (
            mock.patch("chatgpt_dot.cli.load_auth", side_effect=AssertionError("auth")) as auth,
            mock.patch("sys.stdout", out),
            mock.patch("sys.stderr", err),
            mock.patch("sys.stdin", Broken()),
        ):
            code = main(["send", "--stdin"])
        self.assertEqual(code, 2)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("cannot read send input; provide UTF-8 text on stdin", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())
        self.assertNotIn("utf-8", err.getvalue())
        auth.assert_not_called()

    def test_mcp_dot_send_signature_unchanged(self):
        from chatgpt_dot.mcp_server import dot_send

        params = inspect.signature(dot_send).parameters
        hints = typing.get_type_hints(dot_send)
        self.assertEqual(list(params), ["text", "dot_id"])
        self.assertEqual(hints["text"], str)
        self.assertEqual(params["dot_id"].default, None)
