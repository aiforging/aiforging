---
name: capture-pattern
description: Use when the user corrects your code, rejects a diff, asks you to clean up or redo work, or says something like "that's not how we do it" or "always/never do X" — offers to capture the lesson as a reusable pattern or anti-pattern in the AI Forging pattern library, closing the Tempering feedback loop.
---

# Capture Pattern — the Tempering feedback loop

## Overview

When a human corrects your work during an interactive session, the correction often encodes a reusable rule. This skill detects those moments and offers to persist the lesson as a pattern or anti-pattern in the AI Forging library — specifically in `<target>/.aiforging/patterns/` or `<target>/.aiforging/anti-patterns/` — so that every subsequent `hammer-refactor` run against that target checks new code against the new rule.

This skill is **the Tempering pillar made operational**. The Fire stage (TDD) produces working code. The Hammer stage (`hammer-refactor`) refactors it against the existing pattern library. The Tempering stage is how the library *grows* — one captured lesson per code review, one `.md` file per pattern. Every team member contributes by doing their normal code reviews; the skill is how that knowledge gets persisted.

**This skill is reactive, not proactive.** Do not invoke it at session start. Invoke it when a corrective moment occurs mid-conversation and you assess that the correction encodes a reusable, structural rule.

**Bias toward NOT prompting.** When in doubt, do not ask. An over-eager capture-pattern prompt trains the human to say "no" reflexively, which kills the whole feedback loop. One good capture is worth ten declined prompts.

## When to Trigger

**Trigger when the human:**

- Rejects a diff and explains why ("don't do it that way, do it this way").
- Asks you to go back and clean up or redo something you wrote.
- Says "that's not how we do it," "always do X," "never do Y."
- Points out a structural mistake (wrong abstraction, wrong layer, wrong pattern).
- Corrects naming conventions, code organization, or architectural choices that plausibly recur across features.

**Do NOT trigger when the correction is:**

- A contextual business rule (wrong field name, wrong API endpoint, wrong enum value) — that's not a reusable pattern, it's a bug fix.
- A typo or simple mistake with no generalizable lesson.
- Already covered by an existing pattern or anti-pattern file in the target's library.
- A one-time fix unlikely to recur in future features.

## Execution

### Step 1 — Recognize and offer

When you detect a corrective moment, ask concisely:

> "Would you like me to capture this as a [pattern / anti-pattern] for the `hammer-refactor` library? It would live at `<target>/.aiforging/{patterns|anti-patterns}/<name>.md` and be picked up on every subsequent Hammer pass."

If the correction is clearly about what NOT to do, say "anti-pattern." If it's about the right way to do something, say "pattern." If ambiguous, ask which.

If the human declines, drop it. Do not re-ask for the same correction in the same session.

### Step 2 — Resolve the target library

This skill is installed in two places: inside each onboarded target repo (at `<target>/.claude/skills/capture-pattern/SKILL.md`) AND inside the forge workspace (at `<workspace>/.claude/skills/capture-pattern/SKILL.md`). The writing destination depends on where the session is running.

**Case A — session is running inside a target repo.**

Detect with:

```bash
test -d ./.aiforging/patterns && test -d ./.aiforging/anti-patterns && echo "IN_TARGET_REPO"
```

If both directories exist, the cwd is the target. Write to `./.aiforging/patterns/<name>.md` or `./.aiforging/anti-patterns/<name>.md`. No picker needed.

**Case B — session is running inside a forge workspace.**

Detect with:

```bash
test -f ./CLAUDE.md && head -c 500 ./CLAUDE.md | grep -q "AI Forging workspace" && \
  test -f ./.claude/settings.local.json && echo "IN_FORGE_WORKSPACE"
```

If the cwd is a workspace, read the registered targets from `./.claude/settings.local.json` at `permissions.additionalDirectories`. Then:

- **Zero targets registered** → tell the human: "This workspace has no target repos registered yet. Run `/aiforging:setup` from the workspace to onboard a target before capturing patterns." Stop.
- **Exactly one target registered** → use it. Confirm with the human: "I'll save this pattern to `<that-target>/.aiforging/{patterns|anti-patterns}/<name>.md`. OK?"
- **Multiple targets registered** → ask the human to pick: "Which target repo does this pattern apply to? [list the targets from settings.local.json]". Do NOT guess from the current conversation — the human might be thinking about a repo other than the one whose code was on screen when the correction happened.

**Case C — neither a target repo nor a forge workspace.**

Tell the human: "I can only capture patterns from inside a target repo or an AI Forging workspace, and neither looks like the case here. Are you in the right directory?" Stop.

### Step 3 — Check for duplicates

Before drafting anything, scan the resolved target's existing library:

```bash
ls <target>/.aiforging/patterns/
ls <target>/.aiforging/anti-patterns/
```

Read any file whose name or topic might overlap. If an existing file covers the same ground:

- Offer to **update** the existing file instead of creating a new one.
- Show the human the existing file's `## Rule` and `## Detect` sections and ask: "This seems to overlap with `<existing-file>`. Should I extend that file or create a new one?"
- If the existing file is close but the current correction adds a new facet, extending is usually the right call — unless the new facet is substantial enough to warrant its own file.

### Step 4 — Draft the file in AI Forging format

Use the AI Forging pattern format (documented in `<target>/.aiforging/patterns/README.md` if it was seeded during onboarding, or in the plugin source at `conventions/refactoring/README.md`). This is a simpler format than some other projects use — no `Category:` header, no `Safe to auto-refactor:` flag, just the six sections below.

**For a pattern:**

```markdown
# <Pattern Name>

## Rule

<One or two sentences stating the rule as plainly as possible.>

## Why

<The reasoning. Link to architectural principles in `.aiforging/architecture/` where relevant.>

## Detect

<How to recognize when this pattern should be applied, in mechanical terms a
subagent can check. File structure, naming, method shape, signal phrases in
code — be specific.>

1. <First signal.>
2. <Second signal.>
3. <Etc.>

## Apply

<Step-by-step how to apply the pattern. Include a code sketch.>

1. <First step.>
2. <Second step.>
3. <Etc.>

### Before

\`\`\`<language>
<The code the human rejected.>
\`\`\`

### After

\`\`\`<language>
<The corrected version the human endorsed.>
\`\`\`

## Don't apply when

<Edge cases where the pattern does not belong.>

## Related

- <Cross-reference to related patterns or anti-patterns in the library.>

## Source

Captured during interactive session on <YYYY-MM-DD>.
```

**For an anti-pattern:**

```markdown
# <Anti-Pattern Name>

## Rule

<One or two sentences stating what NOT to do.>

## Why

<Reasoning — what goes wrong when this anti-pattern is present.>

## Detect

<Mechanical detection signals. Be specific — anti-pattern files are consumed
by subagents during the Hammer pass, and vague signals produce false
positives that train humans to ignore the feedback.>

1. <First signal.>
2. <Second signal.>
3. <Etc.>

## Eliminate

<Step-by-step how to remove the anti-pattern from a codebase where it
exists.>

1. <First step.>
2. <Second step.>
3. <Etc.>

### Before

\`\`\`<language>
<The anti-pattern as it appeared in the code being reviewed.>
\`\`\`

### After

\`\`\`<language>
<The corrected version.>
\`\`\`

## Don't apply when

<Cases that look similar but are actually acceptable — pragmatic exceptions.>

## Related

- <Cross-reference to the corresponding pattern file (if one exists), or to
  architecture docs.>

## Source

Captured during interactive session on <YYYY-MM-DD>.
```

Fill in the template from the actual correction you and the human just worked through. The `Before` code block is the code the human rejected; the `After` block is whatever the two of you landed on. Use real code from the session, not invented examples.

**Stack-specific language in Before/After.** Use whatever language the target is written in — `php`, `typescript`, `python`, `csharp`, etc. Detect from the current session's file extensions. The hub-plus-api and certainpath-web backends are PHP; other targets may differ.

### Step 5 — Present for approval

Show the human the full draft before writing. Ask:

> "Here's the draft. Save it to `<target>/.aiforging/{patterns|anti-patterns}/<kebab-case-name>.md`?"

Do NOT write the file until the human approves. If they want edits, take them and re-present. If they decline entirely, drop it — the correction won't be lost because the conversation history still has it, and you can offer again if the same correction recurs in a later session (but do not re-offer it in the same session).

### Step 6 — Write the file

On approval, create the file. If the file already exists (the duplicate check in Step 3 missed something), stop and ask again — never overwrite silently.

```bash
# Ensure the directory exists (should, but be safe).
mkdir -p <target>/.aiforging/patterns
mkdir -p <target>/.aiforging/anti-patterns

# Write the file using the Write tool, not shell redirection.
# (Write tool handles atomic writes and avoids quoting headaches.)
```

### Step 7 — Cross-link

After writing, check if a related file exists on the opposite side:

- **New pattern?** Scan `<target>/.aiforging/anti-patterns/` for the anti-pattern that motivates this pattern. If found, offer to add a cross-reference from the existing anti-pattern's `## Related` section to the new pattern file.
- **New anti-pattern?** Scan `<target>/.aiforging/patterns/` for the pattern that fixes this smell. If found, offer to add a cross-reference in the other direction.

Show the human the proposed cross-reference update before applying it. Never edit the existing file silently.

### Step 8 — Confirm and stop

After saving (and any cross-link updates), confirm:

> "Saved to `<target>/.aiforging/{patterns|anti-patterns}/<name>.md`. The next `hammer-refactor` run on this target will include it."

Then return to whatever the human was doing before the capture interrupt. Do NOT chain into proposing additional refactors or re-running the Hammer pass — capture is a side-quest, not a main-quest trigger.

## Over-prompting guard

Do NOT offer to capture a pattern/anti-pattern when:

- The correction is minor or contextual (wrong variable value, missing a business rule, wrong API endpoint, wrong enum value).
- You already offered in this session for a similar correction and the human declined.
- The correction is a one-time fix unlikely to recur.
- The correction is fixing a bug in tests, not a production-code structural issue.
- An existing pattern or anti-pattern file in `<target>/.aiforging/` already captures the rule (even if the file uses slightly different words — read the whole library before offering).

**Bias toward NOT prompting.** Every false-positive offer trains the human to reflexively decline, which breaks the whole Tempering loop. Only offer when the correction clearly encodes a reusable, structural rule. One good capture is worth ten declined prompts.

## Integration

Files created by this skill are consumed by:

- **`hammer-refactor` skill** (installed at `<target>/.claude/skills/hammer-refactor/SKILL.md` during Phase B onboarding). It globs `<target>/.aiforging/patterns/` and `<target>/.aiforging/anti-patterns/` on every run and dispatches one subagent per file, so newly captured rules participate in the next Hammer pass with no additional wiring.
- **Manual code review.** Team members can browse `<target>/.aiforging/patterns/` and `<target>/.aiforging/anti-patterns/` as a living style guide for the target repo.
- **Cross-repo knowledge transfer.** When a captured pattern turns out to be generalizable across targets, a future `/aiforging:propose-pattern` command will let teams promote it from a single target's `.aiforging/` into the plugin's `conventions/refactoring/` library so all future onboarded targets start with it. That upstream flow is not yet built; for now, promote via manual PR against the aiforging plugin source if you want a pattern to spread.

## Hard rules

- **Never write outside the resolved target's `.aiforging/patterns/` or `.aiforging/anti-patterns/` directory.** If the resolution logic in Step 2 fails, stop — do not fall back to some other location.
- **Never overwrite an existing file silently.** Duplicate check in Step 3, confirmation in Step 5, overwrite-check in Step 6.
- **Never inline patterns into existing files "as new sections."** One pattern, one file. This is the scalable-quality principle.
- **Never chain the capture into a Hammer pass.** Capture is read-only with respect to the target's source code. Running Hammer is a separate, explicit command.
- **Never edit the `## Source` field to anything other than `Captured during interactive session on <YYYY-MM-DD>`.** Don't invent authorship. The git blame on the file commit is the authoritative record of who captured it.
