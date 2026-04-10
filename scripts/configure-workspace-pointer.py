#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
configure-workspace-pointer.py — read and update the per-user forge workspace
pointer file at ~/.claude/aiforging.json.

Why this file exists
--------------------
AI Forging's daily-driver command `/aiforging:new-feature` (and future
`/aiforging:*` commands that need to know "which forge workspace are we
targeting right now?") can be invoked from any directory. The normal case is
that the user is already `cd`'d into their forge workspace — the command
detects that from the cwd. But there is also a "run anywhere" mode: the user
types `/aiforging:new-feature` from, say, their Downloads folder, because they
had an idea for a feature and didn't want to context-switch into the workspace
first.

For that mode to work, there has to be a per-user file that says "your active
forge workspace is at <path>." That file is `~/.claude/aiforging.json`. It
lives under the user's Claude Code config dir (`~/.claude/`) and is owned by
this helper script.

File shape
----------
    {
      "active_workspace": "/abs/path/to/forge/workspace",
      "workspaces": [
        "/abs/path/to/forge/workspace",
        "/abs/path/to/another/workspace"
      ]
    }

- `active_workspace`: the single path that "run anywhere" commands target.
  Always absolute. May be absent if the user has never initialized a workspace.
- `workspaces`: a history of every workspace this user has initialized or
  onboarded a target into, newest first. Never pruned automatically — the
  user is the only one who removes entries (via the `forget` subcommand). The
  list exists so multi-workspace users can list and switch between them.

Who writes this file
--------------------
Only `/aiforging:setup` writes it:

- Phase A (init-workspace) writes the newly-created workspace as active and
  prepends it to `workspaces` (if not already present).
- Phase B (onboard-project) sets active to the current workspace at the end of
  onboarding, and prepends it to `workspaces` (if not already present). This
  makes the most-recently-used workspace the active one for run-anywhere.

`/aiforging:new-feature` (and future daily-driver commands) READ this file but
never write it.

Contract
--------
  - Never writes unless explicitly asked (`set-active` / `add` / `forget`).
  - Always creates a timestamped backup before writing.
  - Emits a JSON status object to stdout on every invocation.
  - Creates the pointer file (with `{}`) if it doesn't exist and the user is
    mutating it; `check` on a missing file returns `exists: false` without
    creating anything.
  - Never prunes the `workspaces` history on its own.
  - Validates that workspace paths are absolute and exist. A non-existent path
    is rejected (prevents typos from nuking the active workspace). `--force`
    allows the user to add a path that doesn't exist yet (for scripts that
    bootstrap a workspace and register it in one go).
  - Never reads or touches any file other than the pointer file itself.
  - Refuses to run if `--pointer-file` resolves to anything other than a
    regular file or missing file (no symlinks to unexpected places, no
    directories).

Subcommands
-----------
  check        Read the pointer file and report its contents.
  set-active   Set `active_workspace` to the given path; add to `workspaces`
               if missing.
  add          Add a path to `workspaces` without changing `active_workspace`.
               Useful for history without switching the current target.
  forget       Remove a path from `workspaces`. If the removed path was the
               active one, clear `active_workspace` (do not guess a
               replacement — the user must explicitly pick one).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Any


DEFAULT_POINTER = "~/.claude/aiforging.json"


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------

def _expand(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))


def _resolve_pointer(arg: str | None) -> Path:
    raw = arg if arg else DEFAULT_POINTER
    resolved = Path(_expand(raw))
    # Safety: if it exists, it must be a regular file.
    if resolved.exists() and not resolved.is_file():
        raise SystemExit(
            f"Refusing to operate on {resolved}: expected a regular file, "
            f"got {'directory' if resolved.is_dir() else 'non-file'}"
        )
    return resolved


def _load_pointer(pointer_path: Path) -> dict[str, Any]:
    if not pointer_path.exists():
        return {}
    with pointer_path.open("r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise SystemExit(
                f"Refusing to touch malformed pointer file {pointer_path}: {exc}"
            )
    if not isinstance(data, dict):
        raise SystemExit(
            f"Expected object at root of {pointer_path}, got {type(data).__name__}"
        )
    return data


def _normalize(data: dict[str, Any]) -> dict[str, Any]:
    """Ensure the pointer file has the expected shape."""
    out: dict[str, Any] = {}
    active = data.get("active_workspace")
    if isinstance(active, str) and active:
        out["active_workspace"] = active
    workspaces = data.get("workspaces")
    if isinstance(workspaces, list):
        out["workspaces"] = [w for w in workspaces if isinstance(w, str) and w]
    else:
        out["workspaces"] = []
    return out


def _backup(pointer_path: Path) -> Path | None:
    if not pointer_path.exists():
        return None
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = pointer_path.with_suffix(pointer_path.suffix + f".bak-{ts}")
    backup.write_bytes(pointer_path.read_bytes())
    return backup


def _write_pointer(pointer_path: Path, data: dict[str, Any]) -> None:
    pointer_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = pointer_path.with_suffix(pointer_path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=False)
        fh.write("\n")
    tmp.replace(pointer_path)


def _validate_workspace_path(path_str: str, force: bool) -> str:
    resolved = _expand(path_str)
    if not os.path.isabs(resolved):
        raise SystemExit(
            f"Workspace path must be absolute: {path_str} -> {resolved}"
        )
    if not force and not os.path.isdir(resolved):
        raise SystemExit(
            f"Refusing to register workspace path that doesn't exist: {resolved}. "
            f"Use --force if you're registering a workspace that's about to be created."
        )
    return resolved


