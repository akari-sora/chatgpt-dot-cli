# chatgpt-dot-cli reference

English | [繁體中文](reference.zh-TW.md)

The [README](../README.md) covers install, quick start, and the command list. This page has the details.

- [Install details](#install-details)
- [First-time setup](#first-time-setup)
- [Command reference](#command-reference)
- [Exit codes and error messages](#exit-codes-and-error-messages)
- [Files, environment, cache, redaction](#files-environment-cache-redaction)
- [Safety](#safety)
- [Troubleshooting](#troubleshooting)
- [MCP and trinity-cli](#mcp-and-trinity-cli)
- [Agent skill](#agent-skill)
- [Tests and CI](#tests-and-ci)
- [Platforms](#platforms)

## Install details

Pinned to tag `v0.2.6`. The uv, pipx, and PowerShell commands are in the [README](../README.md#install). The command must be on PATH. uv and pipx put it in `$HOME/.local/bin`.

On Windows the executable is `%USERPROFILE%\.local\bin\chatgpt-dot-cli.exe`. Open a new terminal so PATH updates. pipx works too:

```powershell
py -3.12 -m pip install --user pipx
pipx install "git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.2.6"
chatgpt-dot-cli --version
```

`--version` prints `chatgpt-dot-cli 0.2.6`.

The GitLab Release also attaches a platform-independent wheel and sdist. Install the wheel with pip:

```bash
python3 -m pip install "https://gitlab.com/api/v4/projects/aa22396584%2Fchatgpt-dot-cli/packages/generic/chatgpt-dot-cli/v0.2.6/chatgpt_dot_cli-0.2.6-py3-none-any.whl"
```

To upgrade, install that tag again. `uv tool upgrade` will not move an install that is pinned to a tag.

```bash
uv tool install --force git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.2.6
```

```powershell
uv tool install --force "git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.2.6"
```

Uninstall:

```bash
uv tool uninstall chatgpt-dot-cli
pipx uninstall chatgpt-dot-cli
```

```powershell
uv tool uninstall chatgpt-dot-cli
```

## First-time setup

1. Install the [Codex CLI](https://github.com/openai/codex) and run `codex login` with a ChatGPT account.
2. The login file lives at:
   - Linux: `$HOME/.codex/auth.json`
   - macOS: `$HOME/.codex/auth.json`
   - Windows: `%USERPROFILE%\.codex\auth.json`
   - When `CODEX_HOME` is set, Codex and this CLI both use `$CODEX_HOME/auth.json` instead.
3. If the file is somewhere else, pass `--auth PATH` to the CLI (`~` works). MCP has no `--auth` flag and reads only the default path above.
4. Confirm it works with a read-only command (a few seconds):

```bash
chatgpt-dot-cli list
```

Success prints one line per dot and ends with `N dot(s)`. Do not paste that file into chat. Tokens are never printed.

## Command reference

Global flags:

| Flag | Default | Notes |
| --- | --- | --- |
| `--version` |  | print the version and exit |
| `--auth PATH` | `$CODEX_HOME/auth.json`, or `.codex/auth.json` in the home directory when `CODEX_HOME` is unset | required when the flag is present |
| `--json` | off | redacted JSON. Before or after the subcommand, not after a standalone `--` |

With no subcommand the CLI prints help and exits 2. It does not call the API.

In text mode, `usage`, `show`, and the other read commands print field types, not secret values. The `--json` samples in the reference use fake values.

### `summary`

Plan, dot status, and recent messages. Activity is fetched unless you skip it.

```bash
chatgpt-dot-cli summary --no-activity
```

| Flag | Default |
| --- | --- |
| `--no-activity` | off (activity is fetched) |

`--json` keys: `plan_type`, `usage_http`, `primary_http`, `primary`, `dots`. Each dot has `id`, `name`, `status`, `paused`, `kind`, `threads`, `threads_http`, `activity`, `activity_http`, `computers`, `computers_http`, `automations`, `automations_http`, `environment`, `environment_http`, `email`, `recent`. With `--no-activity`, `activity` and `activity_http` are null and the text line says `activity=skipped`.

### `usage`

```bash
chatgpt-dot-cli usage
```

No flags of its own. `--json` keys: `status`, `body`. Useful keys inside `body`: `plan_type`, `rate_limit` (including `allowed`), `limit_reached`, `primary_window` (including `used_percent`), `reset_after_seconds`. Other fields may be present. Secrets are redacted.

### `primary`

```bash
chatgpt-dot-cli primary
```

No flags of its own. `--json` keys: `status`, `body`.

### `list`

```bash
chatgpt-dot-cli list
```

No flags of its own. Text is `id=... name status= paused= kind=` and then `N dot(s)`. `--json` is an array of redacted dot objects. Useful keys: `id`, `display_name`, `status`, `is_paused`, `aeon_kind`.

### `probe`

HTTP status and field names for every read.

```bash
chatgpt-dot-cli probe
```

No flags of its own. `--json` keys: `usage_http`, `plan_type`, `primary_http`, `list_http`, `dots`. Each dot has `name`, `status`, `paused`, `kind`, `reads` (`path`, `status`, and `items` on the message read).

### `show`

```bash
chatgpt-dot-cli show
```

| Flag | Default |
| --- | --- |
| `--dot-id` | the only dot on the account |
| positional `dot_id` | same. Prefer `--dot-id` |

`--json` keys: `status`, `body`.

### `threads`, `activity`, `root-thread`, `computers`, `env`, `automations`, `email-status`

All read-only. Same flags as `show`: `--dot-id` (preferred) or a positional id. Default: the only dot.

```bash
chatgpt-dot-cli threads
chatgpt-dot-cli activity
chatgpt-dot-cli root-thread
chatgpt-dot-cli computers
chatgpt-dot-cli env
chatgpt-dot-cli automations
chatgpt-dot-cli email-status
```

`--json` keys: `status`, `body`, `info`. `info` is true only when email returns 403 `ineligible`, and that case exits 0. Text mode prints `email channel ineligible`.

Useful keys inside `body`: `items` for `threads`; `data` and `next_cursor` for `activity`; `computers[]` (`display_name`, `is_attached`, `kind`, `local_computer_access_disabled_by_admin`; `signaling_url` is redacted) for `computers`; `status` and `capabilities[].type` / `status` for `env`; `items` for `automations`.

### `by-thread`

```bash
chatgpt-dot-cli by-thread
```

| Flag | Default |
| --- | --- |
| positional `thread_id` | the dot's active root thread |
| `--dot-id` | the only dot. Used only when the thread id is omitted |

`--json` keys: `status`, `body`. If there is no root thread and you omit the id, exit 3 and stderr says `dot has no active root thread`.

### `messages`

Does not create a room. `--dot-id` only; there is no positional id.

```bash
chatgpt-dot-cli messages --limit 2
```

| Flag | Default | Limit |
| --- | --- | --- |
| `--dot-id` | the only dot | required when there is more than one |
| `--limit` | 20 | integer 1..32. Outside that range exits 2 and sends no request |
| `--before` | none | one message id; one older page, then stop |
| `--after` | none | one message id; one newer page, then stop |

The CLI does not send `cursor` and does not follow further pages. `--json` keys are always `name`, `lines`, and `messages`. With no room both lists are empty and `note` is `no messages yet (send creates the room)`; exit 0. `messages` is oldest to newest. `lines` is newest first. `role` is always `user` and does not say who spoke. Speakers are `dot:`, `you:`, or `unknown:`.

### `send`

The only command that writes. It posts text (and `--attach` files) into the dot's messaging inbox. Prefer `--stdin` so the UTF-8 text is not in argv or shell history. Stdin is sent unchanged, including a trailing newline from a file or `echo`. Positional text still works and prints a deprecation warning on stderr. `--stdin` and positional text cannot be used together.

```bash
chatgpt-dot-cli send --help
printf 'hello' | chatgpt-dot-cli send --stdin
```

| Flag | Default |
| --- | --- |
| `--stdin` | read UTF-8 message text from stdin |
| `--attach FILE` | attach a file (repeatable, up to 20 MB each). Files upload to the dot's messaging room first (`POST /messaging/rooms/{id}/files`, as the dot app does); the one message is sent only after every upload succeeded. A failed upload sends no message; files uploaded before the failure stay in the room (the error says how many). File download links print as `***` |
| `--attach-sha256 HEX` | expected sha256 of each `--attach` file, in the same order (repeatable). Each file is read once, and the hashed bytes are the uploaded bytes; a mismatch exits 2 and nothing is uploaded or sent |
| positional `text` | deprecated; still accepted. Put `--` before text that starts with `-` |
| `--dot-id` | the only dot |

Text mode prints `sent to NAME`. `--json` is the redacted created message, including `id`. The desktop main view can show it a little later.

## Exit codes and error messages

| Exit | Message | What to do |
| --- | --- | --- |
| 0 | Success. Email 403 `ineligible` is also success and prints `email channel ineligible` | Nothing. That account cannot use email |
| 2 | No subcommand. Help is printed | Add `list` or another subcommand |
| 2 | `chatgpt-dot-cli: error: --auth requires a path` | Pass a path after `--auth` |
| 2 | `chatgpt-dot-cli: error: send requires message text or --stdin` | Pass positional text or `--stdin` |
| 2 | `chatgpt-dot-cli: error: send cannot use --stdin with positional text` | Use one or the other |
| 2 | `chatgpt-dot-cli: error: cannot read send input; provide UTF-8 text on stdin` | Provide UTF-8 text on stdin |
| 2 | `limit must be an integer from 1 to 32` | Use `--limit` from 1 to 32 |
| 2 | `cannot read auth file: ... Run codex login with a ChatGPT account, or pass --auth PATH.` | Run `codex login`, or point `--auth` at the login file |
| 2 | `auth file is not valid json` | Run `codex login` again |
| 2 | `auth file is not a chatgpt login` | Log in with a ChatGPT account, not an API-key file |
| 2 | `auth file has no access token` or `auth file has no account id` | Run `codex login` again |
| 2 | `auth file has no valid tokens object` | Run `codex login` again |
| 2 | `auth file must be a regular file`, `must not be a symbolic link`, `must be owned by the current user`, or `permits group or other access; set its mode to 600` | Use a regular login file you own, mode 600, not a symlink or pipe |
| 3 | `ChatGPT login expired (401). Open Codex or run codex login, then retry.` | Run `codex login`, then retry |
| 3 | `network error: ...` | Check the network and retry |
| 3 | `response body was not JSON (likely Cloudflare)` | Wait and retry. For `summary`, use `--no-activity` |
| 3 | `GET ... STATUS`, sometimes with an API `code` | 401: log in again. 403/429/503: retry later |
| 3 | `dot id was not found; run chatgpt-dot-cli list and pass --dot-id` | Use an id from `list` |
| 3 | `more than one dot; run chatgpt-dot-cli list and pass --dot-id <id>` | Pass `--dot-id` |
| 3 | `no dot on this account` | Create a dot in ChatGPT first |
| 3 | `dot has no active root thread` | Pass a thread id to `by-thread`, or open a chat first |
| 3 | `message text is empty` | `send` needs text |
| 0 | stderr: `chatgpt-dot-cli: warning: positional send text is deprecated; use --stdin` | Switch to `--stdin`. The message was still sent |
| 0 | stderr: `messaging_room_preview has no aeon member` | Lines say `unknown:`. This is not a failure |

## Files, environment, cache, redaction

The CLI has no config file and reads one environment variable, `CODEX_HOME`, the same way Codex does. The only file it reads is the login file:

| System | Path |
| --- | --- |
| Linux | `$HOME/.codex/auth.json` |
| macOS | `$HOME/.codex/auth.json` |
| Windows | `%USERPROFILE%\.codex\auth.json` |
| `CODEX_HOME` set | `$CODEX_HOME/auth.json` |

The CLI does not write that file, does not change its permissions, and does not keep a disk cache, so it takes no file lock. On Linux and macOS, the opened login file must be a regular file owned by the current user, with no group or other access (normally mode 600). A final-component symlink or FIFO is refused without blocking; POSIX ACLs and parent directories are not checked. Windows rejects ordinary symlinks and non-regular files, and does not inspect ACLs. On Windows, stdout and stderr are set to UTF-8 with `errors=replace`, and newlines are LF.

The MCP `list` cache lives only in that process, for 15 seconds, and is cleared after `dot_send`.

`--json` redacts keys whose names match `token`, `secret`, `key`, `cookie`, `authorization`, `password`, or `session`, plus the exact keys `email`, `account_id`, `user_id`, `signaling_url`, `magic_link_url`, `magic_link_share_text`, and `inspector_url`. `account_user_id`, `id`, `aeon_id`, `created_at`, `content`, `preview`, `display_name`, `kind`, and `is_attached` are not redacted by that list.

## Safety

HTTP redirects are not followed. Text printed to the terminal escapes control characters so they stay visible; `--json` remains valid JSON and decodes to the original values.

Every command is read-only except `send`. `send` POSTs a text message. If there is no room yet, it also opens the messaging room.

This tool never pauses, resumes, or deletes a dot, never connects or disconnects a computer, never claims email, never uses voice, and never calls `/ps/orbit`.

## Troubleshooting

- Command not found: on Linux or macOS add `$HOME/.local/bin` to PATH. On Windows open a new terminal, or call `%USERPROFILE%\.local\bin`.
- Auth file missing: run `codex login`. Exit 2.
- `--limit 33` or `0`: exit 2, and no request is sent.
- `summary` is slow, or activity comes back empty: run `chatgpt-dot-cli summary --no-activity`.
- A non-JSON 403, 429, or 503 is usually Cloudflare. The CLI retries once, then exits 3.
- Email 403 `ineligible` is normal and exits 0.
- More than one dot: pass `--dot-id` on each read. `messages` and `send` accept only `--dot-id`.
- For the dot to work on your computer, the ChatGPT desktop app still has to be open.

## MCP and trinity-cli

MCP is optional. The stdio command is `chatgpt-dot-cli-mcp`. It reads only the default login file.

```bash
uv tool install --force "chatgpt-dot-cli[mcp] @ git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.2.6"
```

From a checkout of this repo:

```bash
uv pip install -e ".[mcp]"
```

If the MCP package is missing, `chatgpt-dot-cli-mcp` exits 1 and prints those two lines.

For cross-agent work (ask all three, hand off, digest) use [trinity-cli](https://gitlab.com/aa22396584/trinity-cli).

## Agent skill

Agent skill install on Linux and macOS: clone tag `v0.2.6` to `$HOME/.local/share/chatgpt-dot-cli`. If that checkout already exists, it runs `fetch --tags` and `checkout --detach`. If a target already exists and is not a symlink, the script prints a skip message on stderr and leaves it alone. A failed clone creates no links.

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

Windows has no matching symlink loop. Copy `skills\chatgpt-dot-cli` into the agent's skill directory.

## Tests and CI

Run the tests locally:

```bash
python3 -m unittest discover -s tests -q
```

CI: jobs use GitLab.com runners by default. Linux runs on Python 3.11, 3.12, and 3.13. Windows runs Python 3.12 on tags, manual runs, and main commits that change code, tests, or packaging. Maintainers can point jobs at their own runners by setting the CI/CD variables `LINUX_RUNNER_TAG` and `WINDOWS_RUNNER_TAG`. There is no macOS CI. Pushing a tag creates a GitLab Release and attaches the wheel and sdist. MIT, see [LICENSE](../LICENSE).

## Platforms

| OS | Python | How it was checked |
| --- | --- | --- |
| Linux | 3.11, 3.12, 3.13 | GitLab CI: the offline unit suite |
| Windows | 3.12 | GitLab CI: the same suite, run automatically when code, tests, or packaging change |
| macOS | 3.11, 3.12, 3.13 | Maintainer machine: the same suite, plus a first-run check that installs from the tag as the README says |

The tests do not contact ChatGPT. There is no macOS CI.
