# chatgpt-dot

唯讀客戶端，用本機 ChatGPT OAuth 讀 Your dot。Your dot 在 ChatGPT App 裡的內部名稱是 orbit，HTTP 資源叫 tbo。

登入和額度查詢同一套：`Authorization: Bearer` 加上 `ChatGPT-Account-Id`，打 `https://chatgpt.com/backend-api`。Token 讀 `~/.codex/auth.json`（`auth_mode` 必須是 `chatgpt`），不會寫進這個 repo。

```bash
python3 client.py
```

輸出是狀態碼和欄位名稱。`display_name` 是空字串時，App 側邊欄顯示 Your dot。連續讀取有時會先拿到 HTML 403，客戶端會等一秒再試一次；JSON 403（例如 email 的 `ineligible`）會直接印出來。

## 2026-10-01 實測

ChatGPT App 26.715，本機 `~/.codex/auth.json`。下面都是 GET。

| 路徑 | 結果 |
| --- | --- |
| `/wham/usage` | 200，`plan_type` 等額度欄位 |
| `/tbo/primary` | 200，`selection`（`thread_id`、`aeon_id`、`generation`、`available`、`messaging_room_id`、`selected_at`） |
| `/tbo` | 200，`items[]`。dot 的 id 在 `items[].id`，`aeon_kind` 為 `orbit` |
| `/tbo/{id}` | 200，與 list item 同一組欄位 |
| `/tbo/{id}/threads` | 200，`items[].thread_id` |
| `/tbo/{id}/activity` | 200，`data`、`next_cursor` |
| `/tbo/{id}/root-thread` | 200，`root_thread_id` |
| `/tbo/{id}/computers` | 200，`computers[]` |
| `/tbo/{id}/environment/status` | 200，`status`、`capabilities` |
| `/tbo/{id}/automations` | 200，`items` |
| `/tbo/by-thread/{thread_id}` | 200，回到同一筆 dot。`thread_id` 用 `active_root_thread_id` |
| `/tbo/{id}/channels/email` | 403，`detail.code` = `ineligible`。路徑存在，這個帳號不能用 email 頻道 |

`/tbo/primary` 回的是目前選取，不是 dot 物件。列出 dot 用 `GET /tbo`。把 `aeon_id` 當成 `/tbo/{id}` 會 404。

## 只從 App 抽出、沒有呼叫

寫入動作沒有打過：`POST /tbo`、`PATCH /tbo/{id}`、`PUT /tbo/primary`、`DELETE /tbo/primary`、`DELETE /tbo/{id}`、`POST /tbo/{id}/runtime/pause`、`POST /tbo/{id}/runtime/resume`、電腦 connect / disconnect、`POST /tbo/{id}/environment/recreate`、email claim、語音 attach / stop、onboarding、`POST /tbo/{id}/messaging-room`。

也沒有打：`GET /tbo/{id}/misalignment-review`、`GET /tbo/{id}/channels/email/options`、`/ps/orbit/{thread_id}/teams`、`/ps/orbit/{id}/slack`。

App 內路由是 `/dots`、`/dots/home`、`/dots/new`、`/dots/:conversationId`，另外有 `/o/:conversationId`。對外網址是 `https://chatgpt.com/agents/a/{id}`。
