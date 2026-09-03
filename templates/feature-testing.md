<!--
  AI Forging testing.md — human QA checklist.

  Written into <workspace>/docs/features/<feature-name>/testing.md.
  Source of truth for this convention: conventions/features/README.md
  ("The files in a feature folder"). If you change one, change the other.

  Required for every feature with a UI surface. Research-only work and purely
  internal / pipeline changes with no visible behavior may skip it — but say so
  in spec.md rather than silently omitting this file.

  Write it BEFORE implementation is finished, from the spec. A checklist written
  afterwards describes what was built; one written from the spec describes what
  was supposed to be built, and the gap between those two is the bug.

  This file is the required input to /aiforging:browser-testing. That skill will
  refuse to run without it and will not invent a checklist.
-->

# Testing — <feature name>

> **How to use this.** These are steps a person performs in the running app, in order. Check
> each box as you go. Items marked 👤 need human judgement — a machine can screenshot a screen
> but cannot tell you it looks right — so those stay yours even when
> `/aiforging:browser-testing` walks the rest.
>
> 👤 = human judgement required.

**Environment:** local, or a named QA environment. Never production.

<!--
  For a nested feature (3+ work items), keep ONE checklist at the feature level and order it
  by work item in dependency order, using the work item as the heading:

    ## 01 — <work item name>
    ### Access and gating
    ### Happy path
    ...

  One checklist that walks the feature the way a user actually meets it beats five checklists
  nobody opens.
-->

## Access and gating

Who can reach this, and confirmation that the people who should not, cannot.

- [ ] A user *without* `<permission / role>` gets denied on `<route>` and sees no navigation entry for it
- [ ] A user *with* `<permission / role>` reaches `<route>` and sees the feature
- [ ] <any tenancy / company-scoping rule: user in org A cannot see org B's records>

## Happy path

The reason the feature exists, walked end to end.

- [ ] <the primary action, with concrete input: "create an invoice for $1,250 with two line items">
- [ ] <what should now be true: "it appears in the list with the correct total and status">
- [ ] 👤 <anything judged by eye: "the summary panel reads clearly to someone who did not build this">

## Edge cases

The empty state, the boundary, the denial, the thing that fails.

- [ ] Empty state renders the "no results" copy, not a blank table
- [ ] Submitting with `<required field>` blank shows an inline error and saves nothing
- [ ] <pagination / large data: "with 25+ rows, page 2 loads and the total count is right">
- [ ] <the failure path: "when `<dependency>` is unavailable, the user sees `<message>` rather than a stack trace">

## Notes for the tester

<!-- Anything the person needs before they start: a seeded account, a feature flag to enable,
     a specific record to use, a known-unrelated bug that will show up and can be ignored. -->

- <e.g. "Use the demo company; the sandbox one has no historical data.">
