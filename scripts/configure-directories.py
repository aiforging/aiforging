#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
configure-directories.py — read and update `permissions.additionalDirectories`
in a Claude Code settings file.

This is the helper that /aiforging:setup uses after the project interview:
once the user has confirmed which target repos they want to drive from their
forge workspace, those absolute paths are written to `.claude/settings.local.json`
(the per-user, gitignored settings file).

Pairing guidance for AI Forging setup:
  - `additionalDirectories`  → configure-directories.py → `settings.local.json`
    (per-user, gitignored — absolute local paths never belong in a committed repo)
  - `enabledPlugins`         → configure-plugins.py    → `settings.json`
    (committed, shareable — identifiers are machine-agnostic)

Supported settings locations (chosen by the setup command, not this script):
  - <forge-workspace>/.claude/settings.local.json   (recommended default)
  - <target-repo>/.claude/settings.local.json       (if needed per-target)
  - ~/.claude/settings.json                         (user scope, legacy)

Contract:
  - Never writes unless explicitly asked (`set` / `add` / `remove`).
  - Always creates a timestamped backup before writing.
  - Emits a JSON status object to stdout on every invocation.
  - Never logs secrets; never reads files outside the target settings file.

Subcommands
-----------
  check       Read a settings file and report its current additionalDirectories.
  add         Add one or more directories (idempotent; no duplicates).
  remove      Remove one or more directories (no-op if absent).
  set         Replace the list entirely with the given directories.

Each subcommand takes --settings-file <path> and writes atomically.
Directory paths passed in should be absolute; ~ is expanded. Relative paths
are resolved against the cwd of the process.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------

def _expand(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))


def _load_settings(settings_path: Path) -> dict[str, Any]:
    if not settings_path.exists():
        return {}
    with settings_path.open("r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise SystemExit(
                f"Refusing to touch malformed settings file {settings_path}: {exc}"
            )
    if not isinstance(data, dict):
        raise SystemExit(f"Expected object at root of {settings_path}, got {type(data).__name__}")
    return data


def _backup(settings_path: Path) -> Path | None:
    if not settings_path.exists():
        return None
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = settings_path.with_suffix(settings_path.suffix + f".bak-{ts}")
    backup.write_bytes(settings_path.read_bytes())
    return backup


def _write_settings(settings_path: Path, data: dict[str, Any]) -> None:
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = settings_path.with_suffix(settings_path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=False)
        fh.write("\n")
    tmp.replace(settings_path)


def _current_list(data: dict[str, Any]) -> list[str]:
    perms = data.get("permissions")
    if not isinstance(perms, dict):
        return []
    lst = perms.get("additionalDirectories")
    if not isinstance(lst, list):
        return []
    # Keep only strings to be defensive
    return [x for x in lst if isinstance(x, str)]


def _set_list(data: dict[str, Any], new_list: list[str]) -> dict[str, Any]:
    perms = data.get("permissions")
    if not isinstance(perms, dict):
        perms = {}
        data["permissions"] = perms
    perms["additionalDirectories"] = new_list
    return data


def _normalize(paths: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in paths:
        p = _expand(raw)
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_check(args: argparse.Namespace) -> int:
    settings_path = Path(_expand(args.settings_file))
    data = _load_settings(settings_path)
    current = _current_list(data)
    json.dump(
        {
            "action": "check",
            "settings_file": str(settings_path),
            "exists": settings_path.exists(),
            "additionalDirectories": current,
            "count": len(current),
        },
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    settings_path = Path(_expand(args.settings_file))
    data = _load_settings(settings_path)
    current = _current_list(data)
    to_add = _normalize(args.directory)
    new_list = list(current)
    added: list[str] = []
    skipped: list[str] = []
    for p in to_add:
        if p in new_list:
            skipped.append(p)
        else:
            new_list.append(p)
            added.append(p)

    backup = _backup(settings_path) if added else None
    if added:
        _set_list(data, new_list)
        _write_settings(settings_path, data)

    json.dump(
        {
            "action": "add",
            "settings_file": str(settings_path),
            "added": added,
            "already_present": skipped,
            "current": new_list,
            "backup": str(backup) if backup else None,
        },
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    settings_path = Path(_expand(args.settings_file))
    data = _load_settings(settings_path)
    current = _current_list(data)
    to_remove = set(_normalize(args.directory))
    new_list = [p for p in current if p not in to_remove]
    removed = [p for p in current if p in to_remove]

    backup = _backup(settings_path) if removed else None
    if removed:
        _set_list(data, new_list)
        _write_settings(settings_path, data)

    json.dump(
        {
            "action": "remove",
            "settings_file": str(settings_path),
            "removed": removed,
            "current": new_list,
            "backup": str(backup) if backup else None,
        },
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


def cmd_set(args: argparse.Namespace) -> int:
    settings_path = Path(_expand(args.settings_file))
    data = _load_settings(settings_path)
    before = _current_list(data)
    after = _normalize(args.directory)
    backup = _backup(settings_path) if before != after else None
    if before != after:
        _set_list(data, after)
        _write_settings(settings_path, data)

    json.dump(
        {
            "action": "set",
            "settings_file": str(settings_path),
            "before": before,
            "after": after,
            "changed": before != after,
            "backup": str(backup) if backup else None,
        },
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Manage permissions.additionalDirectories in a Claude Code settings file.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def _common(sp: argparse.ArgumentParser, dirs_required: bool = True) -> None:
        sp.add_argument("--settings-file", required=True, help="Path to settings.json")
        if dirs_required:
            sp.add_argument(
                "--directory",
                action="append",
                required=True,
                help="Directory path (repeatable).",
            )

    p_check = sub.add_parser("check", help="Report current additionalDirectories.")
    p_check.add_argument("--settings-file", required=True)
    p_check.set_defaults(func=cmd_check)

    p_add = sub.add_parser("add", help="Add one or more directories (idempotent).")
    _common(p_add)
    p_add.set_defaults(func=cmd_add)

    p_rm = sub.add_parser("remove", help="Remove one or more directories.")
    _common(p_rm)
    p_rm.set_defaults(func=cmd_remove)

    p_set = sub.add_parser("set", help="Replace the entire list.")
    _common(p_set)
    p_set.set_defaults(func=cmd_set)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
