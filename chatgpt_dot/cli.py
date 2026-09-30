"""Command line for reading and messaging Your dot."""

from __future__ import annotations

import argparse
import sys

from chatgpt_dot.api import (
    ApiError,
    AuthError,
    ensure_room,
    get_json,
    list_dots,
    list_messages,
    load_auth,
    resolve_dot,
    send_message,
)
from chatgpt_dot.summaries import dot_name, dumps, field_lines, message_line

# Re-export the suffix tuple the probe prints. Defined here to avoid a cycle.
READS_PER_DOT = (
    "/threads",
    "/activity",
    "/root-thread",
    "/computers",
    "/environment/status",
    "/automations",
    "/channels/email",
)


def _auth(path: str) -> tuple[str, str]:
    try:
        return load_auth(path)
    except AuthError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc


def _detail_code(payload: object) -> str | None:
    if not isinstance(payload, dict):
        return None
    detail = payload.get("detail")
    if isinstance(detail, dict) and isinstance(detail.get("code"), str):
        return detail["code"]
    return None


def cmd_usage(access: str, account: str, as_json: bool) -> int:
    status, payload = get_json(access, account, "/wham/usage")
    if as_json:
        print(dumps({"status": status, "body": payload}))
        return 0 if status == 200 else 3
    plan = payload.get("plan_type") if isinstance(payload, dict) else None
    print(f"{status} GET /wham/usage plan_type={plan}")
    return 0 if status == 200 else 3


def cmd_primary(access: str, account: str, as_json: bool) -> int:
    status, payload = get_json(access, account, "/tbo/primary")
    if as_json:
        print(dumps({"status": status, "body": payload}))
    else:
        print(f"{status} GET /tbo/primary")
        for line in field_lines(payload)[:24]:
            print(f"  {line}")
    return 0 if status == 200 else 3


def cmd_list(access: str, account: str, as_json: bool) -> int:
    dots = list_dots(access, account)
    if as_json:
        print(dumps(dots))
        return 0
    for item in dots:
        print(
            f"{dot_name(item)} status={item.get('status')} "
            f"paused={item.get('is_paused')} kind={item.get('aeon_kind')}"
        )
    print(f"{len(dots)} dot(s)")
    return 0


def cmd_show(access: str, account: str, dot_id: str | None, as_json: bool) -> int:
    dot = resolve_dot(access, account, dot_id)
    status, payload = get_json(access, account, f"/tbo/{dot['id']}")
    if as_json:
        print(dumps({"status": status, "body": payload}))
    else:
        print(f"{status} {dot_name(dot)}")
        for line in field_lines(payload)[:24]:
            print(f"  {line}")
    return 0 if status == 200 else 3


def _suffix(access: str, account: str, dot_id: str | None, suffix: str, as_json: bool) -> int:
    dot = resolve_dot(access, account, dot_id)
    status, payload = get_json(access, account, f"/tbo/{dot['id']}{suffix}")
    info = status == 403 and suffix == "/channels/email" and _detail_code(payload) == "ineligible"
    if as_json:
        print(dumps({"status": status, "body": payload, "info": info}))
    else:
        print(f"{status} GET /tbo/{{id}}{suffix}")
        if info:
            print("  email channel ineligible")
        for line in field_lines(payload)[:24]:
            print(f"  {line}")
    if info:
        return 0
    return 0 if status == 200 else 3


def cmd_messages(access: str, account: str, dot_id: str | None, limit: int, as_json: bool) -> int:
    dot = resolve_dot(access, account, dot_id)
    room = ensure_room(access, account, dot)
    items = list_messages(access, account, room, limit)
    if as_json:
        print(dumps(items))
        return 0
    print(f"{dot_name(dot)} messages={len(items)}")
    for item in reversed(items):
        print(message_line(item))
    return 0


def cmd_send(access: str, account: str, dot_id: str | None, text: str, as_json: bool) -> int:
    dot = resolve_dot(access, account, dot_id)
    room = ensure_room(access, account, dot)
    payload = send_message(access, account, room, text)
    if as_json:
        print(dumps(payload))
    else:
        print(f"sent to {dot_name(dot)} role={payload.get('role')}")
    return 0


