# Fire — Red / Green / Refactor

## Where the loop comes from

**Use `superpowers:test-driven-development`.** AI Forging does not define its own Red/Green/Refactor skill. The `superpowers` plugin by Jesse Vincent ships a mature, battle-tested TDD skill, and AI Forging explicitly delegates to it. When Claude is implementing any feature or bug fix under this framework, it invokes the `superpowers:test-driven-development` skill and follows that skill's discipline:

> Write the test first. Watch it fail. Write minimal code to pass. If you didn't watch the test fail, you don't know if it tests the right thing. Violating the letter of the rules is violating the spirit of the rules.

If that skill isn't available in this session, STOP. Either install the superpowers plugin (see the plugin's main README or re-run `/aiforging:setup`) or confirm with your human partner that you're intentionally proceeding without it. Do not reinvent the loop inline.

## Scoped test runs — the feature's test suite, and nothing else

**Before you write the first test, register a named test suite for the feature.** One suite per feature — not one per work item. Every subsequent work item on that feature augments the same suite. Put its name and its exact run command in `plan.md`.

Then, for the entire Red / Green / Refactor loop, **run only that suite** (or a single file inside it):

```
./bin/phpunit --testsuite invoice-tax      # not ./bin/phpunit
pytest -m invoice_tax                       # not pytest
vitest run src/invoicing/tax                # not vitest run
```

> ### ⛔ Never run the full repository suite during the loop
>
> Not during Fire, not during Hammer, not at the end of a slice, not "just to make sure nothing broke." This **overrides** any default agent behavior that wants to run everything to confirm the work is done. If you think the full suite genuinely needs to run, stop and ask the human. Running it is the human's job, once, after implementation is complete.

The speed of the feedback loop is the speed of the cycle. A 3-second focused run and a 3-minute full run are not the same activity at different speeds — one is test-driven development and the other is writing code and checking at lunch. Mature suites also contain tests that deliberately hit sandbox accounts at payment, tax, and e-signature vendors; those are slow on purpose and are pure waste during a refactor.

**This scoping has a real cost, and the framework pays it deliberately:** a change made for feature A can break feature B, and a scoped run will not see it. That is why the full-suite handoff below is mandatory rather than optional.

### The full-suite handoff — mandatory, at the end

When the implementation phase is complete — all work items done, all Fire sequences green, all Hammer slices committed — **stop and hand the full suite to the human in words.** Do not run it. Tell them what was and was not covered, give them the command, and remind them that every refactor was an atomic commit so anything the full suite surfaces is one `git revert` away.

Say it every time, including when the feature was small and you feel confident. Confidence is precisely the state in which this gets skipped.

The complete convention — how to register a suite in each stack, why it is one per feature, and the four places the rule has to be repeated so a fresh-context subagent actually receives it — is in `tdd/feature-test-suite.md`. Read it once; it is short.

## What AI Forging adds on top of the superpowers TDD skill

Two things that superpowers intentionally leaves to each project's architecture:

1. **The test-harness capability contract.** Your tests need to be able to stand up a real, isolated database whose schema comes from the entity graph. See `tdd/test-harness-requirements.md`. Without this, Repository tests degrade into mock theater and the loop loses its teeth. This is *the* biggest single differentiator between "we're doing TDD" and "we're actually doing TDD for a data-driven application."
2. **How to test Repositories specifically.** See `tdd/repository-testing.md`. Real DB, transaction-based isolation per test, factories instead of SQL fixtures, assert on domain objects not rows.

These two documents are architectural — they describe what your test infrastructure has to be capable of and what a good Repository test looks like. They do not replace the TDD loop itself; they make the loop trustworthy when your code touches a database.

## The Fire → Hammer → Tempering arc, briefly

The AI Forging framework frames the full cycle as three stages, and the loop you run under `superpowers:test-driven-development` is the **Fire** stage:

- **Fire (this doc)**: Red/Green/Refactor. The superpowers TDD skill. Plus the harness capability contract that makes it work for data-driven code.
- **Hammer (`refactoring/README.md`)**: The post-TDD pattern pass. Dispatch one subagent per pattern/anti-pattern file via `superpowers:subagent-driven-development` and iterate each against the session's changed files. Scales without a context ceiling.
- **Tempering (`refactoring/README.md`)**: Knowledge capture. Any pattern or anti-pattern observed during the cycle gets a new `.md` file in `refactoring/patterns/` or `refactoring/anti-patterns/`. One pattern, one file, reviewed independently.

Each iteration through Fire → Hammer → Tempering leaves the codebase stronger than it started. That's the compounding thesis.

## What Claude should refuse to do

- **Never generate implementation before a failing test exists.** Even "I'll write the code and then back-fill the tests" is wrong. If you catch yourself doing this, stop and reset the loop.
- **Never weaken a test to make it pass.** Fix the test deliberately with a human in the loop, or fix the code.
- **Never disable or skip tests to unblock a refactor.** A disabled test is a liability that compounds.
- **Never run the full repository suite to "confirm" the work.** Run the feature's named suite. Ask the human before widening scope. See `tdd/feature-test-suite.md`.
- **Never declare implementation complete without handing the full suite to the human.** A green scoped run is not readiness to merge.
- **Never mock the database in a Repository test.** Stand up the real thing via the test harness. See `tdd/repository-testing.md`.
- **Never proceed with Fire-stage work if the test harness can't satisfy the capability contract.** Fix the harness first. That's a prerequisite, not a luxury.

## Related

- `tdd/feature-test-suite.md`
- `tdd/test-harness-requirements.md`
- `tdd/repository-testing.md`
- `refactoring/README.md`
- `architecture/domain-driven-hexagonal.md`
