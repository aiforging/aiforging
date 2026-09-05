---
name: resume-feature
description: Pick up a feature that already exists in the forge workspace — one you paused, or one a teammate started months ago. With a feature name it reads that feature's spec, plan, notes, QA checklist and review records and reports where things actually stand. With no argument it presents the workspace's features and asks which. Read-only orientation — it changes no code, checks out no branches, and dispatches nothing. Trigger on "/aiforging:resume", "where did we leave off on X", "pick up the X feature", or a request to continue existing feature work.
---

# Resume Feature

> **The handoff skill.** A forge workspace is a shared repository, so the feature you are looking at was often planned by someone else, months ago, and its state lives across five or six files. This reads them and tells you where things stand, so that picking up someone else's work costs a minute instead of an afternoon.

**This skill is read-only.** It reads, it reports, it stops. It does not check out branches, dispatch slices, edit plans, or write code. The one exception is the feature index (see Step 1), which is regenerated bookkeeping, never content.

---

## Why this exists

The framework's whole premise is that a feature's intent, plan, and history live in durable files rather than in a chat transcript. That only pays off if someone can walk up cold and read them — otherwise the files are an archive nobody opens, and the knowledge really did live in the transcript after all.

Two situations it is built for:

- **An engineer goes on vacation mid-feature.** Someone else needs to know what is done, what is next, and what was deliberately deferred — without a handover meeting.
- **A feature from three months ago needs one more work item.** Nobody remembers the decisions. The spec recorded them; this surfaces them.

---

## Step 0 — Resolve the workspace

Standard resolution: the cwd is the workspace if `./CLAUDE.md` matches `grep -qE "AI Forging( forge)? workspace"` and `./docs/features/` exists. Otherwise read `active_workspace` from `~/.claude/aiforging.json` (opt-in — it may not exist). Otherwise ask.

If `docs/features/` holds no feature folders, say so and point at `/aiforging:forge` rather than presenting an empty list.

---

## Step 1 — Refresh the feature index

`docs/features/INDEX.md` is a generated table of every feature: name, status, last activity, and a one-line summary. It is **derived, never authored** — nothing in it is a source of truth, so it can always be rebuilt from the feature folders and git.

Rebuild the rows before presenting anything. Cheap, and it means a folder someone created by hand shows up like any other.

For each directory under `docs/features/`:

| Column | Derived from |
|---|---|
| **Feature** | the directory name |
| **Status** | checked vs total `- [ ]` / `- [x]` boxes across `plan.md` (flat) or every `NN-*/plan.md` (nested). No `plan.md` yet → `spec only`. No boxes → `no slices` |
| **Last activity** | `git log -1 --format='%ad %an' --date=short -- docs/features/<name>/` |
| **Summary** | the first non-empty prose line of the `## Summary` section of `spec.md` (or `overview.md` for a nested feature), truncated to about 100 characters |

```bash
# status
grep -rho '^- \[[ x]\]' docs/features/<name>/ | sort | uniq -c
# last activity, and who
git log -1 --format='%ad  %an' --date=short -- docs/features/<name>/
```

**Deriving status from checkboxes is deliberate.** It adds no field anyone has to remember to update, and it cannot disagree with the plan — because it *is* the plan. A status field maintained by hand would be wrong within a month, and a stale status is worse than none: it makes someone skip a feature that actually needed them.

Write the refreshed table to `docs/features/INDEX.md` using the template at `${CLAUDE_PLUGIN_ROOT}/templates/features-INDEX.md` if the file does not exist yet. Mention that you refreshed it; it is a tracked file and will appear in `git status`.

---

## Step 2 — Choose the feature

**With an argument**, match it against directory names: exact first, then prefix, then substring, then token overlap. One match, proceed. Several, present them and ask — never guess between two features, because orienting someone into the wrong one wastes more time than asking.

**With no argument**, present the index, most recently active first, and ask which. Say what the status column means so `3/11` is not mistaken for a score.

Group the list if it is long: **in progress** (some boxes checked, some not), **not started** (`spec only`, or no boxes checked), **complete** (all checked). Most resumes target the first group; a feature with everything checked is usually being extended rather than continued, and that distinction changes what the person needs from you.

---

## Step 3 — Read the feature

Read what exists, in this order. Skip what does not exist; say which were absent rather than silently ignoring them.

