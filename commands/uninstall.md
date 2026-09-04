---
description: Cleanly remove every AI Forging artifact from a forge workspace and its onboarded target repos — conventions, skills, seeded patterns, and settings entries — while preserving everything you created. Your feature folders (specs, plans, testing.md, run records) and user-captured patterns are never touched. Diff-and-ask on customized files; idempotent; never commits to git.
user_invocable: true
---

# /aiforging:uninstall

**Purpose:** Cleanly remove AI Forging artifacts from the forge workspace and all onboarded target repos, while preserving user-created content (feature specs/plans, user-captured patterns, customized files).

**Governance:** Interactive, diff-and-ask. Nothing is deleted silently. Every removal is presented and approved before execution.

---

## Prerequisites

- The plugin must still be loaded (this command runs from the plugin — once the plugin is uninstalled at the machine level, this command is no longer available).
- Can be run from **any directory** — the workspace, a target repo, or anywhere else. See Step 0 for how the invocation context determines scope.

## Step 0 — Detect invocation context and discover scope

The command works from three places, mirroring the run-anywhere model of `/aiforging:new-feature`:

### Case 1 — Invoked from inside a forge workspace

Detected by the workspace markers (same as `/aiforging:setup` Step 1): `./CLAUDE.md` matches `AI Forging( forge)? workspace` (both phrasings are in the wild), `./docs/features/README.md` exists, `./.claude/settings.json` exists.

Discover targets based on workspace scenario:

- **Scenario A (multi-repo):** read `settings.local.json` → list of target paths.
- **Scenario B (monorepo):** scan for sub-directories containing `.aiforging/`, checking TWO levels deep to catch both service wrapper placements (e.g., `webapp/.aiforging/`) and pre-v0.2.0 placements inside app subdirectories (e.g., `webapp/application/.aiforging/`). Deduplicate: if both `webapp/.aiforging/` and `webapp/application/.aiforging/` exist, treat them as one target (`webapp/`) and clean up both locations.
- **Scenario C (single repo):** check if `./.aiforging/` exists at the workspace root.

Default scope: **full** (workspace + all targets).

### Case 2 — Invoked from inside a target repo

Detected by: `./.aiforging/CLAUDE.md` exists (the per-repo pointer written during Phase B onboarding) AND the workspace markers are NOT present (this is a target, not a workspace).

Find the workspace:

1. Read `~/.claude/aiforging.json` to get the active workspace path.
2. If the pointer file doesn't exist or has no active workspace, ask the user: "What's the path to your forge workspace? (Or press Enter to clean up just this target without touching the workspace.)"
3. If a workspace is found, verify the cwd is registered in that workspace's `settings.local.json` (Scenario A) or is a sub-directory of the workspace (Scenario B/C).

Default scope: **this target only**. Offer to expand:

> "This looks like a target repo onboarded to the workspace at `<workspace-path>`. What would you like to clean up?"
>
> 1. **This target only** (default) — remove AI Forging artifacts from this repo.
> 2. **This target + workspace** — also clean up the workspace itself.
> 3. **Everything** — clean up the workspace and all its targets.

### Case 3 — Invoked from anywhere else

Use the run-anywhere pointer:

1. Read `~/.claude/aiforging.json` to get the active workspace path.
2. If found, confirm: "Your active AI Forging workspace is at `<path>`. Uninstall from there? [Y/n]"
3. If not found, abort: "No AI Forging workspace detected. Run this command from inside a workspace or target repo."

If the user confirms, resolve the workspace and proceed as Case 1.

### Present what was found

> "I'll walk you through removing AI Forging artifacts. Nothing is deleted until you approve each step."
>
> "Workspace: `/abs/path/to/workspace` (scenario: multi-repo)"
> "Targets found: 2"
> 1. `/abs/path/to/backend` — conventions, skills, patterns
> 2. `/abs/path/to/frontend` — conventions only
>
> "Scope: [full / workspace-only / pick targets / this-target-only]"

Options:

- **Full** (default when invoked from workspace) — clean workspace + all targets.
- **Workspace-only** — clean workspace artifacts, leave targets untouched.
- **Pick targets** — choose which targets to clean; workspace is always included.
- **This target only** (default when invoked from a target repo) — clean only the current target. The workspace and other targets are untouched. Skip Step 2 entirely.