def cmd_by_thread(access: str, account: str, thread_id: str | None, dot_id: str | None, as_json: bool) -> int:
    if not thread_id:
        dot = resolve_dot(access, account, dot_id)
        thread_id = dot.get("active_root_thread_id")
        if not isinstance(thread_id, str) or not thread_id:
            raise ApiError("dot has no active root thread")
    status, payload = get_json(access, account, f"/tbo/by-thread/{thread_id}")
    if as_json:
        print(dumps({"status": status, "body": payload}))
    else:
        print(f"{status} GET /tbo/by-thread/{{thread_id}}")
        for line in field_lines(payload)[:24]:
            print(f"  {line}")
    return 0 if status == 200 else 3


def cmd_summary(access: str, account: str, as_json: bool) -> int:
    status, usage = get_json(access, account, "/wham/usage")
    plan = usage.get("plan_type") if isinstance(usage, dict) else None
    _, primary = get_json(access, account, "/tbo/primary")
    dots = list_dots(access, account)
    rows = []
    for item in dots:
        threads_status, threads = get_json(access, account, f"/tbo/{item['id']}/threads")
        activity_status, activity = get_json(access, account, f"/tbo/{item['id']}/activity")
        computers_status, computers = get_json(access, account, f"/tbo/{item['id']}/computers")
        auto_status, automations = get_json(access, account, f"/tbo/{item['id']}/automations")
        env_status, environment = get_json(access, account, f"/tbo/{item['id']}/environment/status")
        email_status, email = get_json(access, account, f"/tbo/{item['id']}/channels/email")
        room = item.get("messaging_room_id")
        recent = list_messages(access, account, room, 5) if isinstance(room, str) and room else []
        rows.append(
            {
                "name": dot_name(item),
                "status": item.get("status"),
                "paused": item.get("is_paused"),
                "kind": item.get("aeon_kind"),
                "threads": len(threads.get("items", [])) if isinstance(threads, dict) else None,
                "threads_http": threads_status,
                "activity": len(activity.get("data", [])) if isinstance(activity, dict) else None,
                "activity_http": activity_status,
                "computers": len(computers.get("computers", [])) if isinstance(computers, dict) else None,
                "computers_http": computers_status,
                "automations": len(automations.get("items", [])) if isinstance(automations, dict) else None,
                "automations_http": auto_status,
                "environment": environment.get("status") if isinstance(environment, dict) else None,
                "environment_http": env_status,
                "email": _detail_code(email) or email_status,
                "recent": [message_line(message, 120) for message in reversed(recent)],
            }
        )
    if as_json:
        print(dumps({"plan_type": plan, "usage_http": status, "primary": primary, "dots": rows}))
        return 0
    print(f"plan_type={plan}")
    selection = primary.get("selection") if isinstance(primary, dict) else None
    available = selection.get("available") if isinstance(selection, dict) else None
    print(f"primary available={available}")
    for row in rows:
        print(
            f"{row['name']} status={row['status']} paused={row['paused']} kind={row['kind']} "
            f"threads={row['threads']} activity={row['activity']} computers={row['computers']} "
            f"automations={row['automations']} environment={row['environment']} email={row['email']}"
        )
        for line in row["recent"]:
            print(f"  {line}")
    return 0


