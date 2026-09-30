# chatgpt-dot-cli

[中文](#中文) · [English](#english)

---

## 中文

在自己電腦上讀取和傳訊息給 ChatGPT 官方的 Your dot。

這不是另一個 dot，也不是 dot 的替代品。它只是一個本機 client，用你已經登入的 ChatGPT 帳號，去看同一個 dot 的狀態、讀訊息、送文字。

需要 Python 3.11 以上，以及 [uv](https://docs.astral.sh/uv/) 或 [pipx](https://pipx.pypa.io/)。這個 repo 是公開的，任何人都可以直接安裝。

### 安裝

用 uv（建議）：

```bash
uv tool install git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.1.2
```

或用 pipx：

```bash
pipx install git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.1.2
```

兩種都會把 `chatgpt-dot-cli` 放到 `~/.local/bin`。確認一下：

```bash
chatgpt-dot-cli --help
```

找不到指令的話，把 `~/.local/bin` 加進 PATH（`uv tool update-shell` 或 `pipx ensurepath`），再開一個新的終端機。

更新到最新版：

```bash
uv tool install --force git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git
```

有用 MCP 的話，更新時要保留 `[mcp]`：

```bash
uv tool install --force 'chatgpt-dot-cli[mcp] @ git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git'
```

### 使用

```bash
chatgpt-dot-cli summary          # 方案、dot 狀態、最近訊息
chatgpt-dot-cli messages         # 最近訊息，只讀
chatgpt-dot-cli send "你好"      # 傳一則文字給 dot
chatgpt-dot-cli list             # 列出你的 dot 和 id
```

有多個 dot 時，加 `--dot-id ID`，id 從 `chatgpt-dot-cli list` 拿。想要 JSON 輸出就加 `--json`。其他指令看 `chatgpt-dot-cli --help`。

- `send` 的訊息會進 dot 的訊息收件匣；桌面版主畫面可能晚一點才顯示。
- 要 dot 在你電腦上做事，ChatGPT 桌面版仍然要開著。

### 登入

這個工具不自己登入，它讀 `~/.codex/auth.json`，也就是 Codex CLI 用 ChatGPT 帳號登入後產生的檔案。

- 還沒有這個檔案：先安裝 Codex CLI，執行 `codex login`，選 ChatGPT 帳號登入。
- 出現 401：登入過期了，再跑一次 `codex login`。
- 檔案放在別的地方：用 `--auth 路徑` 指定。

Token 不會被印出來，也不會寫進這個 repo 或任何設定檔。

### 給 agent 裝

agent 要裝的是 skill，不是 MCP。skill 在 repo 裡的 `skills/chatgpt-dot-cli/SKILL.md`，它會教 agent 去呼叫 `chatgpt-dot-cli` 指令。

先照上面「安裝」裝好 CLI，再貼這段。它會把 repo 抓到 `~/.local/share/chatgpt-dot-cli`，然後把 skill 連到各個 coding agent 會讀的目錄：

```bash
src="$HOME/.local/share/chatgpt-dot-cli"
if [ -d "$src/.git" ]; then git -C "$src" pull --ff-only; else git clone https://gitlab.com/aa22396584/chatgpt-dot-cli.git "$src"; fi &&
for d in \
  "$HOME/.claude/skills" \
  "$HOME/.codex/skills" \
  "$HOME/.agents/skills" \
  "$HOME/.config/opencode/skills" \
  "$HOME/.config/opencode/skill" \
  "$HOME/.cursor/skills" \
  "$HOME/.grok/skills"
do
  mkdir -p "$d" && ln -sfn "$src/skills/chatgpt-dot-cli" "$d/chatgpt-dot-cli"
done
```

- `~/.claude/skills`：Claude Code。如果 Gemini、Antigravity、Copilot、Kiro 的 skill 目錄是連到這裡的 symlink，它們也會讀到。
- `~/.agents/skills`：Codex 和 OpenCode 也會讀這裡。
- 已經 clone 過這個 repo 的話，把 `src` 改成你自己的 clone 路徑就好。
- clone 或 pull 失敗時，`fi &&` 會讓後面的迴圈不執行，不會留下壞掉的 symlink。

給 agent 的規則（skill 裡也有寫）：

- skill 連好之後，一律用 `chatgpt-dot-cli` 指令。
- 如果 PATH 上找不到 `chatgpt-dot-cli`，先用上面的 `uv tool install` 指令安裝。
- 不要自己讀 `~/.codex/auth.json`，也不要自己對 `chatgpt.com` 發 HTTP 請求。

### MCP（可選）

不用 MCP 也能完整使用。只有你的工具只吃 MCP 時才需要：用 `uv tool install --force "chatgpt-dot-cli[mcp] @ git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.1.2"` 安裝，然後在 MCP 設定裡把 stdio 指令設成 `chatgpt-dot-cli-mcp`。

### 不會做的事

不暫停、不恢復、不刪除 dot，不連接或中斷電腦，不申請 email 頻道。只做讀取和傳文字訊息。

### 開發

```bash
git clone https://gitlab.com/aa22396584/chatgpt-dot-cli.git
cd chatgpt-dot-cli
python3 -m unittest discover -s tests -q
```

---

## English

Read and message the official ChatGPT Your dot from your own computer.

This is not a second dot and not a replacement for it. It is a local client that uses the ChatGPT account you are already logged in with to check the same dot's status, read its messages, and send it text.

Requires Python 3.11 or newer, plus [uv](https://docs.astral.sh/uv/) or [pipx](https://pipx.pypa.io/). The repo is public, so anyone can install it.

### Install

With uv (recommended):

```bash
uv tool install git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.1.2
```

Or with pipx:

```bash
pipx install git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.1.2
```

Both put `chatgpt-dot-cli` in `~/.local/bin`. Check it:

```bash
chatgpt-dot-cli --help
```

If the command is not found, add `~/.local/bin` to your PATH (`uv tool update-shell` or `pipx ensurepath`) and open a new terminal.

Upgrade to the latest version:

```bash
uv tool install --force git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git
```

If you use MCP, keep the `[mcp]` extra when upgrading:

```bash
uv tool install --force 'chatgpt-dot-cli[mcp] @ git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git'
```

### Usage

```bash
chatgpt-dot-cli summary          # plan, dot status, recent messages
chatgpt-dot-cli messages         # recent messages, read-only
chatgpt-dot-cli send "hello"     # send a text message to the dot
chatgpt-dot-cli list             # list your dots and their ids
```

If you have more than one dot, add `--dot-id ID` with an id from `chatgpt-dot-cli list`. Add `--json` for JSON output. See `chatgpt-dot-cli --help` for the other commands.

- Messages from `send` go to the dot's messaging inbox. The desktop app's main view may show them a bit later.
- For local computer work, the ChatGPT desktop app still needs to be open.

### Auth

The tool does not log in by itself. It reads `~/.codex/auth.json`, the file the Codex CLI writes after you log in with a ChatGPT account.

- No such file yet: install the Codex CLI, run `codex login`, and choose your ChatGPT account.
- Getting 401: the login expired. Run `codex login` again.
- The file lives somewhere else: pass `--auth PATH`.

Tokens are never printed and never written to this repo or any config file.

### Install for agents

Agents install the skill, not MCP. The skill is `skills/chatgpt-dot-cli/SKILL.md` in this repo, and it teaches the agent to call the `chatgpt-dot-cli` command.

Install the CLI first (see Install above), then paste this. It fetches the repo to `~/.local/share/chatgpt-dot-cli` and links the skill into the directories each coding agent reads:

```bash
src="$HOME/.local/share/chatgpt-dot-cli"
if [ -d "$src/.git" ]; then git -C "$src" pull --ff-only; else git clone https://gitlab.com/aa22396584/chatgpt-dot-cli.git "$src"; fi &&
for d in \
  "$HOME/.claude/skills" \
  "$HOME/.codex/skills" \
  "$HOME/.agents/skills" \
  "$HOME/.config/opencode/skills" \
  "$HOME/.config/opencode/skill" \
  "$HOME/.cursor/skills" \
  "$HOME/.grok/skills"
do
  mkdir -p "$d" && ln -sfn "$src/skills/chatgpt-dot-cli" "$d/chatgpt-dot-cli"
done
```

- `~/.claude/skills`: Claude Code. Gemini, Antigravity, Copilot, and Kiro also see it if their skill directories are symlinks to this one.
- `~/.agents/skills`: Codex and OpenCode read this too.
- If you already have a clone of this repo, set `src` to your clone's path instead.
- If the clone or pull fails, `fi &&` stops the loop, so no broken symlinks are created.

Rules for agents (also in the skill):

- Once the skill is linked, always use the `chatgpt-dot-cli` command.
- If `chatgpt-dot-cli` is not on PATH, install it with the `uv tool install` command above first.
- Do not read `~/.codex/auth.json` yourself, and do not send your own HTTP requests to `chatgpt.com`.

### MCP (optional)

Everything works without MCP. You only need it if your tool accepts nothing but MCP: install with `uv tool install --force "chatgpt-dot-cli[mcp] @ git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.1.2"`, then set the stdio command in your MCP config to `chatgpt-dot-cli-mcp`.

### What it will not do

It does not pause, resume, or delete a dot, does not connect or disconnect computers, and does not claim an email channel. It only reads and sends text messages.

### Development

```bash
git clone https://gitlab.com/aa22396584/chatgpt-dot-cli.git
cd chatgpt-dot-cli
python3 -m unittest discover -s tests -q
```
