---
name: capture-pattern
description: Use when the user corrects your code, rejects a diff, asks you to clean up or redo work, or says something like "that's not how we do it" or "always/never do X" — offers to capture the lesson as a reusable pattern or anti-pattern in the AI Forging pattern library, closing the Tempering feedback loop.
---

# Capture Pattern — the Tempering feedback loop


**Exclude `README.md` from every tier listing in this skill.** Each tier directory carries one as a placeholder — git cannot track an empty directory, so without it the tier vanishes on the next clone. It is documentation *about* patterns, which makes it exactly the file a topic-overlap check surfaces first. Reading it as a candidate leads to offering to extend the placeholder instead of writing a new pattern, or cross-linking a real pattern to it.

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

> "Would you like me to capture this as a [pattern / anti-pattern] for the `hammer-refactor` library? I'll ask whether it should be shared across all same-stack targets or kept specific to this repo."

If the correction is clearly about what NOT to do, say "anti-pattern." If it's about the right way to do something, say "pattern." If ambiguous, ask which.

If the human declines, drop it. Do not re-ask for the same correction in the same session.

### Step 2 — Resolve the workspace, target, and writing tier

This skill is installed in target repos AND in the forge workspace (or at the repo root for in-repo workspaces). The writing destination depends on where the session is running AND the tier the user selects.

**First, resolve the workspace and target:**

**Case A — session is running inside a target repo (multi-repo setup).**

Detect with:

```bash
test -d ./.aiforging/patterns && test -d ./.aiforging/anti-patterns && echo "IN_TARGET_REPO"
```

The cwd is the target. The forge workspace is found by checking `~/.claude/aiforging.json` for `active_workspace`. If the pointer doesn't resolve, the shared tier is unavailable — captures can only go to the target-local tier. Note this limitation to the user.

**Case B — session is running inside a monorepo / single-repo workspace (in-repo workspace).**

Detect with:

```bash
test -f ./docs/features/README.md && grep -q "Feature Folder Convention" ./docs/features/README.md && echo "IN_REPO_WORKSPACE"
```

The workspace IS the repo root. If the repo has sub-projects with their own `.aiforging/`, determine which sub-project the correction applies to (from the file being discussed in the session). The shared tier is `<repo-root>/.aiforging/patterns/` or `.aiforging/anti-patterns/`. The target-local tier is `<sub-project>/.aiforging/patterns/` or `.aiforging/anti-patterns/`.

**Case C — session is running inside a separate forge workspace (multi-repo setup).**

Detect with:

```bash
test -f ./CLAUDE.md && grep -q "AI Forging workspace" ./CLAUDE.md && \
  test -f ./.claude/settings.local.json && echo "IN_FORGE_WORKSPACE"
```

Read the registered targets from `./.claude/settings.local.json` at `permissions.additionalDirectories`. Then:

- **Zero targets registered** → tell the human: "This workspace has no target repos registered yet. Run `/aiforging:setup` from the workspace to onboard a target before capturing patterns." Stop.
- **Exactly one target registered** → use it. Confirm with the human.
- **Multiple targets registered** → ask the human to pick: "Which target repo does this pattern apply to?" Do NOT guess from the current conversation.

The shared tier for Case C is `<workspace>/.aiforging/patterns/` or `.aiforging/anti-patterns/`.

**Case D — neither a target repo nor a forge workspace.**

Tell the human: "I can only capture patterns from inside a target repo or an AI Forging workspace, and neither looks like the case here. Are you in the right directory?" Stop.

**Second, detect the target's stack** (needed for shared-tier frontmatter). Run `detect-project.py` against the resolved target, or read cached stack info from `<target>/.aiforging/ANALYSIS.md` if present. Record the stack identifiers (e.g., `symfony-php`, `doctrine`).

### Step 3 — Check for duplicates across both tiers

Before drafting anything, scan BOTH the shared tier and the target-local tier for existing patterns:

```bash
# Shared tier (workspace level) — README.md is the tier placeholder, not a pattern
ls <workspace>/.aiforging/patterns/      2>/dev/null | grep -v '^README\.md$'
ls <workspace>/.aiforging/anti-patterns/ 2>/dev/null | grep -v '^README\.md$'

# Target-local tier
ls <target>/.aiforging/patterns/         2>/dev/null | grep -v '^README\.md$'
ls <target>/.aiforging/anti-patterns/    2>/dev/null | grep -v '^README\.md$'
```

**Skip `README.md` in every tier directory.** It is the placeholder that keeps the tier alive in git, and its body is *about* patterns and anti-patterns — which makes it precisely the file a topic-overlap check surfaces first. Treating it as a candidate leads to offering to extend the placeholder instead of writing a new pattern.

Read any file whose name or topic might overlap. If an existing file covers the same ground (in either tier):

- Offer to **update** the existing file instead of creating a new one.
- Show the human the existing file's `## Rule` and `## Detect` sections and ask: "This seems to overlap with `<existing-file>`. Should I extend that file or create a new one?"
- If the existing file is close but the current correction adds a new facet, extending is usually the right call — unless the new facet is substantial enough to warrant its own file.

### Step 4 — Draft the file in AI Forging format

