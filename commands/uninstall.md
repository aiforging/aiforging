# /aiforging:uninstall

**Purpose:** Cleanly remove AI Forging artifacts from the forge workspace and all onboarded target repos, while preserving user-created content (feature specs/plans, user-captured patterns, customized files).

**Governance:** Interactive, diff-and-ask. Nothing is deleted silently. Every removal is presented and approved before execution.

---

## Prerequisites

- Must be run from inside an AI Forging workspace (same detection as `/aiforging:setup` Step 1).
- The plugin must still be loaded (this command runs from the plugin — once the plugin is uninstalled at the machine level, this command is no longer available).

## Step 0 — Discover scope

Detect workspace scenario and discover targets, same as `/aiforging:update-targets` Step 0:

- **Scenario A (multi-repo):** read `settings.local.json` → list of target paths.
- **Scenario B (monorepo):** scan for sub-directories containing `.aiforging/`.
- **Scenario C (single repo):** check if `./.aiforging/` exists at the workspace root.

Present what was found:

> "I'll walk you through removing AI Forging artifacts. Nothing is deleted until you approve each step."
>
> "Workspace: `/abs/path/to/workspace` (scenario: multi-repo)"
> "Targets found: 2"
> 1. `/abs/path/to/backend` — conventions, skills, patterns
> 2. `/abs/path/to/frontend` — conventions only
>
> "Scope: [full / workspace-only / pick targets]"

Options:

- **Full** (default) — clean workspace + all targets.
- **Workspace-only** — clean workspace artifacts, leave targets untouched.
- **Pick targets** — choose which targets to clean; workspace is always included.

## Step 1 — Inventory and classify (per target)

For each target in scope, scan and classify every AI Forging artifact:

### Category A — Plugin-sourced (safe to remove)

These are copies of plugin content, regenerable by re-running `/aiforging:setup`:

- `<target>/.aiforging/architecture/` — entire directory
- `<target>/.aiforging/tdd/` — entire directory
- `<target>/.aiforging/subagent-orchestration/` — entire directory
- `<target>/.aiforging/frontend-testing/` — entire directory (if present)
- `<target>/.aiforging/CLAUDE.md` — per-repo pointer file
- `<target>/.aiforging/ANALYSIS.md` — analyzer output (regenerable)
- `<target>/.aiforging/README.md` — refactoring docs (plugin copy)
- `<target>/.claude/skills/hammer-refactor/SKILL.md` — skill copy
- `<target>/.claude/skills/capture-pattern/SKILL.md` — skill copy
- Seeded patterns in `<target>/.aiforging/patterns/` and `<target>/.aiforging/anti-patterns/` — files where YAML frontmatter contains `seeded: true`

### Category B — User-created (never remove)

- `<target>/.aiforging/patterns/*.md` where `seeded: true` is NOT present — user-captured patterns
- `<target>/.aiforging/anti-patterns/*.md` where `seeded: true` is NOT present — user-captured anti-patterns

### Category C — Settings entries (remove entries, not files)

- `<target>/.claude/settings.json` — remove the `enabledPlugins` entries for `aiforging` and (optionally) `superpowers`. Do NOT delete the file — other plugins or settings may be present.

### Present the target inventory

```
Target: /abs/path/to/backend

  REMOVE (plugin-sourced):
    .aiforging/architecture/              (5 files)
    .aiforging/tdd/                       (3 files)
    .aiforging/subagent-orchestration/    (1 file)
    .aiforging/CLAUDE.md                  (pointer)
    .aiforging/ANALYSIS.md                (regenerable)
    .aiforging/README.md                  (plugin copy)
    .aiforging/patterns/extract-service-from-controller.md  (seeded)
    .aiforging/anti-patterns/fat-controller.md              (seeded)
    .aiforging/anti-patterns/primitive-obsession.md         (seeded)
    .claude/skills/hammer-refactor/       (skill copy)
    .claude/skills/capture-pattern/       (skill copy)

  KEEP (your work):
    .aiforging/patterns/use-query-bus-for-reads.md          (user-captured)
    .aiforging/anti-patterns/anemic-domain-model.md         (user-captured)

  SETTINGS (remove entries only):
    .claude/settings.json → remove enabledPlugins for aiforging

  Proceed with this target? [Y/n / pick items]
```

