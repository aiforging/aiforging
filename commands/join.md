---
description: Wire an already-shared forge workspace to your machine. Run this after cloning a workspace a teammate created. Reads the committed target registry, asks where each target repo lives on your machine (offering to clone the ones you don't have), writes your own gitignored settings.local.json, checks your plugin prerequisites, and confirms the workspace resolves. Does not re-onboard targets, does not re-run the analyzer, and touches no shared file.
user_invocable: true
---

# /aiforging:join

**For the second engineer onward.** Someone on your team ran `/aiforging:setup`, committed the forge workspace, and pushed it. You cloned it. This connects that workspace to your machine.

## What this is, and what `/aiforging:setup` is

They are different operations and conflating them is how a joiner accidentally re-onboards a target that was onboarded months ago.

| | |
|---|---|
| **`/aiforging:setup`** | Creates a workspace, or adds a **new** target to one. Writes shared files. Runs the architecture analyzer. Changes what the team sees. |
| **`/aiforging:join`** | Connects an **existing** workspace to **your** machine. Writes only your gitignored `settings.local.json`. Changes nothing anyone else will see. |

If you find yourself about to copy conventions into a target, run the analyzer, or edit a committed file — stop. That is Phase B of setup, and this is not it.

## Step 0 — Confirm this is a workspace you're joining, not one you're creating

```bash
test -f ./CLAUDE.md && grep -qE "AI Forging( forge)? workspace" ./CLAUDE.md && echo HAS_MARKER
test -f ./docs/features/README.md && echo HAS_FEATURES
test -f ./.claude/settings.json && echo HAS_SETTINGS
test -f ./.aiforging/targets.json && echo HAS_REGISTRY
test -f ./.claude/settings.local.json && echo HAS_LOCAL
```

- **No workspace markers** → this is not a workspace. Point at `/aiforging:setup` and stop.
- **Markers present, `settings.local.json` already present and populated** → already joined. Report what is registered and offer to verify each path still exists rather than redoing anything.
- **Markers present, no `settings.local.json`** → this is the join case. Proceed.
- **Markers present, no `targets.json`** → the workspace predates the registry (added in v0.4.0). Say so, and fall back to Step 2b.

## Step 1 — Check the prerequisites, before touching anything

Joining fails confusingly when the plugins are missing, because the workspace *looks* right and nothing works. Check first and report plainly:

```bash
claude plugin list
```

The workspace's committed `.claude/settings.json` **enables** `superpowers` and `aiforging` — it does not install them. Enabling a plugin that is not installed does nothing at all, silently. If either is missing from `plugin list`, give the install commands and stop here; there is no point registering paths for a workspace whose tooling cannot run.

State the distinction out loud, because it is the single most common confusion for a joiner:

> Your clone came with `enabledPlugins` already set, which is why nothing prompted you. But enabling is not installing — the plugin code lives on your machine, not in the repo. You need both plugins installed once per machine before this workspace does anything.

## Step 2 — Read the target registry and locate each target

`.aiforging/targets.json` lists what this workspace forges: name, git remote, role, stack. **No absolute paths** — those are per-machine, which is exactly why this step exists.

For each target, in order:

1. **Look for it near the workspace first.** Sibling directories of the workspace, and siblings of its parent, matching the target name or the repo name from the remote. Most teams keep their repos together, so this finds it most of the time.
2. **Confirm what you found** — never assume. Verify the directory's `git remote -v` matches the registry's `remote` before accepting it. Two repos with the same directory name is common enough to matter.
3. **If it is not found, ask**: "Where is `backend` (`git@github.com:acme/acme-api.git`) on your machine? Give me the absolute path, or say `clone` and I'll clone it, or `skip` if you don't work in this one."
4. **If they say clone**, ask where to put it, then clone. Do not pick a location for them.
5. **`skip` is a first-class answer.** A frontend engineer may have no reason to hold a backend repo. Register what they have; note what was skipped; do not treat it as an error.

### Step 2b — No registry (workspace predates v0.4.0)

Derive the target list from what is committed: `target:` tags in `docs/features/*/plan.md` slices, and any subdirectory containing `.aiforging/`. Present what you inferred, ask the user to confirm and correct it, then **offer to write `.aiforging/targets.json`** so the next joiner does not have to guess.

That last part is the only time this command writes a shared file, it is offered rather than assumed, and it is a strict improvement for everyone who joins later.

## Step 3 — Write your own settings.local.json

```bash
if command -v uv >/dev/null 2>&1; then FORGE_PY="uv run"; else FORGE_PY="python3"; fi
$FORGE_PY ${CLAUDE_PLUGIN_ROOT}/scripts/configure-directories.py add \
  --settings-file ./.claude/settings.local.json \
  --directory /abs/path/to/backend
```

One `add` per confirmed target. This file is gitignored — it is yours, it holds absolute paths that are meaningless on anyone else's machine, and **it must never be committed.** If `git status` shows it, the workspace's `.gitignore` is wrong; say so.

## Step 4 — Register the workspace in your pointer file

So that `/aiforging:forge` and `/aiforging:resume` work from any directory:

```bash
$FORGE_PY ${CLAUDE_PLUGIN_ROOT}/scripts/configure-workspace-pointer.py \
  --pointer-file ${HOME}/.claude/aiforging.json set-active --workspace "$(pwd)"
```

**Opt-in.** This is the only thing that writes outside the workspace. Explain what it does and default to yes, but accept no — declining costs the user nothing except having to `cd` into the workspace before running commands.

## Step 5 — Verify, then orient

Confirm the workspace actually resolves: the markers are present, every registered path exists, and each target has `.aiforging/`. Report anything that failed rather than declaring success over it.

Then **show them what is here**, because a joiner's real question is not "did it work" but "what is everyone working on":

> **You're connected.** 3 of 4 targets registered (`unification` skipped).
>
> This workspace has 9 features. Most recently active:
>
> - `renumber` — 3/11 slices — last touched 2 days ago by Priya
> - `cursor-pagination` — 8/8 ✅ — last touched 3 weeks ago by Sam
>
> `/aiforging:resume` picks any of them up and tells you where it stands.
> `/aiforging:forge <name> "<what you want>"` starts a new one.

Build that list the way `resume-feature` does — refresh `docs/features/INDEX.md` and read it. If the skill is available, dispatch it rather than reimplementing the derivation here.

## Hard rules

- **Never write a committed file**, with the single exception of the offered `targets.json` backfill in Step 2b.
- **Never re-onboard a target.** No conventions copying, no analyzer run, no skills install. Those are `/aiforging:setup` Phase B, and the target already has them — they came with the clone.
- **Never commit `settings.local.json`**, and say something if it is not gitignored.
- **Never guess a path.** Verify against the registry's remote, or ask.
- **Never proceed past Step 1 with a missing plugin.** The failure mode downstream is silent and confusing.
