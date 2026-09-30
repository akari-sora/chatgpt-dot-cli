---
name: chatgpt-dot-cli
description: >-
  Read and message the user's ChatGPT Your dot (orbit, tbo). Run the
  chatgpt-dot-cli CLI. If chatgpt-dot-cli MCP tools are already connected in this
  session, you may use them instead. Use when the user asks about Your dot,
  dot status, ChatGPT usage, orbit, tbo, dot threads, activity, computers, or
  wants to send a message to their dot. 讀取或傳訊息給使用者的 ChatGPT
  Your dot：當使用者問到 Your dot、dot 狀態、dot 訊息、ChatGPT 用量、
  orbit、tbo、dot 的 threads、活動、電腦，或想傳訊息給 dot 時使用。
  Do not ask the user to install or enable MCP. 不要要求使用者安裝或啟用 MCP。
---

# ChatGPT Your dot

Your dot is the always-on ChatGPT agent. The desktop app calls it orbit. The HTTP resource is tbo. The CLI is the default. MCP is optional and only used when it is already connected.

## How to talk to it (English)

1. Run the CLI. Try these, in order, and stop at the first one that exists:

```bash
chatgpt-dot-cli list
~/.local/bin/chatgpt-dot-cli list
```

`list` takes about 3 seconds. Run `summary` only when the user asks for status.

If neither exists, install it, then run `chatgpt-dot-cli list` again:

```bash
uv tool install git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git
```

2. If `chatgpt-dot-cli` MCP tools are already connected in this session, you may use them instead. Do not ask the user to install or enable MCP.

In short: CLI first. Use MCP only if it is already connected.

## 怎麼跟它溝通

1. 用 CLI。依序試下面兩個，第一個能跑的就用：`chatgpt-dot-cli list`，然後 `~/.local/bin/chatgpt-dot-cli list`。`list` 大約 3 秒；使用者問狀態時才跑 `summary`。
2. 兩個都沒有的話，先用 `uv tool install git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git` 安裝，再跑一次 `chatgpt-dot-cli list`。
3. 只有這個 session 已經連上 `chatgpt-dot-cli` MCP 工具時，才可以改用 MCP。不要要求使用者安裝或啟用 MCP。

簡單說：CLI 優先，MCP 只在已經連上時才用。

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
- Message lines say `dot:` for the dot and `you:` for the user. In raw JSON, `role` is always `user`; do not use it to tell who spoke.
- 訊息行用 `dot:` 表示 dot 說的，`you:` 表示使用者說的。原始 JSON 的 `role` 永遠是 `user`，不能拿來判斷是誰說的。
- Email channel `403` with `ineligible` means this account cannot use email. That is expected.
- You may send a text message when the user asks you to talk to the dot.
- Refuse pause, resume, delete, connect, disconnect, email claim, and any change the user did not ask for.

## Troubleshooting

- Exit 0 is OK. Exit 2 means the auth file is missing or not a ChatGPT login. Exit 3 is an API or network error.
- On 401, tell the user to run `codex login`. Never read the auth file.
- The command needs network access.