**Also ask about superpowers:** "The `superpowers` plugin was enabled alongside `aiforging`. Remove its `enabledPlugins` entry too? [y/N]" Default: N — superpowers is useful on its own and the user may want to keep it.

## Step 2 — Inventory and classify (workspace)

### Category A — Plugin-sourced (safe to remove)

- `./.claude/skills/capture-pattern/SKILL.md` — workspace skill copy
- `./.aiforging/patterns/*.md` where `seeded: true` — seeded shared-tier patterns
- `./.aiforging/anti-patterns/*.md` where `seeded: true` — seeded shared-tier anti-patterns
- `./.aiforging/README.md` — refactoring docs (plugin copy)
- `~/.claude/aiforging.json` — run-anywhere pointer file

### Category B — User-created (never remove)

- `./docs/features/` — entire directory tree. Specs, plans, all of it. **This is the user's intellectual work.**
- `./.aiforging/patterns/*.md` where `seeded: true` is NOT present — user-captured shared patterns
- `./.aiforging/anti-patterns/*.md` where `seeded: true` is NOT present — user-captured shared anti-patterns

### Category C — Settings entries (remove entries, not files)

- `./.claude/settings.json` — remove `enabledPlugins` entries for `aiforging` (and optionally `superpowers`).
- `./.claude/settings.local.json` — this file exists only for Scenario A. It contains `additionalDirectories` pointing at target repos. Offer to delete the entire file since it's AI Forging-specific (gitignored, per-user). But if it contains OTHER keys beyond `permissions.additionalDirectories`, remove only the `additionalDirectories` key.

### Category D — Template-seeded, possibly customized (ask individually)

These files were created from templates during Phase A but the user may have added their own content:

