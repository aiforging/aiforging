# Feature Folder Convention

> **Where cross-repo feature work lives.** Each feature you drive through the AI Forging flow gets exactly one folder at `docs/features/<feature-name>/` in the **forge workspace**. This is where spec.md, plan.md, and any notes for that feature live — centrally, across however many target repos the feature touches.

## Why central, not per-repo

AI Forging is designed for the reality that most features touch more than one repo: a backend API + a frontend app, a domain service + a worker + a schema migration, etc. If each repo keeps its own `PLAN.md` for the same feature, you end up with fragmented plans that can't reason about the boundary between them.

Instead: the **forge workspace** (a user-chosen directory like `~/forge`, bootstrapped by `/aiforging:setup`) is the central hub. Target repos are reached via `permissions.additionalDirectories`. Feature work lives in `docs/features/<name>/` at the hub. Per-repo `.aiforging/` directories hold repo-specific concerns (analysis snapshots, the seeded pattern library, the hammer-refactor skill) — but the *plan* that spans the repos lives at the hub.

## Step 0 — scope determination (always first)

Before creating the folder, decide the scope of the feature. The answer shapes everything downstream — the folder layout, the number of plans, the dispatch strategy, and the set of target `.aiforging/CLAUDE.md` files that must be read before writing the plan.

- **Single-target feature.** Only one onboarded repo is affected. One spec, one plan, one dispatch chain.
- **Multi-target feature.** Two or more onboarded repos are affected (e.g., a backend API + a frontend app; a domain service + a migration + a worker). One spec that covers the whole feature, but the plan must call out which slices land in which repo, and the plan generator must read every affected repo's `.aiforging/CLAUDE.md` before writing the plan. See "Planning workflow" below.

If the scope is ambiguous at feature-creation time, start single-target and split later. Feature folders are stable once created (see "Naming rules"), so it is better to add a new folder than to rename.

## Folder layout — two shapes

Most features are small enough to live in a **flat** folder: one spec, one plan, one notes file. Larger features with multiple independently-dispatchable work items use the **nested** shape: an overview at the top, and numbered work-item subfolders each with their own spec and plan.

Pick the shape that matches the feature. Do not nest a feature that only has one work item — the overview becomes noise. Do not flatten a feature that has several logically independent work items — the plan becomes an unreadable linear scroll.

### Flat shape (default)

Use this for features with a single work item that fits in one plan. This is the common case.

```
<forge-workspace>/
└── docs/
    └── features/
        ├── README.md                 # this file, copied in during workspace init
        └── <feature-name>/           # one folder per feature; kebab-case names
            ├── spec.md               # WHAT and WHY
            ├── plan.md               # HOW, in subagent-friendly slices
            ├── testing.md            # human QA checklist — required if the feature has a UI surface
            ├── notes.md              # optional, free-form notes during execution
            ├── ai-testing/           # created by /aiforging:browser-testing — numbered run records
            └── ai-reviews/           # created by /aiforging:review-loop — numbered round records
```

### Nested shape (multi-work-item features)

Use this when a feature decomposes into two or more work items that can be planned (and often dispatched) independently. Each work item gets its own `NN-<item-name>/` subfolder with its own spec and plan. The feature-level `overview.md` is the umbrella document that ties the work items together.

```
<forge-workspace>/
└── docs/
    └── features/
        └── <feature-name>/
            ├── overview.md           # WHAT and WHY at the feature level; lists work items and their order
            ├── testing.md            # ONE feature-level QA checklist, ordered by work item
            ├── summary.md            # optional; written AFTER implementation, for 3+ work items
            ├── 01-<work-item-name>/
            │   ├── spec.md           # WHAT and WHY for this work item
            │   └── plan.md           # HOW for this work item
            ├── 02-<work-item-name>/
            │   ├── spec.md
            │   └── plan.md
            ├── notes.md              # optional, feature-level free-form notes
            ├── ai-testing/           # created by /aiforging:browser-testing
            └── ai-reviews/           # created by /aiforging:review-loop
```

Work items are **numbered** with a two-digit prefix (`01-`, `02-`, …) to preserve dispatch order in directory listings. Work items are **kebab-case** after the prefix (`01-backend-schema`, `02-api-endpoints`, `03-frontend-form`). Numbers reflect logical dependency order, not arbitrary sequence — if `02` can't start until `01` is green, that's what the numbering should communicate.

