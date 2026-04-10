<!--
  This file is copied verbatim into <forge-workspace>/docs/features/README.md
  during `/aiforging:setup` phase A (init-workspace).

  Source of truth: conventions/features/README.md in the aiforging plugin repo.
  If you update this template, update the canonical convention doc too.
-->

# Feature Folder Convention

> **Where cross-repo feature work lives.** Each feature you drive through the AI Forging flow gets exactly one folder at `docs/features/<feature-name>/` in this workspace. This is where spec.md, plan.md, and any notes for that feature live — centrally, across however many target repos the feature touches.

## Folder layout

```
docs/features/
├── README.md                   # this file
└── <feature-name>/             # one folder per feature; kebab-case names
    ├── spec.md                 # WHAT and WHY
    ├── plan.md                 # HOW, in subagent-friendly slices
    └── notes.md                # optional, free-form notes
```

## spec.md — the WHAT and WHY

Produced by `superpowers:brainstorming` followed by the spec phase of `superpowers:writing-plans`. The spec should answer:

- **What problem are we solving, in the user's words?**
- **Who is affected, and what changes for them when this ships?**
- **What is explicitly out of scope?**
- **What existing code will this touch?** (List the affected repos and subsystems.)
- **What architectural decisions are we making or deferring?**

## plan.md — the HOW

Produced by the plan phase of `superpowers:writing-plans` using the AI Forging **slice format**. Each slice is small enough for one fresh-context subagent to complete.

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

## Hard rules

- **Feature folders are kebab-case.** `invoice-tax-calculation`, not `InvoiceTaxCalc`.
- **Feature folders are single-purpose.** If a feature grows two heads, split it.
- **Feature folders are stable once created.** If the name was wrong, add a new folder — don't rename. History matters.
- **No source code in feature folders.** Source code lives in target repos, reached via `additionalDirectories`.
- **Fire before Hammer, always.** A `[hammer]` slice never runs before its related `[fire]` slices are green.
- **Human gates are human gates.** Slices marked `[gate: ...]` require explicit user approval before dispatching to a subagent.

For the full canonical version of this convention (including lifecycle, what NOT to put in feature folders, and the relationship to the other AI Forging stages), see the aiforging plugin's `conventions/features/README.md`.