- `./CLAUDE.md` — workspace context. If the user has customized it significantly (compare against the template — if the diff is large, it's customized), default to KEEP. If it's unchanged from the template, default to REMOVE.
- `./README.md` — workspace overview. Same logic as CLAUDE.md.
- `./.gitignore` — may contain user-added entries beyond the template. Default: KEEP.
- `./docs/features/README.md` — convention reference. Default: KEEP (it's inside the protected `docs/features/` tree).

For each Category D file:

> "`./CLAUDE.md` was created by AI Forging setup but appears to have been customized. Remove it? [y/N]"

or

> "`./CLAUDE.md` is unchanged from the AI Forging template. Remove it? [Y/n]"

### Present the workspace inventory

```
Workspace: /abs/path/to/workspace

  REMOVE (plugin-sourced):
    .claude/skills/capture-pattern/       (skill copy)
    .aiforging/patterns/extract-service-from-controller.md  (seeded)
    .aiforging/anti-patterns/fat-controller.md              (seeded)
    .aiforging/anti-patterns/primitive-obsession.md         (seeded)
    .aiforging/README.md                  (plugin copy)
    ~/.claude/aiforging.json              (run-anywhere pointer)

  KEEP (your work):
    docs/features/                        (2 features, 6 files — never touched)
    .aiforging/patterns/use-query-bus-for-reads.md  (user-captured)

  ASK (template-seeded, possibly customized):
    ./CLAUDE.md                           — customized → default KEEP
    ./README.md                           — unchanged → default REMOVE
    ./.gitignore                          — default KEEP

  SETTINGS:
    .claude/settings.json → remove enabledPlugins for aiforging
    .claude/settings.local.json → delete file (AI Forging-specific)

  Proceed with workspace cleanup? [Y/n / pick items]
```

## Step 3 — Execute removals

For each approved removal:

1. **Delete files and directories.** Use `rm -rf` for directories, `rm` for files.
2. **Clean up empty parent directories.** After removing files from `.aiforging/patterns/`, if the directory is now empty, remove it. Walk up: if `.aiforging/` itself is now empty (all conventions removed, all patterns removed), remove it. Same for `.claude/skills/` — if both skill directories were removed and no other skills exist, remove `.claude/skills/`. But NEVER remove `.claude/` itself — it may contain settings files.
3. **Remove settings entries.** Use `configure-plugins.py disable` to cleanly remove `enabledPlugins` entries:

```bash
if command -v uv >/dev/null 2>&1; then FORGE_PY="uv run"; else FORGE_PY="python3"; fi

# Per target and workspace:
$FORGE_PY ${CLAUDE_PLUGIN_ROOT}/scripts/configure-plugins.py disable \
  --settings-file <path>/.claude/settings.json \
  --plugin aiforging@<source>

# If user also approved superpowers removal:
$FORGE_PY ${CLAUDE_PLUGIN_ROOT}/scripts/configure-plugins.py disable \
  --settings-file <path>/.claude/settings.json \
  --plugin superpowers@<source>
```

4. **Delete `settings.local.json`** (workspace, Scenario A only, if approved).
5. **Clear the run-anywhere pointer.** Remove the workspace entry from `~/.claude/aiforging.json`:

```bash
$FORGE_PY ${CLAUDE_PLUGIN_ROOT}/scripts/configure-workspace-pointer.py forget \
  --workspace "$(pwd)"
```

**No backups.** Unlike `update-targets` (which overwrites files that might be restored), uninstall deletes files that are exact copies of plugin content. The originals live in the plugin itself — re-running `/aiforging:setup` regenerates everything. Creating `.bak` files during an uninstall would defeat the purpose of cleaning up.

## Step 4 — Summary

```
AI Forging artifacts removed.

Targets cleaned: 2
  /abs/path/to/backend — 11 plugin files removed, 2 user patterns kept
  /abs/path/to/frontend — 5 plugin files removed

Workspace cleaned:
  Plugin skills removed: capture-pattern
  Seeded patterns removed: 3
  User patterns kept: 1
  Settings entries removed: aiforging (superpowers kept)
  Run-anywhere pointer: cleared
  Template files: CLAUDE.md kept (customized), README.md removed

Preserved (your work):
  docs/features/ — 2 features, 6 files (untouched)
  2 user-captured patterns across workspace + targets

To fully remove the plugin from your machine:
  /plugin uninstall aiforging@<source>

To remove superpowers too (if you no longer need it):
  /plugin uninstall superpowers@<source>
```

## Edge cases

### User-captured patterns with `seeded: true` edited by the user

A pattern file might have `seeded: true` in frontmatter but the user may have edited the body. The uninstall treats `seeded: true` as the signal — if the frontmatter says seeded, it's classified as plugin-sourced. This is correct because the user should have set `seeded: false` (or removed the field) when they edited it. If they didn't, the worst case is they lose their edits — but the summary shows exactly what was removed, and they can recover from git history.

### Target repo that was never fully onboarded

If a path in `settings.local.json` points to a directory with no `.aiforging/`, skip it. Offer to remove the stale `additionalDirectories` entry.

### Workspace with no targets

Valid — clean up workspace artifacts only.

### Empty `.aiforging/` after cleanup

If all seeded patterns are removed and no user-captured patterns exist, the `.aiforging/` directory at the workspace or target level will be empty. Remove it. But if ANY user-captured pattern remains, leave the directory structure intact.

### Other plugins sharing `.claude/skills/`

Before removing `.claude/skills/hammer-refactor/` or `.claude/skills/capture-pattern/`, check that no other plugin contributed files to those directories. In practice this is unlikely (skill directory names are plugin-specific), but if unexpected files exist in a skill directory, warn and skip rather than deleting blindly.

### Re-running uninstall

Idempotent. If artifacts are already gone, the inventory will show nothing to remove and the command exits cleanly.
