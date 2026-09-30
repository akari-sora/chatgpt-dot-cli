# chatgpt-dot

跟 ChatGPT 的 Your dot 讀狀態、看訊息、送文字。App 裡的內部名稱是 orbit，HTTP 資源叫 tbo。

登入用本機 `~/.codex/auth.json`（`auth_mode: chatgpt`）。Token 不進這個 repo、不進 MCP 設定、不印出來。

```bash
uv run --project /Users/iml1s/Documents/mine/chatgpt-dot chatgpt-dot summary
uv run --project /Users/iml1s/Documents/mine/chatgpt-dot chatgpt-dot messages
uv run --project /Users/iml1s/Documents/mine/chatgpt-dot chatgpt-dot send "你好"
python3 -m chatgpt_dot summary
python3 client.py
```

`summary` 是預設。`messages` 讀最近對話。`send` 把文字送到 dot 的 messaging room。`display_name` 是空字串時顯示 Your dot。email 頻道回 `ineligible` 代表這個帳號不能用 email，不是程式壞掉。

## 已實測的讀取

基準是 `https://chatgpt.com/backend-api`，2026-10-01，ChatGPT App 26.715。

- `GET /wham/usage` 200
- `GET /tbo/primary` 200，`selection` 是目前選取，不是 dot 物件
- `GET /tbo` 200，dot id 在 `items[].id`，`aeon_kind` 是 `orbit`
- `GET /tbo/{id}`、`/threads`、`/activity`、`/root-thread`、`/computers`、`/environment/status`、`/automations` 200
- `GET /tbo/by-thread/{thread_id}` 200，thread id 用 `active_root_thread_id`
- `GET /messaging/rooms/{room_id}/messages` 200，`items[].role` 與 `content.text`
- `GET /tbo/{id}/channels/email` 403，`detail.code` 是 `ineligible`

把 `aeon_id` 當成 `/tbo/{id}` 會 404。

## 送訊

`POST /messaging/rooms/{room_id}/messages`，body 是 `content.text`、`request_id`、`idempotency_token`。房間 id 用 dot 的 `messaging_room_id`。沒有房間時才 `POST /tbo/{id}/messaging-room`。

## 沒有做的事

不暫停、不刪除、不連接電腦、不領 email、不打語音、不打 `/ps/orbit`。

## Agent

Skill 在 `skills/chatgpt-dot/SKILL.md`。MCP 指令是 `chatgpt-dot-mcp`，stdio，沒有 env。工具含讀取和 `dot_messages`、`dot_send`。