The selected scope determines which steps run. If scope is "this target only", only Step 1 runs (for the current target) and Step 2 (workspace) is skipped. The summary in Step 4 adapts accordingly.

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
- `<target>/.aiforging/VERSION` — plugin version stamp
- `<target>/.aiforging/patterns/README.md` and `anti-patterns/README.md` — **tier placeholders, plugin-sourced.** They have no `seeded: true` frontmatter, so the seeded-vs-user-captured test would misclassify them as the user's work and keep them. Match them by filename instead: `README.md` inside a tier directory is always the plugin's placeholder, never a captured pattern. Remove the directory itself only if nothing else remains in it.
- `<target>/.aiforging/README.md` — refactoring docs (plugin copy)
- `<target>/.claude/skills/hammer-refactor/SKILL.md` — skill copy
- `<target>/.claude/skills/capture-pattern/SKILL.md` — skill copy

**Legacy locations — remove only if present.** Onboardings from before the two-tier model put things in a target that current onboardings never create. Check for them, remove them if found, and say so in the summary; do not report their absence as a problem:

- `<target>/.aiforging/README.md` — the pattern-library README. It now lives only at the workspace shared tier.
- `<target>/.aiforging/patterns/*.md` and `anti-patterns/*.md` **carrying `seeded: true` frontmatter** — seeded patterns now live only in the shared tier. Files in those directories **without** `seeded: true` are user captures and are never removed, in any scenario.

