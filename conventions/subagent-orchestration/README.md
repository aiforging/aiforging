# Subagent Orchestration Convention

> **How the parent conversation dispatches work, and what the subagents that receive that work are expected to do.** These rules are the glue between plan.md (what to do) and `superpowers:subagent-driven-development` / `hammer-refactor` (who actually does it). They are copied into every onboarded target repo so any teammate working in the target also has them.

## Why subagents at all

The parent conversation that is driving a feature is holding a lot of context: the spec, the plan, the target-repo architecture conventions, the pattern library, the git state, the user's preferences, open questions. If the parent *also* tries to implement every slice, that context blows up — long conversations degrade quality, lose track of earlier decisions, and drift from the spec.

The solution is to **keep the parent lean and push implementation down to fresh-context subagents.** Each subagent is handed exactly one slice of the plan. It loads only the context it needs to complete that slice. It finishes, reports back, and disappears. The parent picks up the report and decides what to dispatch next.

This is how AI Forging scales: adding the 50th pattern to the library costs the parent conversation nothing, because the parent never loads patterns — the hammer-refactor subagents do, one pattern at a time, in parallel, each in its own fresh context.

## The core rules

### 1. The parent is a conductor, not a performer

The parent conversation should, wherever possible:

- Read the spec and plan.
- Decide what to dispatch next.
- Dispatch a subagent.
- Read the subagent's report.
- Update plan.md status.
- Decide what to dispatch next.

The parent conversation should **not**, wherever possible:

- Write production code itself.
- Run the target repo's test suite itself.
- Load more than a slice or two of the target repo into its own context.
- Load the full pattern library into its own context.

If the parent is writing code directly, the slice was probably too small for a dispatch OR the plan is trying to do something the subagent model can't handle cleanly. Stop and reconsider the slice.

### 2. plan.md is the authoritative source

When a subagent is dispatched, its prompt does not embed the full context of the slice. Instead, the prompt **points at** plan.md and tells the subagent which slice to execute. The subagent reads plan.md itself, reads the target repo's `.aiforging/` and root `CLAUDE.md` itself, and takes its marching orders from the plan entry.

This is critical: if the parent embedded slice details into the prompt, and then plan.md was updated during execution (slice renumbering, new gate, revised test list), the dispatched subagents would be working from a snapshot that no longer matches reality. Pointing at plan.md means subagents always see the current truth.

**The minimal subagent prompt** looks like this:

```
Read <forge-workspace>/docs/features/<feature-name>/plan.md.
Read <target-repo>/CLAUDE.md.
Execute Slice <N> for target repo <target>.
Check off each task in the plan as you complete it.
Run ONLY the feature's named test suite (given in the plan's "Test suite" line) — never the
full repository suite. If you believe the full suite must run, stop and ask.
When all tasks for this slice are complete and the feature suite is green, report back.
```

That is the entire prompt. No slice details, no test names, no paths, no pattern references — all of those live in plan.md and the target's `.aiforging/` and `CLAUDE.md`. The subagent resolves them itself.

The one exception is the **scoped-test-run instruction**, which is repeated verbatim in every prompt even though it is also in the plan and in the conventions. That repetition is deliberate: running the whole suite to prove the work is done is the strongest default behavior an agent has, and it has to be countermanded in the prompt itself, where the agent cannot miss it. See rule 8 below.

### 3. Every subagent reads its target's `.aiforging/CLAUDE.md`

Non-negotiable. Before a subagent writes a single line of code, it reads the target repo's root `CLAUDE.md` (which in an AI Forging target points at the target's `.aiforging/` conventions). This is how the subagent learns the folder layout, the naming rules, the controller/repository/DTO conventions, the test commands, and anything else the target's maintainers consider binding.

A subagent that skips this step will produce code that the next Hammer pass has to rewrite. Worse, it will produce code that *passes tests* but lives in the wrong directory or uses the wrong naming convention, and that kind of near-correct damage is the hardest to spot in review.

Subagent prompts should always include the explicit instruction: "Read `<target-repo>/CLAUDE.md` before beginning."

