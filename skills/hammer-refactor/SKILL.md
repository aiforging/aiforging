---
name: hammer-refactor
description: Run the Hammer stage of AI Forging on a passing test suite. Given a green test suite (Fire is complete), walk the pattern and anti-pattern library, identify applicable refactors, and dispatch one fresh-context subagent per refactor slice via superpowers:subagent-driven-development. Never invoked before tests are green. Never weakens tests. Never generates new features. Triggered after test-driven-development produces a green suite and the user is ready to refactor toward the prescribed architecture.
---

# Hammer Refactor

> **Stage 2 of 3.** Fire produced a green test suite. Tempering captures what we learned. Hammer is the disciplined refactor pass in between — shape the code toward the prescribed architecture without changing behavior.

## When to invoke this skill

This skill runs when **all** of the following are true:

1. A feature's tests are green (Fire stage is complete — see `superpowers:test-driven-development`).
2. The user (or an upstream subagent dispatched by plan.md) has opted into a refactor pass on a specific feature or module.
3. There is a `plan.md` for the feature at `<forge-workspace>/docs/features/<feature-name>/plan.md`, OR the user is running a targeted "refactor this one thing" request against a specific file or class.
4. The current target repo has `.aiforging/patterns/` and `.aiforging/anti-patterns/` seeded (installed during `/aiforging:setup` onboarding).

If any of those are false, stop and tell the user what's missing. **Never refactor code that doesn't have passing tests.** Never install patterns on the fly.

### How this skill gets triggered

There are three legitimate entry points:

1. **Plan-driven, automatic.** The AI Forging feature convention requires every Fire sequence in `plan.md` to end with a closing `[hammer]` slice (see `conventions/features/README.md` — "Every Fire sequence ends with a closing `[hammer]` slice"). When a Fire-stage subagent finishes its tasks and its tests go green, its prompt instructs it to dispatch `hammer-refactor` as a subagent against the files it just touched. **This is the default path.** A Fire sequence is not "done" until its closing Hammer pass has run.
2. **User-invoked against a specific feature.** The user explicitly asks "run hammer on feature X" — this skill reads that feature's plan.md and scans the files it names.
3. **User-invoked targeted mode.** The user asks "clean up this one file" with no active feature plan — skip the plan-reading step and treat the target as a one-shot.

In all three paths, Hammer operates as a **dispatcher**, not a direct implementer. See `conventions/subagent-orchestration/README.md` for the parent-as-conductor rules that Hammer follows: the parent context loads no pattern content beyond detection signals, every refactor is dispatched as a fresh-context subagent, and the parent never touches a file on behalf of a dispatched subagent. Hammer is the canonical example of that discipline in action.

## What this skill does NOT do

- Generate new features or new behavior.
- Weaken, skip, or delete existing tests.
- Change public API shapes without explicit confirmation — those are architecture gates, not refactors.
- Refactor code that has no test coverage. If coverage is missing, stop and tell the user to run Fire stage first.
- Execute more than one refactor slice in the current context. Each slice is dispatched to a fresh subagent.

## How it works

The Hammer stage is **not one big monolithic refactor pass**. It is a loop that dispatches one fresh-context subagent per refactor slice. This is the key insight from `superpowers:subagent-driven-development`: each subagent starts with a clean context window, reads exactly the pattern/anti-pattern file it needs, looks at the target code, makes the change, and hands back a report. Then the parent context reviews the report and dispatches the next slice. That's how we scale the pattern library from ~5 patterns today to 50+ without drowning in context.

### Step 1 — Read the current feature plan (if applicable)

If the user invoked this skill in the context of a specific feature, read `<forge-workspace>/docs/features/<feature-name>/plan.md` to find any refactor slices explicitly listed. The plan is the source of truth for **what** to refactor.

If the user invoked this skill in a targeted mode ("refactor this file"), skip this step and treat the target as a one-shot.

### Step 2 — Scan the target code against the anti-pattern library

Walk `.aiforging/anti-patterns/` in the current target repo. For each `*.md` file, read its "Detection Signals" section and grep/analyze the target code for those signals. Build a candidate list of `(anti-pattern, file, line-range, severity)` tuples.

**This is the only step where the parent context loads anti-pattern content.** The parent context needs to know which anti-patterns *exist* in the code, but it does NOT need to know how to *fix* them — that goes to the subagent.

### Step 3 — Prioritize

Rank the candidates by severity (see `conventions/refactoring/README.md` for severity definitions) and by whether the plan.md (if any) explicitly called them out. Present the ranked list to the user and ask for confirmation before dispatching.

**Human gate:** the user approves which slices to run. This is not autonomous refactoring.

### Step 4 — Dispatch one subagent per approved slice

For each approved `(anti-pattern, file, line-range)` slice, use the Task tool (via `superpowers:subagent-driven-development`) to dispatch a fresh-context subagent with a prompt that contains:

