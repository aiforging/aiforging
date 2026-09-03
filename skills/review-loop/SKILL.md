---
name: review-loop
description: Run multiple rounds of code review and fixes on a feature branch across every implicated target repo, without pasting review output between terminals. Spawns one review subagent per repo, triages findings against the source and against prior rounds, classifies each green/amber/red, plans accepted findings into work items, dispatches fixes serialized per repo, and repeats until a stated stop condition. Optional stage that runs AFTER browser-testing. Trigger on "/aiforging:review-loop", "run the review loop", or a request for several rounds of review-then-fix. Do NOT trigger for a single one-off review.
---

# Review Loop

> **Optional stage, after the forge and after `browser-testing`.** Automates the review → triage → fix → re-review cycle that is otherwise run by hand across several terminals and pasted back.

Like `hammer-refactor`, this skill is a **dispatcher**: it decides what to review, verifies what comes back, and hands fixes to fresh-context subagents. It follows `conventions/subagent-orchestration/README.md` — the parent is a conductor, not a performer.

---

## What this is not

- **Not a merge signal.** A clean loop means "no more code-visible defects found," and nothing else. The human's full test suite, their own manual QA, and their own code review remain required and are not automated here. **Say so in the completion message, every time.**
- **Not browser testing.** That is `/aiforging:browser-testing` — a sibling that runs *before* this, reads the running product rather than the diff, and never auto-fixes. Do not fold it in.
- **Not a Hammer pass.** `hammer-refactor` applies a known pattern library to changed files. This looks for defects the library does not name. Different question, different skill.
- **Not for a single review.** One pass over a diff is a one-shot review request, not this.

---

## Before starting

### 1. Resolve the workspace and the feature

Same resolution as the other AI Forging skills: the cwd is the workspace if `./CLAUDE.md` contains the string `AI Forging workspace` and `./docs/features/` exists; otherwise read `active_workspace` from `~/.claude/aiforging.json` (opt-in, so it may not exist) and apply the same check there; otherwise ask.

Then identify the feature folder under `<workspace>/docs/features/` and **confirm it with the user.** Round records land there.

### 2. Clean trees, everywhere

Every implicated repo must have nothing uncommitted. Stop and say so otherwise — concurrent agents plus a dirty tree is how one agent's work gets swept into another's commit.

### 3. Derive the implicated repos from the diff — do not assume

Get the candidate targets from the workspace scenario:

- **Multi-repo**: `permissions.additionalDirectories` in `<workspace>/.claude/settings.local.json`.
- **Monorepo**: sub-directories containing `.aiforging/`.
- **Single repo**: the workspace root.

Then narrow to the repos the feature's branch actually touches. A repo with no diff gets no review agent.

### 4. Establish the base branch per repo — never hardcode it

**This is the step that quietly ruins a round.** Reviewing against the wrong base is not a small error: it produces a diff full of other people's work and a full round of findings that are not yours.

Different repos in the same workspace often have different bases, and a base is frequently a **moving target** — a team may branch features from an integration branch, or from a dated release branch (`2026.08B`) that is re-cut regularly. **Never hardcode a base, never carry one over from a previous round, and never trust a single heuristic:**

- The newest release branch may have been cut *after* this work started.
- The currently checked-out branch may be stale.

Derive the candidates and **confirm with the user, per repo**:

```bash
git -C <repo> branch -r --sort=-committerdate | head -10
git -C <repo> merge-base --fork-point <candidate> HEAD   # sanity-check the fork point
git -C <repo> log --oneline <candidate>..HEAD | wc -l    # does the diff size look like this feature?
```

Record the confirmed base per repo in the round's findings header. If the base changes between rounds, say so loudly — the finding sets are not comparable.

### 5. Record the baselines

Test counts, lint counts, type-error counts, and the runtime/toolchain pin for each repo (a Node or PHP version mismatch produces phantom failures that get reported as findings in every round until someone notices). Review agents get these as **input**, so they classify pre-existing failures correctly instead of reporting them as findings.

### 6. Read the prior verdicts

Read `<workspace>/docs/features/<feature>/ai-reviews/triage-notes.md` if it exists, plus every prior round's `ai-reviews/NN/triage.md`. These are a **required input** to every review agent — see Convergence below. Without them the loop cannot terminate.

### 7. Verify the review capability before fanning out

Each review agent's *first* action is to confirm it can actually perform a review — that whatever code-review capability this session provides is present in *its* listing and invocable — and to **report plainly if it is not, before doing any work.**

Availability at the parent level is not proof of operation at the agent level. The failure mode otherwise is an agent that burns several minutes and returns an empty findings file the orchestrator then has to diagnose mid-round.

If an agent reports the capability missing, **stop the round and tell the human.** The skill's shape then changes to *"orchestrate and triage"* — the human runs the reviews, this skill structures what comes back — and that is a decision for them to make, not a fallback to improvise.

**If the session has no code-review capability at all**, this skill still works: review agents fall back to the rubric in "What a review agent reviews against," below, which is built from artifacts AI Forging already installs in every target.

---

## The round

```
  ┌─→ 1. spawn one review subagent per repo   (parallel — reviews are read-only)
  │   2. each returns structured findings, written to ai-reviews/NN/
  │            ↓
  │   3. TRIAGE — verify every finding against the source; reject the intended, with evidence
  │            ↓
  │   4. CLASSIFY green / amber / red
  │            ↓
  │      any RED ──────────────→ stop the round, ask the human
  │            ↓ (green / amber)
  │   5. plan accepted findings into work item(s) per the feature convention
  │   6. dispatch fix agents — SERIALIZED per repo
  │            ↓
  └─── 7. re-review, or stop (see Stopping)
```

### 1–2. Review agents

One per repo, in parallel — reviews are read-only and cannot collide. Each agent:

- runs at the effort level the user named, if they named one — and **passes it in the form the underlying capability expects.** A level passed in the wrong position is silently ignored and the run falls back to the cheapest setting, which looks like a completed review and is not one;
- reports its **run profile** (tool uses, wall time, whether static analysis ran) in the findings file header, rather than quoting whatever banner the review tool printed. A subagent often cannot observe its own effort banner; the profile distinguishes the levels just as well;
- is given the **confirmed base**, the **baselines**, and the **prior triage verdicts** as input;
- writes `ai-reviews/NN/findings-<repo>.md` **as it goes**, not only at the end. An agent that dies 80% through then leaves 80% of its findings usable.

**Never run a review while a fix agent is live in the same repo.**

#### What a review agent reviews against

In priority order, all of it already present in an onboarded AI Forging target:

1. **Correctness against the feature's `spec.md`** — does the diff do what was agreed?
2. **The target's `.aiforging/anti-patterns/` and `.aiforging/patterns/`** — both tiers, merged and stack-filtered the same way `hammer-refactor` merges them. A finding that names a pattern file is a finding a fix agent can act on precisely.
3. **The target's `.aiforging/architecture/` conventions and root `CLAUDE.md`** — placement, naming, layering.
4. **The usual defect classes** — error handling, boundary conditions, auth and tenancy, N+1 queries and other data-access costs, concurrency, missing or vacuous tests.

Every finding must carry a `file:line` and a concrete failure scenario. A finding that cannot name where it lives is not a finding.

### 3. Triage — the step this loop is built on

**Verify every finding against the source before accepting it.** In the reference implementation roughly **a third of findings described deliberate behavior**, and several were real but for a different reason than stated. Two reported as one duplicate concern were not duplicates.

Record a verdict per finding ID **with evidence** — a grep, a `file:line`, a config value, a query result. *"I checked and it's fine"* is not a verdict.

**Triage's own failure modes** — all four of these happened, and each produced a wasted round:

- **The plan cites a defective exemplar.** If a fix instruction says "do it like `X` does," the fix agent must verify `X` is actually correct. One plan pointed at a helper that was itself broken.
- **Under-scoping to the sites the reviewer named.** For any "X is missing at Y," ask *where else does this shape occur* and enumerate. Every theme patched instance-by-instance came back in a later round; every one enumerated closed and stayed closed.
- **Prescribing a fix that does not work.** Describe **the property that must hold**, not the edit. One prescribed reordering was a no-op.
- **Mis-stating a mechanism.** Say what you verified and how you verified it.

**Cross-round detection is mechanical; the decision is not.** Flag any finding landing on the same file and near the same line as an earlier round's, and surface it. **Never merge automatically.** A *new* finding on a line a previous round just changed is the **thrash signal** — treat it as one.

### 4. Classify — by class, never by felt confidence

The obvious gate — *"proceed unless I have questions"* — fails silently, because an agent that is confident is exactly the one that does not ask. So classify by what the change *is*, not by how sure you feel:

- **GREEN — auto-fix.** Local, mechanical, behavior-preserving, one obvious correct form.
- **AMBER — auto-fix, report prominently.** The correct fix is clear but the change is user-visible.
- **RED — stop and ask.** Changes a recorded decision; diverges from a source implementation being ported; touches auth, tenancy, or data integrity; changes an API contract; edits code **outside** the feature; or the right answer depends on product intent.

**Any RED halts the whole round**, not just that finding — a partial fix set can invalidate the rest of the triage.

### 5–6. Plan and dispatch

Accepted findings become work per `conventions/features/README.md`, using the shapes that convention actually defines — do not invent a new folder layout for review work.

- **Flat shape**: add numbered follow-up slices to the end of the feature's `plan.md`. Never rewrite or renumber a completed slice; a slice that already dispatched is history.
- **Nested shape**: review work gets its own numbered work item (`NN-review-fixes`, continuing the existing sequence) with its own `spec.md` and `plan.md`. **Never renumber existing work items.** Successive rounds append slices to that same work item's plan rather than creating a work item per round — the round number is already recorded in `ai-reviews/NN/`, and one work item per round buries the feature's real structure under review bookkeeping.

Fix agents:

- **Serialized per repo.** A shared test database cannot take two. Reviews may parallelize; fixes may not.
- **Strict TDD** via `superpowers:test-driven-development`, and **a commit per red-green-refactor cycle**.
- **Scoped test runs only** — the feature's named suite, never the full repository suite. See `conventions/tdd/feature-test-suite.md`. This applies to fix agents exactly as it applies to Fire and Hammer agents.
- **Every fix needs a regression test that fails against the unfixed code.** Where one genuinely cannot be written, say so explicitly rather than contorting a test into existence.
- **Every fix prompt must invite push-back with evidence.** In the reference implementation, *every* fix agent that disagreed with the plan turned out to be right — twelve times, including a plan gap, a no-op fix, a defective exemplar, and two mis-stated mechanisms. It only happens if the prompt asks for it.

### 7. Stopping

**Neither finding count nor severity is a stop signal.** Both were tried and both misled: the count settled into a floor with noise (8, 7, 6, 4, 4, 5, 4, 4) and severity *fell* for five rounds and then rose.

Stop when **the remaining risk in a module is better addressed by observing it than by reading it again** — and then go and observe it: a human using the product, or another `browser-testing` run scoped to that module.

That is not a contradiction of the stage ordering. The rule is that browser testing comes *first*, so that behavioral defects and wrong decisions surface before rounds of review get built on top of them. It is not a rule that observation happens only once. Sending a specific, narrowed question back to the product is the correct exit from a review round that has stopped learning anything.

Also stop on:

- a **hard round cap of 2 rounds.** Round 3 and beyond requires the user to explicitly opt in, each time. Two rounds is enough to learn whether the findings are converging;
- **recurrence** — a finding returning after a "fix." Either the fix was wrong or the finding was always intended. Escalate; do not spend another round;
- the human saying so.

**Report tokens per round**, so the opt-in past round 2 is an informed one.

---

## Convergence — or the loop never terminates

Reviewers re-flag settled decisions. In the reference implementation one docblock was flagged in three consecutive rounds by three independent agents.

1. Prior triage verdicts are a **required input** to every review agent.
2. Every "this is intended" verdict is **appended to `ai-reviews/triage-notes.md`** at the feature level, with its evidence.
3. A finding contradicting a recorded verdict needs **new evidence**, not a re-assertion.
4. For repeat offenders, put the rebuttal **in the code** — a short do-not-re-flag comment naming the test that pins the behavior. That is what the reviewer actually reads, and it is what finally stopped the three-round recurrence.

Point 4 is also a **Tempering signal**: a decision that reviewers keep re-litigating is a decision the pattern library does not yet encode. Offer `capture-pattern` on it.

---

## Escalations

A pass that **sees a problem, correctly declines to act on it, and has nowhere to put it** is how the reference implementation lost a finding that then survived four more rounds and a pull request.

Findings that are real but outside a pass's remit go to `ai-reviews/NN/escalations.md`, and **the orchestrator surfaces that file's contents to the human every round** — in the message, not as a path. Writing escalations nobody reads reproduces the failure exactly.

Distinguish clearly: a **rejection** says *"not a problem."* An **escalation** says *"a problem, and not mine to fix."*

---

## The round record

```
<workspace>/docs/features/<feature>/ai-reviews/
  triage-notes.md         accumulated "this is intended" verdicts, with evidence
  01/
    findings-<repo>.md    one per implicated repo, written as the agent goes
    triage.md             a verdict per finding ID, with evidence
    escalations.md        real, out of remit — surfaced to the human every round
  02/
    ...
```

Numbered, append-only. A re-run is a new folder; never overwrite an earlier round.

---

## Safeguards

| | |
|---|---|
| **Clean trees** | Verified before spawning and after every agent returns. A dirty tree after an agent death stops the round for human inspection |
| **No `git add -A`** | Ever. Stage explicit paths — agents have swept another agent's in-flight work into a commit |
| **Serialize fixes per repo** | Shared test database. Reviews may parallelize; fixes may not |
| **Confirmed base per repo** | Never hardcoded, never carried over silently. A wrong base yields a round of other people's findings |
| **Scoped suites only** | The feature's named suite. Full suites are the human's job — see `conventions/tdd/feature-test-suite.md` |
| **Baselines as input** | Or every round re-reports pre-existing failures. One toolchain version mismatch produced phantom failures in two separate reviews |
| **No self-scheduled wake loops** | A finished agent once fired empty notifications for twenty minutes. Stop each agent on completion |
| **Overload / rate limits** | Retry with backoff and jitter; classify transient vs fatal; degrade fan-out to serial under load; after the cap, **park the round and tell the human** — never spin |
| **Resume** | The plan's checkboxes plus `git log` are the ledger. A resumed fix agent re-reads the plan and skips checked tasks |

---

## Relationship to other AI Forging pieces

- **`browser-testing`** runs before this. It reads the product; this reads the diff. Six review rounds cannot find a feature that works exactly as written and is wrong.
- **`hammer-refactor`** runs before both, during implementation. It applies the pattern library; this finds what the library does not name.
- **`capture-pattern`** is the natural exit for a finding class that recurred across rounds — that is a missing pattern, and capturing it stops the next feature from producing the same finding.
- **The full test suite** never runs here. It is handed to the human at the end.

---

## A note on the paths in this file

References like `conventions/tdd/feature-test-suite.md` name files in the **AI Forging plugin's** conventions library. Where you actually find a given file depends on where you are:

- **In an onboarded target repo** — the architecture, tdd, and subagent-orchestration conventions are installed at `<target>/.aiforging/`, so `conventions/tdd/feature-test-suite.md` is `<target>/.aiforging/tdd/feature-test-suite.md`.
- **In the forge workspace** — the feature convention is installed at `docs/features/README.md`, and the pattern-library README at `.aiforging/README.md`.
- **In the plugin itself** — everything is under `${CLAUDE_PLUGIN_ROOT}/conventions/`, which is readable but never writable.

If a referenced file is not where you expect, say so rather than proceeding on a guess about what it said.

---

## Completion message

State, every time:

1. Rounds run, findings by verdict, and what was actually fixed.
2. **The contents of `escalations.md`** — surfaced, not referenced.
3. The stop condition that fired, and why.
4. Tokens spent per round.
5. **What this does not replace**: the human's full test suite — which no AI Forging stage runs, and which they must run before a PR — their own manual QA pass over `testing.md`, and their own code review. **A clean loop is not readiness to merge.**
