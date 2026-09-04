---
description: Start a new feature (or extend an existing one) in the current forge workspace. Creates docs/features/<name>/ with the right shape (flat or nested work items), seeds spec.md with a Summary section captured from the user's initial prompt, and hands off to superpowers:brainstorming for the rest of the spec. Runs the Planning Workflow Step 1 and then stops at the Summary checkpoint. Non-destructive; never executes plans.
user_invocable: true
argument-hint: "[feature-name] [initial prompt...]"
---

# /aiforging:new-feature

This command is the **daily-driver entry point** for starting a feature in a forge workspace. It encodes Step 1 of the four-step planning workflow documented in `${CLAUDE_PLUGIN_ROOT}/conventions/features/README.md` and then stops, handing off to `superpowers:brainstorming` for the rest of the spec interview.

It is NOT a rewrite of spec/plan generation — `superpowers:writing-plans` still does that. It is a thin **setup + feature-detection** shim on top of the canonical convention so that the common "new feature" flow is one command instead of a half-dozen manual steps.

## What this command does not do

- It does NOT execute any slice of any plan.
- It does NOT run `superpowers:writing-plans` automatically — it hands off after the Summary checkpoint and lets the user drive the rest of the planning workflow.
- It does NOT modify any target repo. The only files it writes are the feature's `spec.md` skeleton — and, when the feature has a UI surface, a `testing.md` skeleton — in the forge workspace's `docs/features/` tree.
- It does NOT commit anything to git. That's the user's call.

## Step 0 — Orient yourself

Load the following into your context without summarizing to the user:

- **The three-layer model.** You are running AI Forging *as an end user*. Never write under `${CLAUDE_PLUGIN_ROOT}`. The plugin source is read-only from this command's perspective.
- **The planning workflow.** Before Step 1 below, read `${CLAUDE_PLUGIN_ROOT}/conventions/features/README.md` so the Summary-checkpoint behavior, the flat-vs-nested taxonomy, and the living-documents rules are loaded. Do not paraphrase the convention to the user — just follow it.
- **Do NOT read `${CLAUDE_PLUGIN_ROOT}/PLAN.md`.** That's a plugin-author artifact, not an end-user resource.

## Step 1 — Locate the forge workspace

The command can be invoked from two places: inside a forge workspace (the normal case) or outside one (the "run anywhere" mode).

### 1a. In a forge workspace

The current directory is a forge workspace if ALL of the following are true:

- `./CLAUDE.md` exists AND carries the workspace marker — **either** `AI Forging workspace` or `AI Forging forge workspace`. Both are in the wild; the short one is not a substring of the long one, so match with a regex that accepts both.
- `./docs/features/` exists as a directory.
- `./.claude/settings.json` exists and contains an `enabledPlugins` key.

**Grep the whole `CLAUDE.md`, and accept both markers.** Two things go wrong here and they look identical from the outside — a real workspace reported as not-a-workspace. One is a byte window truncating the search; the other is matching only the newer marker phrase when the workspace carries the older one. Both have happened on real repos.

```bash
test -f ./CLAUDE.md && grep -qE "AI Forging( forge)? workspace" ./CLAUDE.md && echo "MARKER_OK" || echo "NO_MARKER"
```

If all three hold, use the current directory as the workspace root. Proceed to Step 2.

### 1b. Outside a forge workspace — check the pointer file

If the current directory is NOT a forge workspace, check for the pointer file at `${HOME}/.claude/aiforging.json`. If present, it has this shape:

```json
{
  "active_workspace": "/abs/path/to/the/forge/workspace",
  "workspaces": ["/abs/path/to/one", "/abs/path/to/another"]
}
```

If present and the `active_workspace` path exists and is a valid forge workspace (re-run the check from 1a against that path), use that directory as the workspace root, tell the user which workspace you're using, and proceed to Step 2. Print something like:

> No forge workspace in the current directory. Using the active workspace at `<path>` (from `~/.claude/aiforging.json`).

If the pointer file lists multiple workspaces AND no `active_workspace` is set, stop and ask the user which workspace to use. Do NOT guess.

If the pointer file is missing or the active workspace path no longer exists, stop and print:

> You're not inside a forge workspace, and I can't find an active workspace at `~/.claude/aiforging.json`. Either `cd` into an existing forge workspace and re-run this command, or run `/aiforging:setup` in an empty directory to bootstrap one.

Do not attempt to "help" the user by bootstrapping on the fly. Bootstrapping is `/aiforging:setup`'s job.

## Step 2 — Parse arguments

This command accepts two optional arguments: a feature name and an initial prompt. They are parsed positionally:

