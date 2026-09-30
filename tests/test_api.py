import io
import json
import unittest
import urllib.error
from unittest import mock

from chatgpt_dot.api import ApiError, assert_allowed, redact, request_json, resolve_dot, send_message
from chatgpt_dot.cli import main


class AllowlistTests(unittest.TestCase):
    def test_get_paths(self):
        assert_allowed("GET", "/wham/usage")
        assert_allowed("GET", "/tbo")
        assert_allowed("GET", "/tbo/primary")
        assert_allowed("GET", "/tbo/abc-123~def/threads")
        assert_allowed("GET", "/tbo/by-thread/abc")
        assert_allowed("GET", "/messaging/rooms/room1/messages")

    def test_post_only_talks(self):
        assert_allowed("POST", "/messaging/rooms/room1/messages")
        assert_allowed("POST", "/tbo/abc/messaging-room")
        with self.assertRaises(ApiError):
            assert_allowed("POST", "/tbo/abc/runtime/pause")
        with self.assertRaises(ApiError):
            assert_allowed("DELETE", "/tbo/abc")
        with self.assertRaises(ApiError):
            assert_allowed("GET", "/tbo/abc/../../wham/usage")
        with self.assertRaises(ApiError):
            assert_allowed("GET", "/ps/orbit/thread/teams")

    def test_bad_id(self):
        with self.assertRaises(ApiError):
            assert_allowed("GET", "/tbo/has space/threads")
        with self.assertRaises(ApiError):
            assert_allowed("POST", "/messaging/rooms/../messages")


class RedactTests(unittest.TestCase):
    def test_masks_secret_keys(self):
        cleaned = redact(
            {
                "id": "ok",
                "access_token": "secret",
                "nested": {"Authorization": "Bearer x", "role": "user"},
            }
        )
        self.assertEqual(cleaned["id"], "ok")
        self.assertEqual(cleaned["access_token"], "***")
        self.assertEqual(cleaned["nested"]["Authorization"], "***")
        self.assertEqual(cleaned["nested"]["role"], "user")


class RequestTests(unittest.TestCase):
    def test_request_is_get_and_hides_token(self):
        captured = {}

        class Response:
            status = 200

            def read(self):
                return b'{"items":[]}'

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def urlopen(req, timeout=0):
            captured["method"] = req.get_method()
            captured["url"] = req.full_url
            captured["auth"] = req.get_header("Authorization")
            return Response()

        with mock.patch("chatgpt_dot.api.urllib.request.urlopen", urlopen):
            status, payload = request_json("super-secret-token", "acct", "/tbo")
        self.assertEqual(status, 200)
        self.assertEqual(captured["method"], "GET")
        self.assertTrue(captured["url"].endswith("/tbo"))
        self.assertIn("super-secret-token", captured["auth"])
        self.assertNotIn("super-secret-token", json.dumps(payload))

    def test_blocked_before_network(self):
        def urlopen(*args, **kwargs):
            raise AssertionError("network")

        with mock.patch("chatgpt_dot.api.urllib.request.urlopen", urlopen):
            with self.assertRaises(ApiError):
                request_json("tok", "acct", "/tbo/x/runtime/pause", method="POST", body={})

    def test_json_403_is_not_retried(self):
        calls = {"n": 0}

        def urlopen(req, timeout=0):
            calls["n"] += 1
            raise urllib.error.HTTPError(
                req.full_url, 403, "no", hdrs=None, fp=io.BytesIO(b'{"detail":{"code":"ineligible"}}')
            )

        with mock.patch("chatgpt_dot.api.urllib.request.urlopen", urlopen):
            status, payload = request_json("tok", "acct", "/tbo/abc/channels/email")
        self.assertEqual(calls["n"], 1)
        self.assertEqual(status, 403)
        self.assertEqual(payload["detail"]["code"], "ineligible")


class ResolveTests(unittest.TestCase):
    def test_multi_dot_points_at_list(self):
        with mock.patch("chatgpt_dot.api.list_dots", return_value=[{"id": "a"}, {"id": "b"}]):
            with self.assertRaises(ApiError) as ctx:
                resolve_dot("t", "acct", None)
        self.assertIn("chatgpt-dot list", str(ctx.exception))

    def test_single_dot(self):
        with mock.patch(
            "chatgpt_dot.api.list_dots",
            return_value=[{"id": "dot-1", "display_name": ""}],
        ):
            dot = resolve_dot("a", "b", None)
        self.assertEqual(dot["id"], "dot-1")

    def test_send_posts_text(self):
        seen = {}

        def fake_post(access, account, path, body):
            seen["path"] = path
            seen["body"] = body
            seen["access"] = access
            return 200, {"id": "m1", "role": "user"}

        with mock.patch("chatgpt_dot.api.post_json", fake_post):
            payload = send_message("secret-token", "acct", "room1", "hello")
        self.assertEqual(seen["path"], "/messaging/rooms/room1/messages")
        self.assertEqual(seen["body"]["content"]["text"], "hello")
        self.assertEqual(seen["body"]["request_id"], seen["body"]["idempotency_token"])
        self.assertNotIn("secret-token", json.dumps(payload))


