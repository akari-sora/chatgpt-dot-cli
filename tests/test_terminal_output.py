"""Offline checks that CLI text and JSON stay free of raw terminal controls."""

from __future__ import annotations

import io
import json
import unicodedata
import unittest
from contextlib import ExitStack
from unittest import mock

from chatgpt_dot.api import ApiError, AuthError
from chatgpt_dot.cli import main
from chatgpt_dot.summaries import dumps, message_line


TEXT = "hi\x1b]52;c;ZXhhbXBsZQ==\x07there\x9b31m 👩\u200d💻"
VISIBLE = r"hi\x1b]52;c;ZXhhbXBsZQ==\x07there\u009b31m " + "👩\u200d💻"
NAME = "Ex\x1b[2J\x9bample"
VISIBLE_NAME = r"Ex\x1b[2J\u009bample"
JSON_TEXT = "DEL\x7f CSI\x9b31m OSC\x9d52;c;ZXhhbXBsZQ==\x9c DCS\x90example\x9c 👩\u200d💻"


def _dot():
    return {
        "id": "dot_example",
        "display_name": NAME,
        "messaging_room_id": "room_example",
        "messaging_room_preview": {
            "members": [{"account_user_id": "sender_example", "aeon_id": "aeon_example"}]
        },
    }


def _message():
    return {"role": "user", "account_user_id": "sender_example", "content": {"text": TEXT}}


