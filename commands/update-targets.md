---
description: Propagate plugin updates — new or changed skills, conventions, and seeded patterns — into the forge workspace and every previously onboarded target repo, with diff-and-ask semantics and timestamped backups. Manifest-driven, so additions since your install are offered with an explanation rather than installed silently. Nothing under docs/features/ and no user-captured pattern is ever touched. Never runs refactors, tests, or git commits.
user_invocable: true
---

# /aiforging:update-targets

**Purpose:** Propagate plugin-level updates (new or changed skills, conventions, shared-tier seeded patterns) into the forge workspace and all previously onboarded target repos, with diff-and-ask semantics. Nothing is overwritten silently.

**When to run:** After a plugin update (marketplace or `--plugin-dir` reload), or whenever you suspect the copies in your workspace or target repos have drifted from the current plugin version.

**Governance:** This command modifies files but NEVER executes refactors, runs tests, or commits to git. It stages changes and lets you review before committing.

---

## Prerequisites

- Must be run from inside an AI Forging workspace (the same directory markers that `/aiforging:setup` Phase A creates). The `CLAUDE.md` marker is matched as `AI Forging( forge)? workspace` — both phrasings exist in the wild.
- The plugin must be loaded (either via marketplace install or `--plugin-dir`).

## Step 0 — Detect workspace and discover targets

Run the same workspace detection as `/aiforging:setup` Step 1:

```bash
test -f ./CLAUDE.md && grep -qE "AI Forging( forge)? workspace" ./CLAUDE.md && echo "HAS_CLAUDE_MD" || echo "NO_CLAUDE_MD"
test -f ./docs/features/README.md && echo "HAS_FEATURES_README" || echo "NO_FEATURES_README"
test -f ./.claude/settings.json && echo "HAS_SETTINGS_JSON" || echo "NO_SETTINGS_JSON"
test -f ./.claude/settings.local.json && echo "HAS_SETTINGS_LOCAL" || echo "NO_SETTINGS_LOCAL"
```

> **Grep the whole file, never a `head -c` window.** Workspace `CLAUDE.md` files are meant to be customized — `/aiforging:update-targets` itself treats them as "commonly customized" — and a user who adds a paragraph above the marker pushes it out of any fixed byte window. A truncated check reports a genuine workspace as not-a-workspace and aborts. This happened on the first real-world run of `/aiforging:update-targets` (ServiceLine, v0.3.0). The file is small and read once; there is nothing to optimize here.

**Before aborting, check the second signal.** `docs/features/README.md` carries `<!-- AI Forging workspace marker: docs/features -->`. If that file has its marker and `.claude/settings.json` exists but `CLAUDE.md`'s marker is missing, this is a real workspace whose `CLAUDE.md` was customized or predates the marker. Say so, **offer to add the marker line**, and continue — do not abort. A workspace that has been working for months should not stop being one because of a phrasing change.

If neither signal is present, abort:

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

## Step 0.5 — Read the artifact manifest

**Everything this command diffs is described in `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/artifacts.json`.** Read it first. Do not carry a hardcoded list of skills or convention directories in your head — that list is exactly what goes stale, and a stale list means a new artifact installs on fresh setups but never reaches existing users. Silent upgrade gaps are the failure mode this manifest exists to prevent.

Each entry gives you:

- `source` — the path under `${CLAUDE_PLUGIN_ROOT}`.
- `install[]` — one entry per scope (`workspace` / `target`) with the `dest` path relative to that scope's root, whether it is `optional`, which target `roles` it applies to, and any install `bundle` it belongs to.
- `update` — the policy that governs this artifact:
  - **`diff-and-ask`** — diff, default Y, back up before overwriting.
  - **`offer-default-no`** — commonly customized; offer the diff, default N.
  - **`seeded-only`** — only files carrying `seeded: true` frontmatter are eligible; everything else in that directory is user-captured and untouchable.
  - **`create-if-missing`** — create when absent, never modify.
  - **`never`** — user-owned; do not read, diff, or write.
