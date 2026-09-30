---
name: chatgpt-dot-cli
description: >-
  Read and message the user's ChatGPT Your dot (orbit, tbo) with the
  chatgpt-dot-cli CLI. Use chatgpt-dot-cli MCP tools only if they are already
  connected in this session. Use when the user asks about Your dot, dot status,
  dot messages, ChatGPT usage, orbit, tbo, dot threads, activity, computers, or
  wants to send a message to their dot. 用 chatgpt-dot-cli 讀取或傳訊息給使用者的
  ChatGPT Your dot：當使用者問到 Your dot、dot 狀態、dot 訊息、ChatGPT 用量、
  orbit、tbo、dot 的 threads、活動、電腦，或想傳訊息給 dot 時使用。
  Do not ask the user to install or enable MCP. 不要要求使用者安裝或啟用 MCP。
---

# ChatGPT Your dot

This CLI is a local client for the user's official ChatGPT Your dot. It is not a second dot. The desktop app calls the dot orbit; the HTTP resource is tbo.

## English

1. CLI first. Quick check: run `chatgpt-dot-cli list` (about 3 seconds). If it is not on PATH, try `~/.local/bin/chatgpt-dot-cli list`.
2. If neither exists, install it, then run `chatgpt-dot-cli list` again:

   ```bash
   uv tool install git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.1.3
   ```

3. Run `summary` only when the user asks for status.
4. Use `chatgpt-dot-cli` MCP tools only if they are already connected in this session. Do not ask the user to install or enable MCP.

"Your dot" is the default name, shown when `display_name` is empty. After the user renames the dot in the ChatGPT app, the CLI prints the new name.

`messages` labels each line `dot:` (the dot spoke) or `you:` (the user spoke). In JSON, `role` is always `user`; never use it to tell who spoke.

## 中文

1. CLI 優先。快速檢查：跑 `chatgpt-dot-cli list`（大約 3 秒）。PATH 上找不到的話，試 `~/.local/bin/chatgpt-dot-cli list`。
2. 兩個都沒有，就先用 `uv tool install git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.1.3` 安裝，再跑一次 `chatgpt-dot-cli list`。
3. 使用者問狀態時才跑 `summary`。
4. 只有這個 session 已經連上 `chatgpt-dot-cli` MCP 工具時才用 MCP。不要要求使用者安裝或啟用 MCP。

「Your dot」是預設名稱，`display_name` 是空的時候顯示。使用者在 ChatGPT app 裡幫 dot 改名後，CLI 會印出新的名字。

`messages` 每行用 `dot:`（dot 說的）或 `you:`（使用者說的）標示。JSON 裡的 `role` 永遠是 `user`，不能拿來判斷是誰說的。

## Commands

`--json` works before or after the command. `--limit` is capped at 50. Pass `--dot-id` when `list` shows more than one id.

- `list` — dots with ids (quick check)
- `summary` — plan type, status, and recent messages
- `messages` — recent messages with `dot:` / `you:` labels; does not create a room
- `send TEXT` — send a text message; `chatgpt-dot-cli send -- "-text starting with a dash"`
- `usage`, `primary`, `show`, `threads`, `activity`, `root-thread`, `computers`, `env`, `automations`, `email-status`
- `by-thread [THREAD_ID]` — find the dot for a thread
- `probe` — status codes and field names

## Rules / 規則

- Do not read `~/.codex/auth.json`, do not print tokens, and do not send your own HTTP requests to `chatgpt.com`. 不要讀 auth 檔、不要印 token、不要自己呼叫 `chatgpt.com`。
- The dot id comes from `list`. `aeon_id` is not a dot id. dot id 從 `list` 拿，`aeon_id` 不是 dot id。
- Send a text message only when the user asks you to talk to the dot. 使用者要你跟 dot 說話時才傳訊息。
- Messages sent from the CLI go to the dot's messaging inbox; the desktop main view can show them a little later. CLI 傳的訊息進訊息收件匣，桌面版主畫面可能晚一點才顯示。
- Local computer work still needs the ChatGPT desktop app open. 要 dot 在電腦上做事，ChatGPT 桌面版要開著。
- Refuse pause, resume, delete, connect, disconnect, email claim, and any change the user did not ask for. 拒絕暫停、恢復、刪除、連接、中斷、申請 email，以及使用者沒要求的任何變更。

## Troubleshooting / 排錯

- Exit 0 is OK. Exit 2: auth file missing or not a ChatGPT login. Exit 3: API or network error. 結束碼 0 正常；2 是 auth 檔不存在或不是 ChatGPT 登入；3 是 API 或網路錯誤。
- On 401, tell the user to run `codex login`. 出現 401 就請使用者跑 `codex login`。
- Email channel `403` with `ineligible` means this account cannot use email; that is expected. email `403` 加 `ineligible` 表示這個帳號不能用 email，屬正常。
- The command needs network access. 指令需要網路。
