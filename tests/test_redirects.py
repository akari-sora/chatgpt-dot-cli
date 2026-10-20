"""Offline redirect checks. Fake transports only; no live service."""

from __future__ import annotations

import contextlib
import io
import json
import unittest
from email.message import Message
from unittest import mock
import urllib.request
import urllib.response

from chatgpt_dot import api
from chatgpt_dot.cli import main


class FakeTransport:
    """Swap HTTP/HTTPS handlers and keep urllib redirect and error handling."""

    def __init__(self, responses, proxies=None):
        self.responses = list(responses)
        self.requests = []
        fixture = self

        class FakeHTTP(urllib.request.HTTPHandler):
            def http_open(self, req):
                return fixture.open(req)

        class FakeHTTPS(urllib.request.HTTPSHandler):
            def https_open(self, req):
                return fixture.open(req)

        builder = getattr(api, "_build_opener", urllib.request.build_opener)
        self.opener = builder(urllib.request.ProxyHandler(proxies or {}), FakeHTTP(), FakeHTTPS())

    def open(self, req):
        self.requests.append(req)
        code, location, body = self.responses.pop(0) if self.responses else (200, None, b"{}")
        headers = Message()
        if location:
            headers["Location"] = location
        response = urllib.response.addinfourl(io.BytesIO(body), headers, req.full_url, code)
        response.msg = "fixture"
        return response

    @contextlib.contextmanager
    def install(self):
        if hasattr(api, "_OPENER"):
            with mock.patch.object(api, "_OPENER", self.opener):
                yield self
        else:
            with mock.patch("chatgpt_dot.api.urllib.request.urlopen", self.opener.open):
                yield self


class RedirectTests(unittest.TestCase):
    def test_production_opener_does_not_issue_a_second_request(self):
        fixture = FakeTransport(
            [
                (302, "https://other.invalid/outside", b""),
                (200, None, b"{}"),
            ]
        )

        def fake_do_open(handler, http_class, req, **kwargs):
            return fixture.open(req)

        with mock.patch("urllib.request.AbstractHTTPHandler.do_open", fake_do_open):
            result = api.get_json("fake-token", "account_example", "/wham/usage")
        self.assertEqual(len(fixture.requests), 1)
        self.assertEqual(result, (302, None))
        self.assertEqual(fixture.requests[0].full_url, api.BASE + "/wham/usage")

    def test_redirects_stop_for_each_code_method_and_destination(self):
        targets = (
            "https://other.invalid/outside",
            "http://other.invalid/outside",
            api.BASE + "/outside-allowlist",
        )
        for code in (301, 302, 303, 307, 308):
            for method in ("GET", "POST"):
                for target in targets:
                    with self.subTest(code=code, method=method, target=target):
                        path = "/wham/usage" if method == "GET" else "/messaging/rooms/room_example/messages"
                        body = None if method == "GET" else {"content": {"text": "hello"}}
                        fixture = FakeTransport([(code, target, b"")])
                        with fixture.install():
                            result = api.request_json("fake-token", "account_example", path, method, body)
                        self.assertEqual(len(fixture.requests), 1)
                        self.assertEqual(result, (code, None))
                        self.assertEqual(fixture.requests[0].full_url, api.BASE + path)
                        self.assertEqual(fixture.requests[0].get_method(), method)
                        self.assertEqual(fixture.requests[0].get_header("Authorization"), "Bearer fake-token")
                        self.assertEqual(
                            fixture.requests[0].get_header("Chatgpt-account-id"), "account_example"
                        )

    def test_send_reports_redirect_status_without_a_follow(self):
        fixture = FakeTransport([(302, "https://other.invalid/outside", b"")])
        with fixture.install(), self.assertRaisesRegex(api.ApiError, r"^send failed \(302\)$") as caught:
            api.send_message("fake-token", "account_example", "room_example", "hello")
        self.assertEqual(caught.exception.status, 302)
        self.assertEqual(len(fixture.requests), 1)

    def test_cli_usage_redirect_exits_three(self):
        fixture = FakeTransport([(302, "https://other.invalid/outside", b"")])
        out, err = io.StringIO(), io.StringIO()
        with (
            fixture.install(),
            mock.patch("chatgpt_dot.cli.load_auth", return_value=("fake-token", "account_example")),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            code = main(["usage"])
        self.assertEqual(code, 3)
        self.assertEqual(err.getvalue(), "GET /wham/usage 302\n")
        self.assertEqual(len(fixture.requests), 1)

    def test_success_and_expired_login_keep_existing_behavior(self):
        fixture = FakeTransport([(200, None, b'{"plan_type":"example"}')])
        with fixture.install():
            self.assertEqual(
                api.get_json("fake-token", "account_example", "/wham/usage"),
                (200, {"plan_type": "example"}),
            )
        fixture = FakeTransport([(401, None, b"{}")])
        with fixture.install(), self.assertRaises(api.ApiError) as caught:
            api.get_json("fake-token", "account_example", "/wham/usage")
        self.assertEqual(
            str(caught.exception),
            "ChatGPT login expired (401). Open Codex or run `codex login`, then retry.",
        )
        self.assertEqual(caught.exception.status, 401)
        self.assertEqual(len(fixture.requests), 1)

    def test_non_json_retry_keeps_body_and_fresh_ids_for_separate_sends(self):
        for code in (403, 429, 503):
            with self.subTest(code=code):
                fixture = FakeTransport(
                    [(code, None, b"not JSON"), (200, None, b'{"id":"message_example"}')]
                )
                with fixture.install(), mock.patch("chatgpt_dot.api.time.sleep") as sleep:
                    api.send_message("fake-token", "account_example", "room_example", "hello")
                    api.send_message("fake-token", "account_example", "room_example", "hello")
                sleep.assert_called_once_with(1)
                self.assertEqual(len(fixture.requests), 3)
                self.assertEqual(fixture.requests[0].data, fixture.requests[1].data)
                first = json.loads(fixture.requests[0].data)
                second = json.loads(fixture.requests[2].data)
                self.assertEqual(first["request_id"], first["idempotency_token"])
                self.assertNotEqual(first["request_id"], second["request_id"])

    def test_environment_proxy_handler_is_preserved(self):
        with mock.patch("urllib.request.getproxies", return_value={"https": "http://proxy.invalid:8443"}):
            builder = getattr(api, "_build_opener", urllib.request.build_opener)
            opener = builder()
        proxies = [
            handler.proxies
            for handler in opener.handlers
            if isinstance(handler, urllib.request.ProxyHandler)
        ]
        self.assertEqual(proxies, [{"https": "http://proxy.invalid:8443"}])
        fixture = FakeTransport([(200, None, b"{}")], proxies={"https": "http://proxy.invalid:8443"})
        with fixture.install(), mock.patch("urllib.request.proxy_bypass", return_value=False):
            self.assertEqual(api.get_json("fake-token", "account_example", "/wham/usage"), (200, {}))
        self.assertEqual(fixture.requests[0].host, "proxy.invalid:8443")


if __name__ == "__main__":
    unittest.main()