### 4. Dispatch ordering follows dependencies

The plan's slice numbering encodes logical dependencies. The parent dispatches slices in that order, with one exception: **independent slices can dispatch in parallel.**

Examples of dependent chains (must dispatch sequentially):

- A backend schema change → the backend API endpoint that uses it → the frontend form that calls the endpoint. The frontend can't start until the API is green.
- A refactoring slice that renames a symbol → any slice that uses the new name.
- A `[fire]` slice that writes a failing test for a new behavior → the `[fire]` slice that makes the test pass.

Examples of independent slices (can dispatch in parallel):

- Two unrelated Hammer refactors touching disjoint files against different patterns.
- Two Fire sequences in two different target repos that don't share an interface yet.
- All the hammer-refactor subagents dispatched for a single Fire sequence's closing `[hammer]` slice — one per applicable pattern, all at once, each against the files the Fire sequence touched.

When in doubt, dispatch sequentially. The cost of serializing a slice that could have been parallel is a few extra minutes; the cost of racing two slices that should have been sequential is a merge conflict or a broken test suite.

### 5. Every Fire sequence closes with hammer-refactor

This is enforced at the plan level (see `conventions/features/README.md` — "Every Fire sequence ends with a closing `[hammer]` slice") but it is the parent conversation's responsibility to **actually dispatch** that closing slice when the Fire sequence's tests go green. The closing `[hammer]` slice fans out one fresh-context subagent per applicable pattern via `superpowers:subagent-driven-development`, in parallel, against the files the Fire sequence touched.

Skipping the closing Hammer pass is how codebases rot in the AI era. Every new Fire sequence ships new surface area; every new surface area has to be dragged through the pattern library before it accumulates debt. This is the entire point of the Hammer pillar.

If the parent is tempted to skip the Hammer pass because "the tests are green and we're in a hurry," stop. Green tests mean the code *works*; they don't mean the code fits the conventions. Hammer is what makes it fit.

### 6. Subagents check their own boxes

When a subagent completes a task in its assigned slice, the subagent itself checks off the relevant plan.md checkbox. The parent conversation never checks a box on behalf of a subagent, and never unchecks a box a subagent already checked.

The plan is history as well as instructions. Completed boxes are a record of what was done and in what order. A subagent that reports "I finished but forgot to check the box" should be told to re-run, check its box, and report again. The parent does not "help" by editing the plan itself.

### 7. The parent never fabricates work

If a subagent reports incomplete work ("I couldn't run the tests because the fixture was missing" or "I skipped the renaming because it broke something I don't understand"), the parent must **not**:

- Check the box anyway.
- Dispatch the next slice as if this one succeeded.
- Quietly reword the plan to skip the problem.

The parent must either dispatch a follow-up subagent to resolve the blocker, escalate to the user, or both. Fabricated completion is the single worst thing a conductor can do, because every downstream slice dispatches against a false assumption and the entire feature quietly goes off the rails.

### 8. Every dispatched agent runs the feature's suite, and only the feature's suite

The feature has exactly one named test suite, registered before the first test was written and recorded in plan.md. Every Fire subagent, every Hammer subagent, and every fix agent runs **that suite and nothing else** — or a single file within it.

**No dispatched agent runs the full repository suite. Ever.** Not to confirm its slice, not at the end of a sequence, not "to make sure nothing broke." The parent does not run it either. If an agent reports that it ran the full suite, that is a prompt defect: the instruction was missing or the agent overrode it, and either way the next dispatch must carry the instruction explicitly.

Full details, including how to register a suite per stack, are in `tdd/feature-test-suite.md`.

**The parent owes the human a handoff.** When the whole implementation phase is done — every work item, every Fire sequence green, every Hammer slice committed — the parent conversation must stop and tell the human, in words, that every run in the session was scoped, that a cross-feature regression would therefore not have surfaced, and that they should now run the full suite themselves. Give them the command. Do not run it on their behalf, and do not skip the message because the feature felt small.

## Portable subagent prompt templates