def _prepend_unique(seq: list[str], item: str) -> list[str]:
    """Return a new list with `item` at the front and any existing copies removed."""
    return [item] + [x for x in seq if x != item]


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_check(args: argparse.Namespace) -> int:
    pointer_path = _resolve_pointer(args.pointer_file)
    exists = pointer_path.exists()
    data = _normalize(_load_pointer(pointer_path)) if exists else {"workspaces": []}
    active = data.get("active_workspace")
    workspaces = data.get("workspaces", [])
    # Report whether the active path still resolves to an extant directory.
    active_exists = bool(active) and os.path.isdir(_expand(active))
    json.dump(
        {
            "action": "check",
            "pointer_file": str(pointer_path),
            "exists": exists,
            "active_workspace": active,
            "active_exists": active_exists,
            "workspaces": workspaces,
            "workspace_count": len(workspaces),
        },
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


def cmd_set_active(args: argparse.Namespace) -> int:
    pointer_path = _resolve_pointer(args.pointer_file)
    new_active = _validate_workspace_path(args.workspace, args.force)
    data = _normalize(_load_pointer(pointer_path))

    previous_active = data.get("active_workspace")
    changed_active = previous_active != new_active

    workspaces = data.get("workspaces", [])
    new_workspaces = _prepend_unique(workspaces, new_active)
    changed_workspaces = new_workspaces != workspaces

    changed = changed_active or changed_workspaces
    backup = _backup(pointer_path) if changed else None

    data["active_workspace"] = new_active
    data["workspaces"] = new_workspaces

    if changed:
        _write_pointer(pointer_path, data)

    json.dump(
        {
            "action": "set-active",
            "pointer_file": str(pointer_path),
            "previous_active": previous_active,
            "active_workspace": new_active,
            "changed_active": changed_active,
            "changed_workspaces": changed_workspaces,
            "workspaces": new_workspaces,
            "backup": str(backup) if backup else None,
        },
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    pointer_path = _resolve_pointer(args.pointer_file)
    to_add = _validate_workspace_path(args.workspace, args.force)
    data = _normalize(_load_pointer(pointer_path))

    workspaces = data.get("workspaces", [])
    if to_add in workspaces:
        added = False
        new_workspaces = workspaces
    else:
        added = True
        new_workspaces = _prepend_unique(workspaces, to_add)

    changed = added
    backup = _backup(pointer_path) if changed else None

    data["workspaces"] = new_workspaces
    if changed:
        _write_pointer(pointer_path, data)

    json.dump(
        {
            "action": "add",
            "pointer_file": str(pointer_path),
            "added": added,
            "workspace": to_add,
            "workspaces": new_workspaces,
            "backup": str(backup) if backup else None,
        },
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


def cmd_forget(args: argparse.Namespace) -> int:
    pointer_path = _resolve_pointer(args.pointer_file)
    # `forget` does NOT require the path to exist on disk — the whole point is
    # that the user is removing a stale entry.
    target = _expand(args.workspace)
    data = _normalize(_load_pointer(pointer_path))

    workspaces = data.get("workspaces", [])
    was_present = target in workspaces
    new_workspaces = [w for w in workspaces if w != target]

    previous_active = data.get("active_workspace")
    cleared_active = previous_active == target
    if cleared_active:
        data.pop("active_workspace", None)

    changed = was_present or cleared_active
    backup = _backup(pointer_path) if changed else None

    data["workspaces"] = new_workspaces
    if changed:
        _write_pointer(pointer_path, data)

    json.dump(
        {
            "action": "forget",
            "pointer_file": str(pointer_path),
            "workspace": target,
            "was_present": was_present,
            "cleared_active": cleared_active,
            "workspaces": new_workspaces,
            "active_workspace": data.get("active_workspace"),
            "backup": str(backup) if backup else None,
        },
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


# ---------------------------------------------------------------------------
# Argparse wiring
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read and update the per-user forge workspace pointer file "
            "(~/.claude/aiforging.json by default)."
        ),
    )
    parser.add_argument(
        "--pointer-file",
        default=None,
        help=(
            "Path to the pointer file. Defaults to ~/.claude/aiforging.json. "
            "Override for tests or non-default user config layouts."
        ),
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser(
        "check",
        help="Read the pointer file and report its contents without writing.",
    )
    p_check.set_defaults(func=cmd_check)

    p_set = sub.add_parser(
        "set-active",
        help=(
            "Set active_workspace to <workspace> and add it to the workspaces "
            "list if not already present."
        ),
    )
    p_set.add_argument("--workspace", required=True, help="Absolute path to the forge workspace.")
    p_set.add_argument(
        "--force",
        action="store_true",
        help="Allow a path that doesn't yet exist (for bootstrap scripts).",
    )
    p_set.set_defaults(func=cmd_set_active)

    p_add = sub.add_parser(
        "add",
        help=(
            "Add a workspace path to the workspaces list without changing "
            "active_workspace."
        ),
    )
    p_add.add_argument("--workspace", required=True, help="Absolute path to the forge workspace.")
    p_add.add_argument(
        "--force",
        action="store_true",
        help="Allow a path that doesn't yet exist.",
    )
    p_add.set_defaults(func=cmd_add)

    p_forget = sub.add_parser(
        "forget",
        help=(
            "Remove a workspace path from the workspaces list. If the removed "
            "path was active, clear active_workspace (user must pick a new one)."
        ),
    )
    p_forget.add_argument("--workspace", required=True, help="Absolute path to forget.")
    p_forget.set_defaults(func=cmd_forget)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
