# chatgpt-dot-cli

[中文](#中文) · [English](#english)

## 中文

`chatgpt-dot-cli` 是 ChatGPT 官方 Your dot 的本機 client，不是第二個 dot。它用你自己的 ChatGPT 登入，在終端機裡查看同一個 dot、讀訊息、傳文字。

「Your dot」是預設名稱：dot 的 `display_name` 是空的時候就顯示 Your dot。你在 ChatGPT app 裡幫 dot 改名後，CLI 會印出新的名字。

### 安裝

需要 Python 3.11 以上。用 uv：

```bash
uv tool install git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.1.3
```

或用 pipx：

```bash
pipx install git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.1.3
```

執行 `chatgpt-dot-cli --help` 確認裝好了。找不到指令的話，把 `~/.local/bin` 加進 PATH。

### 登入

CLI 讀 `~/.codex/auth.json`，這是 Codex CLI 用 ChatGPT 帳號登入後產生的檔案。沒有這個檔案，或出現 401，就執行 `codex login`。檔案放在別處的話用 `--auth 路徑`。Token 不會被印出來。

### 指令

```bash
chatgpt-dot-cli summary        # 方案、dot 狀態、最近訊息
chatgpt-dot-cli messages       # 最近訊息
chatgpt-dot-cli send "你好"    # 傳文字給 dot
chatgpt-dot-cli list           # 列出你的 dot 和 id
```

- `messages` 每行開頭是 `dot:`（dot 說的）或 `you:`（你說的）。
- 加 `--json` 會輸出 JSON。JSON 裡的 `role` 永遠是 `user`，不代表是誰說的。
- 有多個 dot 時加 `--dot-id ID`，id 從 `list` 拿。
- 用 CLI 傳的訊息會進 dot 的訊息收件匣；桌面版主畫面可能晚一點才顯示。
- 要 dot 在你的電腦上做事，ChatGPT 桌面版仍然要開著。

### 給 agent 用

先照上面裝好 CLI，再執行下面這段。它把 repo clone 到 `~/.local/share/chatgpt-dot-cli`，再把 skill 連進各個 agent 的 skill 目錄。clone 失敗的話不會建立任何連結。

```bash
src="$HOME/.local/share/chatgpt-dot-cli"
if [ -d "$src/.git" ]; then
  git -C "$src" pull --ff-only
else
  git clone https://gitlab.com/aa22396584/chatgpt-dot-cli.git "$src"
fi && [ -f "$src/skills/chatgpt-dot-cli/SKILL.md" ] &&
for d in "$HOME/.claude/skills" "$HOME/.codex/skills" "$HOME/.agents/skills" \
         "$HOME/.config/opencode/skills" "$HOME/.config/opencode/skill" \
         "$HOME/.cursor/skills" "$HOME/.grok/skills"; do
  mkdir -p "$d" && ln -sfn "$src/skills/chatgpt-dot-cli" "$d/chatgpt-dot-cli"
done
```

給 agent 的規則：

- 用 `chatgpt-dot-cli` 指令。只有這個 session 已經連上 MCP 時才用 MCP。
- 不要自己讀 `~/.codex/auth.json`，也不要自己呼叫 `chatgpt.com`。

MCP 是可選的。需要的話用 `uv tool install "chatgpt-dot-cli[mcp] @ git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.1.3"` 安裝，stdio 指令設成 `chatgpt-dot-cli-mcp`。

### 不會做的事

不暫停、不刪除 dot，不連接或中斷電腦，不申請 email。

### 授權與 CI

MIT 授權，見 [LICENSE](LICENSE)。這個 repo 是公開的。

GitLab 有 runner 分鐘數時，CI 會跑測試；push tag 時設定成會建立 release。本機跑測試：

```bash
python3 -m unittest discover -s tests -q
```

---

## English

`chatgpt-dot-cli` is a local client for the official ChatGPT Your dot, not a second dot. It uses your own ChatGPT login to check the same dot, read its messages, and send it text from a terminal.

"Your dot" is the default name: it is shown when the dot's `display_name` is empty. After you rename the dot in the ChatGPT app, the CLI prints the new name.

### Install

Requires Python 3.11 or newer. With uv:

```bash
uv tool install git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.1.3
```

Or with pipx:

```bash
pipx install git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.1.3
```

Run `chatgpt-dot-cli --help` to check the install. If the command is not found, add `~/.local/bin` to your PATH.

### Login

The CLI reads `~/.codex/auth.json`, the file the Codex CLI writes after you log in with a ChatGPT account. If the file is missing, or you get a 401, run `codex login`. If the file lives elsewhere, pass `--auth PATH`. Tokens are never printed.

### Commands

```bash
chatgpt-dot-cli summary        # plan, dot status, recent messages
chatgpt-dot-cli messages       # recent messages
chatgpt-dot-cli send "hello"   # send text to the dot
chatgpt-dot-cli list           # list your dots and their ids
```

- Each `messages` line starts with `dot:` (the dot spoke) or `you:` (you spoke).
- Add `--json` for JSON output. The JSON `role` is always `user` and does not tell you who spoke.
- With more than one dot, add `--dot-id ID` using an id from `list`.
- Messages sent from the CLI go to the dot's messaging inbox; the desktop app's main view can show them a little later.
- For the dot to do work on your computer, the ChatGPT desktop app still needs to be open.

### For agents

Install the CLI as above, then run this. It clones the repo to `~/.local/share/chatgpt-dot-cli` and links the skill into each agent's skill directory. If the clone fails, no links are created.

```bash
src="$HOME/.local/share/chatgpt-dot-cli"
if [ -d "$src/.git" ]; then
  git -C "$src" pull --ff-only
else
  git clone https://gitlab.com/aa22396584/chatgpt-dot-cli.git "$src"
fi && [ -f "$src/skills/chatgpt-dot-cli/SKILL.md" ] &&
for d in "$HOME/.claude/skills" "$HOME/.codex/skills" "$HOME/.agents/skills" \
         "$HOME/.config/opencode/skills" "$HOME/.config/opencode/skill" \
         "$HOME/.cursor/skills" "$HOME/.grok/skills"; do
  mkdir -p "$d" && ln -sfn "$src/skills/chatgpt-dot-cli" "$d/chatgpt-dot-cli"
done
```

Rules for agents:

- Use the `chatgpt-dot-cli` command. Use MCP only if it is already connected in the session.
- Do not read `~/.codex/auth.json` or call `chatgpt.com` yourself.

MCP is optional. If you need it, install with `uv tool install "chatgpt-dot-cli[mcp] @ git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.1.3"` and set the stdio command to `chatgpt-dot-cli-mcp`.

### What it will not do

It will not pause or delete a dot, connect or disconnect a computer, or claim email.

### License and CI

MIT, see [LICENSE](LICENSE). This repo is public.

CI runs the tests when GitLab runner minutes are available, and a pushed tag is set up to create a release. To run the tests locally:

```bash
python3 -m unittest discover -s tests -q
```
