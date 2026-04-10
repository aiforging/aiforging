#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
configure-plugins.py — read and update the `enabledPlugins` map in a Claude
Code settings file.

Claude Code plugins are installed once at the machine level (via
`/plugin install`). Which plugins are actually *active* for a given scope is
controlled by the `enabledPlugins` map in that scope's `.claude/settings.json`:

    {
      "enabledPlugins": {
        "superpowers@claude-plugins-official": true,
        "aiforging@claude-plugins-official": true
      }
    }

This helper is what /aiforging:setup uses to:
  - Enable `superpowers` and `aiforging` in a freshly-initialized forge workspace
    (phase A), so Claude Code auto-activates them when running in the workspace.
  - Enable the same in each onboarded target repo's `.claude/settings.json`
    (phase B step B.3.5), so teammates cloning the target repo get the same
    auto-activation without needing to touch their personal config.

This helper ALWAYS targets `.claude/settings.json` (committed, shareable).
It is the counterpart to `configure-directories.py`, which ALWAYS targets
`.claude/settings.local.json` (gitignored, per-user) for `additionalDirectories`.
Never use this helper on `settings.local.json` or use `configure-directories.py`
on `settings.json` — mixing them is a bug and will leak per-user data into
shared repos.

Plugin identifiers follow the `<name>@<source>` convention where `<source>` is
the marketplace short name (e.g., `claude-plugins-official`, `superpowers-dev`).
The helper does not validate that the named plugin actually exists — it only
writes the map. Validation happens inside Claude Code at session start.

Contract
--------
  - Never writes unless explicitly asked (`enable` / `disable` / `set`).
  - Always creates a timestamped backup before writing.
  - Emits a JSON status object to stdout on every invocation.
  - Creates the target settings file (with an empty object) if it doesn't
    exist, because `/aiforging:setup` may be the first thing that ever touches
    a target repo's `.claude/` directory.
  - Never logs secrets; never reads files outside the target settings file.

Subcommands
-----------
  check      Read a settings file and report the current enabledPlugins map.
  enable     Enable one or more plugins (idempotent; repeatable --plugin).
  disable    Disable one or more plugins (no-op if absent).
  set        Replace the entire enabledPlugins map with the given plugins.

Each subcommand takes --settings-file <path> and writes atomically.
Plugin identifiers must be of the form `<name>@<source>`. Values are always
`true` when enabling; `disable` removes the key entirely rather than setting
it to `false`, matching the convention used in real-world settings files.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


PLUGIN_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+@[A-Za-z0-9_.-]+$")


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
        raise SystemExit(
            f"Expected object at root of {settings_path}, got {type(data).__name__}"
        )
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


def _current_map(data: dict[str, Any]) -> dict[str, bool]:
    current = data.get("enabledPlugins")
    if not isinstance(current, dict):
        return {}
    return {k: bool(v) for k, v in current.items() if isinstance(k, str)}


def _set_map(data: dict[str, Any], new_map: dict[str, bool]) -> dict[str, Any]:
    data["enabledPlugins"] = new_map
    return data


def _validate_plugin_ids(ids: list[str]) -> list[str]:
    bad = [p for p in ids if not PLUGIN_ID_RE.match(p)]
    if bad:
        raise SystemExit(
            "Invalid plugin identifier(s): "
            + ", ".join(bad)
            + ". Expected format: <name>@<source> (e.g., superpowers@claude-plugins-official)"
        )
    return ids


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_check(args: argparse.Namespace) -> int:
    settings_path = Path(_expand(args.settings_file))
    data = _load_settings(settings_path)
    current = _current_map(data)
    json.dump(
        {
            "action": "check",
            "settings_file": str(settings_path),
            "exists": settings_path.exists(),
            "enabledPlugins": current,
            "count": len(current),
        },
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


def cmd_enable(args: argparse.Namespace) -> int:
    settings_path = Path(_expand(args.settings_file))
    data = _load_settings(settings_path)
    current = _current_map(data)
    to_enable = _validate_plugin_ids(args.plugin)

    new_map = dict(current)
    enabled: list[str] = []
    already_on: list[str] = []
    for p in to_enable:
        if current.get(p) is True:
            already_on.append(p)
        else:
            new_map[p] = True
            enabled.append(p)

    changed = new_map != current
    backup = _backup(settings_path) if changed else None
    if changed:
        _set_map(data, new_map)
        _write_settings(settings_path, data)

    json.dump(
        {
            "action": "enable",
            "settings_file": str(settings_path),
            "enabled": enabled,
            "already_on": already_on,
            "current": new_map,
            "backup": str(backup) if backup else None,
        },
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


def cmd_disable(args: argparse.Namespace) -> int:
    settings_path = Path(_expand(args.settings_file))
    data = _load_settings(settings_path)
    current = _current_map(data)
    to_disable = _validate_plugin_ids(args.plugin)

    new_map = dict(current)
    disabled: list[str] = []
    for p in to_disable:
        if p in new_map:
            del new_map[p]
            disabled.append(p)

    changed = new_map != current
    backup = _backup(settings_path) if changed else None
    if changed:
        _set_map(data, new_map)
        _write_settings(settings_path, data)

    json.dump(
        {
            "action": "disable",
            "settings_file": str(settings_path),
            "disabled": disabled,
            "current": new_map,
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
    before = _current_map(data)
    after_ids = _validate_plugin_ids(args.plugin)
    after = {p: True for p in after_ids}

    changed = before != after
    backup = _backup(settings_path) if changed else None
    if changed:
        _set_map(data, after)
        _write_settings(settings_path, data)

    json.dump(
        {
            "action": "set",
            "settings_file": str(settings_path),
            "before": before,
            "after": after,
            "changed": changed,
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
        description="Manage the enabledPlugins map in a Claude Code settings file.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def _plugin_arg(sp: argparse.ArgumentParser) -> None:
        sp.add_argument(
            "--plugin",
            action="append",
            required=True,
            help="Plugin identifier in <name>@<source> form (repeatable).",
        )

    p_check = sub.add_parser("check", help="Report the current enabledPlugins map.")
    p_check.add_argument("--settings-file", required=True)
    p_check.set_defaults(func=cmd_check)

    p_enable = sub.add_parser("enable", help="Enable one or more plugins (idempotent).")
    p_enable.add_argument("--settings-file", required=True)
    _plugin_arg(p_enable)
    p_enable.set_defaults(func=cmd_enable)

    p_disable = sub.add_parser("disable", help="Disable (remove) one or more plugins.")
    p_disable.add_argument("--settings-file", required=True)
    _plugin_arg(p_disable)
    p_disable.set_defaults(func=cmd_disable)

    p_set = sub.add_parser("set", help="Replace the entire enabledPlugins map.")
    p_set.add_argument("--settings-file", required=True)
    _plugin_arg(p_set)
    p_set.set_defaults(func=cmd_set)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