Use the AI Forging pattern format, documented in the pattern-library README at `<workspace>/.aiforging/README.md` (or in the plugin source at `conventions/refactoring/README.md`). Note this is *not* `<tier>/patterns/README.md` — that file is the tier placeholder and describes which tier you are in, not the file format. This is a simpler format than some other projects use — no `Category:` header, no `Safe to auto-refactor:` flag, just the six sections below.

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

### Step 4.5 — Tier selection (shared vs target-local)

After the draft is ready, ask the user which tier to write to. This is the key decision for the two-tier pattern library:

> "Does this pattern apply only to `<current-target>` (target-local), or to all `<stack-family>` targets (shared)?"

Explain the difference concisely:
- **Target-local**: lives in `<target>/.aiforging/{patterns|anti-patterns}/`, applies only to this repo. Use for repo-specific rules.
- **Shared**: lives in `<workspace>/.aiforging/{patterns|anti-patterns}/` with `applies-to` frontmatter, applies to all targets with matching stacks. Use for rules that should be enforced everywhere.

**Default recommendation**: shared. Most patterns captured from real corrections are generalizable. If the user is unsure, suggest shared — it's easy to narrow later, harder to remember to propagate.

**If shared**, prepend the YAML frontmatter to the draft:

```yaml
---
applies-to: [<detected-stack-identifiers>]
captured-from: <target-name>
captured-date: <YYYY-MM-DD>
---
```

The `applies-to` list defaults to the current target's detected stacks, but the user can broaden it (e.g., from `[symfony-php]` to `[symfony-php, laravel-php]`) or narrow it. Offer to adjust.

**If target-local**, no frontmatter is needed. Optionally add `captured-from` and `captured-date` for provenance.

**If the workspace is unavailable** (Case A in Step 2 where the pointer file doesn't resolve), only target-local is available. Inform the user: "I can't locate your forge workspace, so this pattern will be saved to the target-local tier only. To enable shared patterns, set up the workspace pointer with `/aiforging:setup`."

### Step 5 — Present for approval

Show the human the full draft (including frontmatter if shared tier) before writing. Ask:

> "Here's the draft. Save it to `<target>/.aiforging/{patterns|anti-patterns}/<kebab-case-name>.md`?"

Do NOT write the file until the human approves. If they want edits, take them and re-present. If they decline entirely, drop it — the correction won't be lost because the conversation history still has it, and you can offer again if the same correction recurs in a later session (but do not re-offer it in the same session).

### Step 6 — Write the file

On approval, create the file at the tier selected in Step 4.5. If the file already exists (the duplicate check in Step 3 missed something), stop and ask again — never overwrite silently.

**Shared tier destination:**

```bash
# Write to workspace-level shared pattern library
mkdir -p <workspace>/.aiforging/patterns
mkdir -p <workspace>/.aiforging/anti-patterns
# Write the file (with frontmatter) using the Write tool.
```

**Target-local tier destination:**

```bash
# Write to target-specific pattern library
mkdir -p <target>/.aiforging/patterns
mkdir -p <target>/.aiforging/anti-patterns
# Write the file (without frontmatter, or with optional provenance) using the Write tool.
```

### Step 7 — Cross-link

After writing, check if a related file exists on the opposite side:

- **New pattern?** Scan `<target>/.aiforging/anti-patterns/` for the anti-pattern that motivates this pattern. If found, offer to add a cross-reference from the existing anti-pattern's `## Related` section to the new pattern file.
- **New anti-pattern?** Scan `<target>/.aiforging/patterns/` for the pattern that fixes this smell. If found, offer to add a cross-reference in the other direction.

**Skip `README.md` in both scans** — same reason as Step 3. It is the tier placeholder, not a pattern, and cross-linking a real pattern to it produces a dead reference.

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

- **`hammer-refactor` skill** (installed at `<target>/.claude/skills/hammer-refactor/SKILL.md` during onboarding). It merges both the shared tier (workspace-level) and the target-local tier on every run, filters shared patterns by the target's detected stack, and dispatches one subagent per file. Newly captured rules — whether shared or local — participate in the next Hammer pass with no additional wiring.
- **Manual code review.** Team members can browse both `<workspace>/.aiforging/patterns/` (shared) and `<target>/.aiforging/patterns/` (local) as a living style guide. The shared tier is especially useful as a cross-project architectural reference.
- **Cross-repo knowledge transfer.** The two-tier model handles this natively: capturing to the shared tier immediately makes the pattern available to all same-stack targets. No manual propagation step needed. If a pattern was initially captured to the target-local tier and turns out to be generalizable, move it to the shared tier with appropriate `applies-to` frontmatter.

## Hard rules

- **Never write outside the resolved tier's `.aiforging/patterns/` or `.aiforging/anti-patterns/` directory.** Shared-tier writes go to the workspace's `.aiforging/`. Target-local writes go to the target's `.aiforging/`. If the resolution logic in Step 2 fails, stop — do not fall back to some other location.
- **Never overwrite an existing file silently.** Duplicate check in Step 3, confirmation in Step 5, overwrite-check in Step 6.
- **Never inline patterns into existing files "as new sections."** One pattern, one file. This is the scalable-quality principle.
- **Never chain the capture into a Hammer pass.** Capture is read-only with respect to the target's source code. Running Hammer is a separate, explicit command.
- **Never edit the `## Source` field to anything other than `Captured during interactive session on <YYYY-MM-DD>`.** Don't invent authorship. The git blame on the file commit is the authoritative record of who captured it.
