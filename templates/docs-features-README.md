<!--
  This file is copied verbatim into <forge-workspace>/docs/features/README.md
  during `/aiforging:setup` phase A (init-workspace).

  Source of truth: conventions/features/README.md in the aiforging plugin repo.
  If you update this template, update the canonical convention doc too.
-->

# Feature Folder Convention

> **Where cross-repo feature work lives.** Each feature you drive through the AI Forging flow gets exactly one folder at `docs/features/<feature-name>/` in this workspace. This is where spec.md, plan.md, and any notes for that feature live — centrally, across however many target repos the feature touches.

## Step 0 — scope determination

Before creating the folder, decide the scope. A **single-target** feature touches one onboarded repo — one spec, one plan, one dispatch chain. A **multi-target** feature touches two or more onboarded repos — one spec, one plan, but the plan generator must read *every* affected repo's `.aiforging/CLAUDE.md` and `.aiforging/architecture/` before writing the plan.

## Folder layout — two shapes

Most features use the **flat** shape (one spec, one plan). Features with multiple independently-dispatchable work items use the **nested** shape with numbered subfolders.

### Flat shape (default)

```
docs/features/
├── README.md                   # this file
└── <feature-name>/             # one folder per feature; kebab-case names
    ├── spec.md                 # WHAT and WHY
    ├── plan.md                 # HOW, in subagent-friendly slices
    └── notes.md                # optional, free-form notes
```

### Nested shape (multi-work-item features)

```
docs/features/<feature-name>/
├── overview.md                 # WHAT and WHY at the feature level; lists work items and order
├── 01-<work-item-name>/
│   ├── spec.md                 # WHAT and WHY for this work item
│   └── plan.md                 # HOW for this work item
├── 02-<work-item-name>/
│   ├── spec.md
│   └── plan.md
└── notes.md                    # optional, feature-level free-form notes
```

Work items use a numeric two-digit prefix (`01-`, `02-`, …) that reflects logical dependency order. Don't nest if there's only one work item; don't flatten if there are several.

### When NOT to use nested — the layer-split anti-pattern

**Do not split a cohesive feature into nested work items along repo boundaries.** A feature like "tax-inclusive pricing" touching a backend API and a frontend app should NOT become `01-backend-tax-model/` and `02-frontend-tax-display/` — two separate specs can drift apart, and the API contract may not match the frontend's needs by the time the second work item starts.

The correct shape is **flat**: one spec covering holistic behavior across both repos, one plan with per-slice target-repo tags and explicit cross-repo ordering. Use `[gate: contract]` on the slice that locks the API shape so the human approves it before frontend slices dispatch.

**Nested is for sequential phases, not layer splits** — e.g., a data migration where Phase 1 is dual-write and Phase 2 is cutover. Each phase has its own timeline, approval gate, and rollback story.

## Planning workflow (four steps)

1. **Create spec.md from the initial prompt.** Draft a **Summary** section capturing the user's ask in your own words. Stop. Confirm the Summary with the user before writing anything else. This is a hard checkpoint.
2. **Grouped clarifying questions.** Interview in themed rounds of 3–5 questions each, with a heading per round. Skip questions whose answer is obvious from the affected repos' `.aiforging/architecture/`. Flag cross-repo contracts, schema changes, and new domain modules as architectural decisions so the plan can attach a `[gate: architecture]` later.
3. **Architecture review.** Before writing plan.md, read the `.aiforging/architecture/` conventions and root `CLAUDE.md` of **every** affected target repo. Also consult each target's `.aiforging/patterns/`, `.aiforging/anti-patterns/`, and `.aiforging/ANALYSIS.md` if present. This is non-negotiable: plans with incorrect paths produce incorrectly-placed code across every subagent that dispatches against them.
4. **Write plan.md in the slice format.** Every Fire sequence must end with a closing `[hammer]` slice that dispatches `hammer-refactor` against the changed files. Human approval is required before any slice dispatches.

## spec.md — the WHAT and WHY

Produced by `superpowers:brainstorming` followed by the spec phase of `superpowers:writing-plans`. The spec should answer:

- **Summary (user's initial prompt in your words).** Locked at Step 1.
- **What problem are we solving, in the user's words?**
- **Who is affected, and what changes for them when this ships?**
- **What is explicitly out of scope?**
- **What existing code will this touch?** (List the affected repos and subsystems.)
- **What architectural decisions are we making or deferring?**

## plan.md — the HOW

Produced by the plan phase of `superpowers:writing-plans` using the AI Forging **slice format**. Each slice is small enough for one fresh-context subagent to complete. Every Fire sequence ends with a closing `[hammer]` slice.

### Slice template

```markdown
### Slice N — <short imperative title>

- **Stage**: [fire] | [hammer] | [tempering]
- **Target repo**: <repo name as registered in additionalDirectories>
- **Touches**: <path/to/file.ext> (or "new file: <path>")
- **Why**: <one sentence>
- **Test**: <test name or file; for Fire, the test we will write; for Hammer, the suite that must stay green>
- **Pattern reference** (Hammer only): <.aiforging/patterns/name.md or .aiforging/anti-patterns/name.md>
- **Gates**: none | [gate: architecture] | [gate: schema] | [gate: contract]
- **Prompt for subagent**:
  > <the actual prompt to hand to a fresh-context subagent>
```

## Living documents

spec.md and plan.md evolve as the feature is implemented. Rules:

- **Route every change to the right document.** Intent goes in spec, execution goes in plan, everything else goes in notes. If user-visible behavior changes in any way, update the spec first.
- **Preserve completed checkboxes.** Never rewrite a slice that already dispatched and finished — add a follow-up slice instead. The plan is also a history. Subagents check off their own tasks; the parent conversation never unchecks a completed box or fabricates a check.
- **Proactive spec updates for visible behavior changes.** If mid-implementation you notice the behavior is drifting from the spec, stop and update the spec before continuing. Do not push the change straight into the plan. The human approved the spec and deserves a chance to re-approve.

## Hard rules

- **Feature folders are kebab-case.** `invoice-tax-calculation`, not `InvoiceTaxCalc`.
- **Work items are numbered then kebab-case.** `01-backend-schema`, `02-api-endpoints`.
- **Feature folders are single-purpose.** If a feature grows two heads, split it (or switch to the nested shape).
- **Feature folders are stable once created.** If the name was wrong, add a new folder — don't rename. History matters.
- **No source code in feature folders.** Source code lives in target repos, reached via `additionalDirectories`.
- **Fire before Hammer, always.** A `[hammer]` slice never runs before its related `[fire]` slices are green.
- **Every Fire sequence ends with a closing `[hammer]` slice.** No sequence is "done" until the Hammer pass has run against the changed files.
- **Human gates are human gates.** Slices marked `[gate: ...]` require explicit user approval before dispatching to a subagent.

For the full canonical version of this convention (including lifecycle, architecture-review rationale, and the relationship to the other AI Forging stages), see the aiforging plugin's `conventions/features/README.md`.