Feature names are kebab-case and as concrete as possible. Prefer `invoice-tax-calculation` over `taxes`. Prefer `customer-import-csv-v2` over `import`.

### When NOT to use nested — the layer-split anti-pattern

**Do not split a cohesive feature into nested work items along repo boundaries.** This is the most common misuse of the nested shape.

Example of the anti-pattern: a feature like "tax-inclusive pricing" that touches a backend API and a frontend app gets decomposed as `01-backend-tax-model/` and `02-frontend-tax-display/`, each with its own spec and plan. This is wrong because the backend API contract and the frontend's expectations are tightly coupled — two separate specs can drift apart, and by the time the frontend work item starts, the API shape may not match what the frontend needs.

The correct shape is **flat**: one spec that describes the holistic behavior across both repos, one plan whose slices are tagged with their target repo and ordered so that cross-repo dependencies are explicit. Use `[gate: contract]` on the slice that locks in the API shape, so the human approves the contract before any frontend slice dispatches. The plan might look like:

```
Slice 1 [fire] target:backend — Domain model for tax calculation
Slice 2 [fire] target:backend — API endpoint exposing tax-inclusive prices
Slice 3 [gate: contract] — Human approves the API response shape
Slice 4 [hammer] target:backend — Hammer pass on Slices 1–2
Slice 5 [fire] target:frontend — Price display component consuming the new endpoint
Slice 6 [fire] target:frontend — Integration tests against the real API
Slice 7 [hammer] target:frontend — Hammer pass on Slices 5–6
```

**Nested is for sequential phases, not layer splits.** Use nested work items when a feature has genuinely independent phases that are each separately plannable and reviewable — for example, a data migration where Phase 1 is a read-only dual-write and Phase 2 is the cutover that drops the old path. Each phase has its own timeline, its own approval gate, and its own rollback story. That's what the numbered work-item folders are for.

## The files in a feature folder, and what each one is for

Six documents: two are always present, four are conditional. Each has exactly one job; when a document starts doing a second job, that is the signal to split it.

| File | Required? | Written when | Job |
|---|---|---|---|
| `spec.md` | always | before planning, living | **WHAT and WHY.** The thing the human approves. |
| `plan.md` | always | after the spec is locked, living | **HOW**, in subagent-dispatchable slices. |
| `overview.md` | nested shape only | when the second work item is scoped | The umbrella: work items, their order, and the dependencies between them. |
| `testing.md` | **whenever the feature has a UI surface** | alongside the plan, before implementation finishes | **A human QA checklist.** Concrete steps a person clicks through in the running app. |
| `summary.md` | optional; 3+ work items | *after* implementation is complete | An implementation snapshot — what got built, what was deferred, architecture highlights. |
| `notes.md` | optional | any time | Everything that would clutter the other five. |

Two directories may also appear, both machine-written and both numbered so runs accumulate rather than overwrite: `ai-testing/NN/` from `/aiforging:browser-testing` and `ai-reviews/NN/` from `/aiforging:review-loop`. Neither is hand-edited.

### `overview.md` — only when there are multiple work items

A feature with one work item does not get an overview; the spec already is one, and a second document that restates it is noise that goes stale. The moment a second work item is scoped, the overview earns its place, because there is now something no single work item's spec can hold: **the order, and what blocks what.**

Keep it to three things: the feature-level summary, the numbered list of work items with a line each, and the dependency notes. Everything else belongs in a work item's own spec.

### `testing.md` — required for every feature with a UI surface

**A UI-driven QA checklist: concrete steps a human clicks through in the running app, written as checkboxes.** Not a test plan, not a description of the automated suite — the things a person does with a mouse and a keyboard that no unit test covers.

Cover three things, in this order:

1. **Access and gating** — who can reach this, and confirmation that the people who should not, cannot.
2. **The happy path** — the reason the feature exists, walked end to end.
3. **Key edge cases** — the empty state, the boundary, the permission denial, the thing that fails.

For a nested feature (3+ work items), there is still exactly **one** `testing.md` at the feature level, with the checklist ordered by work item in dependency order. One checklist that walks the feature the way a user actually meets it beats five checklists nobody opens.

**Who may skip it:** research-only work items, and purely internal or pipeline changes with no UI surface — a queue consumer, a scheduled import, a refactor with no visible behavior. Skipping is a decision, so say so in the spec rather than silently omitting the file.

