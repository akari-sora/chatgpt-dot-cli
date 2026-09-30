"""Local stdio MCP server. Optional. Read tools plus send, nothing else."""

from __future__ import annotations

import sys

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    FastMCP = None  # type: ignore[misc, assignment]

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
from chatgpt_dot.summaries import dot_name, dumps, message_line

mcp = FastMCP("chatgpt-dot") if FastMCP is not None else None
_READ = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True,
}
_SEND = {
    "readOnlyHint": False,
    "destructiveHint": False,
    "idempotentHint": False,
    "openWorldHint": True,
}


def _session() -> tuple[str, str]:
    try:
        return load_auth()
    except AuthError as exc:
        raise RuntimeError(str(exc)) from exc


def _fail(exc: Exception) -> str:
    return str(exc)


def _tool(annotations: dict):
    def wrap(fn):
        if mcp is None:
            return fn
        return mcp.tool(annotations=annotations)(fn)

    return wrap


@_tool(_READ)
def dot_summary() -> str:
    """Plan type, each dot's status, and the latest messages."""
    try:
        access, account = _session()
        status, usage = get_json(access, account, "/wham/usage")
        _, primary = get_json(access, account, "/tbo/primary")
        rows = []
        for item in list_dots(access, account):
            room = item.get("messaging_room_id")
            recent = (
                list_messages(access, account, room, 5)
                if isinstance(room, str) and room
                else []
            )
            rows.append(
                {
                    "name": dot_name(item),
                    "status": item.get("status"),
                    "paused": item.get("is_paused"),
                    "kind": item.get("aeon_kind"),
                    "id": item.get("id"),
                    "recent": [message_line(message, 160) for message in reversed(recent)],
                }
            )
        plan = usage.get("plan_type") if isinstance(usage, dict) else None
        return dumps({"usage_http": status, "plan_type": plan, "primary": primary, "dots": rows})
    except (ApiError, AuthError) as exc:
        return _fail(exc)


@_tool(_READ)
def dot_usage() -> str:
    """ChatGPT plan usage from GET /wham/usage."""
    try:
        access, account = _session()
        status, payload = get_json(access, account, "/wham/usage")
        return dumps({"status": status, "body": payload})
    except (ApiError, AuthError) as exc:
        return _fail(exc)


@_tool(_READ)
def dot_primary() -> str:
    """Current dot selection from GET /tbo/primary."""
    try:
        access, account = _session()
        status, payload = get_json(access, account, "/tbo/primary")
        return dumps({"status": status, "body": payload})
    except (ApiError, AuthError) as exc:
        return _fail(exc)


@_tool(_READ)
def dot_list() -> str:
    """List dots. The id field is the dot id; aeon_id is not."""
    try:
        access, account = _session()
        return dumps(list_dots(access, account))
    except (ApiError, AuthError) as exc:
        return _fail(exc)


def _one(path_suffix: str, dot_id: str | None) -> str:
    access, account = _session()
    dot = resolve_dot(access, account, dot_id or None)
    path = f"/tbo/{dot['id']}{path_suffix}"
    status, payload = get_json(access, account, path)
    return dumps({"status": status, "name": dot_name(dot), "body": payload})


@_tool(_READ)
def dot_get(dot_id: str | None = None) -> str:
    """Fetch one dot. Omit dot_id when the account has a single dot."""
    try:
        return _one("", dot_id)
    except (ApiError, AuthError) as exc:
        return _fail(exc)


@_tool(_READ)
def dot_threads(dot_id: str | None = None) -> str:
    """List the dot's threads."""
    try:
        return _one("/threads", dot_id)
    except (ApiError, AuthError) as exc:
        return _fail(exc)


@_tool(_READ)
def dot_activity(dot_id: str | None = None) -> str:
    """Recent activity for the dot."""
    try:
        return _one("/activity", dot_id)
    except (ApiError, AuthError) as exc:
        return _fail(exc)


@_tool(_READ)
def dot_root_thread(dot_id: str | None = None) -> str:
    """The dot's root thread id."""
    try:
        return _one("/root-thread", dot_id)
    except (ApiError, AuthError) as exc:
        return _fail(exc)


@_tool(_READ)
def dot_computers(dot_id: str | None = None) -> str:
    """Computers attached to the dot."""
    try:
        return _one("/computers", dot_id)
    except (ApiError, AuthError) as exc:
        return _fail(exc)


@_tool(_READ)
def dot_environment_status(dot_id: str | None = None) -> str:
    """Cloud environment status for the dot."""
    try:
        return _one("/environment/status", dot_id)
    except (ApiError, AuthError) as exc:
        return _fail(exc)


@_tool(_READ)
def dot_automations(dot_id: str | None = None) -> str:
    """Automations on the dot."""
    try:
        return _one("/automations", dot_id)
    except (ApiError, AuthError) as exc:
        return _fail(exc)


@_tool(_READ)
def dot_email_channel_status(dot_id: str | None = None) -> str:
    """Email channel status. 403 ineligible means the account cannot use email."""
    try:
        return _one("/channels/email", dot_id)
    except (ApiError, AuthError) as exc:
        return _fail(exc)


@_tool(_READ)
def dot_by_thread(thread_id: str | None = None, dot_id: str | None = None) -> str:
    """Resolve a dot from a thread id. Defaults to the dot's active root thread."""
    try:
        access, account = _session()
        if not thread_id:
            dot = resolve_dot(access, account, dot_id or None)
            thread_id = dot.get("active_root_thread_id")
            if not isinstance(thread_id, str) or not thread_id:
                return "dot has no active root thread"
        status, payload = get_json(access, account, f"/tbo/by-thread/{thread_id}")
        return dumps({"status": status, "body": payload})
    except (ApiError, AuthError) as exc:
        return _fail(exc)


@_tool(_READ)
def dot_messages(dot_id: str | None = None, limit: int = 20) -> str:
    """Recent messages with the dot, oldest last in the text list."""
    try:
        access, account = _session()
        dot = resolve_dot(access, account, dot_id or None)
        room = dot.get("messaging_room_id")
        if not isinstance(room, str) or not room:
            return "no messages yet (send creates the room)"
        items = list_messages(access, account, room, limit)
        return dumps(
            {
                "name": dot_name(dot),
                "lines": [message_line(item) for item in reversed(items)],
                "messages": items,
            }
        )
    except (ApiError, AuthError) as exc:
        return _fail(exc)


@_tool(_SEND)
def dot_send(text: str, dot_id: str | None = None) -> str:
    """Send a text message to the dot and return the created message."""
    try:
        access, account = _session()
        dot = resolve_dot(access, account, dot_id or None)
        room = ensure_room(access, account, dot)
        payload = send_message(access, account, room, text)
        return dumps({"name": dot_name(dot), "message": payload})
    except (ApiError, AuthError) as exc:
        return _fail(exc)


def main() -> None:
    if mcp is None:
        sys.exit(
            "MCP is optional. Run: uv run --project "
            "/Users/iml1s/Documents/mine/chatgpt-dot --extra mcp chatgpt-dot-mcp"
        )
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
