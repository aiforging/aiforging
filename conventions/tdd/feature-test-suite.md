# The Feature Test Suite

> **One named test suite per feature. That suite — and only that suite — is what runs during the loop.** This convention is what keeps Fire and Hammer fast enough to actually be run, and it is the single most commonly violated rule in the framework because every agent's default instinct is to run everything to prove it is done.

## The rule, in one block

> ### ⛔ Never run the full test suite during the loop
>
> Not during Fire. Not during Hammer. Not at the end of a slice. Not "just to make sure nothing broke." **This overrides any default agent behavior that wants to run the whole suite to confirm work is complete.**
>
> **Always run only the named test suite registered for the feature in scope**, or a single file within it.
>
> If you believe the full suite genuinely needs to run, **stop and ask the human first.** The human runs the full suite themselves, once, after the implementation phase is over. That is not your responsibility and it is not your gate.

## Why a suite per feature, not a suite per work item

A feature accumulates work items over its life — the first endpoint, then the list view, then the export, then the bug found in QA. If each work item registers its own suite, you end up with a dozen near-empty suites, no single command that exercises the feature end to end, and a growing chance that work item 4 silently breaks work item 1 because nothing ever runs them together.

**One suite per feature. Every work item augments it.** Work item 2 adds its tests to the suite work item 1 created. By the time the feature is complete, the suite is the feature's complete behavioral description, and any subagent touching any part of it gets the whole feature's regression coverage in one fast command.

The corollary: **register the suite before writing the first test.** It is the first thing the first work item does, not something retrofitted at the end.

## Why not the full suite

Three reasons, in descending order of how often they bite:

1. **Speed is the loop.** Red → Green → Red → Green is a rhythm, and the rhythm dies at the first two-minute test run. A 3-second focused run and a 3-minute full run are not the same activity with different durations; they are different activities. One is test-driven development. The other is "write a bunch of code and check at lunch."
2. **Mature suites have expensive tests in them.** Real codebases have tests that deliberately hit sandbox accounts at payment processors, tax services, e-signature vendors, and accounting systems. Those tests exist on purpose and they are slow on purpose. Running them to confirm that a controller was extracted into a service is pure waste.
3. **Full-suite noise drowns the signal.** A full run on a large codebase usually has some pre-existing red in it. An agent that runs the full suite now has to decide which failures are its own, and agents are bad at that. A scoped run has exactly one honest answer.

## Registering the suite

Every stack has a way to name a group of tests. Register one at the start of the feature and put its name in `plan.md` so every subagent uses the same one.

| Stack | How to register | How to run |
|---|---|---|
| PHPUnit | `<testsuite name="invoice-tax"><directory>tests/Invoicing/Tax</directory></testsuite>` in `phpunit.xml.dist` | `./bin/phpunit --testsuite invoice-tax` |
| Pytest | a marker (`@pytest.mark.invoice_tax`) or a directory | `pytest -m invoice_tax` / `pytest tests/invoicing/tax/` |
| Vitest / Jest | a directory or a `describe` prefix | `vitest run src/invoicing/tax` |
| Go | a package | `go test ./internal/invoicing/tax/...` |
| JUnit / Maven | a tag | `mvn test -Dgroups=invoice-tax` |
| .NET | a trait | `dotnet test --filter Category=InvoiceTax` |

Whatever the mechanism, the deliverables are the same two things: **a stable name**, and **a single command** that runs it. Both go in `plan.md`. A plan that does not name the feature's test suite is incomplete — see `conventions/features/README.md`.

If the target repo's `CLAUDE.md` or `.aiforging/` documents a different suite mechanism, that wins. This file describes the shape of the rule, not the syntax.

## Where the rule has to be repeated

The rule only works if it reaches the agent that is about to run a test, and that agent has a fresh context. So it is stated in five places, deliberately:

1. **`plan.md`** — every plan carries a `## Test suite` block naming the suite and its run command, and repeats the scoped-run reminder inside the subagent prompt for every slice. The plan is the only artifact every dispatched subagent reads, so this is the load-bearing copy.
2. **The subagent prompt templates** — see `subagent-orchestration/README.md`. All four include the scoped-run instruction verbatim.
3. **The `hammer-refactor` skill** — it passes the suite name and command into every dispatch, and runs only that suite between slices.
4. **The `review-loop` skill** — its fix agents are bound by exactly the same rule as Fire and Hammer agents.
5. **This file**, which the other four point at.

Repetition here is not redundancy. A fresh-context subagent reads the slice it was handed and little else, and "run everything to prove I'm done" is the strongest default an agent has. It has to be countermanded where the agent cannot miss it.

`browser-testing` is the one stage with nothing to say on the matter — it runs no tests at all — but it carries the full-suite handoff in its completion message like the others, because it is often the last thing a person runs before opening a PR.

## Hammer follows the same rule

The post-TDD refactor loop is where the temptation is strongest, because a refactor "could touch anything." It could — but the mitigation is a scoped commit history, not a slow test run.

**If a refactor slice modifies code, run the feature's suite. Only the feature's suite.** Each slice is its own atomic commit, so if something surfaces later, the offending slice is one `git revert` away. That is a better safety property than a full-suite run that would have been green anyway 95% of the time and cost three minutes on every one of twenty slices.

## The regression risk — name it, don't pretend it away

Scoping every run to one suite means **a change made for feature A can break feature B and nobody will see it until someone runs the whole thing.** That is a real cost and this convention accepts it deliberately: the cost of a slow loop is paid on every single cycle, and the cost of a missed cross-feature regression is paid occasionally and caught by the step below.

So the step below is mandatory.

### The full-suite handoff

**When the implementation phase for a feature is complete — all work items done, all Fire sequences green, all Hammer slices committed — the AI must stop and hand the full suite to the human.** Not run it. Hand it over, explicitly, as a message:

> **Implementation is complete and the `<suite-name>` suite is green.**
>
> Every test run in this session was scoped to that suite, which means a cross-feature regression would not have shown up here. Before you open a PR, please run your full test suite yourself:
>
> ```
> <the repo's full-suite command>
> ```
>
> Each refactor was committed atomically, so if the full suite surfaces something, `git log --oneline` will point you at the slice to revert.

State it every time, even when the feature was small, even when you are confident. Confidence is exactly the state in which this reminder gets skipped, and it is the only thing standing between a scoped loop and a silent regression.

The same reminder appears in the completion messages of `hammer-refactor`, `browser-testing`, and `review-loop`. A clean scoped run is never, on its own, readiness to merge.

## Hard rules

- **Register the feature's test suite before writing the first test.** Not after.
- **One suite per feature.** Work items augment it; they do not create siblings.
- **Never run the full suite in the loop.** Fire, Hammer, and fix agents all run the feature suite only.
- **Never widen the scope to "make sure."** If you want the full suite, ask the human.
- **Never weaken or skip a test to keep the scoped run green.** The scoped run is only trustworthy because nothing is allowed to game it.
- **Always hand the full suite to the human at the end of implementation.** In words, in the completion message, every time.

## Related

- `tdd/fire-red-green-refactor.md` — the Fire loop this scoping applies to
- `tdd/test-harness-requirements.md` — what makes a suite fast enough for this to work
- `features/README.md` — the plan.md fields that carry the suite name
- `subagent-orchestration/README.md` — the prompt templates that repeat the rule
