---
name: browser-testing
description: Walk a feature's testing.md in a real browser and report what diverged, without fixing anything. Verifies testing.md exists in the forge workspace's feature folder, marks the items only a human can judge, walks the rest against a local or named QA environment, records one line of textual evidence per step, and hands every failure to a human conversation. Optional stage that runs after implementation and BEFORE review-loop, never as part of it. Trigger on "/aiforging:browser-testing", "walk testing.md", or a request to verify a feature in the browser.
---

# Browser Testing

> **Optional stage, after Fire / Hammer / Tempering.** The forge produced code that passes its tests. This skill goes and uses the product, walks the human QA checklist the feature already has, and reports where the running app and the agreed specification disagree. It changes nothing.

It runs **before** `review-loop`, deliberately. See "Where this sits."

---

## The rule that governs everything else

**A behavioral flaw found in the browser triggers a human conversation. Nothing else.**

Not a fix. Not a work item. Not a plan. Not a retry until it passes. It is written down and brought to a person.

This is not caution for its own sake. In the reference implementation this skill was extracted from, a QA pass found that a user in a delegated-access role was denied a screen the checklist said they should keep — a decision that had been taken deliberately, implemented on two layers, and pinned by three passing tests. An automated responder would have read *expected access, got 403* and **fixed the symptom exactly as specified.** What actually happened is that a human said *"come to think of it, the denial may be preferable"* — which reversed the original decision, removed a divergence from the ledger, and produced a better feature.

> **A failing step is evidence that the product and the specification disagree. It is not evidence about which one is wrong.** Deciding that requires knowing what the feature is *for*, and that lives in the person.

An auto-fixer here is worse than no browser testing at all: it would cement the wrong assumption *and* produce a green checklist attesting to it.

**May do:** execute steps · record what happened, with evidence · mark pass / fail / **unexpected** · bring every failure and every unexpectation to the human, and stop.

**May never do:** edit source · open a work item · add a slice to `plan.md` · retry differently until it passes · decide that a failing step was a bad step.

---

## Preconditions — stop rather than improvise

### 1. Resolve the forge workspace

Same resolution the other AI Forging skills use:

- **Session is inside the workspace** (multi-repo, monorepo, or single-repo): `./CLAUDE.md` exists and contains the string `AI Forging workspace`, and `./docs/features/` exists as a directory. That pair is what `/aiforging:setup` Phase A writes; the same check `/aiforging:new-feature` uses. The workspace is the cwd.
- **Session is inside a target repo**: read `~/.claude/aiforging.json` for `active_workspace`, verify the path exists and passes the same check. (The pointer file is opt-in, so it may not exist.)
- **Neither**: ask the user where the forge workspace is. Do not guess.

### 2. Identify the feature folder — and confirm it

Derive a candidate from recent activity under `<workspace>/docs/features/` — most-recently-modified folders first — and, *if* the team's branch names happen to match feature-folder names, from the current git branch. Nothing in AI Forging creates branches or requires that correspondence, so treat a branch-name match as a hint and never as an answer.

Then **state your candidate and have the user confirm it.** Do not assume. Walking the wrong feature's checklist produces a report that looks authoritative and describes nothing.

### 3. `testing.md` must exist there

If `<workspace>/docs/features/<feature>/testing.md` is missing — **stop and escalate.** Report the folder you looked in.

**Do not invent a checklist.** The document *is* the specification of what correct looks like; a run against a guessed one tests whatever the machine happened to imagine, and then reports a verdict on it. If the feature has a UI surface and no `testing.md`, the fix is for a human to write one — not for you to fill the gap. Point them at `/aiforging:new-feature`, which scaffolds the skeleton, and at the workspace's own `docs/features/README.md`, which documents the three sections a checklist must cover. (If the `aiforging` plugin is installed in this session, the skeleton is also at `${CLAUDE_PLUGIN_ROOT}/templates/feature-testing.md`; if you are running from a workspace copy of this skill without the plugin, that variable is unset — use `docs/features/README.md` instead of guessing a path.)

For a **nested** feature there is one `testing.md` at the feature level, not one per work item. If you find several, stop and ask which is authoritative rather than merging them.

### 4. Local or an explicitly-named QA environment only

**Never production. Never a shared environment unless the user names it in this session.** This is the highest-privilege thing this skill does — it drives a real application as a real user and, below, writes to a database. Confirm the environment out loud before the first step and abort if the answer is ambiguous.