1. The anti-pattern file path (the subagent reads it fresh).
2. The target file path and line range.
3. Absolute rule: "All tests must still pass at the end. Run the feature's test suite before reporting done. If any test fails, revert and report what you tried."
4. Absolute rule: "Do not touch any file outside the specified target unless the anti-pattern file explicitly says the refactor requires it."
5. A reminder to follow the corresponding pattern file (if the anti-pattern names one) from `.aiforging/patterns/`.

Each subagent runs independently. The parent context waits for the report, reviews it, and moves on.

### Step 5 — Verify after each slice

After each subagent reports back, the parent context:

1. Runs the target repo's test suite once more to confirm green. If red, roll back the slice (git) and report the failure.
2. Shows the diff to the user for approval before the next slice.

**Second human gate:** user reviews each slice before the next one dispatches.

### Step 6 — Tempering handoff

When all approved slices are done and green, write a short summary of what was refactored and which patterns/anti-patterns were applied. That summary feeds the Tempering stage (knowledge capture) — typically, new patterns or anti-patterns that emerged during the refactor get written to `.aiforging/patterns/` or `.aiforging/anti-patterns/` as new `.md` files, one per pattern, following the format in `conventions/refactoring/README.md`.

## Safety rules (hard refusals)

- **No refactor without green tests.** If the test suite is not passing at the start, stop.
- **No refactor of untested code.** If the target file has no tests, stop and tell the user to run Fire first.
- **No weakening tests.** If a test appears to block a refactor, the refactor is wrong, not the test.
- **No cross-boundary refactors without explicit approval.** Changing a public API, a database schema, or a cross-module contract is an architectural decision, not a refactor.
- **No silent failures.** Every dispatched subagent must report success or failure with the exact diff applied.
- **One slice per subagent, one subagent per context.** Never batch multiple patterns into a single dispatch — the whole point is to keep each subagent's reasoning scoped to one concern.

## Relationship to other skills

- **Fire** (`superpowers:test-driven-development`) comes first. This skill refuses to run if Fire hasn't produced a green suite.
- **Plan writing** (`superpowers:writing-plans`) produces the `plan.md` this skill reads in Step 1.
- **Subagent dispatch** (`superpowers:subagent-driven-development`) is the transport this skill uses in Step 4. This skill's job is to decide *what* to dispatch; superpowers' job is *how* to dispatch it. The *policy* layer that tells Hammer (and every other plan-driven dispatch point) how to construct subagent prompts, how to order dispatches, and what the subagents are expected to read before starting lives in `conventions/subagent-orchestration/README.md`. Hammer follows that convention — it is not a special case.
- **Architecture analyzer** (`aiforging:architecture-analyzer`) is a sibling skill that runs a non-destructive advisory pass. Hammer is the executable counterpart. Analyzer says "your code is shaped like X, here are the deltas from the ideal." Hammer takes those deltas and actually closes them, one slice at a time.

## Pattern library format

Each `.md` file in `.aiforging/patterns/` and `.aiforging/anti-patterns/` follows the format documented in `.aiforging/architecture/` (copied from the plugin's `conventions/refactoring/README.md`). Minimally, each file has:

- **Name** — imperative verb phrase for patterns ("Extract Service From Controller"), noun phrase for anti-patterns ("Fat Controller").
- **Detection signals** — how to spot it in code. Concrete signals, not vibes.
- **Severity** — Critical / High / Medium / Low / Info.
- **Why it's a problem** (anti-patterns) or **why it helps** (patterns).
- **Before and after example** — minimal code that illustrates the refactor.
- **Related patterns** — what to do next after applying this one.

New patterns that emerge during real refactors get added as new files. The library grows monotonically; we do not edit old patterns silently.

## Example invocation

```
User: I just finished Fire on the invoice tax calculation feature. Run Hammer on
      the backend repo to clean up the service layer.

Hammer skill:
  1. Reads ~/forge/docs/features/invoice-tax-calculation/plan.md, finds three
     refactor slices explicitly listed.
  2. Scans ~/projects/certainpath-backend/src/Invoicing/ for anti-pattern signals.
     Finds: fat-controller in CreateInvoiceController (line 45-120), primitive-
     obsession on TaxRate (line 78).
  3. Presents ranked list; user approves all three slices.
  4. Dispatches subagent A with extract-service-from-controller.md and
     CreateInvoiceController.php:45-120. Waits for report.
  5. Test suite runs: green. Shows diff. User approves.
  6. Dispatches subagent B with value-object-for-money.md and TaxRate usages.
     Waits for report.
  7. Test suite runs: green. Shows diff. User approves.
  8. Writes summary to plan.md. Tempering stage begins.
```

---

**Remember:** Hammer is the disciplined refactor pass, not a free-for-all cleanup. Every move is justified by a pattern file, every move preserves test green, and every move is reviewed before the next one dispatches. If you find yourself "just tidying up" something outside the dispatched slice, stop. That's a separate conversation.