These templates live here so the parent conversation can copy-paste them when dispatching. They are deliberately terse. Do not expand them with slice details; let plan.md carry that.

### Generic target (use this unless the target has a named adapter)

```
Read <forge-workspace>/docs/features/<feature>/plan.md.
Read <target-repo-path>/CLAUDE.md.
Execute Slice <N> for target repo "<target-name>".
Check off each task in the plan as you complete it.
Run ONLY the feature's named test suite (see the plan's "Test suite" line) before considering the
work complete — NEVER the full repository suite. If you think the full suite must run, stop and ask.
Report back with: (a) which tasks you checked off, (b) test-run output, (c) anything you could not finish and why.
```

### Backend target (Symfony/Doctrine happy path)

```
Read <forge-workspace>/docs/features/<feature>/plan.md.
Read <target-repo-path>/CLAUDE.md and <target-repo-path>/.aiforging/architecture/.
Execute the backend-targeted Slice <N> for target repo "<target-name>", following the target's TDD workflow strictly.
Check off each task in the plan as you complete it.
Run the target's static-analysis / style command (as documented in <target-repo-path>/CLAUDE.md —
typically "composer checks" or equivalent), and run ONLY the feature's named test suite (see the
plan's "Test suite" line). NEVER run the full repository suite; if you think it must run, stop and ask.
When all backend tasks for this slice are complete and tests are green, if this is the closing [hammer] slice of a Fire sequence, dispatch the hammer-refactor skill as a subagent against the files you touched.
Report back with: (a) which tasks you checked off, (b) test-run output, (c) anything you could not finish and why.
```

### Frontend target (React + Playwright happy path)

```
Read <forge-workspace>/docs/features/<feature>/plan.md.
Read <target-repo-path>/CLAUDE.md and <target-repo-path>/.aiforging/frontend-testing/ if present.
Execute the frontend-targeted Slice <N> for target repo "<target-name>".
Check off each task in the plan as you complete it.
Run the target's frontend checks command (as documented in <target-repo-path>/CLAUDE.md), and run
ONLY the feature's named test suite / test directory — NEVER the full repository suite.
Report back with: (a) which tasks you checked off, (b) test-run output, (c) anything you could not finish and why.
```

### Hammer-refactor subagent (dispatched by hammer-refactor skill, one per pattern)

```
You are executing a single Hammer pass against <target-repo-path>.
Pattern file to apply: <target-repo-path>/.aiforging/patterns/<pattern-name>.md
           (or anti-pattern file: <target-repo-path>/.aiforging/anti-patterns/<pattern-name>.md)
Scope: the files changed in the current Fire sequence (provided as a list by the parent).
Read <target-repo-path>/CLAUDE.md for repo-wide conventions.
Apply the pattern to each in-scope file. Do not touch out-of-scope files.
If you modified any code, run ONLY the feature's named test suite (given by the parent) after your
changes — NEVER the full repository suite. Do not consider the pass complete if that suite fails.
Report back with: (a) files modified, (b) which violations you found and fixed, (c) test-run output, (d) anything you could not fix and why.
```

## Relationship to `superpowers:subagent-driven-development`

Everything above is built **on top of** `superpowers:subagent-driven-development`. That skill provides the actual dispatch mechanism (fresh-context subagents, parallel dispatch, report collection). AI Forging's contribution is the *policy layer*: what to dispatch, in what order, with what prompts, and what the subagents are expected to read before starting. When this convention says "dispatch a subagent," the concrete mechanism is a `superpowers:subagent-driven-development` call.

Do not reimplement subagent dispatch here. If you are ever tempted to, stop and use superpowers instead.

## Why this convention is copied into every target repo

A teammate who clones the target repo without the forge workspace still benefits from these rules when they run Claude directly inside the target. In that mode there is no plan.md to point at — the teammate is driving a smaller, in-repo workflow — but the principles still apply: keep the parent lean, read CLAUDE.md first, check your own boxes, always close a Fire sequence with a Hammer pass. The target-repo copy lets that workflow stay consistent with how the forge workspace drives it.
