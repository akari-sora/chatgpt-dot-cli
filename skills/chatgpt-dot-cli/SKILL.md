---
name: chatgpt-dot-cli
description: >-
  Read and message the user's ChatGPT Your dot (orbit, tbo). Run the
  chatgpt-dot-cli CLI. If chatgpt-dot-cli MCP tools are already connected in this
  session, you may use them instead. Use when the user asks about Your dot,
  dot 狀態, ChatGPT 用量, orbit, tbo, dot threads, activity, computers, or
  wants to send a message to their dot. Do not ask the user to install or
  enable MCP.
---

# ChatGPT Your dot

Your dot is the always-on ChatGPT agent. The desktop app calls it orbit. The HTTP resource is tbo. The CLI is the default. MCP is optional and only used when it is already connected.

## How to talk to it

1. Run the CLI. Try these, in order, and stop at the first one that exists:

```bash
chatgpt-dot-cli summary
~/.local/bin/chatgpt-dot-cli summary
```

If neither exists, install it, then run `chatgpt-dot-cli summary` again:

```bash
uv tool install git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git
```

2. If `chatgpt-dot-cli` MCP tools are already connected in this session, you may use them instead. Do not ask the user to install or enable MCP.

## Commands

`--json` works before or after the command. `--limit` is capped at 50. Pass `--dot-id` when `chatgpt-dot-cli list` shows more than one id.

- `summary` — plan type, status, and recent messages
- `usage` — ChatGPT plan usage
- `primary` — which dot is selected
- `list` — dots with ids
- `show` — one dot's profile
- `messages` — recent messages; does not create a room
- `send TEXT` — send a text message; `chatgpt-dot-cli send -- "-text starting with a dash"`
- `threads`, `activity`, `root-thread`, `computers`, `env`, `automations`, `email-status`
- `by-thread [THREAD_ID]` — find the dot for a thread
- `probe` — status codes and field names

## Rules

- Do not read `~/.codex/auth.json` and do not print tokens.
- Do not write your own HTTP requests to `chatgpt.com`.
- The dot id comes from `chatgpt-dot-cli list`. `aeon_id` is not a dot id.
- An empty display name is shown as Your dot.
- Email channel `403` with `ineligible` means this account cannot use email. That is expected.
- You may send a text message when the user asks you to talk to the dot.
- Refuse pause, resume, delete, connect, disconnect, email claim, and any change the user did not ask for.

## Troubleshooting

- Exit 0 is OK. Exit 2 means the auth file is missing or not a ChatGPT login. Exit 3 is an API or network error.
- On 401, tell the user to run `codex login`. Never read the auth file.
- The command needs network access.
