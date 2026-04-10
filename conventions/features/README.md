# Feature Folder Convention

> **Where cross-repo feature work lives.** Each feature you drive through the AI Forging flow gets exactly one folder at `docs/features/<feature-name>/` in the **forge workspace**. This is where spec.md, plan.md, and any notes for that feature live — centrally, across however many target repos the feature touches.

## Why central, not per-repo

AI Forging is designed for the reality that most features touch more than one repo: a backend API + a frontend app, a domain service + a worker + a schema migration, etc. If each repo keeps its own `PLAN.md` for the same feature, you end up with fragmented plans that can't reason about the boundary between them.

Instead: the **forge workspace** (a user-chosen directory like `~/forge`, bootstrapped by `/aiforging:setup`) is the central hub. Target repos are reached via `permissions.additionalDirectories`. Feature work lives in `docs/features/<name>/` at the hub. Per-repo `.aiforging/` directories hold repo-specific concerns (analysis snapshots, the seeded pattern library, the hammer-refactor skill) — but the *plan* that spans the repos lives at the hub.

## Folder layout

```
<forge-workspace>/
└── docs/
    └── features/
        ├── README.md                 # this file, copied in during workspace init
        └── <feature-name>/           # one folder per feature; kebab-case names
            ├── spec.md               # WHAT and WHY (brainstorming + superpowers writing-plans spec)
            ├── plan.md               # HOW (superpowers writing-plans output, subagent-friendly chunks)
            └── notes.md              # optional, free-form notes during execution
```

Feature names are kebab-case and as concrete as possible. Prefer `invoice-tax-calculation` over `taxes`. Prefer `customer-import-csv-v2` over `import`.

## spec.md — the WHAT and WHY

Produced by `superpowers:brainstorming` followed by the spec phase of `superpowers:writing-plans`. AI Forging does not redefine this format — we use superpowers' output directly. The spec should answer:

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
4. **Lists the test(s) that must be green before the next slice dispatches.** Fire slices name the test they add; Hammer slices name the test suite that must stay green.
5. **Lists explicit human gates.** Any slice that touches a public API, a schema, a data migration, or a cross-repo contract is marked `[gate: architecture]` and will not dispatch without user approval.

### Minimal slice template

Every slice in plan.md should look roughly like this:

```markdown
### Slice N — <short imperative title>

- **Stage**: [fire] | [hammer] | [tempering]
- **Target repo**: <repo name as registered in additionalDirectories>
- **Touches**: <path/to/file.ext> (or "new file: <path>")
- **Why**: <one sentence>
- **Test**: <test name or test file; for Fire, the test we will write; for Hammer, the suite that must stay green>
- **Pattern reference** (Hammer only): <.aiforging/patterns/name.md or .aiforging/anti-patterns/name.md>
- **Gates**: none | [gate: architecture] | [gate: schema] | [gate: contract]
- **Prompt for subagent**:
  > <the actual prompt to hand to a fresh-context subagent, including any file references>
```

The "Prompt for subagent" field is deliberately explicit. When `hammer-refactor` or `superpowers:executing-plans` walks this plan and dispatches, it can literally copy that block into the subagent's task. No guesswork about what the slice was supposed to mean.

## notes.md — optional, free-form

During execution, things will surface that don't belong in the spec or the plan: things we learned, dead ends, questions for the team, references to conversations or PRs. Put them here. The notes file is not structured. It exists so the spec and plan stay clean while still giving the feature a place for all the messy context.

## Lifecycle

1. **New feature.** User (or `/aiforging:new-feature`, future command) creates `docs/features/<name>/` with an empty or templated spec.md.
2. **Spec phase.** Run `superpowers:brainstorming` and then `superpowers:writing-plans` (spec phase) to fill in spec.md. Human approval.
3. **Plan phase.** Run `superpowers:writing-plans` (plan phase) with the AI Forging slice template above to produce plan.md. Human approval at any `[gate: ...]` slice.
4. **Execute.** Dispatch slices via `superpowers:executing-plans` for Fire work and via `aiforging:hammer-refactor` for Hammer work. Each slice goes to a fresh-context subagent.
5. **Temper.** When the feature is done, any new patterns/anti-patterns discovered get written to the relevant target repo's `.aiforging/patterns/` or `.aiforging/anti-patterns/` as new `.md` files. One pattern per file. The library grows monotonically.
6. **Archive.** The feature folder stays in `docs/features/` for historical reference. Do not delete it; do not rewrite it. Future work that builds on this feature links back to it.

## Naming rules

- Feature folders are **kebab-case**.
- Feature folders are **single-purpose**. If a feature grows two heads, split it into two folders.
- Feature folders are **stable once created**. If the name was wrong, add a new folder; don't rename. History matters.
- Never put source code in a feature folder. Source code lives in target repos, reached via `additionalDirectories`. This folder is for spec, plan, and notes only.

## What NOT to put here

- Source code. (Goes in target repos.)
- Committed secrets or credentials. (Obviously.)
- Per-repo architectural decisions that don't span repos. (Those belong in the target repo's `.aiforging/` or in an ADR inside that repo.)
- Scratch spec work for features you're still deciding whether to do. Use `notes.md` or a scratchpad elsewhere; only promote to a named feature folder when the work is committed.