- **No arguments.** Prompt the user: "What would you like to call the feature? (kebab-case, e.g., `invoice-tax-calculation`)" Then: "Give me the one-or-two-sentence prompt for what the feature does." Capture both answers.
- **One argument.** Treat it as the feature name. Prompt for the initial prompt separately.
- **Two or more arguments.** First argument is the feature name; everything after it is the initial prompt concatenated together.

Normalize the feature name: lowercase, replace spaces with hyphens, strip any characters that aren't `[a-z0-9-]`, collapse repeated hyphens. Reject a name that is empty after normalization, starts or ends with a hyphen, or is longer than 60 characters. On rejection, explain why and re-prompt.

## Step 3 — Feature detection

Before creating anything, check whether this feature already exists or is a near-match to something in `docs/features/`.

Run this detection (bash is fine; keep it simple):

```bash
cd <workspace>
find docs/features -maxdepth 1 -mindepth 1 -type d 2>/dev/null | sort
```

For each existing feature directory:

1. **Exact name match** — `docs/features/<normalized-name>` exists.
2. **Substring match** — existing feature name contains the normalized name, or the normalized name contains an existing feature name.
3. **Token overlap** — 50%+ of the kebab-case tokens overlap between the new name and an existing name.

If ANY match is found, stop and present the matches to the user. Ask:

> Found these existing features that might be related:
>   - `docs/features/<match-1>/` (<spec summary if readable, else "no spec yet">)
>   - `docs/features/<match-2>/` …
>
> Is this a **new** feature, an **extension** of one of the above (new work item inside the existing feature), or should we **abort**? [new | extend-<n> | abort]

- **new**: proceed to Step 4 with the user's original name. Warn about the naming collision if the exact name matches (feature folders are stable-once-created — the user needs to pick a different name). Re-prompt for a name.
- **extend-<n>**: proceed to Step 5 (extension flow) targeting the selected existing feature.
- **abort**: stop and print "No feature created. Feel free to re-run when ready."

If no match is found, skip this confirmation and proceed directly to Step 4.

## Step 4 — New feature: choose the shape

Ask the user whether this feature will have one work item or several:

> Will this feature be a single work item, or will it decompose into multiple work items that can be planned and dispatched somewhat independently?
>
> - **Flat (default)** — `docs/features/<name>/spec.md` + `plan.md` + `notes.md`. Right for most features.
> - **Nested** — `docs/features/<name>/overview.md` + numbered work-item subfolders (`01-<item>/spec.md` + `plan.md`, `02-<item>/spec.md` + `plan.md`, …). Right when you already know there will be two or more work items.
>
> Flat or nested? [F/n]

Default: F (flat). If the user is unsure, recommend flat — the convention says nesting a single-work-item feature creates noise, and it's cheap to keep things flat now and manually reorganize later if the feature genuinely grows two heads.

### 4a. Flat shape — create the folder

```bash
mkdir -p <workspace>/docs/features/<name>
```

Create `<workspace>/docs/features/<name>/spec.md` with this skeleton:

```markdown
# <Human-readable title derived from the feature name>

<!-- AI Forging spec.md
     Follow the planning workflow in conventions/features/README.md:
       Step 1 — Summary (below) — locked checkpoint. Don't fill the rest of
                 this file until the user has confirmed the Summary.
       Step 2 — Grouped clarifying questions in themed rounds of 3–5.
       Step 3 — Architecture review against every affected target's .aiforging/.
       Step 4 — Write plan.md (separate file) with the slice format.
-->

## Summary

> **Captured from the user's initial prompt on YYYY-MM-DD.** This section is the Step 1 checkpoint of the planning workflow. Do not proceed to the rest of the spec until the user has confirmed this captures what they want.

<the initial prompt, restated in your own words — be specific, do not paraphrase into vague goals>

## Problem

_(To be filled in during Step 2 — grouped clarifying questions.)_

## Who is affected

_(To be filled in during Step 2.)_

## In scope / out of scope

_(To be filled in during Step 2.)_

## Affected code

_(List the affected repos and subsystems. Must be filled in before Step 3 — architecture review.)_

## Architectural decisions

_(Decisions or deferrals surfaced during the interview. Gate candidates for plan.md.)_
```

Replace `YYYY-MM-DD` with today's date (you can get it from the shell with `date +%Y-%m-%d` if you're not sure). Replace the angle-bracketed "restated prompt" placeholder with your honest-effort restatement of the user's initial prompt — specific, not paraphrased into vagueness.

Do NOT create `plan.md` yet. The convention is explicit: plan.md is Step 4 of the workflow, not Step 1. An empty `plan.md` is worse than no `plan.md`.