class TerminalOutputTests(unittest.TestCase):
    def invoke(self, argv, stdin_text=None, **returns):
        out, err = io.StringIO(), io.StringIO()
        with ExitStack() as stack:
            stack.enter_context(mock.patch("chatgpt_dot.cli.load_auth", return_value=("fake", "account_example")))
            stack.enter_context(mock.patch("sys.stdout", out))
            stack.enter_context(mock.patch("sys.stderr", err))
            if stdin_text is not None:
                stack.enter_context(mock.patch("sys.stdin", io.StringIO(stdin_text)))
            for name, value in returns.items():
                stack.enter_context(mock.patch(f"chatgpt_dot.cli.{name}", return_value=value))
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def assert_display_safe(self, text):
        leftover = [char for char in text if unicodedata.category(char) == "Cc" and char != "\n"]
        self.assertEqual(leftover, [], repr(text))

    def test_serialized_json_escapes_cc_and_keeps_values(self):
        controls = "".join(chr(codepoint) for codepoint in list(range(32)) + list(range(127, 160)))
        payload = {"raw" + controls: controls + JSON_TEXT, "literal": r"\u009b", "text": "α👩\u200d💻"}
        encoded = dumps(payload)
        self.assert_display_safe(encoded)
        self.assertEqual(json.loads(encoded), payload)
        self.assertIn(r"\u007f", encoded)
        self.assertIn(r"\u009b", encoded)
        self.assertIn("α👩\u200d💻", encoded)
        self.assertTrue(encoded.startswith('{\n  "raw'))
        self.assertTrue(encoded.endswith("\n}"))

    def test_cli_json_stdout_escapes_display_and_preserves_values(self):
        payload = {"plan_type": JSON_TEXT, JSON_TEXT: TEXT}
        code, out, err = self.invoke(["usage", "--json"], get_json=(200, payload))
        self.assertEqual((code, err), (0, ""))
        self.assert_display_safe(out)
        self.assertEqual(json.loads(out), {"status": 200, "body": payload})
        item = dict(_message(), content={"text": JSON_TEXT})
        code, out, err = self.invoke(["messages", "--json"], resolve_dot=_dot(), list_messages=[item])
        self.assertEqual((code, err), (0, ""))
        self.assert_display_safe(out)
        self.assertEqual(json.loads(out)["messages"], [item])

    def test_mcp_json_escapes_display_and_preserves_values(self):
        from chatgpt_dot import mcp_server

        mcp_server.clear_dots_cache()
        self.addCleanup(mcp_server.clear_dots_cache)
        payload = {JSON_TEXT: TEXT, "plan_type": JSON_TEXT}
        item = dict(_message(), content={"text": JSON_TEXT})
        with (
            mock.patch("chatgpt_dot.mcp_server.load_auth", return_value=("fake", "account_example")),
            mock.patch("chatgpt_dot.mcp_server.get_json", return_value=(200, payload)),
            mock.patch("chatgpt_dot.mcp_server.list_dots", return_value=[_dot()]),
            mock.patch("chatgpt_dot.mcp_server.list_messages", return_value=[item]),
        ):
            usage_json = mcp_server.dot_usage()
            messages_json = mcp_server.dot_messages()
        self.assert_display_safe(usage_json)
        self.assert_display_safe(messages_json)
        self.assertEqual(json.loads(usage_json), {"status": 200, "body": payload})
        self.assertEqual(json.loads(messages_json)["messages"], [item])

    def test_message_line_escapes_controls_and_keeps_zwj(self):
        self.assertEqual(message_line(_message(), dot_ids={"sender_example"}), "dot: " + VISIBLE)

    def test_every_cc_character_is_visible_in_role(self):
        for codepoint in list(range(32)) + list(range(127, 160)):
            with self.subTest(codepoint=codepoint):
                escape = f"\\x{codepoint:02x}" if codepoint < 128 else f"\\u{codepoint:04x}"
                self.assertEqual(
                    message_line({"role": chr(codepoint), "content": {"text": "hello"}}),
                    escape + ": hello",
                )

    def test_message_whitespace_collapses_as_before(self):
        item = {"role": "dot", "content": {"text": " \nhello\t\r world\x1c\x1d\x1e\x1f\x85 next "}}
        self.assertEqual(message_line(item), "dot: hello world next")

    def test_truncation_precedes_escaping(self):
        for limit in (120, 160, 240):
            with self.subTest(limit=limit):
                item = {"role": "dot", "content": {"text": "a" * (limit - 2) + "\x1bmore"}}
                self.assertEqual(message_line(item, limit), "dot: " + "a" * (limit - 2) + r"\x1b" + "…")
                item["content"]["text"] = "a" * (limit - 1) + "\x1bmore"
                self.assertEqual(message_line(item, limit), "dot: " + "a" * (limit - 1) + "…")

    def test_messages_text_escapes_name_and_content(self):
        code, out, err = self.invoke(["messages"], resolve_dot=_dot(), list_messages=[_message()])
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, VISIBLE_NAME + " messages=1\ndot: " + VISIBLE + "\n")
        self.assert_display_safe(out)

    def test_messages_json_keeps_raw_name_and_text(self):
        code, out, err = self.invoke(["messages", "--json"], resolve_dot=_dot(), list_messages=[_message()])
        body = json.loads(out)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(body["name"], NAME)
        self.assertEqual(body["messages"], [_message()])
        self.assertEqual(body["lines"], ["dot: " + VISIBLE])

    def test_list_text_escapes_displayed_fields(self):
        item = {
            key: "Ex\x00\x07\x1b\x7f\x9b\n\tample"
            for key in ("id", "display_name", "status", "is_paused", "aeon_kind")
        }
        code, out, err = self.invoke(["list"], list_dots=[item])
        value = r"Ex\x00\x07\x1b\x7f\u009b\x0a\x09ample"
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, f"id={value} {value} status={value} paused={value} kind={value}\n1 dot(s)\n")
        self.assert_display_safe(out)

    def test_list_json_preserves_raw_fields(self):
        item = {key: TEXT for key in ("id", "display_name", "status", "is_paused", "aeon_kind")}
        code, out, err = self.invoke(["list", "--json"], list_dots=[item])
        self.assertEqual((code, err, json.loads(out)), (0, "", [item]))

    def test_usage_plan_text_and_raw_json(self):
        payload = {"plan_type": TEXT}
        code, out, err = self.invoke(["usage"], get_json=(200, payload))
        self.assertEqual((code, out, err), (0, "200 GET /wham/usage plan_type=" + VISIBLE + "\n", ""))
        code, out, err = self.invoke(["usage", "--json"], get_json=(200, payload))
        self.assertEqual(json.loads(out), {"status": 200, "body": payload})

    def test_field_paths_are_escaped_in_read_commands(self):
        payload = {TEXT: {NAME: [{TEXT: "value"}]}}
        for args in (["primary"], ["show"], ["threads"], ["by-thread", "thread_example"]):
            with self.subTest(args=args):
                code, out, err = self.invoke(
                    args, get_json=(200, payload), resolve_dot=_dot(), require_dot_id=_dot()
                )
                self.assertEqual((code, err), (0, ""))
                self.assertIn("  " + VISIBLE + ": object\n", out)
                self.assertIn(VISIBLE + "." + VISIBLE_NAME + "[]." + VISIBLE + ": str", out)
                self.assert_display_safe(out)
                code, out, err = self.invoke(
                    args + ["--json"], get_json=(200, payload), resolve_dot=_dot(), require_dot_id=_dot()
                )
                self.assertEqual(json.loads(out)["body"], payload)

    def test_send_confirmation_and_raw_payload(self):
        payload = {"content": {"text": TEXT}}
        code, out, err = self.invoke(
            ["send", "--stdin"],
            stdin_text="hello",
            resolve_dot=_dot(),
            ensure_room="room_example",
            send_message=payload,
        )
        self.assertEqual((code, out, err), (0, "sent to " + VISIBLE_NAME + "\n", ""))
        code, out, err = self.invoke(
            ["send", "--json", "--stdin"],
            stdin_text="hello",
            resolve_dot=_dot(),
            ensure_room="room_example",
            send_message=payload,
        )
        self.assertEqual(json.loads(out), payload)

    def test_failure_details_are_escaped_on_stderr(self):
        for detail in ({"code": TEXT}, [{"loc": ["query", NAME], "msg": TEXT}]):
            with self.subTest(detail=detail):
                payload = {"detail": detail}
                for args in (["usage"], ["usage", "--json"]):
                    code, out, err = self.invoke(args, get_json=(422, payload))
                    self.assertEqual(code, 3)
                    self.assertIn(VISIBLE, err)
                    self.assert_display_safe(err)
                    if "--json" in args:
                        self.assertEqual(json.loads(out)["body"], payload)

    def test_api_and_auth_error_text_is_escaped(self):
        for error, name, expected_code in ((ApiError(TEXT), "get_json", 3), (AuthError(TEXT), "load_auth", 2)):
            with self.subTest(error=type(error).__name__):
                with mock.patch(f"chatgpt_dot.cli.{name}", side_effect=error):
                    if name == "load_auth":
                        out, err = io.StringIO(), io.StringIO()
                        with mock.patch("sys.stdout", out), mock.patch("sys.stderr", err):
                            code = main(["usage"])
                        output, diagnostic = out.getvalue(), err.getvalue()
                    else:
                        code, output, diagnostic = self.invoke(["usage"])
                self.assertEqual((code, output, diagnostic), (expected_code, "", VISIBLE + "\n"))

    def test_server_detail_in_api_error_is_escaped(self):
        with mock.patch("chatgpt_dot.api.get_json", return_value=(500, {"detail": {"code": TEXT}})):
            code, out, err = self.invoke(["list"])
        self.assertEqual((code, out), (3, ""))
        self.assertIn("GET /tbo failed (500): " + VISIBLE, err)
        self.assert_display_safe(err)

    def _summary(self, as_json=False, problem=False):
        item = dict(_dot(), status=TEXT, is_paused=TEXT, aeon_kind=TEXT)
        top = [(200, {"plan_type": TEXT}), (200, {"selection": {"available": TEXT}}), (200, {"items": [item]})]
        if problem:
            top[0] = (500, {"plan_type": TEXT, "detail": {"code": TEXT}})

        def many(access, account, calls):
            if calls[0][0] == "/wham/usage":
                return top
            return [(200, {"status": TEXT, "detail": {"code": TEXT}, "items": [_message()]}) for _ in calls]

        with mock.patch("chatgpt_dot.cli.get_many", side_effect=many):
            return self.invoke(["summary"] + (["--json"] if as_json else []))

    def test_summary_text_escapes_values_and_recent(self):
        code, out, err = self._summary()
        self.assertEqual((code, err), (0, ""))
        for label in ("plan_type", "primary available", "status", "paused", "kind", "environment", "email"):
            self.assertIn(label + "=" + VISIBLE, out)
        self.assertIn(VISIBLE_NAME + " status=", out)
        self.assertIn("  dot: " + VISIBLE + "\n", out)
        self.assert_display_safe(out)

    def test_summary_json_keeps_raw_values_and_escapes_recent(self):
        code, out, err = self._summary(as_json=True)
        body = json.loads(out)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(body["plan_type"], TEXT)
        self.assertEqual(body["primary"]["selection"]["available"], TEXT)
        self.assertEqual(body["dots"][0]["name"], NAME)
        for field in ("status", "paused", "kind", "environment"):
            self.assertEqual(body["dots"][0][field], TEXT)
        self.assertEqual(body["dots"][0]["recent"], ["dot: " + VISIBLE])

    def test_summary_error_text_safe_and_json_raw(self):
        for as_json in (False, True):
            code, out, err = self._summary(as_json=as_json, problem=True)
            self.assertEqual(code, 3)
            self.assertEqual(err, "GET /wham/usage 500 " + VISIBLE + "\n")
            if as_json:
                self.assertEqual(json.loads(out)["plan_type"], TEXT)

    def _probe(self, as_json=False):
        item = dict(_dot(), status=TEXT, is_paused=TEXT, aeon_kind=TEXT, active_root_thread_id="thread_example")
        top = [(500, {"plan_type": TEXT}), (200, {TEXT: None}), (200, {"items": [item]})]

        def many(access, account, calls):
            if calls[0][0] == "/wham/usage":
                return top
            return [(200, {TEXT: None}) for _ in calls]

        with mock.patch("chatgpt_dot.cli.get_many", side_effect=many):
            return self.invoke(["probe"] + (["--json"] if as_json else []))

    def test_probe_text_safe_and_existing_repr_name_preserved(self):
        code, out, err = self._probe()
        self.assertEqual((code, err), (0, ""))
        self.assertIn("plan_type=" + VISIBLE, out)
        self.assertIn("name=" + repr(NAME), out)
        for label in ("status", "paused", "kind"):
            self.assertIn(label + "=" + VISIBLE, out)
        self.assertIn("  " + VISIBLE + ": NoneType\n", out)
        self.assert_display_safe(out)

    def test_probe_json_fields_are_raw(self):
        code, out, err = self._probe(as_json=True)
        body = json.loads(out)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(body["plan_type"], TEXT)
        self.assertEqual(body["dots"][0]["name"], NAME)
        for field in ("status", "paused", "kind"):
            self.assertEqual(body["dots"][0][field], TEXT)

    def test_mcp_messages_derived_lines_and_raw_fields(self):
        from chatgpt_dot import mcp_server

        mcp_server.clear_dots_cache()
        self.addCleanup(mcp_server.clear_dots_cache)
        with (
            mock.patch("chatgpt_dot.mcp_server.load_auth", return_value=("fake", "account_example")),
            mock.patch("chatgpt_dot.mcp_server.list_dots", return_value=[_dot()]),
            mock.patch("chatgpt_dot.mcp_server.list_messages", return_value=[_message()]),
        ):
            body = json.loads(mcp_server.dot_messages())
        self.assertEqual(body["name"], NAME)
        self.assertEqual(body["messages"], [_message()])
        self.assertEqual(body["lines"], ["dot: " + VISIBLE])

    def test_mcp_summary_derived_recent_and_raw_fields(self):
        from chatgpt_dot import mcp_server

        mcp_server.clear_dots_cache()
        self.addCleanup(mcp_server.clear_dots_cache)
        with (
            mock.patch("chatgpt_dot.mcp_server.load_auth", return_value=("fake", "account_example")),
            mock.patch(
                "chatgpt_dot.mcp_server.get_many",
                side_effect=[
                    [(200, {"plan_type": TEXT}), (200, {TEXT: NAME}), (200, {"items": [_dot()]})],
                    [(200, {"items": [_message()]})],
                ],
            ),
        ):
            body = json.loads(mcp_server.dot_summary())
        self.assertEqual(body["plan_type"], TEXT)
        self.assertEqual(body["primary"], {TEXT: NAME})
        self.assertEqual(body["dots"][0]["name"], NAME)
        self.assertEqual(body["dots"][0]["recent"], ["dot: " + VISIBLE])


if __name__ == "__main__":
    unittest.main()
