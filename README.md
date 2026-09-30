# chatgpt-dot

跟 ChatGPT 的 Your dot 讀狀態、看訊息、送文字。App 裡的內部名稱是 orbit，HTTP 資源叫 tbo。

登入用本機 `~/.codex/auth.json`（`auth_mode: chatgpt`）。Token 不進這個 repo、不進 MCP 設定、不印出來。

## 安裝

CLI 和 skill 是必要的。MCP 是可選的。

```bash
uv tool install --editable /Users/iml1s/Documents/mine/chatgpt-dot
chatgpt-dot --help
```

Skill 指到這個 repo，不要複製：

```bash
repo=/Users/iml1s/Documents/mine/chatgpt-dot/skills/chatgpt-dot
for d in \
  ~/.claude/skills \
  ~/.codex/skills \
  ~/.agents/skills \
  ~/.config/opencode/skills \
  ~/.config/opencode/skill \
  ~/.cursor/skills \
  ~/.grok/skills
do
  mkdir -p "$d"
  ln -sfn "$repo" "$d/chatgpt-dot"
done
```

`~/.claude/skills` 會連到 Gemini、Antigravity、Copilot、Kiro。Codex 和 OpenCode 也會讀 `~/.agents/skills`。

可選 MCP，已經用這條命令登記過的話不用再裝：

```bash
/Users/iml1s/.local/bin/uv run --project /Users/iml1s/Documents/mine/chatgpt-dot --extra mcp chatgpt-dot-mcp
```

## 使用

```bash
chatgpt-dot summary
chatgpt-dot messages
chatgpt-dot send "你好"
chatgpt-dot list
```

`summary` 是預設。`messages` 只讀，不會順便建立房間。`send` 才會在沒有房間時建立。`display_name` 是空字串時顯示 Your dot。email 頻道回 `ineligible` 代表這個帳號不能用 email。

在 repo 裡跑測試：

```bash
cd /Users/iml1s/Documents/mine/chatgpt-dot
python3 -m unittest discover -s tests -v
```

## 已實測的讀取

基準是 `https://chatgpt.com/backend-api`，2026-10-01，ChatGPT App 26.715。

- `GET /wham/usage` 200
- `GET /tbo/primary` 200，`selection` 是目前選取，不是 dot 物件
- `GET /tbo` 200，dot id 在 `items[].id`，`aeon_kind` 是 `orbit`
- `GET /tbo/{id}`、`/threads`、`/activity`、`/root-thread`、`/computers`、`/environment/status`、`/automations` 200
- `GET /tbo/by-thread/{thread_id}` 200，thread id 用 `active_root_thread_id`
- `GET /messaging/rooms/{room_id}/messages` 200
- `POST /messaging/rooms/{room_id}/messages` 已實機送出成功
- `GET /tbo/{id}/channels/email` 403，`detail.code` 是 `ineligible`

把 `aeon_id` 當成 `/tbo/{id}` 會 404。登入過期時回 401，先跑 `codex login`。

## 沒有做的事

不暫停、不刪除、不連接電腦、不領 email、不打語音、不打 `/ps/orbit`。