Do NOT create `notes.md` preemptively. It's optional and gets created when there's actually something to note.

### 4b. Nested shape — create the folder and the first work item

Ask the user for the first work item's name: "What's the name of the first work item? (kebab-case, will be prefixed with `01-`)"

Then ask: "Brief description of this first work item?"

```bash
mkdir -p <workspace>/docs/features/<name>/01-<first-work-item>
```

Create `<workspace>/docs/features/<name>/overview.md`:

```markdown
# <Human-readable feature title>

<!-- AI Forging overview.md
     Feature-level umbrella document. Lists the work items in dispatch order
     and summarizes how they fit together. Each work item has its own
     spec.md and plan.md inside its numbered subfolder.
-->

## Summary

<the initial prompt, restated in your own words>

## Work items

1. **01-<first-work-item>** — <brief description>
   <!-- Add follow-up work items here as they are scoped. Use `NN-` prefix in dispatch order. -->

## Dependencies

_(To be filled in as work items are added. Note which items block which.)_
```

Create `<workspace>/docs/features/<name>/01-<first-work-item>/spec.md` using the same Step-1 Summary skeleton from 4a, but with the Summary focused on this specific work item rather than the whole feature.

## Step 4c — UI surface check and `testing.md` skeleton

After the folder exists (flat or nested), ask one question:

> Will this feature have a **UI surface** — anything a person clicks, sees, or fills in?
>
> - **Yes (default)** — I'll create a `testing.md` skeleton now. It's the human QA checklist: the steps someone walks through in the running app. It's also the required input to `/aiforging:browser-testing` later.
> - **No** — research-only work, or a purely internal / pipeline change with no visible behavior. I'll note that decision in the spec instead.
>
> [Y/n]

Default: Y.

**If yes**, copy the template and fill in the feature name:

```bash
cp ${CLAUDE_PLUGIN_ROOT}/templates/feature-testing.md \
   <workspace>/docs/features/<name>/testing.md
```

Then replace `<feature name>` in the heading with the human-readable feature title. **Leave the placeholder checklist items as placeholders.** You do not know the access rules, the happy path, or the edge cases yet — the spec interview (Step 2 of the planning workflow) is what produces them, and the checklist gets filled in during Step 4 of that workflow, from the spec. Inventing checklist items now, before the spec exists, produces a checklist that tests whatever you imagined rather than what was agreed.

For a **nested** feature, `testing.md` goes at the **feature level**, not inside `01-<work-item>/`. One checklist per feature, ordered by work item.

**If no**, create nothing, and add this line under "In scope / out of scope" in `spec.md`:

```markdown
**No `testing.md`.** This work has no UI surface (<one-line reason: research-only / internal pipeline change / …>), so the UI QA checklist is deliberately skipped per `conventions/features/README.md`.
```

Recording the decision matters more than the decision itself. A missing `testing.md` with no explanation is indistinguishable from an oversight, and six months later nobody can tell which it was.

## Step 5 — Extension flow

When the user said "extend-<n>" in Step 3, the feature already exists. Look at what shape it's in:

```bash
ls <workspace>/docs/features/<existing-name>/
```

### 5a. Existing feature is flat (only spec.md / plan.md / notes.md)

Offer to upgrade it to the nested shape:

> `<existing-name>` is currently flat (one spec, one plan). Adding a new work item means converting it to the nested shape:
>
>   - The existing spec.md will move to `<existing-name>/01-<current-name-or-prompt>/spec.md`.
>   - The existing plan.md will move to `<existing-name>/01-<...>/plan.md`.
>   - A new `<existing-name>/overview.md` will be created.
>   - A new `<existing-name>/02-<new-work-item>/` will be created with its own spec.md.
>
> Proceed? [Y/n]

If yes:

1. Prompt for the name of the existing work item ("What should we call the existing work as `01-<name>`?"). Normalize to kebab-case.
2. Prompt for the new work item's name and brief description.
3. `mkdir -p docs/features/<existing>/01-<existing-work-item>` and `mv docs/features/<existing>/spec.md docs/features/<existing>/01-<existing-work-item>/spec.md`. Same for `plan.md`. **Only `spec.md` and `plan.md` move.** `notes.md`, `testing.md`, `summary.md`, `ai-testing/` and `ai-reviews/` are feature-wide and stay at the feature level — `testing.md` in particular is one checklist per feature, never one per work item. If `testing.md` exists, add a heading for the new work item to it so the checklist stays ordered by work item in dependency order.
4. Create `docs/features/<existing>/overview.md` using the template from 4b, listing BOTH work items.
5. `mkdir -p docs/features/<existing>/02-<new-work-item>` and create its `spec.md` with the Step-1 Summary skeleton.

