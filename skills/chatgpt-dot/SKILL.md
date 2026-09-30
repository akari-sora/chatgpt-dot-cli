---
name: chatgpt-dot
description: >-
  Read and message the user's ChatGPT Your dot (orbit, tbo). Use when the user
  asks about Your dot, dot 狀態, ChatGPT 用量, orbit, tbo, dot threads, activity,
  computers, or wants to send a message to their dot. Prefer the chatgpt-dot
  MCP tools. Otherwise run the chatgpt-dot CLI. Do not call the HTTP API yourself.
---

# ChatGPT Your dot

Your dot is the always-on ChatGPT agent. The desktop app calls it orbit. The HTTP resource is tbo.

## How to talk to it

1. If the `chatgpt-dot` MCP server is connected, use its tools.
2. Otherwise run the CLI from `/Users/iml1s/Documents/mine/chatgpt-dot`:

```bash
uv run --project /Users/iml1s/Documents/mine/chatgpt-dot chatgpt-dot summary
uv run --project /Users/iml1s/Documents/mine/chatgpt-dot chatgpt-dot messages
uv run --project /Users/iml1s/Documents/mine/chatgpt-dot chatgpt-dot send "你的訊息"
```

`python3 -m chatgpt_dot` from that directory does the same thing.

## Rules

- Do not read `~/.codex/auth.json` and do not print tokens.
- Do not write your own HTTP requests to `chatgpt.com`.
- The dot id comes from `GET /tbo` `items[].id`. `aeon_id` is not a dot id.
- An empty display name is shown as Your dot.
- Email channel `403` with `ineligible` means this account cannot use email. That is expected.
- You may send a text message when the user asks you to talk to the dot.
- Refuse pause, resume, delete, connect, disconnect, email claim, and any change the user did not ask for. Those endpoints are not in this tool.
