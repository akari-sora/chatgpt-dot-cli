# chatgpt-dot-cli

[English](README.md) | 繁體中文

在終端機查看你的 ChatGPT Your dot、讀訊息、傳文字。

> 正本和 issue 在 <https://gitlab.com/aa22396584/chatgpt-dot-cli>。trinity-cli 系列的一部分：<https://gitlab.com/aa22396584/trinity-cli>

[![pipeline status](https://gitlab.com/aa22396584/chatgpt-dot-cli/badges/main/pipeline.svg)](https://gitlab.com/aa22396584/chatgpt-dot-cli/-/commits/main)
[![release](https://gitlab.com/aa22396584/chatgpt-dot-cli/-/badges/release.svg)](https://gitlab.com/aa22396584/chatgpt-dot-cli/-/releases)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 功能

- ChatGPT 官方 Your dot 的本機 client，不是第二個 dot。桌面版把這個 dot 叫做 orbit，HTTP 資源是 tbo。
- 讀方案用量、dot 狀態、threads、activity、電腦、automations 與訊息。只有 `send` 會寫入。
- 登入來自 Codex 的 ChatGPT 登入檔，CLI 不另外做帳號。
- 「Your dot」是預設名稱：`display_name` 是空的時候就顯示 Your dot。你在 ChatGPT app 裡改名後，CLI 會印出新名字。
- 可選的 MCP 伺服器：`chatgpt-dot-cli-mcp`。

這個 repo 是公開的。需要 Python 3.11、3.12 或 3.13。支援的系統見[平台](docs/reference.zh-TW.md#平台)。

## 安裝

版本釘在 tag `v0.2.6`。

Linux 或 macOS：

```bash
uv tool install git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.2.6
chatgpt-dot-cli --version
```

或：

```bash
pipx install git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.2.6
chatgpt-dot-cli --version
```

Windows（PowerShell）：

```powershell
irm https://astral.sh/uv/install.ps1 | iex
uv tool install "git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.2.6"
chatgpt-dot-cli --version
```

`--version` 會印出 `chatgpt-dot-cli 0.2.6`。指令要在 PATH 裡，uv/pipx 放在 `$HOME/.local/bin`。Windows 的 pipx、Release 附的 wheel、升級與移除見[安裝細節](docs/reference.zh-TW.md#安裝細節)。

## 設定

1. 安裝 [Codex CLI](https://github.com/openai/codex)，用 ChatGPT 帳號執行 `codex login`。
2. 用唯讀指令確認（約數秒）：`chatgpt-dot-cli list`。成功時會印一行 dot，最後是 `N dot(s)`。

登入檔是 `$HOME/.codex/auth.json`（Windows 是 `%USERPROFILE%\.codex\auth.json`；設了 `CODEX_HOME` 時是 `$CODEX_HOME/auth.json`）。檔案在別處時用 `--auth 路徑`。見[第一次設定](docs/reference.zh-TW.md#第一次設定)。

## 快速開始

`send` 會真的傳訊息，下面只示範輸出形狀。

```text
$ chatgpt-dot-cli list
id=dot_example Example status=active paused=False kind=orbit
1 dot(s)

$ chatgpt-dot-cli messages --limit 2
Example messages=2
dot: example reply
you: example question

$ chatgpt-dot-cli usage
200 GET /wham/usage plan_type=example

$ chatgpt-dot-cli summary --no-activity
plan_type=example
primary available=true
Example status=active paused=False kind=orbit threads=1 activity=skipped computers=1 automations=0 environment=connected email=ineligible
  dot: example reply

$ printf 'hello' | chatgpt-dot-cli send --stdin
sent to Example
```

## 指令

| 指令 | 用途 |
| --- | --- |
| `summary` | 方案、dot 狀態、最近訊息；`--no-activity` 跳過 activity |
| `usage` | ChatGPT 方案用量 |
| `primary` | 目前選的是哪個 dot |
| `list` | 列出 dot 與 id |
| `probe` | 每個讀取的 HTTP 狀態與欄位名稱 |
| `show` | 一個 dot 的資料 |
| `threads`、`activity`、`root-thread`、`computers`、`env`、`automations`、`email-status` | 一個 dot 的唯讀資訊 |
| `by-thread` | 用 thread id 找 dot |
| `messages` | 最近訊息（`--limit` 1..32，預設 20；`--before`／`--after` 取一頁）；不建立房間 |
| `send` | 唯一會寫入的指令：`--stdin` 讀文字，`--attach FILE` 與 `--attach-sha256 HEX` 附檔 |

全域旗標：`--json`（遮罩後的 JSON，可放在子指令前或後）、`--auth PATH`、`--version`。有多個 dot 時加 `--dot-id`。每個旗標、JSON 鍵與錯誤訊息見 [docs/reference.zh-TW.md](docs/reference.zh-TW.md#指令參考)。

## 安全與隱私

- 除了 `send` 以外都是唯讀。`send` 只會 POST 訊息；若還沒有房間，會一併打開訊息房間。這個工具不會暫停、恢復、刪除 dot，不連接或中斷電腦，不申請 email，不使用語音，也不呼叫 `/ps/orbit`。
- 這個 CLI 只連 `chatgpt.com`，用你自己的 ChatGPT 登入。沒有遙測，也不在磁碟上存任何東西。HTTP 重新導向不會被跟隨。
- 登入檔只讀不寫，token 不會印出來。`--json` 會遮罩 token、cookie、email、帳號 id 這類欄位（[完整清單](docs/reference.zh-TW.md#檔案與遮罩)）。
- 文字輸出和 `--json` 仍然有訊息內容、dot 名稱和 id。貼到 issue 前先刪掉。

## 給 agent 用

- 每個指令都可加 `--json`。結束碼 0 是成功（email 403 `ineligible` 也算），2 是參數或登入檔有問題、沒有發出請求，3 是 API、網路或查找錯誤。見[結束碼與錯誤訊息](docs/reference.zh-TW.md#結束碼與錯誤訊息)。
- `send --stdin` 讓訊息不出現在 argv 或 shell 歷史。
- 附帶的 skill 是 `skills/chatgpt-dot-cli/SKILL.md`。把它連到 `~/.claude/skills`、`~/.codex/skills` 等 agent skill 目錄的腳本見 [agent skill](docs/reference.zh-TW.md#agent-skill)。
- MCP（`chatgpt-dot-cli-mcp`，stdio，可選的 `[mcp]`）見 [MCP 與 trinity-cli](docs/reference.zh-TW.md#mcp-與-trinity-cli)。
- 跨 agent（同時問三個、交接、摘要）用 [trinity-cli](https://gitlab.com/aa22396584/trinity-cli)。

## 文件

- [docs/reference.zh-TW.md](docs/reference.zh-TW.md)：安裝細節、每個指令、結束碼與錯誤訊息、檔案與遮罩、疑難排解、MCP、agent skill、測試與 CI、平台。
- [CONTRIBUTING.md](CONTRIBUTING.md)、[SECURITY.zh-TW.md](SECURITY.zh-TW.md)（安全問題照這份回報，不要開公開 issue）、[CHANGELOG.md](CHANGELOG.md)。

## 相關專案

- trinity-cli — 一個 CLI 管三個常駐 agent（Your dot、Grok Bot、Muse）：<https://gitlab.com/aa22396584/trinity-cli>
- chatgpt-dot-cli — ChatGPT Your dot（這個 repo）：<https://gitlab.com/aa22396584/chatgpt-dot-cli>
- grok-bot-cli（fork，`gbot`）— Grok Bot：<https://gitlab.com/aa22396584/grok-bot-cli>
- muse-web-cli — 透過網頁使用 Meta Muse：<https://gitlab.com/aa22396584/muse-web-cli>

## 授權與聲明

MIT 授權，見 [LICENSE](LICENSE)。

非官方：這是個人專案，跟 OpenAI 沒有關係，也沒有得到 OpenAI 的背書或支援。它呼叫 ChatGPT app 用的、沒有公開文件的介面，OpenAI 隨時可能改掉。自動化使用可能違反 OpenAI 的使用條款，帳號風險自負。
