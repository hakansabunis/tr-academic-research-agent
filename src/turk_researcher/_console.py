"""Force Turkish characters to render correctly in this Python process only.

Files (parquet, json, jsonl) are already UTF-8 — this only fixes how the
Windows console renders our `print()` output.

We do NOT modify the user's PowerShell profile, environment variables, or
any system-level encoding. The Win32 SetConsoleOutputCP / SetConsoleCP
calls only affect the console attached to *this* process; once the Python
process exits, the parent shell returns to its previous code page.
"""
from __future__ import annotations

import sys


def setup_utf8() -> None:
    """Idempotent: safe to call multiple times."""
    # 1) Python-level: reconfigure stdout/stderr to UTF-8.
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, TypeError, ValueError):
            pass

    # 2) Windows-level: flip the console code page to CP_UTF8 (65001) for the
    # current process. Equivalent to running `chcp 65001` in this shell, but
    # scoped: PowerShell exits with its original code page intact.
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)
            kernel32.SetConsoleCP(65001)
        except (OSError, AttributeError):
            pass