### 5. A browser you can actually drive

Confirm the browser automation available in this session is connected and that the target origin is reachable *before* starting the walk. Depending on the setup that may be a browser extension, a browser MCP server, or a headed automation driver — this skill does not care which, but it does care that you check first and say plainly if it is missing, rather than discovering it mid-walk and leaving the app in a half-driven state.

Where a per-site permission is required and has not been granted, say so. That permission is granted by the human in their browser's own settings and **cannot** be granted from here.

### 6. A clean git tree in the workspace

Step 1 edits `testing.md`, a document a human wrote. A clean workspace tree is what makes that edit visible and trivially reversible rather than buried in unrelated changes.

Target repos are a different matter. This pass never writes to them, so their trees can be dirty — but **say so if they are**, because a step that fails against uncommitted work is a finding about a work-in-progress, not about the feature, and reporting it as the latter wastes a conversation. Derive the touched repos the same way `review-loop` does (the workspace scenario: `permissions.additionalDirectories`, a monorepo scan, or the repo root) if you need the list; otherwise just ask which repo is running.

---

## Step 1 — Mark the human-only items, inline

Read `testing.md` and mark every item a machine cannot produce a *trustworthy* verdict on:

```markdown
- [ ] Search filters by company name; paging works and the total count is right
- [ ] 👤 Renders correctly in dark mode
- [ ] 👤 The stage wording reads clearly to someone who did not build this
```

**Inline, never moved into a separate section.** A checklist's order encodes how the app is actually used; hoisting the visual items out of that walk means testing them out of context and duplicating every heading.

Add the legend at the top of the file if it is not already there (the template ships with it).

**Judge by whether a machine could produce a verdict you would *believe*, not whether it could produce one at all.** A run can screenshot a dark-mode screen; it cannot tell you the screen looks right. **When uncertain, mark it** — a false 👤 costs a human thirty seconds, a missed one produces a confident lie.

Signals that an item is 👤: visual and layout judgement · color and theme · "looks right" · "reads clearly" · typography and spacing · comparison against another implementation or a design · anything about a rendered document, chart, or image.

**Report exactly what you marked.** This edits a document a human wrote, so the change must be visible and trivially reversible — never silent.

Then tell the user they can work the 👤 items **in parallel** while the walk proceeds. That parallelism is the point of the marking pass: two testers, one machine and one human, on the same checklist at the same time, each doing the part they are actually good at.

---

## Step 2 — Walk the unmarked items

Drive the app. Skip every 👤. For each step record **one short line of plain text** — never screenshots. Screenshots are heavy, undiffable, and unread.

```
✓ A user in a delegated-access role is denied the diagnostics screen
  Signed in as user 4412 (role: delegate at org 17), switched to org 1293, loaded
  /admin/diagnostics → redirected to /403; Diagnostics absent from the admin nav.

✗ Reopening the dialog forgets the search                       ← UNEXPECTED
  Typed "plumb", closed, reopened: the list still showed the 4 filtered rows and
  the search box was empty.
```

Name the **actor** and the **subject**. *"Signed in as user 4412, switched to org 1293"* is checkable in a way *"verified access is denied"* is not. Do this only where it is useful — a step whose evidence would just paraphrase its own title should simply be ticked.

The evidence line is also what catches **a step that passed for the wrong reason.** *"The empty state rendered"* reads fine until the line says the account had thirty records.

### Browser differences are a real source of false findings

**Record which browser every keyboard-related step used, and never report a keyboard finding without naming the browser.** In the reference implementation a manual pass reported that table rows were unreachable by keyboard; it reproduced in one browser and not another, because **Safari on macOS tabs between form controls only by default**, skipping links and buttons unless *Settings → Advanced → "Press Tab to highlight each item"* is enabled (Option-Tab works regardless). That single omission cost a work item's entire premise, two corrected documents, and a wrong hypothesis that survived several conversations.

### Do not trigger native dialogs

`alert` / `confirm` / `prompt` block most browser automation entirely, and the run cannot recover. Prefer flows that avoid them; warn the user before any that cannot be avoided.

---

## Database access — for lookup and for seeding

Both are in scope and both are useful. **Local development database only** — the same environment constraint as the browser walk, enforced separately because it is easy to have a local browser pointed at a remote database.

Get connection details from the target repo's own documentation (`CLAUDE.md`, `.aiforging/`, `.env.test`, the repo's README). Do not invent credentials and do not reuse a connection string the user has not shown you.

**Lookup** — find what to test against: which user holds which role at which organization, which record has enough rows to page, whether a permission row exists at all. Hunting through the UI is slow and often impossible, and guessing produces steps that pass vacuously.

**Seeding** — make a state reachable. Checking pagination needs 25+ rows on one record; by hand that is an hour of clicking, as SQL it is two statements.

### Rules

1. **Mark every seeded row, and report the cleanup statement with the run.** Put a recognizable token — `[QA SEED]` — in a text column on every inserted row, so removal is one `DELETE ... WHERE ... LIKE` that provably cannot touch hand-made data.
2. **Respect the schema's real invariants.** In the reference implementation a seed had to satisfy a partial unique index; a naive bulk insert would have failed or, worse, been "fixed" by dropping the constraint. **Verify invariants after seeding**, not just row counts.
3. **Say what seeded data cannot prove.** Rows inserted directly have no child records, so they exercise paging and ordering and say nothing about calculation, scoring, or generated documents. A step that needs real data must use real data, and the report must not blur the two.
4. **Restore session state.** Impersonation, organization switching, and feature flags are UI flows; a run that dies mid-way leaves the human signed in as someone else, inside the wrong organization, with a flag flipped. End where you began, and say so.
5. **Never seed, and never write, outside the local development database.** If the environment is anything else, lookups are read-only and seeding is off.

---

## The run record

```
<workspace>/docs/features/<feature>/ai-testing/
  01/
    run.md          one evidence line per step; pass / fail / unexpected
    escalations.md  everything that diverged — the handoff to a conversation
  02/
    ...
```

Numbered, append-only. A re-run is a **new** folder; never overwrite an earlier one.

`escalations.md` **is** the deliverable, because the governing rule forbids acting on any of it.

A re-run after fixes is **scoped to what previously failed**, plus anything a fix plausibly touched. Re-walking everything after every fix is how a checklist stops being run at all.

---

## Where this sits

| Step | Who |
|---|---|
| 1. Feature built to presumed-working through Fire → Hammer → Tempering, with a `testing.md` | AI + human decisions |
| 2. **`/aiforging:browser-testing`** walks it — while the human works the 👤 items in parallel | both, concurrently |
| 3. Report what diverged → **conversation** → findings become work items only once a human agrees | human decides |
| 4. Re-run, **scoped to what failed** | AI |
| 5. Once clean, **`/aiforging:review-loop`** | AI, human-gated |
| 6. The human's full test suite · their own pass over `testing.md` · their own code review · then a PR | human only |

**Step 2 comes before step 5, deliberately.** In the reference implementation six review rounds ran to near exhaustion while two behavioral defects sat in the most-used screen — one of them a *wrong decision*, and the cheapest moment to reverse a decision is before ten work items have been built on top of it. Reading the diff harder does not find a feature that is working exactly as written and wrong.

Both steps are **optional**. Fire → Hammer → Tempering is the framework; these two are the checks a team turns on when a feature has a UI surface and enough surface area to warrant them.

---

## Relationship to other AI Forging pieces

- **`testing.md`** (`conventions/features/README.md`) is the required input. This skill has no authority to create it.
- **`hammer-refactor`** runs before this, and shapes code. This skill runs after, and reads behavior. Do not fold either into the other.
- **`review-loop`** runs after this. It reads the diff; this reads the product. Distinct failure classes, distinct skills.
- **`capture-pattern`** is where a *code-shaped* lesson from a browser finding goes — but only after the human conversation has decided the finding is real. Never capture a pattern from an unadjudicated failure.
- **The full test suite** is not this skill's job and never runs here. See `conventions/tdd/feature-test-suite.md`.

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

1. **What was marked 👤**, and that the human owns those items.
2. **Steps walked**, with counts: passed / failed / unexpected.
3. **The contents of `escalations.md`** — surfaced in the message, not merely referenced by path. An escalation nobody reads is an escalation that was lost.
4. **That nothing was fixed**, and that every finding needs a conversation before it becomes work.
5. **The cleanup statement** for any seeded data, and confirmation that session state was restored.
6. **What this does not replace**: the human's own pass over `testing.md`, their full test suite — which no AI Forging stage runs, and which the human must run themselves before a PR — and their own code review. **A clean run is not readiness to merge.**
