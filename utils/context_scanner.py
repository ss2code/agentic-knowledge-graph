"""
context_scanner.py — Pure-Python utilities for scanning project contexts and
reading their associated artifacts and debug logs.

No agent or LLM dependencies; safe to import anywhere.
"""

import json
import os
import re
from glob import glob
from pathlib import Path


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan_contexts(base_dir: str = "data") -> list[dict]:
    """
    Walk base_dir/*/. Return list of contexts that contain a user_data/ subdir.

    Each item:
        {
            "name": str,        # directory name
            "path": str,        # absolute path to context dir
            "state": dict|None, # parsed system_state.json, or None
            "last_updated": str|None,  # state["last_updated"] if present
        }

    Sorted by name.
    """
    base = Path(base_dir)
    if not base.is_dir():
        return []

    results = []
    for candidate in base.iterdir():
        if not candidate.is_dir():
            continue
        user_data = candidate / "user_data"
        if not user_data.is_dir():
            continue

        state = load_artifact(str(candidate), "system_state.json")
        last_updated = None
        if state and isinstance(state, dict):
            last_updated = state.get("last_updated")

        results.append(
            {
                "name": candidate.name,
                "path": str(candidate.resolve()),
                "state": state,
                "last_updated": last_updated,
            }
        )

    results.sort(key=lambda x: x["name"])
    return results


def load_artifact(context_path: str, filename: str) -> dict | None:
    """
    Read context_path/filename as JSON.
    Return parsed dict, or None if the file is missing or the JSON is invalid.
    """
    try:
        file_path = Path(context_path) / filename
        with open(file_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError:
        return None
    except OSError:
        return None


# Filename pattern: debug_llm_<Agent>_<YYYYMMDD_HHMMSS>.md  (timestamp optional)
_LOG_PATTERN = re.compile(
    r"^debug_llm_(?P<agent>[^_](?:[^_]|_(?!\d{8}))*?)(?:_(?P<ts>\d{8}_\d{6}))?\.md$"
)


def load_llm_logs(debug_dir: str, agent_prefix: str | None = None) -> list[dict]:
    """
    Glob debug_llm_*.md files in debug_dir.

    If agent_prefix is given, only include files whose agent name starts with
    agent_prefix (case-sensitive).

    Each returned item:
        {
            "agent": str,      # e.g. "IntentAgent"
            "timestamp": str,  # e.g. "20260202_085255", empty string if absent
            "content": str,    # full file text
        }

    Sorted by timestamp descending (newest first; files with no timestamp sort last).
    """
    debug_path = Path(debug_dir)
    if not debug_path.is_dir():
        return []

    glob_pattern = str(debug_path / "debug_llm_*.md")
    files = sorted(glob(glob_pattern))  # stable base order

    records = []
    for filepath in files:
        basename = os.path.basename(filepath)
        m = _LOG_PATTERN.match(basename)
        if not m:
            # Fallback: try a simpler split for files that don't fully match
            agent, ts = _fallback_parse(basename)
        else:
            agent = m.group("agent")
            ts = m.group("ts") or ""

        if agent_prefix and not agent.startswith(agent_prefix):
            continue

        content = _read_file_safe(filepath)
        if content is None:
            continue

        records.append({"agent": agent, "timestamp": ts, "content": content})

    # Sort: non-empty timestamps descending, then empty-timestamp entries last
    records.sort(key=lambda r: r["timestamp"], reverse=True)
    with_ts = [r for r in records if r["timestamp"]]
    without_ts = [r for r in records if not r["timestamp"]]
    return with_ts + without_ts


def get_last_run_time(debug_dir: str, agent_prefix: str) -> str | None:
    """
    Return a formatted timestamp string from the most-recent log matching
    agent_prefix.  Format: "YYYY-MM-DD HH:MM".

    Returns None if no matching log is found or the timestamp cannot be parsed.
    """
    logs = load_llm_logs(debug_dir, agent_prefix=agent_prefix)
    if not logs:
        return None

    # logs are sorted newest-first; pick first entry that has a timestamp
    for log in logs:
        ts = log.get("timestamp", "")
        if ts:
            formatted = _format_timestamp(ts)
            if formatted:
                return formatted

    return None


def load_graph_build_log(debug_dir: str) -> str | None:
    """
    Read graph_build_log.md raw content from debug_dir.
    Return None if the file does not exist.
    """
    log_path = Path(debug_dir) / "graph_build_log.md"
    return _read_file_safe(str(log_path))


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _read_file_safe(filepath: str) -> str | None:
    """Read a text file; return None on any error."""
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None


def _fallback_parse(basename: str) -> tuple[str, str]:
    """
    Minimal parser for filenames that don't match the strict regex.
    Strips 'debug_llm_' prefix and '.md' suffix, then tries to split off a
    trailing timestamp (YYYYMMDD_HHMMSS).
    """
    stem = basename
    if stem.startswith("debug_llm_"):
        stem = stem[len("debug_llm_"):]
    if stem.endswith(".md"):
        stem = stem[:-3]

    # Check whether the stem ends with a timestamp
    ts_match = re.search(r"_(\d{8}_\d{6})$", stem)
    if ts_match:
        ts = ts_match.group(1)
        agent = stem[: ts_match.start()]
    else:
        ts = ""
        agent = stem

    return agent, ts


def _format_timestamp(ts: str) -> str | None:
    """
    Convert 'YYYYMMDD_HHMMSS' → 'YYYY-MM-DD HH:MM'.
    Return None if the string doesn't match.
    """
    m = re.fullmatch(r"(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})", ts)
    if not m:
        return None
    year, month, day, hour, minute, _ = m.groups()
    return f"{year}-{month}-{day} {hour}:{minute}"