- `since` — the plugin version the artifact first shipped in. Anything whose `since` is newer than what the user has installed is an **addition**, not an update, and should be presented as an offer with an explanation of what it does.

**Read the version stamp first: `<scope-root>/.aiforging/VERSION`.** One line, the plugin version those copies correspond to. It tells you what to compare against, so you can distinguish *the plugin changed this file* from *the user changed this file* — the single most important distinction this command makes, and the one it gets wrong most expensively.

With a stamp, and when the plugin is a git checkout (marketplace installs are), you can diff three ways properly:

```bash
# what the file looked like at the version the user installed
git -C ${CLAUDE_PLUGIN_ROOT} show "v<stamped-version>:conventions/tdd/fire-red-green-refactor.md" 2>/dev/null
```

Then: **on-disk == stamped-version** means pristine, safe to update silently at default Y. **on-disk != stamped-version** means the user customized it — a three-way merge, and it needs to be shown to them.

**If there is no stamp** (onboarded before 0.3.1), or the tag lookup fails, fall back to inference: compare on-disk against both the current plugin version and whatever earlier content you can recover, and **say out loud that you are inferring.** Do not present an inferred classification with the same confidence as a stamped one. Under inference, default customized-looking files to *skip*, not to *overwrite*.

Write the stamp at the end of a successful run (Step 3).

**An explicit `install[].dest` always wins over a `user_owned` pattern that matches the same path.** `user_owned` is a catch-all for files the manifest never names; a file the manifest gives a destination is plugin-managed by definition and its `update` policy governs. Three of the plugin's own files match a `user_owned` pattern literally — `docs/features/README.md`, `.aiforging/patterns/README.md`, `.aiforging/anti-patterns/README.md` — and without this rule a literal reading forbids ever correcting them. The manifest states the same rule under `$precedence`.

Also read the manifest's `user_owned` list. **Nothing matching it is ever diffed, backed up, moved, or overwritten** — not the user's feature folders, not their `testing.md` files, not their `ai-testing/` or `ai-reviews/` run records, not their captured patterns, not their `settings.local.json`.

**If an entry in the manifest names a source file that does not exist in the plugin**, stop and report it rather than skipping quietly — that is a packaging bug, and continuing would hide it.

**Optional artifacts that are not currently installed are offers, not updates.** Never install an optional artifact into a scope that does not have it without asking, and when you ask, say what the artifact does — the user may have declined it deliberately last time.

## Step 1 — Diff workspace-level artifacts

Walk every manifest entry that has an `install` record with `scope: "workspace"`, and diff the installed copy against the plugin's `source`. Present all diffs at once, then ask for bulk or per-item approval.

For a directory-kind artifact, diff file by file. Files present in the target directory but absent from the plugin are **local additions** — leave them alone and say so.

When a file differs, show a **summary** of the change in two or three sentences rather than dumping the whole diff, and offer to show the full diff on request.

### Special handling by policy

**`seeded-only` (the shared-tier pattern library).** For each `.md` in `./.aiforging/patterns/` and `./.aiforging/anti-patterns/`:

1. Read the YAML frontmatter. `seeded: true` means it came from the plugin and is eligible for update. Match to the plugin file by filename.
2. **No `seeded: true`, or no frontmatter at all, means the user captured it. Never touch it** — not to update, not to reformat, not to "fix" its frontmatter. **One exception, by filename: `README.md`.** Every tier directory carries one as a placeholder (git will not keep an empty directory), it has no frontmatter by design, and it is plugin-managed — `template:patterns-tier-readme` and `template:anti-patterns-tier-readme` in the manifest. Match it by name, never by the frontmatter test.
3. Also check for seeded files in the plugin that are **missing** from the workspace. Those are additions.

