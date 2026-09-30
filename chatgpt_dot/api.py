"""The only HTTP client. GET for status, POST only to talk to a dot."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

BASE = "https://chatgpt.com/backend-api"
AUTH_PATH = os.path.expanduser("~/.codex/auth.json")
_ID = r"[A-Za-z0-9][A-Za-z0-9._~-]{0,199}"
_DOT_SUFFIXES = (
    "threads",
    "activity",
    "root-thread",
    "computers",
    "environment/status",
    "automations",
    "channels/email",
)

GET_PATTERNS = (
    re.compile(r"^/wham/usage$"),
    re.compile(r"^/tbo$"),
    re.compile(r"^/tbo/primary$"),
    re.compile(rf"^/tbo/{_ID}$"),
    re.compile(rf"^/tbo/{_ID}/(?:{'|'.join(_DOT_SUFFIXES)})$"),
    re.compile(rf"^/tbo/by-thread/{_ID}$"),
    re.compile(rf"^/messaging/rooms/{_ID}/messages$"),
)
POST_PATTERNS = (
    re.compile(rf"^/messaging/rooms/{_ID}/messages$"),
    re.compile(rf"^/tbo/{_ID}/messaging-room$"),
)
SECRET_KEY = re.compile(
    r"token|secret|key|cookie|authorization|password|session",
    re.IGNORECASE,
)


class AuthError(Exception):
    pass


class ApiError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


def load_auth(path: str = AUTH_PATH) -> tuple[str, str]:
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except OSError as exc:
        raise AuthError(f"cannot read auth file: {exc.strerror}") from exc
    except json.JSONDecodeError as exc:
        raise AuthError("auth file is not valid json") from exc
    if data.get("auth_mode") != "chatgpt":
        raise AuthError("auth file is not a chatgpt login")
    tokens = data.get("tokens") or {}
    access = tokens.get("access_token")
    account = tokens.get("account_id")
    if not isinstance(access, str) or not access:
        raise AuthError("auth file has no access token")
    if not isinstance(account, str) or not account:
        raise AuthError("auth file has no account id")
    return access, account


def assert_allowed(method: str, path: str) -> None:
    if method == "GET":
        patterns = GET_PATTERNS
    elif method == "POST":
        patterns = POST_PATTERNS
    else:
        raise ApiError(f"method not allowed: {method}")
    if not any(pattern.fullmatch(path) for pattern in patterns):
        raise ApiError(f"path not allowed: {method} {path}")


def redact(value: object) -> object:
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            if SECRET_KEY.search(str(key)):
                cleaned[key] = "***"
            else:
                cleaned[key] = redact(item)
        return cleaned
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def request_json(
    access: str,
    account: str,
    path: str,
    method: str = "GET",
    body: dict | None = None,
    query: dict | None = None,
) -> tuple[int, object | None]:
    assert_allowed(method, path)
    url = BASE + path
    if query:
        url = url + "?" + urllib.parse.urlencode({k: v for k, v in query.items() if v is not None})
    payload = None if body is None else json.dumps(body).encode("utf-8")
    last: tuple[int, object | None] = (0, None)
    for attempt in range(2):
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Bearer {access}",
                "ChatGPT-Account-Id": account,
                "Accept": "application/json",
                "User-Agent": "Codex Desktop",
                "originator": "Codex Desktop",
                "OAI-Product-Sku": "CODEX",
                **({"Content-Type": "application/json"} if payload is not None else {}),
            },
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                status = resp.status
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            status = exc.code
            raw = exc.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            raise ApiError(f"network error: {getattr(exc, 'reason', exc)}") from exc
        if not raw:
            last = (status, None)
        else:
            try:
                last = (status, json.loads(raw.decode("utf-8")))
            except json.JSONDecodeError:
                last = (status, None)
        if status == 401:
            raise ApiError(
                "ChatGPT login expired (401). Open Codex or run `codex login`, then retry.",
                401,
            )
        if status in (403, 429, 503) and last[1] is None and attempt == 0:
            time.sleep(1)
            continue
        return last
    return last


def get_json(access: str, account: str, path: str, query: dict | None = None) -> tuple[int, object | None]:
    return request_json(access, account, path, "GET", query=query)


def post_json(access: str, account: str, path: str, body: dict) -> tuple[int, object | None]:
    return request_json(access, account, path, "POST", body=body)


def list_dots(access: str, account: str) -> list[dict]:
    status, payload = get_json(access, account, "/tbo")
    if status != 200 or not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise ApiError(f"GET /tbo failed ({status})", status)
    return [item for item in payload["items"] if isinstance(item, dict) and item.get("id")]


def resolve_dot(access: str, account: str, dot_id: str | None) -> dict:
    dots = list_dots(access, account)
    if dot_id:
        for item in dots:
            if item.get("id") == dot_id:
                return item
        raise ApiError("dot id was not found; run `chatgpt-dot-cli list` and pass --dot-id")
    if len(dots) == 1:
        return dots[0]
    if not dots:
        raise ApiError("no dot on this account")
    raise ApiError("more than one dot; run `chatgpt-dot-cli list` and pass --dot-id <id>")


def ensure_room(access: str, account: str, dot: dict) -> str:
    room = dot.get("messaging_room_id")
    if isinstance(room, str) and room:
        return room
    status, payload = post_json(access, account, f"/tbo/{dot['id']}/messaging-room", {})
    if not isinstance(payload, dict):
        raise ApiError(f"could not open messaging room ({status})", status)
    room = payload.get("messaging_room_id")
    if not isinstance(room, str) or not room:
        raise ApiError(f"messaging room missing ({status})", status)
    return room


def list_messages(access: str, account: str, room_id: str, limit: int = 20) -> list[dict]:
    status, payload = get_json(
        access,
        account,
        f"/messaging/rooms/{room_id}/messages",
        query={"limit": str(max(1, min(limit, 50)))},
    )
    if status != 200 or not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise ApiError(f"GET messages failed ({status})", status)
    return [item for item in payload["items"] if isinstance(item, dict)]


def send_message(access: str, account: str, room_id: str, text: str) -> dict:
    if not text.strip():
        raise ApiError("message text is empty")
    request_id = str(uuid.uuid4())
    status, payload = post_json(
        access,
        account,
        f"/messaging/rooms/{room_id}/messages",
        {
            "content": {"text": text, "attachments": []},
            "request_id": request_id,
            "idempotency_token": request_id,
        },
    )
    if status not in (200, 201) or not isinstance(payload, dict):
        code = None
        if isinstance(payload, dict):
            detail = payload.get("detail")
            if isinstance(detail, dict):
                code = detail.get("code")
        extra = f" {code}" if code else ""
        raise ApiError(f"send failed ({status}){extra}", status)
    return payload
