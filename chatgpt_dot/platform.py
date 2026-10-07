"""Paths, console encoding, and file helpers for Linux, macOS, and Windows.

This package does not spawn subprocesses, so there is no shell and no
executable lookup. The CLI does not write a config or cache file.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def codex_auth_path() -> Path:
    """Codex ChatGPT login. Codex keeps it under CODEX_HOME when that is set."""
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "auth.json"
    return Path.home() / ".codex" / "auth.json"


def configure_stdio() -> None:
    """On Windows, print UTF-8 so zh-TW text does not crash cp950 or cp1252.

    POSIX consoles are left alone. Newlines stay LF so JSON matches the docs.
    """
    if os.name != "nt":
        return
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace", newline="\n")
        except (OSError, ValueError):
            continue


def posix_mode(path: Path) -> int | None:
    """Unix permission bits, or None on Windows.

    Windows uses ACLs, not Unix mode bits, so this check does not run there.
    The CLI never refuses to read the auth file because of these bits.
    """
    if os.name == "nt":
        return None
    try:
        return path.stat().st_mode & 0o777
    except OSError:
        return None
