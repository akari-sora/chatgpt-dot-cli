"""Paths, console encoding, and file helpers for Linux, macOS, and Windows.

This package does not spawn subprocesses, so there is no shell and no
executable lookup. The CLI does not write a config or cache file.
"""

from __future__ import annotations

import errno
import os
import stat
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


class LoginFileError(Exception):
    """The login file cannot be used. The message is safe to print (no path)."""


def open_auth_file(path: Path):
    """Open the Codex login file and return a text handle.

    The check uses the opened descriptor, not a later path lookup. On POSIX the
    file must be a regular file owned by the current user, with no group or
    other access. A final-component symlink is refused with O_NOFOLLOW; a FIFO
    is opened with O_NONBLOCK so the process does not wait for a writer.
    POSIX ACLs and parent directories are not inspected. Windows rejects an
    ordinary symlink and a non-regular file, and does not inspect ACLs.
    """
    flags = os.O_RDONLY
    if os.name == "posix":
        flags |= os.O_NOFOLLOW | os.O_NONBLOCK
    elif path.is_symlink():
        raise LoginFileError("auth file must not be a symbolic link")
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        if os.name == "posix" and exc.errno == errno.ELOOP:
            raise LoginFileError("auth file must not be a symbolic link") from exc
        raise
    try:
        _require_usable_login(os.fstat(descriptor))
    except Exception:
        os.close(descriptor)
        raise
    try:
        return os.fdopen(descriptor, encoding="utf-8-sig")
    except Exception:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise


def _require_usable_login(info: os.stat_result) -> None:
    if not stat.S_ISREG(info.st_mode):
        raise LoginFileError("auth file must be a regular file")
    if os.name != "posix":
        return
    if info.st_uid != os.getuid():
        raise LoginFileError("auth file must be owned by the current user")
    if stat.S_IMODE(info.st_mode) & 0o077:
        raise LoginFileError("auth file permits group or other access; set its mode to 600")
