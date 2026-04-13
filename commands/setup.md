---
description: Interactive setup for the AI Forging framework. Phase A bootstraps a forge workspace in an empty directory (central CLAUDE.md, docs/features/, split .claude/settings.json + settings.local.json, .gitignore, capture-pattern skill, plugin dependency check). Phase B onboards target projects into an existing workspace (detect, analyze, register as additionalDirectories, copy conventions, seed pattern library, optionally install the hammer-refactor + capture-pattern skills bundle, optionally git-init the workspace).
user_invocable: true
---

# /aiforging:setup

This command has **two phases** which it detects and runs in sequence. You MUST detect the phase before asking questions, and you MUST use the helper scripts for all configuration — do NOT manually read or write settings files.

- **Phase A — init-workspace.** Runs when the current directory is NOT yet a forge workspace. Bootstraps the workspace: creates `CLAUDE.md`, `README.md`, `docs/features/README.md`, both `.claude/settings.json` (committed, holds `enabledPlugins`) and `.claude/settings.local.json` (gitignored, holds `permissions.additionalDirectories`), and a `.gitignore`. Checks for the `superpowers` plugin dependency. Optionally runs the git integration subroutine to initialize a git repo and stage the initial commit.
- **Phase B — onboard-project.** Runs when the current directory IS already a forge workspace. Interviews the user for a target project to onboard, runs detection, registers the project under `permissions.additionalDirectories` (in `.claude/settings.local.json`, the per-user file), writes an `enabledPlugins` block into the target repo's own `.claude/settings.json`, copies the conventions library into the target's `.aiforging/`, runs the architecture analyzer, optionally installs the `hammer-refactor` + `capture-pattern` skills bundle and seeds the pattern library. At the end, runs the git integration subroutine to either initialize the workspace as a git repo (first time) or commit the onboarding as a follow-up commit (subsequent times).

Phase B is re-runnable: every time the user wants to onboard another target project into an existing workspace, they re-run `/aiforging:setup` from the workspace root.

This command is **install + analyze + propose plan**. It never executes refactors. If the user asks you to "just do it", remind them of this boundary and stop.

## Settings file split (important — read before Phase A or Phase B touches any settings)

The forge workspace uses Claude Code's native two-file settings convention to cleanly separate shared configuration from per-user state:

- **`.claude/settings.json`** — committed to the workspace's git repo. Contains `enabledPlugins` and any other key that SHOULD be the same for every teammate who clones the workspace. Never contains absolute local paths.
- **`.claude/settings.local.json`** — gitignored. Contains `permissions.additionalDirectories` and anything else that's per-user or machine-specific. Absolute paths to target repos live here.

Claude Code reads both files at session start and merges them. This means a teammate cloning the workspace gets `enabledPlugins` (superpowers + aiforging auto-activate) but must populate `settings.local.json` with their own target repo paths — via re-running `/aiforging:setup` on their own machine.

**Every time this command writes settings, it must target the right file.** The helper scripts exist for exactly this:

- `configure-plugins.py` → always targets `.claude/settings.json` (committed). Writes `enabledPlugins`.
- `configure-directories.py` → always targets `.claude/settings.local.json` (per-user). Writes `permissions.additionalDirectories`.
- `configure-workspace-pointer.py` → always targets `~/.claude/aiforging.json` (per-user, per-machine, under the user's Claude Code config dir — NOT under any workspace or target repo). Writes the `active_workspace` + `workspaces` pointer used by run-anywhere commands. The pointer file is a third kind of config entirely: it is not a Claude Code settings file, it is an AI-Forging-specific pointer that lives alongside Claude Code's user settings.

Never mix these up. If you find yourself writing `additionalDirectories` into `settings.json`, `enabledPlugins` into `settings.local.json`, or workspace pointer data into either of those files, you are introducing a bug.

---

## Helper script runner (uv vs python3)

The helper scripts (`configure-plugins.py`, `configure-directories.py`, `configure-workspace-pointer.py`) and the stack detector (`detect-project.py`) are PEP 723 single-file scripts with NO third-party dependencies. They are designed to be run with `uv run`, but any Python 3.10+ interpreter will execute them correctly — the `# /// script` metadata header is inert when invoked directly with `python3`.

**This matters because `uv` is NOT guaranteed to be on the user's interactive shell PATH.** On the author's own machine (2026-04-10 dogfood session), `uv` was installed but not on PATH at Claude Code invocation time, causing `uv run …` calls from this command to fail. The workaround is to probe for `uv` once and fall back to `python3`.

**Before calling any helper script**, set a runner variable using this probe. Run it once at the start of Phase A (right before Step A.2's first helper call) and once at the start of Phase B (right before Step B.1's detector call) — shell calls from Claude Code are independent so the variable won't survive between bash invocations, which means you must inline this probe into each helper-script bash block:

```bash
# Probe for uv; fall back to python3. Both are equivalent for these scripts
# because they have no third-party deps.
if command -v uv >/dev/null 2>&1; then
  FORGE_PY="uv run"
else
  FORGE_PY="python3"
fi
```

Then invoke each helper with `$FORGE_PY` in place of `uv run`:

```bash
$FORGE_PY ${CLAUDE_PLUGIN_ROOT}/scripts/configure-plugins.py enable \
  --settings-file ./.claude/settings.json \
  --plugin aiforging@claude-plugins-official
```

Every helper-script invocation below uses this pattern. If you see `uv run …` bare without the probe block above it, that's a bug — add the probe.

---

## Step 0 — Orient yourself

Before running any detection, load the following into your context without summarizing to the user:

- **The three-layer model.** You are running the AI Forging plugin *as an end user*, not as a plugin developer. There are three distinct locations with different lifecycles: the **plugin source repo** (wherever `${CLAUDE_PLUGIN_ROOT}` resolves to — read-only from this command's perspective, NEVER modify), the **forge workspace** (the cwd if Phase A is running, or the already-initialized workspace the user is running Phase B from), and each **target repo** registered under `permissions.additionalDirectories` in the workspace's `settings.local.json`. Every write in this command goes to either the forge workspace or a target repo. No write EVER goes to the plugin source.
- **The slice plan format.** When Phase B Step B.9 drafts a feature plan, write it in the AI Forging slice format documented at `${CLAUDE_PLUGIN_ROOT}/conventions/features/README.md` (read-only reference — read it on demand when you reach Step B.9, do not copy it).
- **Do NOT read or reference `${CLAUDE_PLUGIN_ROOT}/PLAN.md`.** That file is the plugin author's development log, not an end-user resource. Reading it pollutes end-user runs with plugin-authoring context; writing to it would mutate the plugin source repo, which this command is forbidden from doing.

---

## Step 0.5 — Scenario interview (first run only)

On a fresh run (no workspace markers detected yet), ask the user about their codebase organization before routing to Phase A. This determines whether the workspace will be a separate directory or the repo itself.

> "How is your codebase organized?"
>
> 1. **Multiple independent repos** — e.g., a backend API in one repo and a frontend app in another.
> 2. **Monorepo** — one repo with distinct sub-projects (e.g., `frontend/`, `backend/`, `packages/*`).
> 3. **Single repo** — one repo, one stack (or tightly intertwined stacks in one directory tree).

Based on the answer:

- **Multiple repos (Scenario A)** → ask: "Do you already have a repo where centralized planning documents live for your team to share? Or would you like me to guide you toward creating a new one?"
  - If they have one → the user should `cd` into that repo and re-run `/aiforging:setup`. It becomes the forge workspace. Route to Phase A (which will detect the empty workspace state) and note to the user that they'll onboard their other repos via Phase B.
  - If they want to create one → the current empty directory becomes the forge workspace. Route to Phase A as currently designed (separate workspace).
- **Monorepo (Scenario B)** → the user should be inside (or `cd` into) the monorepo root. The workspace IS the monorepo. Route to Phase A with `scenario=monorepo`. Phase A will skip `settings.local.json` creation (no `additionalDirectories` needed — everything is under one root) and will detect sub-projects after workspace initialization (see Step A.2.7).
- **Single repo (Scenario C/D)** → the user should be inside (or `cd` into) the repo root. The workspace IS the repo. Route to Phase A with `scenario=single-repo`. Phase A will skip `settings.local.json` creation and treat the repo itself as the single target.

Record the scenario choice — Phase B behavior depends on it (multi-repo Phase B uses `additionalDirectories`; monorepo/single-repo Phase B installs conventions into sub-projects or the repo root directly).

**Skip this interview** if the workspace is already initialized (all four markers present) — Phase B knows the scenario from the existing workspace state.

---

## Step 1 — Detect the phase

The current working directory (cwd) at invocation time tells you which phase to run.

**A directory is already a forge workspace if the following REQUIRED markers are present:**

1. `./CLAUDE.md` exists AND contains the string `AI Forging workspace` somewhere in the first 500 bytes (the marker from the workspace template).
2. `./docs/features/README.md` exists.
3. `./.claude/settings.json` exists (committed, holds `enabledPlugins`).

**Optional marker (Scenario A only):**

4. `./.claude/settings.local.json` exists (gitignored, holds `additionalDirectories`). This file is ONLY present in Scenario A (multi-repo) workspaces. Monorepo and single-repo workspaces (Scenarios B/C) don't create it because the workspace IS the repo — no external paths to register.

Run these checks:

```bash
test -f ./CLAUDE.md && head -c 500 ./CLAUDE.md | grep -q "AI Forging workspace" && echo "HAS_CLAUDE_MD" || echo "NO_CLAUDE_MD"
test -f ./docs/features/README.md && echo "HAS_FEATURES_README" || echo "NO_FEATURES_README"
test -f ./.claude/settings.json && echo "HAS_SETTINGS_JSON" || echo "NO_SETTINGS_JSON"
test -f ./.claude/settings.local.json && echo "HAS_SETTINGS_LOCAL" || echo "NO_SETTINGS_LOCAL"
```

**Migration note:** if you find a workspace that has `./CLAUDE.md` and `./docs/features/README.md` but only `./.claude/settings.json` (no `settings.local.json`) AND that `settings.json` contains `permissions.additionalDirectories`, the workspace was created by an older version of this command that hadn't yet split the settings files. Treat this as Phase B (workspace exists) but warn the user and offer to migrate: move `permissions.additionalDirectories` from `settings.json` to `settings.local.json`, keeping `enabledPlugins` in `settings.json`. Do the migration before proceeding with onboarding.

**Refuse to run from certain locations:**

- If the cwd is inside the aiforging plugin source repo itself (`git remote -v` includes `aiforging` as the repo name, or `.claude-plugin/plugin.json` with `"name": "aiforging"` is in cwd), abort with: "You're inside the AI Forging plugin source repo — this is where the plugin is authored, not where you forge code. Create or `cd` into a separate forge workspace directory (e.g., `mkdir ~/forge && cd ~/forge`) and re-run."
- If the cwd is one of the target repos a user likely works in (heuristic: `git remote -v` names a non-aiforging repo AND `.aiforging/CLAUDE.md` exists), warn: "This looks like a target repo already onboarded to AI Forging, not a forge workspace. The forge workspace is a separate hub directory from which you drive work across repos. Continue here anyway? [y/N]". Default: N.

**Route to phase:**

- All three required markers present → **Phase B (onboard-project)**. (Presence or absence of `settings.local.json` distinguishes Scenario A from B/C but doesn't change the phase.)
- Three markers present but `settings.local.json` missing AND `settings.json` contains `additionalDirectories` → **Phase B with migration preamble** (see Migration note above).
- None or only some required markers present → **Phase A (init-workspace)**. Step 0.5 will determine the scenario before init proceeds.
- Mixed state (some markers missing, some present, and not the migration case) → STOP. Tell the user the workspace is in an inconsistent state, show which markers are missing, and ask whether to re-initialize or abort. Do not silently repair.

---

## PHASE A — init-workspace

Only run these steps if the phase detection in Step 1 routed to Phase A.

### Step A.1 — Check for the superpowers dependency plugin

AI Forging delegates the core TDD, brainstorming, plan-writing, plan-execution, and subagent dispatch skills to the **`superpowers`** plugin ([github.com/obra/superpowers](https://github.com/obra/superpowers), accepted into the official Anthropic marketplace in January 2026). Do not reinvent those skills in AI Forging — install superpowers and reference its skills.

Check whether it's already installed:

```bash
ls ~/.claude/plugins/superpowers 2>/dev/null || \
ls ~/.claude/marketplaces/superpowers-dev 2>/dev/null || \
echo "SUPERPOWERS_NOT_FOUND"
```

If not found, ask the user directly: "Do you already have the `superpowers` plugin installed? [yes / no / not sure]".

**If superpowers is NOT installed**, present the following to the user verbatim:

> AI Forging builds on top of the `superpowers` plugin by Jesse Vincent for its core TDD, brainstorming, and plan-writing/execution skills. I recommend installing it before continuing. To install it now, run these two commands in your Claude Code CLI (not here — they're interactive slash commands):
>
> 1. `/plugin marketplace add obra/superpowers`
> 2. `/plugin install superpowers@superpowers-dev`
>
> Then re-run `/aiforging:setup` from this directory. If you'd rather proceed without superpowers, say so — but be aware that AI Forging assumes the following skills are available and will reference them by name: `superpowers:test-driven-development`, `superpowers:brainstorming`, `superpowers:writing-plans`, `superpowers:executing-plans`, `superpowers:subagent-driven-development`. Without them, the Fire and Hammer stages of the forge will be incomplete.

Wait for the user to choose:
- "installed, continue" → proceed.
- "proceed without it" → proceed and mark in the final summary that superpowers was skipped.
- "install and re-run" → stop. Do not proceed.

Never try to run `/plugin install` yourself — plugin installation is a user-initiated slash command.

### Step A.2 — Seed workspace files

Copy the workspace templates into the cwd, then create the split settings files and a `.gitignore`. None of these files may be overwritten silently. If any target already exists, diff and ask.

```bash
# Workspace CLAUDE.md
cp ${CLAUDE_PLUGIN_ROOT}/templates/workspace-CLAUDE.md ./CLAUDE.md

# Workspace README.md
cp ${CLAUDE_PLUGIN_ROOT}/templates/workspace-README.md ./README.md

# docs/features/ tree with README
mkdir -p ./docs/features
cp ${CLAUDE_PLUGIN_ROOT}/templates/docs-features-README.md ./docs/features/README.md

# .claude/settings.json — COMMITTED, shareable. Starts empty; configure-plugins.py
# fills in the enabledPlugins block in the next step. Never write additionalDirectories here.
mkdir -p ./.claude
cat > ./.claude/settings.json <<'JSON'
{}
JSON

# .claude/settings.local.json — GITIGNORED, per-user. Holds absolute paths to target
# repos. Phase B writes to this file, never to settings.json.
# ONLY CREATE FOR SCENARIO A (multi-repo). Scenarios B/C don't need additionalDirectories
# because the workspace IS the repo — all targets are local sub-directories.
if [ "$SCENARIO" = "multi-repo" ]; then
  cat > ./.claude/settings.local.json <<'JSON'
{
  "permissions": {
    "additionalDirectories": []
  }
}
JSON
fi

# .gitignore — lives at the workspace root. Protects settings.local.json and the
# timestamped backups our helper scripts leave behind. Active immediately if the user
# later git-inits the workspace (Step A.4 or Step B.10).
cat > ./.gitignore <<'GITIGNORE'
# AI Forging workspace — .gitignore
#
# Keep per-user config and helper-script backups out of the shared repo so teammates
# who clone the workspace don't inherit absolute paths from the author's machine.

# Per-user Claude Code settings (absolute paths to target repos live here)
.claude/settings.local.json

# Helper-script backups (configure-plugins.py, configure-directories.py)
.claude/*.bak-*
*.bak-*

# OS cruft
.DS_Store
Thumbs.db
GITIGNORE

# Copy the capture-pattern skill into the workspace so it auto-activates when
# Claude is launched from here. This is the Tempering feedback loop: during any
# session in the workspace (e.g., drafting a plan, reviewing a subagent's output)
# when the human corrects the AI and the correction encodes a reusable rule,
# the skill will offer to persist it as a pattern/anti-pattern. The skill asks
# whether captures should go to the workspace shared tier or a target-local tier.
mkdir -p ./.claude/skills/capture-pattern
cp ${CLAUDE_PLUGIN_ROOT}/skills/capture-pattern/SKILL.md \
   ./.claude/skills/capture-pattern/SKILL.md

# Seed the SHARED TIER of the pattern library at the workspace level.
# These are the framework's starting patterns — they have applies-to frontmatter
# for stack filtering. hammer-refactor reads this directory and filters by target
# stack. Target repos get EMPTY local-tier directories during Phase B onboarding;
# the seeded content lives here at the workspace level (Decision 22 in PLAN.md).
mkdir -p ./.aiforging/patterns ./.aiforging/anti-patterns
cp ${CLAUDE_PLUGIN_ROOT}/conventions/refactoring/patterns/*.md      ./.aiforging/patterns/
cp ${CLAUDE_PLUGIN_ROOT}/conventions/refactoring/anti-patterns/*.md ./.aiforging/anti-patterns/
cp ${CLAUDE_PLUGIN_ROOT}/conventions/refactoring/README.md          ./.aiforging/README.md
```

Then enable the required plugins in the workspace's **committed** settings file so Claude Code automatically activates them when any teammate runs Claude from this directory:

```bash
# Probe for uv; fall back to python3 (see "Helper script runner" section above).
if command -v uv >/dev/null 2>&1; then FORGE_PY="uv run"; else FORGE_PY="python3"; fi

$FORGE_PY ${CLAUDE_PLUGIN_ROOT}/scripts/configure-plugins.py enable \
  --settings-file ./.claude/settings.json \
  --plugin superpowers@claude-plugins-official \
  --plugin aiforging@claude-plugins-official
```

**Ask before you do this** if the user has a different marketplace source for either plugin (e.g., they installed superpowers via `obra/superpowers` and the source identifier is `superpowers-dev`). The defaults assume the official Anthropic marketplace (`claude-plugins-official`), but the user's actual installed marketplace may differ. Ask:

> I'll enable `superpowers` and `aiforging` in this workspace's committed `.claude/settings.json` so they auto-activate when you (or any teammate) run Claude here. I'll use `@claude-plugins-official` as the marketplace source by default. If you have either plugin installed from a different marketplace (e.g., `@superpowers-dev`), tell me now. Otherwise I'll proceed.

Whatever source the user confirms, pass the correct `<name>@<source>` identifier to `configure-plugins.py enable`.

After seeding, show the user the tree that was created — call out explicitly that `settings.json` and `settings.local.json` are DIFFERENT files serving DIFFERENT purposes, and that `.gitignore` will protect the local file once the workspace becomes a git repo. Then confirm before proceeding.

### Step A.2.5 — Register the workspace in the run-anywhere pointer file

Write the new workspace's absolute path into the per-user pointer file at `~/.claude/aiforging.json` so that daily-driver commands like `/aiforging:new-feature` can find it even when the user runs them from outside the workspace. This file is owned by `configure-workspace-pointer.py`. It lives under the user's Claude Code config directory (NOT under `${CLAUDE_PLUGIN_ROOT}` — never write there) and is per-user.

Before calling the helper, tell the user what it does and that it is per-user (not per-workspace, not per-target), and confirm:

> I'll register this workspace at `~/.claude/aiforging.json` so that when you run `/aiforging:new-feature` from any directory — not just this workspace — it can find your active forge workspace automatically. The pointer file lives under your personal Claude config and is never committed to any repo. Proceed? [Y/n]

Default: Y. If the user says no, skip this step and print a reminder that `/aiforging:new-feature` will only work from inside this workspace until the pointer file is populated.

If yes, run:

```bash
$FORGE_PY ${CLAUDE_PLUGIN_ROOT}/scripts/configure-workspace-pointer.py set-active \
  --workspace "$(pwd)"
```

The helper creates `~/.claude/aiforging.json` if it doesn't exist, sets `active_workspace` to the current workspace path, and prepends it to the `workspaces` history list (deduped). A timestamped backup of any pre-existing pointer file is created before the write. Read the JSON output and record `previous_active` and whether `changed_active` was true — if the user had a different active workspace before, mention it in the Phase A summary so they know the run-anywhere target switched.

Rationale for doing this in Phase A: it means a user who bootstraps a workspace and then immediately runs `/aiforging:new-feature` from anywhere — even before onboarding any targets — will hit the newly-created workspace. If the user declines and later realizes they want run-anywhere support, they can always `cd` into the workspace and manually run the helper.

### Step A.2.7 — Monorepo / single-repo sub-project detection (scenario B and C only)

**Skip this step entirely for Scenario A (multiple repos).** Multi-repo workspaces discover targets via Phase B onboarding, not via sub-project detection.

For **Scenario B (monorepo)** and **Scenario C (single repo)**, the workspace IS the repo root. Run `detect-project.py` against the cwd to discover the stack(s) present:

```bash
$FORGE_PY ${CLAUDE_PLUGIN_ROOT}/scripts/detect-project.py "$(pwd)"
```

Parse the JSON output. `detect-project.py` already recurses into child directories for meta-repo detection — the `children` array in the output contains detected sub-projects with their own `stack`, `frameworks`, and `path` fields.

**If `children` is non-empty (monorepo with sub-projects):**

Present the detected sub-projects for confirmation:

> "I detected the following sub-projects in your monorepo:"
>
> 1. `frontend/` — react, next
> 2. `backend/` — symfony-php, doctrine
> 3. `packages/shared/` — node-ts
>
> "Which of these should I onboard with AI Forging conventions? [all / pick by number / none]"

Default: all. For each confirmed sub-project, record it as a target. These targets will be onboarded inline — Phase A continues into a streamlined Phase B loop for each sub-project (no `additionalDirectories` needed since everything is under one root).

**If `children` is empty (single project at root — Scenario C, or a monorepo whose structure wasn't auto-detected):**

The repo root itself is the single target. Confirm with the user:

> "This looks like a single `<detected-stack>` project. I'll install AI Forging conventions at the repo root. OK? [Y/n]"

If yes, record the repo root as the single target. If no, ask the user to point out sub-project directories manually:

> "Tell me the paths to the sub-projects you'd like to onboard (relative to the repo root), separated by commas."

Run `detect-project.py` against each path and proceed.

**For both monorepo and single-repo scenarios, skip `settings.local.json` creation.** There are no `additionalDirectories` to register — the workspace IS the repo, and all targets are subdirectories (or the root itself). The `.claude/settings.local.json` file is only needed for Scenario A (multi-repo) where targets live at external absolute paths.

After this step, the detected/confirmed targets are held in memory for inline onboarding. For Scenario B/C, Step A.3 changes behavior — instead of asking "onboard your first target?", it proceeds directly to inline onboarding of the confirmed sub-projects (see Step A.3).

### Step A.3 — Offer to onboard the first target project

**Scenario A (multi-repo):**

Ask: **"Would you like to onboard your first target project now? [Y/n]"**. Default: Y.

If yes, route directly to **Phase B** (the rest of this document). The workspace is now initialized and counts as a workspace from here on. The git integration subroutine will run at the end of Phase B (Step B.10) with the benefit of target repo metadata for remote inference.

If no, proceed to **Step A.4** (git integration without target info) and then **Step A.5** (Phase A summary).

**Scenario B/C (monorepo or single repo):**

Step A.2.7 already detected and confirmed the sub-project targets. Do NOT ask whether to onboard — proceed directly to inline onboarding. For each confirmed target (sub-project path or repo root), run Phase B Steps B.2 through B.7 against it, with these adjustments:

- **Skip Step B.1** (project path prompt) — the path is already known from Step A.2.7.
- **Skip Step B.3** (register in `settings.local.json`) — monorepo/single-repo targets don't use `additionalDirectories`.
- **Skip Step B.10** (git integration) per-target — run it ONCE after all sub-projects are onboarded, back in Step A.4.
- **Skip Step B.10.5** (workspace pointer refresh) — already done in Step A.2.5.

If multiple sub-projects were confirmed, onboard them sequentially. After all targets are onboarded, proceed to **Step A.4** for git integration (the workspace IS the repo, so `git rev-parse` will likely show it's already a git repo — Step A.4 handles this gracefully).

### Step A.4 — Git integration (onboard-declined path)

This step runs only if the user declined onboarding in Step A.3. Its purpose is to offer git-init for a workspace that has no target repos yet. Without target repos, we cannot infer a remote destination from `.git/config` — so the remote suggestion is generic. The physical-location sanity check and initial commit still apply.

**Skip this step entirely** if any of the following are true:

- `git rev-parse --is-inside-work-tree` returns true inside the workspace cwd. (Already a git repo.)
- The workspace cwd is inside a parent git repo (e.g., `~/dotfiles/forge`). Warn the user about the nesting and ask whether to init a nested repo or leave it tracked by the parent. Default: leave tracked by the parent. If the user chooses nested, proceed with git-init below.

**Otherwise, run the git integration subroutine** (see "Git integration subroutine" section at the bottom of this document) with the `target_context=[]` variant. Pass no target paths — inference is skipped, and the remote suggestion is a generic placeholder.

After the subroutine returns (either "initialized", "deferred", or "declined"), continue to Step A.5.

### Step A.5 — Phase A summary

**Scenario A (multi-repo) — onboarding declined:**

```
AI Forging workspace initialized at: <abs path>
Scenario: multi-repo (separate workspace)

Files created:
  ./CLAUDE.md                                      ← workspace context for Claude
  ./README.md                                      ← human-readable workspace overview
  ./docs/features/README.md                        ← feature-folder convention
  ./.claude/settings.json                          ← committed: enabledPlugins only
  ./.claude/settings.local.json                    ← gitignored: additionalDirectories (empty)
  ./.claude/skills/capture-pattern/SKILL.md        ← Tempering feedback loop
  ./.aiforging/patterns/                           ← shared-tier seeded patterns
  ./.aiforging/anti-patterns/                      ← shared-tier seeded anti-patterns
  ./.gitignore                                     ← protects settings.local.json + backups

Dependencies:
  superpowers plugin: <installed | skipped | missing>
  aiforging plugin:   enabled in .claude/settings.json

Run-anywhere pointer:
  <one of: "registered as active in ~/.claude/aiforging.json" |
           "declined — /aiforging:new-feature will only work from inside this workspace" |
           "previous active was <path> — switched to this workspace">

Git:
  <one of: "initialized with initial commit <hash>" | "deferred — re-run setup or git init manually"
   | "already a git repo — no changes" | "nested inside <parent-repo>, left untracked here">

Next:
  1. Re-run /aiforging:setup in this directory to onboard a target project.
  2. Or start a feature: /aiforging:new-feature <name> <prompt>
```

**Scenario B/C (monorepo / single repo) — inline onboarding completed:**

```
AI Forging workspace initialized at: <abs path>
Scenario: <monorepo | single-repo>

Workspace files:
  ./CLAUDE.md                                      ← workspace context for Claude
  ./README.md                                      ← human-readable workspace overview
  ./docs/features/README.md                        ← feature-folder convention
  ./.claude/settings.json                          ← committed: enabledPlugins only
  ./.claude/skills/capture-pattern/SKILL.md        ← Tempering feedback loop
  ./.claude/skills/hammer-refactor/SKILL.md        ← executable Hammer stage
  ./.aiforging/patterns/                           ← shared-tier seeded patterns
  ./.aiforging/anti-patterns/                      ← shared-tier seeded anti-patterns
  ./.gitignore                                     ← protects settings.local.json + backups

Onboarded targets:
  <target-1-path>/  (<stack>) — conventions installed, ANALYSIS.md written
  <target-2-path>/  (<stack>) — conventions installed, ANALYSIS.md written
  ...

Dependencies:
  superpowers plugin: <installed | skipped | missing>
  aiforging plugin:   enabled in .claude/settings.json

Git:
  <already a git repo — onboarding changes staged / committed>

Next:
  Start a feature: /aiforging:new-feature <name> <prompt>
```

Note: For Scenario B/C, `settings.local.json` is NOT created — the workspace IS the repo and all targets are local sub-directories (or the root itself). No `additionalDirectories` needed.

Then STOP.

- **Scenario A, "yes, onboard now":** Continue to Phase B. (Step A.4 is skipped; git integration runs as Step B.10 instead, so there's exactly one git integration opportunity per setup run.)
- **Scenario B/C:** Inline onboarding already happened during Step A.3. Phase A is done. STOP here.

---

## PHASE B — onboard-project

Only run these steps if phase detection routed here, OR if Phase A's Step A.3 routed here.

> **Scenario-dependent entry points.** Phase B can be reached three ways:
>
> - **Scenario A (multi-repo):** Reached from Phase A Step A.3 ("yes, onboard now") or from a re-run of `/aiforging:setup` in an existing workspace. All steps run as documented.
> - **Scenario B/C (monorepo / single repo) inline onboarding:** Reached from Phase A Step A.3's inline loop. Steps B.1 (path prompt), B.8 (`settings.local.json` registration), and B.9 (workspace pointer) are SKIPPED — the target path comes from Step A.2.7 detection, and there's no `additionalDirectories` to manage.
> - **Re-run in existing workspace:** Phase detection routes directly to Phase B. The scenario is inferred from the workspace state (presence/absence of `settings.local.json`).

> **The onboarding checklist.** Phase B performs up to six things for each target being onboarded. Every item is offered with a default; the user can decline any of them individually. This list is what to keep in mind as the phase walks:
>
> 1. **Register** the target in the workspace's `.claude/settings.local.json` under `permissions.additionalDirectories` (the gitignored per-user settings file — never in the committed `.claude/settings.json`). **(Scenario A only — skipped for monorepo/single-repo where the workspace IS the repo.)**
> 2. **Superpowers prerequisite check.** Verify superpowers is installed at the user level (user is running Claude Code on a machine that has it). If not, recommend installing. This step does NOT install anything into the target repo — superpowers is a user-level plugin. But its presence is recorded in the target's `.aiforging/CLAUDE.md` as a documented prerequisite so future contributors know.
> 3. **Conventions library** → copy `conventions/architecture/` and `conventions/tdd/` into `<target>/.aiforging/`. Also write a per-repo `.aiforging/CLAUDE.md` pointer. (Backend/fullstack only.) For monorepo sub-projects, `<target>` is the sub-project path (e.g., `./backend/`), not the repo root.
> 4. **AI Forging skills bundle** → copy `hammer-refactor` SKILL.md to `<target>/.claude/skills/hammer-refactor/SKILL.md` (executable Hammer stage) and `capture-pattern` SKILL.md to `<target>/.claude/skills/capture-pattern/SKILL.md` (reactive Tempering feedback loop). (Backend/fullstack only; offered as a bundle with default Y, with a fallback to per-skill offers if the bundle is declined.) For monorepo sub-projects, skills install at the REPO ROOT's `.claude/skills/` (not per sub-project) since Claude Code reads skills from the cwd's `.claude/skills/`.
> 5. **Pattern + anti-pattern library seed** → create EMPTY `<target>/.aiforging/patterns/` and `<target>/.aiforging/anti-patterns/` directories for the target-local tier. Seeded patterns live in the workspace shared tier (`.aiforging/patterns/` at the workspace root), installed during Phase A Step A.2. (Backend/fullstack only; offered with default Y if hammer-refactor was installed.) If the workspace shared tier is empty (e.g., a cloned workspace where shared patterns weren't committed), fall back to copying seeded patterns into the target-local tier.
> 6. **Architecture analyzer run** → invoke the `architecture-analyzer` skill against the target, write output to `<target>/.aiforging/ANALYSIS.md`. (Backend/fullstack only.)
> 7. **Frontend testing layer** (optional) → for frontend/fullstack, offer the Playwright conventions.
> 8. **Draft a feature folder in the workspace** (optional) → turn analyzer findings into `<workspace>/docs/features/<name>/spec.md` + `plan.md` in the AI Forging slice format.
>
> At the end of Phase B, the summary (Step B.11) should report which items of this checklist were completed, skipped, or declined.

### Step B.1 — Detect candidate target projects

Ask the user: **"What's the absolute path of the target project you want to onboard?"**

Run the stack detector against that path:

```bash
# Probe for uv; fall back to python3 (see "Helper script runner" section above).
if command -v uv >/dev/null 2>&1; then FORGE_PY="uv run"; else FORGE_PY="python3"; fi

$FORGE_PY ${CLAUDE_PLUGIN_ROOT}/scripts/detect-project.py <abs-path>
```

Parse the JSON output. If `kind` is `meta`, present the children and ask which child to onboard (one at a time; onboarding is per-project, not per-meta-repo).

Present what detection found:

- Absolute path
- Detected `kind` (backend / frontend / fullstack / meta / unknown)
- Detected backend stack + ORM + test runner (if any)
- Detected frontend stack + language + test runner (if any)
- Evidence files

### Step B.2 — Confirm role

If the detected `kind` is ambiguous or `unknown`, ask: **"Is this a backend project, a frontend project, or a fullstack project?"** Record the answer as `role`.

Keep the project in your working memory as:

```json
{
  "path": "/Users/.../project-a-api",
  "role": "backend",
  "stack": "symfony-php",
  "orm": "doctrine",
  "test_runner": "phpunit"
}
```

### Step B.3 — Register under additionalDirectories (in settings.local.json)

**Skip this step for Scenario B/C (monorepo / single repo).** There are no external paths to register — the workspace IS the repo and all targets are local sub-directories.

**Scenario A (multi-repo) only:** Add the target project to the current workspace's **per-user** settings file, `./.claude/settings.local.json`. This is the gitignored file — absolute local paths never go into the committed `settings.json`.

```bash
# Probe for uv; fall back to python3 (see "Helper script runner" section above).
if command -v uv >/dev/null 2>&1; then FORGE_PY="uv run"; else FORGE_PY="python3"; fi

$FORGE_PY ${CLAUDE_PLUGIN_ROOT}/scripts/configure-directories.py add \
  --settings-file ./.claude/settings.local.json \
  --directory "<abs-path-to-target>"
```

Show the resulting JSON output. The helper is idempotent — re-adding an existing path is a no-op.

If the user wants to use a different scope (user-level settings at `~/.claude/settings.json`), ask before defaulting to the workspace-local file. The default is always the workspace's `./.claude/settings.local.json` because (a) the workspace is the intended runtime context for cross-repo forging, and (b) the workspace-local scope keeps per-user paths out of the shared repo.

**Sanity check the file you're targeting.** If `./.claude/settings.local.json` doesn't exist for some reason (e.g., the workspace predates the settings split and was not migrated at Step 1), create it with an empty `{"permissions": {"additionalDirectories": []}}` stub BEFORE calling the helper. The helper will read-or-create the file, but having an explicit stub makes the intent obvious in the file history.

**Do not write `additionalDirectories` into `./.claude/settings.json`.** If you find yourself about to do that, stop — it's a bug. That file is for `enabledPlugins` only.

### Step B.3.5 — Enable plugins in the target repo's settings.json

Claude Code plugins are installed once at the *user level*, but which plugins are actually *active* in a given scope (a project's `.claude/settings.json`, for example) is controlled by the `enabledPlugins` map in that scope's settings. This means we can commit the expectation into the target repo's `.claude/settings.json` so teammates cloning the repo get superpowers and aiforging auto-enabled when they run Claude Code there — regardless of their personal defaults. This is AI Forging's equivalent of a `peerDependencies` declaration.

**First, verify superpowers is installed at the user level.** If Phase A was run in this same session, you already performed this check and can reuse the result. If Phase B was invoked directly in a pre-existing workspace, ask the user: "Do you already have the `superpowers` plugin installed in Claude Code? [yes / no / not sure]".

**If superpowers is NOT installed**, present the following:

> AI Forging expects the `superpowers` plugin to be installed at the user level — it provides the TDD, brainstorming, writing-plans, executing-plans, and subagent-driven-development skills that AI Forging's conventions and the `hammer-refactor` skill depend on. Plugins in Claude Code are installed once per machine, so installing it once covers this target project and every other onboarded project.
>
> To install it, run in your Claude Code CLI:
>
> 1. `/plugin marketplace add anthropics/claude-plugins-official` (or whichever marketplace hosts your copy — `obra/superpowers` also works).
> 2. `/plugin install superpowers@claude-plugins-official` (or `superpowers@superpowers-dev` if you used the obra marketplace).
>
> I'll continue onboarding this target project either way, and I'll still write the `enabledPlugins` block into the target's `.claude/settings.json` so the expectation is committed to the repo. But your Fire and Hammer stages will be incomplete until superpowers is actually installed at the user level.

Record whether superpowers was found, missing, or skipped for the final summary.

**Then write the `enabledPlugins` block into the target repo's `.claude/settings.json`** using the helper. This creates the file if it doesn't already exist, and merges with any existing keys if it does:

```bash
# Probe for uv; fall back to python3 (see "Helper script runner" section above).
if command -v uv >/dev/null 2>&1; then FORGE_PY="uv run"; else FORGE_PY="python3"; fi

$FORGE_PY ${CLAUDE_PLUGIN_ROOT}/scripts/configure-plugins.py enable \
  --settings-file <target>/.claude/settings.json \
  --plugin superpowers@claude-plugins-official \
  --plugin aiforging@claude-plugins-official
```

**Ask before running** if the user's plugin marketplace sources differ from the defaults. Same prompt as in Phase A Step A.2:

> I'll write an `enabledPlugins` block into `<target>/.claude/settings.json` that enables `superpowers` and `aiforging` with `@claude-plugins-official` as the marketplace source. If you have either plugin installed from a different marketplace (e.g., `superpowers@superpowers-dev` from `obra/superpowers`), tell me now so I can use the correct identifier. Otherwise I'll proceed.

Check whether `<target>/.claude/settings.json` already exists before calling the helper. If it does:

1. Show the user the current contents.
2. Explain that the helper will ADD the `enabledPlugins` entries without touching any other keys, and will create a timestamped `.bak-<ts>` backup before writing.
3. Ask for confirmation before calling the helper.

If it doesn't exist, the helper will create it cleanly. No confirmation needed beyond the marketplace-source confirmation above.

Show the resulting JSON output. After this step, a teammate who clones the target repo and runs `claude` in it will have superpowers and aiforging automatically enabled, without needing to configure anything personal.

### Step B.4 — Copy conventions into the target repo's `.aiforging/`

For projects with `role` in (`backend`, `fullstack`):

1. Check whether `<target>/.aiforging/` already exists.
   - If it does, diff the existing contents against `${CLAUDE_PLUGIN_ROOT}/conventions/` and present the diff. Ask before overwriting. Never overwrite silently.
   - If it doesn't, create it and copy:
     - `${CLAUDE_PLUGIN_ROOT}/conventions/architecture/` → `<target>/.aiforging/architecture/`
     - `${CLAUDE_PLUGIN_ROOT}/conventions/tdd/` → `<target>/.aiforging/tdd/`
     - `${CLAUDE_PLUGIN_ROOT}/conventions/subagent-orchestration/` → `<target>/.aiforging/subagent-orchestration/`
     - Do NOT copy `conventions/features/` into the target — that convention belongs in the workspace, not in a target repo.
2. Write `<target>/.aiforging/CLAUDE.md` from `${CLAUDE_PLUGIN_ROOT}/conventions/CLAUDE.md.template`.
3. Check whether `<target>/CLAUDE.md` exists at the target repo root.
   - If it does, append (don't overwrite) a section pointing at `.aiforging/`.
   - If it doesn't, create it with just that section.

For projects with `role` == `frontend`: skip this step. Frontend conventions install happens in Step B.8.

### Step B.5 — Offer to install the AI Forging skills into the target repo

For projects with `role` in (`backend`, `fullstack`), offer to install **two** skills inside the target repo, both committed alongside the code so teammates cloning the repo can use them without needing the aiforging plugin installed on their machine:

> I'd like to install two AI Forging skills into this target repo at `<target>/.claude/skills/`. Both are backend/fullstack-only and together they implement the Hammer and Tempering stages of the forge:
>
> 1. **`hammer-refactor`** (the executable Hammer stage). Scans the target's changed files against the pattern/anti-pattern library in `.aiforging/patterns/` and `.aiforging/anti-patterns/`, dispatching one fresh-context subagent per file via `superpowers:subagent-driven-development`. Adding the 50th pattern costs no more than the 5th because each gets its own subagent.
>
> 2. **`capture-pattern`** (the Tempering feedback loop). Reactive skill that watches for corrective moments during interactive sessions — when you reject a diff, correct a structural choice, or say "that's not how we do it," the skill offers to persist the lesson as a new file under `.aiforging/patterns/` or `.aiforging/anti-patterns/`. The next Hammer pass automatically includes the captured pattern. This is how the library grows: one code review, one `.md` file.
>
> Both skills are discoverable by anyone cloning this target repo, independent of whether the aiforging plugin is installed on their machine. This is deliberate — it matches AI Forging's `peerDependencies` model.
>
> Install both skills into `<target>`? [Y/n]

Default: **Y** for backend/fullstack projects. If the user declines the bundle, offer each skill separately (defaults Y each) — these are the core Hammer and Tempering mechanisms and declining both effectively opts out of the framework's backend value.

If yes:

```bash
# hammer-refactor — executable Hammer stage
mkdir -p <target>/.claude/skills/hammer-refactor
cp ${CLAUDE_PLUGIN_ROOT}/skills/hammer-refactor/SKILL.md \
   <target>/.claude/skills/hammer-refactor/SKILL.md

# capture-pattern — Tempering feedback loop
mkdir -p <target>/.claude/skills/capture-pattern
cp ${CLAUDE_PLUGIN_ROOT}/skills/capture-pattern/SKILL.md \
   <target>/.claude/skills/capture-pattern/SKILL.md
```

**Overwrite safety.** If either skill's `SKILL.md` already exists in the target (from a previous onboarding or a manual copy), diff the current plugin version against the target copy and ask before overwriting. Show the diff. Never overwrite silently — the user may have customized the local copy. If they did customize, offer to back up their version to `SKILL.md.bak-<ts>` before copying the fresh version on top.

**Why capture-pattern lives in both the workspace and each target repo.** Phase A Step A.2 already installed `capture-pattern` into the forge workspace's `.claude/skills/` so it auto-activates in cross-repo forge sessions (where it resolves the target to write to by reading `settings.local.json`). Installing it a second time in each target repo gives teammates who clone *just the target repo* the same feedback loop when they're working on the target directly in that repo (e.g., doing a code review outside the forge workspace). The two copies are identical — the per-target copy is there for discoverability, not for a different behavior.

### Step B.6 — Create empty target-local pattern directories

Create the **target-local tier** directories in the target repo. These start empty — they're for repo-specific pattern captures that only apply to this target. The seeded patterns (shipped with the plugin) already live in the **workspace shared tier** (seeded in Phase A Step A.2). The `hammer-refactor` skill merges both tiers on every run.

```bash
mkdir -p <target>/.aiforging/patterns <target>/.aiforging/anti-patterns
```

If this is the first onboarding AND the workspace shared tier hasn't been seeded yet (e.g., the workspace was created by an older version of the plugin that predates the two-tier model), seed it now:

```bash
# Only if <workspace>/.aiforging/patterns/ doesn't exist or is empty
if [ ! -d ./.aiforging/patterns ] || [ -z "$(ls -A ./.aiforging/patterns/ 2>/dev/null)" ]; then
  mkdir -p ./.aiforging/patterns ./.aiforging/anti-patterns
  cp ${CLAUDE_PLUGIN_ROOT}/conventions/refactoring/patterns/*.md      ./.aiforging/patterns/
  cp ${CLAUDE_PLUGIN_ROOT}/conventions/refactoring/anti-patterns/*.md ./.aiforging/anti-patterns/
  cp ${CLAUDE_PLUGIN_ROOT}/conventions/refactoring/README.md          ./.aiforging/README.md
fi
```

Tell the user:

> Created empty `patterns/` and `anti-patterns/` directories in `<target>/.aiforging/` for repo-specific pattern captures. The framework's seeded patterns (fat-controller, primitive-obsession, extract-service-from-controller) live in the workspace's shared tier at `<workspace>/.aiforging/` and apply to all targets with matching stacks. Use `capture-pattern` during code reviews to add new patterns — it'll ask whether each capture should be shared or target-local.

### Step B.7 — Run the architecture-analyzer skill on the target

For projects with `role` in (`backend`, `fullstack`), invoke the `architecture-analyzer` skill (from `${CLAUDE_PLUGIN_ROOT}/skills/architecture-analyzer/`) against the target. The skill produces a structured report covering:

- Folder-layout alignment with Domain-centric namespacing
- Single-Action Controller shape
- Repository boundaries (Data Mapper vs Active Record smell)
- Test harness capability contract
- DTO / Value Object discipline
- Pattern/anti-pattern library presence

Save the skill's output to `<target>/.aiforging/ANALYSIS.md`. Summarize the top findings to the user inline.

### Step B.8 — Optional frontend testing layer

For projects with `role` in (`frontend`, `fullstack`), ask ONCE:

> AI Forging ships an optional Playwright-oriented frontend testing convention. The core framework doesn't require it — tests are still a backend concern — but Playwright is useful for catching contract regressions between frontend and backend. Install it for this project? [y/N]

Default: **N**. If yes:

```bash
mkdir -p <target>/.aiforging/frontend-testing
cp -r ${CLAUDE_PLUGIN_ROOT}/conventions/frontend-testing/* <target>/.aiforging/frontend-testing/
```

Update the target's `CLAUDE.md` with a pointer.

### Step B.9 — Propose a refactor plan (centrally, in the workspace)

If the architecture analyzer produced findings, offer to create a feature folder for the alignment work. This step is an **auto-invoked specialization** of the `/aiforging:new-feature` command — both commands follow the same shape rules and Step-1 Summary format documented in `${CLAUDE_PLUGIN_ROOT}/conventions/features/README.md`. Do not improvise new rules here. If this step and `/aiforging:new-feature` ever disagree, the convention doc is the source of truth and both commands must align to it.

The differences between this step and the user-invoked `/aiforging:new-feature` are:

- The initial prompt is pre-supplied — it's the architecture-alignment work proposed by the analyzer for `<target>`, not a free-form user prompt.
- This step DOES write a `plan.md` draft (not just a spec.md skeleton), because the analyzer findings are already structured enough to feed the slice format directly. This is the one case where a plan.md can exist before the user has run the full interactive Step 2–3 interview.
- This step is auto-invoked by onboarding; the user never has to type the command name.

Offer the feature creation:

> Based on the analysis of `<target>`, I can draft a proposed refactor plan as a new feature in this workspace. The feature would live at `docs/features/<suggested-name>/` and would contain a spec.md (what the plan addresses) and a plan.md (the sliced refactor path in the AI Forging slice format). This is where all cross-cutting plans live — centralized in the workspace, not fragmented per repo.
>
> Create `docs/features/<suggested-name>/` and draft the proposed plan there? [Y/n]

Default: Y. Suggested name: `<target-repo-basename>-architecture-alignment` in kebab-case.

If yes:

1. **Read the convention.** Load `${CLAUDE_PLUGIN_ROOT}/conventions/features/README.md` so the feature-folder shape rules and the Summary-section format are in your context. Do not paraphrase the convention to the user.
2. **Feature detection.** Check `./docs/features/` for an existing folder that collides with `<suggested-name>` (exact match, substring, or >=50% token overlap). If one exists, append `-2`, `-3`, … to disambiguate until the name is unique. Feature folders are stable-once-created — never rename an existing one.
3. **Pick the shape.** Architecture-alignment features from the analyzer are typically flat (one spec, one plan) because the analyzer produces one unified set of findings for one target repo. Use the flat shape unless the analyzer findings span obviously-independent work items (e.g., a backend-layer refactor group AND a frontend-layer refactor group in a fullstack repo) — in that case, use the nested shape with one numbered work item per group.
4. **Create the folder.**
   ```bash
   mkdir -p ./docs/features/<suggested-name>
   ```
5. **Write spec.md** following the Step-1 Summary format from `conventions/features/README.md`. The Summary section should be pre-filled with: "Architecture alignment work proposed by `architecture-analyzer` for `<target>` on `<today's date>`. Findings summary: `<one-paragraph condensation of the analyzer output>`." The rest of the spec (Problem, Who is affected, In scope / out of scope, Affected code, Architectural decisions) should be filled in from the analyzer's findings — this is safe because the analyzer already did the analysis work. Mark the spec as "proposed" in a header comment so reviewers know it came from an automated analysis rather than a human interview.
6. **Write plan.md** in the AI Forging slice format (see `conventions/features/README.md`), breaking the alignment work into `[hammer]` slices. Each slice must name the target repo, the affected file, the pattern/anti-pattern reference, and the test suite that must stay green. Mark any slice touching a public API, schema, or cross-repo contract as `[gate: architecture]` (or a more specific gate: `[gate: schema]`, `[gate: contract]`). Remember: every group of related refactor slices counts as a Fire sequence for convention purposes, so each group ends with its own closing `[hammer]` slice dispatching hammer-refactor against the files the group touched. (For pure-refactor features the "Fire sequence" is often just the analyzer findings for one subsystem; close each subsystem's slices with a hammer-refactor dispatch.)
7. **Stop.** Do NOT execute the plan. Do NOT commit to git — Step B.10 handles git integration for the whole onboarding. The user reviews the spec and plan, and optionally runs `aiforging:hammer-refactor` on the target repo when ready.
8. **Remind the user about the Summary checkpoint.** Even though the spec was drafted from analyzer output rather than an interactive interview, the Summary section is still a checkpoint — ask the user to confirm that the drafted Summary captures the alignment work they actually want, before they approve the plan. If the user wants to rewrite the Summary or scope it down, accept that edit and regenerate the plan section accordingly.

If no, skip this step. Do not create an empty feature folder "just in case."

### Step B.10 — Git integration

This step runs at the end of Phase B so the workspace's `docs/features/<feature>/` drafts and the updated `settings.local.json` are captured in git history. Behavior branches on whether the workspace is already a git repo.

**Branch 1 — workspace is NOT yet a git repo.** Run the git integration subroutine (see "Git integration subroutine" section at the bottom of this document) with `target_context=[<abs path of the target just onboarded, plus any other targets already in settings.local.json>]`. Pass the full list so remote inference can scan every target's `.git/config` for a shared org or hostname. The subroutine will:

1. Check for parent-repo nesting and warn if present.
2. Propose a physical-location sanity check using the common ancestor of the target repos (if any), without moving anything.
3. Scan each target's `.git/config` `[remote "origin"]` URL and suggest a remote destination that matches the shared org or host (without creating or pushing).
4. Write an initial commit with the full workspace state: `CLAUDE.md`, `README.md`, `.gitignore`, `docs/features/*`, and `.claude/settings.json` (but NOT `settings.local.json`, which is gitignored).
5. Return one of: "initialized with initial commit <hash>", "deferred", "declined".

**Branch 2 — workspace IS already a git repo.** Do NOT re-init. Instead, offer to capture the onboarding as a follow-up commit:

> This workspace is already a git repo. I can stage the changes from onboarding `<target>` and commit them now so the onboarding is captured as its own history entry. The commit would include the updated `docs/features/<feature>/` (if you created one) and any changes to `.gitignore` or `.claude/settings.json` — but NOT `.claude/settings.local.json`, which is gitignored and stays local to your machine.
>
> Suggested message: `Onboard <target-basename> to forge workspace`
>
> Commit now? [Y/n]

Default: Y. If yes:

```bash
git -C <workspace> add -A
git -C <workspace> status --short
git -C <workspace> commit -m "Onboard <target-basename> to forge workspace"
```

Show the user the commit hash and the short-status summary before the commit. If the user declines, leave the changes staged? No — leave them unstaged so the user's own `git add` patterns work normally. Just print "Onboarding changes left uncommitted in the working tree. You can commit them manually when ready."

Record the git state (initialized / follow-up commit / declined / not applicable) for the Step B.11 summary.

### Step B.10.5 — Refresh the run-anywhere pointer file

Phase B runs are the signal that the current workspace is the user's most-recently-used forge workspace — they just onboarded a target into it. Set this workspace as the active run-anywhere target so that `/aiforging:new-feature` (and future daily-driver commands) invoked from outside the workspace land in the right place.

This step is idempotent with Step A.2.5: if Phase A routed directly into Phase B (user said "yes, onboard now" at Step A.3), Phase A already set this workspace as active in the pointer file, and this step is a no-op. If Phase B was invoked directly (user re-ran `/aiforging:setup` from an already-initialized workspace to onboard another target), this step updates the pointer file to reflect "the workspace you're running Phase B in is the newly-current active one." Either way, the end state is correct.

Before calling the helper, check whether the pointer file already points at this workspace — if it does and Phase B was invoked directly (not routed from Phase A), skip silently. If it points somewhere else, tell the user you're switching:

```bash
CURRENT_ACTIVE=$($FORGE_PY ${CLAUDE_PLUGIN_ROOT}/scripts/configure-workspace-pointer.py check \
  | python3 -c "import json,sys; print(json.load(sys.stdin).get('active_workspace') or '')")
```

If `CURRENT_ACTIVE` already equals `$(pwd)`, print:

> Run-anywhere pointer already points at this workspace. No change.

and skip the write.

Otherwise, confirm with the user:

> I'd like to set `~/.claude/aiforging.json` to make this workspace the active run-anywhere target (previously: `<CURRENT_ACTIVE>` or `(none)`). That way, `/aiforging:new-feature` invoked from any directory will target this workspace. Proceed? [Y/n]

Default: Y. If yes:

```bash
$FORGE_PY ${CLAUDE_PLUGIN_ROOT}/scripts/configure-workspace-pointer.py set-active \
  --workspace "$(pwd)"
```

Record the pointer state for the Step B.11 summary: "set as active" / "already active — unchanged" / "declined by user".

If no, skip silently and record "declined" for the summary. The previous active workspace, if any, remains the run-anywhere target.

### Step B.11 — Phase B summary

Report back to the user in this exact format. Every line of the checklist must be present — use `✓` (done), `—` (declined by user), or `✗` (skipped because not eligible or missing prerequisite). This makes it easy to spot any item that got skipped.

```
AI Forging onboarding complete.

Workspace:            <abs path to forge workspace>
Target project:       <abs path to target>
Role:                 <backend | frontend | fullstack>
Stack:                <stack>
ORM:                  <orm or none>

Onboarding checklist:
  ✓  1. Registered in <workspace>/.claude/settings.local.json (additionalDirectories)
  ✓  2. Superpowers prerequisite: <installed | missing | skipped>
  ✓  2a. enabledPlugins written to <target>/.claude/settings.json
  ✓  3. Conventions library copied to <target>/.aiforging/
  ✓  4a. hammer-refactor skill installed at <target>/.claude/skills/hammer-refactor/
  ✓  4b. capture-pattern skill installed at <target>/.claude/skills/capture-pattern/
  ✓  5. Pattern + anti-pattern library seeded (<N> patterns, <M> anti-patterns)
  ✓  6. architecture-analyzer run → <target>/.aiforging/ANALYSIS.md (score: X/10)
  —  7. Frontend testing layer (declined / not applicable)
  ✓  8. Feature folder drafted at <workspace>/docs/features/<feature>/
  ✓  9. Run-anywhere pointer: <set as active in ~/.claude/aiforging.json |
                                already active — unchanged |
                                declined — previous active remains>
  ✓ 10. Git: <initialized with initial commit <hash> |
                 follow-up commit <hash> onto existing repo |
                 already a repo — no changes staged |
                 declined | nested — left tracked by parent repo>

Next:
  1. Review the drafted feature spec and plan at
     <workspace>/docs/features/<feature>/.
  2. Adjust as needed (Claude can help).
  3. When ready, run the hammer-refactor skill against the target repo to begin
     executing [hammer] slices. Fire slices (if any) go through
     superpowers:executing-plans first.
  4. Re-run /aiforging:setup from this workspace to onboard another target repo.
  5. If you initialized a git repo and want to push it, create the remote repo
     at your preferred destination (GitHub, Bitbucket, etc.) and run:
         git remote add origin <suggested-url>
         git push -u origin main
     (suggested-url was printed during Step B.10; it's a suggestion, not a
     commitment — rename the remote and URL however you like).
```

If superpowers was missing or skipped, add a trailing note:

```
⚠  Superpowers is not installed on this machine. AI Forging's Fire and Hammer
   stages assume these skills are available:
       superpowers:test-driven-development
       superpowers:brainstorming
       superpowers:writing-plans
       superpowers:executing-plans
       superpowers:subagent-driven-development
   Install with:
       /plugin marketplace add obra/superpowers
       /plugin install superpowers@superpowers-dev
   (Or /plugin install superpowers@claude-plugins-official if you installed
    from the official Anthropic marketplace.)
```

Then STOP.

---

## Git integration subroutine

Called from **Step A.4** (workspace standalone, no target context) and **Step B.10** (workspace with at least one target in `settings.local.json`). Both call sites reuse this same logic; only the `target_context` input differs.

**Inputs:**

- `workspace_path` — absolute path to the forge workspace cwd.
- `target_context` — list of absolute paths to target repos registered in `settings.local.json`. Empty list in Step A.4, non-empty in Step B.10.

**Outputs (record for the caller's summary):**

- `git_state` — one of: `"initialized"`, `"initialized-nested"`, `"deferred"`, `"declined"`, `"already-a-repo"`, `"already-a-repo-committed"`, `"already-a-repo-declined"`.
- `initial_commit_hash` — short SHA if a commit was made; empty otherwise.
- `suggested_remote_url` — remote URL we suggested (for the caller to echo in Step A.5 or Step B.11); empty if inference found nothing.
- `physical_location_note` — short note about whether the workspace location is sensible vs. the target repos' common ancestor; empty if no targets.

### Subroutine step 1 — Is this already a git repo?

```bash
git -C <workspace_path> rev-parse --is-inside-work-tree 2>/dev/null
```

- If the command returns `true` AND the `.git` directory is inside `workspace_path` itself → `already_a_repo = true`.
- If the command returns `true` but `.git` is in a parent directory → `nested_in_parent = true`, along with the parent path from `git -C <workspace_path> rev-parse --show-toplevel`.
- If the command errors → not a git repo, proceed to subroutine step 2.

**Handling `already_a_repo = true`:** return early with `git_state = "already-a-repo"` (or proceed to Step B.10 Branch 2's follow-up commit logic if the caller is Step B.10). Step A.4 never modifies an existing git repo.

**Handling `nested_in_parent = true`:** warn the user:

> The workspace at `<workspace_path>` is inside an existing git repo at `<parent_toplevel>`. I can either (a) initialize a nested repo here (which git supports but most teams find confusing), or (b) leave the workspace tracked by the parent repo. Which do you prefer? [nested / parent / skip]

- `parent` → return `git_state = "initialized-nested"` with a note that nothing was changed, the workspace is tracked by the parent repo. Done.
- `nested` → proceed to subroutine step 2 but init the repo at `workspace_path` (the nested init); record `git_state = "initialized-nested"` on success.
- `skip` → return `git_state = "declined"`.

### Subroutine step 2 — Physical-location sanity check (advisory only, never a move)

Skip this step if `target_context` is empty.

Compute the common ancestor of every path in `target_context` (the longest shared prefix directory). Example: if targets are `/Users/chris/projects/hub-plus-api` and `/Users/chris/projects/certainpath-web`, the common ancestor is `/Users/chris/projects`.

If the workspace is NOT under the common ancestor, surface an advisory note to the user:

> Your target repos all live under `<common_ancestor>` but this workspace is at `<workspace_path>`. Teams often find it nicer to keep the forge workspace as a sibling of the target repos (e.g., `<common_ancestor>/forge`) so everything is in one place when browsing the filesystem. This is purely cosmetic — the workspace works fine at its current location.
>
> I will NOT move the workspace for you; mid-session directory moves are dangerous. If you want to relocate, exit Claude, run `mv <workspace_path> <common_ancestor>/forge`, then re-run `claude --plugin-dir ~/projects/aiforging` from the new location.
>
> Continue with git-init at the current location? [Y/n]

If the user says no, return `git_state = "declined"`. If yes, proceed. Record the common ancestor in `physical_location_note`.

If the workspace IS under the common ancestor (or the common ancestor is empty because targets are scattered), skip the advisory and proceed silently.

### Subroutine step 3 — Remote destination inference

Skip this step if `target_context` is empty. In that case, `suggested_remote_url` stays empty and Step A.5 prints a generic "create a remote wherever you like and run `git remote add origin <url>`" note.

For each target path in `target_context`, read its `.git/config`:

```bash
git -C <target_path> remote get-url origin 2>/dev/null
```

Collect the set of unique origin URLs. Normalize them into a (host, org, name) triple by regex-matching common formats:

- `git@github.com:org/name.git` → (`github.com`, `org`, `name`)
- `https://github.com/org/name.git` → (`github.com`, `org`, `name`)
- `git@bitbucket.org:org/name.git` → (`bitbucket.org`, `org`, `name`)
- `https://gitlab.com/org/name.git` → (`gitlab.com`, `org`, `name`)

If all targets share the same `(host, org)` tuple, propose a matching URL for the forge workspace:

- SSH style: `git@<host>:<org>/<workspace-basename>.git`
- The workspace basename is the final path component of `workspace_path` (e.g., `forge-test`, `forge`).

Present to the user:

> All <N> of your target repos are hosted at `<host>/<org>`. I suggest creating the forge workspace remote at the same org so teammates can find it alongside the codebases:
>
>     <suggested-url>
>
> I will NOT create the remote for you — that requires org permissions and credentials I don't have. This is just a suggestion. After I git-init and make the initial commit, I'll print a `git remote add` + `git push -u` command that uses this URL. Edit or replace the URL in that command if you'd rather push somewhere else.

If targets have mixed hosts or orgs, skip the suggestion and record `suggested_remote_url = ""`. Step A.5/B.11 will just say "configure a remote manually."

### Subroutine step 4 — git init and initial commit

```bash
# Init with main as the default branch.
git -C <workspace_path> init -b main

# Configure user.email and user.name ONLY if they're not already set globally or locally.
# Do not overwrite. Do not prompt if the user already has them set.
git -C <workspace_path> config user.email >/dev/null 2>&1 || {
  echo "WARN: git user.email is not configured. Commit will fail until you set it with:"
  echo "  git config --global user.email you@example.com"
  echo "  git config --global user.name  'Your Name'"
}

# Stage everything that isn't gitignored.
git -C <workspace_path> add -A

# Show the user exactly what is staged BEFORE committing.
git -C <workspace_path> status --short

# Ask to confirm.
echo "Commit staged changes as the initial commit? [Y/n]"
```

If the user confirms, commit:

```bash
git -C <workspace_path> commit -m "Initialize AI Forging workspace

- CLAUDE.md, README.md, docs/features/
- .claude/settings.json with enabledPlugins (superpowers + aiforging)
- .gitignore excluding settings.local.json and helper-script backups
$(if [ -n "<target_context>" ]; then echo '- docs/features/<feature>/ drafted for <target-basename>'; fi)"
```

Capture the commit hash (`git -C <workspace_path> rev-parse --short HEAD`) into `initial_commit_hash`. Set `git_state = "initialized"` (or `"initialized-nested"` if we went down the nested branch in step 1).

If the user declines the commit, leave the files staged and return `git_state = "deferred"` with a note: "Changes staged but not committed. Run `git -C <workspace_path> commit` when ready."

### Subroutine step 5 — Print the remote-add hint

If `suggested_remote_url` is non-empty AND `git_state` is `"initialized"` or `"initialized-nested"`, print:

```
To push this workspace to a remote after creating the repo at <host>/<org>:

    git -C <workspace_path> remote add origin <suggested_remote_url>
    git -C <workspace_path> push -u origin main
```

If `suggested_remote_url` is empty but `git_state` is `"initialized"`, print the generic hint:

```
When you're ready to push this workspace to a remote, create a repo at your
preferred destination and run:

    git -C <workspace_path> remote add origin <your-url-here>
    git -C <workspace_path> push -u origin main
```

Return all recorded outputs to the caller.

### Subroutine hard rules

- **Never `git push`.** Pushing requires credentials and a real remote. The subroutine creates an initial commit locally and prints the commands. Push is the user's job.
- **Never `git remote add` automatically.** We only suggest the URL; the user runs `git remote add` themselves after creating the remote repo.
- **Never move the workspace directory.** The physical-location advisory is a text note, nothing more.
- **Never commit `.claude/settings.local.json`.** The `.gitignore` written in Step A.2 protects it, but double-check `git status --short` before committing — if `settings.local.json` appears in the staged list, stop immediately, show the user, and fix the `.gitignore` before proceeding.
- **Never configure `user.email` or `user.name` without consent.** Warn if they're missing and let the user decide.
- **Never run destructive git commands.** No `reset --hard`, no `clean -f`, no `rebase`. The subroutine only does `init`, `add`, `status`, `commit`, and `rev-parse` for queries.

---

## Hard rules (both phases)

- **Never write or modify source code in target repos during setup.** This command installs, analyzes, and proposes. Refactoring is a separate, explicit operation.
- **Never overwrite user files silently.** Diff first, ask second, write third. This applies to every template copy, every conventions copy, every pattern seed.
- **Never hand-edit settings files.** Use `configure-directories.py` (for `additionalDirectories` in `settings.local.json`) and `configure-plugins.py` (for `enabledPlugins` in `settings.json`). Never mix the two.
- **Never write absolute local paths into `.claude/settings.json`.** That file is committed and shared. Absolute paths live in `.claude/settings.local.json`, which is gitignored.
- **Never run from the aiforging plugin source repo.** That's a developer context, not a user context.
- **Never invent projects.** If detection finds nothing and the user points at an empty folder, say so and stop.
- **Never use `${CLAUDE_PLUGIN_ROOT}` inside user-facing paths.** It's for scripts the plugin runs, not for paths the user will see or edit.
- **Never dispatch subagents from this command.** Setup is interactive bootstrapping; subagent dispatch belongs to `executing-plans` and `hammer-refactor`.
- **Never `git push` or `git remote add` automatically.** The git integration subroutine only inits the repo and stages an initial commit. Pushing to a remote is the user's explicit follow-up step.
- **Never write anywhere under `${CLAUDE_PLUGIN_ROOT}`.** The plugin source is read-only from this command's perspective. Do not update `PLAN.md`, do not leave breadcrumbs in `conventions/`, do not touch anything under the plugin source directory. End-user session history is captured by git commits in the forge workspace (Step B.10) and by the state of the forge workspace and target repo themselves. There is no plugin-side log of end-user runs — intentionally. An older revision of this command told Claude to append to `${CLAUDE_PLUGIN_ROOT}/PLAN.md` at the end of every run; that instruction was a three-layer-model violation and has been removed. If you see similar instructions in any skill, convention file, or other command, treat them as bugs and stop.