**`offer-default-no` (the workspace's `CLAUDE.md` and `README.md`).** These were seeded from templates and users routinely customize them:

> "Your workspace `CLAUDE.md` differs from the current template. That's expected if you've customized it. Want to see the diff? [y/N]"

Default: skip.

**`docs/features/README.md` is the exception, and defaults to Y.** It is a template, but unlike the other two it carries framework rules that the skills actively depend on — the `testing.md` requirement, the scoped-test-suite rule, the slice format. A workspace running a stale copy will keep planning features against rules the rest of the plugin no longer follows, and nothing will announce it. Offer it at default Y, and if the user has customized it, show the diff so they can merge deliberately.

**Additions whose `since` is newer than the installed version.** Present these as offers, never silent installs — and give each one the *reason* it exists, not just a description of its mechanics.

**This is where the explanation has to work hardest, and it is the easiest place to under-write it.** At install time the user came looking for the framework and is reading carefully. At upgrade time they came to do something else and are being interrupted by an offer for a thing they have never heard of. A one-line summary of what a skill *does* gives them nothing to decide with, so they either decline on principle or accept on trust. Neither is a real choice. Carry across the one sentence that makes the thing make sense — the same sentence `/aiforging:setup` uses when it offers the artifact for the first time.

Compare. Mechanics only, which is not enough:

> "`browser-testing` walks a feature's `testing.md` in a browser and reports divergences without fixing. `review-loop` runs review/triage/fix rounds across repos. Both optional. Install? [Y/n]"

With the reason, which is:

> **New in v0.3.0 — two optional stages that run after a feature is built.** Neither writes a feature, and neither runs unless you invoke it.
>
> **`browser-testing`** walks a feature's `testing.md` QA checklist in a real browser, marking the items only a human can judge so you can work those in parallel. **It fixes nothing, by design:** a failing step means the product and the spec disagree, and deciding which one is wrong needs a person — an auto-fixer would cement the wrong answer *and* hand you a green checklist saying so.
>
> **`review-loop`** runs rounds of review, triage and fix across every repo a feature touched. The triage step is the point: roughly a third of review findings describe deliberate behavior, so each one is verified against the source before it is accepted.
>
> Install them? [Y/n]

### Check the `.gitignore` rules

The manifest's `config:gitignore` entry lists the lines the framework needs. Check each with a **whole-line fixed-string** match:

```bash
for rule in '.claude/settings.local.json' '*.bak-*' '.DS_Store' 'Thumbs.db'; do
  grep -qxF "$rule" ./.gitignore 2>/dev/null || echo "MISSING: $rule"
done
```

**A near-miss does not count.** `.claude/*.bak-*` is not `*.bak-*` — it matches neither nested paths like `.claude/skills/hammer-refactor/SKILL.md.bak-*` nor the backups this command writes into `.aiforging/` and `docs/`. That exact near-miss left seven backups tracked-eligible on the first real update run.

Offer to append only what is missing, and **never rewrite the file** — in Scenarios B and C it belongs to the user's repo and may be hundreds of lines long:

> Your `.gitignore` is missing `*.bak-*`, so the backups this command is about to write would show up as untracked files in `git status` and could be committed by accident. Append it? (Nothing else in the file is touched.) [Y/n]

### Workspace diff summary

```
Workspace update summary  (installed: v0.2.0 → plugin: v0.3.0)

  .claude/skills/capture-pattern/SKILL.md            — updated (tier selection rewrite)
  .aiforging/patterns/extract-service-from-controller.md — unchanged
  .aiforging/anti-patterns/fat-controller.md          — updated (new example added)
  .aiforging/anti-patterns/primitive-obsession.md     — unchanged
  .aiforging/README.md                                — updated (two-tier docs)
  docs/features/README.md                             — updated (testing.md + scoped-suite rules)

  NEW in 0.3.0:
  .claude/skills/browser-testing/SKILL.md             — offered (optional)
  .claude/skills/review-loop/SKILL.md                 — offered (optional)

  Workspace CLAUDE.md / README.md                     — skipped (customized, default N)
  docs/features/** (specs, plans, testing.md, runs)   — untouched (user-owned)

Apply workspace updates? [Y/n / pick by number]
```

Default: Y (apply all). The user can pick individual items by number.

**Derive every count in this summary from the same enumeration you used to classify, and never restate a number from memory.** If you say "11 user-captured patterns are protected," that number must come from `len()` of the list you actually built. Where the set is small enough to name — under about a dozen — **list it instead of counting it**; a name the user recognizes is verifiable, a count is not.

This matters more than it looks: the numbers that appear in this summary are almost always describing *what is protected from modification*, which is the worst available place to be approximately right. It is the figure a user checks before granting permission to proceed. A first real-world run reported "10 features" and "11 user-captured patterns" where the truth was 9 and 10, then self-corrected in the final summary — harmless that time, and exactly the shape of a mistake that would not be harmless.

**Before applying any overwrite**, create a timestamped backup:

```bash
cp <file> <file>.bak-$(date +%Y%m%d%H%M%S)
```

The workspace `.gitignore` already covers `*.bak-*`.

## Step 2 — Diff target-level artifacts (per target)

For each target discovered in Step 0, walk every manifest entry that has an `install` record with `scope: "target"` **and** whose `roles` include this target's detected role. A `backend` target gets the architecture / tdd / subagent-orchestration conventions and the skills bundle. A `frontend` target gets none of those — only the Playwright layer, if it opted in — **but it still gets the version stamp and the two tier directories with their placeholders**, because a frontend target with an `.aiforging/` counts as onboarded, can be asked to capture a frontend-scoped pattern, and needs recorded provenance like any other. Check the manifest's `roles` per artifact rather than assuming 'frontend means nothing applies'. Group every target into a single report.

### Rules that apply to every target artifact

1. **Missing but applicable = an addition.** A convention directory or skill the plugin ships, that this target's role qualifies for, and that is not present, is flagged as new and offered — with a line saying what it is. This is how a target onboarded at v0.1.0 picks up conventions added since.
2. **Present in the target, absent from the plugin = a local addition.** Leave it alone. Say so once; do not ask about it every run.
3. **Rendered templates are rendered before diffing.** `.aiforging/CLAUDE.md` comes from `conventions/CLAUDE.md.template` with the target's real values substituted (workspace path, target name). Diff the *rendered* result, or every target reports a difference that is not one.
4. **Optional artifacts that were declined stay declined** unless the user opts in this run. `frontend-testing/` is only diffed if it is already installed.
5. **`.aiforging/ANALYSIS.md` is never diffed or overwritten.** It is the architecture-analyzer's output — it describes *that target*, not the plugin, so there is nothing to compare it against. If the conventions changed materially this run, suggest re-running the analyzer (Step 4) rather than touching the file.
6. **Target-local patterns are user-owned.** `.aiforging/patterns/` and `.aiforging/anti-patterns/` in a target hold captured, repo-specific patterns. This command has no authority over them — it does not diff them, update them, or reformat them. If the directories do not exist (target onboarded before the two-tier model), offer to create them empty:

   ```bash
   mkdir -p <target>/.aiforging/patterns <target>/.aiforging/anti-patterns
   cp ${CLAUDE_PLUGIN_ROOT}/templates/patterns-tier-README.md      <target>/.aiforging/patterns/README.md
   cp ${CLAUDE_PLUGIN_ROOT}/templates/anti-patterns-tier-README.md <target>/.aiforging/anti-patterns/README.md
   ```

   **Install the placeholder even when the directory already exists.** The common upgrade case is a tier that is present but has no `README.md` — every workspace onboarded before 0.3.1. Treat a missing `<tier>/README.md` as an ordinary manifest addition (`since: 0.3.1`), offered like any other, not as something that only happens when the whole directory is absent.

   **The `README.md` is not decoration — it is what makes the directory survive.** Git cannot track an empty directory, so a tier created empty vanishes on the next clone or checkout and this command re-offers to create it on every future run, forever. On the first real update run, `fe/.aiforging/patterns/` had never held a tracked file in the repo's entire history. The placeholder ends that loop and puts the two-tier explanation where someone will actually meet it.

   **Every pattern-library glob must exclude `README.md`.** It is documentation, not a pattern.

### Target diff summary (per target)

```
Target: /abs/path/to/backend (symfony-php, role: backend)

  .aiforging/architecture/domain-driven-hexagonal.md  — updated
  .aiforging/architecture/naming.md                    — unchanged
  .aiforging/tdd/fire-red-green-refactor.md            — updated (scoped-suite rule)
  .aiforging/tdd/test-harness-requirements.md          — unchanged
  .aiforging/subagent-orchestration/README.md          — updated (scoped-run in every template)
  .aiforging/CLAUDE.md                                 — unchanged (rendered before diff)
  .claude/skills/hammer-refactor/SKILL.md              — updated (feature-suite scoping)
  .claude/skills/capture-pattern/SKILL.md              — unchanged

  NEW in 0.3.0:
  .aiforging/tdd/feature-test-suite.md                 — new convention (not previously installed)

  .aiforging/frontend-testing/                         — not installed (declined at onboarding)
  .aiforging/patterns/ (target-local)                  — untouched (user-owned)

Apply updates to this target? [Y/n / pick by number]
```

Default: Y. Approval is **per target** — the user can accept everything for one repo and decline for another.

**Backup before overwrite**, same as the workspace:

```bash
cp <file> <file>.bak-$(date +%Y%m%d%H%M%S)
```

Targets are separate git repos with their own `.gitignore` files, which may not cover `*.bak-*`. Mention the backups in the closing summary so the user does not commit them by accident.

### Why `browser-testing` and `review-loop` are not offered here

They are workspace-scoped in the manifest, deliberately. `browser-testing`'s required input is `<workspace>/docs/features/<feature>/testing.md`, and `review-loop` fans out across every repo a feature touched and writes its round records into the feature folder. A copy sitting in one target repo would be a skill whose primary input is not in that repo — discoverable, and broken on invocation.

If a target's teammates want them, the answer is for those teammates to work from the forge workspace, not to copy the skill down.

## Step 3 — Apply updates

For each approved update (workspace or target):

1. Create the backup.
2. Copy the new version from `${CLAUDE_PLUGIN_ROOT}`.
3. For new additions (directories or files that didn't exist), create and copy.

**Write the version stamp.** After every scope that was updated, record what it is now at:

```bash
echo "<plugin-version>" > <scope-root>/.aiforging/VERSION
```

Write it for the workspace and for every target that accepted updates — and **only** for those. A target the user skipped is still at its old version, and stamping it would make the next run trust a lie.

**Offer to clear the backups.** Every overwrite left a `*.bak-*` file. They exist so the user can review, not so they can accumulate:

> Seven `.bak-*` files were written next to the originals. Review the diff first, then I can remove them:
>
> ```bash
> find . -name '*.bak-<timestamp>' -delete
> ```
>
> Delete them now, or leave them for you to review first? [leave / delete]

Default: **leave**. Offer once; do not delete without being asked. Use the exact timestamp from this run so the command cannot touch backups from an earlier one.

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

4. **Manifest coverage.** Confirm every manifest entry applicable to each scope is now accounted for — installed, explicitly declined this run, or explicitly declined earlier. Anything that is applicable, absent, and was never offered is a bug in this command; report it rather than leaving it silently missing.

5. **Say what changed in behavior, not just in files.** A list of updated filenames tells the user nothing about what to do differently. When an update changes how the framework operates, name it in a sentence:
   > "Two behavior changes in this update. (1) Plans now name a single test suite per feature, and no agent runs the full repository suite — you run it yourself at the end, and the skills will now remind you to. (2) Features with a UI surface get a `testing.md` QA checklist, which is the required input to the new `browser-testing` skill.
   >
   > Existing feature folders are untouched. Features you plan from here on will pick both up."

6. **Point at what to read.** If new conventions were installed, name the one or two files worth reading now rather than listing all of them:
   > "New this version: `.aiforging/tdd/feature-test-suite.md` — one page on the scoped-suite rule and why the framework accepts the regression trade deliberately. Worth reading once."

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
