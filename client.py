#!/usr/bin/env python3
"""Read-only client for ChatGPT Your dot (internal name orbit / tbo).

Reads ~/.codex/auth.json and calls chatgpt.com/backend-api. Prints status
codes and field names only. Does not print tokens or save response bodies.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = "https://chatgpt.com/backend-api"
AUTH_PATH = os.path.expanduser("~/.codex/auth.json")

# Confirmed with GET on 2026-10-01 against ChatGPT app 26.715's backend.
READS_PER_DOT = (
    "/threads",
    "/activity",
    "/root-thread",
    "/computers",
    "/environment/status",
    "/automations",
    "/channels/email",
)


def load_auth(path: str = AUTH_PATH) -> tuple[str, str]:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("auth_mode") != "chatgpt":
        raise SystemExit(f"expected auth_mode chatgpt in {path}")
    tokens = data.get("tokens") or {}
    access = tokens.get("access_token")
    account = tokens.get("account_id")
    if not access or not account:
        raise SystemExit(f"missing access_token or account_id in {path}")
    return access, account


def request_json(access: str, account: str, path: str) -> tuple[int, object | None]:
    last: tuple[int, object | None] = (0, None)
    for attempt in range(2):
        req = urllib.request.Request(
            BASE + path,
            headers={
                "Authorization": f"Bearer {access}",
                "ChatGPT-Account-Id": account,
                "Accept": "application/json",
                "User-Agent": "Codex Desktop",
                "originator": "Codex Desktop",
                "OAI-Product-Sku": "CODEX",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                status = resp.status
                body = resp.read()
        except urllib.error.HTTPError as exc:
            status = exc.code
            body = exc.read()
        if not body:
            last = (status, None)
        else:
            try:
                last = (status, json.loads(body.decode("utf-8")))
            except json.JSONDecodeError:
                last = (status, None)
        # A burst of reads sometimes gets an HTML 403. A JSON 403 is a real answer.
        if status in (403, 429, 503) and last[1] is None and attempt == 0:
            time.sleep(1)
            continue
        return last
    return last


def field_lines(value: object, prefix: str = "", depth: int = 0) -> list[str]:
    if depth > 2:
        return []
    lines: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(item, dict):
                lines.append(f"{path}: object")
                lines.extend(field_lines(item, path, depth + 1))
            elif isinstance(item, list):
                lines.append(f"{path}: list[{len(item)}]")
                if item and isinstance(item[0], dict):
                    lines.extend(field_lines(item[0], path + "[]", depth + 1))
            else:
                lines.append(f"{path}: {type(item).__name__}")
    return lines


def report(label: str, status: int, payload: object | None) -> None:
    print(f"{status} {label}")
    if payload is None:
        print("  non-json")
        return
    for line in field_lines(payload)[:24]:
        print(f"  {line}")


def dot_label(item: dict) -> str:
    name = (item.get("display_name") or "").strip()
    return name or "Your dot"


def main() -> int:
    access, account = load_auth()
    status, usage = request_json(access, account, "/wham/usage")
    plan = usage.get("plan_type") if isinstance(usage, dict) else None
    print(f"{status} GET /wham/usage plan_type={plan}")

    status, primary = request_json(access, account, "/tbo/primary")
    report("GET /tbo/primary", status, primary)

    status, listing = request_json(access, account, "/tbo")
    items = listing.get("items") if isinstance(listing, dict) else None
    count = len(items) if isinstance(items, list) else 0
    print(f"{status} GET /tbo items={count}")
    if not isinstance(items, list):
        return 1 if status != 200 else 0

    for item in items:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        dot_id = item["id"]
        print(
            "dot"
            f" name={dot_label(item)!r}"
            f" status={item.get('status')}"
            f" paused={item.get('is_paused')}"
            f" kind={item.get('aeon_kind')}"
        )
        detail_status, detail = request_json(access, account, f"/tbo/{dot_id}")
        report("GET /tbo/{id}", detail_status, detail)
        for suffix in READS_PER_DOT:
            code, payload = request_json(access, account, f"/tbo/{dot_id}{suffix}")
            report(f"GET /tbo/{{id}}{suffix}", code, payload)
        thread_id = item.get("active_root_thread_id")
        if isinstance(thread_id, str) and thread_id:
            code, payload = request_json(access, account, f"/tbo/by-thread/{thread_id}")
            report("GET /tbo/by-thread/{thread_id}", code, payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
