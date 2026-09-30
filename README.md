# chatgpt-dot-cli

[![pipeline status](https://gitlab.com/aa22396584/chatgpt-dot-cli/badges/main/pipeline.svg)](https://gitlab.com/aa22396584/chatgpt-dot-cli/-/commits/main)

[中文](#中文) · [English](#english)

## 中文

`chatgpt-dot-cli` 是 ChatGPT 官方 Your dot 的本機 client，不是第二個 dot。它用你自己的 ChatGPT 登入，在終端機裡查看同一個 dot、讀訊息、傳文字。

「Your dot」是預設名稱：dot 的 `display_name` 是空的時候就顯示 Your dot。你在 ChatGPT app 裡幫 dot 改名後，CLI 會印出新的名字。

這個 repo 是公開的，任何人都可以安裝。

### 安裝

需要 Python 3.11 以上。用 uv，版本釘在 tag：

```bash
uv tool install git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.2.0
```

或用 pipx：

```bash
pipx install git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.2.0
```

執行 `chatgpt-dot-cli --help` 確認裝好了。找不到指令的話，把 `~/.local/bin` 加進 PATH。

升級時要重新指定 tag。`uv tool upgrade` 不會把已經釘在某個 tag 的安裝移到下一個 tag：

```bash
uv tool install --force git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.2.0
```

移除：

```bash
uv tool uninstall chatgpt-dot-cli
```

用 pipx 安裝的話：

```bash
pipx uninstall chatgpt-dot-cli
```

### 登入

CLI 讀 `~/.codex/auth.json`，這是 Codex CLI 用 ChatGPT 帳號登入後產生的檔案。沒有這個檔案，或出現 401，就執行 `codex login`。檔案放在別處的話用 `--auth 路徑`。Token 不會被印出來。

MCP 只讀 `~/.codex/auth.json`，沒有 `--auth`。

### 指令

沒有子指令時會印出說明並以結束碼 2 離開，不會呼叫 API，也不會跑 `summary`。完整指令見 `chatgpt-dot-cli --help`。

```bash
chatgpt-dot-cli list
chatgpt-dot-cli messages --limit 10
chatgpt-dot-cli messages --before MESSAGE_ID --limit 5
chatgpt-dot-cli send "你好"
```

- `messages` 的 `--limit` 預設 20，範圍是 1 到 32。超出範圍時結束碼為 2，而且不會送出請求。
- `--before` 和 `--after` 各接一個訊息 id，只取一頁。CLI 不送 `cursor`，也不會自動翻下一頁。
- `messages` 每行開頭是 `dot:`（dot 說的）或 `you:`（你說的）。房間預覽裡沒有帶 `aeon_id` 的成員時，會標成 `unknown:`，並在 stderr 留一行說明。
- `--json` 可放在指令前或後，但不能放在單獨的 `--` 後面。`messages --json` 永遠是物件，含 `name`、`lines`、`messages`。`messages` 是原始訊息，由舊到新；`lines` 是帶說話者的文字，由新到舊。沒有房間時兩個清單都是空的，並附上 `note`，結束碼為 0。JSON 裡的 `role` 永遠是 `user`，不代表是誰說的。
- 有多個 dot 時加 `--dot-id ID`（這是建議寫法），id 從 `list` 拿。`messages` 只接受 `--dot-id`，沒有位置參數。
- `summary` 預設會讀 activity。加上 `--no-activity` 就略過。
- 用 CLI 傳的訊息會進 dot 的訊息收件匣；桌面版主畫面可能晚一點才顯示。
- 要 dot 在你的電腦上做事，ChatGPT 桌面版仍然要開著。

### 結束碼

| 結束碼 | 意思 |
| --- | --- |
| 0 | 成功。email 頻道回 403 且 `ineligible` 也算成功 |
| 2 | 參數錯誤，或 auth 檔不存在、不是 ChatGPT 登入 |
| 3 | API 或網路錯誤 |

### 給 agent 用

先照上面裝好 CLI，再執行下面這段。它把 repo 以 tag `v0.2.0` clone 到 `~/.local/share/chatgpt-dot-cli`；目錄已經存在時改為 `fetch --tags` 再 `checkout --detach`。然後把 skill 連進各個 agent 的 skill 目錄。clone 失敗的話不會建立任何連結。目標路徑已存在而且不是 symlink 時，會在 stderr 印出跳過訊息，不覆蓋。

```bash
src="$HOME/.local/share/chatgpt-dot-cli"
if [ -d "$src/.git" ]; then
  git -C "$src" fetch --tags origin &&
  git -C "$src" checkout --detach v0.2.0
else
  git clone --branch v0.2.0 https://gitlab.com/aa22396584/chatgpt-dot-cli.git "$src"
fi && [ -f "$src/skills/chatgpt-dot-cli/SKILL.md" ] &&
for d in "$HOME/.claude/skills" "$HOME/.codex/skills" "$HOME/.agents/skills" \
         "$HOME/.config/opencode/skills" "$HOME/.config/opencode/skill" \
         "$HOME/.cursor/skills" "$HOME/.grok/skills"; do
  mkdir -p "$d" || exit 1
  dest="$d/chatgpt-dot-cli"
  if [ -e "$dest" ] && [ ! -L "$dest" ]; then
    echo "chatgpt-dot-cli: skip $dest (exists and is not a symlink)" >&2
    continue
  fi
  ln -sfn "$src/skills/chatgpt-dot-cli" "$dest"
done
```

給 agent 的規則：

- 用 `chatgpt-dot-cli` 指令。只有這個 session 已經連上 MCP 時才用 MCP。
- 不要自己讀 `~/.codex/auth.json`，也不要自己呼叫 `chatgpt.com`。

MCP 是可選的。需要的話用下面這行安裝，stdio 指令設成 `chatgpt-dot-cli-mcp`：

```bash
uv tool install --force "chatgpt-dot-cli[mcp] @ git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.2.0"
```

從這個 repo 的工作目錄做可編輯安裝：

```bash
uv pip install -e ".[mcp]"
```

### 不會做的事

不暫停、不刪除 dot，不連接或中斷電腦，不申請 email。

### 授權與 CI

MIT 授權，見 [LICENSE](LICENSE)。

CI 跑在這個專案自己的 runner 上，不用 GitLab 共用 runner。推上 tag 會建立 GitLab Release。本機跑測試：

```bash
python3 -m unittest discover -s tests -q
```

---

## English

`chatgpt-dot-cli` is a local client for the official ChatGPT Your dot, not a second dot. It uses your own ChatGPT login to check the same dot, read its messages, and send it text from a terminal.

"Your dot" is the default name: it is shown when the dot's `display_name` is empty. After you rename the dot in the ChatGPT app, the CLI prints the new name.

This repo is public. Anyone can install it.

### Install

Requires Python 3.11 or newer. With uv, pinned to a tag:

```bash
uv tool install git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.2.0
```

Or with pipx:

```bash
pipx install git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.2.0
```

Run `chatgpt-dot-cli --help` to check the install. If the command is not found, add `~/.local/bin` to your PATH.

To upgrade, install that tag again. `uv tool upgrade` will not move an install that is pinned to a tag:

```bash
uv tool install --force git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.2.0
```

Uninstall:

```bash
uv tool uninstall chatgpt-dot-cli
```

If you installed with pipx:

```bash
pipx uninstall chatgpt-dot-cli
```

### Login

The CLI reads `~/.codex/auth.json`, the file the Codex CLI writes after you log in with a ChatGPT account. If the file is missing, or you get a 401, run `codex login`. If the file lives elsewhere, pass `--auth PATH`. Tokens are never printed.

MCP reads only `~/.codex/auth.json`. It has no `--auth` flag.

### Commands

With no subcommand the CLI prints help and exits 2. It does not call the API, and it does not run `summary`. The full command list is `chatgpt-dot-cli --help`.

```bash
chatgpt-dot-cli list
chatgpt-dot-cli messages --limit 10
chatgpt-dot-cli messages --before MESSAGE_ID --limit 5
chatgpt-dot-cli send "hello"
```

- `messages --limit` defaults to 20 and must be from 1 to 32. A value outside that range exits 2 and does not send a request.
- `--before` and `--after` each take one message id and return a single page. The CLI does not send `cursor` and does not follow further pages.
- Each `messages` line starts with `dot:` (the dot spoke) or `you:` (you spoke). If the room preview has no member with `aeon_id`, the label is `unknown:` and stderr gets one note.
- `--json` may appear before or after the command, but not after a standalone `--`. `messages --json` is always an object with `name`, `lines`, and `messages`. `messages` holds the raw items, oldest to newest. `lines` are speaker-labeled and newest first. With no room, both lists are empty, `note` is set, and the exit code is 0. The JSON `role` is always `user` and does not tell you who spoke.
- With more than one dot, pass `--dot-id ID` (preferred) using an id from `list`. `messages` accepts only `--dot-id`; it has no positional id.
- `summary` fetches activity unless you pass `--no-activity`.
- Messages sent from the CLI go to the dot's messaging inbox; the desktop app's main view can show them a little later.
- For the dot to do work on your computer, the ChatGPT desktop app still needs to be open.

### Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Success. Email channel 403 `ineligible` is also success |
| 2 | Bad arguments, or the auth file is missing or not a ChatGPT login |
| 3 | API or network error |

### For agents

Install the CLI as above, then run this. It clones tag `v0.2.0` to `~/.local/share/chatgpt-dot-cli`. If that checkout already exists, it runs `fetch --tags` and `checkout --detach`. It then links the skill into each agent's skill directory. If the clone fails, no links are created. If a target already exists and is not a symlink, the script prints a skip message on stderr and leaves it alone.

```bash
src="$HOME/.local/share/chatgpt-dot-cli"
if [ -d "$src/.git" ]; then
  git -C "$src" fetch --tags origin &&
  git -C "$src" checkout --detach v0.2.0
else
  git clone --branch v0.2.0 https://gitlab.com/aa22396584/chatgpt-dot-cli.git "$src"
fi && [ -f "$src/skills/chatgpt-dot-cli/SKILL.md" ] &&
for d in "$HOME/.claude/skills" "$HOME/.codex/skills" "$HOME/.agents/skills" \
         "$HOME/.config/opencode/skills" "$HOME/.config/opencode/skill" \
         "$HOME/.cursor/skills" "$HOME/.grok/skills"; do
  mkdir -p "$d" || exit 1
  dest="$d/chatgpt-dot-cli"
  if [ -e "$dest" ] && [ ! -L "$dest" ]; then
    echo "chatgpt-dot-cli: skip $dest (exists and is not a symlink)" >&2
    continue
  fi
  ln -sfn "$src/skills/chatgpt-dot-cli" "$dest"
done
```

Rules for agents:

- Use the `chatgpt-dot-cli` command. Use MCP only if it is already connected in the session.
- Do not read `~/.codex/auth.json` or call `chatgpt.com` yourself.

MCP is optional. If you need it, install with the line below and set the stdio command to `chatgpt-dot-cli-mcp`:

```bash
uv tool install --force "chatgpt-dot-cli[mcp] @ git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.2.0"
```

From a checkout of this repo, the editable install is:

```bash
uv pip install -e ".[mcp]"
```

### What it will not do

It will not pause or delete a dot, connect or disconnect a computer, or claim email.

### License and CI

MIT, see [LICENSE](LICENSE).

CI runs on this project's own runner, not on GitLab shared runners. Pushing a tag creates a GitLab Release. To run the tests locally:

```bash
python3 -m unittest discover -s tests -q
```
