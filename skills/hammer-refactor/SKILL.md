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
4. A pattern library exists — either at the workspace shared tier (`<workspace>/.aiforging/patterns/` + `.aiforging/anti-patterns/`), or at the target-local tier (`<target>/.aiforging/patterns/` + `.aiforging/anti-patterns/`), or both.

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

### Step 0 — Resolve the workspace and detect the target's stack

Before anything else, locate the forge workspace and determine the current target's stack. This is needed for two-tier pattern merging.

**Case A — session is running inside a target repo (multi-repo setup).**

The target repo has `.aiforging/` at its root. The forge workspace is found by:
1. Checking `~/.claude/aiforging.json` for `active_workspace`.
2. If found, verify the path exists, its `CLAUDE.md` contains the string `AI Forging workspace`, and it has a `docs/features/` directory. That pair is what `/aiforging:setup` Phase A writes.
3. If not found, ask the user: "Where is your forge workspace?"

**Case B — session is running inside a monorepo / single-repo workspace.**

The workspace IS the repo (or the repo root). Detect with: the repo root's `CLAUDE.md` contains `AI Forging workspace` and `docs/features/` exists. The target is either the repo root itself (single-repo) or a sub-project within it (monorepo). If the repo has sub-projects with their own `.aiforging/`, resolve which sub-project the user is working in.

**Case C — session is running inside the forge workspace itself (multi-repo).**

The workspace is the cwd. The target must be specified — ask the user which registered target to run Hammer against if not obvious from context (e.g., from a `plan.md` slice that names the target).

**Detect the target's stack** by running `detect-project.py` against the target root (or reading a cached detection result from `.aiforging/ANALYSIS.md` if present). The detected stack identifiers (e.g., `symfony-php`, `doctrine`, `react`) are used in Step 2 to filter shared-tier patterns.

### Step 1 — Read the current feature plan (if applicable)

If the user invoked this skill in the context of a specific feature, read `<forge-workspace>/docs/features/<feature-name>/plan.md` to find any refactor slices explicitly listed. The plan is the source of truth for **what** to refactor.

If the user invoked this skill in a targeted mode ("refactor this file"), skip this step and treat the target as a one-shot.

### Step 2 — Build the merged pattern set from both tiers

The pattern library has two tiers. Merge them into a single set for this run:

**Target-local tier** — glob `<target>/.aiforging/patterns/*.md` and `<target>/.aiforging/anti-patterns/*.md`. These apply unconditionally to this target (no frontmatter filtering).

**Shared tier** — glob `<workspace>/.aiforging/patterns/*.md` and `<workspace>/.aiforging/anti-patterns/*.md`. For each file, read its YAML frontmatter `applies-to` list. Include the file only if `applies-to` contains at least one of the target's detected stack identifiers OR contains `all`. Skip files whose `applies-to` doesn't match (e.g., a `react`-only pattern when running against a Symfony backend).

**Deduplication** — if a shared-tier file and a target-local file have the same filename, the target-local copy wins. This lets a target override a shared pattern with a repo-specific version.

The merged set is the complete list of patterns and anti-patterns for this run. For each anti-pattern in the merged set, read its "Detect" section and grep/analyze the target code for those signals. Build a candidate list of `(anti-pattern, file, line-range, severity)` tuples.

**This is the only step where the parent context loads anti-pattern content.** The parent context needs to know which anti-patterns *exist* in the code, but it does NOT need to know how to *fix* them — that goes to the subagent.

### Step 3 — Prioritize

Rank the candidates by severity (see `conventions/refactoring/README.md` for severity definitions) and by whether the plan.md (if any) explicitly called them out. Present the ranked list to the user and ask for confirmation before dispatching.

**Human gate:** the user approves which slices to run. This is not autonomous refactoring.

### Step 4 — Dispatch one subagent per approved slice

For each approved `(anti-pattern, file, line-range)` slice, use the Task tool (via `superpowers:subagent-driven-development`) to dispatch a fresh-context subagent with a prompt that contains:

1. The anti-pattern file path (the subagent reads it fresh).
2. The target file path and line range.
3. **The feature's test suite name and its exact run command**, taken from `plan.md`'s "Test suite" line (or from the user, in targeted mode).
4. Absolute rule: "If you modify any code, run ONLY the feature's named test suite — `<the command>`. **NEVER run the full repository suite**, not to confirm your slice and not to make sure nothing broke. If you believe the full suite must run, stop and say so instead of running it. If the feature suite fails, revert and report what you tried."
5. Absolute rule: "Do not touch any file outside the specified target unless the anti-pattern file explicitly says the refactor requires it."
6. A reminder to follow the corresponding pattern file (if the anti-pattern names one) from `.aiforging/patterns/`.

Each subagent runs independently. The parent context waits for the report, reviews it, and moves on.

### Step 5 — Verify and commit after each slice

After each subagent reports back, the parent context:

1. **If the slice modified any code**, runs the **feature's named test suite** — and only that suite — to confirm green: `./bin/phpunit --testsuite invoice-tax`, `pytest -m invoice_tax`, `vitest run src/invoicing/tax`. The suite name comes from `plan.md`. **Never the full repository suite** (see `conventions/tdd/feature-test-suite.md`). If a slice changed no code, there is nothing to re-verify — say so and move on. If the suite is red, roll back the slice (`git checkout -- .`) and report the failure — do not proceed to the next slice.
2. Shows the diff to the user for approval.
3. If approved, make an **atomic git commit** for this slice. The commit message should name the pattern/anti-pattern applied and the target file(s), e.g., `refactor: extract service from CreateInvoiceController (fat-controller)`. This gives the user a clean, reviewable history where each refactor is its own commit — easy to revert individually if a problem surfaces later.

**Second human gate:** user reviews each slice before the commit and before the next slice dispatches.

### Step 6 — Tempering handoff and the full-suite reminder

When all approved slices are done and green, write a short summary of what was refactored and which patterns/anti-patterns were applied. That summary feeds the Tempering stage (knowledge capture) — typically, new patterns or anti-patterns that emerged during the refactor get written to `.aiforging/patterns/` or `.aiforging/anti-patterns/` as new `.md` files, one per pattern, following the format in `conventions/refactoring/README.md`.

**Then hand the full test suite to the human — in words, every time.** Do not run it yourself.

> **Hammer is complete. Every slice passed the `<suite-name>` suite individually.**
>
> Every test run in this pass was scoped to that one suite, which is what kept the loop fast — but it also means a regression in a *different* feature would not have shown up here. Before you open a PR, please run your full test suite yourself:
>
> ```
> <the repo's full-suite command>
> ```
>
> Each refactor is its own atomic commit, so if the full suite surfaces something, `git log --oneline` points straight at the slice to revert. You can start reviewing the diffs while it runs.

This message is **not optional and not conditional on how the pass went.** State it even when the pass was small, even when every slice was trivial, even when you are confident. Confidence is exactly the state in which it gets skipped, and it is the only thing standing between a deliberately scoped loop and a silent cross-feature regression. See `conventions/tdd/feature-test-suite.md` for why the framework accepts that trade deliberately rather than pretending it away.

Running the suite is the human's job, not a gate on this skill. Deliver the message and proceed to the Tempering summary either way.

## Safety rules (hard refusals)

- **No refactor without green tests.** If the feature's named test suite is not passing at the start, stop.
- **No full-suite runs.** Neither this skill nor any subagent it dispatches runs the full repository suite, for any reason. If you think it needs to run, tell the human and let them run it.
- **No refactor of untested code.** If the target file has no tests, stop and tell the user to run Fire first.
- **No weakening tests.** If a test appears to block a refactor, the refactor is wrong, not the test.
- **No cross-boundary refactors without explicit approval.** Changing a public API, a database schema, or a cross-module contract is an architectural decision, not a refactor.
- **No silent failures.** Every dispatched subagent must report success or failure with the exact diff applied.
- **One slice per subagent, one subagent per context.** Never batch multiple patterns into a single dispatch — the whole point is to keep each subagent's reasoning scoped to one concern.

## Relationship to other skills