def cmd_probe(access: str, account: str) -> int:
    usage_status, usage = get_json(access, account, "/wham/usage")
    plan = usage.get("plan_type") if isinstance(usage, dict) else None
    print(f"{usage_status} GET /wham/usage plan_type={plan}")
    primary_status, primary = get_json(access, account, "/tbo/primary")
    print(f"{primary_status} GET /tbo/primary")
    for line in field_lines(primary)[:24]:
        print(f"  {line}")
    dots = list_dots(access, account)
    print(f"200 GET /tbo items={len(dots)}")
    for item in dots:
        print(
            "dot"
            f" name={dot_name(item)!r}"
            f" status={item.get('status')}"
            f" paused={item.get('is_paused')}"
            f" kind={item.get('aeon_kind')}"
        )
        detail_status, detail = get_json(access, account, f"/tbo/{item['id']}")
        print(f"{detail_status} GET /tbo/{{id}}")
        for line in field_lines(detail)[:24]:
            print(f"  {line}")
        for suffix in READS_PER_DOT:
            code, payload = get_json(access, account, f"/tbo/{item['id']}{suffix}")
            print(f"{code} GET /tbo/{{id}}{suffix}")
            for line in field_lines(payload)[:24]:
                print(f"  {line}")
        thread_id = item.get("active_root_thread_id")
        if isinstance(thread_id, str) and thread_id:
            code, payload = get_json(access, account, f"/tbo/by-thread/{thread_id}")
            print(f"{code} GET /tbo/by-thread/{{thread_id}}")
            for line in field_lines(payload)[:24]:
                print(f"  {line}")
        room = item.get("messaging_room_id")
        if isinstance(room, str) and room:
            items = list_messages(access, account, room, 5)
            print(f"200 GET /messaging/rooms/{{id}}/messages items={len(items)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read and message your ChatGPT dot.")
    parser.add_argument("--auth", default=None, help="path to auth.json")
    parser.add_argument("--json", action="store_true", help="print redacted JSON")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("summary", help="plan, dot status, and recent messages")
    sub.add_parser("usage")
    sub.add_parser("primary")
    sub.add_parser("list")
    sub.add_parser("probe", help="status codes and field names for every read")

    show = sub.add_parser("show")
    show.add_argument("dot_id", nargs="?")

    for name in (
        "threads",
        "activity",
        "root-thread",
        "computers",
        "env",
        "automations",
        "email-status",
    ):
        cmd = sub.add_parser(name)
        cmd.add_argument("dot_id", nargs="?")

    by_thread = sub.add_parser("by-thread")
    by_thread.add_argument("thread_id", nargs="?")
    by_thread.add_argument("--dot-id")

    messages = sub.add_parser("messages")
    messages.add_argument("dot_id", nargs="?")
    messages.add_argument("--limit", type=int, default=20)

    send = sub.add_parser("send", help="send a text message to the dot")
    send.add_argument("text")
    send.add_argument("--dot-id")
    return parser


_SUFFIX = {
    "threads": "/threads",
    "activity": "/activity",
    "root-thread": "/root-thread",
    "computers": "/computers",
    "env": "/environment/status",
    "automations": "/automations",
    "email-status": "/channels/email",
}


def _split_globals(argv: list[str]) -> tuple[list[str], str | None, bool]:
    cleaned: list[str] = []
    auth_path = None
    as_json = False
    index = 0
    while index < len(argv):
        item = argv[index]
        if item == "--json":
            as_json = True
            index += 1
            continue
        if item == "--auth":
            if index + 1 >= len(argv):
                raise SystemExit(2)
            auth_path = argv[index + 1]
            index += 2
            continue
        cleaned.append(item)
        index += 1
    return cleaned, auth_path, as_json


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    raw = list(sys.argv[1:] if argv is None else argv)
    cleaned, auth_path, as_json = _split_globals(raw)
    args = parser.parse_args(cleaned)
    command = args.command or "summary"
    access, account = load_auth(auth_path) if auth_path else _auth_default()
    try:
        if command == "summary":
            return cmd_summary(access, account, as_json)
        if command == "usage":
            return cmd_usage(access, account, as_json)
        if command == "primary":
            return cmd_primary(access, account, as_json)
        if command == "list":
            return cmd_list(access, account, as_json)
        if command == "show":
            return cmd_show(access, account, args.dot_id, as_json)
        if command == "probe":
            return cmd_probe(access, account)
        if command == "by-thread":
            return cmd_by_thread(access, account, args.thread_id, args.dot_id, as_json)
        if command == "messages":
            return cmd_messages(access, account, args.dot_id, args.limit, as_json)
        if command == "send":
            return cmd_send(access, account, args.dot_id, args.text, as_json)
        if command in _SUFFIX:
            return _suffix(access, account, args.dot_id, _SUFFIX[command], as_json)
    except AuthError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except ApiError as exc:
        print(str(exc), file=sys.stderr)
        return 3
    parser.error(f"unknown command {command}")
    return 2


def _auth_default() -> tuple[str, str]:
    try:
        return load_auth()
    except AuthError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc
