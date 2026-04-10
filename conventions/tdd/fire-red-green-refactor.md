# Fire — Red / Green / Refactor

## Where the loop comes from

**Use `superpowers:test-driven-development`.** AI Forging does not define its own Red/Green/Refactor skill. The `superpowers` plugin by Jesse Vincent ships a mature, battle-tested TDD skill, and AI Forging explicitly delegates to it. When Claude is implementing any feature or bug fix under this framework, it invokes the `superpowers:test-driven-development` skill and follows that skill's discipline:

> Write the test first. Watch it fail. Write minimal code to pass. If you didn't watch the test fail, you don't know if it tests the right thing. Violating the letter of the rules is violating the spirit of the rules.

If that skill isn't available in this session, STOP. Either install the superpowers plugin (see the plugin's main README or re-run `/aiforging:setup`) or confirm with your human partner that you're intentionally proceeding without it. Do not reinvent the loop inline.

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
- **Never mock the database in a Repository test.** Stand up the real thing via the test harness. See `tdd/repository-testing.md`.
- **Never proceed with Fire-stage work if the test harness can't satisfy the capability contract.** Fix the harness first. That's a prerequisite, not a luxury.

## Related

- `tdd/test-harness-requirements.md`
- `tdd/repository-testing.md`
- `refactoring/README.md`
- `architecture/domain-driven-hexagonal.md`
