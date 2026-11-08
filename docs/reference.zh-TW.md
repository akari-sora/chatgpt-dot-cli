# chatgpt-dot-cli 參考

[English](reference.md) | 繁體中文

安裝、快速開始和指令清單在 [README](../README.zh-TW.md)。這頁是細節。

- [安裝細節](#安裝細節)
- [第一次設定](#第一次設定)
- [指令參考](#指令參考)
- [結束碼與錯誤訊息](#結束碼與錯誤訊息)
- [檔案與遮罩](#檔案與遮罩)
- [安全](#安全)
- [疑難排解](#疑難排解)
- [MCP 與 trinity-cli](#mcp-與-trinity-cli)
- [agent skill](#agent-skill)
- [測試與 CI](#測試與-ci)
- [平台](#平台)

## 安裝細節

版本釘在 tag `v0.2.6`。uv、pipx 與 PowerShell 的安裝指令在 [README](../README.zh-TW.md#安裝)。指令要在 PATH 裡。uv/pipx 放在 `$HOME/.local/bin`。

Windows 的執行檔在 `%USERPROFILE%\.local\bin\chatgpt-dot-cli.exe`。新開一個終端機後 PATH 才會更新。也可以用 pipx：

```powershell
py -3.12 -m pip install --user pipx
pipx install "git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.2.6"
chatgpt-dot-cli --version
```

`--version` 會印出 `chatgpt-dot-cli 0.2.6`。

GitLab Release 另附與平台無關的 wheel 與 sdist。用 pip 裝 wheel：

```bash
python3 -m pip install "https://gitlab.com/api/v4/projects/aa22396584%2Fchatgpt-dot-cli/packages/generic/chatgpt-dot-cli/v0.2.6/chatgpt_dot_cli-0.2.6-py3-none-any.whl"
```

升級要重新指定 tag。`uv tool upgrade` 不會把釘在 tag 的安裝移到下一個 tag。

```bash
uv tool install --force git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.2.6
```

```powershell
uv tool install --force "git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.2.6"
```

移除：

```bash
uv tool uninstall chatgpt-dot-cli
pipx uninstall chatgpt-dot-cli
```

```powershell
uv tool uninstall chatgpt-dot-cli
```

## 第一次設定

1. 安裝 [Codex CLI](https://github.com/openai/codex)，用 ChatGPT 帳號執行 `codex login`。
2. 登入檔的位置：
   - Linux：`$HOME/.codex/auth.json`
   - macOS：`$HOME/.codex/auth.json`
   - Windows：`%USERPROFILE%\.codex\auth.json`
   - 設了 `CODEX_HOME` 時，Codex 和這個 CLI 都改用 `$CODEX_HOME/auth.json`。
3. 檔案在別處時，CLI 用 `--auth 路徑`（可以用 `~`）。MCP 沒有 `--auth`，只讀上面那個預設路徑。
4. 確認可用（唯讀，約數秒）：

```bash
chatgpt-dot-cli list
```

成功時會印一行 dot，最後是 `N dot(s)`。不要把這個檔案貼到聊天裡。Token 不會被印出來。

## 指令參考

全域旗標：

| 旗標 | 預設 | 說明 |
| --- | --- | --- |
| `--version` |  | 印出版本後離開 |
| `--auth PATH` | `$CODEX_HOME/auth.json`，沒設 `CODEX_HOME` 時是家目錄裡的 `.codex/auth.json` | 登入檔路徑。有旗標就必須帶路徑 |
| `--json` | 關 | 印遮罩後的 JSON。可放在子指令前或後，不能放在單獨的 `--` 後面 |

沒有子指令時印出說明並以結束碼 2 離開，不呼叫 API。

文字模式的 `usage`、`show` 與各讀取指令印的是欄位型別，不是密文內容。`--json` 的值是假資料時才寫在下面的參考裡。

### `summary`

方案、dot 狀態、最近訊息。預設會讀 activity。

```bash
chatgpt-dot-cli summary --no-activity
```

| 旗標 | 預設 |
| --- | --- |
| `--no-activity` | 關（會讀 activity） |

`--json` 鍵：`plan_type`、`usage_http`、`primary_http`、`primary`、`dots`。每個 dot：`id`、`name`、`status`、`paused`、`kind`、`threads`、`threads_http`、`activity`、`activity_http`、`computers`、`computers_http`、`automations`、`automations_http`、`environment`、`environment_http`、`email`、`recent`。`--no-activity` 時 `activity` 與 `activity_http` 是 null，文字模式印 `activity=skipped`。

### `usage`

```bash
chatgpt-dot-cli usage
```

沒有自己的旗標。`--json` 鍵：`status`、`body`。`body` 裡常用 `plan_type`、`rate_limit`（含 `allowed`）、`limit_reached`、`primary_window`（含 `used_percent`）、`reset_after_seconds`。其他欄位可能存在，密文會被遮罩。

### `primary`

```bash
chatgpt-dot-cli primary
```

沒有自己的旗標。`--json` 鍵：`status`、`body`。

### `list`

```bash
chatgpt-dot-cli list
```

沒有自己的旗標。文字：`id=... name status= paused= kind=`，最後 `N dot(s)`。`--json` 是遮罩後的 dot 陣列，常用鍵：`id`、`display_name`、`status`、`is_paused`、`aeon_kind`。

### `probe`

每個讀取的 HTTP 狀態與欄位名稱。

```bash
chatgpt-dot-cli probe
```

沒有自己的旗標。`--json` 鍵：`usage_http`、`plan_type`、`primary_http`、`list_http`、`dots`。每個 dot：`name`、`status`、`paused`、`kind`、`reads`（`path`、`status`，訊息讀取另有 `items`）。

### `show`

```bash
chatgpt-dot-cli show
```

| 旗標 | 預設 |
| --- | --- |
| `--dot-id` | 帳號上唯一的 dot |
| 位置參數 `dot_id` | 同上。建議用 `--dot-id` |

`--json` 鍵：`status`、`body`。

### `threads`、`activity`、`root-thread`、`computers`、`env`、`automations`、`email-status`

都是唯讀。旗標與 `show` 相同：`--dot-id`（建議）或位置參數，預設是唯一的 dot。

```bash
chatgpt-dot-cli threads
chatgpt-dot-cli activity
chatgpt-dot-cli root-thread
chatgpt-dot-cli computers
chatgpt-dot-cli env
chatgpt-dot-cli automations
chatgpt-dot-cli email-status
```

`--json` 鍵：`status`、`body`、`info`。`info` 只有 email 回 403 且 `ineligible` 時是 true，此時結束碼為 0。文字模式會印 `email channel ineligible`。

`body` 裡常用的鍵：`threads` 的 `items`；`activity` 的 `data` 與 `next_cursor`；`computers` 的 `computers[]`（`display_name`、`is_attached`、`kind`、`local_computer_access_disabled_by_admin`；`signaling_url` 會被遮罩）；`env` 的 `status` 與 `capabilities[].type` / `status`；`automations` 的 `items`。

### `by-thread`

```bash
chatgpt-dot-cli by-thread
```

| 旗標 | 預設 |
| --- | --- |
| 位置參數 `thread_id` | 該 dot 目前的 root thread |
| `--dot-id` | 唯一的 dot。只有省略 thread id 時才用到 |

`--json` 鍵：`status`、`body`。沒有 root thread 且沒給 id 時，結束碼 3，stderr 是 `dot has no active root thread`。

### `messages`

不建立房間。只有 `--dot-id`，沒有位置參數。

```bash
chatgpt-dot-cli messages --limit 2
```

| 旗標 | 預設 | 限制 |
| --- | --- | --- |
| `--dot-id` | 唯一的 dot | 多個 dot 時必填 |
| `--limit` | 20 | 整數 1..32。超出範圍結束碼 2，不送請求 |
| `--before` | 無 | 一個訊息 id，只取更舊的一頁 |
| `--after` | 無 | 一個訊息 id，只取更新的一頁 |

不送 `cursor`，也不會自動翻頁。`--json` 鍵永遠是 `name`、`lines`、`messages`。沒有房間時兩個清單都是空的，並加上 `note`：`no messages yet (send creates the room)`，結束碼 0。`messages` 由舊到新，`lines` 由新到舊。`role` 永遠是 `user`，不能用來判斷是誰說的。說話者是 `dot:`、`you:` 或 `unknown:`。

### `send`

唯一會寫入的指令。把文字（和 `--attach` 的檔案）傳進 dot 的訊息收件匣。建議用 `--stdin` 讀取 UTF-8 文字，避免訊息出現在 argv 或 shell 歷史。stdin 內容會原樣送出，包含檔案或 `echo` 結尾的換行。位置參數仍可用，但會在 stderr 印出棄用警告。`--stdin` 與位置參數不能同時使用。

```bash
chatgpt-dot-cli send --help
printf 'hello' | chatgpt-dot-cli send --stdin
```

| 旗標 | 預設 |
| --- | --- |
| `--stdin` | 從 stdin 讀取 UTF-8 文字 |
| `--attach FILE` | 附加檔案（可重複，每個最多 20 MB）。檔案先上傳到 dot 的訊息房間（`POST /messaging/rooms/{id}/files`，和 dot app 相同），全部上傳成功才送出那一則訊息；任何一個上傳失敗就不送訊息，失敗前已上傳的檔案會留在房間裡（錯誤訊息會說有幾個）。輸出裡的檔案下載連結以 `***` 顯示 |
| `--attach-sha256 HEX` | 每個 `--attach` 檔案預期的 sha256，依同樣順序（可重複）。檔案只讀一次，算出的雜湊和上傳的是同一份位元組；不符就結束碼 2，什麼都不上傳、不送 |
| 位置參數 `text` | 已棄用，仍可用。以 `-` 開頭時前面加 `--` |
| `--dot-id` | 唯一的 dot |

文字模式印 `sent to NAME`。`--json` 是遮罩後的新訊息物件，含 `id`。桌面版主畫面可能晚一點才顯示。

## 結束碼與錯誤訊息

| 結束碼 | 訊息 | 你該做的事 |
| --- | --- | --- |
| 0 | 成功。email 403 且 `ineligible` 也算成功，文字會有 `email channel ineligible` | 不用處理。這表示帳號不能用 email |
| 2 | 沒有子指令。印出說明 | 加上 `list` 或其他子指令 |
| 2 | `chatgpt-dot-cli: error: --auth requires a path` | `--auth` 後面加上檔案路徑 |
| 2 | `chatgpt-dot-cli: error: send requires message text or --stdin` | 提供位置文字或 `--stdin` |
| 2 | `chatgpt-dot-cli: error: send cannot use --stdin with positional text` | 只選一種 |
| 2 | `chatgpt-dot-cli: error: cannot read send input; provide UTF-8 text on stdin` | 在 stdin 提供 UTF-8 文字 |
| 2 | `limit must be an integer from 1 to 32` | 把 `--limit` 改到 1..32 |
| 2 | `cannot read auth file: ... Run codex login with a ChatGPT account, or pass --auth PATH.` | 執行 `codex login`，或用 `--auth` 指到登入檔 |
| 2 | `auth file is not valid json` | 重新 `codex login` |
| 2 | `auth file is not a chatgpt login` | 用 ChatGPT 帳號登入，不要用 API key 登入檔 |
| 2 | `auth file has no access token` 或 `auth file has no account id` | 重新 `codex login` |
| 2 | `auth file has no valid tokens object` | 重新 `codex login` |
| 2 | `auth file must be a regular file`、`must not be a symbolic link`、`must be owned by the current user`、或 `permits group or other access; set its mode to 600` | 用自己擁有的一般登入檔，權限 600，不要用符號連結或管線 |
| 3 | `ChatGPT login expired (401). Open Codex or run codex login, then retry.` | 執行 `codex login` 再試 |
| 3 | `network error: ...` | 檢查網路後重試 |
| 3 | `response body was not JSON (likely Cloudflare)` | 等一下再試。`summary` 可改 `--no-activity` |
| 3 | `GET ... STATUS`，有時後面帶 API `code` | 看狀態碼。401 重新登入；403/429/503 稍後再試 |
| 3 | `dot id was not found; run chatgpt-dot-cli list and pass --dot-id` | 用 `list` 的 id |
| 3 | `more than one dot; run chatgpt-dot-cli list and pass --dot-id <id>` | 加上 `--dot-id` |
| 3 | `no dot on this account` | 先在 ChatGPT 建立 dot |
| 3 | `dot has no active root thread` | `by-thread` 改傳 thread id，或先開一個對話 |
| 3 | `message text is empty` | `send` 要有文字 |
| 0 | stderr：`chatgpt-dot-cli: warning: positional send text is deprecated; use --stdin` | 改用 `--stdin`。訊息仍已送出 |
| 0 | stderr：`messaging_room_preview has no aeon member` | 說話者標成 `unknown:`。不是失敗 |

## 檔案與遮罩

CLI 沒有設定檔，只讀一個環境變數：`CODEX_HOME`，用法跟 Codex 一樣。唯一讀取的檔案是登入檔：

| 系統 | 路徑 |
| --- | --- |
| Linux | `$HOME/.codex/auth.json` |
| macOS | `$HOME/.codex/auth.json` |
| Windows | `%USERPROFILE%\.codex\auth.json` |
| 設了 `CODEX_HOME` | `$CODEX_HOME/auth.json` |

CLI 不寫入這個檔、不改權限、不在磁碟上做快取，所以沒有檔案鎖。Linux 與 macOS 讀取前會檢查已開啟的登入檔：必須是一般檔案、由目前使用者擁有，且群組與其他人不可存取（通常是 600）。最後一層若是符號連結或 FIFO 會被拒絕，而且不會卡住；不檢查 POSIX ACL 或上層目錄。Windows 拒絕一般符號連結與非一般檔案，但不檢查 ACL。Windows 主控台會把 stdout/stderr 設成 UTF-8（`errors=replace`），換行是 LF。

MCP 的 `list` 快取只活在該程序裡，15 秒，`dot_send` 之後清掉。

`--json` 會遮罩鍵名符合 `token`、`secret`、`key`、`cookie`、`authorization`、`password`、`session` 的欄位，以及精確鍵名 `email`、`account_id`、`user_id`、`signaling_url`、`magic_link_url`、`magic_link_share_text`、`inspector_url`。`account_user_id`、`id`、`aeon_id`、`created_at`、`content`、`preview`、`display_name`、`kind`、`is_attached` 不會因為這個清單被遮罩。

## 安全

HTTP 重新導向不會被跟隨。列印到終端機的文字會把控制字元跳脫成可見形式；`--json` 仍是合法 JSON，解碼後是原始值。

除了 `send` 以外都是唯讀。`send` 只會 POST 文字訊息；若還沒有房間，會一併打開訊息房間。

這個工具不會：暫停、恢復、刪除 dot，連接或中斷電腦，申請 email，使用語音，或呼叫 `/ps/orbit`。

## 疑難排解

- 找不到指令：Linux/macOS 把 `$HOME/.local/bin` 加入 PATH；Windows 新開終端機，或用 `%USERPROFILE%\.local\bin`。
- 登入檔不在：執行 `codex login`。結束碼 2。
- `--limit 33` 或 `0`：結束碼 2，沒有發出請求。
- `summary` 很慢，或 activity 是空的：改跑 `chatgpt-dot-cli summary --no-activity`。
- 非 JSON 的 403/429/503：多半是 Cloudflare。CLI 會重試一次，然後結束碼 3。
- email 403 `ineligible`：正常，結束碼 0。
- 多個 dot：每個讀取都加 `--dot-id`。`messages` 與 `send` 只有 `--dot-id`。
- 要 dot 操作你的電腦：ChatGPT 桌面版仍要開著。

## MCP 與 trinity-cli

MCP 是可選的。stdio 指令是 `chatgpt-dot-cli-mcp`。它只讀預設登入檔。

```bash
uv tool install --force "chatgpt-dot-cli[mcp] @ git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.2.6"
```

從這個 repo 的工作目錄：

```bash
uv pip install -e ".[mcp]"
```

沒裝 MCP 套件時，`chatgpt-dot-cli-mcp` 以結束碼 1 離開，並印出上面兩行。

跨 agent（同時問三個、交接、摘要）用 [trinity-cli](https://gitlab.com/aa22396584/trinity-cli)。

## agent skill

給 agent 的 skill：Linux 與 macOS 可以把 tag `v0.2.6` clone 到 `$HOME/.local/share/chatgpt-dot-cli`。目錄已存在時改為 `fetch --tags` 再 `checkout --detach`。目標已存在而且不是 symlink 時，stderr 印跳過，不覆蓋。clone 失敗不會建立連結。

```bash
src="$HOME/.local/share/chatgpt-dot-cli"
if [ -d "$src/.git" ]; then
  git -C "$src" fetch --tags origin &&
  git -C "$src" checkout --detach v0.2.6
else
  git clone --branch v0.2.6 https://gitlab.com/aa22396584/chatgpt-dot-cli.git "$src"
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

Windows 沒有這組 symlink。把 `skills\chatgpt-dot-cli` 複製到該 agent 的 skill 目錄即可。

## 測試與 CI

本機測試：

```bash
python3 -m unittest discover -s tests -q
```

CI：預設使用 GitLab.com 的 runner。Linux 跑 Python 3.11、3.12、3.13。Windows 在 tag、手動執行，以及 main 上改到程式、測試或打包檔時跑 Python 3.12。維護者可設定 CI/CD 變數 `LINUX_RUNNER_TAG` 與 `WINDOWS_RUNNER_TAG`，把 job 指到自己的 runner。macOS 沒有 CI。推上 tag 會建立 GitLab Release，並附上 wheel 與 sdist。MIT 授權，見 [LICENSE](../LICENSE)。

## 平台

| 系統 | Python | 驗證方式 |
| --- | --- | --- |
| Linux | 3.11、3.12、3.13 | GitLab CI：離線單元測試 |
| Windows | 3.12 | GitLab CI：同一套測試，改到程式、測試或打包設定時自動跑 |
| macOS | 3.11、3.12、3.13 | 維護者本機：同一套測試，加上照 README 從 tag 安裝的首次使用檢查 |

測試不連 ChatGPT。macOS 沒有 CI。