1. **`overview.md`** (nested only) — the work items and their dependency order.
2. **`spec.md`** — the intent. **Read the whole thing.** This is the one file that carries *why*, and why is exactly what a person picking up cold does not have.
3. **`plan.md`** — the slices. Note which are checked, which are not, and which carry an unsatisfied `[gate: ...]`.
4. **`notes.md`** — dead ends, open questions, decisions that never made it into the spec. Often the highest-value file on a resume and the one nobody thinks to open.
5. **`testing.md`** — unchecked QA items, and anything marked 👤.
6. **`ai-testing/*/escalations.md`** and **`ai-reviews/*/escalations.md`** — findings that were real, deliberately not acted on, and are still open. **These are the most likely thing to have been lost.** An escalation exists precisely because someone declined to act on it, which is also why nobody remembers it.
7. **`summary.md`** (if present) — the post-implementation snapshot.

Also get the human history, which no file records:

```bash
git log --format='%ad  %an  %s' --date=short -- docs/features/<name>/ | head -20
```

Who worked on this, when they stopped, and what they said they were doing.

---

## Step 4 — Report, then stop

Report in this order — most-actionable first, because the reader is deciding whether to pick this up at all:

1. **What the feature is**, in two or three sentences, from the spec. Not a paraphrase of the title.
2. **Where it stands.** Checked/total, and *which* slices are outstanding by name. A count alone tells nobody what is left.
3. **What is next**, concretely: the first unchecked slice, its target repo, and whether a `[gate: ...]` blocks it.
4. **What is open and easy to miss** — unchecked `testing.md` items, and every escalation, quoted rather than referenced. If an escalation exists, say so before anything else in this section; it is the item most likely to have been dropped.
5. **Decisions worth knowing**, from the spec's architectural-decisions section and from `notes.md`. Especially anything deferred deliberately — a resumer who does not know something was deliberate will "fix" it.
6. **Who last touched it and when.** If it was someone else, say so plainly. If the last activity was months ago, say that too: the surrounding codebase has moved, and the plan's file paths may no longer be accurate.
7. **What you did not find** — missing `testing.md`, no `plan.md` yet, an empty `notes.md`. Absence is information.

Then **stop and ask what they want to do.** Do not dispatch a slice, do not check out a branch, do not start writing. The person now has what they need to decide, and the decision is theirs.

Offer the obvious next moves without taking them:

> Where would you like to start? The usual next steps are dispatching Slice 7 (backend), re-reading the spec against current requirements before continuing, or — if the plan has gone stale — updating it before anything dispatches.

**If the feature is complete and the person wants to extend it**, that is `/aiforging:new-feature` with the extend flow, which adds a new work item rather than reopening a finished one. Say so and hand off.

---

## Working on a feature someone else started

Two rules, both learned the expensive way:

**Do not silently rewrite another engineer's plan.** If the approach now looks wrong, say so and let a human decide. The plan encodes decisions whose reasons may not be written down anywhere, and a plan quietly rewritten during a handoff destroys the record of what was agreed without replacing it.

**A stale plan is a conversation, not a cleanup task.** If the last activity was months ago, the target repos have moved and the plan's paths, module names and test suites may no longer resolve. Check the paths in the first unchecked slice actually exist, and report it if they do not — that is a finding about the plan, not an excuse to rewrite it.

---

## Relationship to other AI Forging pieces

- **`/aiforging:forge`** (`new-feature`) starts a feature. This picks one up. They are the two entry points to the workflow — everything else runs inside a feature that already exists.
- **`superpowers:executing-plans`** is what actually dispatches a slice, after the human decides to continue.
- **`hammer-refactor`**, **`browser-testing`**, **`review-loop`** all operate on a feature this may have just oriented you into.
- **The feature index** (`docs/features/INDEX.md`) is generated here and read here. Nothing else depends on it, so it can be deleted at any time and will be rebuilt.

---

## A note on the paths in this file

Paths like `docs/features/<name>/spec.md` are relative to the **forge workspace**, not to a target repo. In a multi-repo setup the workspace is a separate directory; in a monorepo or single-repo setup the workspace is the repo root. Step 0 resolves which.

---

## Completion message

State, every time:

1. Which feature you oriented into, and that the index was refreshed.
2. Status, outstanding slices by name, and the concrete next step.
3. **Every open escalation, quoted** — not referenced by path.
4. Who last touched it and when.
5. **That you changed nothing** and are waiting for a decision.
