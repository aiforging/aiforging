# /aiforging:update-targets

**Purpose:** Propagate plugin-level updates (new or changed skills, conventions, shared-tier seeded patterns) into the forge workspace and all previously onboarded target repos, with diff-and-ask semantics. Nothing is overwritten silently.

**When to run:** After a plugin update (marketplace or `--plugin-dir` reload), or whenever you suspect the copies in your workspace or target repos have drifted from the current plugin version.

**Governance:** This command modifies files but NEVER executes refactors, runs tests, or commits to git. It stages changes and lets you review before committing.

---

## Prerequisites

- Must be run from inside an AI Forging workspace (the same directory markers that `/aiforging:setup` Phase A creates).
- The plugin must be loaded (either via marketplace install or `--plugin-dir`).

## Step 0 — Detect workspace and discover targets

Run the same workspace detection as `/aiforging:setup` Step 1:

```bash
test -f ./CLAUDE.md && head -c 500 ./CLAUDE.md | grep -q "AI Forging workspace" && echo "HAS_CLAUDE_MD" || echo "NO_CLAUDE_MD"
test -f ./docs/features/README.md && echo "HAS_FEATURES_README" || echo "NO_FEATURES_README"
test -f ./.claude/settings.json && echo "HAS_SETTINGS_JSON" || echo "NO_SETTINGS_JSON"
test -f ./.claude/settings.local.json && echo "HAS_SETTINGS_LOCAL" || echo "NO_SETTINGS_LOCAL"
```

If the required markers aren't present, abort:

> "This doesn't look like an AI Forging workspace. Run `/aiforging:setup` first to bootstrap one."

**Discover targets.** The target list depends on the workspace scenario:

- **Scenario A (multi-repo):** `settings.local.json` exists. Read `permissions.additionalDirectories` to get the list of target paths. Verify each path exists and contains `.aiforging/` (i.e., was actually onboarded, not just registered).
- **Scenario B (monorepo):** No `settings.local.json`. Scan for sub-directories that contain `.aiforging/` — these are the onboarded sub-projects.
- **Scenario C (single repo):** No `settings.local.json`. Check if `./.aiforging/` exists at the workspace root (the repo IS the target).

Present the discovered targets:

> "Found N onboarded target(s):"
>
> 1. `/abs/path/to/backend` — `.aiforging/` present, `hammer-refactor` skill present, `capture-pattern` skill present
> 2. `/abs/path/to/frontend` — `.aiforging/` present, no skills (frontend-only)
>
> "Proceed with update check? [Y/n]"

If no targets are found, suggest running `/aiforging:setup` to onboard one.

## Step 1 — Diff workspace-level artifacts

Check what's installed in the workspace against the current plugin version. For each artifact, compute a diff. Present all diffs at once, then ask for bulk or per-item approval.

### 1a. Workspace capture-pattern skill

Compare `./.claude/skills/capture-pattern/SKILL.md` against `${CLAUDE_PLUGIN_ROOT}/skills/capture-pattern/SKILL.md`.

If they differ, show a summary diff (not the full file — summarize the key changes in 2-3 sentences, then offer to show the full diff if the user wants).

### 1b. Shared-tier seeded patterns

For each `.md` file in `./.aiforging/patterns/` and `./.aiforging/anti-patterns/`:

1. Read the YAML frontmatter. If `seeded: true` is present, this file came from the plugin and is eligible for update.
2. Compare against the corresponding file in `${CLAUDE_PLUGIN_ROOT}/conventions/refactoring/patterns/` or `${CLAUDE_PLUGIN_ROOT}/conventions/refactoring/anti-patterns/` (match by filename).
3. If they differ, include in the diff report.