class ToolSurfaceTests(unittest.TestCase):
    def test_tool_names(self):
        import pathlib

        text = (pathlib.Path(__file__).resolve().parents[1] / "chatgpt_dot" / "mcp_server.py").read_text()
        names = set(__import__("re").findall(r"^def (dot_\w+)\(", text, __import__("re").M))
        self.assertEqual(
            names,
            {
                "dot_summary",
                "dot_usage",
                "dot_primary",
                "dot_list",
                "dot_get",
                "dot_threads",
                "dot_activity",
                "dot_root_thread",
                "dot_computers",
                "dot_environment_status",
                "dot_automations",
                "dot_email_channel_status",
                "dot_by_thread",
                "dot_messages",
                "dot_send",
            },
        )
        self.assertNotIn("runtime/pause", text)
        self.assertNotIn("/ps/orbit", text)


class CliOutputTests(unittest.TestCase):
    def test_list_does_not_print_token(self):
        dots = [{"id": "dot-1", "display_name": "", "status": "active", "is_paused": False, "aeon_kind": "orbit"}]
        buf = io.StringIO()
        err = io.StringIO()
        with (
            mock.patch("chatgpt_dot.cli.load_auth", return_value=("secret-token-value", "acct")),
            mock.patch("chatgpt_dot.cli.list_dots", return_value=dots),
            mock.patch("sys.stdout", buf),
            mock.patch("sys.stderr", err),
        ):
            code = main(["list"])
        text = buf.getvalue() + err.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("Your dot", text)
        self.assertIn("id=dot-1", text)
        self.assertNotIn("secret-token-value", text)

    def test_json_redacts(self):
        buf = io.StringIO()
        with (
            mock.patch("chatgpt_dot.cli.load_auth", return_value=("secret-token-value", "acct")),
            mock.patch(
                "chatgpt_dot.cli.get_json",
                return_value=(200, {"plan_type": "pro", "access_token": "secret-token-value"}),
            ),
            mock.patch("sys.stdout", buf),
        ):
            code = main(["usage", "--json"])
        text = buf.getvalue()
        self.assertEqual(code, 0)
        self.assertNotIn("secret-token-value", text)
        self.assertIn("***", text)

    def test_bad_auth_exits_2(self):
        err = io.StringIO()
        with mock.patch("sys.stderr", err):
            code = main(["--auth", "/no/such/auth.json", "list"])
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err.getvalue())

    def test_auth_equals_form(self):
        err = io.StringIO()
        with mock.patch("sys.stderr", err):
            code = main(["--auth=/no/such/auth.json", "list"])
        self.assertEqual(code, 2)

    def test_network_error_exits_3(self):
        import urllib.error

        err = io.StringIO()
        with (
            mock.patch("chatgpt_dot.cli.load_auth", return_value=("tok", "acct")),
            mock.patch(
                "chatgpt_dot.api.urllib.request.urlopen",
                side_effect=urllib.error.URLError("offline"),
            ),
            mock.patch("sys.stderr", err),
        ):
            code = main(["usage"])
        self.assertEqual(code, 3)
        self.assertIn("network error", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())

    def test_401_tells_user_to_login(self):
        err = io.StringIO()

        def urlopen(req, timeout=0):
            raise urllib.error.HTTPError(req.full_url, 401, "no", hdrs=None, fp=io.BytesIO(b"{}"))

        with (
            mock.patch("chatgpt_dot.cli.load_auth", return_value=("tok", "acct")),
            mock.patch("chatgpt_dot.api.urllib.request.urlopen", urlopen),
            mock.patch("sys.stderr", err),
        ):
            code = main(["list"])
        self.assertEqual(code, 3)
        self.assertIn("codex login", err.getvalue())

    def test_messages_does_not_create_room(self):
        dots = [{"id": "dot-1", "display_name": "", "messaging_room_id": None}]
        out = io.StringIO()
        with (
            mock.patch("chatgpt_dot.cli.load_auth", return_value=("tok", "acct")),
            mock.patch("chatgpt_dot.cli.resolve_dot", return_value=dots[0]),
            mock.patch("chatgpt_dot.cli.ensure_room", side_effect=AssertionError("posted")),
            mock.patch("sys.stdout", out),
        ):
            code = main(["messages"])
        self.assertEqual(code, 0)
        self.assertIn("no messages yet", out.getvalue())


if __name__ == "__main__":
    unittest.main()
