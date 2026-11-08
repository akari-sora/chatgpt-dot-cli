# chatgpt-dot-cli

English | [繁體中文](README.zh-TW.md)

Check, read, and message your ChatGPT Your dot from a terminal.

> Canonical repository and issues: <https://gitlab.com/aa22396584/chatgpt-dot-cli>. Part of the trinity-cli family: <https://gitlab.com/aa22396584/trinity-cli>

[![pipeline status](https://gitlab.com/aa22396584/chatgpt-dot-cli/badges/main/pipeline.svg)](https://gitlab.com/aa22396584/chatgpt-dot-cli/-/commits/main)
[![release](https://gitlab.com/aa22396584/chatgpt-dot-cli/-/badges/release.svg)](https://gitlab.com/aa22396584/chatgpt-dot-cli/-/releases)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## What it does

- A local client for the official ChatGPT Your dot, not a second dot. The desktop app calls the dot orbit; the HTTP resource is tbo.
- Reads plan usage, dot status, threads, activity, computers, automations, and messages. `send` is the only command that writes.
- Auth comes from the Codex ChatGPT login file. This CLI does not have its own account flow.
- "Your dot" is the default name, shown when `display_name` is empty. After you rename the dot in the ChatGPT app, the CLI prints the new name.
- Optional MCP server: `chatgpt-dot-cli-mcp`.

This repo is public. It needs Python 3.11, 3.12, or 3.13. Supported systems: see [Platforms](docs/reference.md#platforms).

## Install

Pinned to tag `v0.2.6`.

Linux or macOS:

```bash
uv tool install git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.2.6
chatgpt-dot-cli --version
```

Or:

```bash
pipx install git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.2.6
chatgpt-dot-cli --version
```

Windows (PowerShell):

```powershell
irm https://astral.sh/uv/install.ps1 | iex
uv tool install "git+https://gitlab.com/aa22396584/chatgpt-dot-cli.git@v0.2.6"
chatgpt-dot-cli --version
```

`--version` prints `chatgpt-dot-cli 0.2.6`. The command must be on PATH: uv and pipx put it in `$HOME/.local/bin`. Windows pipx, the release wheel, upgrade, and uninstall: [Install details](docs/reference.md#install-details).

## Set up

1. Install the [Codex CLI](https://github.com/openai/codex) and run `codex login` with a ChatGPT account.
2. Confirm with a read-only command (a few seconds): `chatgpt-dot-cli list`. Success prints one line per dot and ends with `N dot(s)`.

The login file is `$HOME/.codex/auth.json` (Windows: `%USERPROFILE%\.codex\auth.json`; `$CODEX_HOME/auth.json` when `CODEX_HOME` is set). Pass `--auth PATH` when it is somewhere else. See [First-time setup](docs/reference.md#first-time-setup).

## Quick start

`send` really does send; the block below only shows the shape of the output.

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

## Commands

| Command | What it does |
| --- | --- |
| `summary` | plan, dot status, and recent messages; `--no-activity` skips the activity read |
| `usage` | ChatGPT plan usage |
| `primary` | which dot is currently selected |
| `list` | dots with ids |
| `probe` | HTTP status and field names for every read |
| `show` | one dot's profile |
| `threads`, `activity`, `root-thread`, `computers`, `env`, `automations`, `email-status` | read-only views of one dot |
| `by-thread` | find the dot for a thread id |
| `messages` | recent messages (`--limit` 1..32, default 20; `--before` / `--after` one page); does not create a room |
| `send` | the only write: text from `--stdin`, files with `--attach FILE` and `--attach-sha256 HEX` |

Global flags: `--json` (redacted JSON, before or after the subcommand), `--auth PATH`, `--version`. With more than one dot, pass `--dot-id`. Every flag, JSON key, and error message: [docs/reference.md](docs/reference.md#command-reference).

## Safety and privacy

- Every command is read-only except `send`, which posts a message and, if there is no room yet, opens the messaging room. The tool never pauses, resumes, or deletes a dot, never connects or disconnects a computer, never claims email, never uses voice, and never calls `/ps/orbit`.
- The CLI talks only to `chatgpt.com`, with your own ChatGPT login. There is no telemetry, and nothing is stored on disk. HTTP redirects are not followed.
- The login file is read, never written, and tokens are never printed. `--json` redacts token, cookie, email, and account-id fields ([full list](docs/reference.md#files-environment-cache-redaction)).
- Text output and `--json` still contain message text, dot names, and ids. Remove them before pasting into an issue.

## For agents

- Add `--json` to any command. Exit 0 is success (email 403 `ineligible` included), 2 is usage or a login-file problem with no request sent, 3 is an API, network, or lookup error. [Exit codes and error messages](docs/reference.md#exit-codes-and-error-messages).
- `send --stdin` keeps the message text out of argv and shell history.
- The bundled skill is `skills/chatgpt-dot-cli/SKILL.md`. The script that links it into `~/.claude/skills`, `~/.codex/skills`, and the other agent skill directories is in [Agent skill](docs/reference.md#agent-skill).
- MCP (`chatgpt-dot-cli-mcp`, stdio, optional `[mcp]` extra): [MCP and trinity-cli](docs/reference.md#mcp-and-trinity-cli).
- For cross-agent work (ask all three, hand off, digest), use [trinity-cli](https://gitlab.com/aa22396584/trinity-cli).

## Documentation

- [docs/reference.md](docs/reference.md): install details, every command, exit codes and error messages, files and redaction, troubleshooting, MCP, agent skill, tests and CI, platforms.
- [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md) (report security problems there, not in a public issue), [CHANGELOG.md](CHANGELOG.md).

## Related projects

- trinity-cli — one CLI over three always-on agents (Your dot, Grok Bot, Muse): <https://gitlab.com/aa22396584/trinity-cli>
- chatgpt-dot-cli — ChatGPT Your dot (this repo): <https://gitlab.com/aa22396584/chatgpt-dot-cli>
- grok-bot-cli (fork, `gbot`) — Grok Bot: <https://gitlab.com/aa22396584/grok-bot-cli>
- muse-web-cli — Meta Muse via the web: <https://gitlab.com/aa22396584/muse-web-cli>

## License and disclaimer

MIT, see [LICENSE](LICENSE).

Unofficial: this is a personal project, not affiliated with, endorsed by, or supported by OpenAI. It calls the undocumented interfaces the ChatGPT app uses, and OpenAI can change them at any time. Automated use may break OpenAI's terms; any account risk is yours.