If no, stop and tell the user the feature stays as-is; if they want to add scope, they should either edit the existing spec.md in place (if it's a small addition) or re-run with a different feature name for a separate feature.

### 5b. Existing feature is already nested

Find the highest existing `NN-` prefix and increment it. If `01-foo` and `02-bar` exist, the new work item is `03-<new-name>`.

1. Prompt for the new work item's name and brief description.
2. `mkdir -p docs/features/<existing>/<NN>-<new-work-item>` and create its `spec.md` with the Step-1 Summary skeleton, scoped to the new work item.
3. Append the new work item to the "Work items" list in `docs/features/<existing>/overview.md`, in order.
4. If `docs/features/<existing>/testing.md` exists, append a `## <NN> — <new work item>` section to it with placeholder checkboxes, so the feature's single checklist keeps covering the whole feature. Do NOT create a second `testing.md` inside the work-item folder. If it does not exist and this work item has a UI surface, run the Step 4c offer now.
5. **Do not create or update `summary.md` here.** It is written after implementation, not during scoping.

## Step 6 — Summary checkpoint (Planning Workflow Step 1 handoff)

Show the user what you just created and stop. Print something like:

```
Created:
  <workspace>/docs/features/<name>/
  ├── spec.md      (Step 1 Summary captured — AWAITING CONFIRMATION)
  ├── testing.md   (skeleton — checklist gets filled in from the spec, in planning Step 4)
  │
  └── (plan.md will be created after Steps 2–3 of the planning workflow are done)

Planning workflow — Step 1 checkpoint:
  I captured your prompt into the Summary section of spec.md. Before we go
  further, please review the Summary and confirm it captures what you want.
  If anything is off, tell me now and I'll rewrite the Summary.

  Once the Summary is locked, the next step is Step 2 — the grouped
  clarifying-questions interview. I recommend dispatching
  superpowers:brainstorming for that. Shall I hand off now? [Y/n]
```

Read back the Summary verbatim so the user sees exactly what's in the file. If the user rewrites the Summary, update spec.md and re-confirm. Do not proceed until the user agrees.

On user approval, dispatch `superpowers:brainstorming` against the feature's `spec.md` path. If `superpowers` is not installed, print a short message telling the user to install it (`/plugin install superpowers@claude-plugins-official`) and stop without proceeding further — do not attempt to improvise the interview.

## Step 7 — Hard rules (summary)

These are the non-negotiables. If you catch yourself about to violate one, stop.

- **Never write under `${CLAUDE_PLUGIN_ROOT}`.** The plugin source is read-only from this command's perspective.
- **Never create `plan.md` in Step 4.** Plan.md is Step 4 of the planning workflow, not Step 1 of this command.
- **Never fill in `testing.md`'s checklist here.** Create the skeleton; the items come from the spec, which does not exist yet.
- **Never create a second `testing.md` inside a work-item folder.** One per feature, at the feature level.
- **Never create `summary.md`.** It is written after implementation is complete, by whoever finishes the feature.
- **Never skip the Summary checkpoint.** Do not proceed past Step 6 without user confirmation of the Summary.
- **Never rename an existing feature folder.** If the user chose a name that collides, re-prompt for a different name. Existing features are stable-once-created per the convention.
- **Never modify a target repo.** This command only touches `<workspace>/docs/features/`.
- **Never commit to git.** The user commits when they're ready.
- **Never paraphrase the convention to the user.** If the user asks "why flat vs nested?" just read them the relevant section of `conventions/features/README.md` — don't make up rules.

## Relationship to `/aiforging:setup` Phase B Step B.9

Phase B of the setup command has a "propose an architecture-alignment feature" step (B.9) that ALSO creates a feature folder and drafts a spec. That step uses the same shape rules documented in `conventions/features/README.md` and produces spec.md in the same Step-1-Summary format this command produces. The differences:

- Setup B.9 is **non-interactive about the initial prompt** — the prompt is "the architecture-alignment work proposed by the analyzer for `<target>`."
- Setup B.9 **does** write a `plan.md` draft because the analyzer findings are already structured enough to feed the slice format directly.
- Setup B.9 is **auto-invoked** by the onboarding flow; this command is **user-invoked** as the daily driver.

Both commands are implementations of the same underlying rule: "feature folders follow the shape and planning workflow in `conventions/features/README.md`." If you find yourself writing logic here that contradicts Step B.9, stop — the convention doc is the source of truth, and both commands should agree.