**Write it before implementation is finished, not after.** A checklist written after the fact describes what was built; a checklist written from the spec describes what was *supposed* to be built, and the difference between those two is exactly the bug you are looking for.

`testing.md` is also the input to `/aiforging:browser-testing`, which walks the delegable items in a real browser, marks the ones only a human can judge, and reports what diverged without fixing anything. That skill **refuses to run without this file** and will not invent a checklist — a run against a guessed checklist tests whatever the machine happened to imagine.

#### Shape

```markdown
# Testing — <feature name>

> 👤 = human judgement required; a machine cannot produce a verdict you would believe.

## Access and gating
- [ ] A user without `<permission>` gets a 403 on `/the/route` and sees no nav entry
- [ ] A user with `<permission>` reaches the page

## Happy path
- [ ] Create a <thing> with valid input; it appears in the list with the right totals
- [ ] 👤 The confirmation screen reads clearly to someone who did not build this

## Edge cases
- [ ] Empty state renders with the "no results" copy, not a blank table
- [ ] Submitting with `<field>` blank shows an inline error and does not save
```

### `summary.md` — after the fact, for big features only

For features with three or more work items, an implementation snapshot written **once implementation is complete**: a table of the work items and their state, what was actually built, what was deferred and why, and the two or three architecture decisions a future reader would otherwise have to reconstruct from the plan's checkbox history.

It is optional because it is a convenience, not a control. Its value is entirely to the person who comes back in six months — which is why writing it *before* the work is done defeats the purpose. Do not create it preemptively; an empty `summary.md` is worse than no `summary.md`.

## Planning workflow

Producing spec.md and plan.md is not a one-shot prompt. It is a four-step interactive workflow that keeps the human in the loop at every decision point. The steps below apply whether you are using `superpowers:brainstorming` + `superpowers:writing-plans` (recommended) or driving the conversation manually.

### Step 1 — create spec.md from the initial prompt

When a feature is first mentioned, create the feature folder (flat or nested, per scope determination), drop a spec.md skeleton, and draft a **Summary** section capturing the user's initial prompt in your own words. Do not write the rest of the spec yet. Stop and confirm the summary with the user. This prevents the spec from drifting off the actual ask in the first five minutes.

The Summary section is a hard checkpoint. Do not proceed to Step 2 until the user has agreed that the summary reflects what they want.

### Step 2 — grouped clarifying questions, not an interrogation

Fill the rest of the spec through a conversation, but group questions into **themed rounds of 3–5 questions each** rather than asking one open-ended question at a time or twenty at once. Give each round a themed heading (e.g., "User experience", "Data model", "Out-of-scope boundaries") so the user can answer each round as a batch.

Rules for the interview:

- Never ask open-ended "what do you want?" questions once the Summary is locked. Every question should be specific enough that a one-line answer resolves it.
- Skip questions whose answer is obvious from the architecture conventions in the affected target repos' `.aiforging/architecture/` directories. Check first, then ask only what remains.
- Surface architectural decisions explicitly. If a question would lock in a cross-repo contract, a schema change, or a new domain module, flag it as an architectural decision in the spec so the plan can attach a `[gate: architecture]` later.
- When the spec is complete enough to plan against, stop the interview and confirm with the user before moving to Step 3.

### Step 3 — architecture review against the target repos

Before writing plan.md, the plan generator **must** read the `.aiforging/architecture/` conventions and the root `CLAUDE.md` of every affected target repo. For multi-target features, this means reading *every* affected target, not just the first one. This is a hard rule for one reason: **plans with incorrect paths produce incorrectly-placed code across every subagent that dispatches against them.** A subagent has fresh context. It will trust the plan's paths. If the plan puts the controller in `src/Http/` when the target's convention is `src/Controller/`, every dispatched slice lands in the wrong place.

Artifacts the plan generator must consult before writing plan.md:

- The affected target repo's root `CLAUDE.md` (for its own conventions and guardrails).
- The affected target repo's `.aiforging/architecture/` directory (folder layout, controllers, repositories, DTOs, naming).
- The affected target repo's `.aiforging/patterns/` and `.aiforging/anti-patterns/` directories (so the plan can point Hammer slices at the right pattern files).
- The affected target repo's `.aiforging/ANALYSIS.md` if present (so the plan can avoid proposing slices that conflict with known findings).

### Step 4 — write plan.md in the slice format

