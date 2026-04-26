#!/usr/bin/env python3
"""
eaiou Claude Code PostToolUse hook — records actions inside eaiou's storage
tree to the eaiou provenance graph.

Per the Option C bidirectional MCP integration (design note at
/scratch/repos/eaiou-admin/_notes/2026-04-25-claude-code-mcp-integration.md),
this hook is the smallest viable cut on the Claude Code side: every Edit/Write
that touches a path under /scratch/repos/eaiou/ auto-records to eaiou's
provenance log.

The hook is silent on success and silent on eaiou-unreachable (it must not
block the tool call). Failures are logged to /scratch/repos/eaiou/.claude/
hook_errors.log for later inspection.
"""

import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

EAIOU_API_URL = os.environ.get("EAIOU_API_URL", "http://127.0.0.1:8000")
EAIOU_API_TOKEN = os.environ.get("EAIOU_API_TOKEN", "")
EAIOU_REPO_ROOT = "/scratch/repos/eaiou"
SCOPED_TOOLS = {"Edit", "Write", "NotebookEdit"}
ERROR_LOG = "/scratch/repos/eaiou/.claude/hook_errors.log"


def _log_error(msg: str) -> None:
    """Append to error log; never raise."""
    try:
        with open(ERROR_LOG, "a") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def _file_path_in_scope(path: str) -> bool:
    """Return True only for paths under the eaiou repo."""
    if not path:
        return False
    try:
        resolved = str(Path(path).resolve())
        return resolved.startswith(EAIOU_REPO_ROOT)
    except Exception:
        return False


def _content_hash(path: str) -> str:
    """SHA256 of the file content; empty string on failure."""
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return ""


def _post_to_eaiou(payload: dict) -> None:
    """POST the action record to eaiou; swallow all errors."""
    url = f"{EAIOU_API_URL}/api/v1/provenance/claude_action"
    headers = {"Content-Type": "application/json"}
    if EAIOU_API_TOKEN:
        headers["Authorization"] = f"Bearer {EAIOU_API_TOKEN}"
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=2) as resp:
            resp.read()
    except urllib.error.URLError:
        # eaiou not running locally; expected in many sessions. Silent.
        pass
    except Exception as e:
        _log_error(f"post_failed: {type(e).__name__}: {e}")


def main() -> None:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return
        event = json.loads(raw)
    except json.JSONDecodeError as e:
        _log_error(f"json_decode_failed: {e}")
        return

    tool_name = event.get("tool_name", "")
    if tool_name not in SCOPED_TOOLS:
        return

    tool_input = event.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path", "")
    if not _file_path_in_scope(file_path):
        return

    payload = {
        "tool_name": tool_name,
        "action_type": "file_edit" if tool_name == "Edit" else (
            "file_create" if tool_name == "Write" else "notebook_edit"
        ),
        "file_path": file_path,
        "content_hash": _content_hash(file_path),
        "session_id": event.get("session_id", ""),
        "paper_cosmoid": "",
        "summary": f"{tool_name} on {os.path.relpath(file_path, EAIOU_REPO_ROOT)}",
    }
    _post_to_eaiou(payload)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        _log_error(f"hook_top_level_failure: {type(e).__name__}: {e}")
    sys.exit(0)