**Derive this list from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/artifacts.json` rather than from memory.** Every artifact the plugin installs is listed there with its scope and destination; anything in the manifest's `user_owned` list is never removed. A hardcoded list here goes stale exactly the way it did in `/aiforging:update-targets`, and the failure mode is worse — leftover files after an uninstall the user believes was clean.
- Seeded patterns in `<target>/.aiforging/patterns/` and `<target>/.aiforging/anti-patterns/` — files where YAML frontmatter contains `seeded: true`

### Category B — User-created (never remove)

- `<target>/.aiforging/patterns/*.md` where `seeded: true` is NOT present, **excluding `README.md`** — user-captured patterns
- `<target>/.aiforging/anti-patterns/*.md` where `seeded: true` is NOT present, **excluding `README.md`** — user-captured anti-patterns

### Category C — Settings entries (remove entries, not files)

- `<target>/.claude/settings.json` — remove the `enabledPlugins` entries for `aiforging` and (optionally) `superpowers`. Do NOT delete the file — other plugins or settings may be present.

### Present the target inventory

```
Target: /abs/path/to/backend

  REMOVE (plugin-sourced):
    .aiforging/architecture/              (5 files)
    .aiforging/tdd/                       (4 files)
    .aiforging/subagent-orchestration/    (1 file)
    .aiforging/CLAUDE.md                  (pointer)
    .aiforging/ANALYSIS.md                (analyzer output — regenerable)
    .aiforging/VERSION                    (plugin version stamp)
    .aiforging/patterns/README.md         (tier placeholder)
    .aiforging/anti-patterns/README.md    (tier placeholder)
    .claude/skills/hammer-refactor/       (skill copy)
    .claude/skills/capture-pattern/       (skill copy)

  REMOVE (legacy — only present on pre-two-tier onboardings):
    .aiforging/README.md                                    (now workspace-only)
    .aiforging/patterns/extract-service-from-controller.md  (seeded; now workspace-only)
    .aiforging/anti-patterns/fat-controller.md              (seeded; now workspace-only)
    .aiforging/anti-patterns/primitive-obsession.md         (seeded; now workspace-only)

  KEEP (your work):
    .aiforging/patterns/use-query-bus-for-reads.md          (user-captured)
    .aiforging/anti-patterns/anemic-domain-model.md         (user-captured)

  SETTINGS (remove entries only):
    .claude/settings.json → remove enabledPlugins for aiforging

  Proceed with this target? [Y/n / pick items]
```

**Also ask about superpowers:** "The `superpowers` plugin was enabled alongside `aiforging`. Remove its `enabledPlugins` entry too? [y/N]" Default: N — superpowers is useful on its own and the user may want to keep it.

## Step 2 — Inventory and classify (workspace)

**Skip this step if scope is "this target only".** The workspace is not in scope — only the target repo's artifacts are being removed.

### Category A — Plugin-sourced (safe to remove)

- `./.aiforging/VERSION` — plugin version stamp
- `./.aiforging/patterns/README.md` and `./.aiforging/anti-patterns/README.md` — tier placeholders (see the note above: match by filename, not by frontmatter)
- `./.claude/skills/capture-pattern/SKILL.md` — workspace skill copy
- `./.claude/skills/browser-testing/SKILL.md` — workspace skill copy (if installed)
- `./.claude/skills/review-loop/SKILL.md` — workspace skill copy (if installed)
- `./.aiforging/patterns/*.md` where `seeded: true` — seeded shared-tier patterns
- `./.aiforging/anti-patterns/*.md` where `seeded: true` — seeded shared-tier anti-patterns
- `./.aiforging/README.md` — refactoring docs (plugin copy)
- `~/.claude/aiforging.json` — run-anywhere pointer file

### Category B — User-created (never remove)

- `./docs/features/` — entire directory tree. Specs, plans, `testing.md` QA checklists, `notes.md`, `summary.md`, and the `ai-testing/` and `ai-reviews/` run records. All of it. **This is the user's intellectual work, and the run records are evidence of what was tested and decided.**
- `./.aiforging/patterns/*.md` where `seeded: true` is NOT present, **excluding `README.md`** — user-captured shared patterns
- `./.aiforging/anti-patterns/*.md` where `seeded: true` is NOT present, **excluding `README.md`** — user-captured shared anti-patterns

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

4. **Delete `settings.local.json`** (workspace, Scenario A only, full scope, if approved).
5. **Deregister target from workspace** (target-only scope, Scenario A). If a workspace was found and the target is registered in its `settings.local.json`, offer to remove the `additionalDirectories` entry for this target:

```bash
$FORGE_PY ${CLAUDE_PLUGIN_ROOT}/scripts/configure-directories.py remove \
  --settings-file <workspace>/.claude/settings.local.json \
  --directory "<abs-path-to-target>"
```

6. **Clear the run-anywhere pointer.** (Full scope only.) Remove the workspace entry from `~/.claude/aiforging.json`:

```bash
$FORGE_PY ${CLAUDE_PLUGIN_ROOT}/scripts/configure-workspace-pointer.py forget \
  --workspace "$(pwd)"
```

**No backups.** Unlike `update-targets` (which overwrites files that might be restored), uninstall deletes files that are exact copies of plugin content. The originals live in the plugin itself — re-running `/aiforging:setup` regenerates everything. Creating `.bak` files during an uninstall would defeat the purpose of cleaning up.

## Step 4 — Summary

**Full / workspace + targets scope:**

```
AI Forging artifacts removed.

Targets cleaned: 2
  /abs/path/to/backend — 11 plugin files removed, 2 user patterns kept
  /abs/path/to/frontend — 5 plugin files removed

Workspace cleaned:
  Plugin skills removed: capture-pattern, browser-testing, review-loop
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

**Target-only scope:**

```
AI Forging artifacts removed from this target.

Target: /abs/path/to/backend
  Plugin files removed: 11
  User patterns kept: 2
  Settings entries removed: aiforging (superpowers kept)

Your workspace at /abs/path/to/workspace was not modified.
To also clean up the workspace, run /aiforging:uninstall from there
(or re-run here and choose "Everything").

To fully remove the plugin from your machine:
  /plugin uninstall aiforging@<source>
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

### The workspace `.gitignore`

`/aiforging:setup` **appends** rules to the workspace `.gitignore` rather than owning the file — in monorepo and single-repo scenarios it belongs to the user's repo and may be hundreds of lines long. Uninstall does **not** remove those lines. Removing `*.bak-*` or `.DS_Store` from someone's `.gitignore` is far more likely to be unwanted than leaving four harmless lines behind. Mention them in the summary and let the user decide:

> Four lines were appended to `.gitignore` at onboarding (`.claude/settings.local.json`, `*.bak-*`, `.DS_Store`, `Thumbs.db`). They're left in place — they're harmless, and removing rules from a file you own is riskier than keeping them.

### Other plugins sharing `.claude/skills/`

Before removing any `.claude/skills/<name>/` directory the plugin installed (`hammer-refactor`, `capture-pattern`, `browser-testing`, `review-loop` — the authoritative list is `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/artifacts.json`), check that no other plugin contributed files to those directories. In practice this is unlikely (skill directory names are plugin-specific), but if unexpected files exist in a skill directory, warn and skip rather than deleting blindly.

### Service wrapper targets (v0.2.0+)

When a target was onboarded with service wrapper detection (e.g., `webapp/` wrapping `webapp/application/`), `.aiforging/` lives at the service root (`webapp/.aiforging/`), not inside the app subdirectory. The uninstall should clean up at the service root level. However, if the target was originally onboarded with v0.1.0 (which placed `.aiforging/` at `webapp/application/.aiforging/`), the pre-v0.2.0 artifacts may still exist at the old depth. Check both locations and clean up whichever exists. If both exist (partially migrated state), clean up both and note this in the summary.

### `~/.claude/aiforging.json` does not exist

If the user declined the global config pointer during setup (default N since v0.2.0), `~/.claude/aiforging.json` may not exist. Skip the pointer cleanup step silently — no error, no warning.

### Re-running uninstall

Idempotent. If artifacts are already gone, the inventory will show nothing to remove and the command exits cleanly.