- **Fire** (`superpowers:test-driven-development`) comes first. This skill refuses to run if Fire hasn't produced a green suite.
- **Plan writing** (`superpowers:writing-plans`) produces the `plan.md` this skill reads in Step 1.
- **Subagent dispatch** (`superpowers:subagent-driven-development`) is the transport this skill uses in Step 4. This skill's job is to decide *what* to dispatch; superpowers' job is *how* to dispatch it. The *policy* layer that tells Hammer (and every other plan-driven dispatch point) how to construct subagent prompts, how to order dispatches, and what the subagents are expected to read before starting lives in `conventions/subagent-orchestration/README.md`. Hammer follows that convention — it is not a special case.
- **Browser testing** (`aiforging:browser-testing`) and **review loop** (`aiforging:review-loop`) come *after* Hammer, once the feature is built to presumed-working. Hammer shapes the code; those two check the running product and the diff. Do not fold either into a Hammer pass.
- **Architecture analyzer** (`aiforging:architecture-analyzer`) is a sibling skill that runs a non-destructive advisory pass. Hammer is the executable counterpart. Analyzer says "your code is shaped like X, here are the deltas from the ideal." Hammer takes those deltas and actually closes them, one slice at a time.

## Pattern library format

Each `.md` file in the pattern library (both the workspace shared tier and the target-local tier) follows the format documented in the plugin's `conventions/refactoring/README.md`. Shared-tier files have YAML frontmatter with `applies-to` for stack filtering; target-local files have no frontmatter. See `conventions/refactoring/README.md` for the full two-tier documentation. Minimally, each file has:

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
  0. Resolves workspace: ~/forge (from ~/.claude/aiforging.json pointer).
     Detects target stack: symfony-php, doctrine (from detect-project.py or
     cached ANALYSIS.md).
  1. Reads ~/forge/docs/features/invoice-tax-calculation/plan.md, finds three
     refactor slices explicitly listed.
  2. Builds merged pattern set:
     - Shared tier (~/forge/.aiforging/anti-patterns/): fat-controller.md
       (applies-to includes symfony-php ✓), primitive-obsession.md (all ✓).
       Shared pattern: extract-service-from-controller.md (symfony-php ✓).
     - Target-local tier (~/projects/certainpath-backend/.aiforging/):
       legacy-event-dispatcher.md (local override, no frontmatter).
     - Merged: 4 patterns/anti-patterns for this run.
     Scans target code for detection signals.
     Finds: fat-controller in CreateInvoiceController (line 45-120), primitive-
     obsession on TaxRate (line 78).
  3. Presents ranked list; user approves all three slices.
  4. Dispatches subagent A with extract-service-from-controller.md and
     CreateInvoiceController.php:45-120. Waits for report.
  5. Feature suite (`--testsuite invoice-tax`) runs: green. Shows diff. User
     approves. Commits:
     "refactor: extract service from CreateInvoiceController (fat-controller)"
  6. Dispatches subagent B with primitive-obsession.md and TaxRate usages.
     Waits for report.
  7. Feature suite runs: green. Shows diff. User approves. Commits:
     "refactor: introduce TaxRate value object (primitive-obsession)"
  8. All slices done. Tells the user — in words — that every run was scoped
     to invoice-tax and that they should now run the full suite themselves;
     gives them the command and notes each slice is individually revertible.
  9. Writes summary to plan.md. Tempering stage begins.
```

---

## A note on the paths in this file

References like `conventions/tdd/feature-test-suite.md` name files in the **AI Forging plugin's** conventions library. Where you actually find a given file depends on where you are:

- **In an onboarded target repo** — the architecture, tdd, and subagent-orchestration conventions are installed at `<target>/.aiforging/`, so `conventions/tdd/feature-test-suite.md` is `<target>/.aiforging/tdd/feature-test-suite.md`.
- **In the forge workspace** — the feature convention is installed at `docs/features/README.md`, and the pattern-library README at `.aiforging/README.md`.
- **In the plugin itself** — everything is under `${CLAUDE_PLUGIN_ROOT}/conventions/`, which is readable but never writable.

If a referenced file is not where you expect, say so rather than proceeding on a guess about what it said.

---

**Remember:** Hammer is the disciplined refactor pass, not a free-for-all cleanup. Every move is justified by a pattern file, every move preserves test green, and every move is reviewed before the next one dispatches. If you find yourself "just tidying up" something outside the dispatched slice, stop. That's a separate conversation.