**Files where `seeded: true` is NOT present (or there's no frontmatter) are user-captured patterns. NEVER touch these.**

Also check for NEW seeded files in the plugin that don't exist in the workspace yet — these are additions, not updates.

### 1c. Shared-tier refactoring README

Compare `./.aiforging/README.md` against `${CLAUDE_PLUGIN_ROOT}/conventions/refactoring/README.md`. Include in diff report if different.

### 1d. Workspace templates (optional)

The workspace's `CLAUDE.md`, `README.md`, and `docs/features/README.md` were seeded from templates at init time. Users often customize these, so updates are OFFERED but defaulted to N:

> "Your workspace `CLAUDE.md` differs from the current template. This is expected if you've customized it. Would you like to see the diff? [y/N]"

If the user says yes, show the diff and offer to apply. Default: skip.

### Workspace diff summary

```
Workspace update summary:

  .claude/skills/capture-pattern/SKILL.md     — updated (tier selection rewrite)
  .aiforging/patterns/extract-service-from-controller.md  — unchanged
  .aiforging/anti-patterns/fat-controller.md   — updated (new example added)
  .aiforging/anti-patterns/primitive-obsession.md — unchanged
  .aiforging/README.md                         — updated (two-tier docs)
  NEW: .aiforging/patterns/some-new-pattern.md — new seeded pattern

  Workspace templates:                         — skipped (customized, default N)

Apply workspace updates? [Y/n / pick by number]
```

Default: Y (apply all). The user can also pick individual items by number to apply selectively.

**Before applying any overwrites**, create timestamped backups:

```bash
# For each file being overwritten:
cp <file> <file>.bak-$(date +%Y%m%d%H%M%S)
```

The `.gitignore` already covers `*.bak-*` patterns.

## Step 2 — Diff target-level artifacts (per target)

For each target discovered in Step 0, check what's installed against the current plugin version. Group all targets into a single report.

### 2a. Conventions library

For each conventions directory that should be present (`architecture/`, `tdd/`, `subagent-orchestration/`):

1. If the directory exists in the target's `.aiforging/`, diff each file against `${CLAUDE_PLUGIN_ROOT}/conventions/<dir>/`.
2. If a conventions directory is MISSING from the target but present in the plugin (e.g., `subagent-orchestration/` was added after the target was onboarded), flag it as a new addition.
3. Check for files in the target that don't exist in the plugin — these are target-specific additions. Leave them alone.

### 2b. Per-target CLAUDE.md pointer

Compare `<target>/.aiforging/CLAUDE.md` against a freshly rendered `${CLAUDE_PLUGIN_ROOT}/conventions/CLAUDE.md.template`. The template may contain variables (workspace path, target name) — render it with the target's actual values before diffing.

### 2c. Skills

For each skill that should be present (`hammer-refactor`, `capture-pattern` — backend/fullstack only):

1. If the skill exists in `<target>/.claude/skills/<skill>/SKILL.md`, diff against `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/SKILL.md`.
2. If the skill is MISSING from the target but should be there (backend/fullstack target with no hammer-refactor), flag as a new addition and offer to install.

### 2d. Frontend testing conventions (if installed)

If `<target>/.aiforging/frontend-testing/` exists, diff against `${CLAUDE_PLUGIN_ROOT}/conventions/frontend-testing/`.

### 2e. Target-local pattern directories

**Do NOT diff or modify target-local patterns.** These are user-captured, repo-specific patterns. The update-targets command has no authority over them.

However, if the target-local directories don't exist yet (target was onboarded before the two-tier model), offer to create them:

```bash
mkdir -p <target>/.aiforging/patterns <target>/.aiforging/anti-patterns
```

### Target diff summary (per target)

```
Target: /abs/path/to/backend (symfony-php)

  .aiforging/architecture/domain-driven-hexagonal.md  — updated
  .aiforging/architecture/naming.md                    — unchanged
  .aiforging/tdd/fire-red-green-refactor.md            — unchanged
  .aiforging/tdd/test-harness-requirements.md          — updated (new harness entries)
  NEW: .aiforging/subagent-orchestration/README.md     — new convention (not previously installed)
  .aiforging/CLAUDE.md                                 — updated (two-tier references)
  .claude/skills/hammer-refactor/SKILL.md              — updated (workspace resolution)
  .claude/skills/capture-pattern/SKILL.md              — updated (tier selection)
  .aiforging/frontend-testing/                         — not installed (frontend-only)
  .aiforging/patterns/ (target-local)                  — untouched (user-owned)

Apply updates to this target? [Y/n / pick by number]
```

Default: Y. Per-target approval — the user can accept all updates for one target and decline for another.

**Backup before overwrite**, same as workspace:

```bash
cp <file> <file>.bak-$(date +%Y%m%d%H%M%S)
```

## Step 3 — Apply updates

For each approved update (workspace or target):

1. Create the backup.
2. Copy the new version from `${CLAUDE_PLUGIN_ROOT}`.
3. For new additions (directories or files that didn't exist), create and copy.

**Do not commit.** After applying, print a summary of all changes made and suggest:

> "All approved updates have been applied. Changes are unstaged. Review them and commit when ready:
>
> ```bash
> # In the workspace:
> git diff
> git add -A && git commit -m 'aiforging: update conventions and skills to plugin vX.Y.Z'
>
> # In each target repo (if targets are separate repos):
> cd /abs/path/to/backend
> git diff
> git add -A && git commit -m 'aiforging: update conventions and skills to plugin vX.Y.Z'
> ```"

For monorepo/single-repo scenarios where the workspace IS the repo, there's only one commit to suggest.

## Step 4 — Post-update check

After applying updates, run a quick sanity check:

1. **Shared-tier pattern count.** Report how many patterns are in each tier:
   > "Shared tier: 3 patterns, 2 anti-patterns (all seeded). Target-local: 0 patterns per target (none captured yet)."

2. **Skill version consistency.** Confirm all targets now have the same version of each skill. If any target was skipped, note it:
   > "Warning: `/abs/path/to/frontend` was skipped — its `hammer-refactor` skill is still at the pre-update version."

3. **Architecture analyzer re-run suggestion.** If the conventions changed significantly (e.g., new rules in `architecture/`), suggest re-running the analyzer:
   > "The architecture conventions were updated. Consider re-running the `architecture-analyzer` skill on updated targets to get a fresh `ANALYSIS.md` that reflects the new rules."

---

## Edge cases

### Target repo doesn't exist at the registered path

If a path from `settings.local.json` doesn't exist on disk:

> "Warning: `/abs/path/to/old-target` is registered in `settings.local.json` but the directory doesn't exist. It may have been moved or deleted. Skip this target and continue? [Y/n]"

Offer to remove the stale entry from `settings.local.json` if the user confirms it's gone.

### Target has local modifications to plugin-sourced files

If a conventions file in the target has been manually edited (i.e., differs from BOTH the old plugin version and the new plugin version), the diff will show a three-way situation. In this case:

> "`.aiforging/architecture/naming.md` in `/abs/path/to/backend` has local modifications that don't match either the old or new plugin version. This file may have been intentionally customized. Options:
>
> 1. Overwrite with the new plugin version (backup will be created)
> 2. Skip this file (keep your local version)
> 3. Show the full diff"

Default: 2 (skip). Respect local customization.

### Plugin hasn't changed since last update

If no diffs are found:

> "All workspace and target artifacts are already up to date with the current plugin version. Nothing to do."

### First run after two-tier migration

If a target has seeded patterns in its target-local `<target>/.aiforging/patterns/` (from a pre-two-tier onboarding), offer to migrate them to the workspace shared tier:

> "This target has seeded patterns in its target-local directory (from before the two-tier model). These should live in the workspace's shared tier instead. Migrate them? [Y/n]"

If yes, move the seeded files (those matching plugin filenames) to the workspace shared tier, leaving any user-captured files in place.