Once Steps 1–3 are done, produce plan.md using the slice template below. Every Fire sequence (one or more `[fire]` slices that together deliver a behavioral change) must end with a `[hammer]` slice that reminds the subagent to run `hammer-refactor` against the changed files before the sequence is considered complete. The plan is the only place that enforces this; the subagent prompt will trust the plan.

**The plan must also name the feature's test suite and repeat the scoped-run rule.** See "The plan carries the test-scoping rule" below. This is not decoration: the plan is the only artifact every fresh-context subagent reads, so it is the only place the rule reliably lands.

**Decide `testing.md` here too.** Step 4 is where you determine whether the feature has a UI surface, and therefore whether `testing.md` is required. If it is, draft it from the spec now — before implementation, so it describes what was *supposed* to be built. If it is not (research-only, or a purely internal change with no visible behavior), record that decision in the spec rather than silently omitting the file.

Human approval is required at the end of Step 4 before any slice dispatches. Any slice marked `[gate: ...]` requires explicit re-approval at dispatch time even if the plan as a whole was approved.

## spec.md — the WHAT and WHY

Produced by `superpowers:brainstorming` followed by the spec phase of `superpowers:writing-plans`. AI Forging does not redefine this format — we use superpowers' output directly. The spec should answer:

- **Summary (user's initial prompt in your words).** Locked at Step 1.
- **What problem are we solving, in the user's words?**
- **Who is affected, and what changes for them when this ships?**
- **What is explicitly out of scope?**
- **What existing code will this touch?** (List the affected repos and the rough subsystems within each.)
- **What architectural decisions are we making or deferring?**

Keep it human-readable. The spec is for the humans who will approve the plan, not just for Claude.

## plan.md — the HOW, structured for subagent dispatch

Produced by the plan phase of `superpowers:writing-plans`. This is where AI Forging has strong opinions on top of the base superpowers format, because the plan is the input to `subagent-driven-development` and `hammer-refactor`.

A good AI Forging plan:

1. **Is broken into slices small enough that one fresh-context subagent can complete each slice** without needing to load half the codebase. A slice is typically one file, one function, one test, or one refactor pass — rarely more.
2. **Marks each slice with its stage.** `[fire]` for Fire (write a failing test, then pass it), `[hammer]` for Hammer (refactor against a specific pattern/anti-pattern), `[tempering]` for Tempering (capture a new pattern to the library).
3. **Names the target repo for each slice.** Because the plan lives at the hub and spans multiple repos, every slice must be unambiguous about where the code change lands.
4. **Names the feature's test suite once, at the top, with its exact run command.** One suite per feature — not one per work item. Every slice runs that suite and only that suite.
5. **Lists the test(s) that must be green before the next slice dispatches.** Fire slices name the test they add; Hammer slices name the feature suite that must stay green.
6. **Lists explicit human gates.** Any slice that touches a public API, a schema, a data migration, or a cross-repo contract is marked `[gate: architecture]` and will not dispatch without user approval.
7. **Ends every Fire sequence with a closing `[hammer]` slice.** The closing slice dispatches `hammer-refactor` against the files touched by the Fire sequence. This is non-negotiable: no Fire sequence is "done" until the Hammer pass has run.

### Minimal slice template

Every slice in plan.md should look roughly like this:

```markdown
### Slice N — <short imperative title>

- **Stage**: [fire] | [hammer] | [tempering]
- **Target repo**: <repo name as registered in additionalDirectories>
- **Touches**: <path/to/file.ext> (or "new file: <path>")
- **Why**: <one sentence>
- **Test**: <for Fire, the test we will write; for Hammer, what must stay green — always inside the feature suite named at the top of this plan>
- **Pattern reference** (Hammer only): <.aiforging/patterns/name.md or .aiforging/anti-patterns/name.md>
- **Gates**: none | [gate: architecture] | [gate: schema] | [gate: contract]
- **Prompt for subagent**:
  > <the actual prompt to hand to a fresh-context subagent, including any file references>
  > Run ONLY the feature suite `<suite-name>` via `<run command>`. NEVER run the full
  > repository suite. If you believe it must run, stop and say so instead of running it.
```

The "Prompt for subagent" field is deliberately explicit. When `hammer-refactor` or `superpowers:executing-plans` walks this plan and dispatches, it can literally copy that block into the subagent's task. No guesswork about what the slice was supposed to mean.

### The plan carries the test-scoping rule

Every plan opens with a block like this, before Slice 1:

```markdown
## Test suite

- **Name**: `invoice-tax`
- **Run**: `./bin/phpunit --testsuite invoice-tax`
- **Registered in**: `phpunit.xml.dist` (target repo: backend)

Every slice in this plan runs ONLY this suite. No slice, and no subagent dispatched from a
slice, runs the full repository suite — not to confirm a slice, not at the end of a sequence,
not to make sure nothing broke. If you believe the full suite must run, stop and ask.
The human runs the full suite themselves, once, after implementation is complete.
```

One suite per **feature**, not per work item. Work item 2 adds its tests to the suite work item 1 registered; by the end, that one command exercises the whole feature. Register it before the first test is written.

Every slice's "Prompt for subagent" repeats the scoped-run instruction verbatim, even though it is already in this block. That looks redundant and is not: a fresh-context subagent reads the slice it was pointed at, and "run everything to prove I'm done" is the strongest default an agent has. It must be countermanded where the agent cannot miss it.

**This scoping trades a real risk for a fast loop, deliberately.** A change made for this feature can break another one, and no scoped run will catch it. That is why the plan's final step — after every work item, every Fire sequence, and every Hammer slice — is not a slice at all but a **handoff**: the AI tells the human, in words, that every run was scoped, gives them the full-suite command, and asks them to run it before opening a PR. Put that handoff in the plan as an explicit closing item so it cannot be forgotten in the relief of finishing.

Full detail: `conventions/tdd/feature-test-suite.md`.

## Living documents

spec.md and plan.md are **living documents** that evolve as the feature is implemented. They are not write-once artifacts. But "living" does not mean "free-for-all" — the rules below keep them trustworthy.

### Route every change to the right document

When something changes mid-implementation, it goes to exactly one of spec, plan, or notes:

- **Spec.md** — changes to *intent*: what the feature does, who it affects, what's in or out of scope, what architectural decisions have been made. If the user's visible behavior changes in any way, the spec must be updated.
- **Plan.md** — changes to *execution*: new slices, revised slice prompts, reordering, new test references, new gates. Completed slices are never removed from the plan; they stay as a checkbox history of what was done.
- **Notes.md** — everything else: dead ends, discoveries, open questions, references to conversations or PRs. Anything that would clutter the spec or plan goes here.

When in doubt, update the spec first, then let the plan catch up. The spec is the source of truth about intent; the plan is a derivative of the spec.

### Preserve completed checkboxes

When plan.md is edited mid-flight, **completed checkboxes must be preserved as completed**. Do not rewrite a slice that already dispatched and finished — add a follow-up slice instead. The plan is also a history of what got done and in what order; destroying that history destroys the ability to reason about why the codebase looks the way it does now.

Subagents check off their own tasks as they complete them. The parent conversation never unchecks a box that a subagent checked, and never fabricates a check on a box a subagent didn't explicitly complete.

### Proactive spec updates for visible behavior changes

If you notice, mid-implementation, that the feature's visible behavior differs from what the spec describes — even by a small amount — stop and update the spec before continuing. Do not push the change straight into the plan. The spec is what the human approved; if the behavior diverges, the human needs a chance to re-approve.

This rule is deliberately conservative. It is fine to be over-cautious here. A one-minute spec update is cheap; a silent behavior drift that surfaces in code review is expensive.

## notes.md — optional, free-form

During execution, things will surface that don't belong in the spec or the plan: things we learned, dead ends, questions for the team, references to conversations or PRs. Put them here. The notes file is not structured. It exists so the spec and plan stay clean while still giving the feature a place for all the messy context.

## Lifecycle

0. **Or resume an existing one.** `/aiforging:resume` is the other entry point, and on a shared workspace it is the more common one — it reads a feature's spec, plan, notes and open escalations and reports where things stand, whether you paused it last week or a teammate started it in March. `docs/features/INDEX.md` is the generated table it works from.
1. **New feature.** User (or `/aiforging:new-feature`, aliased `/aiforging:forge`) determines scope, picks flat vs nested, and creates `docs/features/<name>/` with a spec.md skeleton and Summary section. Confirm Summary before proceeding.
2. **Spec phase.** Run Steps 1–2 of the Planning workflow: grouped clarifying questions, themed rounds, architecture-aware. Human approval of the completed spec.
3. **Architecture review.** Step 3: read every affected target's `.aiforging/` and root `CLAUDE.md` before writing plan.md.
4. **Plan phase.** Step 4: produce plan.md in the slice format, with a closing `[hammer]` slice at the end of every Fire sequence. Human approval at any `[gate: ...]` slice.
5. **Execute.** Dispatch slices via `superpowers:executing-plans` for Fire work and via `aiforging:hammer-refactor` for Hammer work. Each slice goes to a fresh-context subagent. Subagents check off their own tasks in plan.md as they complete them. Every run is scoped to the feature's named test suite.
6. **Temper.** When the feature is done, any new patterns/anti-patterns discovered get written to the relevant target repo's `.aiforging/patterns/` or `.aiforging/anti-patterns/` as new `.md` files. One pattern per file. The library grows monotonically.
7. **Verify in the product — optional, and worth it whenever there is a UI.** Run `/aiforging:browser-testing` to walk `testing.md` in a real browser while you work the 👤 items yourself in parallel. It reports what diverged and fixes nothing; every finding is a conversation before it becomes work. Writes `ai-testing/NN/`.
8. **Review the diff — optional.** Once the product behaves, run `/aiforging:review-loop` for rounds of review → triage → fix across every implicated repo. Writes `ai-reviews/NN/`. **Deliberately after step 7:** a review loop can run to exhaustion on the diff while a behavioral defect — or a wrong decision — sits untouched in the most-used screen, and the cheapest moment to reverse a decision is before more work is built on it.
9. **Hand off the full suite.** Tell the human, in words, that every test run was scoped, give them the full-suite command, and let them run it. Then their own pass over `testing.md`, their own code review, and a PR. None of these are automated and none are optional.
10. **Summarize — optional, 3+ work items.** Write `summary.md` now that implementation is done: work items, what was built, what was deferred, architecture highlights.
11. **Archive.** The feature folder stays in `docs/features/` for historical reference. Do not delete it; do not rewrite it. Future work that builds on this feature links back to it.

## Hard rules

The non-negotiables, collected. Each is explained above; this is the checklist.

- **Feature folders are kebab-case**, single-purpose, and **stable once created.** If the name was wrong, add a new folder — history matters.
- **Work items are numbered then kebab-case** (`01-backend-schema`), in dependency order, and are **never renumbered.**
- **No source code in a feature folder.** Source lives in target repos.
- **Fire before Hammer, always.** A `[hammer]` slice never runs before its related `[fire]` slices are green.
- **Every Fire sequence ends with a closing `[hammer]` slice.** No sequence is "done" until the Hammer pass has run against the files it touched.
- **Human gates are human gates.** A slice marked `[gate: ...]` requires explicit approval before it dispatches, even if the plan as a whole was approved.
- **One named test suite per feature, and nothing else runs.** Never the full repository suite — not during Fire, not during Hammer, not to "make sure." Ask the human if you think it must run.
- **Always hand the full suite to the human at the end of implementation.** In words, every time, including when the feature was small.
- **`testing.md` is one per feature**, never one per work item, and it is written before implementation ends.
- **`summary.md` is written after implementation**, never before.
- **`ai-testing/` and `ai-reviews/` are numbered and append-only.** A re-run is a new folder.
- **Completed checkboxes are preserved.** Never rewrite a slice that already dispatched — add a follow-up slice.

## Naming rules

- Feature folders are **kebab-case**.
- Work-item subfolders in the nested shape are **numbered** (`01-`, `02-`, …) then **kebab-case**.
- Feature folders are **single-purpose**. If a feature grows two heads, split it into two folders (or, if the heads share a spec, switch to the nested shape with separate work items).
- Feature folders are **stable once created**. If the name was wrong, add a new folder; don't rename. History matters.
- Never put source code in a feature folder. Source code lives in target repos, reached via `additionalDirectories`. This folder is for the feature's documents and run records only.
- `testing.md` is **one per feature**, never one per work item — even in the nested shape. Order its checklist by work item in dependency order.
- `summary.md` is written **after** implementation, never before. An empty one is worse than none.
- `ai-testing/` and `ai-reviews/` are **numbered and append-only**. A re-run is a new folder; never overwrite an earlier run's record.

## What NOT to put here

- Source code. (Goes in target repos.)
- Committed secrets or credentials. (Obviously.)
- Per-repo architectural decisions that don't span repos. (Those belong in the target repo's `.aiforging/` or in an ADR inside that repo.)
- Scratch spec work for features you're still deciding whether to do. Use `notes.md` or a scratchpad elsewhere; only promote to a named feature folder when the work is committed.
