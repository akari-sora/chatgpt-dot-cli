---
name: chatgpt-dot-cli
description: >-
  Read and message the user's ChatGPT Your dot (orbit, tbo) with the
  chatgpt-dot-cli CLI. Use chatgpt-dot-cli MCP tools only if they are already
  connected in this session. Use when the user asks about Your dot, dot status,
  dot messages, ChatGPT usage, orbit, tbo, dot threads, activity, computers,
  automations, email, environment, or wants to send a message to their dot.
  Reply in the user's language. 用 chatgpt-dot-cli 讀取或傳訊息給使用者的
  ChatGPT Your dot：當使用者問到 Your dot、dot 狀態、dot 訊息、ChatGPT 用量、
  orbit、tbo、dot 的 threads、活動、電腦、自動化、email、環境，或想傳訊息給 dot 時使用。
  Do not ask the user to install or enable MCP. 不要要求使用者安裝或啟用 MCP。
---

# ChatGPT Your dot

This CLI is a local client for the user's official ChatGPT Your dot. It is not a second dot. The desktop app calls the dot orbit; the HTTP resource is tbo.

Reply in the user's language.

1. CLI first. Quick check: run `chatgpt-dot-cli list` (about 3 seconds). If it is not on PATH, try `~/.local/bin/chatgpt-dot-cli list`.
2. If neither exists, install it, then run `chatgpt-dot-cli list` again:

   ```bash
   uv tool install git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.2.0
   ```

3. Run `summary` only when the user asks for status. A bare `chatgpt-dot-cli` is not a summary: with no subcommand it prints help and exits 2, and it does not call the API.
4. Use `chatgpt-dot-cli` MCP tools only if they are already connected in this session. Do not ask the user to install or enable MCP.

"Your dot" is the default name, shown when `display_name` is empty. After the user renames the dot in the ChatGPT app, the CLI prints the new name.

`messages` labels each line `dot:` (the dot spoke) or `you:` (the user spoke). In JSON, `role` is always `user`; never use it to tell who spoke. If the room preview has no aeon member, lines say `unknown:` and stderr notes that. Do not guess from `role`.

## Commands

Run `chatgpt-dot-cli --help` for the full list. `--json` works before or after the command, but not after a standalone `--`. `--limit` defaults to 20 and must be from 1 to 32. `--before` and `--after` each take one message id and return a single page; the CLI does not send `cursor` and does not follow further pages. Pass `--dot-id` when `list` shows more than one id. On `messages`, `--dot-id` is the only form.

- `list` — dots with ids (quick check; this is the first command)
- `summary` — plan type, status, and recent messages; `--no-activity` skips activity
- `messages` — recent messages with `dot:` / `you:` labels; does not create a room. JSON `messages` are oldest to newest; `lines` are newest first
- `send TEXT` — send a text message; `chatgpt-dot-cli send -- "-text starting with a dash"`
- `usage`, `primary`, `show`, `threads`, `activity`, `root-thread`, `computers`, `env`, `automations`, `email-status`
- `by-thread [THREAD_ID]` — find the dot for a thread
- `probe` — status codes and field names; `--json` prints a status object

## Rules

- Do not read `~/.codex/auth.json`, do not print tokens, and do not send your own HTTP requests to `chatgpt.com`. MCP reads only `~/.codex/auth.json`.
- The dot id comes from `list`. `aeon_id` is not a dot id.
- Send a text message only when the user asks you to talk to the dot.
- Messages sent from the CLI go to the dot's messaging inbox; the desktop main view can show them a little later.
- Local computer work still needs the ChatGPT desktop app open.
- Refuse pause, resume, delete, connect, disconnect, email claim, and any change the user did not ask for.

## Troubleshooting

- Exit 0 is OK, including email channel `403` with `ineligible` (that account cannot use email).
- Exit 2: bad arguments, or the auth file is missing or not a ChatGPT login. `--limit` outside 1..32 is exit 2 and does not call the API. `--auth` without a path is exit 2.
- Exit 3: API or network error, including a non-JSON 403/429/503 after one retry (often Cloudflare).
- On 401, tell the user to run `codex login`.
- The command needs network access.
